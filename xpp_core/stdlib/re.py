"""
re - Regular Expression Operations Module for X++
"""

import re as _re
from . import XModule

def match(pattern, string, flags=0):
    m = _re.match(pattern, string, flags)
    return list(m.groups()) if m else None

def search(pattern, string, flags=0):
    m = _re.search(pattern, string, flags)
    return {"start": m.start(), "end": m.end(), "match": m.group(0), "groups": list(m.groups())} if m else None

def findall(pattern, string, flags=0):
    return _re.findall(pattern, string, flags)

def sub(pattern, repl, string, count=0, flags=0):
    return _re.sub(pattern, repl, string, count=count, flags=flags)

def split(pattern, string, maxsplit=0, flags=0):
    return _re.split(pattern, string, maxsplit=maxsplit, flags=flags)

def escape(pattern):
    return _re.escape(pattern)

EXPORT = XModule(
    "re",
    match=match, search=search, findall=findall, sub=sub, split=split, escape=escape
)
