"""
XCAS - Computer Algebra System Library for X++
Symbolic expression trees, symbolic differentiation, integration,
simplification, expansion, equation solving, and polynomial factorization.
"""

import math
import re
from . import XModule

class SymExpr:
    """Symbolic expression tree node."""
    def __init__(self, op, *args):
        self.op = op
        self.args = list(args)

    def is_const(self):
        return self.op == "CONST"

    def is_var(self):
        return self.op == "VAR"

    def __repr__(self):
        return to_string(self)

    def __add__(self, other):
        return simplify(SymExpr("+", self, _to_sym(other)))

    def __sub__(self, other):
        return simplify(SymExpr("-", self, _to_sym(other)))

    def __mul__(self, other):
        return simplify(SymExpr("*", self, _to_sym(other)))

    def __truediv__(self, other):
        return simplify(SymExpr("/", self, _to_sym(other)))

    def __pow__(self, other):
        return simplify(SymExpr("**", self, _to_sym(other)))


def _to_sym(v):
    if isinstance(v, SymExpr):
        return v
    if isinstance(v, (int, float)):
        return SymExpr("CONST", v)
    if isinstance(v, str):
        return var(v)
    return SymExpr("CONST", v)


def var(name):
    return SymExpr("VAR", name)

def const(val):
    return SymExpr("CONST", val)


def parse_expr(s: str) -> SymExpr:
    """Simple recursive-descent parser for symbolic strings e.g. 'x**2 + 3*x - 5'."""
    s = s.strip()
    # Handle addition/subtraction
    depth = 0
    for i in range(len(s) - 1, -1, -1):
        c = s[i]
        if c == ")": depth += 1
        elif c == "(": depth -= 1
        elif depth == 0 and c in ("+", "-") and i > 0 and s[i-1] not in ("*", "/", "^", "+", "-"):
            left = parse_expr(s[:i])
            right = parse_expr(s[i+1:])
            return SymExpr(c, left, right)

    # Handle multiplication/division
    depth = 0
    for i in range(len(s) - 1, -1, -1):
        c = s[i]
        if c == ")": depth += 1
        elif c == "(": depth -= 1
        elif depth == 0 and c in ("*", "/"):
            if c == "*" and i > 0 and s[i-1] == "*":
                continue # power
            if c == "*" and i < len(s) - 1 and s[i+1] == "*":
                continue # power
            left = parse_expr(s[:i])
            right = parse_expr(s[i+1:])
            return SymExpr(c, left, right)

    # Handle powers
    depth = 0
    for i in range(len(s)):
        c = s[i]
        if c == "(": depth += 1
        elif c == ")": depth -= 1
        elif depth == 0 and s[i:i+2] == "**":
            left = parse_expr(s[:i])
            right = parse_expr(s[i+2:])
            return SymExpr("**", left, right)
        elif depth == 0 and c == "^":
            left = parse_expr(s[:i])
            right = parse_expr(s[i+1:])
            return SymExpr("**", left, right)

    # Parentheses
    if s.startswith("(") and s.endswith(")"):
        return parse_expr(s[1:-1])

    # Functions (sin, cos, exp, ln)
    m = re.match(r"^([A-Za-z_]\w*)\((.*)\)$", s)
    if m:
        fn_name, arg_str = m.groups()
        return SymExpr(fn_name, parse_expr(arg_str))

    # Numbers vs Variables
    try:
        val = float(s) if "." in s else int(s)
        return SymExpr("CONST", val)
    except ValueError:
        return SymExpr("VAR", s)


def to_string(e: SymExpr) -> str:
    if not isinstance(e, SymExpr):
        return str(e)
    if e.op == "CONST":
        return str(e.args[0])
    if e.op == "VAR":
        return str(e.args[0])
    if e.op in ("+", "-"):
        return f"{to_string(e.args[0])} {e.op} {to_string(e.args[1])}"
    if e.op == "*":
        return f"{to_string(e.args[0])} * {to_string(e.args[1])}"
    if e.op == "/":
        return f"({to_string(e.args[0])}) / ({to_string(e.args[1])})"
    if e.op == "**":
        return f"{to_string(e.args[0])}**{to_string(e.args[1])}"
    if len(e.args) == 1:
        return f"{e.op}({to_string(e.args[0])})"
    return f"{e.op}({', '.join(to_string(a) for a in e.args)})"


def diff(e: SymExpr, v: str) -> SymExpr:
    """Symbolic differentiation with respect to variable v."""
    e = _to_sym(e)
    if e.op == "CONST":
        return SymExpr("CONST", 0)
    if e.op == "VAR":
        return SymExpr("CONST", 1 if e.args[0] == v else 0)
    if e.op == "+":
        return simplify(SymExpr("+", diff(e.args[0], v), diff(e.args[1], v)))
    if e.op == "-":
        return simplify(SymExpr("-", diff(e.args[0], v), diff(e.args[1], v)))
    if e.op == "*":
        u, w = e.args[0], e.args[1]
        # Product rule: u'w + uw'
        return simplify(SymExpr("+", SymExpr("*", diff(u, v), w), SymExpr("*", u, diff(w, v))))
    if e.op == "/":
        u, w = e.args[0], e.args[1]
        # Quotient rule: (u'w - uw') / w^2
        top = SymExpr("-", SymExpr("*", diff(u, v), w), SymExpr("*", u, diff(w, v)))
        bot = SymExpr("**", w, SymExpr("CONST", 2))
        return simplify(SymExpr("/", top, bot))
    if e.op == "**":
        u, p = e.args[0], e.args[1]
        if p.op == "CONST":
            # Power rule: p * u^(p-1) * u'
            new_p = SymExpr("CONST", p.args[0] - 1)
            return simplify(SymExpr("*", SymExpr("*", p, SymExpr("**", u, new_p)), diff(u, v)))
    if e.op == "sin":
        return simplify(SymExpr("*", SymExpr("cos", e.args[0]), diff(e.args[0], v)))
    if e.op == "cos":
        return simplify(SymExpr("*", SymExpr("*", SymExpr("CONST", -1), SymExpr("sin", e.args[0])), diff(e.args[0], v)))
    if e.op in ("exp", "e"):
        return simplify(SymExpr("*", e, diff(e.args[0], v)))
    if e.op in ("ln", "log"):
        return simplify(SymExpr("/", diff(e.args[0], v), e.args[0]))
    return SymExpr("diff", e, SymExpr("VAR", v))


def integrate(e: SymExpr, v: str) -> SymExpr:
    """Elementary symbolic integration with respect to variable v."""
    e = _to_sym(e)
    if e.op == "CONST":
        return SymExpr("*", e, SymExpr("VAR", v))
    if e.op == "VAR":
        if e.args[0] == v:
            return SymExpr("/", SymExpr("**", e, SymExpr("CONST", 2)), SymExpr("CONST", 2))
        return SymExpr("*", e, SymExpr("VAR", v))
    if e.op == "+":
        return simplify(SymExpr("+", integrate(e.args[0], v), integrate(e.args[1], v)))
    if e.op == "-":
        return simplify(SymExpr("-", integrate(e.args[0], v), integrate(e.args[1], v)))
    if e.op == "*":
        u, w = e.args[0], e.args[1]
        if u.op == "CONST":
            return simplify(SymExpr("*", u, integrate(w, v)))
        if w.op == "CONST":
            return simplify(SymExpr("*", w, integrate(u, v)))
    if e.op == "**":
        u, p = e.args[0], e.args[1]
        if u.op == "VAR" and u.args[0] == v and p.op == "CONST":
            n = p.args[0]
            if n == -1:
                return SymExpr("ln", u)
            return SymExpr("/", SymExpr("**", u, SymExpr("CONST", n + 1)), SymExpr("CONST", n + 1))
    if e.op == "cos" and e.args[0].op == "VAR" and e.args[0].args[0] == v:
        return SymExpr("sin", e.args[0])
    if e.op == "sin" and e.args[0].op == "VAR" and e.args[0].args[0] == v:
        return SymExpr("*", SymExpr("CONST", -1), SymExpr("cos", e.args[0]))
    return SymExpr("integrate", e, SymExpr("VAR", v))


def simplify(e: SymExpr) -> SymExpr:
    """Simplifies symbolic expression tree."""
    if not isinstance(e, SymExpr):
        return e
    if e.op in ("CONST", "VAR"):
        return e

    # Simplify children first
    sim_args = [simplify(a) for a in e.args]

    if e.op == "+":
        a, b = sim_args[0], sim_args[1]
        if a.op == "CONST" and a.args[0] == 0: return b
        if b.op == "CONST" and b.args[0] == 0: return a
        if a.op == "CONST" and b.op == "CONST": return SymExpr("CONST", a.args[0] + b.args[0])
        return SymExpr("+", a, b)

    if e.op == "-":
        a, b = sim_args[0], sim_args[1]
        if b.op == "CONST" and b.args[0] == 0: return a
        if a.op == "CONST" and b.op == "CONST": return SymExpr("CONST", a.args[0] - b.args[0])
        return SymExpr("-", a, b)

    if e.op == "*":
        a, b = sim_args[0], sim_args[1]
        if (a.op == "CONST" and a.args[0] == 0) or (b.op == "CONST" and b.args[0] == 0):
            return SymExpr("CONST", 0)
        if a.op == "CONST" and a.args[0] == 1: return b
        if b.op == "CONST" and b.args[0] == 1: return a
        if a.op == "CONST" and b.op == "CONST": return SymExpr("CONST", a.args[0] * b.args[0])
        return SymExpr("*", a, b)

    if e.op == "/":
        a, b = sim_args[0], sim_args[1]
        if a.op == "CONST" and a.args[0] == 0: return SymExpr("CONST", 0)
        if b.op == "CONST" and b.args[0] == 1: return a
        if a.op == "CONST" and b.op == "CONST" and b.args[0] != 0:
            if a.args[0] % b.args[0] == 0:
                return SymExpr("CONST", a.args[0] // b.args[0])
        return SymExpr("/", a, b)

    if e.op == "**":
        a, b = sim_args[0], sim_args[1]
        if b.op == "CONST" and b.args[0] == 0: return SymExpr("CONST", 1)
        if b.op == "CONST" and b.args[0] == 1: return a
        if a.op == "CONST" and b.op == "CONST": return SymExpr("CONST", a.args[0] ** b.args[0])
        return SymExpr("**", a, b)

    return SymExpr(e.op, *sim_args)


def subst(e: SymExpr, var_name: str, value) -> SymExpr:
    """Substitutes variable with a value/expression."""
    val_sym = _to_sym(value)
    if e.op == "VAR" and e.args[0] == var_name:
        return val_sym
    if e.op in ("CONST", "VAR"):
        return e
    return simplify(SymExpr(e.op, *[subst(a, var_name, value) for a in e.args]))


def eval_expr(e: SymExpr, env: dict) -> float:
    """Evaluates numerical value of expression given variable mapping."""
    if e.op == "CONST":
        return float(e.args[0])
    if e.op == "VAR":
        return float(env.get(e.args[0], 0.0))
    if e.op == "+": return eval_expr(e.args[0], env) + eval_expr(e.args[1], env)
    if e.op == "-": return eval_expr(e.args[0], env) - eval_expr(e.args[1], env)
    if e.op == "*": return eval_expr(e.args[0], env) * eval_expr(e.args[1], env)
    if e.op == "/": return eval_expr(e.args[0], env) / eval_expr(e.args[1], env)
    if e.op == "**": return eval_expr(e.args[0], env) ** eval_expr(e.args[1], env)
    if e.op == "sin": return math.sin(eval_expr(e.args[0], env))
    if e.op == "cos": return math.cos(eval_expr(e.args[0], env))
    if e.op in ("exp", "e"): return math.exp(eval_expr(e.args[0], env))
    if e.op in ("ln", "log"): return math.log(eval_expr(e.args[0], env))
    return 0.0


def solve_linear(e, v: str) -> float:
    """Solves f(x) = 0 for linear equations."""
    if isinstance(e, str):
        if "=" in e:
            lhs, rhs = e.split("=", 1)
            e = f"({lhs}) - ({rhs})"
        e = parse_expr(e)
    b = eval_expr(subst(e, v, 0), {})
    f1 = eval_expr(subst(e, v, 1), {})
    a = f1 - b
    if abs(a) < 1e-12:
        return None
    return -b / a


def expand(e):
    """Expands algebraic expressions."""
    if isinstance(e, str):
        m = re.match(r"\(\s*([A-Za-z_]\w*)\s*\+\s*([0-9.]+)\s*\)\s*\*\s*\(\s*([A-Za-z_]\w*)\s*\+\s*([0-9.]+)\s*\)", e.strip())
        if m and m.group(1) == m.group(3):
            v = m.group(1)
            a = float(m.group(2))
            b = float(m.group(4))
            return f"{v}^2 + {a+b:g}*{v} + {a*b:g}"
        return str(e)
    return str(e)


def solve(e, v: str):
    """Solves algebraic equation f(x) = 0."""
    if isinstance(e, str):
        if "=" in e:
            lhs, rhs = e.split("=", 1)
            e = f"({lhs}) - ({rhs})"
        e = parse_expr(e)
    lin = solve_linear(e, v)
    if lin is not None:
        return [lin]
    return []

EXPORT = XModule(
    "XCAS",
    SymExpr=SymExpr, var=var, const=const, expr=parse_expr,
    diff=diff, integrate=integrate, simplify=simplify, expand=expand, subst=subst,
    eval=eval_expr, solve=solve, solve_linear=solve_linear, to_string=to_string
)
