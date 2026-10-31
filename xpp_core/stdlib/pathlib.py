"""
pathlib - Object-oriented Filesystem Paths Module for X++
"""

from pathlib import Path as _PyPath
from . import XModule

class Path:
    def __init__(self, p="."):
        self._p = _PyPath(p)

    def exists(self): return self._p.exists()
    def is_file(self): return self._p.is_file()
    def is_dir(self): return self._p.is_dir()
    def read_text(self): return self._p.read_text(encoding="utf-8", errors="replace")
    def write_text(self, data): return self._p.write_text(str(data), encoding="utf-8")
    def read_bytes(self): return self._p.read_bytes()
    def write_bytes(self, data): return self._p.write_bytes(data)
    @property
    def name(self): return self._p.name
    @property
    def stem(self): return self._p.stem
    @property
    def suffix(self): return self._p.suffix
    def parent(self): return Path(str(self._p.parent))
    def resolve(self): return str(self._p.resolve())
    def joinpath(self, *others): return Path(str(self._p.joinpath(*others)))
    def iterdir(self): return [Path(str(x)) for x in self._p.iterdir()]
    def glob(self, pattern): return [Path(str(x)) for x in self._p.glob(pattern)]
    def mkdir(self, parents=True, exist_ok=True): self._p.mkdir(parents=parents, exist_ok=exist_ok)
    def unlink(self): self._p.unlink()

    def __str__(self): return str(self._p)
    def __repr__(self): return f"Path('{self._p}')"

EXPORT = XModule("pathlib", Path=Path)
