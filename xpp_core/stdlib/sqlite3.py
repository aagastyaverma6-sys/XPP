"""
sqlite3 - DB-API 2.0 Interface for SQLite Databases in X++
"""

import sqlite3 as _sqlite
from . import XModule

class Connection:
    def __init__(self, database_path):
        self._conn = _sqlite.connect(database_path)
        self._cursor = self._conn.cursor()

    def execute(self, sql, params=None):
        if params is None:
            self._cursor.execute(sql)
        else:
            self._cursor.execute(sql, params)
        return self

    def executemany(self, sql, seq_of_params):
        self._cursor.executemany(sql, seq_of_params)
        return self

    def fetchone(self):
        row = self._cursor.fetchone()
        return list(row) if row else None

    def fetchall(self):
        return [list(row) for row in self._cursor.fetchall()]

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

def connect(database_path=":memory:"):
    return Connection(database_path)

def execute(conn_or_cur, sql, params=None):
    if hasattr(conn_or_cur, "execute"):
        return conn_or_cur.execute(sql, params)
    return None

def fetchall(conn_or_cur):
    if hasattr(conn_or_cur, "fetchall"):
        return conn_or_cur.fetchall()
    return []

EXPORT = XModule(
    "sqlite3",
    connect=connect, Connection=Connection, execute=execute, fetchall=fetchall
)
