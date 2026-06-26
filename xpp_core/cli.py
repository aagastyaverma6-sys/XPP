#!/usr/bin/env python3
import sys, os, argparse, time, re
from . import __version__, RNM_XCOM, RNM_XITR, RNM_ITR, RNM_AI
from .strict_compiler import xcom_compile, run_xcom
from .strict_vm import xitr_run, cache_info
from .fast_transpiler import transpile as fast_transpile
from . import ai_engine
def detect_mode(src_head: str, default=RNM_XITR):
    for line in src_head.splitlines()[:30]:
        s=line.strip()
        if not s or s.startswith("#"): continue
        m=re.match(r'RNM\s*=\s*([A-Za-z_]+)', s, re.I)
        if m: return m.group(1).upper()
        if s.startswith("USE MODEL"): continue
        break
    return default
def strip_header_directives(src: str):
    lines=src.splitlines(True); out=[]; skipped_rnm=False
    for l in lines:
        s=l.strip()
        if not skipped_rnm and re.match(r'RNM\s*=\s*\w+', s, re.I):
            skipped_rnm=True; continue
        if s.startswith("USE MODEL"): continue
        out.append(l)
    return "".join(out)
def main():
    ap=argparse.ArgumentParser(prog="x", description=f"X++ v{__version__}")
    ap.add_argument("cmd", nargs="?", default="run", help="run | compile | transpile | check | version")
    ap.add_argument("file", nargs="?")
    ap.add_argument("--mode","-m", choices=["XCOM","XITR","ITR","AI"])
    ap.add_argument("--strict-ast", action="store_true")
    ap.add_argument("--verbose","-v", action="store_true")
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--emit-py", metavar="FILE")
    ap.add_argument("--emit-pyc", metavar="FILE")
    ap.add_argument("--model")
    ap.add_argument("--bench", action="store_true")
    args, extra = ap.parse_known_args()
    if args.cmd in ("version","--version","-V"):
        print(f"X++ Engine v{__version__}"); print("  XCOM  – strict AOT compiler  (C-like)"); print("  XITR  – strict fast VM       (Java-like)"); print("  ITR   – AI intent compiler   (LLM)"); return 0
    if args.cmd not in ("run","compile","transpile","check"): ap.print_help(); return 1
    if not args.file: print("Usage: x run <file.xp> [--mode XCOM|XITR|ITR] [--verbose]", file=sys.stderr); return 1
    if not os.path.exists(args.file): print(f"Error: file '{args.file}' not found", file=sys.stderr); return 1
    with open(args.file,"r",encoding="utf-8") as f: full_src=f.read()
    model=args.model
    mm=re.search(r'USE MODEL\s+"([^"]+)"', full_src)
    if mm and not model: model=mm.group(1)
    mode=args.mode or detect_mode(full_src)
    if mode=="ITR": mode=RNM_ITR
    t0=time.perf_counter()
    try:
        if args.cmd=="transpile":
            src_strict=strip_header_directives(full_src); py=fast_transpile(src_strict); print(py, end=""); return 0
        if args.cmd=="check":
            src_strict=strip_header_directives(full_src)
            if args.strict_ast:
                from .ast_parser import parse; parse(src_strict); print("OK – AST valid")
            else:
                from .fast_transpiler import compile_src; compile_src(src_strict); print("OK – compiles")
            return 0
        if mode==RNM_XCOM or args.cmd=="compile":
            src_strict=strip_header_directives(full_src)
            code,py=xcom_compile(src_strict, strict_ast=args.strict_ast, out_py=args.emit_py, out_pyc=args.emit_pyc)
            if args.verbose: print(py, file=sys.stderr)
            if args.cmd=="compile":
                print(f"XCOM OK – {len(py)} chars Python, {len(code.co_code)} bytes bytecode")
                if args.bench: print(f"compile: {(time.perf_counter()-t0)*1000:.2f} ms", file=sys.stderr)
                return 0
            exec(code, {"__name__":"__main__","__builtins__":__builtins__})
        elif mode==RNM_XITR:
            src_strict=strip_header_directives(full_src)
            xitr_run(src_strict, strict_ast=args.strict_ast)
            if args.verbose: print(f"[XITR cache] {cache_info()}", file=sys.stderr)
        elif mode in (RNM_ITR, RNM_AI, "AI"):
            lines=full_src.splitlines(True); body_start=0
            for i,l in enumerate(lines):
                if re.match(r'\s*RNM\s*=\s*ITR', l, re.I): body_start=i+1; break
            ai_src="".join(lines[body_start:])
            if not ai_src.strip():
                ai_src=re.sub(r'USE MODEL\s+"[^"]+"\s*\n?', '', full_src)
                ai_src=re.sub(r'^\s*RNM\s*=\s*\w+\s*\n?', '', ai_src, count=1, flags=re.MULTILINE)
            ai_mode="PYTHON"
            if not re.search(r'RNM\s*=\s*ITR', full_src, re.I): ai_mode="ASSEMBLY"
            ai_engine.run_ai_mode(ai_src, mode=ai_mode, model=model, verbose=args.verbose, use_cache=not args.no_cache, argv=extra)
        else: print(f"Unknown mode: {mode}", file=sys.stderr); return 2
    except SystemExit as se: return se.code if isinstance(se.code,int) else 1
    except Exception as e:
        print(f"X++ [{mode}] Error: {e}", file=sys.stderr)
        if args.verbose: import traceback; traceback.print_exc()
        return 1
    if args.bench or args.verbose:
        dt=(time.perf_counter()-t0)*1000; print(f"[{mode}] {dt:.2f} ms", file=sys.stderr)
    return 0
if __name__=="__main__": sys.exit(main())
