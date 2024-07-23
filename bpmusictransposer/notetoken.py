class NoteToken:
    def set_note_type(self, typename):
        self.note_type = typename

    def read_arguments(self, match):
        self.ordered_arguments += match.groups()
        self.keyword_arguments.update(match.groupdict())
        ordered_group_names = [k for k in self.keyword_arguments.keys()]
        ordered_group_names.sort(key=lambda x: match.span(x)[0])
        for (i, k) in enumerate(ordered_group_names):
            self.argument_indices[k] = i

    def translate_arguments(self, defs):
        arg_update = {}
        for (k, v) in self.keyword_arguments.items():
            converted = defs.get(v, v)
            arg_update[k] = converted
            i = self.argument_indices[k]
            self.ordered_arguments[i] = converted
        self.keyword_arguments.update(arg_update)

    def get_type(self):
        return self.note_type

    def get_args(self):
        return self.ordered_arguments

    def get_kwargs(self):
        return self.keyword_arguments

    def add_modifiers(self, modifiers):
        self.modifiers.update(modifiers)

    def set_args(self, values):
        self.ordered_arguments = values

    def set_arg(self, key, value, force=False): 
        if force or key not in self.keyword_arguments or self.keyword_arguments[key] == None:
            self.keyword_arguments[key] = value
            if key in self.argument_indices:
                self.ordered_arguments[self.argument_indices[key]] = value
            else:
                self.argument_indices[key] = len(self.ordered_arguments)
                self.ordered_arguments.append(value)
        
    def set_order(self, keys):
        self.ordered_arguments = []
        for (i, k) in enumerate(keys):
            self.argument_indices[k] = i
            self.ordered_arguments.append(self.keyword_arguments[k])

    def __eq__(self, other):
        if not isinstance(other, NoteToken):
            return False
        compare = ["note_type", "ordered_arguments", "argument_indices", "modifiers"]
        result = True
        for k in compare:
            result = result and getattr(self, k) == getattr(other, k)
        return result

    def __str__(self):
        return "%s(%s/%s, **%s)" % (self.note_type, self.ordered_arguments, self.keyword_arguments, self.modifiers)

    def __repr__(self):
        return self.__str__()

    def __init__(self, name=None):
        self.note_type = name

        self.ordered_arguments = []
        self.keyword_arguments = {}
        self.argument_indices = {}

        self.note_called_arguments = self.ordered_arguments

        self.modifiers = {}
