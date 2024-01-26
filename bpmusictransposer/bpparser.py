import re
import json
import jinja2
from bpmusictransposer.tune import Tune

class MusicParser:
    syntaxre = re.compile('{{([^}]*)}}')

    basetypes = ["note", "snote", "gnote"]
    dyntypes = ["_"]
    metatypes = ["_docstring"]

    def generate(self, musicdef):
        return ""

    def get_tune(self, musicstr):
        tune = Tune()
        music_section = self.preprocess(tune, musicstr)
        tune.notes = self.parse(music_section)
        print(tune)
        return tune

    def preprocess(self, tune, musicstr):
        music_by_lines = [l for l in musicstr.splitlines() if len(l.strip())]
        values = {}
        for header in self.defs["_docstring"]["HeaderInfo"]:
            restring = header
            if "{{" in header:
                template = jinja2.Template(header)
                format_args = self.defs['_docstring']
                restring = template.render(format_args)
            refinder = re.compile(restring)
            found_line = -1
            for i in range(0, len(music_by_lines)):
                if match := refinder.match(music_by_lines[i].strip()):
                    values.update({k:v.strip() for (k, v) in match.groupdict().items()})
                    music_by_lines[i] = music_by_lines[i][0:match.start()] + music_by_lines[i][match.end():]
                    if len(music_by_lines[i].strip()):
                        music_by_lines.pop(i)
        values["time"] = self._find_first_time(musicstr)
        tune.set_values(values)
        return "\r".join(music_by_lines)

    def parse(self, musicstr):
        tokens = self.tokenize(musicstr)
        return self._coalesce([self._parse_token(tok) for tok in tokens])

    def tokenize(self, musicstr):
        return filter(lambda x : x, musicstr.split())

    def _find_first_time(self, musicstr):
        for (regex, func) in self.read_defs["_"].items():
            if func == "time_notation":
                time_sig = regex.search(musicstr).groups()
                return (int(time_sig[0]), int(time_sig[1]))
        return (4,4)

    def _parse_token(self, token):
        if token in self.read_defs:
            return self.read_defs[token]
        else:
            for (check, applyf) in self.read_defs["_"].items():
                if check.fullmatch(token):
                    return (applyf, list(check.fullmatch(token).groups()))
        return token

    def _load_parser(self, filename):
        defstring = ""
        with open(filename, 'r') as file:
            defstring = file.read()
        self.defs = json.loads(defstring)
        self.read_defs = self._reverse_defs(self.defs)
        self.parser_name = "%s-%s" % (self.defs["_docstring"]["FormatName"], self.defs["_docstring"]["FormatVersion"])
        self.parser_extensions = self.defs["_docstring"]["FormatExtensions"]

    def _create_parse_definition(self, item, syntax, syntax_dict=None):
        defs = syntax_dict if syntax_dict else self.defs
        result = []
        if "{{" not in syntax:
            return [(syntax, item)]
        used_vars = self._get_args(syntax)
        itervals = [defs[k.split(':')[0]].items() for k in used_vars]
        for (k, v) in itervals[0]:
            result.append((MusicParser.syntaxre.sub(v, syntax, 1), [item, k]))
        for i in range(1, len(itervals)):
            tempresult = result
            result = []
            for (resk, resv) in tempresult:
                for (k, v) in itervals[i]:
                    result.append((MusicParser.syntaxre.sub(v, resk, 1), resv + [k]))
        return [(k, (v[0], v[1:])) for (k, v) in result]

    def _format(self, applyf, check, token):
        template = jinja2.Template(applyf)
        check_result = check.fullmatch(token)
        args = self._get_args(applyf)
        return [applyf,[check_result[k] for k in args]]

    def _gen_special_matchers(self, matchers):
        result = {}
        for (k, v) in matchers.items():
            matcher_template = v
            used_vars = self._get_args(v)
            values = {}
            for var in used_vars:
                var_split = var.split(':')
                var_key = var_split[0] 
                var_template_key = var_key
                var_index = ""
                if len(var_split) == 2:
                    var_index = var_split[1]
                    var_template_key = "%s_%s" % (var_key, var_index)
                    matcher_template = re.compile(var).sub(var_template_key, matcher_template, 1)
                group_format = "(?P<%s" + var_index + ">%s)"
                if var_key in self.defs:
                    values[var_template_key] = group_format % (var_key, "|".join(self.defs[var_key].values()))
                elif var_key in matchers:
                    values[var_template_key] = group_format % (var_key, matchers[var_key])
            reresult = jinja2.Template(matcher_template).render(values)
            result[re.compile(reresult)] = k
        return result

    def _reverse_defs(self, defs):
        result = {}
        used_values = []
        
        for key in MusicParser.basetypes:
            for k, v in defs[key].items():
                result[v] = [key, k]
        
        for key, value in defs.items():
            if key in MusicParser.basetypes + MusicParser.dyntypes + MusicParser.metatypes:
                continue
            if isinstance(value, str):
                toadd = self._create_parse_definition(key, value)
                for added in toadd:
                    result[added[0]] = added[1]
        result["_"] = self._gen_special_matchers(self.defs["_"])
        return result

    def _coalesce(self, notes):
        is_note = lambda x : x[0] == "note"
        is_modifier = lambda x : x[0] in ["dot"]
        result = []
        curr_note = None
        for note in notes:
            if is_note(note):
                if curr_note:
                    result.append(curr_note)
                curr_note = note
            else:
                if curr_note and is_modifier(note):
                        curr_note[1].append({note[0]: 1})
                else:
                    if curr_note:
                        result.append(curr_note)
                        curr_note = None
                    result.append(note)
        if curr_note:
            result.append(curr_note)
        return result

    def _get_args(self, args_from):
        return MusicParser.syntaxre.findall(args_from)

    def __init__(self, filedef):
        self.write_defs = {}
        self.read_defs = {}

        self.parser_name = ""
        self.parser_extensions = []

        self._load_parser(filedef)
