from collections import deque, OrderedDict
from itertools import chain, islice

class DuplicateCommentError(Exception): pass
class InvalidIDError(Exception): pass
class MissingParentError(Exception): pass

class CommentTree:
    """Nested list of dicts representing a comment tree."""
    def __init__(self, *iterables_of_rows):
        self.mapping = OrderedDict()  # {} in future implementation?
        self._children = {}
        self.output = []
        self.add(*iterables_of_rows)

    def add(self, *iterables_of_rows):
        if not iterables_of_rows: return

        for row in chain(*iterables_of_rows):
            rid = row['id']
            if rid not in self.mapping:
                row = dict(row)
                self.mapping[rid] = row
                self.mapping[rid]['children'] = self._children.setdefault(rid, [])
                self._children.setdefault(row['parent_id'], []).append(row)
            else: self.mapping[rid].update(row)

        self.output, cache = [], set()
        for row in self.mapping.values():
            if row['id'] in cache: continue
            else: cache.add(row['id'])

            while row['parent_id'] not in cache and row['parent_id'] in self.mapping:
                row = self.mapping[row['parent_id']]
                cache.add(row['id'])
            if row['parent_id'] not in self.mapping: self.output.append(row)

    def delete(self, row_id):
        temp = deque((self.mapping[row_id],))
        if temp[0] in self.output: self.output.remove(temp[0])
        while temp:
            row = temp.popleft()
            temp.extend(self._children.pop(row['id']))
            if row['parent_id'] in self._children: self._children[row['parent_id']].remove(row)
            self.mapping.pop(row['id'])

    def copy(self):
        return CommentTree(self.mapping.values())

    def clear(self):
        self.mapping = {}
        self._children = {}
        self.output = []

    def items(self):
        temp = deque(self.output)
        while temp:
            row = temp.popleft()
            yield row
            if row['id'] in self._children:
                temp.extendleft(self._children[row['id']][::-1])

    def items_breadth_first(self):
        temp = deque(self.output)
        while temp:
            row = temp.popleft()
            yield row
            if row['id'] in self._children:
                temp.extend(self._children[row['id']])

    def items_by_id(self, reverse=False):
        return map(self.mapping.__getitem__, sorted(self.mapping, reverse=reverse))

    def __len__(self):
        return len(self.mapping)

    def __contains__(self, item):
        return item in self.mapping

    def __getitem__(self, item):
        return self.mapping[item]

    def get_index(self, index):
        return next(islice(self.mapping.values(), index, index+1))

    def __add__(self, other):
        if isinstance(other, CommentTree): self.add(other.mapping.values())
        else: self.add(other)
        return self

    def __eq__(self, other):
        if isinstance(other, CommentTree): return self.mapping == other.mapping
        elif isinstance(other, list): return self.output == other
        else: return False

    def __ne__(self, other):
        if isinstance(other, CommentTree): return self.mapping != other.mapping
        elif isinstance(other, list): return self.output != other
        else: return True

    def __bool__(self):
        return bool(self.mapping)

    def __iter__(self):
        return self.items()

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.output)
