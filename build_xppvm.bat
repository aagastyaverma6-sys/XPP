@echo off
REM ============================================================
REM  X++ v0.4.1 – Build the native VM (xppvm.exe) on Windows
REM  Requires: MinGW-w64 g++ (or clang++) in PATH
REM  Build:    build\xppvm.exe  (+ zjit_runtime.hpp next to it)
REM ============================================================
setlocal
cd /d "%~dp0"

where g++ >nul 2>&1
if errorlevel 1 (
  echo [X++] g++ not found. Install MinGW-w64 (e.g. winget install mingw) and retry.
  exit /b 1
)

if not exist build mkdir build

echo [X++] Compiling native VM (xppvm.exe)...
g++ -O2 -std=c++17 -o build\xppvm.exe ^
  native\xpp_main.cpp native\xpp_parse.cpp native\xpp_codegen.cpp ^
  native\xpp_vm.cpp native\xpp_values.cpp native\xpp_nativegen.cpp

if errorlevel 1 (
  echo [X++] Build FAILED.
  exit /b 1
)

copy /Y native\zjit_runtime.hpp build\zjit_runtime.hpp >nul
echo [X++] Build OK: build\xppvm.exe
echo [X++] Add  %~dp0build  to PATH, or set XPP_NATIVE_DIR=%~dp0build
endlocal
