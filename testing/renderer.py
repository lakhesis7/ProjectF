import re

re_USERNAME_MENTIONS = re.compile(r'(?<!\\)\B@(?P<USERNAME>[a-zA-Z0-9][a-zA-Z0-9_]{2,24})\b')
def transform_username_mentions(m):
    return 'user:' + m.group('USERNAME')

re_BOLD_ITALICS = re.compile(r'(?ms)(?<!\\)((?P<BOLD_ITALICS>\*{3})|(?P<BOLD>\*{2})|(?P<ITALICS>\*))(?P<TEXT>.*?)\1')
def transform_bold_italics(m):
    if m.group('BOLD_ITALICS'): return '<b><i>{}</i></b>'.format(parse(m.group('TEXT'), safe=True))
    elif m.group('BOLD'): return '<b>{}</b>'.format(parse(m.group('TEXT'), safe=True))
    else: return '<i>{}</i>'.format(parse(m.group('TEXT'), safe=True))

re_CODE_BLOCK = re.compile(r'(?s)(?<!\\)`(?P<TEXT>.*?)(?!\\)`')
def transform_code_block(m):
    return '<code>{}</code>'.format(m.group('TEXT'))

re_EMOTES = re.compile(r'(?<!\\)\B:(?P<EMOTE>[a-zA-Z0-9_]+?):')
def transform_emotes(m):
    return '<img {}>'.format(m.group('EMOTE'))

re_LINKS = re.compile(r'(?si)(?P<IS_IMAGE>!)?(?<!\\)\[(?P<LINK>\S+?)( (?P<CAPTION>.*?))?(?<!\\)\]')
def transform_links(m):
    return '<a {}{}>{}</a>'.format(
            'image:' if m.group('IS_IMAGE') else '',
            m.group('LINK'),
            parse(m.group('CAPTION'), safe=True) or m.group('LINK')
    )

re_SPOILERS = re.compile(r'(?<!\\)~~(?P<TEXT>.+)(?<!\\)~~')
def transform_spoilers(m):
    return '<spoiler>{}</spoiler>'.format(parse(m.group('TEXT')))

FULL_PARSE_REGEXES = (
    (re_USERNAME_MENTIONS, transform_username_mentions),
    (re_BOLD_ITALICS, transform_bold_italics),
    (re_CODE_BLOCK, transform_code_block),
    (re_EMOTES, transform_emotes),
    (re_LINKS, transform_links),
    (re_SPOILERS, transform_spoilers),
)

SAFE_PARSE_REGEXES = (
    (re_BOLD_ITALICS, transform_bold_italics),
    (re_CODE_BLOCK, transform_code_block),
    (re_EMOTES, transform_emotes),
)

def parse(text, safe=False):
    result = ''
    regexes_to_match = SAFE_PARSE_REGEXES if safe else FULL_PARSE_REGEXES

    while text:
        m_min, m_func = None, None
        for regex, func in regexes_to_match:
            m = regex.search(text)
            if m:
                if not m_min or m.start() < m_min.start():
                    m_min = m
                    m_func = func
                    if not m.start(): break

        if m_min:
            result += text[:m_min.start()]
            result += m_func(m_min)
            text = text[m_min.end():]
        else:
            result += text
            break

    return result

from utils.time_this import TimeThis

with TimeThis(): print(parse('''~~[link ]~~'''))
