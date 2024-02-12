import re, json, os
import sys
from bpmusictransposer.tune import Tune
from itertools import takewhile, islice
from importlib import resources as impresources
from . import parserdefs

class FindReplace:
    def run(self, match):
        if self.key == None:
            return None
        return (self.key, match.group(self.key))

    def __init__(self, key, regex):
        self.key = key
        self.regex = regex

class MusicParser:
    parsers = {}

    basetypes = ["note", "snote", "gnote"]
    dyntypes = ["_"]
    metatypes = ["_docstring", "_modifiers", "_postprocess"]

    argument_re = re.compile('{{([^}]*)}}')

    def get_tune_from_file(self, filename):
        with open(filename, encoding=self.encoding) as file:
            tunestr = file.read()
        return self.get_tune(tunestr)

    def get_tune(self, musicstr):
        return self.parse(Tune(), musicstr)

    def _get_note_type(self, notedef):
        if isinstance(notedef, str):
            return notedef
        return notedef[0]

    def parse(self, tune, musicstr):
        preprocessed_parts = self._pretokenize_parse(musicstr)
        header = {}
        remove = []
        for i, note in enumerate(preprocessed_parts):
            if isinstance(note, tuple):
                if tuple[1] == '':
                    remove.insert(0, i)
                elif not note[0] in header or not header[note[0]]:
                    header[note[0]] = note[1]
                    remove.insert(0, i)
        for i in remove:
            preprocessed_parts.pop(i)
        tune.set_values(header)
        note_result = []
        splitre = re.compile("[-\s]")
        for note_section in islice(preprocessed_parts, len(header), None):
            if isinstance(note_section, str):
                for token in filter(lambda x : x, splitre.split(note_section)):
                    result = self._parse_token(token)
                    if isinstance(result, str):
                        if result in self.defs:
                            result = [result, (), {}]
                        else:
                            print("Could not parse string, dumping: %s" % result, file=sys.stderr)
                            continue
                    args = [x for x in result[1] if x]
                    result[1] = tuple(args)
                    if result[0]:
                        note_result.append(result)
            else:
                note_result.append(note_section)
        tune.notes = self.post_process(note_result)
        times = [x for x in tune.notes if isinstance(x, list) and x[0] == "time_notation"]
        if len(times) == 0:
            tune.time = (4,4)
        else:
            tune.time = tuple(map(int, times[0][1]))
        return tune


    def post_process(self, notes):
        def _add_dots_to_previous_note(acc, note):
            for i in range(-1, -len(notes), -1):
                next_note = notes[i]
                if isinstance(next_note, list) and next_note[0] == "note":
                    next_note[2]['dot'] =  next_note[2].get('dot', 0) + len(note[1][0])
                    return {}
            return {}
        def _add_tuplet_to_previous_notes(acc, note):
            print(note)
            count = note[1][0]
            if "state" in note[2]:
                if "state" == "start":
                    print("Tuplet start: %s" % count)
                    return { "tuplet": count }
                elif "state" == "end":
                    return { "tuplet": None }
                return
            return
        def _simple_add(note):
            def _add(acc, x):
                acc.append(note)
                return {}
            return _add
        result = []
        state = {}
        handlers = {
            "common_time": _simple_add(["time_notation", ('4','4'), {}]),
            "cut_common_time": _simple_add(["time_notation", ('2','2'), {}]),
            "dot": _add_dots_to_previous_note,
            "tuplet": _add_tuplet_to_previous_notes
        }
        for note in filter(lambda x : x != None, notes):
            ntype = self._get_note_type(note)
            if ntype in handlers:
                state.update(handlers[ntype](result, note))
            else:
                add_value = note
                if ntype == "note":
                    if "in_tuplet" in state:
                        add_value[2]['tuplet'] = True
                result.append(add_value)
        return result

    def tokenize(self, musicstr):
        return musicstr.trim().split()

    # Parser resolvers
    def _parse_token(self, token):
        for c in self.category_defs:
            if args := c['filter'](token):
                target = c['target']
                if target is None:
                    return self.read_defs[token]
                defargs = self._resolve_args(args)
                modf = lambda a, x : x
                if 'modifier' in c:
                    modf = c['modifier']
                    # Special case for simple targets:
                    if target not in self.read_defs:
                        return modf(args, [target, (), {}])
                if callable(self.read_defs[target]):
                    return modf(args, self.read_defs[c['target']](defargs))
                return modf(args, [target, (), {}])
        if token in self.defs['_postprocess']:
            return [self.defs['_postprocess'][token], (), {}]
        return token

    def _resolve_args(self, args):
        result = []
        for arg in args.groups():
            if arg in self.read_defs:
                result.append(self.read_defs[arg])
            else:
                result.append(arg)
        return tuple(result)

    def _pretokenize_parse(self, musicstr):
        # This logic is still bad, pls fix
        # It should match some string with a group or not, or mix:
        # "abcd I should match this in a group, and this not in a group efgh"
        # Chop it into pieces on the match:
        # "abcd ","[redacted]", " efgh"
        # Then shove it back together with a directive:
        # "abcd ", ["groupname", ("I should match this in a group"), {}], " efgh"
        musicparts = [self._fix_broken_args(musicstr)]
        for (finder, parser) in self.pretokenize_defs:
            replacements = []
            for i, musicpart in enumerate(musicparts):
                if not isinstance(musicpart, str):
                    # We've already tokenized this part
                    continue
                matches = [ x for x in reversed([match for match in finder.finditer(musicpart)])]
                if not matches:
                    continue
                # Work through matches backwards:
                before = musicpart
                replacement = []
                for match in matches:
                    replacement.append(before[match.end():])
                    before = before[0:match.start()]
                    token = parser(match)
                    if token:
                        replacement.append(token)
                if before:
                    replacement.append(before)

                # Now we have a list of [lastpart, lastpart-1...], queue up replacing our actual string:
                replacements.insert(0, (i, replacement))
            for (i, replacement) in replacements:
                musicparts.pop(i)
                # Bounce out our current section:
                # Jam in replacements in (reverse) order:
                for replacement_part in replacement:
                    musicparts.insert(i, replacement_part)
        # We should be parsed
        return musicparts
                
    def _fix_broken_args(self, musicstr):
        newline_re = re.compile("[\n\r]")
        parts = newline_re.split(musicstr)
        incomplete_re = re.compile("[^\\[{(]*[\\[({][^\\]})]*")
        complete_re = re.compile(".*[({\\[({].*[)}\\]]")
        result = []
        in_broken_args = False
        for part in parts:
            if in_broken_args:
                result[-1] += part
                if complete_re.search(result[-1]):
                    in_broken_args = False
            else:
                result.append(part)
                if incomplete_re.fullmatch(part):
                    in_broken_args = True
        return "\n".join(result)

    # Parser builders

    def _build_base_types(self):
        for i in range(0, len(self.basetypes)):
            key = self.basetypes[i]
            if key not in self.defs and i > 0:
                prev_key = self.basetypes[i-1]
                print("No definition for %s, falling back to %s" % (prev_key, key), file=sys.stderr)
                print("If %s and %s are supposed to be different, this is a problem." % (prev_key, key), file=sys.stderr)
                key = prev_key
            elif key not in self.defs:
                print("Failed to load base key %s" % key, file=sys.stderr)
                continue
            for (k, v) in self.defs[key].items():
                if isinstance(v, list):
                    for value in v:
                        self.read_defs[value] = k
                else:
                    self.read_defs[v] = k

    def _build_header_definitions(self):
        header_defs = self.defs["_docstring"]["HeaderInfo"]
        for regex in header_defs:
            find_re = self._build_re(regex[0])
            replace_with = None if len(regex) == 1 else regex[1]
            fr = FindReplace(replace_with, find_re)
            self.pretokenize_defs.append((find_re, fr.run))

    def _build_match(self, name, definition):
        if not self._is_complex(definition):
            return True

        categorizer = self._build_categorizer(name, definition)
        mutator = self._build_mutator(name, definition)

        self.category_defs.append(categorizer)
        self.read_defs[name] = mutator

        return False

    def _build_read_definitions(self):
        self._build_base_types()
        exempt_types = self.basetypes + self.dyntypes + self.metatypes
        simple_conversions = []
        self.category_defs.append({"name": "placeholder"})
        for (k,v) in filter(lambda x : x[0] in self.basetypes, self.defs["_"].items()):
            categorizer = self._build_categorizer(k, v)
            self.category_defs.append(categorizer)
            mutator = self._build_mutator(k, v)
            self.read_defs[k] = mutator
        for (k,v) in filter(lambda k : k[0] not in exempt_types, self.defs.items()):
            if isinstance(v, list):
                for match in v:
                    if self._build_match(k,match):
                        self.read_defs[match] = k
                        simple_conversions.append(match)
                        continue
            else:
                if self._build_match(k,v):
                    self.read_defs[v] = k
                    simple_conversions.append(v)
                    continue
        self.category_defs[0] = {"filter": lambda x : x in simple_conversions, "target": None}
        self._build_modifier_definitions()

    def _add_modifier(self, modifier):
        def add(match, notedef):
            notedef[2].update(modifier)
            return notedef
        return add

    def _add_selector_modifier(self, modifier):
        def add(match, notedef):
            toadd = {}
            result_dict = match.groupdict()
            print(result_dict)
            for (k, v) in result_dict.items():
                if k in modifier and v != None:
                    toadd[k] = modifier[k][v] if isinstance(modifier[k], dict) else modifier[k]
            notedef[2].update(toadd)
            return notedef
        return add
            
    def _has_selector(self, modifier):
        result = False
        for (k,v) in modifier.items():
            print(k)
            print(v)
            result = result or isinstance(v, dict)
        return result

    def _build_modifier_definitions(self):
        for (key, moddef) in self.defs['_modifiers'].items():
            for target in moddef['_applies']:
                classifier = {'target': target, 'filter': lambda x : False, 'modifier': lambda args, x : x}
                repattern = moddef['_pattern'].replace('item', target)
                modifier_re = self._build_re(repattern)
                modifier = {}
                for (k, v) in moddef['_modify'].items():
                    if not isinstance(v, dict):
                        modifier[k] = v
                    else:
                        modifier[k] = v
                classifier['filter'] = modifier_re.fullmatch
                classifier['modifier'] = self._add_selector_modifier(modifier) if self._has_selector(modifier) else self._add_modifier(modifier)
                self.category_defs.append(classifier)


    def _build_extended_re(self, value):
        if not self._is_complex(value):
            return "(?P<%s>%s)" % ("%s", value)
        return self._replace_arguments(value)

    def _get_re(self, key, modifier=False):
        if key in self.defs:
            redef = self.defs[key]
            if isinstance(redef, dict):
                values = []
                for value in redef.values():
                    if isinstance(value, list):
                        values += value
                    else:
                        values.append(value)
                return "(?P<%s>%s)" % ("%s", "|".join(values))
            elif isinstance(redef, list):
                redef = "(%s)" % "|".join(redef)
            result = self._build_re(redef).pattern 
            return result
        elif key in self.defs["_"]:
            return self._build_extended_re(self.defs["_"][key])
        raise Exception("Bad key: '%s'" % key)

    def _build_re(self, regexstr):
        resultstr = regexstr
        if self._is_complex(resultstr):
            resultstr = self._replace_arguments(resultstr)
        return re.compile(resultstr)

    def _build_mutator(self, funcname, value):
        return lambda x : [funcname, x, {}]
            

    def _build_categorizer(self, target, definition):
        categorizer = {"filter": lambda x : False, "target": target}
        match_re = re.compile(self._replace_arguments(definition))
        categorizer["filter"] = lambda x : match_re.fullmatch(x)
        return categorizer

    def _replace_arguments(self, value):
        args = self.argument_re.findall(value)
        result = value
        for arg in args:
            re_value = self._get_re(arg.split(":")[0])
            if "%s" in re_value:
                re_value = re_value % arg.replace(":", "_")
            result = result.replace("{{%s}}" % arg, re_value, 1)
        return result
                
    def _is_complex(self, definition):
        if isinstance(definition, list):
            return False
        return self.argument_re.search(definition) != None

    def _load_parser(self, jsondef, register=False):
        self.defs = jsondef
        self.encoding = jsondef.get("Encoding", "utf-8")
        self._build_header_definitions()
        self._build_read_definitions()
        if register:
            self.parsers[jsondef["_docstring"]["FormatName"]] = self

    def __init__(self, jsondef, register=True):
        self.category_defs = []
        self.write_defs = {}
        self.pretokenize_defs = []
        self.read_defs = {}

        self.parser_name = ""
        self.parser_extensions = []

        self._load_parser(jsondef, register)
    def parserdefs():
        return parserdefs

def load_parsers():
    if not MusicParser.parsers:
        parsers = impresources.files(parserdefs)
        for parserfile in parsers.iterdir():
            if parserfile.suffix == '.json':
                try:
                    parserjson = json.loads(parserfile.read_text())
                    MusicParser(parserjson, register=True)
                except Exception as e:
                    print("Could not load parser definition: %s" % parserfile.name, file=sys.stderr)
                    print(e, file=sys.stderr)

load_parsers()
