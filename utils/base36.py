from itertools import count as _count
from typing import Iterator, Optional

DIGITS = '0123456789abcdefghijklmnopqrstuvwxyz'

def encode(number: int) -> str:
    number = abs(number)
    result = ''
    while number:
        result = DIGITS[number % 36] + result
        number //= 36
    return result or DIGITS[0]

def decode(string: str) -> int:
    return int(string, base=36)

def count(start: int=0, stop: Optional[int]=None, step: int=1) -> Iterator[str]:
    if stop: yield from map(encode, range(start, stop, step))
    else: yield from map(encode, _count(start, step))
