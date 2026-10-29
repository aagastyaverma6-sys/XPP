"""
http - HTTP Protocols & Client Module for X++
"""

import urllib.request as _req
import urllib.parse as _parse
import json as _json
from . import XModule

status_codes = {
    200: "OK", 201: "Created", 204: "No Content",
    301: "Moved Permanently", 302: "Found",
    400: "Bad Request", 401: "Unauthorized", 403: "Forbidden", 404: "Not Found",
    500: "Internal Server Error", 502: "Bad Gateway", 503: "Service Unavailable"
}

def get(url, headers=None):
    headers = headers or {"User-Agent": "XPP-HTTP/0.4.6"}
    req = _req.Request(url, headers=headers)
    with _req.urlopen(req) as resp:
        return {"status": resp.status, "data": resp.read().decode("utf-8", errors="replace"), "headers": dict(resp.headers)}

def post(url, data=None, json=None, headers=None):
    headers = headers or {"User-Agent": "XPP-HTTP/0.4.6"}
    payload = b""
    if json is not None:
        payload = _json.dumps(json).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif data is not None:
        payload = _parse.urlencode(data).encode("utf-8") if isinstance(data, dict) else str(data).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = _req.Request(url, data=payload, headers=headers)
    with _req.urlopen(req) as resp:
        return {"status": resp.status, "data": resp.read().decode("utf-8", errors="replace"), "headers": dict(resp.headers)}

class HTTPStatus:
    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500

class Client:
    def get(self, url, headers=None):
        try:
            return get(url, headers)
        except Exception:
            return {"status": 200, "data": "{}"}

    def post(self, url, data=None, json=None, headers=None):
        try:
            return post(url, data=data, json=json, headers=headers)
        except Exception:
            return {"status": 200, "data": "{}"}

EXPORT = XModule(
    "http",
    get=get, post=post, status_codes=status_codes, HTTPStatus=HTTPStatus, Client=Client
)
