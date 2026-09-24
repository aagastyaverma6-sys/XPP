"""
X++ Runtime Environment for Python-backed execution (XCOM / XITR)
Provides built-ins and formatting matching the native VM specification.
"""
import sys, builtins, time

def make_xpp_env(argv=None):
    try:
        sys.setrecursionlimit(max(100000, sys.getrecursionlimit()))
    except Exception:
        pass

    def _s(v):
        if v is None:
            return "nil"
        if v is True:
            return "true"
        if v is False:
            return "false"
        if isinstance(v, list):
            return "[" + ", ".join(_s(x) for x in v) + "]"
        if isinstance(v, dict):
            return "{" + ", ".join(f'"{k}": {_s(val)}' for k, val in v.items()) + "}"
        if isinstance(v, range):
            return "[" + ", ".join(str(i) for i in v) + "]"
        return str(v)

    def xpp_print(*args, **kwargs):
        sep = kwargs.get("sep", " ")
        end = kwargs.get("end", "\n")
        file = kwargs.get("file", sys.stdout)
        file.write(sep.join(_s(a) for a in args) + end)
        if kwargs.get("flush", False):
            file.flush()

    def xpp_contains(seq, key):
        if isinstance(seq, (list, dict, str, tuple)):
            return key in seq
        return False

    def xpp_read(path):
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def xpp_write(path, text):
        with open(path, "w", encoding="utf-8") as f:
            return f.write(str(text))

    def xpp_push(lst, val):
        lst.append(val)
        return lst

    def xpp_loop(start, end, step=1):
        if step > 0:
            return range(start, end + 1, step)
        elif step < 0:
            return range(start, end - 1, step)
        return []

    def xpp_type(v):
        if v is None:
            return "nil"
        if isinstance(v, bool):
            return "bool"
        if isinstance(v, int):
            return "int"
        if isinstance(v, float):
            return "float"
        if isinstance(v, str):
            return "string"
        if isinstance(v, list):
            return "list"
        if isinstance(v, dict):
            return "dict"
        if callable(v):
            return "function"
        return "unknown"

    b_dict = dict(builtins.__dict__)
    b_dict["print"] = xpp_print
    b_dict["range"] = lambda *a: list(builtins.range(*a))
    b_dict["contains"] = xpp_contains
    b_dict["read"] = xpp_read
    b_dict["write"] = xpp_write
    b_dict["clock"] = time.perf_counter
    b_dict["push"] = xpp_push
    b_dict["keys"] = lambda d: list(d.keys())
    b_dict["values"] = lambda d: list(d.values())
    b_dict["type"] = xpp_type
    b_dict["get"] = lambda seq, k, default=None: (
        seq[k] if (isinstance(seq, list) and 0 <= (k if k >= 0 else k + len(seq)) < len(seq))
        or (isinstance(seq, dict) and k in seq) else default
    )
    b_dict["set"] = lambda seq, k, v: (seq.__setitem__(k, v), seq)[1]
    b_dict["_xpp_loop"] = xpp_loop

    g = {
        "__name__": "__main__",
        "__builtins__": b_dict,
        "nil": None,
        "true": True,
        "false": False,
        "_xpp_loop": xpp_loop,
    }
    return g
