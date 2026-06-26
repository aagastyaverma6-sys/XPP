# X++ (XPlusPlus) v0.3
*Programming For Everyone*

**Strict pseudocode compiler + fast VM + AI intent fallback**

X++ is an experimental, intent-driven semantic compiler engine that treats Large Language Models like dynamic execution hardware. Write code using strict X++ grammar, standard pseudocode algorithms, or loose, unstructured English steps. The engine automatically translates your design down to optimized Python 3 or raw x86_64 NASM Assembly binaries.

It has been developed using python by the founder of Atom Software, Aagastya Verma. This is my first programming language so I will largely appreciate constructive criticism and pull requests or suggestions will be the driving force of this new programming revolution.

Subreddit: r/X++_LANG

## Key Innovations – v0.3

- **XCOM – Intent-Based Strict Compilation:** NEW in 0.3. A real deterministic compiler front-end – regex text transpiler, ~0.3ms / KLOC, C-like speed. Optional Lark AST validation for Java-like safety. Outputs Python bytecode / .pyc.
- **XITR – Fast VM:** NEW in 0.3. Code-object cache, warm start 0ms – Java-like. Perfect for scripting.
- **ITR – AI Intent Compiler (preserved):** The backend extracts functional logical patterns from conversational speech or textbook pseudo-code, bypassing rigid language syntax parsing.
- **Cryptographic Caching Layer:** Avoids network latency and duplicate AI compilation calls by hashing your prompt configurations, source scripts, OS ABI, and selected models into unique SHA-256 fingerprints stored in `~/.xpp_cache`. If code does not change, execution is instant and deterministic.
- **Self-Healing Assembly Optimization:** If a low-level target compilation fails local syntax checks, the engine reads `stderr` from the compilation utility, passes it to the AI infrastructure, patches register allocation constraints on the fly, and re-links your binary without human intervention.

## Modes

| RNM | Name | Speed |
|-----|------|-------|
| `RNM=XCOM` | Strict AOT Compiler | **C-like** |
| `RNM=XITR` | Strict Fast VM | **Java-like** |
| `RNM=ITR`  | AI Intent | network / cached |

Strict X++ syntax (pseudocode):
```
RNM=XCOM
fn fib(n):
  if n <= 1:
    return n
  end
  return fib(n-1) + fib(n-2)
end
loop i from 0 to 10:
  out fib(i)
end
```

## Instant Installation

Setting up X++ requires zero manual configuration.

1. Download and extract the repository zip folder onto your computer.
2. `pip install -e .`  (or `pip install lark requests`)
   – or on Windows double-click **`setup.bat`**.
3. Paste your secret OpenRouter API token when prompted (only needed for `RNM=ITR` AI mode).
4. Restart your active command terminals or VS Code windows to refresh system path variables.

## Usage

Execute your source files smoothly across any system directory pathway:

```
x run test.xp
```

More:

```
x run app.xp --mode XCOM
x run app.xp --mode XITR --verbose
x compile app.xp --emit-py app.py --emit-pyc app.pyc
x transpile app.xp
x check app.xp --strict-ast
# AI legacy:
x run ai_demo.xp --mode ITR
```

### Semantic Validation & Guardrails (Updated for v0.3)

Strict modes (`XCOM` / `XITR`) use a real deterministic compiler – no LLM involved.

This isn't a loose "text-to-code" prompt wrapper that passes conversational chatter to an API – **unless you explicitly choose `RNM=ITR`**.

The AI mode core system prompt enforces strict syntactic validation. If you pass a vague, conversational, or non-algorithmic prompt to the engine, the validation layer catches it and fails loudly with:
`Sorry no valid algorithm found`

It completely bypasses standard AI hallucinations or conversational chatter, treating your plain text files like an actual structured blueprint that must pass logic validation checks.

## About

This is my first time creating a programming language, please tell any issues or flaws in the code. Constructive criticism and suggestions and pull requests are highly appreciated.
