"""
X++ Runtime Environment for Python-backed execution (XCOM / XITR)
Provides built-ins, formatting, standard library modules, and package importing.
"""
import sys, builtins, time, importlib
from .stdlib import get_all_stdlibs, get_stdlib
from .pm import resolve_package

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
            # Special display for XModules vs raw dicts
            if hasattr(v, "__name__") and not v.__class__ is dict:
                return f"<module '{v.__name__}'>"
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

    def xpp_import(name):
        clean_name = name.strip("\"'").split("/")[-1].split("@")[0].replace("-", "_").replace(".", "_")
        std = get_stdlib(clean_name)
        if std is not None:
            return std
        # Try resolving via package manager
        resolved = resolve_package(name)
        if resolved and resolved[1]:
            # Load package module
            from .fast_transpiler import transpile
            with open(resolved[1], "r", encoding="utf-8") as pf:
                py_code = transpile(pf.read())
            sub_g = make_xpp_env()
            exec(py_code, sub_g)
            from .stdlib import XModule
            exports = {k: v for k, v in sub_g.items() if not k.startswith("_")}
            return XModule(clean_name, **exports)
        # Fallback to standard Python import
        try:
            return importlib.import_module(name)
        except Exception:
            raise ImportError(f"Cannot import X++ module or package '{name}'")

    def _xg(obj, attr):
        if isinstance(obj, dict) and attr in obj:
            return obj[attr]
        if hasattr(obj, attr):
            return getattr(obj, attr)
        if isinstance(obj, dict):
            return obj.get(attr, None)
        return getattr(obj, attr)

    def _xs(obj, attr, val):
        if isinstance(obj, dict):
            obj[attr] = val
        else:
            setattr(obj, attr, val)
        return val

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
    b_dict["__xpp_import__"] = xpp_import
    b_dict["_xg"] = _xg
    b_dict["_xs"] = _xs

    # Preload all 34 standard library modules into environment
    std_modules = get_all_stdlibs()

    g = {
        "__name__": "__main__",
        "__builtins__": b_dict,
        "nil": None,
        "true": True,
        "false": False,
        "_xpp_loop": xpp_loop,
        "__xpp_import__": xpp_import,
    }
    g.update(std_modules)
    return g
