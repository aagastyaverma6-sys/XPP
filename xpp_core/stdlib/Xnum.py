"""
Xnum - Numerical Array & Matrix Computing for X++ (Numpy counterpart)
Supports multidimensional arrays, shapes, reshaping, mathematical ops,
broadcasting, linear algebra dot products, and reductions.
"""

import math
import random as _py_random
from . import XModule

class NDArray:
    """Multidimensional Array implementation in pure X++ Python runtime."""
    def __init__(self, data, shape=None):
        if isinstance(data, NDArray):
            self.data = list(data.data)
            self.shape = list(data.shape)
        elif isinstance(data, list):
            flat, s = self._flatten(data)
            self.data = flat
            self.shape = shape or s
        else:
            self.data = [data]
            self.shape = shape or [1]

    def _flatten(self, lst):
        if not isinstance(lst, list):
            return [lst], []
        if not lst:
            return [], [0]
        if not isinstance(lst[0], list):
            return list(lst), [len(lst)]
        flat = []
        sub_shapes = []
        for item in lst:
            f, s = self._flatten(item)
            flat.extend(f)
            sub_shapes.append(s)
        return flat, [len(lst)] + sub_shapes[0]

    @property
    def size(self):
        p = 1
        for dim in self.shape: p *= dim
        return p

    @property
    def ndim(self):
        return len(self.shape)

    def to_list(self):
        def _unflatten(data, shape):
            if not shape:
                return data[0] if data else 0
            if len(shape) == 1:
                return data[:shape[0]]
            step = 1
            for d in shape[1:]: step *= d
            res = []
            for i in range(shape[0]):
                chunk = data[i * step : (i + 1) * step]
                res.append(_unflatten(chunk, shape[1:]))
            return res
        return _unflatten(self.data, self.shape)

    def reshape(self, new_shape):
        p = 1
        for d in new_shape: p *= d
        if p != self.size:
            raise ValueError(f"Cannot reshape array of size {self.size} into shape {new_shape}")
        return NDArray(list(self.data), list(new_shape))

    def transpose(self):
        if len(self.shape) != 2:
            return NDArray(list(self.data), list(reversed(self.shape)))
        rows, cols = self.shape
        trans_data = [0] * (rows * cols)
        for r in range(rows):
            for c in range(cols):
                trans_data[c * rows + r] = self.data[r * cols + c]
        return NDArray(trans_data, [cols, rows])

    def flatten(self):
        return NDArray(list(self.data), [self.size])

    def __getitem__(self, item):
        lst = self.to_list()
        return lst[item]

    def __repr__(self):
        return f"array({self.to_list()})"


# Array Creation
def array(data):
    return NDArray(data)

def zeros(shape):
    if isinstance(shape, int): shape = [shape]
    size = 1
    for s in shape: size *= s
    return NDArray([0] * size, shape)

def ones(shape):
    if isinstance(shape, int): shape = [shape]
    size = 1
    for s in shape: size *= s
    return NDArray([1] * size, shape)

def full(shape, fill_value):
    if isinstance(shape, int): shape = [shape]
    size = 1
    for s in shape: size *= s
    return NDArray([fill_value] * size, shape)

def eye(n):
    res = zeros([n, n])
    for i in range(n):
        res.data[i * n + i] = 1
    return res

def identity(n):
    return eye(n)

def arange(start, stop=None, step=1):
    if stop is None:
        start, stop = 0, start
    data = []
    curr = start
    if step > 0:
        while curr < stop:
            data.append(curr)
            curr += step
    elif step < 0:
        while curr > stop:
            data.append(curr)
            curr += step
    return NDArray(data, [len(data)])

def linspace(start, stop, num=50):
    if num <= 1:
        return NDArray([start], [1])
    step = (stop - start) / (num - 1)
    data = [start + i * step for i in range(num)]
    return NDArray(data, [num])

def random(shape):
    if isinstance(shape, int): shape = [shape]
    size = 1
    for s in shape: size *= s
    data = [_py_random.random() for _ in range(size)]
    return NDArray(data, shape)


# Operations
def reshape(arr, shape):
    if isinstance(arr, NDArray):
        return arr.reshape(shape)
    return NDArray(arr).reshape(shape)

def transpose(arr):
    if isinstance(arr, NDArray):
        return arr.transpose()
    return NDArray(arr).transpose()

def flatten(arr):
    if isinstance(arr, NDArray):
        return arr.flatten()
    return NDArray(arr).flatten()

def dot(a, b):
    a = a if isinstance(a, NDArray) else NDArray(a)
    b = b if isinstance(b, NDArray) else NDArray(b)
    if len(a.shape) == 1 and len(b.shape) == 1:
        if a.shape[0] != b.shape[0]:
            raise ValueError("Shapes not aligned for 1D dot product")
        return sum(x * y for x, y in zip(a.data, b.data))
    if len(a.shape) == 2 and len(b.shape) == 2:
        r1, c1 = a.shape
        r2, c2 = b.shape
        if c1 != r2:
            raise ValueError(f"Cannot multiply matrix ({r1}x{c1}) and ({r2}x{c2})")
        res_data = [0] * (r1 * c2)
        for i in range(r1):
            for k in range(c1):
                aik = a.data[i * c1 + k]
                for j in range(c2):
                    res_data[i * c2 + j] += aik * b.data[k * c2 + j]
        return NDArray(res_data, [r1, c2])
    return [x * y for x, y in zip(a.data, b.data)]

def matmul(a, b):
    return dot(a, b)

def sum_vals(arr, axis=None):
    arr = arr if isinstance(arr, NDArray) else NDArray(arr)
    if axis is None:
        return sum(arr.data)
    # 2D axis reduction
    if len(arr.shape) == 2:
        r, c = arr.shape
        if axis == 0:
            return [sum(arr.data[i * c + j] for i in range(r)) for j in range(c)]
        elif axis == 1:
            return [sum(arr.data[i * c + j] for j in range(c)) for i in range(r)]
    return sum(arr.data)

def mean_vals(arr, axis=None):
    arr = arr if isinstance(arr, NDArray) else NDArray(arr)
    s = sum_vals(arr, axis)
    if axis is None:
        return s / arr.size
    count = arr.shape[axis]
    if isinstance(s, list):
        return [v / count for v in s]
    return s / count

def std_vals(arr, axis=None):
    arr = arr if isinstance(arr, NDArray) else NDArray(arr)
    m = mean_vals(arr, axis)
    if axis is None:
        return math.sqrt(sum((x - m) ** 2 for x in arr.data) / arr.size)
    return [0.0]

def min_val(arr):
    arr = arr if isinstance(arr, NDArray) else NDArray(arr)
    return min(arr.data)

def max_val(arr):
    arr = arr if isinstance(arr, NDArray) else NDArray(arr)
    return max(arr.data)

def norm(v):
    arr = v.data if isinstance(v, NDArray) else v
    return math.sqrt(sum(float(x) ** 2 for x in arr))

def cross(u, v):
    u = u.data if isinstance(u, NDArray) else u
    v = v.data if isinstance(v, NDArray) else v
    return [
        u[1] * v[2] - u[2] * v[1],
        u[2] * v[0] - u[0] * v[2],
        u[0] * v[1] - u[1] * v[0]
    ]

def clip(arr, a_min, a_max):
    arr = arr if isinstance(arr, NDArray) else NDArray(arr)
    return NDArray([max(a_min, min(a_max, x)) for x in arr.data], list(arr.shape))

EXPORT = XModule(
    "Xnum",
    NDArray=NDArray,
    array=array, zeros=zeros, ones=ones, full=full, eye=eye, identity=identity,
    arange=arange, linspace=linspace, random=random,
    reshape=reshape, transpose=transpose, flatten=flatten,
    dot=dot, matmul=matmul, norm=norm, cross=cross,
    sum=sum_vals, mean=mean_vals, std=std_vals, min=min_val, max=max_val, clip=clip
)
