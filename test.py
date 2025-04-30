import unittest
from server import SecurityKernel, ClearanceLevel


class TestBLPModel(unittest.TestCase):
    def setUp(self):
        self.kernel = SecurityKernel(":memory:")  # Используем БД в памяти
        self.kernel._init_db()

        self.kernel.add_subject('alice', ClearanceLevel.SECRET)
        self.kernel.add_subject('bob', ClearanceLevel.CONFIDENTIAL)
        self.kernel.add_subject('charlie', ClearanceLevel.TOP_SECRET)

        self.kernel.add_object('doc1', ClearanceLevel.CONFIDENTIAL)
        self.kernel.add_object('doc2', ClearanceLevel.TOP_SECRET)
        self.kernel.add_object('doc3', ClearanceLevel.SECRET)

    def test_read_level_up(self):
        # bob (CONFIDENTIAL) reads doc2 (TOP_SECRET)
        result = self.kernel.read('bob', 'doc2')
        self.assertEqual(result['object'], 'doc2')
        self.assertIn('notice', result)

        # Ensure level changed
        subjects = self.kernel.list_subjects()
        self.assertEqual(subjects['bob']['level'], 'Top Secret')

    def test_write_level_down(self):
        # charlie (TOP_SECRET) writes to doc1 (CONFIDENTIAL)
        result = self.kernel.write('charlie', 'doc1')
        self.assertIn('notice', result)
        self.assertIn('charlie wrote to doc1', result['result'])

        # Level should be lowered
        subjects = self.kernel.list_subjects()
        self.assertEqual(subjects['charlie']['level'], 'Confidential')

    def test_no_level_change_on_allowed_read(self):
        result = self.kernel.read('alice', 'doc1')
        self.assertNotIn('notice', result)
        self.assertEqual(result['object'], 'doc1')

    def test_no_level_change_on_allowed_write(self):
        result = self.kernel.write('bob', 'doc1')
        self.assertEqual(result, 'bob wrote to doc1.')

    def test_subject_list(self):
        result = self.kernel.list_subjects()
        self.assertIn('alice', result)
        self.assertEqual(result['alice']['level'], 'Secret')

    def test_object_list(self):
        result = self.kernel.list_objects()
        self.assertIn('doc3', result)
        self.assertEqual(result['doc3']['level'], 'Secret')


if __name__ == '__main__':
    unittest.main()
