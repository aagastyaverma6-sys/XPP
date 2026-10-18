"""
functools - Higher-order Functions and Operations on Callable Objects for X++
"""

import functools as _ft
from . import XModule

def reduce(function, iterable, initializer=None):
    if initializer is None:
        return _ft.reduce(function, iterable)
    return _ft.reduce(function, iterable, initializer)

def partial(func, *args, **keywords):
    return _ft.partial(func, *args, **keywords)

def memoize(func):
    cache = {}
    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]
    return wrapper

def compose(*functions):
    def _c(x):
        for f in reversed(functions):
            x = f(x)
        return x
    return _c

EXPORT = XModule(
    "functools",
    reduce=reduce, partial=partial, memoize=memoize, compose=compose
)
