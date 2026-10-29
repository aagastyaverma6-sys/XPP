"""
logging - Logging Facility Module for X++
"""

import sys
import time
from . import XModule

DEBUG = 10
INFO = 20
WARNING = 30
ERROR = 40
CRITICAL = 50

_CURRENT_LEVEL = INFO

def set_level(level):
    global _CURRENT_LEVEL
    _CURRENT_LEVEL = int(level)

def _log(level_name, level_val, msg):
    if level_val >= _CURRENT_LEVEL:
        t = time.strftime("%Y-%m-%d %H:%M:%S")
        sys.stderr.write(f"[{t}] [{level_name}] {msg}\n")
        sys.stderr.flush()

def debug(msg): _log("DEBUG", DEBUG, msg)
def info(msg): _log("INFO", INFO, msg)
def warning(msg): _log("WARNING", WARNING, msg)
def error(msg): _log("ERROR", ERROR, msg)
def critical(msg): _log("CRITICAL", CRITICAL, msg)

EXPORT = XModule(
    "logging",
    DEBUG=DEBUG, INFO=INFO, WARNING=WARNING, ERROR=ERROR, CRITICAL=CRITICAL,
    set_level=set_level, debug=debug, info=info, warning=warning,
    error=error, critical=critical
)
