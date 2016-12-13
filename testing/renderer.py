import re
import json
from collections import OrderedDict
from utils.time_this import TimeThis

class Rule:
    tag = None
    regex = None
    rules = ()

    def transform(self, match): pass

    def parse(self, text, rules=None): pass

class EscapedChar(Rule):
    tag = 'escaped'
    regex = re.compile(r'\\([\\*{\[\]}_^=-])')

    def transform(self, match): return match.group(1)

class CodeBlock(Rule):
    tag = 'code'
    regex = re.compile(r'\B{{{([^{}](.|\n)*?)}}}\B')

    def transform(self, match): return 'CC{}CC'.format(match.group(1))

class Link(Rule):
    tag = 'link'
    regex = re.compile(r'\[\[(\S+)( (\S+))?\]\]')

    def transform(self, match): return match.group()

class UserMention(Rule):
    tag = 'user_mention'
    regex = re.compile(r'(@([a-zA-Z0-9][a-zA-Z0-9_]{2,23}[a-zA-Z0-9]))')

    def transform(self, match): return '@@{}@@'.format(match.group(2))

class Emoji(Rule):
    tag = 'emoji'
    regex = re.compile(r':(\w+):')

    with open('emoji.json', 'rt') as f:
        emojis = json.load(f)

    def transform(self, match):
        try: return ''.join(chr(int(u, base=16)) for u in self.emojis[match.group(1)]['unicode'].split('-'))
        except KeyError: return self.parse(match.group(1), self.rules)  # TODO

class BoldItalics(Rule):
    tag = 'bold_italics'
    regex = re.compile(r'(\*{1,3})([^*].*?)(\1)')
    rules = ('bold_italics', 'subscript')

    def transform(self, match):
        format_str = ('i{}i', 'b{}b', 'bi{}ib')[len(match.group(1)) - 1]
        return format_str.format(self.parse(match.group(2), self.rules))

class Subscript(Rule):
    tag = 'subscript'
    regex = re.compile(r'_([^_].*?)_')
    rules = ('bold_italics', 'subscript')

    def transform(self, match): return '<sub>{}</sub>'.format(self.parse(match.group(1), self.rules))

DEFAULT_RULES = (
    EscapedChar(),
    CodeBlock(),
    UserMention(),
    Emoji(),
    BoldItalics(),
    Subscript()
)

class BarkBrown:
    def __init__(self, rules=DEFAULT_RULES):
        self.mapping = OrderedDict()
        for rule in rules: self.mapping[rule.tag] = rule

        for rule in self.mapping.values():
            rule.rules = tuple(self.mapping[r] for r in rule.rules)
            rule.parse = self.parse

    def parse(self, text, rules=None):
        if rules is None: rules = self.mapping.values()

        repls = ['{}'] * text.count('{}')  # Maintain any '{}' within the input text

        for rule in rules:
            while True:
                m = rule.regex.search(text)
                if m is None: break
                repls_start_index = text.count('{}', 0, m.start())
                repls_end_index = repls_start_index + m.group().count('{}')

                # Replacement's for {}'s within the match's text are replaced with the transform text full fleshed out
                repls[repls_start_index: repls_end_index] = [
                    rule.transform(m).format(*repls[repls_start_index: repls_end_index])
                ]

                text = text[:m.start()] + '{}' + text[m.end():]

        return text.format(*repls)
