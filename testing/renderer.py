import json
import re

class RegexRule:
    def __init__(self, name, pattern, descent_rules=None, func=None, flags=re.DOTALL | re.MULTILINE):
        self.name = name
        self.pattern = pattern
        self.regex = re.compile(pattern, flags=flags)
        self.descent_rules = descent_rules or []
        self.func = func

    def __str__(self): return f'{self.__class__.__name__}({self.name!r}, {self.pattern!r})'

    def __repr__(self): return f'{self.__class__.__name__}({self.name!r}, {self.pattern!r})'

class Renderer:
    DEFAULT_PATTERNS = (
        RegexRule('CODE', r'(?P<CODE>(?<!\\){{3}(?P<CODE_TEXT>[^{}].*?)(?<!\\)}{3})', ()),
        RegexRule('ESCAPE', r'(?P<ESCAPE>\\(?P<ESCAPE_TEXT>[-\\*\[\]_^=\n{}]))', ()),
        RegexRule(
            'LINK',
            r'(?P<LINK>\[\[(?P<URL>\S+?) ?(\|(?P<DESCRIPTION>.*?)(?P<EXTENSIONS>(\|.*?)*)\]\])?)',
            ('ESCAPE', 'EMOJI', 'BOLD_ITALICS', 'SUPERSCRIPT', 'SUBSCRIPT')),
        RegexRule(
            'USER_MENTION',
            r'(?P<USER_MENTION>@(?P<USERNAME>[a-zA-Z0-9][a-zA-Z0-9_]{2,23}[a-zA-Z0-9]))',
            ()),
        RegexRule('EMOJI', r'(?P<EMOJI>:(?P<EMOJI_TEXT>\w+):)', ()),  # FIXME: Add specific emoji text regexes
        RegexRule(
            'TABLE',
            r'(?P<TABLE>^(?P<TABLE_FIRSTROW>\|(.*?\|)+?$)(?P<TABLE_OTHERROWS>(\n^\|(.*?\|)+$)+)?)',
            ('ESCAPE', 'CODE', 'LINK', 'USER_MENTION', 'EMOJI', 'HEADING', 'BULLET_LIST', 'NUMBER_LIST',
             'BOLD_ITALICS', 'SUPERSCRIPT', 'SUBSCRIPT')),
        RegexRule(
            'BULLET_LIST',
            r'(?P<BULLET_LIST>^\* (?P<BL_FIRSTROW>.*)(?P<BL_OTHERROWS>(\n\*+ .*)*))',
            ('ESCAPE', 'CODE', 'LINK', 'USER_MENTION', 'EMOJI', 'HEADING', 'BOLD_ITALICS', 'SUPERSCRIPT',
             'SUBSCRIPT')),
        RegexRule(
            'NUMBER_LIST',
            r'(?P<NUMBER_LIST>^# (?P<NL_FIRSTROW>.*)(?P<NL_OTHERROWS>(\n#+ .*)*))',
            ('ESCAPE', 'CODE', 'LINK', 'USER_MENTION', 'EMOJI', 'HEADING', 'BOLD_ITALICS', 'SUPERSCRIPT',
             'SUBSCRIPT')),
        RegexRule(
            'HEADING',
            r'(?P<HEADING>^(?:(?P<HEADING_LEVEL>=+) )(?P<HEADING_TEXT>.+?$))',
            ('ESCAPE', 'CODE', 'LINK', 'USER_MENTION', 'EMOJI', 'BOLD_ITALICS', 'SUPERSCRIPT', 'SUBSCRIPT')),
        RegexRule(
            'BOLD_ITALICS',
            r'(?P<BOLD_ITALICS>(?P<BI_LEVEL>\*{1,3})(?P<BI_TEXT>[^*].*?)(?P=BI_LEVEL))',
            ('BOLD_ITALICS', 'SUPERSCRIPT', 'SUBSCRIPT')),
        RegexRule(
            'SUPERSCRIPT',
            r'(?P<SUPERSCRIPT>\^{2}(?P<SUPERSCRIPT_TEXT>[^^].*?)\^{2})',
            ('BOLD_ITALICS', 'SUPERSCRIPT', 'SUBSCRIPT')),
        RegexRule(
            'SUBSCRIPT',
            r'(?P<SUBSCRIPT>_{2}(?P<SUBSCRIPT_TEXT>[^_].*?)_{2})',
            ('BOLD_ITALICS', 'SUPERSCRIPT', 'SUBSCRIPT')),
        RegexRule('HORIZ_RULE', r'(?P<HORIZ_RULE>^-{3,}$)', ()),
    )

    def __init__(self, patterns=DEFAULT_PATTERNS):
        for p in patterns:
            if not isinstance(p, RegexRule):
                raise TypeError(f'Expected type {RegexRule}, got type {p.__class__}.')

        self.patterns = {p.name: p for p in patterns}

        self.regexes = {None: tuple(self.patterns.values())}
        for p in self.patterns.values():
            self.regexes[p.name] = tuple(map(self.patterns.get, p.descent_rules))
            if not p.func: p.func = getattr(self, f'parse_{p.name}', self.parse_DEFAULT)

    def parse(self, text, descent_rule=None):
        text = text.replace('%', '%%')
        repls = []

        for p in self.regexes[descent_rule]:
            while True:
                match = p.regex.search(text)
                if not match: break

                repls_start_index = sum(1 for r in repls if r[1] < match.start())
                repls_end_index = repls_start_index + sum(1 for r in repls if match.start() <= r[1] <= match.end())
                repls[repls_start_index: repls_end_index] = [
                    (p.func(match) % tuple(r[0] for r in repls[repls_start_index: repls_end_index]), match.start())
                ]

                text = text[:match.start()] + '%s' + text[match.end():]

        return text % tuple(r[0] for r in repls)

    def parse_old(self, text, descent_rule=None):
        repls = ['%s'] * text.count('%s')

        for p in self.regexes[descent_rule]:
            while True:
                m = p.regex.search(text)
                if not m: break

                repls_start_index = text.count('%s', 0, m.start())
                repls_end_index = repls_start_index + m[0].count('%s')
                repls[repls_start_index: repls_end_index] = [
                    p.func(m) % tuple(repls[repls_start_index: repls_end_index])
                ]

                text = text[:m.start()] + '%s' + text[m.end():]

        return text % tuple(repls)

    def parse_DEFAULT(self, match): return match[0]

    def parse_CODE(self, match): return 'CC' + match['CODE_TEXT'] + 'CC'

    def parse_ESCAPE(self, match): return match['ESCAPE_TEXT']

    def parse_LINK(self, match):
        extensions = [e.lower().lstrip('#') for e in match['EXTENSIONS'].split('|') if e]
        result = 'LINKTO:{}'.format(match['URL'])
        if match['DESCRIPTION']: result += ':{}'.format(self.parse(match['DESCRIPTION'], 'LINK'))
        for k, v in {'spoiler': ':SPOILER', 'nsfw': ':NSFW', 'latex': ':LaTeX'}.items():
            if k in extensions: result += v
        return result

    def parse_USER_MENTION(self, match): return 'LINKTOUSER:{}'.format(match['USERNAME'])

    with open('emoji.json', 'rt') as f: EMOJIS = json.load(f)

    def parse_EMOJI(self, match): return match[0]

    def parse_TABLE(self, match): return match[0]

    def parse_BULLET_LIST(self, match): return match[0]

    def parse_NUMBER_LIST(self, match): return match[0]

    def parse_HEADING(self, match): return match[0]

    def parse_BOLD_ITALICS(self, match):
        format_str = ('i{}i', 'b{}b', 'bi{}ib')[len(match['BI_LEVEL']) - 1]
        return format_str.format(self.parse(match['BI_TEXT'], 'BOLD_ITALICS'))

    def parse_SUPERSCRIPT(self, match): return match[0]

    def parse_SUBSCRIPT(self, match): return match[0]

    def parse_HORIZ_RULE(self, match): return match[0]
