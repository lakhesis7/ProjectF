import unittest
from operator import itemgetter

class TestCommentTree(unittest.TestCase):
    from comment_tree import CommentTree

    def setUp(self):
        # 8
        # ├─10
        # └─ 9─11
        # 1
        # └─ 3
        # 13 (parent=6)
        self.test_data = [
            dict(id=10, parent_id=8),    # Child comment before parent
            dict(id=1, parent_id=None),  # Root comment in between child and parent
            dict(id=8, parent_id=None),  # Root comment with children present
            dict(id=9, parent_id=8),     # Child comment after parent
            dict(id=13, parent_id=6),    # Orphan comment
            dict(id=11, parent_id=9),    # Deep child comment
            dict(id=3, parent_id=1),
        ]
        self.expected_output = [
            dict(id=8, parent_id=None, children=[
                dict(id=10, parent_id=8, children=[]),
                dict(id=9, parent_id=8, children=[
                    dict(id=11, parent_id=9, children=[])
                ]),
            ]),
            dict(id=1, parent_id=None, children=[
                dict(id=3, parent_id=1, children=[])
            ]),
            dict(id=13, parent_id=6, children=[])
        ]

        self.blank_ct = self.CommentTree()
        self.full_ct = self.CommentTree(self.test_data)
        self.secondary_ct = self.CommentTree(self.test_data[:3], self.test_data[3:])

    def test_equalities(self):
        self.assertTrue(self.full_ct.output == self.expected_output)
        self.assertTrue(self.full_ct == self.expected_output)
        self.assertTrue(self.full_ct == self.secondary_ct)
        self.assertTrue(self.blank_ct.output == [])
        self.assertTrue(self.blank_ct == [])

        self.assertFalse(self.full_ct == [])
        self.assertFalse(self.full_ct == self.blank_ct)

    def test_bool(self):
        self.assertFalse(self.blank_ct)
        self.assertTrue(self.full_ct)

    def test_len(self):
        self.assertEqual(len(self.blank_ct), 0)
        self.assertEqual(len(self.full_ct), 7)
        self.assertEqual(len(self.secondary_ct), 7)

    def test_contains(self):
        self.assertTrue(11 in self.full_ct)
        self.assertFalse(11 in self.blank_ct)

    def test_getitem(self):
        self.assertEqual(self.full_ct[11], dict(id=11, parent_id=9, children=[]))
        self.assertEqual(self.full_ct.get_index(5), dict(id=11, parent_id=9, children=[]))

    def test_iterators(self):
        self.assertEqual(list(map(itemgetter('id'), self.full_ct.items())), [8, 10, 9, 11, 1, 3, 13])
        self.assertEqual(list(map(itemgetter('id'), self.full_ct.items_breadth_first())), [8, 1, 13, 10, 9, 3, 11])
        self.assertEqual(list(map(itemgetter('id'), self.full_ct.items_by_id())), [1, 3, 8, 9, 10, 11, 13])

    def test_add(self):
        self.assertEqual(self.blank_ct + self.test_data, self.full_ct)
        self.assertEqual(self.blank_ct + self.full_ct, self.full_ct)
        self.assertEqual(self.CommentTree(self.test_data[:3], self.test_data[3:]), self.full_ct)
        self.assertEqual(self.CommentTree(self.test_data[:3]) + self.CommentTree(self.test_data[3:]), self.full_ct)

    def test_clear(self):
        self.full_ct.clear()
        self.assertEqual(self.full_ct, self.blank_ct)

    def test_delete(self):
        self.full_ct.delete(row_id=9)
        result = [
            {'parent_id': None, 'children': [{'parent_id': 8, 'children': [], 'id': 10}], 'id': 8},
            {'parent_id': None, 'children': [{'parent_id': 1, 'children': [], 'id': 3}], 'id': 1},
            {'parent_id': 6, 'children': [], 'id': 13}
        ]
        self.assertEqual(self.full_ct, result)

    def test_copy(self):
        t = self.full_ct.copy()
        self.assertNotEqual(id(t), id(self.full_ct))
        self.assertEqual(t, self.full_ct)

class TestBase36(unittest.TestCase):
    from utils import base36

    def test_encode(self):
        for n, s in zip([0, 1024, -1024], ['0', 'sg', 'sg']):
            with self.subTest(number=n):
                self.assertEqual(self.base36.encode(n), s)

    def test_decode(self):
        for n, s in zip([0, 1024], ['0', 'sg']):
            with self.subTest(string=s):
                self.assertEqual(self.base36.decode(s), n)

class TestHumanize(unittest.TestCase):
    from utils import humanize
    from datetime import datetime, timedelta

    def setUp(self):
        self.epoch = self.datetime(2016, 1, 1)
        self.expected = [
            (self.timedelta(weeks=3.5*-52), '3.5 years to go'),
            (self.timedelta(weeks=-52), '1.0 year to go'),
            (self.timedelta(days=3.5*-30.4375), '3.5 months to go'),
            (self.timedelta(days=-30.4375), '1.0 month to go'),
            (self.timedelta(weeks=-3.5), '3.5 weeks to go'),
            (self.timedelta(weeks=-1), '1.0 week to go'),
            (self.timedelta(days=-3.5), '3.5 days to go'),
            (self.timedelta(days=-1.0), '1.0 day to go'),
            (self.timedelta(hours=-3.5), '3.5 hours to go'),
            (self.timedelta(hours=-1), '1.0 hour to go'),
            (self.timedelta(minutes=-3.5), '3.5 minutes to go'),
            (self.timedelta(minutes=-1), '1.0 minute to go'),
            (self.timedelta(seconds=-3.5), '3.5 seconds to go'),
            (self.timedelta(seconds=-1.0), '1.0 second to go'),
            (self.timedelta(seconds=0.0), '0.0 seconds ago'),
            (self.timedelta(seconds=-0.0), '0.0 seconds ago'),
            (self.timedelta(seconds=1.0), '1.0 second ago'),
            (self.timedelta(seconds=3.5), '3.5 seconds ago'),
            (self.timedelta(minutes=1.0), '1.0 minute ago'),
            (self.timedelta(minutes=3.5), '3.5 minutes ago'),
            (self.timedelta(hours=1.0), '1.0 hour ago'),
            (self.timedelta(hours=3.5), '3.5 hours ago'),
            (self.timedelta(days=1.0), '1.0 day ago'),
            (self.timedelta(days=3.5), '3.5 days ago'),
            (self.timedelta(weeks=1.0), '1.0 week ago'),
            (self.timedelta(weeks=3.5), '3.5 weeks ago'),
            (self.timedelta(days=30.4375), '1.0 month ago'),
            (self.timedelta(days=3.5*30.4375), '3.5 months ago'),
            (self.timedelta(weeks=52), '1.0 year ago'),
            (self.timedelta(weeks=3.5*52), '3.5 years ago'),
        ]

    def test_convert_datetime(self):
        for td, result in self.expected:
            self.assertEqual(self.humanize.convert_datetime(self.epoch, self.epoch + td), result)

    def test_convert_timedelta(self):
        for td, result in self.expected:
            self.assertEqual(self.humanize.convert_timedelta(td), result)

if __name__ == '__main__':
    unittest.main()
