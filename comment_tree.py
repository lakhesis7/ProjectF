import random
import json
from collections import defaultdict, deque, OrderedDict
from typing import Any, Callable, Iterable, Iterator, List, MutableMapping, Tuple

__all__ = ['CommentTree']

Comment = MutableMapping[str, Any]

class CommentTree:
    """Nested list of dicts representing a comment tree."""
    def __init__(self, comments: Iterable[Comment] = None) -> None:
        self.mapping = OrderedDict()
        self.children = defaultdict(OrderedDict)
        self._output = OrderedDict()
        if comments is not None: self.update(comments)

    def update(self, comments: Iterable[Comment]) -> None:
        for comment in comments:
            self.mapping[comment['id']] = comment
            comment['children'] = self.children[comment['id']]
            self.children[comment['parent']][comment['id']] = comment
        self._output = None

    @property
    def output(self) -> OrderedDict:
        """Returns comment tree as a nested list of dicts"""
        if self._output is not None: return self._output  # DEBUG: comment this line out for line profiling
        result, cache = OrderedDict(), set()
        for comment in self.mapping.values():
            while comment['id'] not in cache:
                cache.add(comment['id'])
                if comment['parent'] not in self.mapping:
                    result[comment['id']] = comment
                    break
                comment = self.mapping[comment['parent']]
        self._output = result
        return result

    def detach(self, comment_id: Any) -> None:
        """Detach a comment and all its descendants from the tree"""
        if comment_id is None: return self.clear()
        for comment in self.iterate(comment_id): del self[comment['id']]
        self._output = None

    def prune(self, max_length: int) -> None:
        """Prune the comment tree up to max_length, choosing only the top-most comments and their ancestors."""
        if max_length <= 0: self.clear()
        elif max_length >= len(self.mapping): return

        new_mapping = {}
        for comment in self.mapping.values():
            temp = {}
            while comment['id'] not in new_mapping and comment['id'] not in temp:
                temp[comment['id']] = comment
                if comment['parent'] not in self.mapping: break
                comment = self.mapping[comment['parent']]
            if len(new_mapping) + len(temp) > max_length: break
            new_mapping.update(temp)
        self.__init__(v for k, v in self.mapping.items() if k in new_mapping)

    def copy(self) -> 'CommentTree': pass

    def clear(self) -> None: self.__init__()

    def group_by_level(self, start_comment_id) -> Iterator[Tuple[Comment]]:
        """Iterator returning list of comments grouped by depth/level"""
        queue = (self.mapping[start_comment_id],) if start_comment_id is not None else tuple(self.output.values())
        while queue:
            yield queue
            queue = tuple(child for parent in queue for child in parent['children'].values())

    def iterate(self, start_comment_id=None) -> Iterator[Comment]:
        """Pre-order iteration"""
        queue = deque((self.mapping[start_comment_id],) if start_comment_id is not None else self.output.values())
        while queue:
            comment = queue.popleft()
            yield comment
            queue.extendleft(reversed(comment['children'].values()))

    def __len__(self) -> int:
        return len(self.mapping)

    def __contains__(self, comment_id: Any) -> bool:
        return comment_id in self.mapping

    def __getitem__(self, comment_id: Any) -> Comment:
        return self.mapping[comment_id]

    def __delitem__(self, comment_id: Any) -> None:
        comment = self.mapping[comment_id]
        del self.children[comment['parent']][comment_id]
        if comment['parent'] not in self.mapping and not self.children[comment['parent']]:
            del self.children[comment['parent']]
        if not self.children[comment_id]: del self.children[comment_id]
        del self.mapping[comment_id]
        self._output = None

    def __bool__(self) -> bool:
        return bool(self.mapping)

    def __iter__(self) -> Iterator[Comment]:
        yield from self.iterate()

    def __repr__(self) -> str:  # DEBUG: Fix
        return f'''{self.__class__.__name__}({list(self.mapping.values())!r})'''

    def __json__(self):
        return json.dumps(self.output, indent=4)

class CommentTreeSorter:
    @staticmethod
    def custom_sort(comment_tree: CommentTree, key: Callable, descending: bool = False):
        comment_tree.__init__(sorted(comment_tree.mapping.values(),
                                     key=key,
                                     reverse=descending))
        return comment_tree

    @staticmethod
    def sort_by_id(comment_tree: CommentTree, descending: bool = False) -> CommentTree:
        comment_tree.__init__(sorted(comment_tree.mapping.values(),
                                     key=lambda c: c['id'],
                                     reverse=descending))
        return comment_tree

    @staticmethod
    def sort_by_random(comment_tree: CommentTree) -> CommentTree:
        items = list(comment_tree.mapping.values())
        random.shuffle(items)
        comment_tree.__init__(items)
        return comment_tree

    @staticmethod
    def sort_by_score(comment_tree: CommentTree, descending: bool = True) -> CommentTree:
        comment_tree.__init__(sorted(comment_tree.mapping.values(),
                                     key=lambda c: c['score'],
                                     reverse=descending))
        return comment_tree

    @staticmethod
    def sort_by_votes(comment_tree: CommentTree, voter_type=None, descending: bool = True) -> CommentTree:
        pass

    @staticmethod
    def sort_by_created(comment_tree: CommentTree, descending: bool = True) -> CommentTree:
        comment_tree.__init__(sorted(comment_tree.mapping.values(),
                                     key=lambda c: c['created_utc'],
                                     reverse=descending))
        return comment_tree

    @staticmethod
    def sort_by_contentiousness(comment_tree: CommentTree, descending: bool = True) -> CommentTree:
        comment_tree.__init__(sorted(comment_tree.mapping.values(),
                                     key=lambda c: c['contentiousness'],
                                     reverse=descending))
        return comment_tree

def _generate_data(num_comments=10000, num_parents=5000, seed=0, start_index=0, sort_by_score=True):  # DEBUG
    from random import Random
    from utils.bases import Base36
    rng = Random(seed)

    if num_parents is None: num_parents = rng.randint(1, int(num_comments // 4))
    elif num_parents > num_comments: raise ValueError('Number of parents exceeds total number ')
    result = [{'id': i, 'parent': None, 'score': rng.randint(-500, 5000)}
              for i in Base36.range(start_index, start_index + num_parents)]
    for i in Base36.range(start_index + num_parents, start_index + num_comments, 1):
        result.append({'id': i, 'parent': rng.choice(result)['id'], 'score': rng.randint(-500, 5000)})
    if sort_by_score: result.sort(key=lambda c: (c['score'], c['id']), reverse=True)
    return result
