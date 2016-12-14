import re
import json
from utils.time_this import TimeThis

class Pattern:
    registered_patterns = {}
    DEFAULT_RULES = []

    def __init_subclass__(cls, pattern, flags=0, rules=(), is_default=True):
        cls.name = cls.__name__
        try: cls.regex = re.compile(pattern=pattern, flags=flags)
        except Exception: raise Exception(pattern)
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
        if rules is None: rules = cls.rules

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

class DefaultPatterns:
    class EscapedChar(Pattern,
                      pattern=r'\\(?P<TEXT>[\\*{\[\]}_^=\n\-])'):
        @classmethod
        def transform(cls, match): return match['TEXT']

    class CodeBlock(Pattern,
                    pattern=r'\B{{{(?P<TEXT>[^{}].*?)}}}\B', flags=re.DOTALL):
        @classmethod
        def transform(cls, match): return 'CC{}CC'.format(match['TEXT'])

    class Link(Pattern,
               pattern=r'\[\[(?P<LINK>\S+?)(\|(?P<DESCRIPTION>(.*?)))?(?P<EXTENSIONS>(\|\S*?)*)\]\]', flags=re.DOTALL,
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

    class UserMention(Pattern,
                      pattern=r'(?P<TEXT>@(?P<USERNAME>[a-zA-Z0-9][a-zA-Z0-9_]{2,23}[a-zA-Z0-9]))'):
        @classmethod
        def transform(cls, match): return '@@{}@@'.format(match['USERNAME'])

    class Emoji(Pattern,
                pattern=r':(\w+):'):
        with open('emoji.json', 'rt') as f:
            emojis = json.load(f)

        @classmethod
        def transform(cls, match):
            try: return ''.join(chr(int(u, base=16)) for u in cls.emojis[match[1]]['unicode'].split('-'))
            except KeyError: return cls.parse(match[1])  # TODO

    class Table(Pattern,
                pattern=r'^\|(?P<FIRSTROW>(.*?\|)+$)(?P<OTHERROWS>(\n^\|(.*?\|)+$)+)', flags=re.DOTALL | re.MULTILINE,
                rules=('EscapedChar', 'CodeBlock', 'Link', 'UserMention',
                       'Emoji', 'Heading', 'BulletPoint', 'NumberedList',
                       'BoldItalics', 'Superscript', 'Subscript')):  # TODO
        @classmethod
        def transform(cls, match):
            result = [[cls.parse(r) for r in match['FIRSTROW'].strip().split('|')]]

    class Heading(Pattern,
                  pattern=r'^(?P<LEVEL>=+) (?P<TEXT>\S.+)', flags=re.MULTILINE,
                  rules=('EscapedChar', 'CodeBlock', 'Link', 'UserMention',
                         'Emoji', 'BoldItalics', 'Superscript', 'Subscript')): pass

    class BulletPoint(Pattern,
                      pattern=r'^\* (.*)(\n\*+ .*)*',  # TODO
                      rules=('EscapedChar', 'CodeBlock', 'Link', 'UserMention',
                             'Emoji', 'BoldItalics', 'Superscript', 'Subscript')): pass

    class NumberedList(Pattern,
                       pattern=r'^# (.*)(\n#+ .*)*',  # TODO
                       rules=('EscapedChar', 'CodeBlock', 'Link', 'UserMention',
                              'Emoji', 'BoldItalics', 'Superscript', 'Subscript')): pass

    class BoldItalics(Pattern,
                      pattern=r'(?P<LEVEL>\*{1,3})(?P<TEXT>[^*].*?)(\1)', flags=re.DOTALL,
                      rules=('BoldItalics', 'Superscript', 'Subscript')):
        @classmethod
        def transform(cls, match):
            format_str = ('i{}i', 'b{}b', 'bi{}ib')[len(match['LEVEL']) - 1]
            return format_str.format(cls.parse(match['TEXT']))

    class Superscript(Pattern,
                      pattern=r'\^\^(?P<TEXT>[^^].*?)\^\^',
                      rules=('BoldItalics', 'Superscript', 'Subscript')):
        @classmethod
        def transform(cls, match): return '~sup~{}~/sup~'.format(match['TEXT'])

    class Subscript(Pattern,
                    pattern=r'__(?P<TEXT>[^_].*?)__',
                    rules=('BoldItalics', 'Superscript', 'Subscript')):
        @classmethod
        def transform(cls, match): return '~sub~{}~/sub~'.format(match['TEXT'])

    class HorizontalRule(Pattern,
                         pattern=r'^-{3,}$', flags=re.MULTILINE): pass

def parse_text(text): return Pattern.parse(text, rules=Pattern.DEFAULT_RULES)
