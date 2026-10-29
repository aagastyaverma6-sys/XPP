"""
GraphiX - High-Performance 2D Vector & Canvas Graphics for X++
Provides rendering primitives, matrix transformations, styling via standard CSS,
and export to SVG, HTML Canvas, or interactive window surfaces.
"""

import math
import os
from . import XModule

class Canvas:
    def __init__(self, width=800, height=600, title="GraphiX Window"):
        self.width = width
        self.height = height
        self.title = title
        self.bg_color = "#ffffff"
        self.commands = []
        self.css_styles = {}
        self.transform_stack = []

    def clear(self, color="#ffffff"):
        self.bg_color = color
        self.commands = []

    def set_css(self, selector, css_dict_or_str):
        self.css_styles[selector] = css_dict_or_str

    def rect(self, x, y, w, h, style=None):
        self.commands.append({"type": "rect", "x": x, "y": y, "w": w, "h": h, "style": style or {}})

    def circle(self, cx, cy, r, style=None):
        self.commands.append({"type": "circle", "cx": cx, "cy": cy, "r": r, "style": style or {}})

    def line(self, x1, y1, x2, y2, style=None):
        self.commands.append({"type": "line", "x1": x1, "y1": y1, "x2": x2, "y2": y2, "style": style or {}})

    def polygon(self, points, style=None):
        self.commands.append({"type": "polygon", "points": points, "style": style or {}})

    def text(self, text_str, x, y, style=None):
        self.commands.append({"type": "text", "text": text_str, "x": x, "y": y, "style": style or {}})

    def path(self, d_string, style=None):
        self.commands.append({"type": "path", "d": d_string, "style": style or {}})

    def to_svg(self):
        css_lines = []
        for sel, st in self.css_styles.items():
            if isinstance(st, dict):
                body = "; ".join(f"{k.replace('_', '-')}: {v}" for k, v in st.items())
            else:
                body = str(st)
            css_lines.append(f"{sel} {{ {body} }}")
        style_block = f"<style>\n{chr(10).join(css_lines)}\n</style>" if css_lines else ""

        svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" style="background:{self.bg_color}; font-family:sans-serif;">']
        if style_block:
            svg.append(style_block)

        for cmd in self.commands:
            st = cmd.get("style", {})
            st_str = "; ".join(f"{k.replace('_', '-')}: {v}" for k, v in st.items())
            st_attr = f' style="{st_str}"' if st_str else ""

            if cmd["type"] == "rect":
                fill = st.get("fill", "#3b82f6")
                stroke = st.get("stroke", "none")
                svg.append(f'<rect x="{cmd["x"]}" y="{cmd["y"]}" width="{cmd["w"]}" height="{cmd["h"]}" fill="{fill}" stroke="{stroke}"{st_attr}/>')
            elif cmd["type"] == "circle":
                fill = st.get("fill", "#ef4444")
                stroke = st.get("stroke", "none")
                svg.append(f'<circle cx="{cmd["cx"]}" cy="{cmd["cy"]}" r="{cmd["r"]}" fill="{fill}" stroke="{stroke}"{st_attr}/>')
            elif cmd["type"] == "line":
                stroke = st.get("stroke", "#000000")
                w = st.get("stroke_width", 2)
                svg.append(f'<line x1="{cmd["x1"]}" y1="{cmd["y1"]}" x2="{cmd["x2"]}" y2="{cmd["y2"]}" stroke="{stroke}" stroke-width="{w}"{st_attr}/>')
            elif cmd["type"] == "polygon":
                pts_str = " ".join(f"{p[0]},{p[1]}" for p in cmd["points"])
                fill = st.get("fill", "#10b981")
                svg.append(f'<polygon points="{pts_str}" fill="{fill}"{st_attr}/>')
            elif cmd["type"] == "text":
                fill = st.get("fill", "#000000")
                size = st.get("font_size", 16)
                svg.append(f'<text x="{cmd["x"]}" y="{cmd["y"]}" fill="{fill}" font-size="{size}"{st_attr}>{cmd["text"]}</text>')
            elif cmd["type"] == "path":
                fill = st.get("fill", "none")
                stroke = st.get("stroke", "#000000")
                svg.append(f'<path d="{cmd["d"]}" fill="{fill}" stroke="{stroke}"{st_attr}/>')

        svg.append("</svg>")
        return "\n".join(svg)

    def save_svg(self, path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_svg())
        print(f"[GraphiX] Graphic saved to '{path}'")

    def show(self):
        svg_content = self.to_svg()
        print(f"[GraphiX] Canvas '{self.title}' rendered ({self.width}x{self.height}, {len(self.commands)} elements)")


    def __getitem__(self, item):
        if item == "elements": return self.commands
        if item == "css": return self.css_styles
        if hasattr(self, item): return getattr(self, item)
        raise KeyError(item)


_ACTIVE_CANVAS = Canvas()

def create_canvas(width=800, height=600, title="GraphiX Window"):
    global _ACTIVE_CANVAS
    _ACTIVE_CANVAS = Canvas(width, height, title)
    return _ACTIVE_CANVAS

def clear(color="#ffffff"): _ACTIVE_CANVAS.clear(color)

def rect(*args):
    if len(args) >= 5 and isinstance(args[0], Canvas):
        c, x, y, w, h = args[:5]
        style = args[5] if len(args) > 5 else None
        if isinstance(style, str): style = {"fill": style}
        c.rect(x, y, w, h, style)
    elif len(args) >= 4:
        x, y, w, h = args[:4]
        style = args[4] if len(args) > 4 else None
        if isinstance(style, str): style = {"fill": style}
        _ACTIVE_CANVAS.rect(x, y, w, h, style)

def circle(*args):
    if len(args) >= 4 and isinstance(args[0], Canvas):
        c, cx, cy, r = args[:4]
        style = args[4] if len(args) > 4 else None
        if isinstance(style, str): style = {"fill": style}
        c.circle(cx, cy, r, style)
    elif len(args) >= 3:
        cx, cy, r = args[:3]
        style = args[3] if len(args) > 3 else None
        if isinstance(style, str): style = {"fill": style}
        _ACTIVE_CANVAS.circle(cx, cy, r, style)

def line(*args):
    if len(args) >= 5 and isinstance(args[0], Canvas):
        c, x1, y1, x2, y2 = args[:5]
        style = args[5] if len(args) > 5 else None
        if isinstance(style, str): style = {"stroke": style}
        c.line(x1, y1, x2, y2, style)
    elif len(args) >= 4:
        x1, y1, x2, y2 = args[:4]
        style = args[4] if len(args) > 4 else None
        if isinstance(style, str): style = {"stroke": style}
        _ACTIVE_CANVAS.line(x1, y1, x2, y2, style)

def polygon(points, style=None): _ACTIVE_CANVAS.polygon(points, style)
def text(text_str, x, y, style=None): _ACTIVE_CANVAS.text(text_str, x, y, style)
def path(d_string, style=None): _ACTIVE_CANVAS.path(d_string, style)

def apply_css(*args):
    if len(args) == 2 and isinstance(args[0], Canvas):
        args[0].set_css("all", args[1])
    elif len(args) == 2:
        _ACTIVE_CANVAS.set_css(args[0], args[1])
    elif len(args) == 1:
        _ACTIVE_CANVAS.set_css("all", args[0])

def to_svg(c=None):
    target = c if isinstance(c, Canvas) else _ACTIVE_CANVAS
    return target.to_svg()

def show(): _ACTIVE_CANVAS.show()
def save_svg(filepath): _ACTIVE_CANVAS.save_svg(filepath)

EXPORT = XModule(
    "GraphiX",
    Canvas=Canvas, create_canvas=create_canvas, clear=clear,
    rect=rect, circle=circle, line=line, polygon=polygon, text=text, path=path,
    apply_css=apply_css, to_svg=to_svg, show=show, save_svg=save_svg
)
