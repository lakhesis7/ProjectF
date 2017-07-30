import builtins
import itertools
from typing import Iterator, Optional

class BaseConverter:
    def __init__(self, base=62, digits='0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'):
        if not (1 < base <= len(digits)): raise ValueError(base, digits)
        self.base = base
        self.digits = digits
        self.index_by_digits = {d: i for i, d in enumerate(digits)}

    def encode(self, number: int) -> str:
        result, is_neg, number = [], number < 0, abs(number)
        while number:
            result.append(self.digits[number % self.base])
            number //= self.base
        if is_neg: result.append('-')
        return ''.join(reversed(result or self.digits[0]))

    def decode(self, string: str) -> int:
        result, power = 0, 1
        for digit in reversed(string):
            result += self.index_by_digits[digit] * power
            power *= self.base
        return result

    def range(self, start: int=0, stop: Optional[int]=None, step: int=1) -> Iterator[str]:
        if stop is None: start, stop = 0, start
        yield from map(self.encode, builtins.range(start, stop, step))

    def count(self, start: int=0, step: int=1):
        yield from map(self.encode, itertools.count(start, step))
