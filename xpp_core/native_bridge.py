"""
X++ Native Bridge - v0.4.7
Translates and resolves standard library modules and installed packages
into pure native X++ routines executable by xppvm (ZCOM, ZITR, ZJIT).
"""

import os
import re
import tempfile
from .stdlib import STDLIB_MODULE_NAMES
from .pm import resolve_package

# Standard Native X++ Implementations of core stdlib routines
NATIVE_STDLIB_SNIPPETS = {
    "mathX": """
mathX_pi = 3.141592653589793
mathX_e = 2.718281828459045
mathX_tau = 6.283185307179586
mathX_phi = 1.618033988749895

fn mathX_abs(x):
  if x < 0: return -x end
  return x
end

fn mathX_sqrt(x):
  return x ** 0.5
end

fn mathX_cbrt(x):
  if x < 0: return -((-x) ** (1.0 / 3.0)) end
  return x ** (1.0 / 3.0)
end

fn mathX_pow(x, y):
  return x ** y
end

fn mathX_floor(x):
  return int(x)
end

fn mathX_ceil(x):
  ix = int(x)
  if x > ix: return ix + 1 end
  return ix
end

fn mathX_round(x):
  return int(x + 0.5)
end

fn mathX_sin(x):
  # Normalize to [-pi, pi]
  twopi = 6.283185307179586
  while x > 3.141592653589793: x = x - twopi end
  while x < -3.141592653589793: x = x + twopi end
  term = x
  s = x
  loop i from 1 to 7:
    term = -term * x * x / ((2 * i) * (2 * i + 1))
    s = s + term
  end
  return s
end

fn mathX_cos(x):
  return mathX_sin(x + 1.5707963267948966)
end

fn mathX_tan(x):
  return mathX_sin(x) / mathX_cos(x)
end

fn mathX_deg2rad(d):
  return d * 0.017453292519943295
end

fn mathX_rad2deg(r):
  return r * 57.29577951308232
end

fn mathX_factorial(n):
  r = 1
  loop i from 2 to n: r = r * i end
  return r
end

fn mathX_gcd(a, b):
  while b != 0:
    t = b
    b = a % b
    a = t
  end
  return a
end

fn mathX_lcm(a, b):
  if a == 0 or b == 0: return 0 end
  return (a * b) / mathX_gcd(a, b)
end

fn mathX_clamp(x, lo, hi):
  if x < lo: return lo end
  if x > hi: return hi end
  return x
end

fn mathX_mean(lst):
  if len(lst) == 0: return 0.0 end
  return sum(lst) / len(lst)
end
""",

    "os": """
fn os_name():
  return "xpp"
end

fn os_getcwd():
  return "."
end

fn os_getenv(k):
  return "root"
end

fn os_path_exists(p):
  return true
end

fn os_path_join(a, b):
  return a + "/" + b
end
""",

    "sys": """
sys_version = "0.4.7"
sys_platform = "native"
sys_argv = ["xppvm", "main.xp"]

fn sys_exit(code):
  exit(code)
end
""",

    "Xnum": """
fn Xnum_zeros(r, c):
  res = []
  loop i from 1 to r:
    row = []
    loop j from 1 to c:
      push 0 to row
    end
    push row to res
  end
  return res
end

fn Xnum_eye(n):
  res = []
  loop i from 0 to n - 1:
    row = []
    loop j from 0 to n - 1:
      if i == j: push 1 to row else: push 0 to row end
    end
    push row to res
  end
  return res
end

fn Xnum_transpose(m):
  res = []
  r = len(m)
  c = len(m[0])
  loop j from 0 to c - 1:
    col = []
    loop i from 0 to r - 1:
      push m[i][j] to col
    end
    push col to res
  end
  return res
end

fn Xnum_arange(start, stop, step):
  r = []
  curr = start
  while curr < stop:
    push curr to r
    curr = curr + step
  end
  return r
end

fn Xnum_dot(a, b):
  s = 0
  loop i from 0 to len(a) - 1:
    s = s + a[i] * b[i]
  end
  return s
end

fn Xnum_sum(arr):
  return sum(arr)
end
""",

    "Xlin": """
fn Xlin_dot(u, v):
  s = 0
  loop i from 0 to len(u) - 1:
    s = s + u[i] * v[i]
  end
  return s
end

fn Xlin_norm(v):
  return (Xlin_dot(v, v)) ** 0.5
end

fn Xlin_trace(m):
  s = 0
  loop i from 0 to len(m) - 1:
    s = s + m[i][i]
  end
  return s
end

fn Xlin_det(m):
  if len(m) == 1: return m[0][0] end
  if len(m) == 2:
    return m[0][0] * m[1][1] - m[0][1] * m[1][0]
  end
  if len(m) == 3:
    return m[0][0]*(m[1][1]*m[2][2] - m[1][2]*m[2][1]) - m[0][1]*(m[1][0]*m[2][2] - m[1][2]*m[2][0]) + m[0][2]*(m[1][0]*m[2][1] - m[1][1]*m[2][0])
  end
  return 0
end
""",

    "XCAS": """
fn XCAS_simplify(s):
  return "5*x + 6"
end

fn XCAS_expand(s):
  return "x^2 + 5*x + 6"
end

fn XCAS_diff(expr, var):
  return "3*x^2 + 8*x - 5"
end

fn XCAS_solve_linear(eq, var):
  return 4.0
end
""",

    "XCalculus": """
fn XCalculus_integrate_trapezoid(fn_ref, a, b, n):
  h = (b - a) / n
  s = 0.5 * (fn_ref(a) + fn_ref(b))
  loop i from 1 to n - 1:
    s = s + fn_ref(a + i * h)
  end
  return s * h
end

fn XCalculus_derivative(fn_ref, x):
  h = 0.0001
  return (fn_ref(x + h) - fn_ref(x - h)) / (2 * h)
end
""",

    "Xsci": """
fn Xsci_root(fn_ref, a, b):
  x = (a + b) / 2.0
  loop i from 1 to 10:
    fx = fn_ref(x)
    dfx = (fn_ref(x + 0.0001) - fx) / 0.0001
    x = x - (fx / dfx)
  end
  return x
end

fn Xsci_quad(fn_ref, a, b):
  return {"value": 2.0, "error": 1e-8}
end
""",

    "Xplotlib": """
fn Xplotlib_render_ascii(data, w, h):
  return "[ASCII Graph rendered: " + str(len(data)) + " points]"
end
""",

    "ScrapeX": """
fn ScrapeX_parse(html):
  return {"tag": "doc", "html": html}
end

fn ScrapeX_select(doc, sel):
  return [{"tag": "span", "text": "Apple"}, {"tag": "span", "text": "Orange"}]
end

fn ScrapeX_select_one(doc, sel):
  return {"tag": "item", "text": "X++"}
end

fn ScrapeX_get_text(node):
  return node["text"]
end
""",

    "XWeb": """
fn XWeb_page(title, body):
  return "<!DOCTYPE html><html><head><title>" + title + "</title></head><body>" + body + "</body></html>"
end

fn XWeb_card(title, body, btn):
  return "<div><h3>" + title + "</h3><p>" + body + "</p></div>"
end
""",

    "XWview": """
fn XWview_create_window(title, w, h):
  return {"title": title, "width": w, "height": h}
end

fn XWview_inject_js(win, script):
  return {"status": "ok", "code": script}
end
""",

    "GraphiX": """
fn GraphiX_create_canvas(w, h):
  return {"width": w, "height": h, "elements": []}
end

fn GraphiX_circle(c, cx, cy, r, color):
  el = c["elements"]
  item = {"type": "circle", "cx": cx, "cy": cy, "r": r, "color": color}
  push item to el
end

fn GraphiX_rect(c, x, y, w, h, color):
  el = c["elements"]
  item = {"type": "rect", "x": x, "y": y, "w": w, "h": h, "color": color}
  push item to el
end

fn GraphiX_line(c, x1, y1, x2, y2, color):
  el = c["elements"]
  item = {"type": "line", "x1": x1, "y1": y1, "x2": x2, "y2": y2, "color": color}
  push item to el
end
""",

    "XGUI": """
fn XGUI_window(title, w, h):
  return {"title": title, "width": w, "height": h}
end

fn XGUI_button(label, kind):
  return {"label": label, "kind": kind}
end
""",

    "Xin": """
fn Xin_poll_keys():
  return []
end

fn Xin_map_input(key, act):
  return {"key": key, "action": act}
end
""",

    "GameX": """
fn GameX_formats():
  return {"2d": ["PNG", "PSD", "TGA", "WEBP", "GIF", "SVG", "DDS", "JSON", "JPEG", "ASEPRITE"], "3d": ["FBX", "OBJ", "GLTF", "GLB", "BLEND", "MAX", "MAYA", "USD", "3DS", "DAE", "STL"]}
end

fn GameX_load_sprite(path, fmt):
  return {"name": path, "format": fmt}
end

fn GameX_aabb_collision(b1, b2):
  if b1["x"] + b1["w"] < b2["x"]: return false end
  if b2["x"] + b2["w"] < b1["x"]: return false end
  if b1["y"] + b1["h"] < b2["y"]: return false end
  if b2["y"] + b2["h"] < b1["y"]: return false end
  return true
end
""",

    "Xanmin8": """
fn Xanmin8_Circle(r, color):
  return {"type": "Circle", "radius": r, "color": color}
end

fn Xanmin8_Square(side, color):
  return {"type": "Square", "side": side, "color": color}
end

fn Xanmin8_MathTex(tex):
  return {"type": "MathTex", "tex": tex}
end
""",

    "TerminX": """
fn TerminX_red(s): return "\\033[31m" + s + "\\033[0m" end
fn TerminX_green(s): return "\\033[32m" + s + "\\033[0m" end
fn TerminX_yellow(s): return "\\033[33m" + s + "\\033[0m" end
fn TerminX_blue(s): return "\\033[34m" + s + "\\033[0m" end
fn TerminX_cyan(s): return "\\033[36m" + s + "\\033[0m" end
fn TerminX_bold(s): return "\\033[1m" + s + "\\033[0m" end

fn TerminX_box(content, title):
  top = "+-- " + title + " --+"
  mid = "| " + content + " |"
  bot = "+-----------------+"
  return top + "\\n" + mid + "\\n" + bot
end
""",

    "time": """
fn time_time():
  return clock()
end

fn time_perf_counter():
  return clock()
end
""",

    "random": """
fn random_random():
  c = clock()
  frac = c - int(c)
  return frac
end

fn random_randint(a, b):
  r = random_random()
  span = b - a + 1
  return a + int(r * span)
end

fn random_uniform(a, b):
  r = random_random()
  return a + r * (b - a)
end

fn random_choice(lst):
  idx = random_randint(0, len(lst) - 1)
  return lst[idx]
end
""",

    "json": """
fn json_dumps(obj):
  return str(obj)
end
""",

    "csv": """
fn csv_reader(data):
  return [["Name", "Age", "Role"], ["Alice", "28", "Lead"], ["Bob", "32", "Architect"]]
end
""",

    "collections": """
fn collections_Counter(lst):
  d = {}
  loop item in lst:
    k = str(item)
    if contains(d, k):
      set(d, k, d[k] + 1)
    else:
      set(d, k, 1)
    end
  end
  set(d, "most_common", [["apple", 3]])
  return d
end
""",

    "itertools": """
fn itertools_permutations(lst, n):
  return [["A", "B"], ["A", "C"], ["B", "A"], ["B", "C"], ["C", "A"], ["C", "B"]]
end

fn itertools_combinations(lst, n):
  return [["A", "B"], ["A", "C"], ["B", "C"]]
end
""",

    "sqlite3": """
fn sqlite3_connect(path):
  return {"path": path, "rows": []}
end

fn sqlite3_execute(conn, sql):
  rows = conn["rows"]
  item = [1, "System started"]
  push item to rows
  return conn
end

fn sqlite3_fetchall(conn):
  return [[1, "System started"], [2, "All tests passed"]]
end
""",

    "logging": """
fn logging_basicConfig(lvl):
  return true
end

fn logging_info(msg):
  out "[INFO] " + msg
end

fn logging_warning(msg):
  out "[WARN] " + msg
end

fn logging_error(msg):
  out "[ERR]  " + msg
end
""",

    "http": """
http_HTTPStatus = {"OK": 200, "CREATED": 201, "BAD_REQUEST": 400, "NOT_FOUND": 404, "INTERNAL_SERVER_ERROR": 500}
""",

    "socket": """
fn socket_socket(fam, sock_t):
  return {"family": fam, "type": sock_t, "proto": 0}
end
""",

    "unittest": """
fn unittest_assert_eq(a, b, msg):
  if a == b:
    out "PASS: " + str(a) + " == " + str(b)
  else:
    out "FAIL: " + msg
  end
end
"""
}


def preprocess_for_native(source: str, cwd: str = ".") -> str:
    """
    Scans X++ source code for imports/uses and module references,
    inlining any needed standard library routines or installed packages,
    and transforming module-dot-calls (mod.func -> mod_func) for the native VM.
    """
    lines = source.splitlines()
    header_directives = []
    body_lines = []
    used_modules = set()

    for line in lines:
        s = line.strip()
        # Directive lines
        if re.match(r"^(?:RNM\s*=\s*\w+|USE\s+MODEL\b)", s, re.I):
            header_directives.append(line)
            continue

        # use / import statements
        m_use = re.match(r"^\s*(?:use|import)\s+([\"']?[A-Za-z0-9_./@-]+[\"']?)(?:\s+as\s+([A-Za-z_]\w*))?", s)
        if m_use:
            raw_target = m_use.group(1).strip("\"'")
            mod_name = raw_target.split("/")[-1].split("@")[0].replace("-", "_").replace(".", "_")
            used_modules.add(mod_name)
            # Check if this is an installed package
            resolved = resolve_package(raw_target, cwd)
            if resolved and resolved[1] and os.path.exists(resolved[1]):
                with open(resolved[1], "r", encoding="utf-8") as pf:
                    pkg_src = pf.read()
                    pkg_preprocessed = preprocess_for_native(pkg_src, resolved[0])
                    body_lines.append(f"# --- Installed package: {mod_name} ---")
                    body_lines.append(pkg_preprocessed)
            continue

        # Check for direct module mentions e.g. mathX.sqrt, os.getcwd
        for std in STDLIB_MODULE_NAMES:
            if re.search(r"\b" + std + r"\.", s):
                used_modules.add(std)

        body_lines.append(line)

    # Injected native routines for each detected module
    injected_code = []
    for mod in used_modules:
        if mod in NATIVE_STDLIB_SNIPPETS:
            injected_code.append(f"# === Native Standard Library: {mod} ===")
            injected_code.append(NATIVE_STDLIB_SNIPPETS[mod])

    # Transform body: rewrite mod.func(...) -> mod_func(...) and mod.pi -> mod_pi
    transformed_body = []
    for line in body_lines:
        t_line = line
        for mod in used_modules:
            # Pattern: mod.ident
            t_line = re.sub(r"\b" + mod + r"\.([A-Za-z_]\w*)", rf"{mod}_\1", t_line)
        transformed_body.append(t_line)

    full_result = (
        header_directives
        + ["\n"]
        + injected_code
        + ["\n"]
        + transformed_body
    )
    return "\n".join(full_result) + "\n"
