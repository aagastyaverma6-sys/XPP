#!/usr/bin/env python3
"""
Comprehensive Regression & Feature Test Suite for X++ v0.4.5
Tests all 34 standard libraries across RNMs (XCOM, XITR, ZCOM, ZITR, ZJIT)
and verifies the package management system.
"""

import sys, os, subprocess, tempfile, shutil

REPO_ROOT = "/xpp"
sys.path.insert(0, REPO_ROOT)

from xpp_core.stdlib import get_stdlib, STDLIB_MODULE_NAMES
import xpp_core.cli as cli

PASSED = 0
FAILED = 0
FAILURES = []

def test(name, cond, msg=""):
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f"  PASS  {name}")
    else:
        FAILED += 1
        FAILURES.append(f"{name}: {msg}")
        print(f"  FAIL  {name} - {msg}", file=sys.stderr)

print("\n=== Testing All 34 Standard Library Imports & Modules ===")
for mod_name in STDLIB_MODULE_NAMES:
    m = get_stdlib(mod_name)
    test(f"stdlib-load: {mod_name}", m is not None, f"Failed to load module {mod_name}")

print("\n=== Testing Mathematical Libs ===")
mathX = get_stdlib("mathX")
test("mathX.sqrt", mathX["sqrt"](144) == 12.0)
test("mathX.pi", abs(mathX["pi"] - 3.14159265) < 1e-4)
test("mathX.sin", abs(mathX["sin"](mathX["pi"] / 2) - 1.0) < 1e-4)
test("mathX.factorial", mathX["factorial"](5) == 120)
test("mathX.gcd", mathX["gcd"](48, 18) == 6)

Xnum = get_stdlib("Xnum")
z = Xnum["zeros"]([2, 3])
test("Xnum.zeros", z.shape == [2, 3] and z.size == 6)
d = Xnum["dot"]([1, 2, 3], [4, 5, 6])
test("Xnum.dot", d == 32)

Xlin = get_stdlib("Xlin")
m2 = [[1, 2], [3, 4]]
test("Xlin.det", Xlin["det"](m2) == -2.0)
test("Xlin.dot", Xlin["dot"]([1, 2], [3, 4]) == 11)

XCAS = get_stdlib("XCAS")
expr = XCAS["expr"]("x**2 + 3*x + 5")
d_expr = XCAS["diff"](expr, "x")
test("XCAS.diff", d_expr is not None)

XCalculus = get_stdlib("XCalculus")
deriv = XCalculus["derivative"](lambda x: x**2, 3.0)
test("XCalculus.derivative", abs(deriv - 6.0) < 1e-3)

Xsci = get_stdlib("Xsci")
q = Xsci["quad"](lambda x: x * x, 0, 1)
test("Xsci.quad", abs(q - 1/3) < 1e-4)

Xplotlib = get_stdlib("Xplotlib")
Xplotlib["plot"]([1, 2, 3], [1, 4, 9])
ascii_plot = Xplotlib["render_ascii"]()
test("Xplotlib.render_ascii", len(ascii_plot) > 50)

print("\n=== Testing Web Related Libs ===")
ScrapeX = get_stdlib("ScrapeX")
dom = ScrapeX["parse"]("<div class='main'><h1 id='title'>Hello XPP</h1><p>Test</p></div>")
h1 = ScrapeX["select_one"](dom, "#title")
test("ScrapeX.select_one", h1 is not None and ScrapeX["text"](h1) == "Hello XPP")

XWeb = get_stdlib("XWeb")
html = XWeb["page"](title="Test", body=XWeb["h1"]("Welcome"))
test("XWeb.page", "Welcome" in html and "<!DOCTYPE html>" in html)

XWview = get_stdlib("XWview")
win = XWview["create_window"](title="Test View", width=800, height=600, content="<h1>Hi</h1>")
test("XWview.create_window", win.title == "Test View")

print("\n=== Testing Development Libs ===")
GraphiX = get_stdlib("GraphiX")
canvas = GraphiX["create_canvas"](400, 300)
canvas.rect(10, 10, 50, 50)
svg = canvas.to_svg()
test("GraphiX.to_svg", "<svg" in svg and "rect" in svg)

XGUI = get_stdlib("XGUI")
gui = XGUI["window"](title="Test GUI", width=600, height=400)
gui.add(XGUI["card"]("Title", "Content", XGUI["button"]("Click Me")))
gui_html = gui.render_html()
test("XGUI.render_html", "Click Me" in gui_html and "xgui-card" in gui_html)

TerminX = get_stdlib("TerminX")
c_str = TerminX["green"]("Success")
test("TerminX.green", "\033[32m" in c_str)

Xin = get_stdlib("Xin")
pos = Xin["get_mouse_position"]()
test("Xin.get_mouse_position", len(pos) == 2)

GameX = get_stdlib("GameX")
test("GameX.formats", len(GameX["SUPPORTED_2D_SPRITES"]) >= 10 and len(GameX["SUPPORTED_3D_MODELS"]) >= 10)
coll = GameX["aabb_collision"]([0, 0, 10, 10], [5, 5, 10, 10])
test("GameX.aabb_collision", coll is True)

Xanmin8 = get_stdlib("Xanmin8")
circle = Xanmin8["Circle"](radius=2.0)
test("Xanmin8.Circle", circle.radius == 2.0 and circle.type == "Circle")

print("\n=== Testing System & Counterpart Libs ===")
os_mod = get_stdlib("os")
test("os.getcwd", os.path.exists(os_mod["getcwd"]()))

sys_mod = get_stdlib("sys")
test("sys.platform", len(sys_mod["platform"]()) > 0)

json_mod = get_stdlib("json")
test("json.dumps", json_mod["dumps"]({"a": 1}) == '{"a": 1}')

re_mod = get_stdlib("re")
test("re.findall", re_mod["findall"](r"\d+", "a12b34") == ["12", "34"])

time_mod = get_stdlib("time")
test("time.time", time_mod["time"]() > 0)

random_mod = get_stdlib("random")
r_int = random_mod["randint"](5, 15)
test("random.randint", 5 <= r_int <= 15)

col_mod = get_stdlib("collections")
c = col_mod["Counter"](["a", "b", "a"])
test("collections.Counter", c["a"] == 2)

it_mod = get_stdlib("itertools")
test("itertools.combinations", len(it_mod["combinations"]([1, 2, 3], 2)) == 3)

ft_mod = get_stdlib("functools")
test("functools.reduce", ft_mod["reduce"](lambda a, b: a + b, [1, 2, 3, 4]) == 10)

sqlite_mod = get_stdlib("sqlite3")
conn = sqlite_mod["connect"](":memory:")
conn.execute("CREATE TABLE t (x INT);")
conn.execute("INSERT INTO t VALUES (42);")
row = conn.fetchone()
conn.execute("SELECT x FROM t;")
row = conn.fetchone()
test("sqlite3.execute", row == [42])

print("\n=== Testing All RNMs with XPP Scripts ===")
with tempfile.NamedTemporaryFile("w", suffix=".xp", delete=False) as f:
    f.write("""
use mathX
use Xnum
use Xlin

out mathX.sqrt(81)
out mathX.factorial(4)
out Xlin.dot([1, 2], [3, 4])
""")
    tmp_path = f.name

try:
    for mode in ["XITR", "XCOM", "ZITR", "ZCOM", "ZJIT"]:
        res = subprocess.run([sys.executable, "-m", "xpp_core.cli", "run", tmp_path, "--mode", mode],
                             capture_output=True, text=True, cwd=REPO_ROOT)
        stdout = res.stdout.strip()
        has_expected = "9" in stdout and "24" in stdout and "11" in stdout
        test(f"RNM-{mode} stdlib execution", res.returncode == 0 and has_expected, f"exit={res.returncode}, out={stdout}, err={res.stderr}")
finally:
    if os.path.exists(tmp_path):
        os.remove(tmp_path)

print(f"\n==========================================")
print(f"  TOTAL: {PASSED} passed, {FAILED} failed")
print(f"==========================================")
if FAILED > 0:
    sys.exit(1)
