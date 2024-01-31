from functools import reduce

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
                "clefc": "\clef treble",
                "sharpc": "",
                "sharpf": "",
                "repeatstart": '\\repeat volta 2 {',
                "repeatend": '}\r',
                "lineend": '\\bar "|"\r\\break',
                "tie": "~"
            }
    func_translation = {
                "partstart": "bar",
                "partend": "bar",
                "barstart": "bar",
                "barend": "bar"
            }

    def bar(self, bartype):
        barval = '\\bar "%s"'
        barvals = { "partstart": "|.",
                    "partend": ".|",
                    "barstart": "|",
                    "barend": "|"
                }
        nobreak = ["barstart", "barend"]
        result = barval % barvals[bartype]
        if self.offset:
            result = '%s \r%s' % (result, self.offset)
            self.offset = None
        elif bartype in nobreak:
            result = "%s\r        \\noBreak" % result

        return '%s\r        ' % result

    def __getattr__(self, name):
        def method(*args):
            if name in self.simple_translation:
                return self.simple_translation[name]
            elif name in self.func_translation:
                return getattr(self, self.func_translation[name])(name)
            raise AttributeError("'%s' has no attribute '%s'" % (self.__class__.__name__, name))
        return method

    def build_embellishment(self, notes):
        if len(notes) == 1:
            return "\grace { %s16 }" % self.notes[notes[0]]
        return "\grace { %s16 %s }" % (self.notes[notes[0]], ' '.join(map(lambda n : self.notes[n], notes[1:])))

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
        return 'a_"%s"' % note

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

    def note(self, value, length, modifiers=None):
        self.prev_note = value
        result = "%s%d" % (self.notes[value], int(length))
        if modifiers and "dot" in modifiers:
            for x in range(0, modifiers["dot"]):
                result += '.'
        if self.is_tying == 0:
            self.is_tying = 1
        elif self.is_tying:
            result = "~ %s" % result
        return result

    def time_notation(self, upper, lower):
        return '\\time %s/%s' % (upper, lower)

    def strike(self, value, modifier={}):
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

    def double(self, note, modifier = {}):
        doubling = []
        if not modifier and note != "HA":
            doubling.append('HG')
        elif "thumb" in modifier:
            doubling.append('HA')
        elif "half" in modifier:
            pass
        if note in ["HA", "HG"]:
            return self.build_embellishment(doubling + [self.note_below(note)])
        return self.build_embellishment(doubling + [note, self.note_above(note)])

    def throw(self):
        return self.build_embellishment(["LG", "D", "C"])

    def nlets(self, *args, **kwargs):
        print(args)
        return ''

    def tie(self, modifiers={}):
        if 'state' in modifiers:
            if modifiers['state'] == 'start':
                self.is_tying = 0
            elif modifiers['state'] == 'end' and self.is_tying != None:
                self.is_tying == None
            else:
                return '~'
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

    def _embellishments(self):
        return """
        lgdouble = \grace {g''16 g' d'' }
        adouble = \grace {g''16 a' d'' }
        bdouble = \grace {g''16 b' d'' }
        cdouble = \grace {g''16 c'' d'' }
        ddouble = \grace {g''16 d'' e'' }
        edouble = \grace {g''16 e'' f'' }
        fdouble = \grace {g''16 f'' g'' }
        gdouble = \grace {a''16 g'' f'' }
        hadouble = \grace {a''16 g''}
        lghalf = \grace { g'16 d'' }
        ahalf = \grace { a'16 d'' }
        bhalf = \grace { b'16 d'' }
        chalf = \grace { c''16 d'' }
        dhalf = \grace { d''16 e'' }
        ehalf = \grace { e''16 f'' }
        fhalf = \grace { f''16 g'' }
        ghalf = \grace { g''16 f'' }
        grip = \grace { g'16 d'' g' }
        dgrip = \grace { g'16 b' g' }
        throw = \grace { g'16 d'' c'' }
        taorluath = \grace { g'16 d'' g' e'' }
        dtaorluath = \grace { g'16 b' g' e'' }
        birl = \grace { a'16 g' a' g' }
        hbirl = \grace { a''16 a' g' a' g' }
        abirl = \grace { g'16 a' g' }
        hdstrike = \grace { g''16 d'' g' }
        dhpshake = \grace { g''16 d'' e'' d'' c'' }
        chpshake = \grace { g''16 c'' e'' c'' g' }
        darado = \grace { g'16 e'' g' d'' g' }
        """

    def _decode(self, note):
        'A note is either: "funcname" or ("funcname", [args])'
        fname = ""
        fargs = []
        if isinstance(note, str):
            fname = self._normalize(note)
        else:
            fname = note[0]
            fargs = note[1]
            if isinstance(fargs, tuple):
                fargs = [self._normalize(n) for n in fargs]
        if not isinstance(fargs, list):
            return getattr(self, fname)(fargs)
        return getattr(self, fname)(*fargs)

    def _find_offset(self, time, notes, note_offset=0):
        time_count = time[0]
        time_denom = time[1]
        
        for i in range(0, len(notes)):
            if isinstance(notes[i], str) and notes[i].endswith('end'):
                first_bar_index = i
                break

        prebar_notes = filter(lambda x : x[0] == 'note', notes[0:first_bar_index])
        
        def set_weight(note):
            note_denom = int(note[1])
            base_value = time_denom / note_denom
            addl_value = 0
            if len(note) == 3:
                temp_val = base_value
                for x in range(note[2]["dot"]):
                    addl_value += 0.5 * temp_val
                    temp_val = temp_val / 2
            return base_value + addl_value

        offset = time_count - reduce(lambda acc, x: acc + set_weight(x[1]), prebar_notes, 0)

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
        return " ".join([ self._decode(note) for note in filter(lambda x : x, tune.notes) ])

    def from_tune(self, tune):
        header = self._generate_header(tune)
        self.offset = self._find_offset(tune.time, tune.notes)
        music = self._generate_music(tune)
        # TODO: Read ahead to get the correct start point
        return ("""\\version "2.20.0"
\score {
    \header {
        %s
    }
    
    \layout {
        indent = 0\cm
    }
    \\absolute {
        \override Stem.neutral-direction = -1
        \override Stem.direction = -1
        %s
    }
}
        """ % (header, music)).strip()

    def __init__(self):
        self.prev_note = ""
        self.offset = ""
        self.is_tying = None
