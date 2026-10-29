"""
time - Time Access and Conversions Module for X++
"""

import time as _time
from . import XModule

def time_val(): return _time.time()
def sleep(seconds): _time.sleep(seconds)
def perf_counter(): return _time.perf_counter()
def monotonic(): return _time.monotonic()
def ctime(secs=None): return _time.ctime(secs)
def strftime(format_str, t=None):
    return _time.strftime(format_str, _time.localtime(t) if t else _time.localtime())
def localtime(secs=None):
    t = _time.localtime(secs)
    return {
        "year": t.tm_year, "month": t.tm_mon, "day": t.tm_mday,
        "hour": t.tm_hour, "minute": t.tm_min, "second": t.tm_sec,
        "wday": t.tm_wday, "yday": t.tm_yday
    }

EXPORT = XModule(
    "time",
    time=time_val, sleep=sleep, perf_counter=perf_counter,
    monotonic=monotonic, ctime=ctime, strftime=strftime, localtime=localtime
)
