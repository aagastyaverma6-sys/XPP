# X++ v0.4.6 Release Notes – Setup Never Fails

**Release Date:** 29 Oct 2026 • **Tag:** `v0.4.6` • **Previous:** `v0.4.5`

X++ v0.4.6 is a **stability hotfix** that makes `v0.4.5` actually shippable. No breaking language changes — same pseudocode, same 34 libs, same 5 RNMs — but setup now works on every machine, even without `g++`.

---

## 1. Setup Never Fails (the big one)

**Problem in 0.4.5:** `xppvm` binary was deleted, so every new user had to compile C++ with `g++`/`clang++`. On college/office PCs with no `winget` or no internet, `setup.bat` / `setup.sh` showed `[i] no g++ yet` and looked broken.

**Fix in 0.4.6:**
- `setup.bat` → new step `[3a/4] Prebuilt xppvm (download)` – tries `powershell Invoke-WebRequest https://github.com/aagastyaverma6-sys/XPP/releases/latest/download/xppvm.exe` into `build/` before trying to compile. If offline, falls back to compile; if both fail, gracefully falls back to `XITR`/`XCOM` (Python) – `x run` **always works**.
- `setup.sh` / `setup.command` → new step `[2b/4]` – tries `curl -fsSL .../latest/download/xppvm -o ./build/xppvm` (or `wget`), same fallback chain.
- New GitHub Actions workflow `.github/workflows/build-xppvm.yml` builds `xppvm` + `xppvm.exe` + `zjit_runtime.hpp` on Windows/Linux/macOS for **every tag/release** and auto-attaches them to the Release. No manual build needed.

**Result:** `Download → unpack → double-click setup → x run hello.xp` works everywhere, even without admin.

---

## 2. Version Sync – Everything is 0.4.6 Now

| File | 0.4.5 | 0.4.6 |
|------|-------|-------|
| `xpp_core/__init__.py` | `__version__ = "0.4.5"` | `__version__ = "0.4.6"` |
| `pyproject.toml` | `version = "0.4.5"` | `version = "0.4.6"` |
| `xpp_lang.egg-info/PKG-INFO` | `0.4.1` | `0.4.6` |
| `vscode/xpp-vscode/package.json` | `0.4.1` | `0.4.6` |
| `package.json` (root) | `0.4.5` | `0.4.6` |
| `tools/xpp_setup.py` | `v0.4.1 SETUP` | `v0.4.6 SETUP` |
| `native/Makefile` | `v0.4.1` | `v0.4.6` |
| `setup.bat` / `setup.sh` / `setup.command` | `v0.4.1` | `v0.4.6` |
| `build_xppvm.bat` | `v0.4.1` | `v0.4.6` |
| `xite.py` | `v0.4.1` | `v0.4.6` |
| `bench/test_all.sh` | `v0.4.1` / `v0.4.5` | `v0.4.6` |
| `xpp_core/*` (`cli`, `pm`, `native_bridge`, `fast_transpiler`, `stdlib/*`) | `0.4.5` | `0.4.6` |
| `xp.tmLanguage.json` + `vscode/grammar/xp.tmLanguage.json` | `XCOM|XITR|ITR` | `XCOM|XITR|ZCOM|ZITR|ZJIT|ITR` + `use|import|as` |

---

## 3. Repo Hygiene

- **New `.gitignore`** – ignores `__pycache__/`, `*.pyc`, `*.xbc`, `*.zexe`, `build/`, `xppvm`, `xppvm.exe`, `xpp_packages/`, `dist/`, `.venv/` etc. No more junk in commits.
- **New `CHANGELOG.md`** – replaces scattered `RELEASE_NOTES_v0.4.x.md` with [Keep a Changelog](https://keepachangelog.com/) format.
- **This file** `RELEASE_NOTES_v0.4.6.md` – GitHub Release notes (copy this into the Release description).
- Grammar fixed: `xp.tmLanguage.json` now highlights `use`, `import`, `as` and all 6 RNMs.

---

## 4. CI / Workflows

- **`.github/workflows/build-xppvm.yml`** – builds on `ubuntu-latest`, `macos-latest`, `windows-latest` on every tag + `release: published` + manual dispatch. Uploads artifacts and auto-attaches to Release via `softprops/action-gh-release`.
- **`.github/workflows/ci.yml`** – quick smoke test on `push` to `main`: `pip install -e .`, `make -C native`, `bench/test_v045.py`, `x run examples/hello.xp`.

---

## 5. What Did NOT Change (still 0.4.5 features, just more stable)

- Language: `fn/end, if/elif/else/end, while, loop from/to/step, loop in, safe/fail, out, push, in, read`, lists, dicts, `true/false/nil`
- 5 RNMs: `ZITR` (default NaN-boxed VM), `ZCOM` (`.xbc`), `ZJIT` (C++→machine code), `XCOM`/`XITR` (Python), `ITR` (OpenRouter AI)
- XPM + 34 StdLibs: `mathX, Xsci, Xnum, Xlin, XCAS, XCalculus, Xplotlib, ScrapeX, XWeb, XWview, GraphiX, XGUI, TerminX, Xin, GameX, Xanmin8` + 19 system libs
- Benchmarks unchanged: `sum 1..5M` `XITR 381ms / ZITR 202ms / ZJIT 50ms`, `fib(28)` `55/91/10 ms`

---

## 6. Upgrade from 0.4.5

```bash
git pull
# or fresh:
git clone https://github.com/aagastyaverma6-sys/XPP.git
cd XPP
# Windows
setup.bat
# Linux/macOS
./setup.sh
# then
x run examples/hello.xp
x run examples/fib_fast.xp --mode ZJIT
```

No code changes needed – `v0.4.5` programs run unchanged on `v0.4.6`.

---

## 7. Known Issues Fixed in 0.4.6

- `setup.bat` title still `v0.4.1` → fixed `v0.4.6`
- `PKG-INFO` stale `0.4.1` → fixed `0.4.6`
- `vscode` extension `0.4.1` → fixed `0.4.6` + grammar `ZCOM/ZITR/ZJIT`
- `__pycache__` committed → now ignored
- No prebuilt binaries in Release → now auto-built via Actions

---

**Full diff:** `v0.4.5...v0.4.6` • **License:** GPL-3.0 • **Author:** Aagastya Verma / Atom Software • **Site:** https://xpplang.vercel.app
