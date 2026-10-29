"""
datetime - Date and Time Types Module for X++
"""

import datetime as _dt
from . import XModule

class DateTime:
    def __init__(self, y, m, d, h=0, minute=0, s=0):
        self._d = _dt.datetime(y, m, d, h, minute, s)

    @property
    def year(self): return self._d.year
    @property
    def month(self): return self._d.month
    @property
    def day(self): return self._d.day
    @property
    def hour(self): return self._d.hour
    @property
    def minute(self): return self._d.minute
    @property
    def second(self): return self._d.second

    def isoformat(self):
        return self._d.isoformat()

    def strftime(self, fmt="%Y-%m-%d %H:%M:%S"):
        return self._d.strftime(fmt)

    def format(self, fmt="%Y-%m-%d %H:%M:%S"):
        return self._d.strftime(fmt)

    def timestamp(self):
        return self._d.timestamp()

    def __repr__(self):
        return f"DateTime({self.format()})"


def now():
    n = _dt.datetime.now()
    return DateTime(n.year, n.month, n.day, n.hour, n.minute, n.second)

def utcnow():
    n = _dt.datetime.utcnow()
    return DateTime(n.year, n.month, n.day, n.hour, n.minute, n.second)

def from_timestamp(ts):
    n = _dt.datetime.fromtimestamp(ts)
    return DateTime(n.year, n.month, n.day, n.hour, n.minute, n.second)

EXPORT = XModule(
    "datetime",
    now=now, utcnow=utcnow, from_timestamp=from_timestamp, DateTime=DateTime
)
