import unittest
from server import SecurityKernel, ClearanceLevel, AccessDenied, TranquilityViolation


class TestBLPModel(unittest.TestCase):
    def setUp(self):
        self.kernel = SecurityKernel()

        self.kernel.cursor.execute("DELETE FROM subjects")
        self.kernel.cursor.execute("DELETE FROM objects")
        self.kernel.cursor.execute("DELETE FROM temp_levels")
        self.kernel.db.commit()

        self.kernel.add_subject('alice', ClearanceLevel.SECRET)
        self.kernel.add_subject('bob', ClearanceLevel.CONFIDENTIAL)
        self.kernel.add_subject('charlie', ClearanceLevel.TOP_SECRET)

        self.kernel.add_object('doc1', ClearanceLevel.CONFIDENTIAL)
        self.kernel.add_object('doc2', ClearanceLevel.TOP_SECRET)
        self.kernel.add_object('doc3', ClearanceLevel.SECRET)

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
            self.kernel.set_subject_level('alice', ClearanceLevel.CONFIDENTIAL)

    def test_label_change_allowed(self):
        result = self.kernel.set_subject_level('bob', ClearanceLevel.SECRET)
        self.assertIn("bob", result)
        subjects = self.kernel.list_subjects()
        self.assertEqual(subjects['bob']['original_level'], 'Secret')

    def test_list_subjects(self):
        subjects = self.kernel.list_subjects()
        self.assertIn('alice', subjects)
        self.assertEqual(subjects['alice']['original_level'], 'Secret')
        self.assertEqual(subjects['alice']['current_level'], 'Secret')

    def test_list_objects(self):
        objects = self.kernel.list_objects()
        self.assertIn('doc1', objects)
        self.assertEqual(objects['doc1']['level'], 'Confidential')

    def test_override_level_success(self):
        result = self.kernel.override_level('alice', ClearanceLevel.CONFIDENTIAL)
        self.assertIn("temporary level set to Confidential", result)

        subjects = self.kernel.list_subjects()
        self.assertEqual(subjects['alice']['current_level'], 'Confidential')
        self.assertEqual(subjects['alice']['original_level'], 'Secret')
        self.assertEqual(subjects['alice']['temporary_level'], 'Confidential')

    def test_override_level_fail_higher(self):
        with self.assertRaises(ValueError):
            self.kernel.override_level('bob', ClearanceLevel.SECRET)

    def test_restore_level(self):
        self.kernel.override_level('alice', ClearanceLevel.CONFIDENTIAL)
        result = self.kernel.restore_level('alice')
        self.assertIn("restored to original level", result)

        subjects = self.kernel.list_subjects()
        self.assertEqual(subjects['alice']['current_level'], 'Secret')
        self.assertEqual(subjects['alice']['original_level'], 'Secret')
        self.assertNotIn('temporary_level', subjects['alice'])

    def test_write_after_override(self):
        with self.assertRaises(AccessDenied):
            self.kernel.write('alice', 'doc1')

        self.kernel.override_level('alice', ClearanceLevel.CONFIDENTIAL)

        result = self.kernel.write('alice', 'doc1')
        self.assertEqual(result, 'alice wrote to doc1.')

        with self.assertRaises(AccessDenied):
            self.kernel.read('alice', 'doc3')

    def test_read_after_restore(self):

        self.kernel.override_level('alice', ClearanceLevel.CONFIDENTIAL)
        self.kernel.restore_level('alice')

        result = self.kernel.read('alice', 'doc3')
        self.assertEqual(result['object'], 'doc3')

        with self.assertRaises(AccessDenied):
            self.kernel.write('alice', 'doc1')


if __name__ == '__main__':
    unittest.main()