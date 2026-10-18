#!/usr/bin/env python3
"""
X++ v0.4.5 CLI
  RNM=ZCOM / RNM=ZITR / RNM=ZJIT  -> native VM (xppvm), no Python at runtime
  RNM=XCOM / RNM=XITR              -> Python fast paths (kept)
  RNM=ITR                          -> AI intent compiler (LLM via OpenRouter)

Package Management:
  x install github.com/<owner>/<repo>
  x install                         # install all in xpp.json
  x remove <package>
  x list
  x update [package]
  x init [name]

Usage:
  x run file.xp            # auto: native ZITR if xppvm is built, else XITR
  x run file.xp --mode ZJIT
  x compile file.xp --emit-xbc app.xbc
"""
import sys, os, argparse, time, re, shutil, subprocess, tempfile

from . import (
    __version__,
    RNM_XCOM, RNM_XITR, RNM_ITR, RNM_AI,
    RNM_ZCOM, RNM_ZITR, RNM_ZJIT,
)
from .strict_compiler import xcom_compile, run_xcom
from .strict_vm import xitr_run, cache_info
from .fast_transpiler import transpile as fast_transpile
from .env import make_xpp_env
from .native_bridge import preprocess_for_native
from .pm import (
    install_package, install_all, remove_package,
    list_packages, update_package, init_project
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------- native VM
def native_binary():
    """Locate xppvm (repo root, env XPPVM, or PATH)."""
    cands = [
        os.environ.get("XPPVM"),
        os.path.join(REPO_ROOT, "xppvm"),
        os.path.join(REPO_ROOT, "build", "xppvm.exe"),
        os.path.join(REPO_ROOT, "xppvm.exe"),
        shutil.which("xppvm"),
    ]
    for c in cands:
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None


def build_native(verbose=False):
    """Build xppvm on first use so `x run` always just works."""
    if verbose:
        print("[Z] no xppvm found – building native VM...", file=sys.stderr)
    try:
        if os.name == "nt":
            subprocess.run(
                [os.path.join(REPO_ROOT, "build_xppvm.bat")],
                cwd=REPO_ROOT, shell=True, check=True,
                stdout=subprocess.DEVNULL if not verbose else None,
                stderr=subprocess.DEVNULL if not verbose else None,
            )
            return os.path.join(REPO_ROOT, "build", "xppvm.exe")
        subprocess.run(["make", "-C", os.path.join(REPO_ROOT, "native")],
                       check=True,
                       stdout=subprocess.DEVNULL if not verbose else None,
                       stderr=subprocess.DEVNULL if not verbose else None)
        return os.path.join(REPO_ROOT, "xppvm")
    except Exception as e:
        if verbose:
            print(f"Error: could not build xppvm ({e}).\n"
                  "Install g++/clang (or MinGW on Windows) and run: make -C native",
                  file=sys.stderr)
        return None


def run_native(args, cmd, file):
    """Run a native subcommand; returns exit code or None if unavailable."""
    exe = native_binary() or build_native(verbose=getattr(args, "verbose", False))
    if not exe:
        return None

    # Preprocess file for standard libraries and packages if it's a source file
    actual_file = file
    temp_created = None
    if file and os.path.exists(file) and file.endswith(".xp"):
        try:
            with open(file, "r", encoding="utf-8") as sf:
                src_content = sf.read()
            processed_src = preprocess_for_native(src_content, os.path.dirname(os.path.abspath(file)))
            if processed_src != src_content:
                fd, temp_path = tempfile.mkstemp(suffix=".xp", prefix="xpp_native_")
                with os.fdopen(fd, "w", encoding="utf-8") as tf:
                    tf.write(processed_src)
                actual_file = temp_path
                temp_created = temp_path
        except Exception:
            actual_file = file

    try:
        argv = [exe, cmd, actual_file]
        if getattr(args, "verbose", False):
            argv.append("-v")
        if getattr(args, "disasm", False) and cmd == "zcom":
            argv.append("--disasm")
        if getattr(args, "emit_xbc", None) and cmd == "zcom":
            argv.extend(["-o", args.emit_xbc])
        env = os.environ.copy()
        env["PYTHONPATH"] = REPO_ROOT + os.pathsep + env.get("PYTHONPATH", "")
        env["XPP_NATIVE_DIR"] = os.path.join(REPO_ROOT, "native")
        t0 = time.perf_counter()
        rc = subprocess.run(argv, env=env).returncode
        if (getattr(args, "verbose", False) or getattr(args, "bench", False)) and rc == 0:
            dt = (time.perf_counter() - t0) * 1000
            print(f"[{cmd}] total {dt:.2f} ms", file=sys.stderr)
        return rc
    finally:
        if temp_created and os.path.exists(temp_created):
            try:
                os.remove(temp_created)
            except Exception:
                pass


# ------------------------------------------------------------- mode detect
def detect_mode(src_head: str, default=None):
    for line in src_head.splitlines()[:30]:
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = re.match(r"RNM\s*=\s*([A-Za-z_]+)", s, re.I)
        if m:
            return m.group(1).upper()
        if s.startswith("USE MODEL"):
            continue
        break
    return default or (RNM_ZITR if native_binary() else RNM_XITR)


def strip_header_directives(src: str):
    lines = src.splitlines(True)
    out = []
    skipped_rnm = False
    for l in lines:
        s = l.strip()
        if not skipped_rnm and re.match(r"RNM\s*=\s*\w+", s, re.I):
            skipped_rnm = True
            continue
        if s.startswith("USE MODEL"):
            continue
        out.append(l)
    return "".join(out)


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(
        prog="x",
        description=f"X++ v{__version__} – strict pseudocode compiler + native VM + package manager + AI",
    )
    ap.add_argument("cmd", nargs="?", default="run",
                    help="run | compile | install | remove | list | update | init | disasm | transpile | check | version")
    ap.add_argument("file", nargs="?")
    ap.add_argument("--mode", "-m",
                    choices=[RNM_ZCOM, RNM_ZITR, RNM_ZJIT,
                             RNM_XCOM, RNM_XITR, RNM_ITR, RNM_AI])
    ap.add_argument("--global", "-g", dest="global_pkg", action="store_true",
                    help="Install/manage package globally (~/.xpp/packages)")
    ap.add_argument("--strict-ast", action="store_true")
    ap.add_argument("--verbose", "-v", action="store_true")
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--emit-py", metavar="FILE")
    ap.add_argument("--emit-pyc", metavar="FILE")
    ap.add_argument("--emit-xbc", metavar="FILE")
    ap.add_argument("--disasm", action="store_true")
    ap.add_argument("--model")
    ap.add_argument("--bench", action="store_true")
    args, extra = ap.parse_known_args()

    # ------------------------------------------------ Package Manager Commands
    if args.cmd in ("install", "i", "add"):
        if args.file:
            ok = install_package(args.file, is_global=args.global_pkg, verbose=True)
            return 0 if ok else 1
        else:
            ok = install_all(verbose=True)
            return 0 if ok else 1

    if args.cmd in ("remove", "uninstall", "rm"):
        if not args.file:
            print("Usage: x remove <package_name>", file=sys.stderr)
            return 1
        ok = remove_package(args.file, is_global=args.global_pkg, verbose=True)
        return 0 if ok else 1

    if args.cmd in ("list", "pkg"):
        list_packages()
        return 0

    if args.cmd in ("update", "up"):
        update_package(args.file, is_global=args.global_pkg, verbose=True)
        return 0

    if args.cmd in ("init", "new"):
        init_project(args.file)
        return 0

    # ------------------------------------------------ Version Command
    if args.cmd in ("version", "--version", "-V"):
        print(f"X++ Engine v{__version__}")
        print("  ZCOM – native bytecode AOT compiler   (CLI: xppvm)")
        print("  ZITR – native VM interpreter          (default when xppvm exists)")
        print("  ZJIT – native AOT backend (C++ -> machine code)")
        print("  XCOM – strict AOT (Python bytecode)")
        print("  XITR – fast VM (Python exec)")
        print("  ITR  – AI intent compiler (LLM)")
        print("  XPM  – Package manager (x install github.com/<lib>)")
        return 0

    if args.cmd in ("disasm", "zcom", "zitr", "zjit"):
        rc = run_native(args, args.cmd, args.file)
        if rc is None:
            print("Error: xppvm native binary not available. Install g++/clang and run: make -C native",
                  file=sys.stderr)
            return 2
        return rc

    if args.cmd not in ("run", "compile", "transpile", "check"):
        ap.print_help()
        return 1

    if not args.file:
        print("Usage: x run <file.xp> [--mode ZCOM|ZITR|ZJIT|XCOM|XITR|ITR]",
              file=sys.stderr)
        return 1
    if not os.path.exists(args.file):
        print(f"Error: file '{args.file}' not found", file=sys.stderr)
        return 1

    with open(args.file, "r", encoding="utf-8") as f:
        full_src = f.read()

    model = args.model
    mm = re.search(r'USE MODEL\s+"([^"]+)"', full_src)
    if mm and not model:
        model = mm.group(1)
    mode = args.mode or detect_mode(full_src)
    if mode == "AI":
        mode = RNM_ITR
    if args.cmd == "compile" and mode in (RNM_ZITR, RNM_ZJIT):
        mode = RNM_ZCOM

    t0 = time.perf_counter()
    try:
        # ------------------------------ transpile / check
        if args.cmd == "transpile":
            src_strict = strip_header_directives(full_src)
            print(fast_transpile(src_strict), end="")
            return 0
        if args.cmd == "check":
            src_strict = strip_header_directives(full_src)
            if args.strict_ast:
                from .ast_parser import parse
                parse(src_strict)
                print("OK – AST valid")
            else:
                from .fast_transpiler import compile_src
                compile_src(src_strict)
                print("OK – compiles")
            return 0

        # ------------------------------ native modes
        if mode in (RNM_ZCOM, RNM_ZITR, RNM_ZJIT):
            if mode == RNM_ZCOM:
                rc = run_native(args, "zcom", args.file)
                if rc is not None and args.cmd == "run":
                    rc = run_native(args, "zitr", args.file)
                if rc is None:
                    if not args.mode:
                        mode = RNM_XCOM
                    else:
                        print("Error: native mode ZCOM requires xppvm. Install g++/clang and run: make -C native",
                              file=sys.stderr)
                        return 2
                else:
                    return rc
            elif mode == RNM_ZITR:
                rc = run_native(args, "zitr", args.file)
                if rc is None:
                    # Fall back to XITR when native VM is not built/available
                    if args.verbose:
                        print("[i] Native VM (xppvm) not available; running with XITR engine", file=sys.stderr)
                    mode = RNM_XITR
                else:
                    return rc
            elif mode == RNM_ZJIT:
                rc = run_native(args, "zjit", args.file)
                if rc is None or rc != 0:
                    # If C++ compiler is not present on host, fall back to native ZITR / AOT
                    rc = run_native(args, "zitr", args.file)
                    if rc is None:
                        mode = RNM_XCOM
                    else:
                        return rc
                return rc

        # ------------------------------ strict / VM execution
        if mode == RNM_XCOM or args.cmd == "compile":
            src_strict = strip_header_directives(full_src)
            code, py = xcom_compile(
                src_strict, strict_ast=args.strict_ast,
                out_py=args.emit_py, out_pyc=args.emit_pyc,
            )
            if args.verbose:
                print(py, file=sys.stderr)
            if args.cmd == "compile":
                print(f"XCOM OK – {len(py)} chars Python, "
                      f"{len(code.co_code)} bytes bytecode")
                if args.bench:
                    print(f"compile: {(time.perf_counter()-t0)*1000:.2f} ms",
                          file=sys.stderr)
                return 0
            g = make_xpp_env(argv=extra)
            exec(code, g)

        elif mode == RNM_XITR:
            src_strict = strip_header_directives(full_src)
            xitr_run(src_strict, strict_ast=args.strict_ast, argv=extra)
            if args.verbose:
                print(f"[XITR cache] {cache_info()}", file=sys.stderr)

        elif mode in (RNM_ITR, RNM_AI):
            from . import ai_engine
            lines = full_src.splitlines(True)
            body_start = 0
            for i, l in enumerate(lines):
                if re.match(r"\s*RNM\s*=\s*ITR", l, re.I):
                    body_start = i + 1
                    break
            ai_src = "".join(lines[body_start:])
            if not ai_src.strip():
                ai_src = re.sub(r'USE MODEL\s+"[^"]+"\s*\n?', "", full_src)
                ai_src = re.sub(r"^\s*RNM\s*=\s*\w+\s*\n?", "", ai_src,
                                count=1, flags=re.MULTILINE)
            ai_mode = "PYTHON"
            if not re.search(r"RNM\s*=\s*ITR", full_src, re.I):
                ai_mode = "ASSEMBLY"
            ai_engine.run_ai_mode(ai_src, mode=ai_mode, model=model,
                                  verbose=args.verbose,
                                  use_cache=not args.no_cache, argv=extra)
        else:
            print(f"Unknown mode: {mode}", file=sys.stderr)
            return 2

    except SystemExit as se:
        return se.code if isinstance(se.code, int) else 1
    except Exception as e:
        print(f"X++ [{mode}] Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    if args.bench or args.verbose:
        dt = (time.perf_counter() - t0) * 1000
        print(f"[{mode}] {dt:.2f} ms", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
