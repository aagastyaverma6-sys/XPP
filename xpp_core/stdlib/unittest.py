"""
unittest - Unit Testing Framework for X++
"""

import sys
from . import XModule

class TestCase:
    def __init__(self, name="XppTest"):
        self.name = name
        self.passed = 0
        self.failed = 0
        self.errors = []

    def assert_true(self, condition, msg="Expected true"):
        if condition:
            self.passed += 1
        else:
            self.failed += 1
            self.errors.append(f"FAIL: {msg}")

    def assert_false(self, condition, msg="Expected false"):
        self.assert_true(not condition, msg)

    def assert_eq(self, a, b, msg=None):
        if a == b:
            self.passed += 1
        else:
            self.failed += 1
            self.errors.append(msg or f"FAIL: {a} != {b}")

    def assert_approx(self, a, b, tol=1e-5, msg=None):
        if abs(a - b) <= tol:
            self.passed += 1
        else:
            self.failed += 1
            self.errors.append(msg or f"FAIL: {a} not approx {b} (diff={abs(a-b)})")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n===== Test Suite '{self.name}': {self.passed}/{total} passed =====")
        for err in self.errors:
            print(f"  * {err}", file=sys.stderr)
        return self.failed == 0


def test_case(name="XppTest"):
    return TestCase(name)

def assertEqual(a, b, msg=None):
    if a != b:
        raise AssertionError(msg or f"AssertionError: {a} != {b}")

def assertTrue(cond, msg=None):
    if not cond:
        raise AssertionError(msg or "AssertionError: Condition is not true")

TestSuite = TestCase

EXPORT = XModule(
    "unittest",
    TestCase=TestCase, TestSuite=TestSuite, test_case=test_case,
    assertEqual=assertEqual, assertTrue=assertTrue
)
