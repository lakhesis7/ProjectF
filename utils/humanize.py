from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from typing import Optional

# ############### DATETIME ############### #
TIMEDELTA_INTERVALS = (
    (timedelta(days=365.2425), 'year'),
    (timedelta(days=30.436875), 'month'),
    # (timedelta(days=7), 'week'),
    (timedelta(days=1), 'day'),
    (timedelta(hours=1), 'hour'),
    (timedelta(minutes=1), 'minute'),
    (timedelta(seconds=1), 'second'),
    # (timedelta(milliseconds=1), 'millisecond'),
    # (timedelta(microseconds=1), 'microsecond'),
)

def timedelta_(td: timedelta) -> str:
    for unit, unit_name in TIMEDELTA_INTERVALS:
        if unit <= td:
            return f'''{td / unit:.1f} {unit_name}s ago'''
    return 'just now'

def timedelta_multi(td: timedelta, max_levels=None):
    results = OrderedDict()
    for unit, unit_name in TIMEDELTA_INTERVALS:
        if td // unit != 0: results[unit_name] = td // unit
        td %= unit
    if len(results) == 0: return 'just now'

    if max_levels is None: max_levels = len(results)
    else: max_levels = min(max_levels, len(results))

    string = ''
    for _ in range(1, max_levels):
        unit_name, value = results.popitem(last=False)
        string += f'''{value} {unit_name}{'s' if value != 1 else ''}, '''
    else: string = string[:-2] + ' and '
    unit_name, value = results.popitem(last=False)
    return string + f'''{value} {unit_name}{'s' if value != 1 else ''}'''

def datetime_(dt: datetime, now: Optional[datetime] = None) -> str:
    if now is None: now = datetime.utcnow()
    if dt.tzinfo != now.tzinfo:
        tz = dt.tzinfo or now.tzinfo
        dt, now = dt.astimezone(tz), now.astimezone(tz)
    return timedelta_(now - dt)

def strftime(dt: Optional[datetime] = None) -> str:
    if dt is None: dt = datetime.now(timezone.utc)
    elif dt.tzinfo is None: dt = dt.astimezone(timezone.utc)
    return f'{dt:%A, %d %B %Y %H:%M:%S %Z}'  # Monday, 02 January 2017 14:25:37 UTC

def strptime(string: str) -> datetime:
    return datetime.strptime(string, '%A, %d %B %Y %H:%M:%S %Z')

# ############### NUMBERS ############### #
def percentage(pct: float) -> str: return f'{pct:3.1%}'
