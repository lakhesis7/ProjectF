import json
import re
from operator import attrgetter

class RegexRule:
    def __init__(self, name, pattern, descent_rules=None, func=None, flags=re.DOTALL | re.MULTILINE, **kwargs):
        self.name = name
        self.pattern = pattern
        self.regex = re.compile(pattern, flags=flags)
        self.descent_rules = descent_rules or ()
        self.func = func

    def __repr__(self): return f'{self.__class__.__name__}({self.name!r}, {self.pattern!r})'

# TODO: Implement common rule patterns as customizable classes
# class SimpleRegexRule(RegexRule):
#     def __init__(self, name, left_quote, right_quote=None, is_escaped=True, **kwargs):
#         right_quote = right_quote or left_quote
#         if is_escaped:
#             left_quote = '(?<!\\)' + left_quote
#             right_quote = '(?<!\\)' + right_quote
#
#         pattern = fr'(?P<{name}>{left_quote}(?P<{name}_TEXT>.*?){right_quote})'
#         super().__init__(name, pattern, **kwargs)

class Renderer:
    DEFAULT_PATTERNS = (
        RegexRule('CODE', r'(?P<CODE>(?<!\\){{3}(?P<CODE_TEXT>[^{}].*?)(?<!\\)}{3})'),
        RegexRule('ESCAPE', r'(?P<ESCAPE>\\(?P<ESCAPE_TEXT>[-\\*\[\]_^=\n{}]))'),
        RegexRule(
            'LINK',
            r'(?P<LINK>(?<!\\)\[\[(?P<URL>\S+?) *?(\|(?P<DESCRIPTION>.*?)(?P<EXTENSIONS>((?<!\\)\|.*?)*))?(?<!\\)\]\])',
            ('ESCAPE', 'EMOJI', 'BOLD', 'ITALICS', 'UNDERLINE', 'STRIKETHROUGH', 'SUPERSCRIPT', 'SUBSCRIPT')),
        RegexRule(
            'USER_MENTION',
            r'(?P<USER_MENTION>(?<!\\)@(?P<USERNAME>[a-zA-Z0-9][a-zA-Z0-9_]{2,23}[a-zA-Z0-9]))'),
        RegexRule('EMOJI', r'(?P<EMOJI>:(?P<EMOJI_TEXT>\w+):)'),  # FIXME: Add specific emoji text regexes
        RegexRule(
            'TABLE',
            r'(?P<TABLE>^(?P<TABLE_FIRSTROW>\|(.*?\|)+?$)(?P<TABLE_OTHERROWS>(\n^\|(.*?\|)+$)+)?)',
            ('ESCAPE', 'CODE', 'LINK', 'USER_MENTION', 'EMOJI', 'HEADING', 'BULLET_LIST', 'NUMBER_LIST',
             'BOLD', 'ITALICS', 'UNDERLINE', 'STRIKETHROUGH', 'SUPERSCRIPT', 'SUBSCRIPT')),
        RegexRule(
            'BULLET_LIST',
            r'(?P<BULLET_LIST>^\* (?P<BL_FIRSTROW>.*)(?P<BL_OTHERROWS>(\n\*+ .*)*))',
            ('ESCAPE', 'CODE', 'LINK', 'USER_MENTION', 'EMOJI', 'HEADING', 'BOLD', 'ITALICS', 'UNDERLINE',
             'STRIKETHROUGH', 'SUPERSCRIPT', 'SUBSCRIPT')),
        RegexRule(
            'NUMBER_LIST',
            r'(?P<NUMBER_LIST>^# (?P<NL_FIRSTROW>.*)(?P<NL_OTHERROWS>(\n#+ .*)*))',
            ('ESCAPE', 'CODE', 'LINK', 'USER_MENTION', 'EMOJI', 'HEADING', 'BOLD', 'ITALICS', 'UNDERLINE',
             'STRIKETHROUGH', 'SUPERSCRIPT', 'SUBSCRIPT')),
        RegexRule(
            'HEADING',
            r'(?P<HEADING>^(?:(?P<HEADING_LEVEL>=+) )(?P<HEADING_TEXT>.+?$))',
            ('ESCAPE', 'LINK', 'USER_MENTION', 'EMOJI', 'BOLD', 'ITALICS', 'UNDERLINE', 'STRIKETHROUGH', 'SUPERSCRIPT',
             'SUBSCRIPT')),
        RegexRule(
            'BOLD',
            r'(?P<BOLD>(?<!\\)\*{2}(?P<BOLD_TEXT>[^*].*?)(?<!\\)\*{2})',
            ('ESCAPE', 'ITALICS', 'UNDERLINE', 'STRIKETHROUGH', 'SUPERSCRIPT', 'SUBSCRIPT')),
        RegexRule(
            'ITALICS',
            r'(?P<ITALICS>(?<!\\)/{2}(?P<ITALICS_TEXT>[^/].*?)(?<!\\)/{2})',
            ('ESCAPE', 'BOLD', 'UNDERLINE', 'STRIKETHROUGH', 'SUPERSCRIPT', 'SUBSCRIPT')),
        RegexRule(
            'UNDERLINE',
            r'(?P<UNDERLINE>(?<!\\)_{2}(?P<UNDERLINE_TEXT>[^_].*?)(?<!\\)_{2})',
            ('ESCAPE', 'BOLD', 'ITALICS', 'STRIKETHROUGH', 'SUPERSCRIPT', 'SUBSCRIPT', )),
        RegexRule(
            'STRIKETHROUGH',
            r'(?P<STRIKETHROUGH>(?<!\\)-{2}(?P<STRIKETHROUGH_TEXT>[^-].*?)(?<!\\)-{2})',
            ('ESCAPE', 'BOLD', 'ITALICS', 'UNDERLINE', 'SUPERSCRIPT', 'SUBSCRIPT')),
        RegexRule(
            'SUPERSCRIPT',
            r'(?P<SUPERSCRIPT>(?<!\\)\^{2}(?P<SUPERSCRIPT_TEXT>[^^].*?)(?<!\\)\^{2})',
            ('ESCAPE', 'BOLD', 'ITALICS', 'UNDERLINE', 'STRIKETHROUGH')),
        RegexRule(
            'SUBSCRIPT',
            r'(?P<SUBSCRIPT>(?<!\\)~{2}(?P<SUBSCRIPT_TEXT>[^~].*?)(?<!\\)~{2})',
            ('ESCAPE', 'BOLD', 'ITALICS', 'UNDERLINE', 'STRIKETHROUGH')),
        RegexRule('HORIZ_RULE', r'(?P<HORIZ_RULE>^-{4,}$)'),
    )

    def __init__(self, patterns=DEFAULT_PATTERNS):
        self.patterns = {p.name: p for p in patterns}

        self.regexes = {None: re.compile(
                '|'.join(map(attrgetter('pattern'), self.DEFAULT_PATTERNS)), flags=re.DOTALL | re.MULTILINE
        )}
        for p in self.patterns.values():
            if p.descent_rules:
                self.regexes[p.name] = re.compile(
                    '|'.join(self.patterns[r].pattern for r in p.descent_rules), flags=re.DOTALL | re.MULTILINE
                )
            if not p.func: p.func = getattr(self, f'parse_{p.name}', self.parse_DEFAULT)

    def parse(self, text, descent_rule=None):
        output = ''

        while True:
            match = self.regexes[descent_rule].search(text)
            if not match: break
            output += text[:match.start()] + self.patterns[match.lastgroup].func(match)
            text = text[match.end():]

        return output + text

    def parse_DEFAULT(self, match):
        return match[0]

    def parse_CODE(self, match):
        return '<code>{}</code>'.format(match['CODE_TEXT'])

    def parse_ESCAPE(self, match):
        return match['ESCAPE_TEXT']

    def parse_LINK(self, match):
        result = 'LINKTO:{}'.format(match['URL'])
        if match['DESCRIPTION']: result += ':{}'.format(self.parse(match['DESCRIPTION'], 'LINK'))
        if match['EXTENSIONS']:
            extensions = [e.lower().lstrip('#') for e in match['EXTENSIONS'].split('|') if e]
            for k, v in {'spoiler': ':SPOILER', 'nsfw': ':NSFW', 'latex': ':LaTeX'}.items():
                if k in extensions: result += v
        return result

    def parse_USER_MENTION(self, match):
        return 'LINKTOUSER:{}'.format(match['USERNAME'])

    with open('emoji.json', 'rt') as f:
        EMOJIS = json.load(f)

    def parse_EMOJI(self, match):
        return match[0]

    def parse_TABLE(self, match):
        return match[0]

    def parse_BULLET_LIST(self, match):
        return match[0]

    def parse_NUMBER_LIST(self, match):
        return match[0]

    def parse_HEADING(self, match):
        return match[0]

    def parse_BOLD(self, match):
        return '<b>{}</b>'.format(self.parse(match['BOLD_TEXT'], 'BOLD'))

    def parse_ITALICS(self, match):
        return '<i>{}</i>'.format(self.parse(match['ITALICS_TEXT'], 'ITALICS'))

    def parse_UNDERLINE(self, match):
        return '<u>{}</u>'.format(self.parse(match['UNDERLINE_TEXT'], 'UNDERLINE'))

    def parse_STRIKETHROUGH(self, match):
        return '<str>{}</str>'.format(self.parse(match['STRIKETHROUGH_TEXT'], 'STRIKETHROUGH'))

    def parse_SUPERSCRIPT(self, match):
        return '<sup>{}</sup>'.format(self.parse(match['SUPERSCRIPT_TEXT'], 'SUPERSCRIPT'))

    def parse_SUBSCRIPT(self, match):
        return '<sub>{}</sub>'.format(self.parse(match['SUBSCRIPT_TEXT'], 'SUBSCRIPT'))

    def parse_HORIZ_RULE(self, match):
        return '|' * 10
