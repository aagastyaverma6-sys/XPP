"""
json - JSON Encoder and Decoder Module for X++
"""

import json as _json
from . import XModule

def dumps(obj, indent=None): return _json.dumps(obj, indent=indent)
def loads(s): return _json.loads(s)
def dump(obj, filepath, indent=2):
    with open(filepath, "w", encoding="utf-8") as f:
        _json.dump(obj, f, indent=indent)
def load(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return _json.load(f)

EXPORT = XModule(
    "json",
    dumps=dumps, loads=loads, dump=dump, load=load
)
