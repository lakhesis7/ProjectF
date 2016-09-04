from collections import OrderedDict
import re

re_USERNAME_MENTIONS = re.compile(r'(?<!\\)\B@(?P<USERNAME>[a-zA-Z0-9][a-zA-Z0-9_]{2,24})\b')
def transform_username_mentions(m):
    return {
        'type': 'link',
        'prefix': '''<a href='/@{}'>{}</a>'''.format(m.group('USERNAME'), m.group()),
        'suffix': '',
        'children': [],
    }

re_BOLD_ITALICS = re.compile(r'(?s)(?<!\\)(?P<FORMATTING>\*+)(?P<TEXT>[^*].*?)(?<!\\)\1')
def transform_bold_italics(m):
    tag_length = len(m.group('FORMATTING'))
    return {
        'type': 'italics' if tag_length == 1 else 'bold' if tag_length == 2 else 'bold_italics',
        'prefix': '<i>' if tag_length == 1 else '<b>' if tag_length == 2 else '<b><i>',
        'suffix': '</i>' if tag_length == 1 else '</b>' if tag_length == 2 else '</i></b>',
        'children': [parse(m.group('TEXT'))]
    }

re_CODE_BLOCK = re.compile(r'(?s)(?<!\\)(?P<FORMATTING>`+)(?P<TEXT>[^`].*?)(?<!\\)\1')
def transform_code_block(m):
    return '<code>{}</code>'.format(m.group('TEXT'))

re_EMOTES = re.compile(r'(?<!\\)\B:(?P<EMOTE>[a-zA-Z0-9_]+?):')
def transform_emotes(m):
    return '<img {}>'.format(m.group('EMOTE'))

re_LINKS = re.compile(r'(?si)(?P<IS_IMAGE>!)?(?<!\\)\[\[(?P<LINK>\S+?)( (?P<CAPTION>.*?))?(?<!\\)\]\]')
def transform_links(m):
    return '<a {}{}>{}</a>'.format(
            'image:' if m.group('IS_IMAGE') else '',
            m.group('LINK'),
            parse(m.group('CAPTION'), safe=False) or m.group('LINK')
    )

regexes = OrderedDict()
regexes['code'] = (re.compile(r'(?s)(?<!\\)(?P<FORMATTING>`+)(?P<TEXT>[^`].*?)(?<!\\)\1'), transform_code_block)

def parse(*args, **kwargs): pass