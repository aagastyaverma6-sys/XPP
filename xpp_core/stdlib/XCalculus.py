"""
XCalculus - Complete Calculus Suite for X++
Limits, derivatives, partial derivatives, Jacobian, Hessian,
single/double/triple integrals, gradient, divergence, curl, and Laplacian.
"""

import math
from . import XModule

# -------------------------------------------------------------------- Limits
def limit(fn, x0, direction="both", h=1e-7):
    """Calculates limit of fn(x) as x -> x0."""
    if direction == "left":
        return fn(x0 - h)
    elif direction == "right":
        return fn(x0 + h)
    else:
        left = fn(x0 - h)
        right = fn(x0 + h)
        if abs(left - right) < 1e-4:
            return 0.5 * (left + right)
        return float("nan")


# --------------------------------------------------------------- Derivatives
def derivative(fn, x, order=1, h=1e-5):
    """Computes nth order derivative using central finite differences."""
    if order == 1:
        return (fn(x + h) - fn(x - h)) / (2 * h)
    elif order == 2:
        return (fn(x + h) - 2 * fn(x) + fn(x - h)) / (h * h)
    elif order == 3:
        return (fn(x + 2*h) - 2*fn(x + h) + 2*fn(x - h) - fn(x - 2*h)) / (2 * h**3)
    else:
        # Recursive approximation
        return (derivative(fn, x + h, order - 1, h) - derivative(fn, x - h, order - 1, h)) / (2 * h)


def partial_derivative(fn, point, var_idx, h=1e-5):
    """Partial derivative with respect to point[var_idx]."""
    pt_fwd = list(point)
    pt_bwd = list(point)
    pt_fwd[var_idx] += h
    pt_bwd[var_idx] -= h
    return (fn(pt_fwd) - fn(pt_bwd)) / (2 * h)


def jacobian(fn_vec, point, h=1e-5):
    """Computes Jacobian matrix for a vector-valued function."""
    m = len(fn_vec)
    n = len(point)
    J = []
    for i in range(m):
        row = []
        for j in range(n):
            row.append(partial_derivative(fn_vec[i], point, j, h))
        J.append(row)
    return J


def hessian(scalar_fn, point, h=1e-4):
    """Computes Hessian matrix of second-order partial derivatives."""
    n = len(point)
    H = []
    for i in range(n):
        row = []
        for j in range(n):
            if i == j:
                pt_p = list(point); pt_p[i] += h
                pt_m = list(point); pt_m[i] -= h
                d2 = (scalar_fn(pt_p) - 2 * scalar_fn(point) + scalar_fn(pt_m)) / (h * h)
            else:
                pt_pp = list(point); pt_pp[i] += h; pt_pp[j] += h
                pt_pm = list(point); pt_pp[i] += h; pt_pm[j] -= h
                pt_mp = list(point); pt_mp[i] -= h; pt_mp[j] += h
                pt_mm = list(point); pt_mm[i] -= h; pt_mm[j] -= h
                d2 = (scalar_fn(pt_pp) - scalar_fn(pt_pm) - scalar_fn(pt_mp) + scalar_fn(pt_mm)) / (4 * h * h)
            row.append(d2)
        H.append(row)
    return H


# ----------------------------------------------------------------- Integrals
def integrate(fn, a, b, n=1000):
    """Definite integral using Simpson's rule."""
    if n % 2 == 1: n += 1
    h = (b - a) / n
    s = fn(a) + fn(b)
    for i in range(1, n):
        x = a + i * h
        s += 4 * fn(x) if i % 2 == 1 else 2 * fn(x)
    return s * h / 3.0


def double_integral(fn, x_bounds, y_bounds, nx=50, ny=50):
    """Double integral over 2D rectangular region."""
    x0, x1 = x_bounds
    y0, y1 = y_bounds
    hx = (x1 - x0) / nx
    hy = (y1 - y0) / ny
    total = 0.0
    for i in range(nx):
        x = x0 + (i + 0.5) * hx
        for j in range(ny):
            y = y0 + (j + 0.5) * hy
            total += fn(x, y)
    return total * hx * hy


def triple_integral(fn, x_bounds, y_bounds, z_bounds, nx=20, ny=20, nz=20):
    """Triple integral over 3D volume."""
    x0, x1 = x_bounds
    y0, y1 = y_bounds
    z0, z1 = z_bounds
    hx = (x1 - x0) / nx
    hy = (y1 - y0) / ny
    hz = (z1 - z0) / nz
    total = 0.0
    for i in range(nx):
        x = x0 + (i + 0.5) * hx
        for j in range(ny):
            y = y0 + (j + 0.5) * hy
            for k in range(nz):
                z = z0 + (k + 0.5) * hz
                total += fn(x, y, z)
    return total * hx * hy * hz


# ---------------------------------------------------------- Vector Calculus
def gradient(scalar_fn, point, h=1e-5):
    """Gradient vector ∇f(point)."""
    return [partial_derivative(scalar_fn, point, i, h) for i in range(len(point))]


def divergence(vector_fn, point, h=1e-5):
    """Divergence ∇ · F(point)."""
    n = len(point)
    div = 0.0
    for i in range(n):
        # Component i of F
        f_i = lambda pt: vector_fn(pt)[i]
        div += partial_derivative(f_i, point, i, h)
    return div


def curl(vector_3d_fn, point, h=1e-5):
    """Curl ∇ × F(point) in 3D."""
    F1 = lambda pt: vector_3d_fn(pt)[0]
    F2 = lambda pt: vector_3d_fn(pt)[1]
    F3 = lambda pt: vector_3d_fn(pt)[2]

    dF3_dy = partial_derivative(F3, point, 1, h)
    dF2_dz = partial_derivative(F2, point, 2, h)
    dF1_dz = partial_derivative(F1, point, 2, h)
    dF3_dx = partial_derivative(F3, point, 0, h)
    dF2_dx = partial_derivative(F2, point, 0, h)
    dF1_dy = partial_derivative(F1, point, 1, h)

    return [
        dF3_dy - dF2_dz,
        dF1_dz - dF3_dx,
        dF2_dx - dF1_dy
    ]


def laplacian(scalar_fn, point, h=1e-4):
    """Laplacian ∇²f(point) = ∇ · ∇f."""
    H = hessian(scalar_fn, point, h)
    return sum(H[i][i] for i in range(len(point)))


def directional_derivative(scalar_fn, point, direction, h=1e-5):
    """Directional derivative in direction vector."""
    grad = gradient(scalar_fn, point, h)
    d_norm = math.sqrt(sum(d * d for d in direction))
    if d_norm < 1e-12: return 0.0
    u = [d / d_norm for d in direction]
    return sum(g * ui for g, ui in zip(grad, u))


def integrate_trapezoid(fn, a, b, n=100):
    """Numerical definite integration via trapezoid rule."""
    h = (b - a) / n
    s = 0.5 * (fn(a) + fn(b))
    for i in range(1, n):
        s += fn(a + i * h)
    return s * h


def integrate_simpson(fn, a, b, n=100):
    """Numerical definite integration via Simpson's rule."""
    if n % 2 == 1: n += 1
    h = (b - a) / n
    s = fn(a) + fn(b)
    for i in range(1, n):
        x = a + i * h
        s += 4 * fn(x) if i % 2 == 1 else 2 * fn(x)
    return s * h / 3.0


EXPORT = XModule(
    "XCalculus",
    limit=limit,
    derivative=derivative, partial_derivative=partial_derivative,
    jacobian=jacobian, hessian=hessian,
    integrate=integrate, integrate_trapezoid=integrate_trapezoid, integrate_simpson=integrate_simpson,
    double_integral=double_integral, triple_integral=triple_integral,
    gradient=gradient, divergence=divergence, curl=curl, laplacian=laplacian,
    directional_derivative=directional_derivative
)
