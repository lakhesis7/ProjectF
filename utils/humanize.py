from datetime import datetime, timedelta

INTERVALS = {
    timedelta(weeks=52)    : 'year',
    timedelta(days=30.4375): 'month',
    timedelta(weeks=1)     : 'week',
    timedelta(days=1)      : 'day',
    timedelta(hours=1)     : 'hour',
    timedelta(minutes=1)   : 'minute',
    timedelta(seconds=1)   : 'second',
}

def convert_timedelta(td):
    for unit, unit_name in INTERVALS.items():
        if unit <= td:
            result = td / unit
            if result != 1.0: unit_name += 's'
            return f'{result:.2g} {unit_name} ago'
    return 'just now'

def convert_datetime(dt, now=None):
    if now is None: now = datetime.utcnow()
    return convert_timedelta(now - dt)
