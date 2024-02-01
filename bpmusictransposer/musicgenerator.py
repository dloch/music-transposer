from functools import reduce
from itertools import islice
from jinja2 import Template, Environment, FileSystemLoader

class MusicGenerator:
    notes = {
                "LG": "g'",
                "LA": "a'",
                "B": "b'",
                "C": "c''",
                "D": "d''",
                "E": "e''",
                "F": "f''",
                "HG": "g''",
                "HA": "a''"
            }

    sorted_notes = ["LG", "LA", "B", "C", "D", "E", "F", "HG", "HA"]

    strike_notes = {
                "LG": "LG",
                "LA": "LG",
                "B": "LG",
                "C": "LG",
                "D": "LG",
                "E": "A",
                "F": "E",
                "HG": "F",
                "HA": "HG"
            }

    simple_translation = {
                "sharpc": "",
                "sharpf": "",
            }
    func_translation = {
                "partstart": "bar",
                "partend": "bar",
                "barstart": "bar",
                "barend": "bar",
                "repeatstart": "repeatstart",
                "repeatend": "repeatend"
            }

    def _get_indent(self):
        return '\n' + ' ' * self._indent_level * self._indent_spaces

    def clefc(self, *_args):
        return '%s\\clef treble' % self._get_indent()

    def lineend(self, *_args):
        return '%s\\bar"|"%s\\break\n' % (self._get_indent(), self._get_indent())

    def repeatstart(self, *_args):
        print("Open bracket")
        response = '%s\\repeat volta 2 {' % self._get_indent()
        self._indent_level += 1
        if self.offset:
            response = '%s%s%s\n%s' % (response, self._get_indent(), self.offset, self._get_indent())
            self.offset = None
        return response

    def repeatend(self, *_args):
        self._indent_level -= 1
        print("Ending bracket")
        return "%s}%s\\break\n" % (self._get_indent(), self._get_indent())

    def bar(self, bartype):
        barval = '%s\\bar "%s"' % (self._get_indent(), '%s')
        barvals = { "partstart": "|.",
                    "partend": ".|",
                    "barstart": "|",
                    "barend": "|"
                }
        nobreak = ["barstart", "barend"]
        result = barval % barvals[bartype]
        if self.offset:
            result = '%s\n%s' % (result, self.offset)
            self.offset = None
        elif bartype in nobreak:
            result = "%s \\noBreak" % result

        return '%s\n' % result

    def __getattr__(self, name):
        def method(*args, modifiers={}):
            if name in self.simple_translation:
                return self.simple_translation[name]
            elif name in self.func_translation:
                if modifiers:
                    return getattr(self, self.func_translation[name])(name, *args, modifiers=modifiers)
                return getattr(self, self.func_translation[name])(name, *args)
            raise AttributeError("'%s' has no attribute '%s'" % (self.__class__.__name__, name))
        return method

    def build_embellishment(self, notes):
        self.prev_note = ""
        if len(notes) == 1:
            return "%s\grace { %s16 } " % (self._get_indent(), self.notes[notes[0]])
        return "%s\grace { %s16 %s } " % (self._get_indent(), self.notes[notes[0]], ' '.join(map(lambda n : self.notes[n], notes[1:])))

    def _ignore(self, *_args, **_kwargs):
        return ''

    def _normalize(self, note):
        normal = { "G": "HG", "A": "LA" }
        if isinstance(note, str):
            normal_note = note.upper()
            if normal_note in normal:
                return normal[normal_note]
            if normal_note in self.notes:
                return normal_note
        return note

    def footer(self, note):
        if not self.prev_note:
            return '^"%s"' % note
        return '_"%s"' % note

    def note_above(self, note, starting = "D"):
        note_index = self.sorted_notes.index(note)
        starting_index = self.sorted_notes.index(starting)
        if note == "HA":
            return "HA"
        return self.sorted_notes[note_index + 1 if note_index >= starting_index else starting_index]

    def note_below(self, note, starting = "HA"):
        note_index = self.sorted_notes.index(note)
        starting_index = self.sorted_notes.index(starting)
        if note == "LG":
            return "LG"
        return self.sorted_notes[note_index - 1 if note_index <= starting_index else starting_index]

    def note(self, value, length, modifiers={}):
        result = "%s%d" % (self.notes[value], int(length))
        if modifiers and "dot" in modifiers:
            for x in range(0, modifiers["dot"]):
                result += '.'
        if self.is_tying != None:
            result = "%s%s" % (self.tie(modifiers={"state": "check"}), result)
        if self.prev_note:
            result = "%s%s" % (self._get_indent(), result)
        self.prev_note = value
        return result 

    def time_notation(self, upper, lower):
        return '%s\\time %s/%s' % (self._get_indent(), upper, lower)

    def endingstart(self, num):
        result = []
        self._in_endings = True
        self._indent_level += 1
        return "%s\set Score.repeatCommands = #'((volta \"%s\"))%s" % (self._get_indent(), num, self._get_indent())

    def endingend(self):
        self._in_endings = False
        self._indent_level -= 1
        return "%s\\set Score.repeatCommands = #'((volta #f))%s" % (self._get_indent(), self._get_indent())

    def strike(self, value, modifiers={}):
        return self.grace(value)

    def gracestrike(self, gracenote, from_note):
        gnote = gracenote
        strike_note = self.strike_notes[from_note]
        if gracenote == "LG":
            gnote = "HG"
            strike_note = self.note_below(from_note)
        return self.build_embellishment([gnote, from_note, strike_note])

    def grace(self, value):
        return self.build_embellishment([value])

    def double(self, note, modifiers = {}):
        doubling = []
        if not modifiers and note != "HA":
            doubling.append('HG')
        elif "thumb" in modifiers:
            doubling.append('HA')
        elif "half" in modifiers:
            pass
        if note in ["HA", "HG"]:
            return self.build_embellishment(doubling + [self.note_below(note)])
        return self.build_embellishment(doubling + [note, self.note_above(note)])

    def throw(self):
        return self.build_embellishment(["LG", "D", "C"])

    def nlets(self, *args, **kwargs):
        return ''

    def tie(self, modifiers={}):
        if 'state' in modifiers:
            if modifiers['state'] == 'start':
                self.is_tying = 0
            elif modifiers['state'] == 'end':
                if self.is_tying == None:
                    return '~'
                self.is_tying = None
            elif modifiers['state'] == 'check':
                if self.is_tying == 0:
                    self.is_tying += 1
                    return ""
                return "~"
        else:
            return '~'

    def birl(self, modifiers={}):
        result = []
        if "half" in modifiers:
            pass
        elif "thumb" in modifiers:
            result.append("HA")
        elif "a" in modifiers:
            result.append("LA")
        elif "heavy" in modifiers:
            result.append("HG")
        return self.build_embellishment(result + ["LG", "LA", "LG"])

    def _grip_helper(self):
        mid_note = ["B"] if self.prev_note == "D" else ["D"]
        return ["LG"] + mid_note + ["LG"]

    def grip(self):
        return self.build_embellishment(self._grip_helper())

    def tarluath(self):
        return self.build_embellishment(self._grip_helper() + ["E"])

    def rodin(self):
        return self.build_embellishment(["LG", "B", "LG"])

    def _decode(self, note):
        'A note is either: "funcname" or ("funcname", [args])'
        fname = ""
        fargs = []
        fkwargs = {}
        if isinstance(note, str):
            fname = self._normalize(note)
        else:
            fname = note[0]
            fargs = note[1]
            if len(note) >= 3:
                fkwargs = note[2]
            if isinstance(fargs, tuple):
                fargs = [self._normalize(n) for n in fargs]
        if not isinstance(fargs, list):
            return getattr(self, fname)(fargs)
        if fkwargs:
            return getattr(self, fname)(*fargs, modifiers=fkwargs)
        return getattr(self, fname)(*fargs)


    def _find_offset(self, time, notes, note_offset=0):
        time_count = time[0]
        time_denom = time[1]
        
        first_bar_index = 0
        prebar_notes = []
        for i, note in enumerate(notes):
            if isinstance(note, list) and note[0] == 'note':
                prebar_notes.append(note)
            elif isinstance(note, str) and note.endswith('end'):
                first_bar_index = i
                break

        def set_weight(note):
            note_denom = int(note[1][1])
            base_value = time_denom / note_denom
            addl_value = 0
            if "dot" in note[2]:
                temp_val = base_value
                for x in range(note[2]["dot"]):
                    addl_value += 0.5 * temp_val
                    temp_val = temp_val / 2
            return base_value + addl_value

        prebar_count = reduce(lambda acc, x: acc + set_weight(x), prebar_notes, 0)

        offset = time_count - prebar_count

        if not offset:
            return ""

        return "\set Timing.measurePosition = #(ly:make-moment %d/%d)" % (offset, time_denom)

    def _generate_header(self, tune):
        return """
            piece = "%s"
            opus = "%s"
        """ % (tune.title, tune.composer)

    def _generate_music(self, tune):
        self.prev_note = ""
        result = []
        for i in range(0, len(tune.notes)):
            note = tune.notes[i]
            if not note or note == "_ignore":
                continue
            if self._in_endings != None and not self._in_endings and note[0] != 'endingstart':
                self._in_endings = None
                result.append("\n}")
            if response := self._decode(note):
                result.append(response)
                if note in ["repeatstart", "partstart"] or isinstance(note, list) and note[0] == "time_notation":
                    time = self._curr_time
                    if note[0] == "time_notation":
                        self._curr_time = tuple([int(t) for t in note[1]])
                    if new_offset := self._find_offset(time, islice(tune.notes, i + 1, None)):
                        self.offset = new_offset
        return "".join(result)

    def from_tune(self, tune):
        self.__reset__()
        header = self._generate_header(tune)
        self._curr_time = tune.time
        self.offset = self._find_offset(tune.time, tune.notes)
        music = self._generate_music(tune)
        return self.template.render({"header": header, "music": music})

    def __reset__(self):
        self.prev_note = ""
        self.offset = ""
        self.is_tying = None
        self._in_endings = None
        self._indent_level = 2
        self._curr_time = (0,0)

    def __init__(self):
        self.__reset__()
        self._indent_spaces = 4
        jinja_env = Environment(loader = FileSystemLoader('transposer-data/templates'))
        self.template = jinja_env.get_template("base.ly.jinja")
