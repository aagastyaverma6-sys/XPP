"""
X++ Standard Library Suite - v0.4.5
Contains all mathematical, web, development, and system counterpart modules.
"""

import sys as _py_sys
import importlib

class XModule(dict):
    """
    Module container accessible both via attribute lookups (mod.foo)
    and dict subscripting (mod['foo']) for seamless compatibility across
    transpilation and VM runtimes.
    """
    def __init__(self, _mod_name: str, **kwargs):
        super().__init__(**kwargs)
        self.__name__ = _mod_name
        self.__dict__.update(kwargs)

    def __getattr__(self, item):
        if item in self:
            return self[item]
        raise AttributeError(f"Module '{self.__name__}' has no attribute '{item}'")

    def __setattr__(self, key, value):
        if key in ("__name__",):
            super().__setattr__(key, value)
        else:
            self[key] = value
            self.__dict__[key] = value

    def __repr__(self):
        return f"<xpp_module '{self.__name__}' ({len(self)} members)>"


STDLIB_MODULE_NAMES = [
    # Mathematical Libs
    "mathX", "Xsci", "Xnum", "Xlin", "XCAS", "XCalculus", "Xplotlib",
    # Web Related Libs
    "ScrapeX", "XWeb", "XWview",
    # Development Libs
    "GraphiX", "XGUI", "TerminX", "Xin", "GameX", "Xanmin8",
    # System & Python Counterpart Libs
    "os", "sys", "pathlib", "shutil", "time", "datetime",
    "random", "json", "csv", "re", "collections", "itertools",
    "functools", "urllib", "http", "socket", "unittest", "logging", "sqlite3"
]

_LOADED_MODULES = {}

def get_stdlib(name: str):
    """Dynamically loads and returns a standard library module by name."""
    if name in _LOADED_MODULES:
        return _LOADED_MODULES[name]
    if name not in STDLIB_MODULE_NAMES:
        return None
    try:
        mod = importlib.import_module(f".{name}", package=__name__)
        if hasattr(mod, "EXPORT"):
            res = mod.EXPORT
        elif hasattr(mod, name):
            res = getattr(mod, name)
        else:
            # Wrap all public members into XModule
            members = {k: v for k, v in mod.__dict__.items() if not k.startswith("_")}
            res = XModule(name, **members)
        _LOADED_MODULES[name] = res
        return res
    except Exception as e:
        _py_sys.stderr.write(f"[XPP StdLib] Error loading module '{name}': {e}\n")
        return None

def get_all_stdlibs():
    """Returns a dictionary of all standard libraries ready for runtime environment."""
    res = {}
    for name in STDLIB_MODULE_NAMES:
        m = get_stdlib(name)
        if m is not None:
            res[name] = m
    return res
