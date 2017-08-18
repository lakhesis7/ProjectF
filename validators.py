import re
import ipaddress

class FunctionValidator:
    def __init__(self, validate_func):
        self.validate = validate_func

    def validate(self, obj):
        pass

    def __call__(self, obj, *args, **kwargs):
        try: return bool(self.validate(obj))
        except: return False

    def __and__(self, other):
        if not callable(other): raise TypeError(other)
        return FunctionValidator(lambda obj: self(obj) and other(obj))

    def __or__(self, other):
        if not callable(other): raise TypeError(other)
        return FunctionValidator(lambda obj: self(obj) or other(obj))

    def __invert__(self):
        return FunctionValidator(lambda obj: not self(obj))

class TypeValidator(FunctionValidator):
    def __init__(self, type_):
        super().__init__(lambda obj: type(obj) is type_)
        self.type = type_

class MembershipValidator(FunctionValidator):
    def __init__(self, container):
        super().__init__(lambda obj: obj in container)
        self.container = container

class RegexValidator(FunctionValidator):
    def __init__(self, regex, mode='fullmatch'):
        func = getattr(regex, mode, 'fullmatch')
        super().__init__(lambda obj: func(obj) is not None)
        self.regex = regex
        self.mode = mode

class LengthValidator(FunctionValidator):
    def __init__(self, min_inclusive=None, max_inclusive=None):
        if min_inclusive is None and max_inclusive is None:
            raise ValueError(min_inclusive, max_inclusive)
        elif min_inclusive is None:
            super().__init__(lambda obj: len(obj) <= max_inclusive)
        elif max_inclusive is None:
            super().__init__(lambda obj: min_inclusive <= len(obj))
        else:
            super().__init__(lambda obj: min_inclusive <= len(obj) <= max_inclusive)
        self.min_inclusive = min_inclusive
        self.max_inclusive = max_inclusive

UsernameValidator = TypeValidator(str) & RegexValidator(re.compile('[a-zA-Z0-9][a-zA-Z0-9_]{2,24}'))
PasswordValidator = TypeValidator(str) & LengthValidator(8, 256)
EmailValidator = RegexValidator(
    re.compile(r'((?:[-!#$%&\'*+/=?^`{|}~\w]|\\.)+(?:\.(?:[-!#$%&\'*+/=?^`{|}~\w]|\\.)+)*|"(?:[^\\"]|\\.)+")@(?:\[(?:(('
               r'?:(?:[01][\d]{0,2}|2(?:[0-4]\d?|5[0-5]?|[6-9])?|[3-9]\d?)\.){3}(?:[01][\d]{0,2}|2(?:[0-4]\d?|5[0-5]?|['
               r'6-9])[a-fA-F0-9]{1,4}:){5}:(?:[a-fA-F0-9]{1,4}:)?[a-fA-F0-9]{1,4}|(?:[a-fA-F0-9]{1,4}:){4}:(?:[a-fA-F0'
               r'-9]{1,4}:){0,2}[a-fA-F0-9]{1,4}|(?:[a-fA-F0-9]{1,4}:){3}:(?:[a-fA-F0-9]{1,4}:){0,3}[a-fA-F0-9]{1,4}|(?'
               r':[a-fA-F0-9]{1,4}:){2}:(?:[a-fA-F0-9]{1,4}:){0,4}[a-fA-F0-9]{1,4}|[a-fA-F0-9]{1,4}::(?:[a-fA-F0-9]{1,4'
               r'}:){0,5}[a-fA-F0-9]{1,4}|::(?:[a-fA-F0-9]{1,4}:){0,6}[a-fA-F0-9]{1,4}|(?:[a-fA-F0-9]{1,4}:){1,7}:|(?:['
               r'a-fA-F0-9]{1,4}:){6}(?:(?:[01][\d]{0,2}|2(?:[0-4]\d?|5[0-5]?|[6-9])?|[3-9]\d?)\.){3}(?:[01][\d]{0,2}|2'
               r'(?:[0-4]\d?|5[0-5]?|[6-9])?|[3-9]\d?)|(?:[a-fA-F0-9]{1,4}:){0,5}:(?:(?:[01][\d]{0,2}|2(?:[0-4]\d?|5[0-'
               r'5]?|[6-9])?|[3-9]\d?)\.){3}(?:[01][\d]{0,2}|2(?:[0-4]\d?|5[0-5]?|[6-9])?|[3-9]\d?)|::(?:[a-fA-F0-9]{1,'
               r'4}:){0,5}(?:(?:[01][\d]{0,2}|2(?:[0-4]\d?|5[0-5]?|[6-9])?|[3-9]\d?)\.){3}(?:[01][\d]{0,2}|2(?:[0-4]\d?'
               r'|5[0-5]?|[6-9])?|[3-9]\d?))|([-a-zA-Z0-9]{0,62}[a-zA-Z0-9]:[^\[\\\]]+))\]|([a-zA-Z0-9](?:[-a-zA-Z0-9]{'
               r'0,62}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[-a-zA-Z0-9]{0,62}[a-zA-Z0-9])?)+))'))
URLValidator = RegexValidator(
    re.compile(r'(?:(?i:http|ftp)s?://)(?:\S+(?::\S*)?@)?(?:(?:[01]\d\d|2(?:[0-4]\d|5[0-5]))(?:\.(?:[01]\d\d|2(?:[0-4]'
               r'\d|5[0-5])){3}|(?:(?:(?:(?:[a-fA-F0-9]){1,4}:){1,4}:[^\s:](?:(?:25[0-5]|(?:2[0-4]|1?\d)?\d\.){3}25[0-5'
               r']|(?:2[0-4]|1?\d)?\d))|(?:::(?:[Ff]{4}(?::0{1,4})?:)?[^\s:](?:(?:25[0-5]|(?:2[0-4]|1?\d)?\d\.){3}25[0-'
               r'5]|(?:2[0-4]|1?\d)?\d))|(?:[Ff][Ee]80:(?::(?:[a-fA-F0-9]){1,4}){0,4}%[a-zA-Z0-9]+)|(?::(?:(?::(?:[a-fA'
               r'-F0-9]){1,4}){1,7}|:))|(?:(?:[a-fA-F0-9]){1,4}:(?:(?::(?:[a-fA-F0-9]){1,4}){1,6}))|(?:(?:(?:[a-fA-F0-9'
               r']){1,4}:){1,2}(?::(?:[a-fA-F0-9]){1,4}){1,5})|(?:(?:(?:[a-fA-F0-9]){1,4}:){1,3}(?::(?:[a-fA-F0-9]){1,4'
               r'}){1,4})|(?:(?:(?:[a-fA-F0-9]){1,4}:){1,4}(?::(?:[a-fA-F0-9]){1,4}){1,3})|(?:(?:(?:[a-fA-F0-9]){1,4}:)'
               r'{1,5}(?::(?:[a-fA-F0-9]){1,4}){1,2})|(?:(?:(?:[a-fA-F0-9]){1,4}:){1,6}:(?:[a-fA-F0-9]){1,4})|(?:(?:(?:'
               r'[a-fA-F0-9]){1,4}:){1,7}:)|(?:(?:(?:[a-fA-F0-9]){1,4}:){7,7}(?:[a-fA-F0-9]){1,4}))|(?:[a-zA-Z\u00a1-\u'
               r'ffff0-9]+)(?:\.[a-zA-Z\u00a1-\uffff0-9]+)+)|localhost)(?::\d{1,5})?(?:/.*)?'))
Ipv4Validator = FunctionValidator(lambda ip: ipaddress.IPv4Address(ip))
Ipv6Validator = FunctionValidator(lambda ip: ipaddress.IPv6Address(ip))
