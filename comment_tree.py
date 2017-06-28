from collections import defaultdict, deque, OrderedDict
from typing import Any, Callable, Iterable, Iterator, Mapping

class DuplicateCommentError(Exception): pass
class MissingParentError(Exception): pass
Comment = Mapping[str, Any]

class CommentTree:
    """Nested list of dicts representing a comment tree."""
    def __init__(self, comments: Iterable[Comment]=()) -> None:
        self.mapping = OrderedDict()
        self.children = defaultdict(list)
        self._modified, self._output = False, []
        if comments: self.add(comments)

    def add(self, comments: Iterable[Comment], *, to_dict_function: Callable[[Comment], dict]=None) -> None:
        if to_dict_function: comments = map(to_dict_function, comments)
        for comment in comments:
            self.mapping[comment['id']] = comment
            comment['children'] = self.children[comment['id']]
            self.children[comment['parent_id']].append(comment)
        self._modified, self._output = True, None

    @property
    def output(self) -> list:
        if not self._modified: return self._output  # DEBUG: comment this line out for line profiling
        result, cache = [], set()
        for cid, comment in self.mapping.items():
            if cid in cache: continue
            cache.add(cid)

            while comment['parent_id'] in self.mapping:
                if comment['parent_id'] in cache: break
                cache.add(comment['parent_id'])
                comment = self.mapping[comment['parent_id']]
            else:
                if comment['parent_id'] not in self.mapping: result.append(comment)
        self._modified, self._output = False, result
        return result

    def delete(self, *comment_ids: str) -> None:
        if not comment_ids: raise ValueError('No comment id(s) given.')
        for cid in comment_ids:
            queue = deque((self.mapping[cid],))
            while queue:
                comment = queue.popleft()
                queue.extend(self.children.pop(comment['id']))
                self.children[comment['parent_id']].remove(comment)
                self.mapping.pop(comment['id'])
        self._modified, self._output = True, None

    def copy(self):
        return CommentTree(self.mapping.values())

    def clear(self) -> None:
        self.__init__()

    def items(self, method: str='depth') -> Iterator[Comment]:
        queue = deque(self.output)
        if method not in ('depth', 'breadth'): raise ValueError(method)
        while queue:
            comment = queue.popleft()
            yield comment
            queue.extend(comment['children'])
            if method == 'depth': queue.rotate(len(comment['children']))

    def __len__(self) -> int:
        return len(self.mapping)

    def __contains__(self, comment_id: str) -> bool:
        return comment_id in self.mapping

    def __getitem__(self, comment_id: str) -> Comment:
        return self.mapping[comment_id]

    def __delitem__(self, comment_id: str) -> None:
        if self.mapping[comment_id]['parent_id'] in self.mapping:
            self.children[self.mapping[comment_id]['parent_id']].remove(self.mapping[comment_id])
        if not self.children[comment_id]: del self.children[comment_id]
        del self.mapping[comment_id]

    def __bool__(self) -> bool:
        return bool(self.mapping)

    def __iter__(self) -> Iterator[Comment]:
        return self.items(method='depth')

    def __str__(self) -> str:
        return f'{self.__class__.__name__}<{self.output!r}>'

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.mapping!r})'

    def _json(self):  # DEBUG: Possibly keep?
        import json
        return json.dumps(self.output, indent=4)

    @classmethod
    def _benchmark(cls, n_comments=500, n_trees=1000):
        from timeit import timeit
        result = timeit(
            setup=f'''from comment_tree import _generate_data, CommentTree;D = _generate_data({n_comments})''',
            stmt='''CommentTree(D).output''',
            number=n_trees
        )

        print(*([
            f'TOTAL TIME: \33[1;34m{result:0.4f} sec\33[0m',
            f'\33[1;34m{n_trees} x {n_comments} = {n_trees * n_comments} comments\33[0m',
            f'    \33[1;32m{n_trees / result:0.3f}\33[0m trees per sec',
            f'       {n_trees / result * 60:0.3f} trees per min',
            f'       {n_trees / result * 3600:0.3f} trees per hr',
            f'       {n_trees / result * 86400:0.3f} trees per day',
            '',
            f'    \33[1;32m{result / n_trees * 1000:0.3f}\33[0m msecs per tree',
            f'    \33[1;32m{int(n_trees * n_comments // result):d}\33[0m comments per sec',
            f'    {1000000 * result / n_trees / n_comments:0.3f} usecs per comment',
            f'        {1000 * result / n_trees / n_comments * 100:0.3f} msec per 100 comments',
            f'        {1000 * result / n_trees / n_comments * 250:0.3f} msec per 250 comments',
            f'        {1000 * result / n_trees / n_comments * 500:0.3f} msec per 500 comments',
            f'        {1000 * result / n_trees / n_comments * 1000:0.3f} msec per 1000 comments',
            f'        {1000 * result / n_trees / n_comments * 10000:0.3f} msec per 10000 comments',
            f'        {1000 * result / n_trees / n_comments * 100000:0.3f} msec per 100k comments',
        ]), sep='\n')

def _generate_data(num_comments=10000, num_parents=25, seed=0, start_index=0):  # DEBUG
    from random import Random
    RNG = Random(seed)

    if num_parents > num_comments: raise ValueError('Number of parents exceeds total number ')
    result = [{'id': i, 'parent_id': None, 'score': RNG.randint(-500, 5000)} for i in range(start_index, start_index + num_parents)]
    for i in range(start_index + num_parents, start_index + num_comments, 1):
        result.append({'id': i, 'parent_id': RNG.choice(result)['id'], 'score': RNG.randint(-500, 5000)})
    RNG.shuffle(result)
    return result

if __name__ == '__main__':
    from line_profiler import LineProfiler
    D = _generate_data()

    lp = LineProfiler()
    lp.add_function(CommentTree.add)
    lp.add_function(CommentTree.output.fget)
    lp.run('CommentTree(D).output')
    lp.print_stats(stripzeros=True)

    CommentTree._benchmark()
