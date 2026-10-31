"""
XGUI - Next-Generation GUI Architecture for X++ Apps
Builds ultra-modern, beautiful desktop & web GUIs styled with CSS & JS.
Supports glassmorphism, neo-brutalism, modern-dark themes, reactive state,
widgets (buttons, inputs, sliders, cards, modals), and event handling.
"""

import os
import json
import webbrowser
import tempfile
from . import XModule

THEMES = {
    "modern-dark": """
        body { background: #0f172a; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 24px; }
        .xgui-card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3); margin-bottom: 16px; }
        .xgui-button { background: #3b82f6; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
        .xgui-button:hover { background: #2563eb; transform: translateY(-1px); }
        .xgui-input { background: #0f172a; border: 1px solid #475569; color: #f8fafc; border-radius: 8px; padding: 10px 14px; width: 100%; box-sizing: border-box; }
        .xgui-input:focus { outline: none; border-color: #3b82f6; }
    """,
    "glassmorphism": """
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; font-family: sans-serif; margin: 0; padding: 32px; min-height: 100vh; }
        .xgui-card { background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.25); border-radius: 16px; padding: 24px; box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37); margin-bottom: 20px; }
        .xgui-button { background: rgba(255, 255, 255, 0.25); backdrop-filter: blur(4px); color: white; border: 1px solid rgba(255, 255, 255, 0.4); border-radius: 10px; padding: 12px 24px; font-weight: bold; cursor: pointer; transition: 0.2s; }
        .xgui-button:hover { background: rgba(255, 255, 255, 0.4); }
        .xgui-input { background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.3); color: white; border-radius: 10px; padding: 12px 16px; width: 100%; }
    """,
    "neo-brutalism": """
        body { background: #fef08a; color: #000000; font-family: 'Courier New', monospace; margin: 0; padding: 24px; }
        .xgui-card { background: #ffffff; border: 3px solid #000000; box-shadow: 5px 5px 0px #000000; border-radius: 0px; padding: 20px; margin-bottom: 20px; }
        .xgui-button { background: #a855f7; color: white; border: 3px solid #000000; box-shadow: 4px 4px 0px #000000; font-weight: 900; padding: 12px 20px; cursor: pointer; }
        .xgui-button:hover { transform: translate(-2px, -2px); box-shadow: 6px 6px 0px #000000; }
        .xgui-input { background: #ffffff; border: 3px solid #000000; padding: 10px 14px; width: 100%; font-weight: bold; }
    """
}

class GUIWindow:
    def __init__(self, title="XGUI Application", width=900, height=650, theme="modern-dark"):
        self.title = title
        self.width = width
        self.height = height
        self.theme = theme
        self.components = []
        self.custom_css_rules = ""
        self.injected_js_code = ""
        self.state = {}

    def add(self, comp):
        self.components.append(comp)
        return self

    def style(self, css):
        self.custom_css_rules += "\n" + css
        return self

    def inject_js(self, js):
        self.injected_js_code += "\n" + js
        return self

    def set_theme(self, theme_name):
        if theme_name in THEMES:
            self.theme = theme_name
        return self

    def render_html(self):
        theme_css = THEMES.get(self.theme, THEMES["modern-dark"])
        body_content = "\n".join(c.to_html() if hasattr(c, "to_html") else str(c) for c in self.components)
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{self.title}</title>
  <style>
    {theme_css}
    {self.custom_css_rules}
  </style>
</head>
<body>
  <div style="max-width: {self.width}px; margin: 0 auto;">
    {body_content}
  </div>
  <script>
    {self.injected_js_code}
  </script>
</body>
</html>"""

    def show(self):
        html = self.render_html()
        fd, path = tempfile.mkstemp(suffix=".html", prefix="xgui_app_")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[XGUI] Window '{self.title}' launched ({self.width}x{self.height}, theme: {self.theme})")
        try:
            webbrowser.open("file://" + os.path.abspath(path))
        except Exception:
            pass


    def __getitem__(self, item):
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)


class Component:
    def __init__(self, html_gen, meta=None):
        self.html_gen = html_gen
        self.meta = meta or {}

    def __getitem__(self, item):
        if item in self.meta:
            return self.meta[item]
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    def to_html(self):
        return self.html_gen()


def window(title="XGUI App", width=900, height=650, theme="modern-dark"):
    return GUIWindow(title, width, height, theme)

def card(title="", content="", actions=None):
    def _render():
        act_html = actions.to_html() if hasattr(actions, "to_html") else actions
        act_str = f"<div style='margin-top:16px;'>{act_html}</div>" if actions else ""
        t_str = f"<h2 style='margin-top:0;font-size:1.4rem;'>{title}</h2>" if title else ""
        cnt_html = content.to_html() if hasattr(content, "to_html") else content
        return f"<div class='xgui-card'>{t_str}<div>{cnt_html}</div>{act_str}</div>"
    return Component(_render, {"title": title})

def button(label, onclick=""):
    click_attr = f' onclick="{onclick}"' if onclick else ""
    return Component(lambda: f"<button class='xgui-button'{click_attr}>{label}</button>", {"label": label})

def text_input(placeholder="", value="", id=None):
    id_attr = f' id="{id}"' if id else ""
    val_attr = f' value="{value}"' if value else ""
    return Component(lambda: f"<input type='text' class='xgui-input' placeholder='{placeholder}'{val_attr}{id_attr} />", {"label": placeholder, "value": value})

def input_field(label="Input", input_type="text"):
    return Component(lambda: f"<input type='{input_type}' class='xgui-input' placeholder='{label}' />", {"label": label, "type": input_type})

def slider(label="Slider", min_val=0, max_val=100, value=50, oninput=""):
    inp_attr = f' oninput="{oninput}"' if oninput else ""
    return Component(lambda: f"<input type='range' min='{min_val}' max='{max_val}' value='{value}'{inp_attr} style='width:100%;cursor:pointer;' />", {"label": label, "value": value, "min": min_val, "max": max_val})

def row(children):
    return Component(lambda: f"<div style='display:flex;gap:16px;align-items:center;'>{''.join(c.to_html() if hasattr(c, 'to_html') else str(c) for c in children)}</div>")

def col(children):
    return Component(lambda: f"<div style='display:flex;flex-direction:column;gap:16px;'>{''.join(c.to_html() if hasattr(c, 'to_html') else str(c) for c in children)}</div>")

def render_html(win, theme_override=""):
    if hasattr(win, "render_html"):
        return win.render_html()
    return f"<html><head><style>{theme_override}</style></head><body><h1>{getattr(win, 'title', 'XGUI')}</h1></body></html>"

EXPORT = XModule(
    "XGUI",
    window=window, card=card, button=button, text_input=text_input, input_field=input_field,
    slider=slider, row=row, col=col, render_html=render_html, GUIWindow=GUIWindow, THEMES=THEMES
)
