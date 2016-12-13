import re
import json
from utils.time_this import TimeThis

class Pattern:
    registered_patterns = {}
    DEFAULT_RULES = []

    def __init_subclass__(cls, pattern, flags=0, rules=(), is_default=True):
        cls.name = cls.__name__
        cls.regex = re.compile(pattern=pattern, flags=flags)
        cls.pattern = pattern
        cls.search = cls.regex.search
        cls.rules = rules
        cls.registered_patterns[cls.name] = cls
        cls.is_default = is_default
        if is_default: cls.DEFAULT_RULES.append(cls.name)

    @classmethod
    def transform(cls, match): return match[0]

    @classmethod
    def debug(cls, text): return cls.parse(text, rules=(cls.name,))

    @classmethod
    def parse(cls, text, rules=None):
        if rules is None: rules = cls.rules if issubclass(cls, Pattern) else cls.DEFAULT_RULES

        repls = ['{}'] * text.count('{}')  # Maintain any '{}' within the input text

        for rule in (cls.registered_patterns[r] for r in rules):
            while True:
                m = rule.search(text)
                if m is None: break
                repls_start_index = text.count('{}', 0, m.start())
                repls_end_index = repls_start_index + m.group().count('{}')

                # Replacement's for {}'s within the match's text are replaced with the transform text full fleshed out
                repls[repls_start_index: repls_end_index] = [
                    rule.transform(m).format(*repls[repls_start_index: repls_end_index])
                ]

                text = text[:m.start()] + '{}' + text[m.end():]

        return text.format(*repls)

class EscapedChar(Pattern, pattern=r'\\([\\*{\[\]}_^=-])'):
    @classmethod
    def transform(cls, match): return match[1]

class CodeBlock(Pattern, pattern=r'\B{{{([^{}](.|\n)*?)}}}\B'):
    @classmethod
    def transform(cls, match): return 'CC{}CC'.format(match[1])

class Link(Pattern,
           pattern=r'\[\[(?P<LINK>\S+?)(\|(?P<DESCRIPTION>(.*?)))?(?P<EXTENSIONS>(\|\S*?)*)\]\]',
           rules=('EscapedChar', 'Emoji', 'BoldItalics', 'Subscript')):
    extension_mapping = {'spoiler': ':SPOILER', 'nsfw': ':NSFW', 'latex': 'LaTeX'}

    @classmethod
    def transform(cls, match):
        extensions = (e.lower().rstrip('#') for e in match['EXTENSIONS'].split('|') if e)
        result = 'LINKTO:{}'.format(match['LINK'])
        if match['DESCRIPTION']: result += ':{}'.format(cls.parse(match['DESCRIPTION']))
        for k, v in cls.extension_mapping.items():
            if k in extensions: result += v
        return result

class UserMention(Pattern, pattern=r'(@([a-zA-Z0-9][a-zA-Z0-9_]{2,23}[a-zA-Z0-9]))'):
    @classmethod
    def transform(cls, match): return '@@{}@@'.format(match[2])

class Emoji(Pattern, pattern=r':(\w+):'):
    with open('emoji.json', 'rt') as f:
        emojis = json.load(f)

    @classmethod
    def transform(cls, match):
        try: return ''.join(chr(int(u, base=16)) for u in cls.emojis[match[1]]['unicode'].split('-'))
        except KeyError: return cls.parse(match[1])  # TODO

class Table(Pattern,
            pattern=r'^\|(.*?\|)+(\n\|(.*?\|)+)+',
            rules=('EscapedChar', 'CodeBlock', 'Link', 'UserMention',
                   'Emoji', 'Heading', 'BulletPoint', 'NumberedList',
                   'BoldItalics', 'Superscript', 'Subscript')): pass

class Heading(Pattern,
              pattern=r'^= (.*)(\n=+ .*)*',
              rules=('EscapedChar', 'CodeBlock', 'Link', 'UserMention',
                     'Emoji', 'BoldItalics', 'Superscript', 'Subscript')): pass

class BulletPoint(Pattern,
                  pattern=r'^\* (.*)(\n\*+ .*)*',
                  rules=('EscapedChar', 'CodeBlock', 'Link', 'UserMention',
                         'Emoji', 'BoldItalics', 'Superscript', 'Subscript')): pass

class NumberedList(Pattern,
                   pattern=r'^# (.*)(\n#+ .*)*',
                   rules=('EscapedChar', 'CodeBlock', 'Link', 'UserMention',
                          'Emoji', 'BoldItalics', 'Superscript', 'Subscript')): pass

class BoldItalics(Pattern, pattern=r'(\*{1,3})([^*].*?)(\1)', rules=('BoldItalics', 'Superscript', 'Subscript')):
    @classmethod
    def transform(cls, match):
        format_str = ('i{}i', 'b{}b', 'bi{}ib')[len(match[1]) - 1]
        return format_str.format(cls.parse(match[2]))

class Superscript(Pattern, pattern=r'\^\^([^^].*?)\^\^', rules=('BoldItalics', 'Superscript', 'Subscript')):
    @classmethod
    def transform(cls, match): return '~sup~{}~/sup~'.format(match[1])

class Subscript(Pattern, pattern=r'__([^_].*?)__', rules=('BoldItalics', 'Superscript', 'Subscript')):
    @classmethod
    def transform(cls, match): return '~sub~{}~/sub~'.format(match[1])

class HorizontalRule(Pattern, pattern=r'^-{3,}$'): pass

with TimeThis(): print(Link.debug('''[[hi|there:joy:bear|spoiler|nsfw]]'''))
