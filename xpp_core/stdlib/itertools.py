"""
itertools - Functions Creating Iterators for Efficient Looping for X++
"""

import itertools as _it
from . import XModule

def chain(*iterables): return list(_it.chain(*iterables))
def combinations(iterable, r): return [list(c) for c in _it.combinations(iterable, int(r))]
def permutations(iterable, r=None): return [list(p) for p in _it.permutations(iterable, int(r) if r else None)]
def product(*iterables, repeat=1): return [list(p) for p in _it.product(*iterables, repeat=repeat)]
def repeat(elem, n=None): return list(_it.repeat(elem, int(n))) if n else _it.repeat(elem)
def islice(iterable, *args): return list(_it.islice(iterable, *args))
def accumulate(iterable, fn=None): return list(_it.accumulate(iterable, fn))

EXPORT = XModule(
    "itertools",
    chain=chain, combinations=combinations, permutations=permutations,
    product=product, repeat=repeat, islice=islice, accumulate=accumulate
)
