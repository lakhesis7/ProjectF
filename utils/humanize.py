import datetime as __d

TIMEDELTA_INTERVALS = (
    (__d.timedelta(weeks=52)    , 'year'),
    (__d.timedelta(days=30.4375), 'month'),
    (__d.timedelta(weeks=1)     , 'week'),
    (__d.timedelta(days=1)      , 'day'),
    (__d.timedelta(hours=1)     , 'hour'),
    (__d.timedelta(minutes=1)   , 'minute'),
    (__d.timedelta(seconds=1)   , 'second'),
)

def timedelta(td):
    for unit, unit_name in TIMEDELTA_INTERVALS:
        if unit <= td:
            result = td / unit
            if result != 1.0: unit_name += 's'
            return f'{result:.2g} {unit_name} ago'
    return 'just now'

def datetime(now, other=None):
    if other is None: other = __d.datetime.utcnow()
    return timedelta(other - now)

def strftime(dt=None):
    if dt is None: dt = __d.datetime.now(__d.timezone.utc)
    return f'{dt:%A, %d %B %Y %H:%M:%S %Z}'  # Monday, 02 January 2017 14:25:37 UTC

def humanize_percentage(pct): return f'{pct:3.1%}'
