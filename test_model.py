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

if __name__ == '__main__':
    unittest.main()
