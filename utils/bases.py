import builtins
import itertools
from typing import Any, Generator, Iterable, Optional, Tuple

class BaseConverter:
    def __init__(self, digits: str) -> None:
        if len(digits) <= 1 or len(set(digits)) < len(digits): raise ValueError(digits)
        self.base = len(digits)
        self.digits = digits
        self.index_by_digit = {d: i for i, d in enumerate(digits)}

    def encode(self, number: int) -> str:
        number = int(number)
        result, is_negative, number = [], number < 0, abs(number)
        while number:
            result.append(self.digits[number % self.base])
            number //= self.base
        if is_negative: result.append('-')
        return ''.join(reversed(result or self.digits[0]))

    def decode(self, string: str) -> int:
        result, power, is_negative = 0, 1, string.startswith('-')
        if is_negative: string = string[1::]
        for digit in reversed(string):
                result += self.index_by_digit[digit] * power
                power *= self.base
        return -result if is_negative else result

    def range(self, start: int = 0, stop: Optional[int] = None, step: int = 1) -> Generator[str, None, None]:
        if stop is None: start, stop = 0, start
        yield from map(self.encode, builtins.range(start, stop, step))

    def count(self, start: int = 0, step: int = 1) -> Generator[str, None, None]:
        yield from map(self.encode, itertools.count(start, step))

    def enumerate(self, iterable: Iterable[Any]) -> Generator[Tuple[int, Any], None, None]:
        yield from zip(self.count(), iterable)

Base2 = BaseConverter(digits='01')
Base8 = BaseConverter(digits='01234567')
Base10 = BaseConverter(digits='0123456789')
Base16 = BaseConverter(digits='0123456789abcdef')
Base32 = BaseConverter(digits='abcdefghijklmnopqrstuvwxyz234567')
Base36 = BaseConverter(digits='0123456789abcdefghijklmnopqrstuvwxyz')
Base62 = BaseConverter(digits='0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
Base64 = BaseConverter(digits='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_')
Base85 = BaseConverter(digits='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!#$%&()*+-;<=>?@^_`{|}~')
