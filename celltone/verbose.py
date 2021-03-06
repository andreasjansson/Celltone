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


import os
import textwrap
from model import Clause

DEFAULT_WIDTH = 80
SPACES = 5

width = DEFAULT_WIDTH

class Verbose(object):

    def __init__(self, verbosity = 1):
        self.verbosity = verbosity

    def print_parts(self, parts, iteration_length):
        find_width()
        if self.verbosity < 1:
            return

        for name in sorted(parts.keys()):
            print(PartFormatter(parts[name], iteration_length))
        print('')

    def print_log(self, items):
        find_width()
        if self.verbosity < 2:
            return

        for item in items:
            print(RuleFormatter(item, self.verbosity >= 3))
        print('')

class PartFormatter(object):

    def __init__(self, part, iteration_length):
        line = part.name + ': '
        for t in range(iteration_length):
            i = (part.pointer + t) % len(part.notes)
            if i == 0:
                line += '['
            else:
                line += ' '
            note = part.notes[i]
            if note == '_' or (note < 10 and note >= 0):
                line += ' '
            line += str(part.notes[i])
            if i == len(part.notes) - 1:
                line += ']'
            else:
                line += ','
            
        self.lines = wrap(line)

    def __str__(self):
        return '\n'.join(self.lines)

class RuleFormatter(object):

    def __init__(self, item, verbose = False):
        self.item = item
        self.verbose = verbose
        self.lines = []
        self.format()

    def format(self):
        self.format_rule()
        if self.verbose:
            self.lines += ['']
            self.format_clauses()
            self.lines += ['=====>', '']
            self.format_modifiers()

    def format_rule(self):
        rule = self.item.rule
        self.lines += wrap(str(rule))
        
    def format_clauses(self):
        self.format_list(self.item.rule.lhs, self.item.beat_before)

    def format_modifiers(self):
        self.format_list(self.item.rule.rhs, self.item.beat_after)

    def format_list(self, clauses, beat):
        pivot = self.item.pivot
        participants = {}
        for c in clauses:
            clause = Clause(c.subject, c.object, beat, pivot)
            name = clause.subject_part.name
            # beat is a copy, so we can do what we want with it
            indexed = beat[name]
            part = indexed.part
            if name not in participants:
                participants[name] = part
                part.involved_indices = []
            index = (clause.real_subject_index) % len(part.notes)
            part.involved_indices.append(index)
            if clause.object_indexed:
                index = (clause.real_object_index) % len(part.notes)
                part.involved_indices.append(index)

        for i, name in enumerate(sorted(participants.keys())):
            part = participants[name]
            # unique, sorted
            involved_indices = list(set(part.involved_indices))
            involved_indices.sort()
            self.format_part(part, involved_indices)
            if i < len(participants) - 1:
                print('')

    def format_part(self, part, involved_indices):
        pos = 0
        init = '%s = [' % part.name
        pos = len(init)
        spaces = ' ' * SPACES
        offset = 0
        while offset < len(part.notes):
            lines, offset = self.get_marked_part_lines(part, involved_indices,
                                                       offset, init)
            self.lines += lines
            if init != spaces:
                init = spaces

    def get_marked_part_lines(self, part, involved_indices, offset, init):
        part_line = init
        mark_line = ' ' * len(init)
        for i, note in enumerate(part.notes[offset:], offset):
            n = len(str(note))
            part_line += str(note)

            if i < len(part.notes) - 1:
                part_line += ',' # space inserted later, if we don't break line
            else:
                part_line += ']'

            if i in involved_indices:
                mark_line += '^'
            mark_line += ' ' * (len(part_line) - len(mark_line))

            if i < len(part.notes) - 2:
                next_len = len(part_line) + len(str(part.notes[i + 1]))
                if i + 1 < len(part.notes) - 1:
                    next_len += 1 # for the space that will get added
                next_len += 1 # for , or ]
                if next_len > width:
                    break

            if i < len(part.notes) - 1:
                part_line += ' '
                mark_line += ' '

        return ([part_line, mark_line], i + 1)

    def __str__(self):
        return '\n'.join(self.lines)
            

def wrap(text):
    '''
    wrap() is a wrapper around textwrap.wrap
    '''
    lines = textwrap.wrap(text, width, subsequent_indent = ' ' * SPACES,
                          break_on_hyphens = False)
    return lines
    

def find_width():
    global width
    size = os.popen('stty size 2> /dev/null', 'r').read()
    if not size or ' ' not in size:
        width = DEFAULT_WIDTH
    else:
        width = int(size.split()[1])

