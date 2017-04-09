import re

class FunctionValidator:
    def __init__(self, func):
        self.validate = func

    def validate(self, obj):
        pass

    def __call__(self, obj, *args, **kwargs):
        try:
            return self.validate(obj)
        except:
            raise ValueError(obj)

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

class MembershipValidator(FunctionValidator):
    def __init__(self, container):
        super().__init__(lambda obj: obj in container)

class RegexValidator(FunctionValidator):
    def __init__(self, regex):
        super().__init__(lambda obj: regex.match(obj) is not None)

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

UsernameValidator = RegexValidator(re.compile(pattern=r'[a-zA-Z0-9][a-zA-Z0-9_]{2,24}'))
PasswordValidator = RegexValidator(re.compile(pattern=r'[\w\s]{8,256}'))
EmailValidator = RegexValidator(re.compile(
    pattern=r'^((?:[-!#$%&\'*+/=?^`{|}~\w]|\\.)+(?:\.(?:[-!#$%&\'*+/=?^`{|}~\w]|\\.)+)*|"(?:[^\\"]|\\.)+")@(?:\[(?:((?:'
            r'(?:[01][\d]{0,2}|2(?:[0-4]\d?|5[0-5]?|[6-9])?|[3-9]\d?)\.){3}(?:[01][\d]{0,2}|2(?:[0-4]\d?|5[0-5]?|[6-9])'
            r'?|[3-9]\d?))|IPv6:((?:[a-fA-F0-9]{1,4}:){7}[a-fA-F0-9]{1,4}|(?:[a-fA-F0-9]{1,4}:){6}:[a-fA-F0-9]{1,4}|(?:'
            r'[a-fA-F0-9]{1,4}:){5}:(?:[a-fA-F0-9]{1,4}:)?[a-fA-F0-9]{1,4}|(?:[a-fA-F0-9]{1,4}:){4}:(?:[a-fA-F0-9]{1,4}'
            r':){0,2}[a-fA-F0-9]{1,4}|(?:[a-fA-F0-9]{1,4}:){3}:(?:[a-fA-F0-9]{1,4}:){0,3}[a-fA-F0-9]{1,4}|(?:[a-fA-F0-9'
            r']{1,4}:){2}:(?:[a-fA-F0-9]{1,4}:){0,4}[a-fA-F0-9]{1,4}|[a-fA-F0-9]{1,4}::(?:[a-fA-F0-9]{1,4}:){0,5}[a-fA-'
            r'F0-9]{1,4}|::(?:[a-fA-F0-9]{1,4}:){0,6}[a-fA-F0-9]{1,4}|(?:[a-fA-F0-9]{1,4}:){1,7}:|(?:[a-fA-F0-9]{1,4}:)'
            r'{6}(?:(?:[01][\d]{0,2}|2(?:[0-4]\d?|5[0-5]?|[6-9])?|[3-9]\d?)\.){3}(?:[01][\d]{0,2}|2(?:[0-4]\d?|5[0-5]?|'
            r'[6-9])?|[3-9]\d?)|(?:[a-fA-F0-9]{1,4}:){0,5}:(?:(?:[01][\d]{0,2}|2(?:[0-4]\d?|5[0-5]?|[6-9])?|[3-9]\d?)\.'
            r'){3}(?:[01][\d]{0,2}|2(?:[0-4]\d?|5[0-5]?|[6-9])?|[3-9]\d?)|::(?:[a-fA-F0-9]{1,4}:){0,5}(?:(?:[01][\d]{0,'
            r'2}|2(?:[0-4]\d?|5[0-5]?|[6-9])?|[3-9]\d?)\.){3}(?:[01][\d]{0,2}|2(?:[0-4]\d?|5[0-5]?|[6-9])?|[3-9]\d?))|('
            r'[-a-zA-Z0-9]{0,62}[a-zA-Z0-9]:[^\[\\\]]+))\]|([a-zA-Z0-9](?:[-a-zA-Z0-9]{0,62}[a-zA-Z0-9])?(?:\.[a-zA-Z0-'
            r'9](?:[-a-zA-Z0-9]{0,62}[a-zA-Z0-9])?)+))$'))
URLValidator = RegexValidator(re.compile(
    pattern=r'^(?:(?i:http|ftp)s?:\/\/)(?:\S+(?::\S*)?@)?(?:(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]'
            r'\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-zA-Z\u00a1-\uffff0-9]+-?)*[a-zA-Z\u00a1'
            r'-\uffff0-9]+)(?:\.(?:[a-zA-Z\u00a1-\uffff0-9]+-?)*[a-zA-Z\u00a1-\uffff0-9]+)*(?:\.(?:[a-zA-Z\u00a1-\uffff'
            r']{2,})))(?::\d{2,5})?(?:\/[^\s]*)?$'))

# URLValidatorWithoutLocalAddresses: ^(?:(?:https?|ftp):\/\/)(?:\S+(?::\S*)?@)?(?:(?!10(?:\.\d{1,3}){3})(?!127(?:\.\d{1
# ,3}){3})(?!169\.254(?:\.\d{1,3}){2})(?!192\.168(?:\.\d{1,3}){2})(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})(?:[1-9
# ]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-
# zA-Z\u00a1-\uffff0-9]+-?)*[a-zA-Z\u00a1-\uffff0-9]+)(?:\.(?:[a-zA-Z\u00a1-\uffff0-9]+-?)*[a-zA-Z\u00a1-\uffff0-9]+)*(
# ?:\.(?:[a-zA-Z\u00a1-\uffff]{2,})))(?::\d{2,5})?(?:\/[^\s]*)?$

print(URLValidator('Http://javascript:alert("hi");@192.168.2.4'))
