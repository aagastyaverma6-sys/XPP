# X++ v0.4.7 Release Notes – Polish & Reliability Release

**Release Date:** 31 Oct 2026 • **Tag:** 0.4.7 • **Previous:** 0.4.6

X++ v0.4.7 is the **Polish & Reliability Release**, introducing a revamped transparent brand identity, full lockfile and branch/tag pinning for XPM, integrated testing and code formatting tools, and Rust/Clang-grade diagnostic pointers.

---

## What's New in v0.4.7

### 1. Minimalist Transparent Brand Identity
- Removed legacy boxed backgrounds in favor of a modern, continuous monoline vector loop emblem (icons/xpp-logo-minimal.svg).
- Features a luminous gradient contour, transparent background, and vibrant accent plus glyphs for modern desktop and dark-mode integration.

### 2. XPM Package Manager Hardening
- **Tag & Branch Pinning:** Support for @tag and #branch in dependency strings:
  `ash
  x install github.com/user/lib@v1.2.0
  x install github.com/user/lib#main
  `
- **Deterministic Lockfiles (xpp.lock):** Automatic Git commit SHA resolution and lockfile synchronization for repeatable builds.

### 3. Developer Experience (DX) & Tooling
- **x fmt Formatter:** Built-in canonical code indentation and block formatting for .xp files:
  `ash
  x fmt [file.xp]
  `
- **x check Linter:** Static syntax checker highlighting unclosed or mismatched blocks (n, if, while, loop, safe, ail) before execution.
- **x test Test Suite Runner:** Automatic discovery and execution of *_test.xp and 	est*.xp files with summary reports:
  `ash
  x test
  `
- **Rust/Clang-Grade Diagnostics:** Pinpoint error reporting with caret pointers (^^^), line numbers, and actionable suggestions.

### 4. XITE IDE Evolution
- Redesigned UI styling with Cupertino glassmorphism, translucency, and preparation for low-latency AI ghost completions.

---

## Upgrading
`ash
# Clone or pull latest
git pull origin main

# Verify version
x version
`

**Full diff:** 0.4.6...v0.4.7 • **License:** GPL-3.0 • **Author:** Aagastya Verma / Atom Software • **Site:** https://xpplang.vercel.app
