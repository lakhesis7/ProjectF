import html
import re
import string
from utils.emojis import EMOJIs

class MissingPattern(Exception): pass

class InvalidMatch(Exception): pass

class Renderer:
    def __init__(self,
                 pre_processors=(),
                 patterns=(),
                 descent_rules=(),
                 transforms=(),
                 post_processors=()):
        self._pre_processors = pre_processors
        self._patterns = patterns
        self._descent_rules = descent_rules
        self._transforms = transforms
        self._post_processors = post_processors
        self._descent_regexes = {}

        for name, descendees in self._descent_rules.items():
            if descendees: self._descent_regexes[name] = re.compile(
                pattern='|'.join(self._patterns[descendee_name] for descendee_name in descendees),
                flags=re.DOTALL | re.MULTILINE,
            )

    def parse(self, text):
        for p in self._pre_processors: text = p(text)
        text = self._parse(text)
        for p in self._post_processors: text = p(text)
        return text

    def _parse(self, text, rule=None):
        output = []
        current_pos, text_length = 0, len(text)

        while current_pos < text_length:
            match = self._descent_regexes[rule].search(text, current_pos)
            if not match: break
            try:
                chunk = (text[current_pos:match.start()], self._transforms[match.lastgroup](match))
                output.extend(chunk)
                current_pos = match.end()
            except InvalidMatch:
                output.append(text[0])
                current_pos += 1
        if not output: return text
        output.append(text[current_pos:])
        return ''.join(output)

class DefaultRenderer(Renderer):
    def __init__(self):
        super().__init__(
            pre_processors=(
                self._pre_NON_PRINTABLE,
                self._pre_WHITESPACE,
                self._pre_NEWLINE,
                self._pre_HTML_ESCAPE,
            ),
            patterns={
                'CODE'        : r'(?P<CODE>(?<!\\)\{\{\{(?P<CODE_TEXT>.*?)\}\}\})',
                'LINK'        : r'(?P<LINK>(?<!\\)\[\['
                                r'(?P<LINK_DESCRIPTION>\s*[^\|]+?\s*)'
                                r'((?<!\\)\|(?P<LINK_URL>\s*(?i:https?:\/\/)[^\s]+?\s*)?)'
                                r'((?<!\\)\|(?P<LINK_EXTENSTIONS>.*?((?<!\\)\|.*?)*))?'
                                r'\]\])',
                'USER_MENTION': r'(?P<USER_MENTION>(?<!\\)@(?P<USERNAME>[a-zA-Z0-9][a-zA-Z0-9_]{2,23}[a-zA-Z0-9]))',
                'EMOJI'       : r'(?P<EMOJI>(?<!\\):(?P<EMOJI_TEXT>[-+a-zA-Z0-9_]+?):)',
                'TABLE'       : r'(?P<TABLE>^(?:(?P<TABLE_HAS_HEADER>=)?)(?-s:\|(.*?\|)+(\n\|(.*?\|)+$)*($|\n)))',
                'BULLET_LIST' : r'(?P<BULLET_LIST>^(?<!\\)\* .*?$(\n\*+ .*?$)*)',
                'NUMBER_LIST' : r'(?P<NUMBER_LIST>^(?<!\\)# .*?$(\n#+ .*?$)*)',
                'HEADING'     : r'(?P<HEADING>^(?P<HEADING_LEVEL>(?<!\\)=+) (?P<HEADING_TEXT>.+?$))',
                'HORIZ_RULE'  : r'(?P<HORIZ_RULE>^-{4,}$)',
                'BOLD'        : r'(?P<BOLD>(?<!\\)\*\*(?P<BOLD_TEXT>.*?)(?<!\\)\*\*)',
                'ITALICS'     : r'(?P<ITALICS>(?<!\\)//(?P<ITALICS_TEXT>.*?)(?<!\\)//)',
                'UNDERLINE'   : r'(?P<UNDERLINE>(?<!\\)__(?P<UNDERLINE_TEXT>.*?)(?<!\\)__)',
                'STRIKED'     : r'(?P<STRIKED>(?<!\\)--(?P<STRIKED_TEXT>.*?)(?<!\\)--)',
                'SUPERSCRIPT' : r'(?P<SUPERSCRIPT>(?<!\\)\^\^(?P<SUPERSCRIPT_TEXT>.*?)(?<!\\)\^\^)',
                'SUBSCRIPT'   : r'(?P<SUBSCRIPT>(?<!\\)~~(?P<SUBSCRIPT_TEXT>.*?)(?<!\\)~~)',
            },
            descent_rules={
                None          : ('CODE', 'LINK', 'USER_MENTION', 'EMOJI', 'TABLE', 'BULLET_LIST', 'NUMBER_LIST',
                                 'HEADING', 'HORIZ_RULE', 'BOLD', 'ITALICS', 'UNDERLINE', 'STRIKED', 'SUPERSCRIPT',
                                 'SUBSCRIPT'),
                'CODE'        : (),
                'LINK'        : ('EMOJI', 'BOLD', 'ITALICS', 'UNDERLINE', 'STRIKED', 'SUPERSCRIPT', 'SUBSCRIPT'),
                'USER_MENTION': (),
                'EMOJI'       : (),
                'TABLE'       : ('LINK', 'USER_MENTION', 'EMOJI', 'HEADING', 'BULLET_LIST', 'NUMBER_LIST',
                                 'BOLD', 'ITALICS', 'UNDERLINE', 'STRIKED', 'SUPERSCRIPT', 'SUBSCRIPT'),
                'BULLET_LIST' : ('LINK', 'USER_MENTION', 'EMOJI', 'HEADING', 'BOLD', 'ITALICS', 'UNDERLINE', 'STRIKED',
                                 'SUPERSCRIPT', 'SUBSCRIPT'),
                'NUMBER_LIST' : ('LINK', 'USER_MENTION', 'EMOJI', 'HEADING', 'BOLD', 'ITALICS', 'UNDERLINE', 'STRIKED',
                                 'SUPERSCRIPT', 'SUBSCRIPT'),
                'HEADING'     : ('LINK', 'USER_MENTION', 'EMOJI', 'BOLD', 'ITALICS', 'UNDERLINE', 'STRIKED',
                                 'SUPERSCRIPT', 'SUBSCRIPT'),
                'HORIZ_RULE'  : (),
                'BOLD'        : ('EMOJI', 'ITALICS', 'UNDERLINE', 'STRIKED', 'SUPERSCRIPT', 'SUBSCRIPT'),
                'ITALICS'     : ('EMOJI', 'BOLD', 'UNDERLINE', 'STRIKED', 'SUPERSCRIPT', 'SUBSCRIPT'),
                'UNDERLINE'   : ('EMOJI', 'BOLD', 'ITALICS', 'STRIKED', 'SUPERSCRIPT', 'SUBSCRIPT'),
                'STRIKED'     : ('EMOJI', 'BOLD', 'ITALICS', 'UNDERLINE', 'SUPERSCRIPT', 'SUBSCRIPT'),
                'SUPERSCRIPT' : ('EMOJI', 'BOLD', 'ITALICS', 'UNDERLINE', 'STRIKED'),
                'SUBSCRIPT'   : ('EMOJI', 'BOLD', 'ITALICS', 'UNDERLINE', 'STRIKED'),

            },
            transforms={
                'CODE'        : self._transform_CODE,
                'LINK'        : self._transform_LINK,
                'USER_MENTION': self._transform_USER_MENTION,
                'EMOJI'       : self._transform_EMOJI,
                'TABLE'       : self._transform_TABLE,
                'BULLET_LIST' : self._transform_BULLET_LIST,
                'NUMBER_LIST' : self._transform_NUMBER_LIST,
                'HEADING'     : self._transform_HEADING,
                'HORIZ_RULE'  : self._transform_HORIZ_RULE,
                'BOLD'        : self._transform_BOLD,
                'ITALICS'     : self._transform_ITALICS,
                'UNDERLINE'   : self._transform_UNDERLINE,
                'STRIKED'     : self._transform_STRIKED,
                'SUPERSCRIPT' : self._transform_SUPERSCRIPT,
                'SUBSCRIPT'   : self._transform_SUBSCRIPT,
            },
            post_processors=(
                self._post_BACKSLASH_UNESCAPE,
            ),
        )

        self._emojis = EMOJIs
        self._pipe_split = re.compile(r'(?<!\\)\|')
        self._non_printable_table = {c: None for c in range(160) if chr(c) not in string.printable}
        # self._whitespace_re = re.compile(r'^\s+|\s+$')
        self._newline_re = re.compile(r'\r\n?')
        self._table_row_split = re.compile(r'(?<=(?<!\\)\|)\n')
        self._bullet_list_split_re = re.compile(r'(\*+) (.*?)($|(?<!\\)\n)')
        self._number_list_split_re = re.compile(r'(#+) (.*?)($|(?<!\\)\n)')
        self._backslash_escape_re = re.compile(r'\\([-\\{}\[\]:@#*/_^~|])')

    def _pre_NON_PRINTABLE(self, text):
        return text.translate(self._non_printable_table)

    def _pre_WHITESPACE(self, text):
        # return self._whitespace_re.sub('', text)
        return text.strip()

    def _pre_NEWLINE(self, text):
        return self._newline_re.sub('\n', text)

    def _pre_HTML_ESCAPE(self, text):
        return html.escape(text)

    def _transform_CODE(self, match):
        return f'<code>{match["CODE_TEXT"]}</code>'

    def _transform_LINK(self, match):
        result = '['
        if match['LINK_URL']: result += f'link to {match["LINK_URL"]} with '
        result += f'text {match["LINK_DESCRIPTION"]}'
        if match['LINK_EXTENSIONS']:
            exts = list(filter(None, self._pipe_split.split(match['LINK_EXTENSIONS'])))
            if exts: result += f' with attributes {"".join(exts)}'
        return result + ']'

    def _transform_USER_MENTION(self, match):
        return f'[link to user {match["USER_MENTION"]}]'

    def _transform_EMOJI(self, match):
        try:
            return self._emojis[match['EMOJI']]
        except KeyError:
            raise InvalidMatch(match['EMOJI'])

    def _transform_TABLE(self, match):
        rows = self._table_row_split.split(match['TABLE'])
        output = '<table>'
        if match['TABLE_HAS_HEADER']:
            row = rows.pop(0)
            output += '<thead><tr>'
            for cell in self._pipe_split.split(row)[1:-1]:
                output += f'<th>{self._parse(cell, "TABLE")}</th>'
            output += '</tr></thead>'
        if not rows: return output + '</table>'

        output += '<tbody>'
        for row in rows:
            output += '<tr>'
            for cell in self._pipe_split.split(row)[1:-1]:
                output += f'<td>{self._parse(cell, "TABLE")}</td>'
            output += '</tr>'
        return output + '</tbody></table>'

    def _transform_BULLET_LIST(self, match):
        rows = [(len(m[0]), self._parse(m[1], 'BULLET_LIST')) for m in self._bullet_list_split_re.findall(match[0])]
        current_level = 0
        output = ''

        for row in rows:
            if row[0] > current_level:
                if row[0] - current_level > 1: raise InvalidMatch(match[0])
                output += '<ul><li>' + row[1]
            elif row[0] < current_level:
                output += '</li></ul>' * (current_level - row[0]) + '<li>' + row[1]
            else:
                output += '</li><li>' + row[1]
            current_level = row[0]
        return output + '</li></ul>' * current_level

    def _transform_NUMBER_LIST(self, match):
        rows = [(len(m[0]), self._parse(m[1], 'NUMBER_LIST')) for m in self._number_list_split_re.findall(match[0])]
        types = ['1', 'a', 'i']
        current_level = 0
        output = ''

        for row in rows:
            if row[0] > current_level:
                if row[0] - current_level > 1: raise InvalidMatch(match[0])
                output += f'<ol type="{types[current_level % len(types)]}"><li>' + row[1]
            elif row[0] < current_level:
                output += '</li></ol>' * (current_level - row[0]) + '<li>' + row[1]
            else:
                output += '</li><li>' + row[1]
            current_level = row[0]
        return output + '</li></ol>' * current_level

    def _transform_HEADING(self, match):
        level = min(len(match["HEADING_LEVEL"]), 6)
        return f'<h{level}>{match["HEADING_TEXT"]}</h{level}>'

    def _transform_BOLD(self, match):
        if not match['BOLD_TEXT']: return ''
        return '<b>{}</b>'.format(self._parse(match['BOLD_TEXT'], 'BOLD'))

    def _transform_ITALICS(self, match):
        if not match['ITALICS_TEXT']: return ''
        return '<i>{}</i>'.format(self._parse(match['ITALICS_TEXT'], 'ITALICS'))

    def _transform_UNDERLINE(self, match):
        if not match['UNDERLINE_TEXT']: return ''
        return '<u>{}</u>'.format(self._parse(match['UNDERLINE_TEXT'], 'UNDERLINE'))

    def _transform_STRIKED(self, match):
        if not match['STRIKED_TEXT']: return ''
        return '<s>{}</s>'.format(self._parse(match['STRIKED_TEXT'], 'STRIKED'))

    def _transform_SUPERSCRIPT(self, match):
        if not match['SUPERSCRIPT_TEXT']: return ''
        return '<sup>{}</sup>'.format(self._parse(match['SUPERSCRIPT_TEXT'], 'SUPERSCRIPT'))

    def _transform_SUBSCRIPT(self, match):
        if not match['SUBSCRIPT_TEXT']: return ''
        return '<sub>{}</sub>'.format(self._parse(match['SUBSCRIPT_TEXT'], 'SUBSCRIPT'))

    def _transform_HORIZ_RULE(self, match):
        return '<hr />'

    def _post_BACKSLASH_UNESCAPE(self, text):
        return self._backslash_escape_re.sub(r'\1', text)

d = DefaultRenderer()
