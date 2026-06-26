"""X++ AI Intent Engine – v0.3.1 Strict
RNM=ITR – LLM acts as a strict deterministic compiler, zero chatter.
"""
import os, sys, subprocess, requests, re, hashlib, platform, tempfile, ast

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
DEFAULT_MODEL = "meta-llama/llama-3.2-3b-instruct:free"
VERSION = "0.3.1-ai"

# ---------- strict output cleaning ----------
def clean_ai_code(text: str) -> str:
    """
    X++ Strict AI Code Extractor v0.3.1
    Guarantees: output is ast.parse()-able or empty.
    """
    if not text:
        return ""
    t = text
    # strip reasoning tags
    t = re.sub(r'<think>.*?</think>', '', t, flags=re.DOTALL|re.IGNORECASE)
    t = re.sub(r'<\/?(?:think|reasoning|analysis|scratchpad|output|code)[^>]*>', '', t, flags=re.IGNORECASE)
    # extract first fenced block
    m = re.search(r'```(?:python|py|python3|xpp|xp)?\s*\n(.*?)\n```', t, re.DOTALL|re.IGNORECASE)
    if not m:
        m = re.search(r'```\s*\n?(.*?)\n?```', t, re.DOTALL)
    if m:
        t = m.group(1)
    # strip fence remnants
    t = re.sub(r'```[a-zA-Z0-9_+\-]*', '', t)
    t = t.replace('```','').replace('~~~','')
    lines = t.splitlines()
    # find first code line
    def is_code_start(s: str) -> bool:
        s=s.strip()
        if not s: return False
        return bool(re.match(r'^(import |from |def |class |if |elif |else:|for |while |try:|except|return |break|continue|pass|raise |print\(|@|async |with |#|"""|\'\'\'|[A-Za-z_][\w\.]*\s*[=\(\[]|\[|\{|\"|\'|\d)', s))
    start=0
    chatter = ("here is","here's","sure","below is","the following","this is","output:","result:","python:","certainly","of course","i'll","i will","okay","alright","as requested","###","**")
    for i, ln in enumerate(lines):
        s = ln.strip()
        if not s: continue
        low = s.lower()
        if any(low.startswith(w) for w in chatter):
            start = i+1; continue
        if is_code_start(s):
            start = i; break
    lines = lines[start:]
    # trim trailing chatter
    trailing = ("hope this","let me know","feel free","note:","explanation","this code","above code","remember","please","thanks","is there","would you","can i","need anything")
    last_code = -1
    for i in range(len(lines)-1, -1, -1):
        s = lines[i].strip()
        if not s: continue
        low = s.lower()
        if any(mk in low for mk in trailing) and not re.search(r'[=\(\)\[\]{}:"\'#]|^import |^def |^return |^print', s):
            continue
        last_code = i
        break
    if last_code >= 0:
        lines = lines[:last_code+1]
    t = "\n".join(lines).strip().strip("`~ \t\r\n")
    # final: ast-parse surgical trim
    def try_parse(c):
        try: ast.parse(c); return True
        except SyntaxError: return False
    if t and not try_parse(t):
        sp = t.splitlines()
        # trim top
        for drop in range(1, min(25, len(sp))):
            cand = "\n".join(sp[drop:])
            if cand.strip() and try_parse(cand):
                t = cand; break
        # trim bottom
        if not try_parse(t):
            sp = t.splitlines()
            for drop in range(1, min(25, len(sp))):
                cand = "\n".join(sp[:len(sp)-drop])
                if cand.strip() and try_parse(cand):
                    t = cand; break
    return t.strip()

def verify_env():
    if not OPENROUTER_API_KEY:
        print("X++ AI Fatal: OPENROUTER_API_KEY env var not found.", file=sys.stderr)
        print("  export OPENROUTER_API_KEY='sk-or-...'", file=sys.stderr)
        sys.exit(1)

def ask_ai(system_prompt, user_code, model=None, verbose=False, timeout=60):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/aagastyaverma6-sys/XPP",
        "X-Title": "X++ v0.3 Strict Compiler"
    }
    payload = {
        "model": model or DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_code}
        ],
        "temperature": 0.0,
        "top_p": 0.0,
        "top_k": 1,
        "repetition_penalty": 1.0,
        "max_tokens": 3000,
        # stop tokens kill chatter at the source
        "stop": ["```", "Here is", "Here ", "Sure", "Below", "Note:", "Explanation:", "\n\nI ", "\nThe ", "\n\n# ", "\n\n- ", "\n\n*"],
        "seed": 0,
        "provider": {"order": ["groq","together","fireworks","openrouter"], "allow_fallbacks": False}
    }
    if verbose:
        print(f"[AI] {model or DEFAULT_MODEL} …", file=sys.stderr)
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=timeout)
        if r.status_code == 429:
            print("[AI] Rate limited – will try cache.", file=sys.stderr)
            return None
        r.raise_for_status()
        data = r.json()
        if "choices" not in data or not data["choices"]:
            raise ValueError(f"AI error response: {data}")
        return data["choices"][0]["message"]["content"].strip()
    except requests.RequestException as e:
        body = ""
        try:
            body = e.response.text[:400] if hasattr(e, "response") and e.response is not None else str(e)
        except Exception:
            body = str(e)
        print(f"[AI] Network error: {body}", file=sys.stderr)
        return None

def cached_ai(system_prompt, user_code, model, use_cache=True, verbose=False):
    cache_dir = os.path.expanduser("~/.xpp_cache")
    os.makedirs(cache_dir, exist_ok=True)
    os_tag = f"{platform.system()}-{platform.machine()}"
    fp = hashlib.sha256(f"{os_tag}||{system_prompt}||{model}||{user_code}".encode("utf-8")).hexdigest()
    cp = os.path.join(cache_dir, fp + ".txt")
    if use_cache and os.path.exists(cp):
        if verbose: print("[AI] cache hit", file=sys.stderr)
        with open(cp, "r", encoding="utf-8") as f: return f.read()
    txt = ask_ai(system_prompt, user_code, model, verbose)
    if txt:
        with open(cp, "w", encoding="utf-8") as f: f.write(txt)
        return txt
    return None

# ---------- STRICT COMPILER PROMPTS ----------
PYTHON_PROMPT = """You are X++ Strict Compiler v0.3 – a deterministic code transpiler, NOT a chatbot.
Your job: translate X++ pseudocode OR plain-English algorithms into executable Python 3. Output CODE ONLY. Zero chatter.

STRICT OUTPUT CONTRACT – VIOLATION = COMPILATION FAILURE:
1. FIRST CHARACTER of your response MUST be a valid Python token: [a-zA-Z_#"'0-9([].
   NEVER start with: Here, Sure, Below, Certainly, ```, -, *, 
   NEVER output markdown fences, NEVER output explanations.
2. Output RAW Python code ONLY. NO markdown. NO comments except # Sorry no valid algorithm found sentinel.
3. NO conversational text. Zero chatter.
4. Output must pass ast.parse() first try.
5. If input has NO algorithm / is vague chatter → output EXACTLY ONE LINE:
# Sorry no valid algorithm found

TRANSLATION MAP – X++ → Python 3:
out val1, val2        → print(val1, val2)
var = in "prompt"     → var = input("prompt")
var = in              → var = input()
loop i from X to Y    → for i in range(X, Y + 1):
loop i from X to Y step Z → for i in range(X, Y + 1, Z):
loop x in y           → for x in y:
while cond            → while cond:
push v to lst         → lst.append(v)
read "f"              → open("f").read()
safe: … fail e: … end → try: … except Exception as e:
fn name(a,b): … end   → def name(a,b):
true / false / nil    → True / False / None

FORMAT:
- 4-space indent, Pythonic.
- If input is plain English: emit OPTIMAL Python 3.
- Preserve logic exactly. No hallucinated I/O.

EXAMPLES – COPY THIS STYLE EXACTLY:
Input:
out "hi"
Output:
print("hi")

Input:
loop i from 1 to 5:
out i
end
Output:
for i in range(1, 5 + 1):
    print(i)

REMEMBER: FIRST CHARACTER = CODE. NO CHATTER. NO FENCES. RAW PYTHON ONLY.
VIOLATION CRASHES THE COMPILER.
"""

ASSEMBLY_PROMPT_TMPL = """You are X++ Strict NASM Compiler v0.3 – deterministic transpiler, NOT chatbot.

STRICT OUTPUT CONTRACT:
1. FIRST CHARACTER MUST be 's' from 'section .data' – NO chatter, NO markdown.
2. Output RAW x86_64 NASM ONLY. Must assemble with nasm -f {asm_fmt} clean.
3. If not compilable → output EXACTLY:
; Sorry no valid algorithm found

RULES:
- Target: {target_os}
- Registers ONLY: rax,rbx,rcx,rdx,rsi,rdi,rbp,rsp,r8-r15 – NEVER r16+
- Strings in 'section .data' only
- fn name(a,b) → label, args via {calling_conv}
- out → {api_hint}
- Emit:
  section .data
  section .text
  global _start   (Linux) / global main (Windows)
- End with proper exit syscall

FIRST OUTPUT CHAR = 's'. NO CHATTER.
"""

# ---------- runner ----------
def _extract_first_valid_python(text: str) -> str:
    lines = text.splitlines()
    start = 0
    for i, ln in enumerate(lines):
        s = ln.strip()
        if re.match(r'^(import |from |def |class |if |for |while |try:|#|print\(|[A-Za-z_][\w]*\s*[=\(]|\[|\{|\"|\')', s):
            start = i; break
    cand = "\n".join(lines[start:])
    for trim in range(0, min(20, len(lines)-start)):
        test = "\n".join(lines[start:len(lines)-trim] if trim else lines[start:])
        try:
            ast.parse(test)
            return test
        except SyntaxError:
            continue
    return cand

def run_ai_python(source: str, model=None, verbose=False, use_cache=True, argv=None, retries=2):
    verify_env()
    ai_code = cached_ai(PYTHON_PROMPT, source, model or DEFAULT_MODEL, use_cache, verbose)
    if not ai_code:
        print("X++ Error: Could not get a response from the AI and no cache exists. Try again in a minute.", file=sys.stderr)
        sys.exit(2)
    ai_code = clean_ai_code(ai_code)
    if "Sorry no valid algorithm found" in ai_code or ai_code.strip().startswith("# Sorry"):
        print("Sorry no valid algorithm found", file=sys.stderr)
        sys.exit(3)
    try:
        ast.parse(ai_code)
    except SyntaxError as e:
        if verbose:
            print(f"[AI] Syntax check failed line {e.lineno}: {e.msg}", file=sys.stderr)
            print("--- AI OUTPUT ---\n", ai_code, "\n----------------", file=sys.stderr)
        repaired = _extract_first_valid_python(ai_code)
        try:
            ast.parse(repaired)
            ai_code = repaired
            if verbose: print("[AI] Auto-repaired chatter.", file=sys.stderr)
        except SyntaxError:
            if retries > 0:
                if verbose: print("[AI] Strict recompile – zero chatter…", file=sys.stderr)
                fix_prompt = PYTHON_PROMPT + "\n\nCRITICAL FAILURE: Previous output failed ast.parse: " + str(e) + "\nRETRY RULES: FIRST CHARACTER MUST BE A PYTHON TOKEN. NO MARKDOWN. NO CHATTER. OUTPUT RAW PYTHON ONLY OR '# Sorry no valid algorithm found'."
                ai_code2 = ask_ai(fix_prompt, source, model or DEFAULT_MODEL, verbose=verbose)
                if ai_code2:
                    ai_code2 = clean_ai_code(ai_code2)
                    try:
                        ast.parse(ai_code2)
                        ai_code = ai_code2
                    except SyntaxError as e2:
                        print(f"[AI] Syntax check failed after repair: {e2}", file=sys.stderr)
                        if verbose: print("--- FAILED ---\n", ai_code2, file=sys.stderr)
                        sys.exit(4)
            else:
                print(f"[AI] Syntax check failed: {e}", file=sys.stderr)
                sys.exit(4)
    if verbose:
        print("\n--- GENERATED PYTHON ---\n"+ai_code+"\n-------------------------\n", file=sys.stderr)
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tf:
        tf.write(ai_code); tmp=tf.name
    try:
        import sys as _sys
        old_argv=_sys.argv[:]; _sys.argv=[tmp]+(argv or [])
        g={"__name__":"__main__","__file__":tmp,"__builtins__":__builtins__}
        with open(tmp,"r",encoding="utf-8") as f: code=compile(f.read(),tmp,"exec")
        exec(code,g); _sys.argv=old_argv
    finally:
        try: os.remove(tmp)
        except: pass

def run_ai_assembly(source: str, model=None, verbose=False, use_cache=True, argv=None):
    verify_env()
    target_os = "Windows x64" if platform.system()=="Windows" else "Linux x86_64"
    api_hint = "Win64 API (e.g., GetStdHandle, WriteFile) or msvcrt calls" if platform.system()=="Windows" else "sys_write/sys_read syscalls"
    calling_conv = "Shadow space and RCX, RDX, R8, R9" if platform.system()=="Windows" else "RDI, RSI, RDX, RCX, R8, R9"
    asm_fmt = "win64" if platform.system()=="Windows" else "elf64"
    system_prompt = ASSEMBLY_PROMPT_TMPL.format(target_os=target_os, api_hint=api_hint, calling_conv=calling_conv, asm_fmt=asm_fmt)
    ai_code = cached_ai(system_prompt, source, model or DEFAULT_MODEL, use_cache, verbose)
    if not ai_code:
        print("X++ Error: AI compilation failed and no cached version exists.", file=sys.stderr); sys.exit(2)
    ai_code = clean_ai_code(ai_code)
    if verbose:
        print("\n--- GENERATED ASSEMBLY ---\n"+ai_code+"\n---------------------------\n", file=sys.stderr)
    with tempfile.TemporaryDirectory() as td:
        asm_path=os.path.join(td,"a.asm"); obj_path=os.path.join(td,"a.o"); bin_path=os.path.join(td,"a.exe" if platform.system()=="Windows" else "a.out")
        with open(asm_path,"w",encoding="utf-8") as f: f.write(ai_code)
        linker = ["gcc",obj_path,"-o",bin_path,"-no-pie"] if platform.system()=="Windows" else ["ld",obj_path,"-o",bin_path]
        def do_compile():
            subprocess.run(["nasm","-f",asm_fmt,asm_path,"-o",obj_path], check=True, capture_output=True, text=True)
            subprocess.run(linker, check=True, capture_output=True, text=True)
            subprocess.run([bin_path]+(argv or []), check=False); return True
        try: do_compile()
        except subprocess.CalledProcessError as e:
            print("[X++] Assembly syntax anomaly caught. Engaging AI Self-Healing Engine...", file=sys.stderr)
            healing = f"The previous assembly code you generated failed to compile with this exact error:\n{e.stderr}\nFix the syntax constraints and return ONLY the corrected x86_64 NASM code. FIRST CHARACTER MUST BE 's'."
            fixed = cached_ai(healing, ai_code, model or DEFAULT_MODEL, use_cache=False, verbose=verbose)
            if fixed:
                fixed = clean_ai_code(fixed)
                with open(asm_path,"w",encoding="utf-8") as f: f.write(fixed)
                try: do_compile()
                except subprocess.CalledProcessError:
                    print("X++ Fatal Error: Code layout exceeds automated resolution.", file=sys.stderr); sys.exit(5)
        except FileNotFoundError as fnf:
            print(f"Dependency Missing: {fnf.filename} isnt installed or not in PATH.", file=sys.stderr); sys.exit(6)

def run_ai_mode(source: str, mode="PYTHON", model=None, verbose=False, use_cache=True, argv=None):
    if mode.upper() == "ASSEMBLY":
        return run_ai_assembly(source, model, verbose, use_cache, argv)
    return run_ai_python(source, model, verbose, use_cache, argv)
