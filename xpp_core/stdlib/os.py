"""
os - Operating System & Filesystem Module for X++
"""

import os as _os
import sys as _sys
from . import XModule

def name(): return _os.name
def getcwd(): return _os.getcwd()
def chdir(path): return _os.chdir(path)
def listdir(path="."): return _os.listdir(path)
def mkdir(path): return _os.mkdir(path)
def makedirs(path): return _os.makedirs(path, exist_ok=True)
def remove(path): return _os.remove(path)
def rmdir(path): return _os.rmdir(path)
def rename(src, dst): return _os.rename(src, dst)
def environ(): return dict(_os.environ)
def getenv(k, default=None): return _os.getenv(k, default)
def setenv(k, v): _os.environ[k] = str(v)
def path_exists(p): return _os.path.exists(p)
def path_isdir(p): return _os.path.isdir(p)
def path_isfile(p): return _os.path.isfile(p)
def path_join(*parts): return _os.path.join(*parts)
def path_split(p): return list(_os.path.split(p))
def path_basename(p): return _os.path.basename(p)
def path_dirname(p): return _os.path.dirname(p)
def path_ext(p): return _os.path.splitext(p)[1]
def system(cmd): return _os.system(cmd)

EXPORT = XModule(
    "os",
    name=_os.name, path=_os.path, getcwd=getcwd, chdir=chdir, listdir=listdir,
    mkdir=mkdir, makedirs=makedirs, remove=remove, rmdir=rmdir, rename=rename,
    environ=environ, getenv=getenv, setenv=setenv,
    path_exists=path_exists, path_isdir=path_isdir, path_isfile=path_isfile,
    path_join=path_join, path_split=path_split, path_basename=path_basename,
    path_dirname=path_dirname, path_ext=path_ext, system=system
)
