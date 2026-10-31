"""
Xin - Keyboard & Mouse Input Detection for X++
Provides key event polling, single character capture, mouse coordinate tracking,
and asynchronous event listeners.
"""

import sys
import os
from . import XModule

class InputState:
    def __init__(self):
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_buttons = [False, False, False]
        self.pressed_keys = set()
        self.event_handlers = {}

_STATE = InputState()

def getch():
    """Reads a single keypress without waiting for Enter."""
    if os.name == "nt":
        import msvcrt
        return msvcrt.getch().decode("utf-8", errors="ignore")
    else:
        import tty, termios
        fd = sys.stdin.fileno()
        try:
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch
        except Exception:
            return sys.stdin.read(1) if not sys.stdin.isatty() else ""

def get_key():
    return getch()

def is_key_pressed(key: str) -> bool:
    return key.lower() in _STATE.pressed_keys

class MousePos(dict):
    def __init__(self, x, y):
        super().__init__(x=x, y=y)
        self.x = x
        self.y = y
    def __getitem__(self, item):
        if item in (0, "0"): return self.x
        if item in (1, "1"): return self.y
        return super().__getitem__(item)


def get_mouse_position():
    return MousePos(_STATE.mouse_x, _STATE.mouse_y)

def is_mouse_down(button: int = 0) -> bool:
    if 0 <= button < len(_STATE.mouse_buttons):
        return _STATE.mouse_buttons[button]
    return False

def poll_keys():
    return list(_STATE.pressed_keys)

def map_input(key, action):
    return {"key": key, "action": action}

def on(event_name: str, handler):
    _STATE.event_handlers.setdefault(event_name, []).append(handler)

def emit(event_name: str, *args):
    for h in _STATE.event_handlers.get(event_name, []):
        h(*args)

EXPORT = XModule(
    "Xin",
    getch=getch, get_key=get_key, is_key_pressed=is_key_pressed, poll_keys=poll_keys,
    get_mouse_position=get_mouse_position, is_mouse_down=is_mouse_down, map_input=map_input,
    on=on, emit=emit
)
