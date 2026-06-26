@echo off
echo ====================================================
echo X++ v0.3 AUTOMATED SYSTEM SETUP
echo ====================================================
echo.
set "LANG_PATH=%~dp0"
set "LANG_PATH=%LANG_PATH:~0,-1%"
echo [+] Detecting installation path: %LANG_PATH%
echo [+] Installing Python dependencies...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install lark requests >nul 2>&1
echo [+] Registering 'x' command...
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "CURPATH=%%b"
echo %CURPATH% | find /i "%LANG_PATH%" >nul
if errorlevel 1 (
  powershell -Command "[Environment]::SetEnvironmentVariable('Path', [Environment]::GetEnvironmentVariable('Path','User') + ';%LANG_PATH%', 'User')"
  echo     PATH updated.
) else (
  echo     PATH already contains X++.
)
echo.
echo ====================================================
echo OPENROUTER API KEY CONFIGURATION (for RNM=ITR AI mode)
echo ====================================================
echo.
echo You can get a free key from https://openrouter.ai
echo (Skip if you only use XCOM / XITR strict modes)
echo.
set /p "USER_KEY=Paste your OpenRouter API Key [Enter to skip]: "
if not "%USER_KEY%"=="" (
  setx OPENROUTER_API_KEY "%USER_KEY%" >nul
  echo [+] API Key saved to OPENROUTER_API_KEY
) else (
  echo [!] Skipped – set OPENROUTER_API_KEY manually later if needed.
)
echo.
echo ====================================================
echo VS CODE SYNTAX HIGHLIGHTING
echo ====================================================
set "VSCODE_EXT_DIR=%USERPROFILE%\.vscode\extensions\xpp-lang-0.3.0"
if not exist "%VSCODE_EXT_DIR%" mkdir "%VSCODE_EXT_DIR%"
if not exist "%VSCODE_EXT_DIR%\syntaxes" mkdir "%VSCODE_EXT_DIR%\syntaxes"
copy /Y "%LANG_PATH%\package.json" "%VSCODE_EXT_DIR%\package.json" >nul
copy /Y "%LANG_PATH%\xp.tmLanguage.json" "%VSCODE_EXT_DIR%\syntaxes\xp.tmLanguage.json" >nul
copy /Y "%LANG_PATH%\language-configuration.json" "%VSCODE_EXT_DIR%\language-configuration.json" >nul 2>&1
echo [+] Syntax highlighting installed to: %VSCODE_EXT_DIR%
echo.
echo ====================================================
echo [+] SUCCESS! X++ v0.3 installed.
echo.
echo   x run examples\hello.xp --mode XITR
echo   x run examples\fib.xp --mode XCOM
echo   x run examples\ai_demo.xp --mode ITR
echo.
echo [!] PLEASE RESTART ANY OPEN TERMINALS OR VS CODE.
echo ====================================================
pause
