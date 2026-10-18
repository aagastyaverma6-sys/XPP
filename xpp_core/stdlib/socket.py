"""
socket - Low-level Networking Interface for X++
"""

import socket as _sock
from . import XModule

AF_INET = _sock.AF_INET
SOCK_STREAM = _sock.SOCK_STREAM
SOCK_DGRAM = _sock.SOCK_DGRAM

def gethostname(): return _sock.gethostname()
def gethostbyname(hostname): return _sock.gethostbyname(hostname)

def create_connection(address, timeout=10):
    return _sock.create_connection(address, timeout=timeout)

def send_message(host, port, message):
    with _sock.socket(_sock.AF_INET, _sock.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(message.encode("utf-8"))
        data = s.recv(4096)
        return data.decode("utf-8", errors="replace")

def socket_fn(family="AF_INET", sock_type="SOCK_STREAM", proto=0):
    return {"family": str(family), "type": str(sock_type), "proto": proto}

EXPORT = XModule(
    "socket",
    socket=socket_fn,
    AF_INET=AF_INET, SOCK_STREAM=SOCK_STREAM, SOCK_DGRAM=SOCK_DGRAM,
    gethostname=gethostname, gethostbyname=gethostbyname,
    create_connection=create_connection, send_message=send_message
)
