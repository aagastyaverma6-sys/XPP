@echo off
echo ====================================================
echo             X++ AUTOMATED SYSTEM SETUP               
echo ====================================================
echo.

set "LANG_PATH=%~dp0"
set "LANG_PATH=%LANG_PATH:~0,-1%"

echo [+] Detecting installation path: %LANG_PATH%

echo [+] Registering 'x' command to your system environment...
powershell -Command "[Environment]::SetEnvironmentVariable('Path', [Environment]::GetEnvironmentVariable('Path', 'User') + ';%LANG_PATH%', 'User')"

echo.
echo ====================================================
echo             OPENROUTER API KEY CONFIGURATION         
echo ====================================================
echo.
echo You can get a free key from https://openrouter.ai
echo.
set /p "USER_KEY=Paste your OpenRouter API Key here and press Enter: "

if not "%USER_KEY%"=="" (
    setx OPENROUTER_API_KEY "%USER_KEY%" >nul
    echo [+] API Key successfully saved to your system!
) else (
    echo [!] No key entered. You will need to set up OPENROUTER_API_KEY manually later.
)

echo.
echo ====================================================
echo [+] SUCCESS! Installation complete.
echo [!] PLEASE RESTART ANY OPEN TERMINALS OR VS CODE.
echo ====================================================
pause