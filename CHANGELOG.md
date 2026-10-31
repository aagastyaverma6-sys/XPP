# Changelog – X++ (XPlusPlus)

All notable changes to X++ follow [Keep a Changelog](https://keepachangelog.com/) and [SemVer](https://semver.org/).

## [0.4.6] - 2026-10-29
### Fixed
- **Setup never fails now:** `setup.bat` / `setup.sh` / `setup.command` first try to download prebuilt `xppvm`/`xppvm.exe` + `zjit_runtime.hpp` from GitHub Releases (`/latest/download/`). Only if offline do they fall back to compiling with `g++`/`clang++`. If both fail, gracefully falls back to `XITR`/`XCOM` (Python) – `x run` always works.
- Version drift fixed: `xpp_core/__init__.py`, `pyproject.toml`, `vscode/xpp-vscode/package.json`, `tools/xpp_setup.py`, `native/Makefile`, `setup.*`, `build_xppvm.bat` all now `0.4.6`.
- `.gitignore` added – `__pycache__/`, `*.pyc`, `*.xbc`, `*.zexe`, `build/`, `xppvm*`, `xpp_packages/` no longer tracked.
- Grammar: `xp.tmLanguage.json` now highlights `ZCOM|ZITR|ZJIT` and `use|import|as`.

### Added
- GitHub Actions: `build-xppvm.yml` (Windows/Linux/macOS) – builds and uploads `xppvm` binaries to every Release.
- `CHANGELOG.md` (this file) – replaces scattered `RELEASE_NOTES_*.md`.

### Changed
- README title `v0.4.5 → v0.4.6`.

## [0.4.5] - 2026-10-18
### Added
- **XPM Package Manager:** `x install github.com/<owner>/<repo>`, `x install`, `x remove`, `x list`, `x update`, `x init`, `xpp.json` + `xpp.lock` with commit pinning + `xpp_packages/` + `~/.xpp/packages/` + tarball fallback.
- **34 Standard Libraries** verified on all 5 RNMs (`XCOM, XITR, ZCOM, ZITR, ZJIT`): `mathX, Xsci, Xnum, Xlin, XCAS, XCalculus, Xplotlib, ScrapeX, XWeb, XWview, GraphiX, XGUI, TerminX, Xin, GameX (12 2D + 10 3D formats), Xanmin8` + 19 system libs (`os, sys, pathlib, shutil, time, datetime, random, json, csv, re, collections, itertools, functools, urllib, http, socket, unittest, logging, sqlite3`).
- 110 examples (`examples/*.xp`), `bench/test_v045.py` golden suite.

## [0.4.1] - 2026-09-30
### Added
- Native VM `native/` (C++17, zero deps): `ZCOM` (bytecode `.xbc`), `ZITR` (NaN-boxed stack VM, flat dispatch, 10k recursion), `ZJIT` (C++→machine code), `xppvm` CLI, `zjit_runtime.hpp`, benchmarks `sum 1..5M: XITR 381ms / ZITR 202ms / ZJIT 50ms`, `fib(28): 55/91/10 ms`.
- One-click setup: `setup.bat`, `setup.sh`, `setup.command`, `tools/xpp_setup.py` with 6-try pip shim, PATH, OS file icons, VS Code extension + Code Runner.

## [0.3.x] - 2026-06..09
- Legacy `XCOM`/`XITR`/`ITR` (AI via OpenRouter) pseudocode core: `fn/end, if/elif/else/end, while, loop from/to/step, loop in, safe/fail, out, push, in, read`, lists/dicts, true/false/nil.
