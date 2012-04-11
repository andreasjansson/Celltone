class Part:

    def __init__(self, name, notes):
        self.name = name
        self.notes = notes
        self.properties = {
            'channel': 0,
            'velocity' : 127,
            }
        self.pointer = 0
        self.altered = False

    def set_property(self, name, value):
        if name not in self.properties:
            raise Exception('Property undefined: ' + name)
        self.properties[name] = value

    def note_at(self, index):
        return self.notes[index % len(self.notes)]

class Pause:
    pass

class Clause:

    def __init__(self, indexed, comparator, subject):
        self.indexed = indexed
        self.comparator = comparator
        self.subject = subject

    def matches(self, beat):
        name = self.indexed.part.name
        if name not in beat:
            return False

        current_index = beat[name].index
        part = self.indexed.part
        note = part.note_at(current_index + self.indexed.index)

        if isinstance(self.subject, Indexed):
            current_subject_index = beat[self.subject.part.name].index
            subject_note = self.subject.part.note_at(current_subject_index +
                                                     self.subject.index)
        else:
            subject_note = self.subject
        
        return self.comparator(note, subject_note)

class Rule:

    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def apply(self, beat):
        for clause in lhs:
            if not clause.matches(beat):
                return
        for alter_item in rhs:
            name = alter_item.indexed.part.name
            part = beat[name].part
            alter_item.alter(part)

class Indexed:

    def __init__(self, part, index):
        self.part = part
        self.index = index

class AlterItem:

    def __init__(self, indexed, subject):
        self.indexed = indexed
        self.subject = subject

class Comparator:

    @staticmethod
    def eq(note1, note2):
        return note1 == note2

    @staticmethod
    def neq(note1, note2):
        return note1 != note2

class Polyphony:

    def __init__(self, parts, iteration_length):
        self.parts = parts
        self.iteration_length = iteration_length

    def reset_altered(self):
        for part in self.parts:
            part.altered = False

