# X++ strict fast transpiler – C-like front-end speed
import re
_control = {
    "fn": re.compile(r'^\s*fn\s+([A-Za-z_]\w*)\s*\(([^)]*)\)\s*:\s*$'),
    "if": re.compile(r'^\s*if\s+(.+):\s*$'),
    "elif": re.compile(r'^\s*elif\s+(.+):\s*$'),
    "else": re.compile(r'^\s*else\s*:\s*$'),
    "while": re.compile(r'^\s*while\s+(.+):\s*$'),
    "loop_from": re.compile(r'^\s*loop\s+([A-Za-z_]\w*)\s+from\s+(.+)\s+to\s+(.+?)(?:\s+step\s+(.+))?\s*:\s*$'),
    "loop_in": re.compile(r'^\s*loop\s+([A-Za-z_]\w*)\s+in\s+(.+)\s*:\s*$'),
    "safe": re.compile(r'^\s*safe\s*:\s*$'),
    "fail": re.compile(r'^\s*fail(?:\s+([A-Za-z_]\w*))?\s*:\s*$'),
    "end": re.compile(r'^\s*end\s*$'),
    "return": re.compile(r'^\s*return(?:\s+(.+))?$'),
    "break": re.compile(r'^\s*break\s*$'),
    "continue": re.compile(r'^\s*continue\s*$'),
    "out": re.compile(r'^\s*out\s+(.+)$'),
    "push": re.compile(r'^\s*push\s+(.+)\s+to\s+([A-Za-z_]\w*)$'),
    "assign": re.compile(r'^\s*([A-Za-z_]\w*(?:\.[A-Za-z_]\w*|\[[^\]]+\])*)\s*=\s*(.+)$'),
}
def _expr(e: str) -> str:
    e = re.sub(r'\bin\s+(".*?")', r'input(\1)', e)
    e = re.sub(r"\bin\s+('.*?')", r'input(\1)', e)
    e = re.sub(r'\bread\s+(".*?")', r'open(\1).read()', e)
    e = re.sub(r"\bread\s+('.*?')", r'open(\1).read()', e)
    e = re.sub(r'\btrue\b', 'True', e)
    e = re.sub(r'\bfalse\b', 'False', e)
    e = re.sub(r'\bnil\b', 'None', e)
    return e
def transpile(src: str) -> str:
    out=[]; indent=0; stack=[]
    for raw_line in src.splitlines():
        line=raw_line.rstrip(); stripped=line.strip()
        if not stripped or stripped.startswith("#"): continue
        if _control["end"].match(stripped):
            if stack: stack.pop(); indent=max(0,indent-4)
            continue
        m=_control["fn"].match(stripped)
        if m: name,params=m.groups(); out.append(" "*indent+f"def {name}({params}):"); stack.append("fn"); indent+=4; continue
        m=_control["if"].match(stripped)
        if m: out.append(" "*indent+f"if {_expr(m.group(1))}:"); stack.append("if"); indent+=4; continue
        m=_control["elif"].match(stripped)
        if m: indent=max(0,indent-4); out.append(" "*indent+f"elif {_expr(m.group(1))}:"); indent+=4; continue
        m=_control["else"].match(stripped)
        if m: indent=max(0,indent-4); out.append(" "*indent+"else:"); indent+=4; continue
        m=_control["while"].match(stripped)
        if m: out.append(" "*indent+f"while {_expr(m.group(1))}:"); stack.append("while"); indent+=4; continue
        m=_control["loop_from"].match(stripped)
        if m:
            var,start,end,step=m.groups(); start_e=_expr(start); end_e=_expr(end)
            if step: out.append(" "*indent+f"for {var} in range({start_e}, ({end_e})+1, {_expr(step)}):")
            else: out.append(" "*indent+f"for {var} in range({start_e}, ({end_e})+1):")
            stack.append("loop"); indent+=4; continue
        m=_control["loop_in"].match(stripped)
        if m: var,it=m.groups(); out.append(" "*indent+f"for {var} in {_expr(it)}:"); stack.append("loop"); indent+=4; continue
        m=_control["safe"].match(stripped)
        if m: out.append(" "*indent+"try:"); stack.append("safe"); indent+=4; continue
        m=_control["fail"].match(stripped)
        if m: exc=m.group(1); indent=max(0,indent-4); out.append(" "*indent+(f"except Exception as {exc}:" if exc else "except Exception:")); indent+=4; continue
        m=_control["return"].match(stripped)
        if m: v=m.group(1); out.append(" "*indent+(f"return {_expr(v)}" if v else "return")); continue
        if _control["break"].match(stripped): out.append(" "*indent+"break"); continue
        if _control["continue"].match(stripped): out.append(" "*indent+"continue"); continue
        m=_control["out"].match(stripped)
        if m: out.append(" "*indent+f"print({_expr(m.group(1))})"); continue
        m=_control["push"].match(stripped)
        if m: val,lst=m.groups(); out.append(" "*indent+f"{lst}.append({_expr(val)})"); continue
        m=_control["assign"].match(stripped)
        if m: lhs,rhs=m.groups(); out.append(" "*indent+f"{lhs} = {_expr(rhs)}"); continue
        out.append(" "*indent+_expr(stripped))
    return "\n".join(out)+("\n" if out else "")
def compile_src(src: str, filename="<xpp>", optimize=2):
    py = transpile(src)
    code = compile(py, filename, "exec", optimize=optimize, dont_inherit=True)
    return code, py
