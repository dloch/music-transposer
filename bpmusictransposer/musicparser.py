import re
import json
from bpmusictransposer.tune import Tune
from itertools import takewhile, islice

class FindReplace:
    def run(self, input):
        if self.key == None:
            return self.key
        return (self.key, self.regex.fullmatch(input).group(self.key))

    def __init__(self, key, regex):
        self.key = key
        self.regex = regex

class MusicParser:
    basetypes = ["note", "snote", "gnote"]
    dyntypes = ["_"]
    metatypes = ["_docstring", "_modifiers"]

    argument_re = re.compile('{{([^}]*)}}')

    def get_tune(self, musicstr):
        return self.parse(Tune(), musicstr)

    def parse(self, tune, musicstr):
        preprocessed_parts = self._pretokenize_parse(tune, musicstr)
        header = {x[0]: x[1] for x in takewhile(lambda x : isinstance(x, tuple), preprocessed_parts)}
        tune.set_values(header)
        note_result = []
        for note_section in islice(preprocessed_parts, len(header), None):
            if isinstance(note_section, str):
                for token in note_section.split():
                    note_result.append(self._parse_token(token))
            else:
                note_result.append(note_section)
        for note in filter(lambda x : x != None, note_result):
            if note == "dot" or isinstance(note, list) and note[0] == "dot":
                if 'dot' in tune.notes[-1][2]:
                    tune.notes[-1][2]['dot'] += 1
                else:
                    tune.notes[-1][2]['dot'] = 1
            else:
                tune.notes.append(note)
        return tune

    def tokenize(self, musicstr):
        return musicstr.trim().split()

    # Parser resolvers
    def _parse_token(self, token):
        for c in self.category_defs:
            if args := c['filter'](token):
                if c['target'] is None:
                    return self.read_defs[token]
                defargs = self._resolve_args(args)
                modf = lambda a, x : x
                if 'modifier' in c:
                    modf = c['modifier']
                    # Special case for simple targets:
                    if c['target'] not in self.read_defs:
                        return modf(args, [c['target'], (), {}])
                return modf(args, self.read_defs[c['target']](defargs))
        return token

    def _resolve_args(self, args):
        result = []
        for arg in args.groups():
            if arg in self.read_defs:
                result.append(self.read_defs[arg])
            else:
                result.append(arg)
        return tuple(result)

    def _pretokenize_parse(self, tune, musicstr):
        musicparts = musicstr.split('\n')
        replacements = []
        for (finder,parser) in self.pretokenize_defs.items():
            for i in range(0, len(musicparts)):
                temparr = []
                tempstr = musicparts[i]
                while match := finder.search(tempstr):
                    if match.start() > 0:
                        temparr.append(tempstr[0:match.start()])
                    tempres = parser(match.group())
                    if tempres:
                        temparr.append(tempres)
                    else:
                        temparr.append(None)
                    tempstr = tempstr[match.end():]
                if len(temparr) > 0:
                    temparr.append(tempstr)
                    replacements.append((i, temparr))
        for replacement in reversed(replacements):
            index = replacement[0]
            out = musicparts.pop(replacement[0])
            for toadd in reversed(replacement[1]):
                if toadd:
                    musicparts.insert(index, toadd)
        return [x for x in musicparts if len(x) > 0]

    # Parser builders

    def _build_base_types(self):
        for i in range(0, len(self.basetypes)):
            key = self.basetypes[i]
            if key not in self.defs and i > 0:
                prev_key = self.basetypes[i-1]
                print("No definition for %s, falling back to %s" % (prev_key, key))
                print("If %s and %s are supposed to be different, this is a problem." % (prev_key, key))
                key = prev_key
            elif key not in self.defs:
                print("Failed to load base key %s" % key)
                continue
            for (k, v) in self.defs[key].items():
                if isinstance(v, list):
                    for value in v:
                        self.read_defs[value] = k
                else:
                    self.read_defs[v] = k

    def _build_header_definitions(self):
        header_defs = self.defs["_docstring"]["HeaderInfo"]
        for key in header_defs["_"]:
            find_re = self._build_re(key)
            fr = FindReplace(None, find_re)
            self.pretokenize_defs[find_re] = fr.run
        for (key, value) in header_defs.items():
            if key == "_":
                continue
            find_re = self._build_re(value)
            fr = FindReplace(key, find_re)
            self.pretokenize_defs[find_re] = fr.run

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
            for (k, v) in result_dict.items():
                if k in modifier:
                    toadd[k] = modifier[k][v] if isinstance(modifier[k], dict) else modifier[k]
            notedef[2].update(toadd)
            return notedef
        return add
            
    def _has_selector(self, modifier):
        result = False
        for (k,v) in modifier.items():
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

    def _load_parser(self, filedef):
        with open(filedef, 'r') as file:
            self.defs = json.loads(file.read())
        self._build_header_definitions()
        self._build_read_definitions()

    def __init__(self, filedef):
        self.category_defs = []
        self.write_defs = {}
        self.pretokenize_defs = {}
        self.read_defs = {}

        self.parser_name = ""
        self.parser_extensions = []

        self._load_parser(filedef)
