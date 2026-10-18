"""
urllib - URL Handling Modules for X++
"""

import urllib.parse as _parse
import urllib.request as _req
from . import XModule

def quote(s): return _parse.quote(str(s))
def unquote(s): return _parse.unquote(str(s))
def urlencode(d): return _parse.urlencode(d)
def urljoin(base, url): return _parse.urljoin(base, url)
def urlparse(url):
    p = _parse.urlparse(url)
    return {"scheme": p.scheme, "netloc": p.netloc, "path": p.path, "query": p.query, "fragment": p.fragment}
def urlopen(url):
    with _req.urlopen(url) as resp:
        return resp.read().decode("utf-8", errors="replace")

EXPORT = XModule(
    "urllib",
    quote=quote, unquote=unquote, urlencode=urlencode,
    urljoin=urljoin, urlparse=urlparse, urlopen=urlopen
)
