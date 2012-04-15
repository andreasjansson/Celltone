from copy import copy, deepcopy
import threading

PAUSE = '_'

class Logger:

    def __init__(self):
        self.items = []

    def add(self, rule, beat_before, beat_after):
        self.items.append(LogItem(rule, beat_before, beat_after))

    def clear(self):
        self.items = []

class LogItem:
    def __init__(self, rule, beat_before, beat_after):
        self.rule = rule
        self.beat_before = beat_before
        self.beat_after = beat_after

logger = Logger()

class Config:

    def __init__(self):
        # defaults
        self.options = {
            'tempo': 120,
            'subdiv': 16,
            'iterlength': None
            }

        # pretty arbitrary upper limits
        self.boundaries = {
            'tempo': (1, 10000),
            'subdiv': (1, 10000),
            'iterlength' : (1, 10000),
            }

    def set(self, name, value):
        if name not in self.options:
            raise Exception('Unknown global option \'%s\'' % name)
        minimum, maximum = self.boundaries[name]
        if value < minimum:
            raise Exception('%s must be >= %d' % (name, minimum))
        if value > maximum:
            raise Exception('%s must be <= %d' % (name, maximum))
        self.options[name] = value

    def get(self, name):
        return self.options[name]

class Part:

    def __init__(self, name, notes):
        self.name = name
        self.notes = notes
        self.create_notes_copy()

        # defaults
        self.properties = {
            'channel': 0,
            'velocity': 100,
            'octava' : 4,
            }
        self.prop_bounds = {
            'channel': (0, 127),
            'velocity': (0, 127),
            'octava': (0, 10),
            }
        self.pointer = 0
        self.altered = None
        self.reset_altered()

    def set_property(self, name, value):
        if name not in self.properties:
            raise Exception('Undefined property \'%s\'' % name)
        minimum, maximum = self.prop_bounds[name]
        if value < minimum:
            raise Exception('%s must be >= %d' % (name, minimum))
        if value > maximum:
            raise Exception('%s must be <= %d' % (name, maximum))
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
        note = note + 12 * self.properties['octava']
        return MidiNote(note, self.properties['channel'], self.properties['velocity'])

    def create_notes_copy(self):
        '''
        Rules should depend on the state of the part before
        the iteration, hence we copy the notes and use them
        in the clauses and modifiers.
        '''
        self.notes_copy = copy(self.notes)

    def __str__(self):
        return '%s = [%s]' % (self.name, ', '.join(map(str, self.notes)))

class Clause:

    def __init__(self, indexed, comparator, subject):
        self.indexed = indexed
        self.comparator = comparator
        self.subject = subject

    def matches(self, beat):
        part = self.indexed.part
        current_index = beat[part.name].index
        note = part.get_note_copy_at(current_index + self.indexed.index)

        if isinstance(self.subject, Indexed):
            current_subject_index = beat[self.subject.part.name].index
            subject_note = self.subject.part.get_note_copy_at(current_subject_index +
                                                     self.subject.index)
        else:
            subject_note = self.subject
        
        return self.comparator.compare(note, subject_note)

    def __str__(self):
        return '%s %s %s' % (str(self.indexed), str(self.comparator), str(self.subject))

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

        beat_before = deepcopy(beat)

        for modifier in self.rhs:
            name = modifier.indexed.part.name
            modifier.alter(beat)

        logger.add(self, beat_before, deepcopy(beat))

    def __str__(self):
        lhs = ', '.join(map(str, self.lhs))
        rhs = ', '.join(map(str, self.rhs))
        return '{%s} => {%s}' % (lhs, rhs)

class Indexed:

    def __init__(self, part, index):
        self.part = part
        self.index = index

    def __str__(self):
        return '%s[%d]' % (self.part.name, self.index)

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

    def __str__(self):
        if self.indexed == self.subject:
            return str(self.indexed)
        return '%s = %s' % (str(self.indexed), str(self.subject))

class Comparator:
    def compare(self, note1, note2):
        raise NotImplementedError()

class CompEQ(Comparator):
    def compare(self, note1, note2):
        return note1 == note2
    def __str__(self):
        return '=='

class CompNEQ(Comparator):
    def compare(self, note1, note2):
        return note1 != note2
    def __str__(self):
        return '!='
    
class CompLT(Comparator):
    def compare(self, note1, note2):
        if note1 == PAUSE:
            note1 = float("-inf")
        if note2 == PAUSE:
            note2 = float("-inf")
        return note1 < note2
    def __str__(self):
        return '<'

class CompLTE(Comparator):
    def compare(self, note1, note2):
        return Comparator.eq(note1, note2) or Comparator.lt(note1, note2)
    def __str__(self):
        return '<='

class CompGT(Comparator):
    def compare(self, note1, note2):
        if note1 == PAUSE:
            note1 = float("-inf")
        if note2 == PAUSE:
            note2 = float("-inf")
        return note1 > note2
    def __str__(self):
        return '>'

class CompGTE(Comparator):
    def compare(self, note1, note2):
        return Comparator.eq(note1, note2) or Comparator.gt(note1, note2)
    def __str__(self):
        return '>='

class MidiNote:

    def __init__(self, note, channel, velocity):
        self.note = int(note)
        self.channel = int(channel)
        self.velocity = int(velocity)


class Engine:

    def __init__(self, parts, rules):
        self.parts = parts
        self.iteration_length = reduce(lambda x, y: max(x, len(y.notes)), parts.values(), 0)
        self.rules = rules
        self.original_parts = deepcopy(parts)

    def get_midi_notes(self):
        midi_notes = []
        for i in range(self.iteration_length):
            midi_notes.append([])
            for part in self.parts.values():
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
        for part in self.parts.values():
            part.reset_altered()

    def beats(self):
        beats = []
        for i in range(self.iteration_length):
            beats.append({})
            for part in self.parts.values():
                index = (part.pointer + i) % len(part.notes)
                beats[i][part.name] = Indexed(part, index)
        return beats

    def notes_read_copy(self):
        for part in self.parts.values():
            part.create_notes_copy()

    def update_pointers(self):
        for part in self.parts.values():
            part.pointer = (part.pointer + self.iteration_length) % len(part.notes)

    def reset_parts(self):
        self.parts = self.original_parts
