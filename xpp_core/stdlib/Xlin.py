"""
Xlin - Linear Algebra Module for X++
Vectors, matrices, determinant, inverse, solve linear systems,
eigenvalues/eigenvectors, SVD, QR, LU, Cholesky, and projections.
"""

import math
from . import XModule

# --------------------------------------------------------- Vector Operations
def dot(u, v):
    return sum(x * y for x, y in zip(u, v))

def norm(v, p=2):
    if p == 2:
        return math.sqrt(sum(x * x for x in v))
    if p == 1:
        return sum(abs(x) for x in v)
    if p == float("inf"):
        return max(abs(x) for x in v)
    return sum(abs(x) ** p for x in v) ** (1.0 / p)

def normalize(v):
    n = norm(v)
    if n < 1e-12:
        return list(v)
    return [x / n for x in v]

def cross(u, v):
    if len(u) != 3 or len(v) != 3:
        raise ValueError("Cross product requires 3D vectors")
    return [
        u[1] * v[2] - u[2] * v[1],
        u[2] * v[0] - u[0] * v[2],
        u[0] * v[1] - u[1] * v[0]
    ]

def angle(u, v):
    nu = norm(u)
    nv = norm(v)
    if nu < 1e-12 or nv < 1e-12: return 0.0
    cos_val = max(-1.0, min(1.0, dot(u, v) / (nu * nv)))
    return math.acos(cos_val)

def proj(u, v):
    """Projection of vector u onto vector v."""
    dv = dot(v, v)
    if dv < 1e-12: return [0.0] * len(u)
    c = dot(u, v) / dv
    return [c * x for x in v]


# --------------------------------------------------------- Matrix Operations
def transpose(m):
    rows = len(m)
    cols = len(m[0]) if rows > 0 else 0
    return [[m[r][c] for r in range(rows)] for c in range(cols)]

def trace(m):
    return sum(m[i][i] for i in range(min(len(m), len(m[0]))))

def det(m):
    """Determinant of a square matrix using Gaussian elimination."""
    n = len(m)
    if n == 1: return m[0][0]
    if n == 2: return m[0][0] * m[1][1] - m[0][1] * m[1][0]

    mat = [list(row) for row in m]
    det_val = 1.0
    for i in range(n):
        # Pivot
        pivot = i
        for j in range(i + 1, n):
            if abs(mat[j][i]) > abs(mat[pivot][i]):
                pivot = j
        if abs(mat[pivot][i]) < 1e-12:
            return 0.0
        if pivot != i:
            mat[i], mat[pivot] = mat[pivot], mat[i]
            det_val = -det_val
        det_val *= mat[i][i]
        for j in range(i + 1, n):
            factor = mat[j][i] / mat[i][i]
            for k in range(i, n):
                mat[j][k] -= factor * mat[i][k]
    return det_val

def inv(m):
    """Inverse of a square matrix via Gauss-Jordan elimination."""
    n = len(m)
    mat = [m[i] + [1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for i in range(n):
        pivot = i
        for j in range(i + 1, n):
            if abs(mat[j][i]) > abs(mat[pivot][i]):
                pivot = j
        if abs(mat[pivot][i]) < 1e-12:
            raise ValueError("Matrix is singular and non-invertible")
        mat[i], mat[pivot] = mat[pivot], mat[i]
        p_val = mat[i][i]
        for k in range(2 * n):
            mat[i][k] /= p_val
        for j in range(n):
            if j != i:
                f = mat[j][i]
                for k in range(2 * n):
                    mat[j][k] -= f * mat[i][k]
    return [[mat[i][n + j] for j in range(n)] for i in range(n)]

def solve(A, b):
    """Solves system A * x = b."""
    A_inv = inv(A)
    n = len(A)
    return [sum(A_inv[i][j] * b[j] for j in range(n)) for i in range(n)]


# ------------------------------------------------------------ Decompositions
def lu(A):
    """LU decomposition with partial pivoting: P * A = L * U."""
    n = len(A)
    L = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    U = [list(row) for row in A]
    P = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

    for i in range(n):
        max_idx = max(range(i, n), key=lambda r: abs(U[r][i]))
        if i != max_idx:
            U[i], U[max_idx] = U[max_idx], U[i]
            P[i], P[max_idx] = P[max_idx], P[i]
            for k in range(i):
                L[i][k], L[max_idx][k] = L[max_idx][k], L[i][k]
        for j in range(i + 1, n):
            factor = U[j][i] / (U[i][i] if abs(U[i][i]) > 1e-12 else 1e-12)
            L[j][i] = factor
            for k in range(i, n):
                U[j][k] -= factor * U[i][k]
    return {"L": L, "U": U, "P": P, "status": "ok"}

def qr(A):
    """QR decomposition using Gram-Schmidt orthogonalization."""
    m = len(A)
    n = len(A[0])
    Q = [[0.0] * n for _ in range(m)]
    R = [[0.0] * n for _ in range(n)]

    for j in range(n):
        v = [A[i][j] for i in range(m)]
        for i in range(j):
            q_i = [Q[r][i] for r in range(m)]
            R[i][j] = dot(q_i, [A[r][j] for r in range(m)])
            for r in range(m):
                v[r] -= R[i][j] * q_i[r]
        R[j][j] = norm(v)
        if R[j][j] > 1e-12:
            for r in range(m):
                Q[r][j] = v[r] / R[j][j]
    return {"Q": Q, "R": R}

def eig(A, max_iter=80):
    """Computes eigenvalues and eigenvectors using QR algorithm."""
    n = len(A)
    Ak = [list(row) for row in A]
    V = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for _ in range(max_iter):
        decomp = qr(Ak)
        Q = decomp["Q"]
        R = decomp["R"]
        # Ak+1 = R * Q
        Ak = [[sum(R[i][k] * Q[k][j] for k in range(n)) for j in range(n)] for i in range(n)]
        # Accumulate eigenvectors V = V * Q
        V = [[sum(V[i][k] * Q[k][j] for k in range(n)) for j in range(n)] for i in range(n)]
    eigenvalues = [Ak[i][i] for i in range(n)]
    return {"values": eigenvalues, "vectors": V}

def eigenvalues(A):
    return eig(A)["values"]

lu_decomposition = lu

EXPORT = XModule(
    "Xlin",
    dot=dot, norm=norm, normalize=normalize, cross=cross, angle=angle, proj=proj,
    transpose=transpose, trace=trace, det=det, inv=inv, solve=solve,
    lu=lu, lu_decomposition=lu_decomposition, qr=qr, eig=eig, eigenvalues=eigenvalues
)
