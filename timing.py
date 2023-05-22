from datetime import datetime
from dateutil import tz
from time import perf_counter


def iso_now():
    return datetime.now(tz=tz.tzlocal()).isoformat()


def accurate_time():
    return perf_counter()


def formatted_time_since_now(dt):
    if dt is None:
        return "---"
    td = datetime.now() - dt
    seconds = td.total_seconds()
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:03.0f}:{minutes:02.0f}:{seconds:02.0f}"

