import json
import re

# TODO: Implement common rule patterns as customizable classes
class RegexRule:
    def __init__(self, name, pattern, descent_rules=None, func=None, is_default=True, flags=re.DOTALL | re.MULTILINE):
        self.name = name
        self.pattern = pattern
        self.regex = re.compile(pattern, flags=flags)
        self.descent_rules = descent_rules or ()
        self.func = func
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
            if not p.func: p.func = getattr(self, f'_parse_{p.name}', self._parse_DEFAULT)

        self.preprocessors = []
        self.postprocessors = []

        for key in dir(self):
            if key.startswith('pre_'): self.preprocessors.append(getattr(self, key))
            elif key.startswith('post_'): self.postprocessors.append(getattr(self, key))

    def parse(self, text):
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
                output += text[:match.start()] + self.patterns[match.lastgroup].func(match)
                text = text[match.end():]
            except InvalidMatch:
                output += text[0]
                text = text[1:]

        return output + text

    def _parse_DEFAULT(self, match):
        return match[0]

class DefaultRenderer(Renderer):
    def __init__(self):
        super().__init__([
            RegexRule('EDGE_WHITESPACE', r'(?P<EDGE_WHITESPACE>(?-m:^\s+|\s+$))'),
            RegexRule('NEWLINE', r'(?P<NEWLINE>\r\n|\r)'),
            RegexRule('CODE', r'(?P<CODE>(?<!\\){{3}(?P<CODE_TEXT>[^{}].*?)(?<!\\)}{3})'),
            RegexRule('ESCAPE', r'(?P<ESCAPE>\\(?P<ESCAPE_TEXT>[-\\*\[\]_^=\n{}]))'),
            RegexRule(
                'LINK',
                r'(?P<LINK>'
                r'(?<!\\)\[\['
                r'(?P<URL>\S+?) *?'
                r'(\|(?P<DESCRIPTION>.*?)(?P<EXTENSIONS>((?<!\\)\|.*?)*))?'
                r'(?<!\\)\]\])',
                ('ESCAPE', 'EMOJI', 'BOLD', 'ITALICS', 'UNDERLINE', 'STRIKETHROUGH', 'SUPERSCRIPT', 'SUBSCRIPT')),
            RegexRule(
                'USER_MENTION',
                r'(?P<USER_MENTION>(?<!\\)@(?P<USERNAME>[a-zA-Z0-9][a-zA-Z0-9_]{2,23}[a-zA-Z0-9]))'),
            RegexRule('EMOJI', r'(?P<EMOJI>:(?P<EMOJI_TEXT>[-+a-zA-Z0-9_]+?):)'),
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
                ('ESCAPE', 'LINK', 'USER_MENTION', 'EMOJI', 'BOLD', 'ITALICS', 'UNDERLINE', 'STRIKETHROUGH',
                 'SUPERSCRIPT',
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
                ('ESCAPE', 'BOLD', 'ITALICS', 'STRIKETHROUGH', 'SUPERSCRIPT', 'SUBSCRIPT',)),
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
        ])

        self.emojis = {}
        with open('eac.json', 'rt') as f:
            for key, value in json.load(f).items():
                if '-' in key: key = ''.join(chr(int(x, base=16)) for x in key.split('-'))
                else: key = chr(int(key, base=16))
                self.emojis[value['alpha_code']] = key
                if value['aliases']:
                    for alias in value['aliases'].split('|'):
                        self.emojis[alias] = key

    def _parse_EDGE_WHITESPACE(self, match):
        return ''

    def _parse_NEWLINE(self, match): return '\n'

    def _parse_CODE(self, match):
        return '<code>{}</code>'.format(match['CODE_TEXT'])

    def _parse_ESCAPE(self, match):
        return match['ESCAPE_TEXT']

    def _parse_LINK(self, match):
        result = 'LINKTO:{}'.format(match['URL'])
        if match['DESCRIPTION']: result += ':{}'.format(self._parse(match['DESCRIPTION'], 'LINK'))
        if match['EXTENSIONS']:
            extensions = [e.lower().lstrip('#') for e in match['EXTENSIONS'].split('|') if e]
            for k, v in {'spoiler': ':SPOILER', 'nsfw': ':NSFW', 'latex': ':LaTeX'}.items():
                if k in extensions: result += v
        return result

    def _parse_USER_MENTION(self, match):
        return 'LINKTOUSER:{}'.format(match['USERNAME'])

    def _parse_EMOJI(self, match):
        try: return self.emojis[match[0].lower()]
        except KeyError: raise InvalidMatch(match[0])

    def _parse_TABLE(self, match):
        return match[0]

    def _parse_BULLET_LIST(self, match):
        return match[0]

    def _parse_NUMBER_LIST(self, match):
        return match[0]

    def _parse_HEADING(self, match):
        return match[0]

    def _parse_BOLD(self, match):
        return '<b>{}</b>'.format(self._parse(match['BOLD_TEXT'], 'BOLD'))

    def _parse_ITALICS(self, match):
        return '<i>{}</i>'.format(self._parse(match['ITALICS_TEXT'], 'ITALICS'))

    def _parse_UNDERLINE(self, match):
        return '<u>{}</u>'.format(self._parse(match['UNDERLINE_TEXT'], 'UNDERLINE'))

    def _parse_STRIKETHROUGH(self, match):
        return '<str>{}</str>'.format(self._parse(match['STRIKETHROUGH_TEXT'], 'STRIKETHROUGH'))

    def _parse_SUPERSCRIPT(self, match):
        return '<sup>{}</sup>'.format(self._parse(match['SUPERSCRIPT_TEXT'], 'SUPERSCRIPT'))

    def _parse_SUBSCRIPT(self, match):
        return '<sub>{}</sub>'.format(self._parse(match['SUBSCRIPT_TEXT'], 'SUBSCRIPT'))

    def _parse_HORIZ_RULE(self, match):
        return '|' * 10

# TODO: """(?P<URL_VALIDATOR>[-a-zA-Z0-9@:%_\+.~#?&//=]{2,256}\.[A-Za-z]{2,4}\b(\/[-a-zA-Z0-9@:%_\+.~#?&//=]*)?)"""
