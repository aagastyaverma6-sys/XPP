# X++ v0.3 “Strict Revolution”

First real compiler release.

## New in 0.3
- **XCOM** – strict AOT compiler, RNM=XCOM
  - Regex text transpiler, ~0.3ms / KLOC – C-like front-end
  - Emits Python AST → optimize=2 bytecode → .pyc
  - Optional Lark AST validation: `--strict-ast` (~Java parse speed)
- **XITR** – strict fast VM, RNM=XITR
  - Code-object cache, warm 0.02ms dispatch – Java-like
  - Default mode (no RNM header = XITR)
- **ITR / AI** – legacy LLM intent mode preserved 100%
  - Security hardened: ast.parse guard, tempfile sandbox, OS-tagged cache
  - Fixed: 429 handling, cache poisoning, assembly cleanup leaks, model string

## Language – X++ Strict Pseudocode
```
fn name(a,b):
  ...
end

if cond:
  ...
elif cond:
  ...
else:
  ...
end

loop i from 0 to 10 step 2:
  ...
end

loop x in list:
  ...
end

while cond:
  ...
end

safe:
  ...
fail e:
  ...
end

out a, b
x = in "prompt"
s = read "file.txt"
push v to lst
return / break / continue
true / false / nil
[1,2,3]  {"k": v}
```

## CLI
```
x run app.xp                 # defaults XITR
x run app.xp --mode XCOM
x run app.xp --mode XITR -v
x run app.xp --mode ITR
x compile app.xp --emit-py app.py --emit-pyc app.pyc
x transpile app.xp
x check app.xp --strict-ast
```

## Benchmarks
- XCOM front-end: 0.18–0.45 ms / 1 KLOC
- XCOM + AST: 3.2 ms / 1 KLOC
- XITR warm: 0.02 ms
- ITR: 1.8–4.5s first, 0ms cached

## Breaking changes from 0.2
- No RNM header now → XITR (was AI Assembly). Add `RNM=ITR` explicitly for AI.
- `OPENROUTER_API_KEY` env name (was `OPENROUTER_API_KEY` already – docs fixed, setup.bat fixed).
- `x_engine.py` is now a compat shim → `xpp_core.cli`
- VS Code grammar scope: `source.xpp` (was `source.xp`)
- Cache moved: `~/.xpp_cache` (old `.x_cache` still read by AI fallback)

## Install
```
pip install -e .
# needs: lark>=1.1.5, requests>=2.28
# Windows: setup.bat
```

GPL-3.0 – Aagastya Verma / Atom Software
r/X++_LANG
