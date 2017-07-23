import builtins
import itertools
from typing import Iterator, Optional

DIGITS = '0123456789abcdefghijklmnopqrstuvwxyz'

def encode(number: int) -> str:
    result, is_neg, number = [], number < 0, abs(number)
    while number:
        result.append(DIGITS[number % 36])
        number //= 36
    if is_neg: result.append('-')
    return ''.join(reversed(result or DIGITS[0]))

def decode(string: str) -> int:
    return int(string, base=36)

def range(start: int=0, stop: Optional[int]=None, step: int=1) -> Iterator[str]:
    if stop is None: start, stop = 0, start
    yield from map(encode, builtins.range(start, stop, step))

def count(start: int=0, step: int=1):
    yield from map(encode, itertools.count(start, step))
