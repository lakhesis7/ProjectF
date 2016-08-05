import unittest

class TestCommentTree(unittest.TestCase):
    from comment_tree import CommentTree

    # 8
    # ├─10
    # └─ 9─11
    # 1
    # └─ 3
    # 13 (parent=6)
    data = [
        dict(id=10, parent_id=8),    # Child comment before parent
        dict(id=1, parent_id=None),  # Root comment in between child and parent
        dict(id=8, parent_id=None),  # Root comment with children present
        dict(id=9, parent_id=8),     # Child comment after parent
        dict(id=13, parent_id=6),    # Orphan comment
        dict(id=11, parent_id=9),    # Deep child comment
        dict(id=3, parent_id=1),
    ]
    data_processed = [
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

    t0 = CommentTree()
    t1 = CommentTree(data)
    t2 = CommentTree(data[:3])
    t2.add(data[3:])
    t3 = CommentTree(data[:3], data[3:])

    def test_equalities(self):
        self.assertEqual(self.t1.output, self.data_processed, 'comparing with lists')
        self.assertEqual(self.t1, self.t2)
        self.assertEqual(self.t1, self.t3)

        self.assertNotEqual(self.t1, [])
        self.assertNotEqual(self.t1, self.t0)

    def test_bool(self):
        self.assertFalse(self.t0)
        self.assertTrue(self.t1)

    def test_len(self):
        self.assertEqual(len(self.t0), 0)
        self.assertEqual(len(self.t1), 7)

    def test_contains(self):
        self.assertTrue(11 in self.t1)
        self.assertFalse(11 in self.t0)

    def test_getitem(self):
        self.assertEqual(self.t1[11], dict(id=11, parent_id=9, children=[]))

    def test_iterators(self):
        self.assertEqual([c['id'] for c in self.t1.items()], [8, 10, 9, 11, 1, 3, 13])
        self.assertEqual([c['id'] for c in self.t1.items_breadth_first()], [8, 1, 13, 10, 9, 3, 11])
        self.assertEqual([c['id'] for c in self.t1.items_by_id()], [1, 3, 8, 9, 10, 11, 13])

    def test_add(self):
        t = self.CommentTree() + self.data
        self.assertEqual(t, self.t1)

        t = self.CommentTree() + self.t1
        self.assertEqual(t, self.t2)

    def test_clear(self):
        t = self.CommentTree(self.data)
        t.clear()
        self.assertEqual(t, self.t0)

    def test_delete(self):
        t = self.CommentTree(self.data)
        t.delete(row_id=9)
        result = [
            {'parent_id': None, 'children': [{'parent_id': 8, 'children': [], 'id': 10}], 'id': 8},
            {'parent_id': None, 'children': [{'parent_id': 1, 'children': [], 'id': 3}], 'id': 1},
            {'parent_id': 6, 'children': [], 'id': 13}
        ]
        self.assertEqual(t.output, result)

    def test_copy(self):
        t = self.t1.copy()
        self.assertNotEqual(id(t), id(self.t1))
        self.assertEqual(t, self.t1)

class TestBase36(unittest.TestCase):
    from utils import base36

    def test_encode(self):
        self.assertEqual(self.base36.encode(0), '0')
        self.assertEqual(self.base36.encode(1024), 'sg')
        self.assertEqual(self.base36.encode(-1024), 'sg')

    def test_decode(self):
        self.assertEqual(self.base36.decode('0'), 0)
        self.assertEqual(self.base36.decode('sg'), 1024)

class TestHumanize(unittest.TestCase):
    from utils import humanize
    from datetime import datetime, timedelta

    epoch = datetime(2016, 1, 1)
    expected = [
        (timedelta(weeks=3.5*-52), '3.5 years to go'),
        (timedelta(weeks=-52), '1.0 year to go'),
        (timedelta(days=3.5*-30.4375), '3.5 months to go'),
        (timedelta(days=-30.4375), '1.0 month to go'),
        (timedelta(weeks=-3.5), '3.5 weeks to go'),
        (timedelta(weeks=-1), '1.0 week to go'),
        (timedelta(days=-3.5), '3.5 days to go'),
        (timedelta(days=-1.0), '1.0 day to go'),
        (timedelta(hours=-3.5), '3.5 hours to go'),
        (timedelta(hours=-1), '1.0 hour to go'),
        (timedelta(minutes=-3.5), '3.5 minutes to go'),
        (timedelta(minutes=-1), '1.0 minute to go'),
        (timedelta(seconds=-3.5), '3.5 seconds to go'),
        (timedelta(seconds=-1.0), '1.0 second to go'),
        (timedelta(seconds=0.0), '0.0 seconds ago'),
        (timedelta(seconds=-0.0), '0.0 seconds ago'),
        (timedelta(seconds=1.0), '1.0 second ago'),
        (timedelta(seconds=3.5), '3.5 seconds ago'),
        (timedelta(minutes=1.0), '1.0 minute ago'),
        (timedelta(minutes=3.5), '3.5 minutes ago'),
        (timedelta(hours=1.0), '1.0 hour ago'),
        (timedelta(hours=3.5), '3.5 hours ago'),
        (timedelta(days=1.0), '1.0 day ago'),
        (timedelta(days=3.5), '3.5 days ago'),
        (timedelta(weeks=1.0), '1.0 week ago'),
        (timedelta(weeks=3.5), '3.5 weeks ago'),
        (timedelta(days=30.4375), '1.0 month ago'),
        (timedelta(days=3.5*30.4375), '3.5 months ago'),
        (timedelta(weeks=52), '1.0 year ago'),
        (timedelta(weeks=3.5*52), '3.5 years ago'),
    ]

    def test_convert_datetime(self):
        for td, result in self.expected:
            self.assertEqual(self.humanize.convert_datetime(self.epoch, self.epoch + td), result)

    def test_convert_timedelta(self):
        for td, result in self.expected:
            self.assertEqual(self.humanize.convert_timedelta(td), result)

if __name__ == '__main__':
    unittest.main()
