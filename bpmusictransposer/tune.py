class Tune:
    def set_values(self, argobj):
        toplevel = ["title", "tunetype", "composer", "footer", "tempo", "time"]
        for (k, v) in argobj.items():
            if k in toplevel:
                self.__setattr__(k, v)
            else:
                self.miscparseinfo[k] = v

    def __init__(self):
        self.title = ""
        self.tunetype = ""
        self.composer = ""
        self.footer = ""
        self.tempo = 0
        self.time = (0,0)
        self.miscparseinfo = {}

        self.notes = []


    def __str__(self):
        return { "title": self.title, "time": "%d/%d" % self.time, "tunetype": self.tunetype, "composer": self.composer, "footer": self.footer, "tempo": self.tempo, "misc": self.miscparseinfo }.__str__()
