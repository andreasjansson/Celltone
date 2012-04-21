# Celltone - Generative music composition using cellular automata
# Copyright (C) 2012   andreas@jansson.me.uk
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at
# your option) any later version.
# 
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# 

# TODO: profiling/optimisation

from copy import copy, deepcopy
import threading

PAUSE = '_'

class Logger(object):

    def __init__(self):
        self.items = []

    def add(self, log_item):
        self.items.append(log_item)

    def clear(self):
        self.items = []

class RuleLog(object):
    def __init__(self, rule, pivot, beat_before, beat_after):
        self.rule = rule
        self.pivot = pivot
        self.beat_before = beat_before
        self.beat_after = beat_after

logger = Logger()

class Config(object):

    def __init__(self):
        # defaults
        self.options = {
            'tempo': 120,
            'subdiv': 16,
            'iterlength': None,
            'partorder': None,
            }

        # pretty arbitrary upper limits
        self.boundaries = {
            'tempo': (1, 10000),
            'subdiv': (1, 10000),
            'iterlength': (1, 10000),
            'partorder': None,
            }

    def set(self, name, value):
        if name not in self.options:
            raise Exception('Unknown global option \'%s\'' % name)
        if self.boundaries[name]:
            minimum, maximum = self.boundaries[name]
            if value < minimum:
                raise Exception('%s must be >= %d' % (name, minimum))
            if value > maximum:
                raise Exception('%s must be <= %d' % (name, maximum))
        self.options[name] = value

    def get(self, name):
        return self.options[name]

class Part(object):

    def __init__(self, name, notes):
        self.name = name
        self.notes = notes
        self.original_notes = copy(notes)
        self.create_notes_copy()

        # defaults
        self.properties = {
            'channel': 0,
            'velocity': 100,
            'octava' : 4,
            'transpose': 0,
            }
        self.prop_bounds = {
            'channel': (0, 127),
            'velocity': (0, 127),
            'octava': (0, 10),
            'transpose': (-127, 127),
            }
        self.pointer = 0
        self.altered = None
        self.reset_altered()
        self.next_part = self.prev_part = None

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
        from cellmidi import MidiNote
        note = self.notes[index % len(self.notes)]
        if note == PAUSE:
            return None
        note = note + self.properties['transpose'] + 12 * self.properties['octava']
        return MidiNote(note, self.properties['channel'], self.properties['velocity'])

    def create_notes_copy(self):
        '''
        Rules should depend on the state of the part before
        the iteration, hence we copy the notes and use them
        in the conditions and modifiers.
        '''
        self.notes_copy = copy(self.notes)

    # TODO: make this O(1)
    def other_part_at(self, index):
        '''
        Naive pointer implementation.
        '''
        if index == 0:
            return self
        if index > 0:
            return self.next_part.other_part_at(index - 1)
        if index < 0:
            return self.prev_part.other_part_at(index + 1)

    def __str__(self):
        return '%s = [%s]' % (self.name, ', '.join(map(str, self.notes)))

class Clause(object):
    '''
    A clause represents the state of a condition or a modifier
    at one particular beat, on one pivot part. In a matrix, this
    would be a cell.
    '''

    def __init__(self, subject, object, beat, pivot):
        self.subject = subject
        self.object = object
        self.beat = beat
        self.pivot = pivot

        if isinstance(self.subject, Indexed):
            self.subject_indexed = self.subject
        else: # AnyIndexed
            self.subject_indexed = self.subject.bind(pivot)
        self.subject_part = self.subject_indexed.part
        current_index = beat[self.subject_part.name].index
        self.real_subject_index = self.subject_indexed.index + current_index
        self.subject_note = self.subject_part.get_note_copy_at(self.real_subject_index)

        self.object_indexed = None
        if isinstance(self.object, Indexed) or isinstance(self.object, AnyIndexed):
            if isinstance(self.object, Indexed):
                self.object_indexed = self.object
            else:
                self.object_indexed = self.object.bind(pivot)
            current_object_index = beat[self.object_indexed.part.name].index
            self.real_object_index = self.object_indexed.index + current_index
            self.object_part = self.object_indexed.part
            self.object_note = self.object_part.get_note_copy_at(self.real_object_index)
        else:
            self.object_note = self.object

class Condition(object):

    def __init__(self, subject, comparator, object):
        self.subject = subject
        self.comparator = comparator
        self.object = object

    def matches(self, beat, pivot):
        clause = Clause(self.subject, self.object, beat, pivot)
        return self.comparator.compare(clause.subject_note, clause.object_note)

    def __str__(self):
        return '%s %s %s' % \
            (str(self.subject), str(self.comparator), str(self.object))

class Modifier(object):

    def __init__(self, subject, object):
        self.subject = subject
        self.object = object

    def can_alter(self, beat, pivot):
        clause = Clause(self.subject, self.object, beat, pivot)
        return not clause.subject_part.get_altered_at(clause.real_subject_index)

    def alter(self, beat, pivot):
        clause = Clause(self.subject, self.object, beat, pivot)
        clause.subject_part.set_note_at(clause.real_subject_index, clause.object_note)

    def __str__(self):
        if self.subject == self.object:
            return str(self.subject)
        return '%s = %s' % (str(self.subject), str(self.object))

class Rule(object):

    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def apply(self, beat, pivot):
        for condition in self.lhs:
            if not condition.matches(beat, pivot):
                return
        # TODO: see if faster to run can_alter before matching
        for modifier in self.rhs:
            if not modifier.can_alter(beat, pivot):
                return

        beat_before = deepcopy(beat)

        for modifier in self.rhs:
            modifier.alter(beat, pivot)

        logger.add(RuleLog(self, pivot, beat_before, deepcopy(beat)))

    def __str__(self):
        lhs = ', '.join(map(str, self.lhs))
        rhs = ', '.join(map(str, self.rhs))
        return '{%s} => {%s}' % (lhs, rhs)

class Indexed(object):

    def __init__(self, part, index):
        self.part = part
        self.index = index

    def __str__(self):
        return '%s[%d]' % (self.part.name, self.index)

class AnyIndexed(object):

    def __init__(self, part_index, index):
        self.part_index = part_index
        self.index = index

    def bind(self, bind_part):
        part = bind_part.other_part_at(self.part_index)
        return Indexed(part, self.index)

    def __str__(self):
        return '<%d>[%d]' % (self.part_index, self.index)

class Comparator(object):
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
        return CompEQ().compare(note1, note2) or CompLT().compare(note1, note2)
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
        return CompEQ().compare(note1, note2) or CompGT().compare(note1, note2)
    def __str__(self):
        return '>='

class Engine(object):

    def __init__(self, parts, rules, part_order, config):

        self.parts = parts

        iterlength = config.get('iterlength')
        if iterlength is None:
            self.iteration_length = self.longest_part_length()
        else:
            self.iteration_length = iterlength

        self.rules = rules

        if config.get('partorder'):
            part_order = config.get('partorder')
        
        link_parts(part_order)
        self.part_order = part_order

    def longest_part_length(self):
        return reduce(lambda x, y: max(x, len(y.notes)), self.parts.values(), 0)

    def update_parts(self, parts):
        deleted = self.parts.keys()
        for name, part in parts.iteritems():
            deleted = filter(lambda x: x != name, deleted)
            if name not in self.parts or part.notes != self.parts[name].original_notes:
                self.parts[name] = part
            self.parts[name].properties = part.properties
        for name in deleted:
            del parts[name]

    def update_rules(self, rules):
        self.rules = rules

    def update_part_order(self, part_order):
        def part_name(part):
            return part.name
        if map(part_name, part_order) != (part_name, self.part_order):
            new_part_order = []
            for part in part_order:
                new_part_order.append(self.parts[part.name])
            self.part_order = new_part_order
            link_parts(self.part_order)
    
    def update_config(self, config):
        iterlength = config.get('iterlength')
        if iterlength is None:
            self.iteration_length = self.longest_part_length()
        else:
            self.iteration_length = iterlength

    def get_midi_notes(self):
        '''
        Returns a list of time steps, each element being a list of notes.
        '''
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

        # Rules are applied for each part as a pivot, for each beat.
        # TODO: optimise
        for rule in self.rules:
            for pivot in self.part_order:
                for beat in self.beats():
                    rule.apply(beat, pivot)

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


def link_parts(part_order):
    for i, part in enumerate(part_order):
        part.next_part = part_order[(i + 1) % len(part_order)]
        part.prev_part = part_order[(i - 1) % len(part_order)]
