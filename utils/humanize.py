from datetime import datetime, timedelta

_INTERVALS = (
    ('year',   timedelta(weeks=52),     timedelta(weeks=52)),
    ('month',  timedelta(days=30.4375), timedelta(days=30.4375)),
    ('week',   timedelta(weeks=1),      timedelta(weeks=1)),
    ('day',    timedelta(days=1),       timedelta(days=1)),
    ('hour',   timedelta(hours=1),      timedelta(hours=1)),
    ('minute', timedelta(minutes=1),    timedelta(minutes=1)),
    ('second', timedelta(seconds=1),    timedelta(seconds=0)),
)
_ZERO_TIMEDELTA = timedelta(0)

def convert_timedelta(td):
    is_future = td < _ZERO_TIMEDELTA
    td = abs(td)

    for name, unit, minimum in _INTERVALS:
        if td >= minimum:
            difference = td / unit
            return '%0.1f %s%s %s' % (
                difference,
                name,
                's' if difference != 1.0 else '',
                'to go' if is_future else 'ago'
            )

def convert_datetime(dt, now=None):
    if now is None: now = datetime.utcnow()
    return convert_timedelta(now - dt)
