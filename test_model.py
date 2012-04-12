from model import *
import unittest

class TestModel(unittest.TestCase):

    def test_clause_number(self):
        a = Part('a', [1,2,3,4])
        clause = Clause(Indexed(a, -1), Comparator.eq, 1)

        self.assertTrue(clause.matches({'a': Indexed(a, 1)}))
        self.assertFalse(clause.matches({'a': Indexed(a, 0)}))
        self.assertFalse(clause.matches({'a': Indexed(a, 2)}))
        self.assertFalse(clause.matches({'a': Indexed(a, 3)}))

        clause = Clause(Indexed(a, -1), Comparator.eq, 4)
        self.assertTrue(clause.matches({'a': Indexed(a, 0)}))
        self.assertFalse(clause.matches({'a': Indexed(a, 1)}))

        clause = Clause(Indexed(a, -2), Comparator.neq, 4)
        self.assertTrue(clause.matches({'a': Indexed(a, 3)}))
        self.assertFalse(clause.matches({'a': Indexed(a, 1)}))
        
    def test_clause_indexed(self):
        a = Part('a', [1,2,3,4])
        b = Part('b', [1,2,3])

        clause = Clause(Indexed(a, -1), Comparator.eq, Indexed(b, 0))
        self.assertTrue(clause.matches({'a': Indexed(a, 1), 'b': Indexed(b, 0)}))
        self.assertFalse(clause.matches({'a': Indexed(a, 0), 'b': Indexed(b, 0)}))
        self.assertFalse(clause.matches({'a': Indexed(a, 1), 'b': Indexed(b, 2)}))

        clause = Clause(Indexed(a, 2), Comparator.eq, Indexed(b, 1))
        self.assertTrue(clause.matches({'a': Indexed(a, 2), 'b': Indexed(b, 2)}))

        clause = Clause(Indexed(a, 0), Comparator.neq, Indexed(b, 0))
        self.assertTrue(clause.matches({'a': Indexed(a, 1), 'b': Indexed(b, 0)}))
        self.assertFalse(clause.matches({'a': Indexed(a, 1), 'b': Indexed(b, 1)}))

    def test_can_alter(self):
        a = Part('a', [1,2,3,4])
        a.set_note_at(-1, 5)
        a.set_note_at(2, 6)
        self.assertEquals([1,2,6,5], a.notes)

        modifier = Modifier(Indexed(a, 1), 7)
        self.assertTrue(modifier.can_alter({'a': Indexed(a, 0)}))
        self.assertTrue(modifier.can_alter({'a': Indexed(a, 3)}))
        self.assertFalse(modifier.can_alter({'a': Indexed(a, 1)}))
        self.assertFalse(modifier.can_alter({'a': Indexed(a, 2)}))

    def test_alter(self):
        a = Part('a', [1,2,3,4])
        b = Part('b', [5,6,7])

        modifier = Modifier(Indexed(a, -2), 8)
        modifier.alter({'a': Indexed(a, 0)})
        self.assertEquals([1,2,8,4], a.notes)

        a.create_notes_copy()

        modifier = Modifier(Indexed(b, 0), Indexed(a, 1))
        modifier.alter({'a': Indexed(a, 1), 'b': Indexed(b, 2)})
        self.assertEquals([5,6,8], b.notes)

    def test_rule_apply_single(self):
        a = Part('a', [1,2,3,4])
        b = Part('b', [5,6,7])

        lhs = [Clause(Indexed(a, 0), Comparator.eq, 3)]
        rhs = [Modifier(Indexed(a, 1), 8)]
        rule = Rule(lhs, rhs)
        rule.apply({'a': Indexed(a, 1), 'b': Indexed(b, 2)})
        self.assertEquals([1,2,3,4], a.notes)
        rule.apply({'a': Indexed(a, 2), 'b': Indexed(b, 2)})
        self.assertEquals([1,2,3,8], a.notes)

    def test_rule_apply_overlapping(self):
        a = Part('a', [1,1,1,1,1])

        _ = PAUSE # for readability
        lhs = [Clause(Indexed(a, 0), Comparator.eq, 1)]
        rhs = [Modifier(Indexed(a, 0), 2), Modifier(Indexed(a, 1), _)]
        rule = Rule(lhs, rhs)
        rule.apply({'a': Indexed(a, 0)})
        self.assertEquals([2, _, 1, 1, 1], a.notes)
        rule.apply({'a': Indexed(a, 1)})
        self.assertEquals([2, _, 1, 1, 1], a.notes)
        rule.apply({'a': Indexed(a, 2)})
        self.assertEquals([2, _, 2, _, 1], a.notes)
        rule.apply({'a': Indexed(a, 3)})
        self.assertEquals([2, _, 2, _, 1], a.notes)
        rule.apply({'a': Indexed(a, 4)})
        self.assertEquals([2, _, 2, _, 1], a.notes)

    def test_engine_midi_notes(self):
        _ = PAUSE # for readability
        
        a = Part('a', [0, _, 1, _, 0, _, 3, _])
        b = Part('b', [0, 3, _])
        parts = [a, b]

        engine = Engine(parts, [])
        self.assertEquals(8, engine.iteration_length)
        midi_notes = engine.get_midi_notes()

        def f(notes, midi_note):
            ns = [n.note for n in midi_note]
            self.assertEquals(notes, ns)
            
        f([0, 0], midi_notes[0])
        f([3], midi_notes[1])
        f([1], midi_notes[2])
        f([0], midi_notes[3])
        f([0, 3], midi_notes[4])
        f([], midi_notes[5])
        f([3, 0], midi_notes[6])
        f([3], midi_notes[7])
        
    def test_engine_iterate_single(self):
        _ = PAUSE # for readability
        
        a = Part('a', [0, _, 1, _, 0, _, 3, _])
        b = Part('b', [0, 3, _])
        parts = [a, b]

        lhs = [Clause(Indexed(a, -1), Comparator.neq, _),
               Clause(Indexed(a, 0), Comparator.eq, _)]
        rhs = [Modifier(Indexed(a, -1), _),
               Modifier(Indexed(a, 0), Indexed(a, -1))]
        rule = Rule(lhs, rhs)
        rules = [rule]

        engine = Engine(parts, rules)
        engine.iterate()

        self.assertEquals(0, a.pointer)
        self.assertEquals(2, b.pointer)

        self.assertEquals([_, 0, _, 1, _, 0, _, 3], a.notes)
        self.assertEquals([0, 3, _], b.notes)


if __name__ == '__main__':
    unittest.main()
