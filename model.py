from copy import copy

PAUSE = '_'

class Part:

    def __init__(self, name, notes):
        self.name = name
        self.notes = notes
        self.create_notes_copy()
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

    def get_note_copy_at(self, index):
        return self.notes_copy[index % len(self.notes)]

    def set_note_at(self, index, note):
        self.notes[index % len(self.notes)] = note
        self.altered[index % len(self.notes)] = True

    def get_altered_at(self, index):
        return self.altered[index % len(self.notes)]

    def reset_altered(self):
        self.altered = [False] * len(self.notes)

    def get_midi_note_at(self, index):
        note = self.notes[index % len(self.notes)]
        if note == PAUSE:
            return None
        return MidiNote(note, self.properties['channel'], self.properties['velocity'])

    def create_notes_copy(self):
        self.notes_copy = copy(self.notes)

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
        for clause in self.lhs:
            if not clause.matches(beat):
                return
        for modifier in self.rhs:
            if not modifier.can_alter(beat):
                return
        for modifier in self.rhs:
            name = modifier.indexed.part.name
            modifier.alter(beat)

class Indexed:

    def __init__(self, part, index):
        self.part = part
        self.index = index

class Modifier:

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
            subject_note = self.subject.part.get_note_copy_at(current_subject_index +
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

class MidiNote:

    def __init__(self, note, channel, velocity):
        self.note = int(note)
        self.channel = int(channel)
        self.velocity = int(velocity)

class Engine:

    def __init__(self, parts, rules):
        self.parts = parts
        self.iteration_length = reduce(lambda x, y: max(x, len(y.notes)), parts, 0)
        self.rules = rules

    def get_midi_notes(self):
        midi_notes = {}
        for i in range(self.iteration_length):
            midi_notes[i] = []
            for part in self.parts:
                midi_note = part.get_midi_note_at(part.pointer + i)
                if midi_note:
                    midi_notes[i].append(midi_note)
        return midi_notes

    def iterate(self):
        self.reset_altered()
        self.notes_read_copy()

        for rule in self.rules:
            for beat in self.beats():
                rule.apply(beat)

        self.update_pointers()

    def reset_altered(self):
        for part in self.parts:
            part.reset_altered()

    def beats(self):
        beats = []
        for i in range(self.iteration_length):
            beats.append({})
            for part in self.parts:
                index = (part.pointer + i) % len(part.notes)
                beats[i][part.name] = Indexed(part, index)
        return beats

    def notes_read_copy(self):
        for part in self.parts:
            part.create_notes_copy()

    def update_pointers(self):
        for part in self.parts:
            part.pointer = (part.pointer + self.iteration_length) % len(part.notes)

