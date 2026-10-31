@echo off
echo ========================================
echo  Xite – Build Windows EXE
echo  X++ v0.3.1
echo ========================================
pip install pyinstaller lark requests -q
python build_exe.py
echo.
echo Done! Check dist\Xite.exe
pause
