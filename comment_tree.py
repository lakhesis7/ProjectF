from collections import deque, OrderedDict
from itertools import chain, islice
import json

class DuplicateCommentError(Exception): pass
class Missingparent_idError(Exception): pass

class CommentTree:
    """Nested list of dicts representing a comment tree."""
    def __init__(self, *iterables_of_rows):
        self.mapping = OrderedDict()  # {} in future implementations?
        self._children = {}
        self.output = []
        self.add(*iterables_of_rows)

    def add(self, *iterables_of_rows, allow_duplicate=True, allow_missing_parent_ids=True):
        if not iterables_of_rows: return

        for row in map(dict, chain(*iterables_of_rows)):
            if row['id'] in self.mapping and not allow_duplicate: raise DuplicateCommentError(row)
            self.mapping[row['id']] = row
            row['children'] = self._children.setdefault(row['id'], [])
            self._children.setdefault(row['parent_id'], []).append(row)

        self.output, cache = [], set()
        for rid, row in self.mapping.items():
            if rid in cache: continue
            else: cache.add(rid)

            while row['parent_id'] in self.mapping:
                if row['parent_id'] in cache: break
                cache.add(row['parent_id'])
                row = self.mapping[row['parent_id']]
            else:
                if row['parent_id'] is None or allow_missing_parent_ids: self.output.append(row)
                else: raise Missingparent_idError(row)

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
        self.mapping = OrderedDict()
        self._children = {}
        self.output = []

    def items(self):
        temp = deque(self.output)
        while temp:
            row = temp.popleft()
            yield row
            temp.extendleft(row['children'][::-1])

    def items_breadth_first(self):
        temp = deque(self.output)
        while temp:
            row = temp.popleft()
            yield row
            temp.extend(row['children'])

    def items_by_id(self, reverse=False):
        return map(self.mapping.__getitem__, sorted(self.mapping, reverse=reverse))

    def truncate(self, length):
        if length >= len(self): return
        comments = list(self.items())[:length]
        self.clear()
        self.add(comments)

    def __len__(self):
        return len(self.mapping)

    def __contains__(self, item):
        return item in self.mapping

    def __getitem__(self, item):
        if isinstance(item, slice): return list(islice(self.mapping.values(), item.start, item.stop, item.step))
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

    def __str__(self):
        from utils.misc import DTJson
        return f'{self.__class__.__name__}({json.dumps(self.output, cls=DTJson, indent=4)})'

    def __repr__(self):
        return f'{self.__class__.__name__}({list(self.mapping.values())!r})'

# d = [
#     dict(id=10, parent_id=8),    # Child comment before parent_id
#     dict(id=1, parent_id=None),  # Root comment in between child and parent_id
#     dict(id=8, parent_id=None),  # Root comment with children present
#     dict(id=9, parent_id=8),     # Child comment after parent_id
#     dict(id=13, parent_id=6),    # Orphan comment
#     dict(id=11, parent_id=9),    # Deep child comment
#     dict(id=3, parent_id=1),
# ]