# X++ v0.4.1 – "Bare Metal" Release

The language stays the easiest to learn and write — same pseudocode, no
pointers, automatic GC — but the engine underneath is now a native VM:

## New – Native VM (`native/`, zero-dependency C++17)

- **ZCOM** – strict bytecode AOT compiler.
  - Parses strict X++ pseudocode into a compact, verifiable bytecode format
    (`.xbc`, little-endian, `XBC1`).
  - Deterministic, fast: `xppvm zcom app.xp --disasm` shows every instruction.
- **ZITR** – native stack VM interpreter.
  - NaN-boxed 64-bit values (int / float / string / list / dict / function /
    builtin in one machine word) — no boxing objects for numbers.
  - Arena garbage collection: lists/dicts/strings are freed automatically,
    zero manual memory management.
  - Full language: `fn`, `if/elif/else`, `while`, `loop from..to..step`,
    `loop x in list`, `safe/fail` (real exception stack), recursion, closures
    of builtins, `out`, `push`, `in`, `read`, lists, dicts, index/attr
    access, `and/or` short-circuit, `**`, `%`, comparisons.
- **ZJIT** – native AOT backend.
  - Translates the same AST directly to portable C++ (embedding a small
    self-contained runtime) and compiles it with the system C++ compiler to
    a native executable. Runs closest to C speed; no Python involved at all.
- **xppvm** CLI: `zcom | zitr | zjit | disasm | run | version`.

## Compatibility
- **Windows / Linux / macOS**: pure C++17 + libc / libstdc++ only.
- `make -C native` (Linux/macOS) or `build_xppvm.bat` (Windows, MinGW-w64).
- Bytecode `.xbc` is portable across machines.

## Engine stays invisible
- `x run app.xp` still works exactly like before; it auto-builds `xppvm`
  once and uses ZITR (native) as the default. `RNM=XITR`/`XCOM` legacy paths
  remain available for compatibility; `RNM=ITR` AI mode unchanged.

## Files
- `bench/test_all.sh` – 29-test golden regression suite (ZITR + ZJIT must be
  byte-identical; also covers legacy XITR)
- `native/xpp.hpp`, `native/xpp_parse.cpp` – lexer/parser (recursive descent)
- `native/xpp_codegen.cpp` – bytecode compiler + `.xbc` ser/deser + disasm
- `native/xpp_vm.cpp`, `native/xpp_values.cpp` – VM runtime + builtins
- `native/xpp_nativegen.cpp`, `native/zjit_runtime.hpp` – native AOT backend
- `native/Makefile`, `build_xppvm.bat` – builds

## Benchmarks (this machine: Linux x86-64, CPython 3.11, g++ 12.2)

| Workload | XITR (CPython) | ZITR (VM) | ZJIT (native) |
|----------|----------------|-----------|---------------|
| `sum 1..5,000,000` | 381 ms | 202 ms | 50 ms |
| `fib(28)` recursive | 55 ms | 91 ms | 10 ms |

ZJIT executes as a cached native binary (rebuilds only when the source
changes), so `x run --mode ZJIT` is ~1 s the first time and instant after.

## One-click setup + file icons
- `setup.bat` (Windows), `setup.sh` (Linux/macOS), `setup.command` (macOS
  double-click) – install every dependency the engine needs (Python, g++,
  VS Code on Windows), build + install the VM, register PATH, and wire up
  the X++ file logo.
- `tools/xpp_setup.py` – cross-platform engine used by all setups (incl. a
  pip-free `x` shim fallback so setup works on locked-down systems).
- `icons/` – X++ logo (PNG sizes, `xpp.ico` for Windows, `xpp.icns` for macOS).
- `vscode/xpp-vscode/` – VS Code extension with syntax highlighting +
  **X++ file icon theme**; setup also installs Code Runner for the Run button.
- OS registration: Windows Explorer `.xp` icon, Linux hicolor/mime/desktop
  in `~/.local/share`, macOS `X++ Files.app` handler + `duti` if available.

## Stability fixes (final audit, v0.4.1)
- Interpreter dispatch is now **flat/non-recursive** — X++ recursion depth to
  10,000+ works (previously crashed around 100).
- Fixed builtin argument ordering for `len(x)`, `in "prompt"`, `read "file"`
  (callee is now pushed before arguments).
- ZJIT: `len()` results are boxed before printing; `safe/fail`, negative
  `step` loops, string/list/dict ops verified in native AOT.
- `xppvm zitr app.xbc` now runs compiled bytecode directly (portable .xbc
  round-trip: `xppvm zcom app.xp -o app.xbc` → `xppvm zitr app.xbc`).
- 16/16 regression tests pass across ZITR / ZJIT / legacy XITR.

## Roadmap (next versions)
- Register-based JIT with profiling feedback (replace AOT-by-C++ path on
  hot loops); threaded/indirect-threaded dispatch for ZITR.
- Modules/imports (`use "file.xp"`), native FFI (`use c`), multi-threading.
- Windows `xppvm.exe` CI build + installer integration; Xite gets native
  run buttons wired to ZITR/ZJIT.
- Bench suite (`bench/`) + per-OS reported numbers.

GPL-3.0 – Aagastya Verma / Atom Software · r/X++_LANG
