from .fast_transpiler import compile_src, transpile
from .ast_parser import parse as ast_parse
import marshal, importlib.util
def xcom_compile(src: str, strict_ast: bool=False, out_py: str=None, out_pyc: str=None):
    if strict_ast: ast_parse(src)
    code, py = compile_src(src, optimize=2)
    if out_py:
        with open(out_py, "w", encoding="utf-8") as f: f.write("# X++ XCOM v0.3\n"+py)
    if out_pyc:
        with open(out_pyc, "wb") as f:
            f.write(importlib.util.MAGIC_NUMBER)
            f.write((0).to_bytes(12,"little"))
            f.write(b"XPP\x00")
            marshal.dump(code, f)
    return code, py
def run_xcom(src: str, strict_ast=False, argv=None):
    code,_ = xcom_compile(src, strict_ast=strict_ast)
    g={"__name__":"__main__","__builtins__":__builtins__}
    if argv:
        import sys; old=sys.argv[:]; sys.argv=["xpp"]+argv
        try: exec(code,g)
        finally: sys.argv=old
    else: exec(code,g)
    return g
