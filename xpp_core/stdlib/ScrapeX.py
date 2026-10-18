"""
ScrapeX - High-Performance Web Scraping Module for X++
Fetches web resources, parses DOM structures, extracts tables/links/forms,
and selects nodes using modern CSS selectors.
"""

import urllib.request
import urllib.parse
import re
from html.parser import HTMLParser
from . import XModule

class DOMNode:
    """Represents an HTML DOM element node."""
    def __init__(self, tag, attrs=None, text=""):
        self.tag = tag.lower()
        self.attrs = attrs or {}
        self.text_content = text
        self.children = []
        self.parent = None

    def add_child(self, child):
        child.parent = self
        self.children.append(child)

    @property
    def id(self):
        return self.attrs.get("id", "")

    @property
    def classes(self):
        return self.attrs.get("class", "").split()

    def get_text(self):
        parts = [self.text_content]
        for c in self.children:
            parts.append(c.get_text())
        return " ".join("".join(parts).split())

    def __getitem__(self, item):
        if hasattr(self, item):
            return getattr(self, item)
        if item in self.attrs:
            return self.attrs[item]
        raise KeyError(item)

    def __repr__(self):
        return f"<{self.tag} id='{self.id}' class='{' '.join(self.classes)}'>{self.text_content[:20]}</{self.tag}>"


class _DOMBuilder(HTMLParser):
    def __init__(self):
        super().__init__()
        self.root = DOMNode("root")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        node = DOMNode(tag, attr_dict)
        self.stack[-1].add_child(node)
        if tag not in ("br", "hr", "img", "input", "meta", "link"):
            self.stack.append(node)

    def handle_endtag(self, tag):
        if len(self.stack) > 1 and self.stack[-1].tag == tag.lower():
            self.stack.pop()

    def handle_data(self, data):
        if self.stack:
            self.stack[-1].text_content += data


# ------------------------------------------------------------- Network Fetch
def fetch(url, headers=None, timeout=20):
    headers = headers or {"User-Agent": "Mozilla/5.0 (compatible; ScrapeX/0.4.5)"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")

def get(url, params=None, headers=None):
    if params:
        url += ("?" if "?" not in url else "&") + urllib.parse.urlencode(params)
    return fetch(url, headers=headers)

def post(url, data=None, headers=None):
    headers = headers or {"User-Agent": "Mozilla/5.0 (compatible; ScrapeX/0.4.5)"}
    encoded = urllib.parse.urlencode(data).encode("utf-8") if isinstance(data, dict) else (data.encode("utf-8") if data else b"")
    req = urllib.request.Request(url, data=encoded, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8", errors="replace")


# ---------------------------------------------------------------- DOM Parsing
def parse(html_str):
    builder = _DOMBuilder()
    builder.feed(html_str)
    return builder.root


def _matches_selector(node: DOMNode, sel: str) -> bool:
    sel = sel.strip()
    if not sel or node.tag == "root":
        return False
    # ID: #my-id
    if sel.startswith("#"):
        return node.id == sel[1:]
    # Class: .my-class
    if sel.startswith("."):
        return sel[1:] in node.classes
    # Tag: div, h1, a
    if re.match(r"^[A-Za-z0-9_-]+$", sel):
        return node.tag == sel.lower()
    # Attribute: [attr=val]
    m = re.match(r"^\[([A-Za-z0-9_-]+)=['\"]?(.*?)['\"]?\]$", sel)
    if m:
        attr, val = m.groups()
        return node.attrs.get(attr) == val
    return False


def _collect_all(node: DOMNode):
    res = [node]
    for c in node.children:
        res.extend(_collect_all(c))
    return res


def select(dom: DOMNode, selector: str):
    """Selects elements matching a CSS selector."""
    all_nodes = _collect_all(dom)
    return [n for n in all_nodes if _matches_selector(n, selector)]


def select_one(dom: DOMNode, selector: str):
    nodes = select(dom, selector)
    return nodes[0] if nodes else None


def text(node: DOMNode):
    return node.get_text() if node else ""

def attr(node: DOMNode, name: str):
    return node.attrs.get(name, "") if node else ""

def attrs(node: DOMNode):
    return dict(node.attrs) if node else {}


# -------------------------------------------------------- High-Level Helpers
def extract_links(html_or_dom, base_url=""):
    dom = parse(html_or_dom) if isinstance(html_or_dom, str) else html_or_dom
    links = []
    for a in select(dom, "a"):
        href = a.attrs.get("href", "")
        if href:
            full = urllib.parse.urljoin(base_url, href) if base_url else href
            links.append({"href": full, "text": a.get_text()})
    return links


def extract_tables(html_or_dom):
    dom = parse(html_or_dom) if isinstance(html_or_dom, str) else html_or_dom
    tables = []
    for t in select(dom, "table"):
        rows = []
        for tr in select(t, "tr"):
            cells = [c.get_text() for c in tr.children if c.tag in ("td", "th")]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    return tables


def extract_images(html_or_dom, base_url=""):
    dom = parse(html_or_dom) if isinstance(html_or_dom, str) else html_or_dom
    images = []
    for img in select(dom, "img"):
        src = img.attrs.get("src", "")
        if src:
            full = urllib.parse.urljoin(base_url, src) if base_url else src
            images.append({"src": full, "alt": img.attrs.get("alt", "")})
    return images


def extract_table(html_or_dom):
    tables = extract_tables(html_or_dom)
    if tables:
        t = tables[0]
        headers = t[0] if t else []
        rows = t[1:] if len(t) > 1 else []
        return {"headers": headers, "rows": rows}
    return {"headers": [], "rows": []}

get_text = text

EXPORT = XModule(
    "ScrapeX",
    DOMNode=DOMNode,
    fetch=fetch, get=get, post=post, parse=parse,
    select=select, select_one=select_one, text=text, get_text=get_text, attr=attr, attrs=attrs,
    extract_links=extract_links, extract_tables=extract_tables, extract_table=extract_table, extract_images=extract_images
)
