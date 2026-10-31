"""
Xsci - Scientific Computing Suite for X++ (Scipy counterpart)
Provides optimization, numerical quadrature/integration, signal processing,
interpolation, special functions, and probability distributions.
"""

import math
from . import XModule

# ------------------------------------------------------------- Optimization
def minimize(fn, x0, tol=1e-5, max_iter=200, step=0.01):
    """Simple gradient-descent / Nelder-Mead hybrid numerical minimizer."""
    if isinstance(x0, (int, float)):
        x = float(x0)
        h = 1e-5
        for _ in range(max_iter):
            grad = (fn(x + h) - fn(x - h)) / (2 * h)
            if abs(grad) < tol:
                break
            x -= step * grad
        return {"x": x, "fun": fn(x), "success": True}
    else:
        # Multidimensional gradient descent
        x = [float(val) for val in x0]
        h = 1e-5
        n = len(x)
        for _ in range(max_iter):
            grad = []
            fx = fn(x)
            grad_norm = 0.0
            for i in range(n):
                xh = list(x)
                xh[i] += h
                g_i = (fn(xh) - fx) / h
                grad.append(g_i)
                grad_norm += g_i ** 2
            grad_norm = math.sqrt(grad_norm)
            if grad_norm < tol:
                break
            for i in range(n):
                x[i] -= step * grad[i]
        return {"x": x, "fun": fn(x), "success": True}


def root(fn, x0, tol=1e-6, max_iter=100):
    """Finds root of f(x) = 0 using Newton-Raphson with secant fallback."""
    x = float(x0)
    h = 1e-5
    for _ in range(max_iter):
        fx = fn(x)
        if abs(fx) < tol:
            return {"x": x, "fun": fx, "success": True}
        dfx = (fn(x + h) - fn(x - h)) / (2 * h)
        if abs(dfx) < 1e-12:
            dfx = 1e-12
        x -= fx / dfx
    return {"x": x, "fun": fn(x), "success": abs(fn(x)) < tol}


def curve_fit(fn, xdata, ydata, p0):
    """Non-linear least squares fit using Gauss-Newton / gradient descent."""
    p = [float(val) for val in p0]
    m = len(xdata)
    n = len(p)
    h = 1e-5
    alpha = 0.01
    for _ in range(250):
        residuals = [fn(xdata[i], *p) - ydata[i] for i in range(m)]
        # Compute gradient of sum of squared residuals
        grad = [0.0] * n
        for j in range(n):
            pj = list(p)
            pj[j] += h
            for i in range(m):
                d_ij = (fn(xdata[i], *pj) - fn(xdata[i], *p)) / h
                grad[j] += 2 * residuals[i] * d_ij
        for j in range(n):
            p[j] -= alpha * grad[j] / m
    return p


# -------------------------------------------------- Quadrature & Integration
class QuadResult(float):
    def __new__(cls, val, err=1e-8):
        obj = super().__new__(cls, val)
        obj.value = float(val)
        obj.error = float(err)
        return obj
    def __getitem__(self, item):
        if item == "value": return self.value
        if item == "error": return self.error
        raise KeyError(item)


def quad(fn, a, b, n=1000):
    """Composite Simpson's 1/3 rule for numerical integration."""
    if n % 2 == 1:
        n += 1
    h = (b - a) / n
    s = fn(a) + fn(b)
    for i in range(1, n):
        x = a + i * h
        s += 4 * fn(x) if i % 2 == 1 else 2 * fn(x)
    return QuadResult(s * h / 3.0, 1e-8)


def trapz(y, x=None):
    """Trapezoidal integration over samples y."""
    n = len(y)
    if n < 2: return 0.0
    if x is None:
        return sum(0.5 * (y[i] + y[i + 1]) for i in range(n - 1))
    return sum(0.5 * (y[i] + y[i + 1]) * (x[i + 1] - x[i]) for i in range(n - 1))


def simpson(y, x=None):
    """Simpson's rule over samples y."""
    n = len(y)
    if n < 3: return trapz(y, x)
    if n % 2 == 0:
        return trapz(y[:2], x[:2] if x else None) + simpson(y[1:], x[1:] if x else None)
    if x is None:
        h = 1.0
        s = y[0] + y[-1] + 4 * sum(y[i] for i in range(1, n - 1, 2)) + 2 * sum(y[i] for i in range(2, n - 2, 2))
        return s * h / 3.0
    s = 0.0
    for i in range(0, n - 2, 2):
        h = (x[i + 2] - x[i]) / 2.0
        s += (h / 3.0) * (y[i] + 4 * y[i + 1] + y[i + 2])
    return s


# ------------------------------------------------------------- Interpolation
def interp1d(x, y, kind="linear"):
    """Returns a callable linear/step interpolator."""
    pts = sorted(zip(x, y), key=lambda p: p[0])
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]

    def _interp(x_val):
        if x_val <= xs[0]: return ys[0]
        if x_val >= xs[-1]: return ys[-1]
        for i in range(len(xs) - 1):
            if xs[i] <= x_val <= xs[i + 1]:
                if kind == "nearest":
                    return ys[i] if abs(x_val - xs[i]) < abs(x_val - xs[i+1]) else ys[i+1]
                # Linear
                t = (x_val - xs[i]) / (xs[i + 1] - xs[i])
                return ys[i] + t * (ys[i + 1] - ys[i])
        return ys[-1]

    return _interp


# --------------------------------------------------------- Signal Processing
def fft(x):
    """Cooley-Tukey 1D Fast Fourier Transform."""
    n = len(x)
    if n <= 1:
        return [complex(val) for val in x]
    # Pad to power of 2 if needed
    p = 1
    while p < n: p <<= 1
    if p != n:
        x = list(x) + [0] * (p - n)
        n = p
    even = fft(x[0::2])
    odd = fft(x[1::2])
    t = [math.e ** (-2j * math.pi * k / n) * odd[k] for k in range(n // 2)]
    return [even[k] + t[k] for k in range(n // 2)] + [even[k] - t[k] for k in range(n // 2)]


def ifft(x):
    """Inverse Fast Fourier Transform."""
    n = len(x)
    conj_x = [complex(val).conjugate() for val in x]
    f = fft(conj_x)
    return [complex(val.conjugate().real / n, val.conjugate().imag / n) for val in f]


def convolve(a, b):
    """1D discrete convolution of two sequences."""
    na, nb = len(a), len(b)
    res = [0.0] * (na + nb - 1)
    for i in range(na):
        for j in range(nb):
            res[i + j] += a[i] * b[j]
    return res


def correlate(a, b):
    return convolve(a, list(reversed(b)))


def filter_lowpass(data, cutoff, fs, order=4):
    """Simple moving-average / recursive IIR lowpass filter approximation."""
    dt = 1.0 / fs
    rc = 1.0 / (2 * math.pi * cutoff)
    alpha = dt / (rc + dt)
    out = [data[0]]
    for i in range(1, len(data)):
        out.append(out[-1] + alpha * (data[i] - out[-1]))
    return out


# --------------------------------------------------------- Special Functions
def bessel_j0(x):
    """Zero-order Bessel function of the first kind."""
    s = 1.0
    term = 1.0
    for m in range(1, 25):
        term *= -(x * x / 4.0) / (m * m)
        s += term
        if abs(term) < 1e-15: break
    return s


def bessel_j1(x):
    """First-order Bessel function of the first kind."""
    s = x / 2.0
    term = x / 2.0
    for m in range(1, 25):
        term *= -(x * x / 4.0) / (m * (m + 1))
        s += term
        if abs(term) < 1e-15: break
    return s


def beta_fn(a, b):
    """Beta function B(a, b)."""
    return (math.gamma(a) * math.gamma(b)) / math.gamma(a + b)


def gamma_fn(x):
    return math.gamma(x)


def legendre_p(n, x):
    """Legendre polynomial P_n(x)."""
    if n == 0: return 1.0
    if n == 1: return x
    p0, p1 = 1.0, x
    for k in range(2, n + 1):
        pk = ((2 * k - 1) * x * p1 - (k - 1) * p0) / k
        p0, p1 = p1, pk
    return p1


# -------------------------------------------------- Probability & Statistics
def norm_pdf(x, mu=0.0, sigma=1.0):
    return (1.0 / (sigma * math.sqrt(2 * math.pi))) * math.exp(-0.5 * ((x - mu) / sigma) ** 2)


def norm_cdf(x, mu=0.0, sigma=1.0):
    return 0.5 * (1.0 + math.erf((x - mu) / (sigma * math.sqrt(2))))


def norm_ppf(p, mu=0.0, sigma=1.0):
    """Inverse CDF (probit) approximation."""
    if p <= 0: return -math.inf
    if p >= 1: return math.inf
    # Rational approximation
    q = p - 0.5
    if abs(q) <= 0.42:
        r = q * q
        val = q * (((-25.44106049637 * r + 41.39119773534) * r - 18.61500062529) * r + 2.50662823884) / \
              ((((3.13082909833 * r - 21.06224101826) * r + 23.08336743743) * r + 1.0) * r - 1.0)
    else:
        r = p if q < 0 else 1.0 - p
        r = math.sqrt(-math.log(r))
        val = (((2.32121276858 * r + 4.85014127135) * r - 2.29796479134) * r - 2.78718931138) / \
              ((1.63706728976 * r + 3.54388924762) * r + 1.0)
        if q < 0: val = -val
    return mu + sigma * val


def poisson_pmf(k, lam):
    if k < 0: return 0.0
    return (math.exp(-lam) * (lam ** k)) / math.factorial(int(k))


def euclidean_distance(p1, p2):
    return math.sqrt(sum((float(a) - float(b)) ** 2 for a, b in zip(p1, p2)))


def cosine_similarity(v1, v2):
    dot = sum(float(a) * float(b) for a, b in zip(v1, v2))
    n1 = math.sqrt(sum(float(a) ** 2 for a in v1))
    n2 = math.sqrt(sum(float(b) ** 2 for b in v2))
    return dot / (n1 * n2) if n1 > 0 and n2 > 0 else 0.0


EXPORT = XModule(
    "Xsci",
    minimize=minimize, root=root, curve_fit=curve_fit,
    quad=quad, trapz=trapz, simpson=simpson,
    interp1d=interp1d,
    fft=fft, ifft=ifft, convolve=convolve, correlate=correlate, filter_lowpass=filter_lowpass,
    bessel_j0=bessel_j0, bessel_j1=bessel_j1, beta_fn=beta_fn, gamma_fn=gamma_fn, legendre_p=legendre_p,
    norm_pdf=norm_pdf, norm_cdf=norm_cdf, norm_ppf=norm_ppf, poisson_pmf=poisson_pmf,
    euclidean_distance=euclidean_distance, cosine_similarity=cosine_similarity
)
