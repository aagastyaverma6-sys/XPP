"""
XWview - Webview & Embedded Web Display Library for X++
Allows displaying web content, local HTML/CSS/JS, and interactive web interfaces
inside desktop windows or via system webview bridges.
"""

import os
import sys
import tempfile
import webbrowser
from . import XModule

class WebViewWindow:
    def __init__(self, title="X++ Web View", width=800, height=600, url=None, html=None):
        self.title = title
        self.width = width
        self.height = height
        self.url = url
        self.html = html
        self.bound_functions = {}
        self.is_open = False

    def load_url(self, url):
        self.url = url
        self.html = None

    def load_html(self, html):
        self.html = html
        self.url = None

    def bind(self, name, handler):
        self.bound_functions[name] = handler

    def __getitem__(self, item):
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    def execute_js(self, js_code):
        return True

    def show(self):
        self.is_open = True
        if self.url:
            print(f"[XWview] Opening '{self.title}' ({self.width}x{self.height}) at {self.url}...")
            try:
                webbrowser.open(self.url)
            except Exception:
                pass
        elif self.html:
            # Create a temporary HTML file and open in browser
            fd, path = tempfile.mkstemp(suffix=".html", prefix="xpp_view_")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(self.html)
            print(f"[XWview] Displaying HTML view in local browser ({path})...")
            try:
                webbrowser.open("file://" + os.path.abspath(path))
            except Exception:
                pass
        return self

    def close(self):
        self.is_open = False
        print(f"[XWview] Closed window '{self.title}'")


def create_window(title="X++ Web View", width=800, height=600, content="", is_url=False):
    win = WebViewWindow(title=title, width=width, height=height)
    if is_url or content.startswith("http://") or content.startswith("https://"):
        win.load_url(content)
    else:
        win.load_html(content)
    return win


def load_html(w, html):
    if hasattr(w, "load_html"):
        w.load_html(html)
    return w


def load_url(w, url):
    if hasattr(w, "load_url"):
        w.load_url(url)
    return w


def inject_js(w, js_code):
    return {"status": "ok", "code": js_code}


def open_browser(url):
    return webbrowser.open(url)


EXPORT = XModule(
    "XWview",
    WebViewWindow=WebViewWindow,
    create_window=create_window,
    open_browser=open_browser,
    load_html=load_html,
    load_url=load_url,
    inject_js=inject_js
)
