import re, json, os
import sys
from bpmusictransposer.tune import Tune
from bpmusictransposer.notetoken import NoteToken
from itertools import takewhile, islice
from importlib import resources as impresources
from . import parserdefs
from functools import partial

from pprint import pprint

class MusicParser:
    argument_re = re.compile('{{([^}]*)}}')

    loglevel = 0
    logger = sys.stdout
    parsers = {}
    
    def _log(self, level, msg):
        if level <= self.loglevel and self.logger:
            print(msg, file=self.logger)

    def set_loglevel(self, level):
        self.loglevel = level
        self.logger = None if level == 0 else sys.stdout

    def get_tune_from_file(self, filename):
        with open(filename, encoding=self.encoding) as file:
            tunestr = file.read()
        return self.get_tune(tunestr)

    def get_tune(self, musicstr):
        result = Tune()
        result.notes = self.parse(musicstr)
        header = self._process_first_and_remove(["title", "tunetype", "composer"], result)
        result.set_values(header)
        time = self._find_first("time_notation", result)
        if time:
            time_parts = time.get_args()
            result.time = (int(time_parts[0]), int(time_parts[1]))
        return result

    def parse(self, musicstr):
        notes = musicstr.split("\n")
        notes = self._preprocess_parse(notes)
        notes = self._token_parse(notes)
        return notes

    def _preprocess_parse(self, notes):
        result = []
        fixre = re.compile("[\[{(][^\]})]*$")
        fixing = ""
        def needs_fix(part):
            return fixre.match(part) != None

        def is_fixed(part):
            return fixre.match(part) == None

        for note in notes:
            toadd = note
            if fixing:
                fixing += note
                if is_fixed(fixing):
                    toadd = fixing
                    fixing = ""
            elif needs_fix(note):
                fixing += note
                continue
            for (target, matcher) in self.preprocess_matchers:
                if matched := matcher(toadd):
                    toadd = self.preprocess_handlers[target](matched)
                    break
            if toadd:
                result.append(toadd)
        return result

    def _token_parse(self, notes):
        tokens = []
        for note in notes:
            if isinstance(note, str):
                tokens += note.split()
            else:
                tokens.append(note)

        result = []
        reparse = []
        for (i, token) in enumerate(tokens):
            toadd = token
            if isinstance(token, str):
                for (target, matcher) in self.parser_matchers:
                    if match := matcher(token):
                        toadd = self.parser_handlers[target](match)
                        break
            if callable(toadd):
                toadd = toadd(result)
            if toadd:
                if isinstance(toadd, str):
                    reparse.append(len(result))
                result.append(toadd)
        return self._compound_token_parse(result, reparse)

    def _compound_token_parse(self, notes, indices):
        result = notes
        for i in reversed(indices):
            next = result.pop(i)
        return result

    def _process_first_and_remove(self, keys, tune):
        to_find = keys
        remove = []
        result = {}
        for (i, note) in enumerate(tune.notes):
            if note.note_type in to_find:
                to_find.remove(note.note_type)
                result[note.note_type] = note
                remove.append(i)
        for i in reversed(remove):
            tune.notes.pop(i)
        return result
    def _find_first(self, key, tune):
        for (i, note) in enumerate(tune.notes):
            if key == note.get_type():
                return note
        return None

    # Parser builders
    def _replace_arguments(self, value):
        args = self.argument_re.findall(value)
        result = value
        if args:
            for arg in args:
                re_value = self.internal_defs[arg.split(":")[0]]
                if '%s' in re_value:
                    re_value = re_value % arg.replace(":", "_")
                result = result.replace("{{%s}}" % arg, re_value, 1)
        return result
                
    def _add_all(self, target, key, values):
        if isinstance(values, str):
            target[values] = key
            return [values]
        else:
            for v in values:
                target[v] = key
            return values

    def _build_internal_defs(self, defs):
        defkey = "_internal_defs"
        if defkey not in defs:
            return
        for (k, v) in defs[defkey].items():
            self._log(3, "Add Internal definition: %s" % k)
            self._log(4, v)
            self._log(4, "====================================")
            if isinstance(v, str):
                self.internal_defs[k] = "(?P<%s>%s)" % ("%s", v)
            elif isinstance(v, dict):
                repattern = "(?P<%s>%s)"
                redata = []
                for (subkey, values) in v.items():
                    redata += self._add_all(self.internal_defs, subkey, values)
                self.internal_defs[k] = repattern % ("%s", "|".join(redata))
        self._log(1, "Build internal definitions")
        self._log(2, self.internal_defs)

    def _build_ingest_handler(self, name):
        def handle(match):
            result = NoteToken(name)
            result.read_arguments(match)
            result.translate_arguments(self.internal_defs)
            return result
        return handle

    def _build_modifier_handler(self, modifiers):
        def omnihandle(note):
            for (k,v) in modifiers.items():
                result = {}
                if isinstance(v, list):
                    if v[0] == "_!f":
                        result[k] = globals()[v[1]][v[2]](note.keyword_arguments[v[3]])
                    else:
                        result[k] = [note.keyword_arguments[key] for key in v]
                elif isinstance(v, dict):
                    arg = note.keyword_arguments.get(k, None)
                    if arg:
                        result[k] = modifiers[k][arg]
                    else:
                        result[k] = arg
                else:
                    result[k] = v
                note.add_modifiers(result)
                return note
        return omnihandle

    def _build_type_handler(self, mutate):
        def typehandle(note):
            note.set_note_type(mutate)
            return note
        return typehandle

    def _build_mutate_handler(self, mutate):
        def default(token):
            for (key, value) in mutate["default"].items():
                token.set_arg(key, value)
            return token
        def order(token):
            token.set_order(token.mutate["order"])
            return token
        f = lambda x : x
        if "default" in mutate:
            f = default
        if "order" in mutate:
            f = self._compose(order, f)
        return f

    def _build_args_handler(self, args):
        def set_args(note):
            note.ordered_arguments = args
            return note
        return set_args

    def _build_apply_handler(self, apply):
        def prevn(count, apply_token, notes):
            applied = 0
            for i in range(-1, -len(notes), -1):
                if isinstance(notes[i], NoteToken) and notes[i].note_type == apply["target"]:
                    notes[i].add_modifiers(apply_token.modifiers)
                    applied += 1
                if applied >= count:
                    break
            return apply_token if "return" in apply and apply["return"] else None

        def apply_handler(token):
            count = apply["prevn"]
            if isinstance(count, str):
                count = int(token.keyword_arguments[count])
            return partial(prevn, count, token)
        return apply_handler

    def _compose(self, f, g):
        return lambda x : f(g(x))

    def _arg_compose(self, f, g):
        '''Compose where g takes and returns a tuple of variadic/dict for f'''
        def composed(*args, **kwargs):
            (largs, kargs) = g(*args, **kwargs)
            return f(*largs, **kargs)
        return composed

    def _token_compose(self, f, g):
        '''Compose where g takes a variadic/dict, and returns a token [T,(),{}]'''
        def composed(match):
            (name, args, kwargs) = g(*args, **kwargs)
            return f(name, *args, **kwargs)
        return composed

    def _build_simple_matcher(self, pattern):
        patternre = re.compile(pattern)
        def match(tocheck, complete=True):
            if complete:
                return patternre.fullmatch(tocheck)
            return patternre.search(tocheck)
        return match

    def _build_arg_matcher(self, pattern, name=None, register=False):
        matchre = self._replace_arguments(pattern)
        if register and name and not name in self.internal_defs:
            self.internal_defs[name] = matchre
        return self._build_simple_matcher(matchre)

    def _add_parser_matcher(self, matchers, target, pattern):
        matchers.append((target, self._build_arg_matcher(pattern, target, True)))

    def _add_preprocess_data(self, target, *patterns):
        for pattern in patterns:
            if isinstance(pattern, list):
                self._add_parser_matcher(self.preprocess_matchers, target, *pattern)
            else:
                self._add_parser_matcher(self.preprocess_matchers, target, pattern)
        if target not in self.preprocess_handlers:
            handler = self._build_ingest_handler(target)
            self.preprocess_handlers[target] = handler

    def _build_preprocess_defs(self, defs):
        defkey = "_preprocess"
        if defkey not in defs:
            return
        for definition in defs[defkey]:
            self._log(3, "Add Preprocess definition: %s" % definition["target"])
            self._log(4, definition["pattern"])
            self._log(4, "====================================")
            if isinstance(definition["pattern"], str):
                self._add_preprocess_data(definition["target"], definition["pattern"])
            else:
                self._add_preprocess_data(definition["target"], *definition["pattern"])

    def _add_parser_matchers(self, target, *patterns):
        for pattern in patterns:
            self._add_parser_matcher(self.parser_matchers, target, pattern)

    def _add_parser_handler(self, target, definition):
        handled = ["Ingest"]
        handlers = [
            ("type", self._build_type_handler),
            ("mutate", self._build_mutate_handler),
            ("args", self._build_args_handler),
            ("modifiers", self._build_modifier_handler),
            ("apply", self._build_apply_handler)
        ]
        handler = self._build_ingest_handler(target)
        for toapply in filter(lambda k : k[0] in definition, handlers):
            handler = self._compose(toapply[1](definition[toapply[0]]), handler)
            handled.append(toapply[0].capitalize())
        self.parser_handlers[target] = handler

    def _build_parser_defs(self, defs):
        defkey = "_parser_defs"
        if defkey not in defs:
            return
        for definition in defs[defkey]:
            self._log(3, "Add Parse definition: %s" % definition["target"])
            self._log(4, definition["pattern"])
            self._log(4, "====================================")
            if isinstance(definition["pattern"], str):
                self._add_parser_matchers(definition["target"], definition["pattern"])
            else:
                self._add_parser_matchers(definition["target"], *definition["pattern"])
            self._add_parser_handler(definition["target"], definition)

    def _add_modifier_matcher(self, target, name, definition):
        name = "%s_%s" % (name, target)
        matcher = self._build_arg_matcher(definition["pattern"].replace("{{item}}", "{{%s}}" % target), name, True)
        self.parser_matchers.append((name, matcher))
        return name
        
    def _add_modifier_handler(self, target, name, definition):
        g = self.parser_handlers[target]
        handler = self._compose(self._build_modifier_handler(definition["modify"]), g)
        self.parser_handlers[name] = handler


    def _build_modifier_defs(self, defs):
        defkey = "_modifiers"
        if defkey not in defs:
            return
        for definition in defs[defkey]:
            for target in definition["applies"]:
                self._log(3, "Add Modified definition: %s" % definition["name"])
                self._log(3, "Against: %s" % target)
                self._log(4, definition)
                target_name = self._add_modifier_matcher(target, definition["name"], definition)
                self._log(3, "As: %s" % target_name)
                self._add_modifier_handler(target, target_name, definition)
                self._log(3, "====================================")

    def _load_parser(self, jsondef, register=False):
        defs = jsondef
        self.encoding = jsondef["_docstring"].get("Encoding", "utf-8")
        self._build_internal_defs(defs)
        self._build_preprocess_defs(defs)
        self._build_parser_defs(defs)
        self._build_modifier_defs(defs)
        if register:
            self.parsers[jsondef["_docstring"]["FormatName"]] = self

    def __init__(self, jsondef, register=True):
        noop = lambda *args, **kwargs: None

        self.internal_defs = {}

        self.preprocess_matchers = []
        self.preprocess_handlers = { "_": noop }

        self.parser_matchers = []
        self.parser_handlers = { "_": noop }

        self.parser_name = ""
        self.parser_extensions = []

        self._load_parser(jsondef, register)

def load_parsers():
    if not MusicParser.parsers:
        parsers = impresources.files(parserdefs)
        for parserfile in parsers.iterdir():
            if parserfile.suffix == '.json':
                parserjson = json.loads(parserfile.read_text())
                MusicParser(parserjson, register=True)
                try:
                    parserjson = json.loads(parserfile.read_text())
                    MusicParser(parserjson, register=True)
                except Exception as e:
                    print("Could not load parser definition: %s" % parserfile.name, file=sys.stderr)
                    print(e, file=sys.stderr)

load_parsers()
