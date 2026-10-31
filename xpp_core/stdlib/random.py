"""
random - Pseudo-random Number Generators for X++
"""

import random as _rnd
from . import XModule

def random_val(): return _rnd.random()
def randint(a, b): return _rnd.randint(int(a), int(b))
def choice(seq): return _rnd.choice(seq)
def choices(seq, k=1): return _rnd.choices(seq, k=k)
def shuffle(lst): _rnd.shuffle(lst); return lst
def sample(population, k): return _rnd.sample(population, k)
def uniform(a, b): return _rnd.uniform(a, b)
def gauss(mu, sigma): return _rnd.gauss(mu, sigma)
def seed(val): _rnd.seed(val)

EXPORT = XModule(
    "random",
    random=random_val, randint=randint, choice=choice, choices=choices,
    shuffle=shuffle, sample=sample, uniform=uniform, gauss=gauss, seed=seed
)
