import sys
import sys, os 
sys.path.append('..')
from celltone.celltone import Celltone
import celltone.model
import celltone.parser
import unittest

class TestHighlevel(unittest.TestCase):

    def test_anyindexed(self):

        code = '''
a = [1, _, _]
b = [_, _]
c = [1, _, _, _]

a.channel = 0
b.channel = 1
c.channel = 2

a.octava = 0
b.octava = 0
c.octava = 0

{<0>[0] == <1>[0], <0>[0] == 1} => {<0>[0] = _, <2>[0] = 1}
'''

        ct = Celltone(code)
        midi_notes = ct.engine.get_midi_notes()
        m = midi_map(midi_notes)
        self.assertEquals([{0: 1, 2: 1}, {}, {}, {0: 1}], m)

        ct.engine.iterate()
        midi_notes = ct.engine.get_midi_notes()
        m = midi_map(midi_notes)
        self.assertEquals([{1: 1}, {}, {0: 1, 1: 1}, {}], m)

        ct.engine.iterate()
        midi_notes = ct.engine.get_midi_notes()
        m = midi_map(midi_notes)
        self.assertEquals([{1: 1}, {}, {1: 1, 2: 1}, {}], m)
    
def midi_map(midi_notes):
    m = []
    for i, notes in enumerate(midi_notes):
        m.append({})
        for note in notes:
            m[i][note.channel] = note.note

    return m

if __name__ == '__main__':
    unittest.main()
