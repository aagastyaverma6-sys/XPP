"""
csv - CSV File Reading and Writing Module for X++
"""

import csv as _csv
import io as _io
from . import XModule

def reader(csv_str_or_path, delimiter=","):
    """Reads CSV content from file path or raw string."""
    if "\n" not in csv_str_or_path and _csv.os.path.exists(csv_str_or_path):
        with open(csv_str_or_path, "r", encoding="utf-8", errors="replace") as f:
            return list(_csv.reader(f, delimiter=delimiter))
    return list(_csv.reader(_io.StringIO(csv_str_or_path), delimiter=delimiter))

def writer(rows, delimiter=","):
    output = _io.StringIO()
    w = _csv.writer(output, delimiter=delimiter)
    for r in rows:
        w.writerow(r)
    return output.getvalue()

def write_file(filepath, rows, delimiter=","):
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        w = _csv.writer(f, delimiter=delimiter)
        for r in rows:
            w.writerow(r)

EXPORT = XModule(
    "csv",
    reader=reader, writer=writer, write_file=write_file
)
