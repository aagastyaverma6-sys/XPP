# Build Xite.exe – Windows standalone
# Run on Windows: python build_exe.py
import PyInstaller.__main__, sys, os
# icon optional
icon = "xite.ico" if os.path.exists("xite.ico") else None
args = [
    "xite.py",
    "--name=Xite",
    "--onefile",
    "--windowed",
    "--noconfirm",
    "--clean",
    "--collect-all=lark",
    "--add-data=xpp_core;xpp_core",
    "--add-data=examples;examples",
]
if icon: args.append(f"--icon={icon}")
# version info
PyInstaller.__main__.run(args)
print("\nBuilt: dist/Xite.exe")
