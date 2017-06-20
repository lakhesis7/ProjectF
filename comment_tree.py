from collections import deque, OrderedDict, defaultdict
from itertools import chain, islice

class DuplicateCommentError(Exception): pass
class MissingParentError(Exception): pass

class CommentTree:
    """Nested list of dicts representing a comment tree."""
    def __init__(self, *rows):
        self.mapping = {}
        self._children = defaultdict(list)
        self.output = []
        self.add(*rows)

    @classmethod
    def from_row_iterables(cls, *row_iterables):
        return cls(chain(*row_iterables))

    def add(self, rows, *, allow_duplicate=True, allow_missing_parent_ids=True):
        for row in map(dict, rows):
            if row['id'] in self.mapping and not allow_duplicate: raise DuplicateCommentError(row)
            self.mapping[row['id']] = row
            row['children'] = self._children[row['id']]
            self._children[row['parent_id']].append(row)

        self.output, cache = [], set()
        for rid, row in self.mapping.items():
            if rid in cache: continue
            cache.add(rid)

            while row['parent_id'] in self.mapping:
                if row['parent_id'] in cache: break
                cache.add(row['parent_id'])
                row = self.mapping[row['parent_id']]
            else:
                if row['parent_id'] is None or allow_missing_parent_ids: self.output.append(row)
                else: raise MissingParentError(row)

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

    def __repr__(self):
        return f'{self.__class__.__name__}({self.output!r})'

    def _tojson(self):
        import json
        return json.dumps(self.output)

def _generate_data(num_comments=10000, num_parents=25, seed=0):
    from random import Random
    RNG = Random(seed)

    if num_parents >= num_comments: raise ValueError('Number of parents exceeds total number ')
    result = [{'id': i, 'parent_id': None} for i in range(num_parents)]
    for i in range(num_parents, num_comments, 1):
        result.append({'id': i, 'parent_id': RNG.choice(result)['id']})
    RNG.shuffle(result)
    return result

from utils.time_this import LineProfiler

D = _generate_data()

lp = LineProfiler()
lp.add_function(CommentTree.add)
lp.runcall(CommentTree, D)
print(lp.print_stats())
