"""
XWeb - Web Creation & Full-Stack Development Module for X++
Generates semantic HTML, responsive modern CSS, reactive JS,
manages HTTP routes, and exports production-ready static sites.
"""

import http.server
import socketserver
import os
import json
from . import XModule

# ------------------------------------------------------------- HTML Builders
def tag(name, content="", **attrs):
    """Generates an HTML element with attributes and content."""
    attr_str = ""
    for k, v in attrs.items():
        k_clean = k.replace("_", "-")
        attr_str += f' {k_clean}="{v}"'
    if name in ("img", "input", "br", "hr", "meta", "link"):
        return f"<{name}{attr_str} />"
    if isinstance(content, list):
        content = "\n".join(str(c) for c in content)
    return f"<{name}{attr_str}>{content}</{name}>"

def div(content="", **attrs): return tag("div", content, **attrs)
def p(content="", **attrs): return tag("p", content, **attrs)
def span(content="", **attrs): return tag("span", content, **attrs)
def a(content="", href="#", **attrs): return tag("a", content, href=href, **attrs)
def button(content="", **attrs): return tag("button", content, **attrs)
def h1(content="", **attrs): return tag("h1", content, **attrs)
def h2(content="", **attrs): return tag("h2", content, **attrs)
def h3(content="", **attrs): return tag("h3", content, **attrs)
def h4(content="", **attrs): return tag("h4", content, **attrs)
def section(content="", **attrs): return tag("section", content, **attrs)
def nav(content="", **attrs): return tag("nav", content, **attrs)
def header(content="", **attrs): return tag("header", content, **attrs)
def footer(content="", **attrs): return tag("footer", content, **attrs)
def ul(items, **attrs): return tag("ul", "\n".join(tag("li", it) for it in items), **attrs)
def ol(items, **attrs): return tag("ol", "\n".join(tag("li", it) for it in items), **attrs)
def img(src, alt="", **attrs): return tag("img", src=src, alt=alt, **attrs)
def input_tag(type="text", placeholder="", **attrs): return tag("input", type=type, placeholder=placeholder, **attrs)


# -------------------------------------------------------------- CSS Builders
def style(rules: dict) -> str:
    """Converts a dictionary of CSS properties into an inline style string."""
    return "; ".join(f"{k.replace('_', '-')}: {v}" for k, v in rules.items())

def stylesheet(selectors: dict) -> str:
    """Converts a dictionary of selectors and rules into a complete CSS stylesheet."""
    lines = []
    for sel, rules in selectors.items():
        lines.append(f"{sel} {{")
        for prop, val in rules.items():
            lines.append(f"  {prop.replace('_', '-')}: {val};")
        lines.append("}\n")
    return "\n".join(lines)


# ---------------------------------------------------------- Full Page Layout
def page(title="X++ Web Page", body="", css="", js="", meta=None):
    """Assembles a full HTML5 document."""
    meta = meta or {}
    meta_tags = ['<meta charset="utf-8">', '<meta name="viewport" content="width=device-width, initial-scale=1.0">']
    for k, v in meta.items():
        meta_tags.append(f'<meta name="{k}" content="{v}">')

    css_block = f"<style>\n{css}\n</style>" if css else ""
    js_block = f"<script>\n{js}\n</script>" if js else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  {"\n  ".join(meta_tags)}
  <title>{title}</title>
  {css_block}
</head>
<body>
{body}
{js_block}
</body>
</html>"""


# ------------------------------------------------------------- Web Server App
class WebApp:
    def __init__(self):
        self.routes = {}

    def route(self, path, handler):
        self.routes[path] = handler

    def get(self, path, handler):
        self.route(path, handler)

    def render(self, path):
        handler = self.routes.get(path)
        if handler:
            return handler()
        return "<h1>404 Not Found</h1>", 404

    def export_static(self, output_dir="dist"):
        os.makedirs(output_dir, exist_ok=True)
        for path, handler in self.routes.items():
            filename = "index.html" if path in ("/", "") else path.strip("/") + ".html"
            filepath = os.path.join(output_dir, filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            content = handler()
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content if isinstance(content, str) else str(content))
        print(f"[XWeb] Static site exported to '{output_dir}/'")


def card(title, content, btn_text="Action"):
    return f"""<div class="card" style="border:1px solid #333;border-radius:8px;padding:16px;margin:8px;">
  <h3>{title}</h3>
  <p>{content}</p>
  <button style="padding:6px 12px;background:#0066cc;color:#fff;border:none;border-radius:4px;">{btn_text}</button>
</div>"""


def dashboard(title, metrics):
    cards = []
    for m in metrics:
        cards.append(f"""<div style="background:#222;color:#eee;padding:12px;border-radius:6px;margin:4px;">
  <strong>{m.get('label', '')}</strong>: {m.get('value', '')}
</div>""")
    return page(title, f"<h1>{title}</h1>\n" + "\n".join(cards))


def app():
    return WebApp()

EXPORT = XModule(
    "XWeb",
    tag=tag, div=div, p=p, span=span, a=a, button=button,
    h1=h1, h2=h2, h3=h3, h4=h4, section=section, nav=nav, header=header, footer=footer,
    ul=ul, ol=ol, img=img, input_tag=input_tag,
    style=style, stylesheet=stylesheet, page=page, card=card, dashboard=dashboard, app=app, WebApp=WebApp
)
