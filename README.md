![X++ logo](icons/xpp-logo.png)

# X++ (XPlusPlus) v0.4.1
*Programming For Everyone*

**Same pseudocode. Same ease. Now a real native VM.**

X++ is an intent-driven language: you write **strict pseudocode** (or loose English steps for the AI mode), type one command, and it *booms*. Version 0.4.1 adds a **zero-dependency native VM** (C++17) so your programs run **without Python** — the Python stack is still available for the legacy and AI paths.

- **Ease of Python** – pseudocode syntax, automatic garbage collection, no pointers, no manual memory management, no build files. Write the code, type `x run app.xp`, done.
- **Speed of native code** – ZITR is a fast stack VM; ZJIT compiles your `.xp` straight to machine code (via portable C++ emitted by the backend, compiled with your system compiler).
- **Unmatched compatibility** – the VM and the native backend are pure C++17 and build on Windows / Linux / macOS. Same bytecode `.xbc` (`.bc`) runs anywhere.

**Version history:** this repo carries the v0.3 legacy release notes; see `RELEASE_NOTES_v0.4.1.md` for what's new in 0.4.1.

---

## One command, that's it

```
x run app.xp
```

`x` auto-detects `RNM=ZITR`/`RNM=ZCOM` headers, builds `xppvm` once if it's missing (needs g++/clang), and runs your pseudocode on the native VM. Everything stays exactly as simple as before — the VM is plumbing, not something you manage.

Subreddit: r/X++_LANG · Author: Aagastya Verma / Atom Software

## Modes

| RNM | Name | What it is | Needs |
|-----|------|------------|-------|
| `RNM=ZITR` | Native fast VM (default) | Stack VM over `.xbc` bytecode | `xppvm` (auto-built) |
| `RNM=ZCOM` | Strict bytecode AOT | `.xp` → `.xbc` bytecode, verifiable/disassemblable | `xppvm` |
| `RNM=ZJIT` | Native AOT backend | `.xp` → C++ → machine code, runs fastest | `xppvm` + system C++ compiler |
| `RNM=XCOM` | Legacy strict AOT | `.xp` → Python bytecode (v0.3, kept) | Python |
| `RNM=XITR` | Legacy fast VM | Python `exec` code-object cache (v0.3, kept) | Python |
| `RNM=ITR` | AI intent compiler | LLM translates English steps → executable (v0.3, kept) | OpenRouter key |

## Language – the same easy pseudocode

```
RNM=ZITR
fn fib(n):
  if n <= 1:
    return n
  end
  return fib(n-1) + fib(n-2)
end
loop i from 0 to 10:
  out i, fib(i)
end
```

All the v0.3 pseudocode stays identical: `fn / end`, `if / elif / else / end`, `while`, `loop i from a to b step s`, `loop x in list`, `safe / fail / end`, `out`, `push v to lst`, `in`, `read`, lists `[1,2,3]`, dicts `{"k": v}`, `true / false / nil`, `and / or / not`, `**`, `%`, etc. **No pointers, no types to annotate, no manual freeing — the VM garbage-collects automatically.**

## Instant Installation – download → unpack → run setup → boom

**Windows:** download the zip, unpack, then double-click:

```
setup.bat
```

**macOS / Linux:**

```
./setup.sh                          ← macOS: double-click setup.command
```

The setup installs *everything* by itself — no manual steps:

- **Python 3.9+** (only if missing: winget on Windows, system package manager on Linux, Xcode CLT on macOS)
- **g++/clang** (only if missing — needed for the native VM / ZJIT)
- **VS Code** (Windows; on Linux/macOS it wires itself in if VS Code is already installed)
- the **native VM (`xppvm`)** — builds once, installs it with its runtime
- the **`x` command** on PATH (with a pip-free shim fallback so it always lands)
- **X++ file logo everywhere**: VS Code icon theme + Code Runner "Run" button, Windows Explorer registry icon, Linux hicolor/mime icons, macOS Finder handler app

Then open any editor — VS Code, Notepad, TextEdit, whatever — write:

```
out "hello world"
```

save as `hello.xp`, and:

```
x run hello.xp
```

…or in VS Code press the **Code Runner run button**. Boom. (Restart your terminal / VS Code once after setup so PATH and the icon theme load.)

> Optional AI mode (`RNM=ITR`) needs an OpenRouter key:
> `export OPENROUTER_API_KEY=...` then `x run ai_demo.xp --mode ITR`.

## Build the VM by hand (optional)

```
# Linux / macOS
make -C native            # -> ./xppvm
./xppvm zitr app.xp

# Windows (MinGW-w64)
build_xppvm.bat           # -> build\xppvm.exe
```

## Usage

```
x run app.xp                        # native VM (auto ZITR)
x run app.xp --mode ZJIT            # native AOT – fastest
x run app.xp --mode ZCOM            # compile + run bytecode
x compile app.xp --emit-xbc app.xbc
x disasm app.xbc                    # (or: xppvm disasm app.xbc)
x run ai_demo.xp --mode ITR         # legacy AI intent mode

xppvm zcom app.xp --disasm          # see the bytecode
xppvm zitr app.xp                   # run directly, no Python at all
xppvm zjit app.xp --keep            # build + keep the native binary
```

## Benchmarks (Linux, x86-64, g++ 12.2 – run on your machine with `--bench`)

Measured on this machine (Linux x86-64, CPython 3.11, g++ 12.2). ZJIT times are
native execution only; the first build takes ~1 s, and is cached (rebuilt only
when the source changes).

| Workload | XITR (CPython) | ZITR (VM) | ZJIT (native AOT) |
|----------|----------------|-----------|-------------------|
| `sum 1..5,000,000` (`bench/sum_loop.xp`) | 381 ms | **202 ms** | **50 ms** |
| `fib(28)` recursive (`bench/fib_rec.xp`) | 55 ms | 91 ms | **10 ms** |

ZITR already beats CPython on hot numeric loops; ZJIT is **5–8× faster** than
CPython and typically within ~5–10× of hand-written C (a register-based JIT
will close the last gap — see release notes).

## Regression suite

`bash bench/test_all.sh` runs 29 golden tests across ZITR, ZJIT and the
legacy XITR engine — semantics (evaluation order, scoping, short-circuit
`and`/`or`, empty-container truthiness), control flow, mutual + 20,000-deep
recursion, collections/builtins, `safe`/error propagation, `read`, comments
and directives. Both native engines must produce byte-identical output.

## About

X++ is in beta; updates roll out constantly. This is my first programming language — constructive criticism, suggestions, and pull requests drive the project.

- License: GPL-3.0-or-later
- Legacy v0.3 releases: `RELEASE_NOTES_v0.3.md`
- New in v0.4.1: `RELEASE_NOTES_v0.4.1.md`
