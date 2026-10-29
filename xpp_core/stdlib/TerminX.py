"""
TerminX - Terminal & Console UI Toolkit for X++
Provides ANSI colors, text styles, terminal cursor controls,
bordered boxes, aligned tables, progress bars, and prompts.
"""

import sys
import shutil
from . import XModule

# ANSI Escape Codes
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_DIM = "\033[2m"
C_ITALIC = "\033[3m"
C_UNDERLINE = "\033[4m"

COLORS = {
    "black": "\033[30m", "red": "\033[31m", "green": "\033[32m", "yellow": "\033[33m",
    "blue": "\033[34m", "magenta": "\033[35m", "cyan": "\033[36m", "white": "\033[37m",
    "bright_black": "\033[90m", "bright_red": "\033[91m", "bright_green": "\033[92m",
    "bright_yellow": "\033[93m", "bright_blue": "\033[94m", "bright_magenta": "\033[95m",
    "bright_cyan": "\033[96m", "bright_white": "\033[97m"
}

BG_COLORS = {
    "bg_black": "\033[40m", "bg_red": "\033[41m", "bg_green": "\033[42m",
    "bg_yellow": "\033[43m", "bg_blue": "\033[44m", "bg_magenta": "\033[45m",
    "bg_cyan": "\033[46m", "bg_white": "\033[47m"
}

def colorize(text, fg=None, bg=None, bold=False, underline=False):
    prefix = ""
    if bold: prefix += C_BOLD
    if underline: prefix += C_UNDERLINE
    if fg and fg in COLORS: prefix += COLORS[fg]
    if bg and bg in BG_COLORS: prefix += BG_COLORS[bg]
    return f"{prefix}{text}{C_RESET}"

def red(s): return colorize(s, "red")
def green(s): return colorize(s, "green")
def yellow(s): return colorize(s, "yellow")
def blue(s): return colorize(s, "blue")
def magenta(s): return colorize(s, "magenta")
def cyan(s): return colorize(s, "cyan")
def bold(s): return f"{C_BOLD}{s}{C_RESET}"
def italic(s): return f"{C_ITALIC}{s}{C_RESET}"
def underline(s): return f"{C_UNDERLINE}{s}{C_RESET}"

# Cursor & Screen
def clear():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()

def move_cursor(row, col):
    sys.stdout.write(f"\033[{row};{col}H")
    sys.stdout.flush()

def get_terminal_size():
    cols, rows = shutil.get_terminal_size(fallback=(80, 24))
    return {"cols": cols, "rows": rows}

# Rich UI Components
def box(text_content, title="", style="rounded", color="cyan"):
    lines = text_content.splitlines() if isinstance(text_content, str) else [str(x) for x in text_content]
    max_w = max(len(l) for l in lines) if lines else 0
    if title:
        max_w = max(max_w, len(title) + 4)
    w = max_w + 4

    # Borders
    if style == "double":
        tl, tr, bl, br, hz, vt = "╔", "╗", "╚", "╝", "═", "║"
    elif style == "rounded":
        tl, tr, bl, br, hz, vt = "╭", "╮", "╰", "╯", "─", "│"
    else:
        tl, tr, bl, br, hz, vt = "+", "+", "+", "+", "-", "|"

    out = []
    if title:
        t_pad = (w - 2 - len(title) - 2)
        top = tl + hz + f" {title} " + (hz * max(0, t_pad)) + tr
    else:
        top = tl + (hz * (w - 2)) + tr

    out.append(colorize(top, color))
    for l in lines:
        pad = w - 4 - len(l)
        out.append(colorize(vt, color) + "  " + l + (" " * pad) + colorize(vt, color))
    out.append(colorize(bl + (hz * (w - 2)) + br, color))
    return "\n".join(out)


def table(headers, rows, style="clean"):
    cols = len(headers)
    col_widths = [len(str(h)) for h in headers]
    for row in rows:
        for i in range(min(cols, len(row))):
            col_widths[i] = max(col_widths[i], len(str(row[i])))

    fmt = " │ ".join(f"{{:<{w}}}" for w in col_widths)
    sep = "─┼─".join("─" * w for w in col_widths)

    out = []
    out.append(bold(fmt.format(*headers)))
    out.append(sep)
    for row in rows:
        padded = list(row) + [""] * (cols - len(row))
        out.append(fmt.format(*[str(x) for x in padded[:cols]]))
    return "\n".join(out)


def progress_bar(current, total, width=30, label=""):
    frac = max(0.0, min(1.0, current / total)) if total > 0 else 0.0
    filled = int(frac * width)
    bar_str = "█" * filled + "░" * (width - filled)
    pct = int(frac * 100)
    lbl = f"{label} " if label else ""
    return f"{lbl}[{bar_str}] {pct}% ({current}/{total})"


def prompt(question, default=""):
    def_str = f" [{default}]" if default else ""
    sys.stdout.write(bold(question) + def_str + ": ")
    sys.stdout.flush()
    try:
        val = input()
        return val if val else default
    except EOFError:
        return default

def banner(text, color="cyan"):
    w = len(text) + 6
    border = "=" * w
    content = f"== {text} =="
    return colorize(f"{border}\n{content}\n{border}", color, bold=True)


EXPORT = XModule(
    "TerminX",
    colorize=colorize, red=red, green=green, yellow=yellow, blue=blue,
    magenta=magenta, cyan=cyan, bold=bold, italic=italic, underline=underline,
    clear=clear, move_cursor=move_cursor, get_terminal_size=get_terminal_size,
    box=box, table=table, progress_bar=progress_bar, prompt=prompt, banner=banner
)
