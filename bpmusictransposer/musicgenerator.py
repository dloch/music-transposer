from functools import reduce
from itertools import islice
import sys
from jinja2 import Template, Environment, PackageLoader

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
                "E": "LA",
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

    def _in_context(self, context):
        for c in self._context:
            if c[0] == context:
                return True
        return False

    def _enter_context(self, context):
        self._indent_level += 1
        self._context.append(context)

    def _leave_context(self, context):
        result = None
        if len(self._context) > 0:
            if self._context[-1][0] != context:
                return None
            result = self._context.pop()
            response = "%s%s" % (self._get_indent(), result[1])
            self._indent_level -= 1
            return response
        return None
            

    def clefc(self, *_args):
        return '%s\\clef treble' % self._get_indent()

    def sharp(self, note, **kwargs):
        return ""

    def natural(self, note, **kwargs):
        return ""

    def flat(self, note, **kwargs):
        return ""

    def lineend(self, *_args):
        return '%s\\bar"|"%s\\break\n' % (self._get_indent(), self._get_indent())

    def repeatstart(self, *_args):
        response = '%s\\repeat volta 2 {' % self._get_indent()
        self._enter_context(("repeat", "}"))
        if self.offset:
            response = '%s%s%s\n%s' % (response, self._get_indent(), self.offset, self._get_indent())
            self.offset = None
        return response

    def repeatend(self, *_args):
        context_end = self._leave_context("repeat")
        response = "%s\\break\n" % self._get_indent()
        if context_end:
            response = "%s%s" % (context_end, response)
        return response


    def bar(self, bartype):
        barval = '%s\\bar "%s"' % (self._get_indent(), '%s')
        barvals = { "partstart": "|.",
                    "partend": ".|",
                    "barstart": "|",
                    "barend": "|"
                }
        nobreak = ["barstart", "barend"]
        result = barval % barvals[bartype]
        if bartype in nobreak:
            result = '%s%s' % (result, self._get_indent())
        else:
            result = '%s%s\\break' % (result, self._get_indent())
            self.offset = None
        return '%s\n' % result

    def __getattr__(self, name):
        def method(*args, **modifiers):
            if name in self.simple_translation:
                return self.simple_translation[name]
            elif name in self.func_translation:
                if modifiers:
                    return getattr(self, self.func_translation[name])(name, *args, **modifiers)
                return getattr(self, self.func_translation[name])(name, *args)
            raise AttributeError("'%s' has no attribute '%s'" % (self.__class__.__name__, name))
        return method

    def build_zipped_embellishment(self, notes):
        self.prev_note = ""
        return "%s\grace { %s }" % (self._get_indent(), ' '.join(map(lambda x : "%s%d" % x, notes)))

    def build_embellishment(self, notes):
        if not self.prev_note:
            self.embellishment_fix = True
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

    def fermata(self, *_args):
        return "^\\fermata"

    def text(self, value):
        return ('_"%s"' if self.prev_note else '^"%s"') % value

    def footer(self, *args, **kwargs):
        return self.text(args[0])

    def title(self, *args, **kwargs):
        # TODO: Reformat for when we have multiple pieces in one file
        return self.text(args[0])

    def tunetype(self, *args, **kwargs):
        return self.text(args[0])

    def composer(self, *args, **kwargs):
        return self.text(args[0])

    def tempo(self, *args, **kwargs):
        return self.text("Tempo %s" % args[0])

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

    def note(self, value, length, **modifiers):
        result = "%s%d" % (self.notes[value], int(length))
        if "dot" in modifiers:
            for x in range(0, modifiers["dot"]):
                result += '.'
        if "tuplet" in modifiers and not self._in_context("tuplet"):
            result = "%s%s" % (self.tuplet(3, int(length)/2), result)
        if self.is_tying != None:
            result = "%s%s" % (self.tie(modifiers={"state": "check"}), result)
        if self.prev_note:
            result = "%s%s" % (self._get_indent(), result)
        self.prev_note = value
        return result 

    def rest(self, length, **kwargs):
        return '%sr%s' % (self._get_indent(), length)

    def time_notation(self, upper, lower, **kwargs):
        return '%s\\time %s/%s' % (self._get_indent(), upper, lower)

    def endingstart(self, *num, **kwargs):
        result = []
        self._enter_context(("ending", "#f"))
        self._indent_level += 1
        template = "%s\set Score.repeatCommands = #'((volta \"%s\"))%s" % (self._get_indent(), "%s", self._get_indent())
        if len(num) > 0:
            return template % num[0]
        return template % ""

    def endingend(self, **kwargs):
        self._in_endings = False
        if self._leave_context("ending"):
            return "%s\\set Score.repeatCommands = #'((volta #f))%s" % (self._get_indent(), self._get_indent())
        return ""

    def strike(self, *values, **modifiers):
        # TODO: Fix the parser to not do weird shit
        i = 0
        while not values[i]:
            i += 1
        if not modifiers:
            return self.grace(values[i])
        result = []
        if "half" in modifiers:
            # half strike OFF OF value
            result.append(values[i])
        result.append("C" if "light" in modifiers else self.strike_notes[values[i]])
        return self.build_embellishment(result)

    def gracestrike(self, gracenote, from_note, **modifiers):
        gnote = gracenote
        strike_note = self.strike_notes[from_note]
        if gracenote == "LG":
            gnote = "HG"
            strike_note = self.note_below(from_note)
        if "light" in modifiers:
            strike_note = "C"
        return self.build_embellishment([gnote, from_note, strike_note])

    def doublestrike(self, from_note, **modifiers):
        startnote = {"heavy": ["HG"],
            "thumb": ["HA"]}
        result = []
        for k in modifiers.keys():
            if k in startnote:
                result = startnote[k]
        drop_note = self.strike_notes[from_note]
        if "light" in modifiers:
            drop_note = "C"
        return self.build_embellishment(result + [from_note, drop_note, from_note])

    def triplestrike(self, from_note, **modifiers):
        result = []
        startnote = {"heavy": ["HG"],
            "thumb": ["HA"]}
        for (k, v) in startnote.items():
            if k in modifiers:
                result = v
        drop_note = self.strike_notes[from_note]
        if "light" in modifiers:
            drop_note = "C"
        if "half" not in modifiers:
            result.append(from_note)
        return self.build_embellishment(result + [drop_note, from_note, drop_note, from_note])

    def grace(self, value, **kwargs):
        return self.build_embellishment([value])

    def doublegrace(self, *values, **kwargs):
        return self.build_embellishment(values)

    def double(self, note, **modifiers):
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

    def throw(self, **modifiers):
        if "half" in modifiers:
            result = ["D", "C"]
        else:
            result = ["LG", "D", "C"]
        if "heavy" in modifiers:
            result.insert(0, "LG")
        return self.build_embellishment(result)


    def pele(self, note, **modifiers):
        result = []
        if 'thumb' in modifiers:
            result.append('HA')
        elif 'half' in modifiers:
            pass
        else:
            result.append('HG')
        result += [note, self.note_above(note, starting="E"), note]
        if 'low' in modifiers:
            result.append('LG')
        else:
            result.append(self.strike_notes[note])
        return self.build_embellishment(result)

    def tuplet(self, *args, **kwargs):
        if "start" in kwargs:
            self._enter_context(("tuplet", "}"))
            return "\\tuplet %s/%s {" % args
        return self._leave_context("tuplet")

    def tie(self, *_args, **modifiers):
        # Drop args, in case the tie specifies a note
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

    def birl(self, **modifiers):
        result = []
        if "half" in modifiers:
            pass
        elif "thumb" in modifiers:
            result.append("HA")
        elif "A" in modifiers:
            result.append("LA")
        elif "heavy" in modifiers:
            result.append("HG")
        return self.build_embellishment(result + ["LG", "LA", "LG"])

    def _start_modifier_helper(self, modifiers):
        if "heavy" in modifiers:
            return "HG"
        elif "thumb" in modifiers:
            return "HA"
        return None

    def _grip_helper(self, prev_note=None):
        mid_note = ["B"] if prev_note == "D" else ["D"]
        return ["LG"] + mid_note + ["LG"]

    def grip(self, *note, **modifiers):
        if len(note) == 0 or not note[0]:
            return self.build_embellishment(self._grip_helper(self.prev_note))
        if not modifiers and note[0] == "B":
            return self.build_embellishment(self._grip_helper("D"))
        result = []
        if "heavy" in modifiers:
            result.append('HG')
        elif "thumb" in modifiers:
            result.append('HA')
        return self.build_embellishment(result + [note[0], "LG", "D", "LG"])

    def dgrip(self):
        return self.build_embellishment(self._grip_helper("D"))

    def tarluath(self):
        return self.build_embellishment(self._grip_helper(self.prev_note) + ["E"])

    def dtarluath(self):
        return self.build_embellishment(self._grip_helper("D") + ["E"])

    def crunluath(self, **modifiers):
        return self.build_embellishment(["LG", "D", "LG", "E", "LA", "F", "LA"])

    def hiharin(self, **modifiers):
        return self.build_embellishment(["D", "LA", "LG", "LA", "LG"])

    def rodin(self):
        return self.build_embellishment(["LG", "B", "LG"])

    def cadence(self, *notes, **modifiers):
        builder = []
        if "fermata" in modifiers:
            # TODO: Shove a fermata on the cadence
            pass
        # TODO: Make the behavior consistent with what's expected
        patterns = ["", [8], [32, 8], [32,8,32]]
        patterned_notes = map("".join, zip(map(lambda x: self.notes[x], notes), patterns[len(notes)]))
        patterned_notes = zip(notes, patterns[len(notes)])
        return self.build_zipped_embellishment(patterned_notes)

    def darado(self, *args, **modifiers):
        result = []
        if "half" not in modifiers:
            result.append("LG")
        result += ["D", "LG", "C", "LG"]
        return self.build_embellishment(result)

    def edre(self, *values, **modifiers):
        # TODO: Fix this whole thing
        # edres depend on the next note, maybe?
        # On B, with edre("LG"), we should return "HG", "B", "LG", "D", "LG" apparently
        # I don't know
        result = []
        low_note = "LA" if len(values) == 0 else values[0]
        if "heavy" in modifiers:
            result.append("HG")
        elif "thumb" in modifiers:
            result.append("HA")
        result += ["E", low_note, "F", low_note]
        return self.build_embellishment(result)

    def dare(self, *values, **modifiers):
        result = ["F", "E", "HG", "E"]
        if "heavy" in modifiers:
            result.insert(0, "HG")
        elif "thumb" in modifiers:
            result.insert(0, "HA")
        return self.build_embellishment(result)

    def chedare(self, *values, **modifiers):
        result = ["F", "E", "HG", "E", "F", "E"]
        return self.build_embellishment(result)

    def endari(self, *values, **modifiers):
        result = ["E", "LA", "F", "LA"]
        return self.build_embellishment(result)

    def embari(self, *values, **modifiers):
        result = ["E", "LG", "F", "LG"]
        return self.build_embellishment(result)

    def _decode(self, note):
        'A note is either: "funcname" or ("funcname", [args])'
        fname = ""
        fargs = []
        fkwargs = {}
        try:
            if isinstance(note, str):
                fname = self._normalize(note)
            else:
                fname = note.note_type
                fargs = note.ordered_arguments
                fkwargs = note.modifiers
            if not isinstance(fargs, list):
                return getattr(self, fname)(fargs)
            if fkwargs:
                return getattr(self, fname)(*fargs, **fkwargs)
            return getattr(self, fname)(*fargs)
        except Exception as e:
            raise Exception("%s in %s with *%s **%s" % (str(e), fname, fargs, fkwargs))


    def _find_offset(self, time, notes, note_offset=0):
        time_count = time[0]
        time_denom = time[1]
        
        first_bar_index = 0
        prebar_notes = []
        for i, note in enumerate(notes):
            if note.get_type() == 'note':
                prebar_notes.append(note)
            elif note.get_type().endswith('end'):
                first_bar_index = i
                break

        def set_weight(note):
            note_denom = int(note.get_args()[1])
            base_value = time_denom / note_denom
            addl_value = 0
            if "dot" in note.modifiers:
                temp_val = base_value
                for x in range(note.modifiers["dot"]):
                    addl_value += 0.5 * temp_val
                    temp_val = temp_val / 2
            return base_value + addl_value

        prebar_count = reduce(lambda acc, x: acc + set_weight(x), prebar_notes, 0)

        offset = time_count - prebar_count

        offset_time_denom = time_denom
    
        while offset > 1 and 1 / offset > 1 and not offset.is_integer():
            offset *=2
            offset_time_denom *= 2

        return "\set Timing.measurePosition = #(ly:make-moment %d/%d)" % (offset, offset_time_denom)

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
            if not note or note == '' or note == "_ignore":
                continue
            if response := self._decode(note):
                result.append(response)
                if self.embellishment_fix:
                    result.append("%s\override Stem.direction = -1%s" % (self._get_indent(), self._get_indent()))
                    self.embellishment_fix = False
                    self.stem_reversed = True
                if not self.stem_reversed and self.prev_note:
                    result.insert(-1, "%s\override Stem.direction = -1%s" % (self._get_indent(), self._get_indent()))
                if note.note_type in ["repeatstart", "partstart", "time_notation"]:
                    time = self._curr_time
                    if note.note_type == "time_notation":
                        self._curr_time = tuple([int(t) for t in note.ordered_arguments])
                    if new_offset := self._find_offset(time, islice(tune.notes, i + 1, None)):
                        self.offset = new_offset
        return "".join(result)

    def from_tune(self, tune):
        self.__reset__()
        header = self._generate_header(tune)
        self._curr_time = tune.time
        if self._curr_time == (0,0):
            self._curr_time = (4,4)
        self.offset = self._find_offset(self._curr_time, tune.notes)
        music = self._generate_music(tune)
        return self.template.render({"header": header, "music": music})

    def __reset__(self):
        self.prev_note = ""
        self.embellishment_fix = False
        self.stem_reversed = False
        self.offset = ""
        self._context = []
        self.is_tying = None
        self._in_endings = None
        self._indent_level = 2
        self._curr_time = (0,0)

    def __init__(self):
        self.__reset__()
        self._indent_spaces = 4
        jinja_env = Environment(loader = PackageLoader('bpmusictransposer', 'templates'))
        self.template = jinja_env.get_template("base.ly.jinja")
