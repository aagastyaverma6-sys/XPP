"""
shutil - High-Level File Operations Module for X++
"""

import shutil as _shutil
from . import XModule

def copy(src, dst): return _shutil.copy(src, dst)
def copy2(src, dst): return _shutil.copy2(src, dst)
def copytree(src, dst): return _shutil.copytree(src, dst, dirs_exist_ok=True)
def move(src, dst): return _shutil.move(src, dst)
def rmtree(path): return _shutil.rmtree(path, ignore_errors=True)
def which(cmd): return _shutil.which(cmd)
def disk_usage(path):
    u = _shutil.disk_usage(path)
    return {"total": u.total, "used": u.used, "free": u.free}

EXPORT = XModule(
    "shutil",
    copy=copy, copy2=copy2, copytree=copytree, move=move,
    rmtree=rmtree, which=which, disk_usage=disk_usage
)
