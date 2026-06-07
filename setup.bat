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
echo             VS CODE SYNTAX HIGHLIGHTING              
echo ====================================================
set "VSCODE_EXT_DIR=%USERPROFILE%\.vscode\extensions\x-plus-plus-lang"
if not exist "%VSCODE_EXT_DIR%\syntaxes" mkdir "%VSCODE_EXT_DIR%\syntaxes"

echo [+] Installing VS Code extension to: %VSCODE_EXT_DIR%

(
echo {
echo   "name": "x-plus-plus-lang",
echo   "displayName": "X++ Hyperlang Support",
echo   "version": "0.1.0",
echo   "engines": { "vscode": "^1.50.0" },
echo   "contributes": {
echo     "languages": [{"id": "hyperlang", "aliases": ["X++"], "extensions": [".xp"]}],
echo     "grammars": [{"language": "hyperlang", "scopeName": "source.xp", "path": "./syntaxes/xp.tmLanguage.json"}]
echo   }
echo }
) > "%VSCODE_EXT_DIR%\package.json"

(
echo {
echo   "name": "X++ Hyperlang",
echo   "scopeName": "source.xp",
echo   "patterns": [
echo     { "name": "keyword.control.xp", "match": "\\b(USE MODEL|RNM=ITR)\\b" },
echo     { "name": "entity.name.section.xp", "match": "^\\s*(STEP\\s+\\d+|Stanza\\s+[IVXLC]+:?)" },
echo     { "name": "variable.other.constant.xp", "match": "\\b(RED|GREEN|BLUE|SKY_BLUE|GRASS_GREEN|BROWN)\\b" },
echo     { "name": "string.quoted.double.xp", "begin": "\"", "end": "\"" },
echo     { "name": "keyword.other.xp", "match": "\\b(TAKE|MAKE|ADD|CHANGE|VICTORY)\\b" }
echo   ]
echo }
) > "%VSCODE_EXT_DIR%\syntaxes\xp.tmLanguage.json"

echo [+] Syntax highlighting installed!

echo.
echo ====================================================
echo [+] SUCCESS! Installation complete.
echo [!] PLEASE RESTART ANY OPEN TERMINALS OR VS CODE.
echo ====================================================
pause
