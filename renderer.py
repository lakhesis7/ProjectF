import re
from emojis import EMOJIs as _EMOJIs
from itertools import chain

# TODO: Implement common rule patterns as customizable classes
class RegexRule:
    def __init__(self, name, pattern, descent_rules=None, transform_func=None, is_default=True,
                 flags=re.DOTALL | re.MULTILINE):
        self.name = name
        self.pattern = pattern
        self.regex = re.compile(pattern, flags=flags)
        self.descent_rules = descent_rules or ()
        self.transform_func = transform_func
        self.is_default = is_default

    def __repr__(self): return f'{self.__class__.__name__}({self.name!r}, {self.pattern!r})'

class InvalidMatch(Exception): pass

class Renderer:
    def __init__(self, patterns):
        self.patterns = {p.name: p for p in patterns}
        self.regexes = {None: re.compile(
                '|'.join(p.pattern for p in self.patterns.values() if p.is_default), flags=re.DOTALL | re.MULTILINE
        )}
        for p in self.patterns.values():
            if p.descent_rules:
                self.regexes[p.name] = re.compile(
                    '|'.join(self.patterns[r].pattern for r in p.descent_rules), flags=re.DOTALL | re.MULTILINE
                )
            if not p.transform_func: p.transform_func = getattr(self, f'transform_{p.name}', self.transform_DEFAULT)

        self.preprocessors = []
        self.postprocessors = []

        for key in dir(self):
            if key.startswith('pre_'): self.preprocessors.append(getattr(self, key))
            elif key.startswith('post_'): self.postprocessors.append(getattr(self, key))

    def parse(self, text):
        if not isinstance(text, str): raise TypeError(f'expected string object, not {text.__class__.__name__}')
        for p in self.preprocessors: text = p(text)
        text = self._parse(text)
        for p in self.postprocessors: text = p(text)
        return text

    def _parse(self, text, descent_rule=None):
        output = ''

        while text:
            match = self.regexes[descent_rule].search(text)
            if not match: break
            try:
                output += text[:match.start()] + self.patterns[match.lastgroup].transform_func(match)
                text = text[match.end():]
            except InvalidMatch:
                output += text[0]
                text = text[1:]

        return output + text

    def transform_DEFAULT(self, match):
        return match[0]

class DefaultRenderer(Renderer):
    def __init__(self):
        super().__init__([
            RegexRule('WHITESPACE', r'(?P<WHITESPACE>^\s+|\s+$)', is_default=False),
            RegexRule('NEWLINE', r'(?P<NEWLINE>\r\n|\r)', is_default=False),
            RegexRule(
                'ESCAPE',
                r'(?<!\\)(?P<ESCAPE>\\(?P<SINGLE_ESCAPE>.)|{{{(?P<BLOCK_ESCAPE>.+?)(?<!\\)}}})',
                is_default=False),
            RegexRule(
                'LINK',
                '(?P<LINK>\[\[(?P<URL>\S+?) *?(\|(?P<DESCRIPTION>.*?)(?P<EXTENSIONS>(\|.*?)*))?\]\])',
                ('ESCAPE', 'EMOJI', 'BOLD', 'ITALICS', 'UNDERLINE', 'STRIKETHROUGH', 'SUPERSCRIPT', 'SUBSCRIPT')),
            RegexRule(
                'USER_MENTION',
                r'(?P<USER_MENTION>@(?P<USERNAME>[a-zA-Z0-9][a-zA-Z0-9_]{2,23}[a-zA-Z0-9]))'),
            RegexRule('EMOJI', r'(?P<EMOJI>:(?P<EMOJI_TEXT>[-+a-zA-Z0-9_]+?):)'),
            RegexRule(
                'TABLE',
                r'(?P<TABLE>(?-s:^\|(.*?\|)+(\n\|(.*?\|)+$)*($|\n)))',
                ('ESCAPE', 'LINK', 'USER_MENTION', 'EMOJI', 'HEADING', 'BULLET_LIST', 'NUMBER_LIST',
                 'BOLD', 'ITALICS', 'UNDERLINE', 'STRIKETHROUGH', 'SUPERSCRIPT', 'SUBSCRIPT')),
            RegexRule('TABLE_ROW_SPLIT', r'(?<=\|)\n', is_default=False),
            RegexRule('TABLE_CELL_SPLIT', r'\|', is_default=False),
            RegexRule(
                'BULLET_LIST',
                r'(?P<BULLET_LIST>^\* .*?$(\n\*+ .*?$)*)',
                ('ESCAPE', 'LINK', 'USER_MENTION', 'EMOJI', 'HEADING', 'BOLD', 'ITALICS', 'UNDERLINE',
                 'STRIKETHROUGH', 'SUPERSCRIPT', 'SUBSCRIPT')),
            RegexRule('BULLET_LIST_SPLIT', r'(?P<BULLET_LIST_SPLIT>(\*+) (.*?)($|\n))', is_default=False),
            RegexRule(
                'NUMBER_LIST',
                r'(?P<NUMBER_LIST>^# .*?$(\n#+ .*?$)*)',
                ('ESCAPE', 'LINK', 'USER_MENTION', 'EMOJI', 'HEADING', 'BOLD', 'ITALICS', 'UNDERLINE',
                 'STRIKETHROUGH', 'SUPERSCRIPT', 'SUBSCRIPT')),
            RegexRule('NUMBER_LIST_SPLIT', r'(?P<NUMBER_LIST_SPLIT>(#+) (.*?)($|\n))', is_default=False),
            RegexRule(
                'HEADING',
                r'(?P<HEADING>^(?P<HEADING_LEVEL>=+) (?P<HEADING_TEXT>.+?$))',
                ('ESCAPE', 'LINK', 'USER_MENTION', 'EMOJI', 'BOLD', 'ITALICS', 'UNDERLINE', 'STRIKETHROUGH',
                 'SUPERSCRIPT',
                 'SUBSCRIPT')),
            RegexRule('HORIZ_RULE', r'(?P<HORIZ_RULE>^-{4,}$)'),
            RegexRule(
                'BOLD',
                r'(?P<BOLD>\*{2}(?P<BOLD_TEXT>.*?)\*{2})',
                ('ESCAPE', 'EMOJI', 'ITALICS', 'UNDERLINE', 'STRIKETHROUGH', 'SUPERSCRIPT', 'SUBSCRIPT')),
            RegexRule(
                'ITALICS',
                r'(?P<ITALICS>/{2}(?P<ITALICS_TEXT>.*?)/{2})',
                ('ESCAPE', 'EMOJI', 'BOLD', 'UNDERLINE', 'STRIKETHROUGH', 'SUPERSCRIPT', 'SUBSCRIPT')),
            RegexRule(
                'UNDERLINE',
                r'(?P<UNDERLINE>_{2}(?P<UNDERLINE_TEXT>.*?)_{2})',
                ('ESCAPE', 'EMOJI', 'BOLD', 'ITALICS', 'STRIKETHROUGH', 'SUPERSCRIPT', 'SUBSCRIPT',)),
            RegexRule(
                'STRIKETHROUGH',
                r'(?P<STRIKETHROUGH>-{2}(?P<STRIKETHROUGH_TEXT>.*?)-{2})',
                ('ESCAPE', 'EMOJI', 'BOLD', 'ITALICS', 'UNDERLINE', 'SUPERSCRIPT', 'SUBSCRIPT')),
            RegexRule(
                'SUPERSCRIPT',
                r'(?P<SUPERSCRIPT>\^{2}(?P<SUPERSCRIPT_TEXT>.*?)\^{2})',
                ('ESCAPE', 'EMOJI', 'BOLD', 'ITALICS', 'UNDERLINE', 'STRIKETHROUGH')),
            RegexRule(
                'SUBSCRIPT',
                r'(?P<SUBSCRIPT>~{2}(?P<SUBSCRIPT_TEXT>.*?)~{2})',
                ('ESCAPE', 'EMOJI', 'BOLD', 'ITALICS', 'UNDERLINE', 'STRIKETHROUGH')),
        ])

    nonprintable_table = {c: None for c in chain(range(0, 32), range(127, 160))}
    def pre_NONPRINTABLE(self, text):
        return text.translate(self.nonprintable_table)

    def pre_WHITESPACE(self, text):
        return self.patterns['WHITESPACE'].regex.sub('', text)

    escape_groups = []
    def pre_ESCAPE(self, text):
        self.escape_groups = list(self.patterns['ESCAPE'].regex.finditer(text))
        return self.patterns['ESCAPE'].regex.sub('\x00', text)

    def post_ESCAPE(self, text):
        for m in self.escape_groups:
            text = text.replace('\x00', m['SINGLE_ESCAPE'] or m['BLOCK_ESCAPE'], 1)
        return text

    def pre_NEWLINES(self, text):
        return self.patterns['NEWLINE'].regex.sub('\n', text)

    def transform_LINK(self, match):
        if '\x00' in match['URL']: raise InvalidMatch(match[0])
        result = 'LINKTO:{}'.format(match['URL'])
        if match['DESCRIPTION']: result += ':{}'.format(self._parse(match['DESCRIPTION'], 'LINK'))
        if match['EXTENSIONS']:
            extensions = [e.lower().lstrip('#') for e in match['EXTENSIONS'].split('|') if e]
            for k, v in {'spoiler': ':SPOILER', 'nsfw': ':NSFW', 'latex': ':LaTeX'}.items():
                if k in extensions: result += v
        return result

    def transform_USER_MENTION(self, match):
        return 'LINKTOUSER:{}'.format(match['USERNAME'])

    def transform_EMOJI(self, match):
        try: return _EMOJIs[match[0].lower()]
        except KeyError: raise InvalidMatch(match[0])

    def transform_TABLE(self, match):
        rows = self.patterns['TABLE_ROW_SPLIT'].regex.split(match[0])
        output = '<table>'
        for row in rows:
            output += '<tr>'
            for cell in self.patterns['TABLE_CELL_SPLIT'].regex.split(row)[1:-1]:
                output += f'<td>{cell}</td>'
            output += '</tr>'
        return output + '</table>'

    def transform_BULLET_LIST(self, match):
        rows = [(len(m[0]), self._parse(m[1], 'BULLET_LIST'))
                for m in self.patterns['BULLET_LIST_SPLIT'].regex.findall(match[0])]
        current_level = 0
        output = ''

        for row in rows:
            if row[0] > current_level:
                if row[0] - current_level > 1: raise InvalidMatch(match[0])
                output += '<ul><li>' + row[1]
            elif row[0] < current_level:
                output += '</li></ul>' * (current_level - row[0]) + '<li>' + row[1]
            else: output += '</li><li>' + row[1]
            current_level = row[0]
        return output + '</li></ul>' * current_level

    def transform_NUMBER_LIST(self, match):
        rows = [(len(m[0]), self._parse(m[1], 'NUMBER_LIST'))
                for m in self.patterns['NUMBER_LIST_SPLIT'].regex.findall(match[0])]
        types = ['1', 'a', 'i']
        current_level = 0
        output = ''

        for row in rows:
            if row[0] > current_level:
                if row[0] - current_level > 1: raise InvalidMatch(match[0])
                output += f'<ol type="{types[current_level % len(types)]}"><li>' + row[1]
            elif row[0] < current_level:
                output += '</li></ol>' * (current_level - row[0]) + '<li>' + row[1]
            else: output += '</li><li>' + row[1]
            current_level = row[0]
        return output + '</li></ol>' * current_level

    def transform_HEADING(self, match):
        level = min(len(match["HEADING_LEVEL"]), 6)
        return f'<h{level}>{match["HEADING_TEXT"]}</h{level}>'

    def transform_BOLD(self, match):
        if not match['BOLD_TEXT']: return ''
        return '<b>{}</b>'.format(self._parse(match['BOLD_TEXT'], 'BOLD'))

    def transform_ITALICS(self, match):
        if not match['ITALICS_TEXT']: return ''
        return '<i>{}</i>'.format(self._parse(match['ITALICS_TEXT'], 'ITALICS'))

    def transform_UNDERLINE(self, match):
        if not match['UNDERLINE_TEXT']: return ''
        return '<u>{}</u>'.format(self._parse(match['UNDERLINE_TEXT'], 'UNDERLINE'))

    def transform_STRIKETHROUGH(self, match):
        if not match['STRIKETHROUGH_TEXT']: return ''
        return '<s>{}</s>'.format(self._parse(match['STRIKETHROUGH_TEXT'], 'STRIKETHROUGH'))

    def transform_SUPERSCRIPT(self, match):
        if not match['SUPERSCRIPT_TEXT']: return ''
        return '<sup>{}</sup>'.format(self._parse(match['SUPERSCRIPT_TEXT'], 'SUPERSCRIPT'))

    def transform_SUBSCRIPT(self, match):
        if not match['SUBSCRIPT_TEXT']: return ''
        return '<sub>{}</sub>'.format(self._parse(match['SUBSCRIPT_TEXT'], 'SUBSCRIPT'))

    def transform_HORIZ_RULE(self, match):
        return '<hr>'

# TODO: """(?P<URL_VALIDATOR>[-a-zA-Z0-9@:%_\+.~#?&//=]{2,256}\.[A-Za-z]{2,4}\b(\/[-a-zA-Z0-9@:%_\+.~#?&//=]*)?)"""
