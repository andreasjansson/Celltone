import sys
import sys, os 
sys.path.append('..')
from celltone.model import *
import unittest

class TestModel(unittest.TestCase):

    def test_comparators(self):
        _ = PAUSE
        self.assertTrue(CompLT().compare(_, 0))
        self.assertTrue(CompLT().compare(_, -100))
        self.assertTrue(CompLTE().compare(_, 1))
        self.assertTrue(CompGT().compare(0, _))
        self.assertTrue(CompGT().compare(-100, _))
        self.assertTrue(CompGTE().compare(1, _))
        self.assertFalse(CompLT().compare(0, _))

    def test_condition_indexed_number(self):
        a = Part('a', [1,2,3,4])
        cond = Condition(Indexed(a, -1), CompEQ(), 1)

        self.assertTrue(cond.matches({'a': Indexed(a, 1)}, None))
        self.assertFalse(cond.matches({'a': Indexed(a, 0)}, None))
        self.assertFalse(cond.matches({'a': Indexed(a, 2)}, None))
        self.assertFalse(cond.matches({'a': Indexed(a, 3)}, None))

        cond = Condition(Indexed(a, -1), CompEQ(), 4)
        self.assertTrue(cond.matches({'a': Indexed(a, 0)}, None))
        self.assertFalse(cond.matches({'a': Indexed(a, 1)}, None))

        cond = Condition(Indexed(a, -2), CompNEQ(), 4)
        self.assertTrue(cond.matches({'a': Indexed(a, 3)}, None))
        self.assertFalse(cond.matches({'a': Indexed(a, 1)}, None))

    def test_condition_indexed_indexed(self):
        a = Part('a', [1,2,3,4])
        b = Part('b', [1,2,3])

        cond = Condition(Indexed(a, -1), CompEQ(), Indexed(b, 0))
        self.assertTrue(cond.matches({'a': Indexed(a, 1), 'b': Indexed(b, 0)}, None))
        self.assertFalse(cond.matches({'a': Indexed(a, 0), 'b': Indexed(b, 0)}, None))
        self.assertFalse(cond.matches({'a': Indexed(a, 1), 'b': Indexed(b, 2)}, None))

        cond = Condition(Indexed(a, 2), CompEQ(), Indexed(b, 1))
        self.assertTrue(cond.matches({'a': Indexed(a, 2), 'b': Indexed(b, 2)}, None))

        cond = Condition(Indexed(a, 0), CompNEQ(), Indexed(b, 0))
        self.assertTrue(cond.matches({'a': Indexed(a, 1), 'b': Indexed(b, 0)}, None))
        self.assertFalse(cond.matches({'a': Indexed(a, 1), 'b': Indexed(b, 1)}, None))

    def test_condition_indexed_anyindexed(self):
        a = Part('a', [1,2,3,4])
        b = Part('b', [1,2,3])

        link_parts([a, b])
        cond = Condition(Indexed(a, -1), CompEQ(), AnyIndexed(1, 0))
        self.assertTrue(cond.matches({'a': Indexed(a, 1), 'b': Indexed(b, 0)}, a))
        self.assertFalse(cond.matches({'a': Indexed(a, 0), 'b': Indexed(b, 0)}, b))
        self.assertFalse(cond.matches({'a': Indexed(a, 1), 'b': Indexed(b, 2)}, a))

        cond = Condition(Indexed(a, 2), CompEQ(), AnyIndexed(0, 1))
        self.assertTrue(cond.matches({'a': Indexed(a, 2), 'b': Indexed(b, 2)}, b))

        cond = Condition(Indexed(a, 0), CompNEQ(), AnyIndexed(-1, 0))
        self.assertTrue(cond.matches({'a': Indexed(a, 1), 'b': Indexed(b, 0)}, a))
        self.assertFalse(cond.matches({'a': Indexed(a, 1), 'b': Indexed(b, 1)}, b))

    def test_condition_anyindexed_number(self):
        a = Part('a', [1,2,3])
        b = Part('b', [2,3,4,1])

        link_parts([a, b])
        cond = Condition(AnyIndexed(0, 1), CompEQ(), 1)
        self.assertTrue(cond.matches({'a': Indexed(a, 2), 'b': Indexed(b, 0)}, a))
        self.assertFalse(cond.matches({'a': Indexed(a, 1), 'b': Indexed(b, 0)}, a))
        self.assertFalse(cond.matches({'a': Indexed(a, 0), 'b': Indexed(b, 0)}, b))
        self.assertTrue(cond.matches({'a': Indexed(a, 2), 'b': Indexed(b, 2)}, b))

    def test_condition_anyindexed_indexed(self):
        a = Part('a', [1,2,3])
        b = Part('b', [2,3,4,1])

        cond = Condition(AnyIndexed(0, 1), CompEQ(), Indexed(a, 1))
        self.assertTrue(cond.matches({'a': Indexed(a, 0), 'b': Indexed(b, 0)}, a))
        self.assertTrue(cond.matches({'a': Indexed(a, 0), 'b': Indexed(b, 2)}, a))
        self.assertTrue(cond.matches({'a': Indexed(a, 2), 'b': Indexed(b, 0)}, a))
        self.assertFalse(cond.matches({'a': Indexed(a, 0), 'b': Indexed(b, 0)}, b))
        self.assertTrue(cond.matches({'a': Indexed(a, 2), 'b': Indexed(b, 2)}, b))

    def test_condition_anyindexed_anyindexed(self):
        I = Indexed

        a = Part('a', [1,2,3])
        b = Part('b', [2,3,4,1])
        c = Part('c', [4,5,1])

        link_parts([a, b, c])
        cond = Condition(AnyIndexed(0, 1), CompEQ(), AnyIndexed(1, 0))
        self.assertTrue(cond.matches({'a': I(a, 0), 'b': I(b, 0), 'c': I(c, 1)}, a))
        self.assertTrue(cond.matches({'a': I(a, 2), 'b': I(b, 1), 'c': I(c, 0)}, b))
        self.assertTrue(cond.matches({'a': I(a, 0), 'b': I(b, 1), 'c': I(c, 1)}, c))
        self.assertFalse(cond.matches({'a': I(a, 0), 'b': I(b, 1), 'c': I(c, 2)}, c))

    def test_can_alter(self):
        a = Part('a', [1,2,3,4])
        a.set_note_at(-1, 5)
        a.set_note_at(2, 6)
        self.assertEquals([1,2,6,5], a.notes)

        modifier = Modifier(Indexed(a, 1), 7)
        self.assertTrue(modifier.can_alter({'a': Indexed(a, 0)}, None))
        self.assertTrue(modifier.can_alter({'a': Indexed(a, 3)}, None))
        self.assertFalse(modifier.can_alter({'a': Indexed(a, 1)}, None))
        self.assertFalse(modifier.can_alter({'a': Indexed(a, 2)}, None))

    def test_alter(self):
        a = Part('a', [1,2,3,4])
        b = Part('b', [5,6,7])

        modifier = Modifier(Indexed(a, -2), 8)
        modifier.alter({'a': Indexed(a, 0)}, None)
        self.assertEquals([1,2,8,4], a.notes)

        a.create_notes_copy()

        modifier = Modifier(Indexed(b, 0), Indexed(a, 1))
        modifier.alter({'a': Indexed(a, 1), 'b': Indexed(b, 2)}, None)
        self.assertEquals([5,6,8], b.notes)

    def test_rule_apply_single(self):
        a = Part('a', [1,2,3,4])
        b = Part('b', [5,6,7])

        lhs = [Condition(Indexed(a, 0), CompEQ(), 3)]
        rhs = [Modifier(Indexed(a, 1), 8)]
        rule = Rule(lhs, rhs)
        rule.apply({'a': Indexed(a, 1), 'b': Indexed(b, 2)}, None)
        self.assertEquals([1,2,3,4], a.notes)
        rule.apply({'a': Indexed(a, 2), 'b': Indexed(b, 2)}, None)
        self.assertEquals([1,2,3,8], a.notes)

    def test_rule_apply_overlapping(self):
        a = Part('a', [1,1,1,1,1])

        _ = PAUSE # for readability
        lhs = [Condition(Indexed(a, 0), CompEQ(), 1)]
        rhs = [Modifier(Indexed(a, 0), 2), Modifier(Indexed(a, 1), _)]
        rule = Rule(lhs, rhs)
        rule.apply({'a': Indexed(a, 0)}, None)
        self.assertEquals([2, _, 1, 1, 1], a.notes)
        rule.apply({'a': Indexed(a, 1)}, None)
        self.assertEquals([2, _, 1, 1, 1], a.notes)
        rule.apply({'a': Indexed(a, 2)}, None)
        self.assertEquals([2, _, 2, _, 1], a.notes)
        rule.apply({'a': Indexed(a, 3)}, None)
        self.assertEquals([2, _, 2, _, 1], a.notes)
        rule.apply({'a': Indexed(a, 4)}, None)
        self.assertEquals([2, _, 2, _, 1], a.notes)

    def test_engine_midi_notes(self):
        _ = PAUSE # for readability
        
        a = Part('a', [0, _, 1, _, 0, _, 3, _])
        a.set_property('octava', 0)
        b = Part('b', [0, 3, _])
        b.set_property('octava', 0)
        parts = {'a': a, 'b': b}

        engine = Engine(parts, [], [a, b])
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
        parts = {'a': a, 'b': b}

        lhs = [Condition(Indexed(a, -1), CompNEQ(), _),
               Condition(Indexed(a, 0), CompEQ(), _)]
        rhs = [Modifier(Indexed(a, -1), _),
               Modifier(Indexed(a, 0), Indexed(a, -1))]
        rule = Rule(lhs, rhs)
        rules = [rule]

        engine = Engine(parts, rules, [a, b])
        engine.iterate()

        self.assertEquals(0, a.pointer)
        self.assertEquals(2, b.pointer)

        self.assertEquals([_, 0, _, 1, _, 0, _, 3], a.notes)
        self.assertEquals([0, 3, _], b.notes)

    def test_engine_iterate_multiple(self):
        _ = PAUSE # for readability
        
        a = Part('a', [0, _, 1, _, 0, _, 3, _])
        b = Part('b', [0, 3, _])
        parts = {'a': a, 'b': b}

        lhs = [Condition(Indexed(a, 0), CompEQ(), Indexed(b, 0)),
               Condition(Indexed(a, 1), CompEQ(), _)]
        rhs = [Modifier(Indexed(a, 0), Indexed(a, 0))]
        rule1 = Rule(lhs, rhs)

        lhs = [Condition(Indexed(a, -1), CompNEQ(), _),
               Condition(Indexed(a, 0), CompEQ(), _)]
        rhs = [Modifier(Indexed(a, -1), _),
               Modifier(Indexed(a, 0), Indexed(a, -1))]
        rule2 = Rule(lhs, rhs)

        rules = [rule1, rule2]

        engine = Engine(parts, rules, [a, b])
        engine.iterate()

        self.assertEquals(0, a.pointer)
        self.assertEquals(2, b.pointer)

        self.assertEquals([0, _, _, 1, _, 0, _, 3], a.notes)
        self.assertEquals([0, 3, _], b.notes)


if __name__ == '__main__':
    unittest.main()
