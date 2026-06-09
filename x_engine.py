import sys
import os
import subprocess
import requests
import platform
import re
import hashlib

# get the api key from the system env
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
DEFAULT_MODEL = "meta-llama/llama-3.2-3b-instruct:free"
VERSION = "0.2.2"

def clean_ai_code(text):
    """
    grabs code from markdown blocks if they there, otherwise just returns the text. 
    tries to be smart about AI chatter.
    """
    match = re.search(r"```(?:[a-zA-Z]*)\n?(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    return text.strip()

def verify_environment():
    if not OPENROUTER_API_KEY:
        print("X++ Fatal Error: OPENROUTER_API_KEY env var not found.")
        print("Run: export OPENROUTER_API_KEY='your_key' (Linux/macOS)")
        print("Run: set OPENROUTER_API_KEY=your_key (Windows CMD)")
        print("Run: $env:OPENROUTER_API_KEY='your_key' (Windows PowerShell)")
        sys.exit(1)

def ask_ai_compiler(system_prompt, user_code, model_override=None, verbose=False):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_override or DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_code}
        ],
        "temperature": 0.0
    }
    if verbose:
        print(f"Requesting compilation from {model_override or DEFAULT_MODEL}...")
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        if 'choices' not in data: raise ValueError(f"API Error: {data}")
        return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        if "429" in str(e):
            print("Rate Limit Exceeded: The free AI model is busy. X++ will now use local cache.")
            print("Tip: Wait 60 seconds or try a different model using 'USE MODEL'.")
            return None
        
        # try to get a more specific error from the response body if available
        error_body = e.response.json() if hasattr(e, 'response') and e.response is not None else str(e)
        print(f"Network Error: Cant talk to the X++ cloud backend. {error_body}")
        sys.exit(1)

def get_cached_ai_response(system_prompt, user_code, active_model, use_cache=True, verbose=False):
    """
    check for a local cached version of the AI response so we dont waste credits.
    """
    cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".x_cache")
    os.makedirs(cache_dir, exist_ok=True)
    
    # make a unique fingerprint for this specific code and prompt
    fingerprint = hashlib.sha256(f"{system_prompt}{user_code}{active_model}".encode()).hexdigest()
    cache_path = os.path.join(cache_dir, fingerprint)

    if use_cache and os.path.exists(cache_path):
        if verbose: print("Using cached AI compilation.")
        with open(cache_path, "r", encoding="utf-8") as f:
            return f.read()

    response = ask_ai_compiler(system_prompt, user_code, active_model, verbose)
    
    if response:
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(response)
    return response

def main():
    verify_environment()

    # basic cli arg check
    if len(sys.argv) < 2:
        print(f"X++ Engine v{VERSION}")
        print("Usage: x run <filename.xp> [--verbose] [--no-cache]")
        sys.exit(0)

    if sys.argv[1] in ["--version", "-v"]:
        print(f"X++ Engine Version {VERSION}")
        sys.exit(0)

    if sys.argv[1] != "run" or len(sys.argv) < 3:
        print("Usage: x run <filename.xp> [--verbose] [--no-cache]")
        sys.exit(1)

    # Parse arguments and flags
    args = sys.argv[2:]
    filepath = next((a for a in args if a.endswith('.xp')), None)
    if not filepath:
        print(" Error: No X++ (.xp) source file specified.")
        return
    
    verbose = "--verbose" in args or "-v" in args
    use_cache = "--no-cache" not in args
    script_args = [a for a in args if a != filepath and not a.startswith("-")]

    if not filepath.endswith('.xp'):
        print(" Error: X++ source files must use the '.xp' extension.")
        return
    if not os.path.exists(filepath):
        # if its not here check where the engine is instaled
        engine_home = os.path.dirname(os.path.abspath(__file__))
        fallback_path = os.path.join(engine_home, filepath)

        if os.path.exists(fallback_path):
            filepath = fallback_path
        else:
            print(f" Error: Source file '{filepath}' could not be located.")
            print(f" Looked in: {os.path.abspath(filepath)}")
            print(f" Also checked engine home: {os.path.abspath(fallback_path)}")
            return

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if not lines:
        print(" Error: Source file is empty.")
        return

    full_content = "".join(lines)
    # see if the user wants a specific model
    model_match = re.search(r'USE MODEL "([^"]+)"', full_content)
    active_model = model_match.group(1) if model_match else DEFAULT_MODEL
    if model_match: print(f"Using requested model: {active_model}")

    # find if we doing python or assembly (skip empty lines, comments, and model specs)
    first_meaningful_line = next((l.strip() for l in lines if l.strip() and not l.strip().startswith("#") and not l.strip().startswith("USE MODEL")), "")

    if first_meaningful_line == "RNM=ITR":
        mode = "PYTHON"
        # find the header and take the rest of the code
        header_idx = next(i for i, l in enumerate(lines) if l.strip() == "RNM=ITR")
        user_code = "".join(lines[header_idx + 1:])
    else:
        mode = "ASSEMBLY"
        user_code = full_content

    # ==========================================
    # 🐍 PYTHON RUNTIME MODE
    # ==========================================
    if mode == "PYTHON":
        system_prompt = """You are the official compiler backend for X++. Translate X++ code into valid Python 3.
        Rules:
        - also if the code is plain english algorithm make the most optimal code for it
        - Pure indentation block structure (No braces '{}').
        - 'out val1, val2' -> 'print(val1, val2)'
        - 'var = in "prompt"' -> 'var = input("prompt")'
        - 'loop i from X to Y' -> 'for i in range(X, Y + 1):'
        - 'loop item in list' -> 'for item in list:'
        - 'while condition' -> 'while condition:'
        - 'push val to list' -> 'list.append(val)'
        - 'read "file.txt"' -> 'open("file.txt").read()'
        - 'safe' / 'fail' blocks -> 'try:' / 'except Exception:'
        - Functions use parentheses: 'fn name(arg1, arg2)' -> 'def name(arg1, arg2):'
        Output ONLY raw executable Python/NASM code. Absolutely NO markdown backticks (```python) or explanations."""

        ai_code = get_cached_ai_response(system_prompt, user_code, active_model, use_cache, verbose)
        if not ai_code:
            print("X++ Error: Could not get a response from the AI and no cache exists. Try again in a minute.")
            sys.exit(1)
            
        ai_code = clean_ai_code(ai_code)

        if verbose:
            print("\n--- GENERATED PYTHON ---")
            print(ai_code + "\n" + "-"*25)

        temp_py = ".temp_runtime.py"
        with open(temp_py, "w", encoding='utf-8') as f:
            f.write(ai_code)
        
        try:
            subprocess.run([sys.executable, temp_py] + script_args)
        finally:
            if os.path.exists(temp_py):
                os.remove(temp_py)

    # ==========================================
    # 🔨 ASSEMBLY COMPILER MODE (SELF-HEALING)
    # ==========================================
    elif mode == "ASSEMBLY":
        target_os = "Windows x64" if platform.system() == "Windows" else "Linux x86_64"
        api_hint = "Win64 API (e.g., GetStdHandle, WriteFile) or msvcrt calls" if platform.system() == "Windows" else "sys_write/sys_read syscalls"
        calling_conv = "Shadow space and RCX, RDX, R8, R9" if platform.system() == "Windows" else "RDI, RSI, RDX, RCX, R8, R9"

        system_prompt = f"""You are the official compiler backend for X++. Translate X++ into {target_os} NASM Assembly.
        Rules:
        - Block structure relies entirely on indentation.
        - Use ONLY valid x64 registers (rax, rbx, rcx, rdx, rsi, rdi, rbp, rsp, r8-r15). Never use r16+.
        - Strings MUST be declared in 'section .data'. Do not move strings directly into registers.
        - Translate 'fn name(arg1, arg2)' into assembly labels, passing args via {calling_conv}.
        - Map 'out' functions to {api_hint}.
        Output ONLY raw, compilation-ready NASM Assembly code. Absolutely NO markdown backticks or explanations."""

        ai_code = get_cached_ai_response(system_prompt, user_code, active_model, use_cache, verbose)
        if not ai_code:
            print("X++ Error: AI compilation failed and no cached version exists.")
            sys.exit(1)

        ai_code = clean_ai_code(ai_code)

        if verbose:
            print("\n--- GENERATED ASSEMBLY ---")
            print(ai_code + "\n" + "-"*27)

        temp_asm = ".temp.asm"
        temp_obj = ".temp.o"
        temp_bin = ".temp_bin"
        
        # fix things for windows users
        asm_format = "elf64"
        linker = ["ld", temp_obj, "-o", temp_bin]
        if platform.system() == "Windows":
            asm_format = "win64"
            temp_bin = ".temp_bin.exe"
            linker = ["gcc", temp_obj, "-o", temp_bin] # Using GCC as a common Windows linker

        with open(temp_asm, "w", encoding='utf-8') as f:
            f.write(ai_code)

        def run_compilation(asm_file, obj_file, bin_file, fmt, link_cmd, extra_args):
            try:
                subprocess.run(["nasm", "-f", fmt, asm_file, "-o", obj_file], check=True, capture_output=True, text=True)
                subprocess.run(link_cmd, check=True, capture_output=True, text=True)
                # make sure we call local file right
                exec_path = bin_file if platform.system() == "Windows" or bin_file.startswith(("./", "/")) else f"./{bin_file}"
                subprocess.run([exec_path] + extra_args)
                return True
            except FileNotFoundError as e:
                print(f"Dependency Missing: {e.filename} isnt installed or not in PATH.")
                return False

        try:
            if not run_compilation(temp_asm, temp_obj, temp_bin, asm_format, linker, script_args):
                pass # helper handled the error
        except subprocess.CalledProcessError as e:
            print("[X++] Assembly syntax anomaly caught. Engaging AI Self-Healing Engine...")
            
            healing_prompt = f"The previous assembly code you generated failed to compile with this exact error:\n{e.stderr}\nFix the syntax constraints and return ONLY the corrected x86_64 NASM code."
            fixed_code = get_cached_ai_response(healing_prompt, ai_code, active_model, use_cache=False, verbose=verbose)
            fixed_code = clean_ai_code(fixed_code)
            
            with open(temp_asm, "w", encoding='utf-8') as f:
                f.write(fixed_code)
            try:
                run_compilation(temp_asm, temp_obj, temp_bin, asm_format, linker, script_args)
            except subprocess.CalledProcessError:
                print("X++ Fatal Error: Code layout exceeds automated resolution.")
                if platform.system() == "Windows":
                    print("Tip: If you dont have a full NASM/GCC toolchain, add 'RNM=ITR' to the top of your .xp file.")
        finally:
            # clean up temp junk from disk
            for file in [temp_asm, temp_obj, temp_bin]:
                if os.path.exists(file):
                    os.remove(file)

if __name__ == "__main__":
    main()
