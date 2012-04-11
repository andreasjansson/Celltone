class Part:

    PAUSE = '_'

    def __init__(self, name, notes):
        self.name = name
        self.notes = notes
        self.properties = {
            'channel': 0,
            'velocity' : 127,
            }
        self.pointer = 0
        self.altered = None
        self.reset_altered()

    def set_property(self, name, value):
        if name not in self.properties:
            raise Exception('Property undefined: ' + name)
        self.properties[name] = value

    def get_note_at(self, index):
        return self.notes[index % len(self.notes)]

    def set_note_at(self, index, note):
        self.notes[index % len(self.notes)] = note
        self.altered[index % len(self.notes)] = True

    def get_altered_at(self, index):
        return self.altered[index % len(self.notes)]

    def reset_altered(self):
        self.altered = [False] * len(self.notes)

class Clause:

    def __init__(self, indexed, comparator, subject):
        self.indexed = indexed
        self.comparator = comparator
        self.subject = subject

    def matches(self, beat):
        part = self.indexed.part
        current_index = beat[part.name].index
        note = part.get_note_at(current_index + self.indexed.index)

        if isinstance(self.subject, Indexed):
            current_subject_index = beat[self.subject.part.name].index
            subject_note = self.subject.part.get_note_at(current_subject_index +
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
            if not alter_item.can_alter():
                return
        for alter_item in rhs:
            name = alter_item.indexed.part.name
            alter_item.alter(beat)

class Indexed:

    def __init__(self, part, index):
        self.part = part
        self.index = index

class AlterItem:

    def __init__(self, indexed, subject):
        self.indexed = indexed
        self.subject = subject

    def can_alter(self, beat):
        part = self.indexed.part
        current_index = beat[part.name].index
        return not part.get_altered_at(current_index + self.indexed.index)

    def alter(self, beat):
        part = self.indexed.part
        current_index = beat[part.name].index
        part = self.indexed.part

        if isinstance(self.subject, Indexed):
            current_subject_index = beat[self.subject.part.name].index
            subject_note = self.subject.part.get_note_at(current_subject_index +
                                                         self.subject.index)
        else:
            subject_note = self.subject

        part.set_note_at(current_index + self.indexed.index, subject_note)

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
            part.reset_altered()

