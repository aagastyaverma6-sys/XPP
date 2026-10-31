"""
sys - System-specific Parameters & Functions Module for X++
"""

import sys as _sys
from . import XModule

def argv(): return list(_sys.argv)
def version(): return _sys.version
def platform(): return _sys.platform
def exit(code=0): _sys.exit(code)
def getrecursionlimit(): return _sys.getrecursionlimit()
def setrecursionlimit(n): _sys.setrecursionlimit(int(n))
def path(): return list(_sys.path)
def stdout_write(s): _sys.stdout.write(str(s)); _sys.stdout.flush()
def stderr_write(s): _sys.stderr.write(str(s)); _sys.stderr.flush()
def stdin_read(): return _sys.stdin.read()

# Expose standard stream attributes
stdin = _sys.stdin
stdout = _sys.stdout
stderr = _sys.stderr

EXPORT = XModule(
    "sys",
    argv=argv, version=version, platform=platform, exit=exit,
    getrecursionlimit=getrecursionlimit, setrecursionlimit=setrecursionlimit,
    path=path, stdout_write=stdout_write, stderr_write=stderr_write, stdin_read=stdin_read,
    stdin=stdin, stdout=stdout, stderr=stderr
)
