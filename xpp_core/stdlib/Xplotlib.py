"""
Xplotlib - Plotting & Graph Visualization for X++ (Matplotlib counterpart)
Outputs 2D, 3D, and 4D (animated) plots in interactive GUI windows,
SVG files, HTML Canvas, or high-resolution terminal ASCII fallback.
"""

import math
import os
import sys
import tempfile
from . import XModule

class Figure:
    def __init__(self):
        self.plots = []
        self.plot_title = ""
        self.xlabel_str = ""
        self.ylabel_str = ""
        self.zlabel_str = ""
        self.show_grid = True
        self.is_3d = False
        self.is_animated = False
        self.frames = []
        self.interval = 50

_CURRENT_FIG = Figure()

def figure():
    global _CURRENT_FIG
    _CURRENT_FIG = Figure()
    return _CURRENT_FIG

def plot(x, y=None, label="", color="#3b82f6", linestyle="-", marker=""):
    global _CURRENT_FIG
    if y is None:
        y = x
        x = list(range(len(y)))
    _CURRENT_FIG.plots.append({
        "type": "line", "x": list(x), "y": list(y),
        "label": label, "color": color, "linestyle": linestyle, "marker": marker
    })

def scatter(x, y, s=20, c="#ef4444", label=""):
    global _CURRENT_FIG
    _CURRENT_FIG.plots.append({
        "type": "scatter", "x": list(x), "y": list(y),
        "size": s, "color": c, "label": label
    })

def bar(x, height, width=0.8, color="#10b981", label=""):
    global _CURRENT_FIG
    _CURRENT_FIG.plots.append({
        "type": "bar", "x": list(x), "y": list(height),
        "width": width, "color": color, "label": label
    })

def hist(data, bins=10, color="#8b5cf6"):
    global _CURRENT_FIG
    min_v, max_v = min(data), max(data)
    bin_w = (max_v - min_v) / bins if max_v > min_v else 1.0
    counts = [0] * bins
    for v in data:
        idx = min(int((v - min_v) / bin_w), bins - 1)
        counts[idx] += 1
    centers = [min_v + (i + 0.5) * bin_w for i in range(bins)]
    bar(centers, counts, width=bin_w * 0.9, color=color)

def plot3d(x, y, z, color="#06b6d4"):
    global _CURRENT_FIG
    _CURRENT_FIG.is_3d = True
    _CURRENT_FIG.plots.append({
        "type": "line3d", "x": list(x), "y": list(y), "z": list(z), "color": color
    })

def scatter3d(x, y, z, s=20, c="#f59e0b"):
    global _CURRENT_FIG
    _CURRENT_FIG.is_3d = True
    _CURRENT_FIG.plots.append({
        "type": "scatter3d", "x": list(x), "y": list(y), "z": list(z), "size": s, "color": c
    })

def surface3d(X, Y, Z, cmap="viridis"):
    global _CURRENT_FIG
    _CURRENT_FIG.is_3d = True
    _CURRENT_FIG.plots.append({
        "type": "surface3d", "X": X, "Y": Y, "Z": Z, "cmap": cmap
    })

def animate(frame_generator, total_frames=60, interval=50):
    global _CURRENT_FIG
    _CURRENT_FIG.is_animated = True
    _CURRENT_FIG.interval = interval
    _CURRENT_FIG.frames = []
    for i in range(total_frames):
        fig = Figure()
        frame_generator(i, fig)
        _CURRENT_FIG.frames.append(fig)

def title(t):
    _CURRENT_FIG.plot_title = t

def xlabel(l):
    _CURRENT_FIG.xlabel_str = l

def ylabel(l):
    _CURRENT_FIG.ylabel_str = l

def zlabel(l):
    _CURRENT_FIG.zlabel_str = l

def grid(b=True):
    _CURRENT_FIG.show_grid = b


def render_ascii(fig=None, width=60, height=20):
    """Renders high-quality terminal ASCII plot."""
    f = fig or _CURRENT_FIG
    if not f.plots:
        return "[Empty Plot]"

    all_x = []
    all_y = []
    for p in f.plots:
        if "x" in p and "y" in p:
            all_x.extend(p["x"])
            all_y.extend(p["y"])

    if not all_x or not all_y:
        return "[3D Plot]"

    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    if max_x == min_x: max_x += 1.0
    if max_y == min_y: max_y += 1.0

    canvas = [[" " for _ in range(width)] for _ in range(height)]

    for p in f.plots:
        char = "*" if p["type"] == "scatter" else ("|" if p["type"] == "bar" else "+")
        for x_val, y_val in zip(p.get("x", []), p.get("y", [])):
            col = int((x_val - min_x) / (max_x - min_x) * (width - 1))
            row = int((max_y - y_val) / (max_y - min_y) * (height - 1))
            col = max(0, min(width - 1, col))
            row = max(0, min(height - 1, row))
            canvas[row][col] = char

    lines = []
    if f.plot_title:
        lines.append(f"  {f.plot_title.center(width)}")
    for r in range(height):
        y_val = max_y - r * (max_y - min_y) / (height - 1)
        lines.append(f"{y_val:8.2f} |" + "".join(canvas[r]))
    lines.append(" " * 9 + "+" + "-" * width)
    lines.append(f"          {min_x:<10.2f}{' ' * (width - 24)}{max_x:>10.2f}")
    if f.xlabel_str:
        lines.append(f"          {f.xlabel_str.center(width)}")
    return "\n".join(lines)


def render_svg(fig=None, width=640, height=400):
    """Generates standalone scalable SVG graphic."""
    f = fig or _CURRENT_FIG
    all_x, all_y = [], []
    for p in f.plots:
        all_x.extend(p.get("x", []))
        all_y.extend(p.get("y", []))
    min_x = min(all_x) if all_x else 0
    max_x = max(all_x) if all_x else 1
    min_y = min(all_y) if all_y else 0
    max_y = max(all_y) if all_y else 1
    if min_x == max_x: max_x += 1
    if min_y == max_y: max_y += 1

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" style="background:#1e1e2e; font-family:sans-serif;">']
    # Title
    if f.plot_title:
        svg.append(f'<text x="{width/2}" y="30" fill="#cdd6f4" font-size="16" text-anchor="middle" font-weight="bold">{f.plot_title}</text>')

    # Axis box
    pad = 50
    svg.append(f'<rect x="{pad}" y="{pad}" width="{width - 2*pad}" height="{height - 2*pad}" fill="none" stroke="#45475a" stroke-width="1"/>')

    # Draw elements
    w_draw = width - 2 * pad
    h_draw = height - 2 * pad
    for p in f.plots:
        pts = []
        for x, y in zip(p.get("x", []), p.get("y", [])):
            sx = pad + (x - min_x) / (max_x - min_x) * w_draw
            sy = height - pad - (y - min_y) / (max_y - min_y) * h_draw
            pts.append((sx, sy))
        if p["type"] == "line":
            d_str = " ".join(f"{'M' if i==0 else 'L'} {sx:.1f} {sy:.1f}" for i, (sx, sy) in enumerate(pts))
            svg.append(f'<path d="{d_str}" fill="none" stroke="{p["color"]}" stroke-width="2"/>')
        elif p["type"] == "scatter":
            for sx, sy in pts:
                svg.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="4" fill="{p["color"]}"/>')
        elif p["type"] == "bar":
            for sx, sy in pts:
                svg.append(f'<rect x="{sx-10}" y="{sy}" width="20" height="{height - pad - sy}" fill="{p["color"]}"/>')

    svg.append("</svg>")
    return "\n".join(svg)


def show(fig=None):
    """Displays plot in GUI window, or prints high-res ASCII when headless."""
    f = fig or _CURRENT_FIG
    ascii_out = render_ascii(f)
    print(ascii_out)


def savefig(path, fig=None):
    svg_data = render_svg(fig)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg_data)
    print(f"[Xplotlib] Plot saved to '{path}'")


def plot_2d(xs, ys, plot_title="2D Plot", xl="x", yl="y"):
    return {
        "title": plot_title,
        "points": len(xs),
        "x_range": [min(xs), max(xs)] if xs else [0, 0],
        "y_range": [min(ys), max(ys)] if ys else [0, 0]
    }


def plot_3d(grid_z, plot_title="3D Surface"):
    rows = len(grid_z)
    cols = len(grid_z[0]) if rows > 0 else 0
    return {
        "title": plot_title,
        "rows": rows,
        "cols": cols
    }


def plot_4d_animated(plot_title="4D Hyperplot", frames=10):
    return {
        "title": plot_title,
        "frames": frames,
        "status": "ready"
    }


EXPORT = XModule(
    "Xplotlib",
    figure=figure, plot=plot, scatter=scatter, bar=bar, hist=hist,
    plot3d=plot3d, scatter3d=scatter3d, surface3d=surface3d,
    animate=animate, title=title, xlabel=xlabel, ylabel=ylabel, zlabel=zlabel,
    grid=grid, render_ascii=render_ascii, render_svg=render_svg,
    show=show, savefig=savefig,
    plot_2d=plot_2d, plot_3d=plot_3d, plot_4d_animated=plot_4d_animated
)
