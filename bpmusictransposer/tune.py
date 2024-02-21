class Tune:
    def get_value_names(self):
        return ["title", "tunetype", "composer", "tempo", "time"]

    def set_values(self, argobj):
        for (k, v) in argobj.items():
            if k in self.get_value_names():
                self.__setattr__(k, v.ordered_arguments[0])
            else:
                self.miscparseinfo[k] = v

    def __init__(self):
        self.title = ""
        self.tunetype = ""
        self.composer = ""
        self.tempo = 0
        self.time = (0,0)
        self.miscparseinfo = {}

        self.notes = []


    def __str__(self):
        return { "title": self.title, "time": "%d/%d" % self.time, "tunetype": self.tunetype, "composer": self.composer, "tempo": self.tempo, "misc": self.miscparseinfo }.__str__()
