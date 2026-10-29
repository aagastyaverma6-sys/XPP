"""
collections - Container Datatypes Module for X++
"""

import collections as _col
from . import XModule

def Counter(iterable=None):
    return _col.Counter(iterable or [])

def deque(iterable=None, maxlen=None):
    return _col.deque(iterable or [], maxlen=maxlen)

def OrderedDict(d=None):
    return _col.OrderedDict(d or {})

def defaultdict(default_factory):
    return _col.defaultdict(default_factory)

EXPORT = XModule(
    "collections",
    Counter=Counter, deque=deque, OrderedDict=OrderedDict, defaultdict=defaultdict
)
