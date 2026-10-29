"""
mathX - Complete Mathematical Operations Module for X++
Includes arithmetic, trigonometry, calculus helpers, combinatorics, statistics, and constants.
"""

import math
from . import XModule

# Constants
pi = math.pi
e = math.e
tau = math.tau
phi = 1.61803398874989484820
inf = float("inf")
nan = float("nan")

# Basic & Advanced Arithmetic
def abs_val(x):
    return abs(x)

def sqrt(x):
    return math.sqrt(x)

def cbrt(x):
    return math.cbrt(x) if hasattr(math, "cbrt") else (x ** (1.0 / 3.0) if x >= 0 else -((-x) ** (1.0 / 3.0)))

def pow_val(x, y):
    return math.pow(x, y)

def exp(x):
    return math.exp(x)

def exp2(x):
    return math.pow(2, x)

def expm1(x):
    return math.expm1(x)

def log(x, base=None):
    if base is None:
        return math.log(x)
    return math.log(x, base)

def log2(x):
    return math.log2(x)

def log10(x):
    return math.log10(x)

def log1p(x):
    return math.log1p(x)

def floor(x):
    return math.floor(x)

def ceil(x):
    return math.ceil(x)

def round_val(x, n=0):
    return round(x, n) if n != 0 else round(x)

def trunc(x):
    return math.trunc(x)

def sgn(x):
    if x > 0: return 1
    if x < 0: return -1
    return 0

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def lerp(a, b, t):
    return a + (b - a) * t

# Combinatorics & Number Theory
def factorial(n):
    return math.factorial(int(n))

def gcd(a, b):
    return math.gcd(int(a), int(b))

def lcm(a, b):
    a, b = int(a), int(b)
    return abs(a * b) // math.gcd(a, b) if a and b else 0

def comb(n, k):
    return math.comb(int(n), int(k))

def perm(n, k=None):
    return math.perm(int(n), int(k)) if k is not None else math.factorial(int(n))

def is_prime(n):
    n = int(n)
    if n < 2: return False
    if n in (2, 3): return True
    if n % 2 == 0 or n % 3 == 0: return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0: return False
        i += 6
    return True

def primes_up_to(limit):
    limit = int(limit)
    if limit < 2: return []
    sieve = [True] * (limit + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(limit**0.5) + 1):
        if sieve[i]:
            for j in range(i*i, limit + 1, i):
                sieve[j] = False
    return [i for i, is_p in enumerate(sieve) if is_p]

# Trigonometry
def sin(x): return math.sin(x)
def cos(x): return math.cos(x)
def tan(x): return math.tan(x)
def asin(x): return math.asin(x)
def acos(x): return math.acos(x)
def atan(x): return math.atan(x)
def atan2(y, x): return math.atan2(y, x)
def sinh(x): return math.sinh(x)
def cosh(x): return math.cosh(x)
def tanh(x): return math.tanh(x)
def asinh(x): return math.asinh(x)
def acosh(x): return math.acosh(x)
def atanh(x): return math.atanh(x)
def deg2rad(deg): return math.radians(deg)
def rad2deg(rad): return math.degrees(rad)
def hypot(x, y): return math.hypot(x, y)

# Statistics & Special
def mean(lst):
    return sum(lst) / len(lst) if lst else 0.0

def median(lst):
    if not lst: return 0.0
    s = sorted(lst)
    n = len(s)
    mid = n // 2
    if n % 2 == 1:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2.0

def variance(lst):
    if len(lst) < 2: return 0.0
    m = mean(lst)
    return sum((x - m) ** 2 for x in lst) / (len(lst) - 1)

def stdev(lst):
    return math.sqrt(variance(lst))

def erf(x): return math.erf(x)
def erfc(x): return math.erfc(x)
def gamma(x): return math.gamma(x)
def lgamma(x): return math.lgamma(x)

EXPORT = XModule(
    "mathX",
    pi=pi, e=e, tau=tau, phi=phi, inf=inf, nan=nan,
    abs=abs_val, sqrt=sqrt, cbrt=cbrt, pow=pow_val, exp=exp, exp2=exp2, expm1=expm1,
    log=log, log2=log2, log10=log10, log1p=log1p, floor=floor, ceil=ceil, round=round_val,
    trunc=trunc, sgn=sgn, clamp=clamp, lerp=lerp, factorial=factorial, gcd=gcd, lcm=lcm,
    comb=comb, perm=perm, is_prime=is_prime, primes_up_to=primes_up_to,
    sin=sin, cos=cos, tan=tan, asin=asin, acos=acos, atan=atan, atan2=atan2,
    sinh=sinh, cosh=cosh, tanh=tanh, asinh=asinh, acosh=acosh, atanh=atanh,
    deg2rad=deg2rad, rad2deg=rad2deg, hypot=hypot,
    mean=mean, median=median, variance=variance, stdev=stdev, std=stdev,
    erf=erf, erfc=erfc, gamma=gamma, lgamma=lgamma
)
