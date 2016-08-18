from timeit import timeit

n = 10000

print(timeit(
    '''[].insert(0, 0)''',
    number=n,
))

print(timeit(
    '''[][0:0] = (0,)''',
    number=n,
))
