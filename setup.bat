@echo off
setlocal EnableExtensions EnableDelayedExpansion
title X++ v0.4.1 – ONE-CLICK SETUP
color 0B
cd /d "%~dp0"

echo.
echo ============================================================
echo        X++ v0.4.1  -  AUTO SETUP  (Windows)
echo   Download, unpack, double-click this file. Done.
echo ============================================================
echo.

rem ------------------------------------------------------------
rem  0) admin notice
rem ------------------------------------------------------------
net session >nul 2>&1
if errorlevel 1 (
  echo  [i] Running without admin - OK. Every install below is
  echo      user-level or winget-able.
) else (
  echo  [+] Administrator privileges detected.
)
echo.

set "PYTHON_CMD="

rem ------------------------------------------------------------
rem  1) PYTHON  (needed for the `x` command and AI mode)
rem ------------------------------------------------------------
echo  [1/4]  Python 3.9+
call :find_python
if defined PYTHON_CMD goto :python_ok

echo  [X++] Python not found - installing Python 3.12 via winget...
winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements >nul 2>&1
if errorlevel 1 (
  echo  [X++] winget failed - downloading the official installer...
  powershell -NoProfile -Command "try { Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe' -OutFile '%TEMP%\xpp-python-setup.exe' } catch { exit 1 }"
  if exist "%TEMP%\xpp-python-setup.exe" (
    "%TEMP%\xpp-python-setup.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1 Include_pip=1
    del "%TEMP%\xpp-python-setup.exe" >nul 2>&1
  )
)
call :find_python
if not defined PYTHON_CMD (
  echo  [X] Python still missing. Please install it from python.org and rerun.
  exit /b 1
)
:python_ok
echo  [+] Python: %PYTHON_CMD%

rem ------------------------------------------------------------
rem  2) VS CODE (editor + run button + file icons)
rem ------------------------------------------------------------
echo.
echo  [2/4]  VS Code
set "CODE_CMD="
where code >nul 2>&1 && set "CODE_CMD=code"
if not defined CODE_CMD if exist "%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd" set "CODE_CMD=%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd"
if not defined CODE_CMD if exist "%ProgramFiles%\Microsoft VS Code\bin\code.cmd" set "CODE_CMD=%ProgramFiles%\Microsoft VS Code\bin\code.cmd"

if not defined CODE_CMD (
  echo  [X++] VS Code not found - installing via winget...
  winget install -e --id Microsoft.VisualStudioCode --accept-package-agreements --accept-source-agreements >nul 2>&1
  if exist "%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd" set "CODE_CMD=%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd"
)
if defined CODE_CMD (echo  [+] VS Code: %CODE_CMD%) else (echo  [i] VS Code later? Just rerun setup after installing it.)

rem ------------------------------------------------------------
rem  3) C++ COMPILER (g++ - only needed for xppvm/ZJIT)
rem ------------------------------------------------------------
echo.
echo  [3/4]  C++ compiler (g++)
set "GXX="
where g++ >nul 2>&1 && set "GXX=g++"
if not defined GXX if exist "C:\msys64\mingw64\bin\g++.exe" set "GXX=C:\msys64\mingw64\bin\g++.exe"
if not defined GXX if exist "C:\MinGW\bin\g++.exe" set "GXX=C:\MinGW\bin\g++.exe"

if not defined GXX (
  echo  [X++] Installing MinGW-w64 g++ via MSYS2 (winget)...
  winget install -e --id MSYS2.MSYS2 --accept-package-agreements --accept-source-agreements >nul 2>&1
  if exist "C:\msys64\usr\bin\bash.exe" (
    echo  [X++] Installing gcc package inside MSYS2 (one time, may take a bit)...
    "C:\msys64\usr\bin\bash.exe" -lc "pacman -Sy --needed --noconfirm mingw-w64-x86_64-gcc" >nul 2>&1
    if exist "C:\msys64\mingw64\bin\g++.exe" set "GXX=C:\msys64\mingw64\bin\g++.exe"
  )
)
if defined GXX (echo  [+] g++: %GXX%) else (echo  [i] no g++ yet - XCOM/XITR still work; ZJIT needs it.)

rem ------------------------------------------------------------
rem  4) RUN THE UNIVERSAL SETUP (builds VM, installs everything,
rem     registers icons, PATH, VS Code theme, run button)
rem ------------------------------------------------------------
echo.
echo  [4/4]  Installing X++ (VM, commands, icons, VS Code)...
"%PYTHON_CMD%" tools\xpp_setup.py --all
if errorlevel 1 (
  echo.
  echo  [X] Setup hit an error. Rerun; the log above shows what failed.
  pause
  exit /b 1
)

echo.
echo ============================================================
echo   DONE! Open a NEW terminal and type:
echo
echo       x run examples\hello.xp
echo       x run examples\fib_fast.xp --mode ZJIT
echo
echo   VS Code: open this folder, play button = Run.
echo   .xp files now show the X++ logo.
echo ============================================================
pause
exit /b 0

rem ------------------------------------------------------------
:find_python
set "PYTHON_CMD="
for %%P in ("py.exe" "python.exe") do (
  if not defined PYTHON_CMD (
    where %%P >nul 2>&1
    if not errorlevel 1 (
      %%~nP -c "import sys; sys.exit(0 if sys.version_info>=(3,9) else 1)" >nul 2>&1
      if not errorlevel 1 (
        for /f "delims=" %%V in ('%%~nP -c "import sys;print(sys.executable)" 2^>nul') do set "PYTHON_CMD=%%V"
      )
    )
  )
)
rem freshly installed Pythons are not on this session's PATH yet
if not defined PYTHON_CMD (
  for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Launcher\py.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
  ) do (
    if not defined PYTHON_CMD if exist %%P (
      %%P -c "import sys; sys.exit(0 if sys.version_info>=(3,9) else 1)" >nul 2>&1
      if not errorlevel 1 for /f "delims=" %%V in ('%%P -c "import sys;print(sys.executable)" 2^>nul') do set "PYTHON_CMD=%%V"
    )
  )
)
exit /b 0
