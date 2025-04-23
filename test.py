import unittest
from server import SecurityKernel, Label, ClearanceLevel, AccessDenied, TranquilityViolation

class TestBLPModel(unittest.TestCase):
    def setUp(self):
        self.kernel = SecurityKernel()

        self.kernel.add_subject('alice', Label(ClearanceLevel.SECRET, ['A']))
        self.kernel.add_subject('bob', Label(ClearanceLevel.CONFIDENTIAL, ['A']))
        self.kernel.add_subject('charlie', Label(ClearanceLevel.TOP_SECRET, ['A']))

        self.kernel.add_object('doc1', Label(ClearanceLevel.CONFIDENTIAL, ['A']))
        self.kernel.add_object('doc2', Label(ClearanceLevel.TOP_SECRET, ['A']))
        self.kernel.add_object('doc3', Label(ClearanceLevel.SECRET, ['A']))

    def test_read_access_granted(self):
        result = self.kernel.read('alice', 'doc1')
        self.assertEqual(result['object'], 'doc1')

    def test_read_access_denied(self):
        with self.assertRaises(AccessDenied):
            self.kernel.read('bob', 'doc2')

    def test_write_access_granted(self):
        result = self.kernel.write('bob', 'doc1')
        self.assertEqual(result, 'bob wrote to doc1.')

    def test_write_access_denied(self):
        with self.assertRaises(AccessDenied):
            self.kernel.write('charlie', 'doc1')

    def test_tranquility_violation(self):
        with self.assertRaises(TranquilityViolation):
            self.kernel.set_subject_label('alice', Label(ClearanceLevel.CONFIDENTIAL, ['A']))

    def test_label_change_allowed(self):
        result = self.kernel.set_subject_label('bob', Label(ClearanceLevel.SECRET, ['A', 'B']))
        self.assertIn("bob", result)

    def test_list_subjects(self):
        subjects = self.kernel.list_subjects()
        self.assertIn('alice', subjects)
        self.assertEqual(subjects['alice']['level'], ClearanceLevel.SECRET)

    def test_list_objects(self):
        objects = self.kernel.list_objects()
        self.assertIn('doc1', objects)
        self.assertEqual(objects['doc1']['level'], ClearanceLevel.CONFIDENTIAL)

if __name__ == '__main__':
    unittest.main()
