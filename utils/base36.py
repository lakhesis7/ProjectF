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
