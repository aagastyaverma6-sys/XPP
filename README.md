# X++ (XPlusPlus) 

X++ is an experimental, intent-driven semantic compiler engine that treats Large Language Models like dynamic execution hardware. Write code using strict X++ grammar, standard pseudocode algorithms, or loose, unstructured English steps. The engine automatically translates your design down to optimized Python 3 or raw x86_64 NASM Assembly binaries. It has been developed using python by the founder of Atom Software, Aagastya Verma. This is my first programming language so I will largely appriciate constructive critisism and pull requests or suggestions will be the driving force of this new programming revolution.

##  Key Innovations

* **Intent-Based Compilation:** The backend layout extracts functional logical patterns from conversational speech or textbook pseudo-code, bypassing rigid language syntax parsing.
* **Cryptographic Caching Layer:** Avoids network latncy and duplicate AI compilation calls by hashing your prompt configurations, source scripts, and selected models into unique SHA-256 fingerprints stored in `.x_cache`. If code does not change, execution is instant and determnistic.
* **Self-Healing Assembly Optimization:** If a low-level target compilation fails local syntax checks, the engine reads `stderr` from the compilation utility, passes it to the AI infrastructure, patches register allocatoinn constraints on the fly, and re-links your binary without human intervention.

##  Instant Installation

Setting up X++ requires zero manual configuration. 

1. Download and extract the repository zip folder onto your computer.
2. Open the directory folder and double-click **`setup.bat`**.
3. Paste your secret OpenRouter API token when prompted to store your security configuration securely.
4. Restart your active command terminals or VS Code windows to refresh system path variables.

##  Usage

Excute your source files smoothly across any system directory pathway:

```bash
x run test.xp
```
###  Semantic Validation & Guardrails (Updated for Beta)
This isn't a loose "text-to-code" prompt wrapper that passes conversational chatter to an API. 
The core system prompt enforces strict syntactic validation. If you pass a vague, conversational, 
or non-algorithmic prompt to the engine, the validation layer catches it and fails loudly with:
'Sorry no valid algorithm found'

It completely bypasses standard AI hallucinations or conversational chatter, treating your 
plain text files like an actual structured blueprint that must pass logic validation checks.

