# Build Xite.exe – Windows standalone
# Run on Windows: python build_exe.py
import PyInstaller.__main__, sys, os
# icon optional
icon = "icons/xpp.ico" if os.path.exists("icons/xpp.ico") else None
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
    "--add-data=icons;icons",
]
if icon: args.append(f"--icon={icon}")
# version info
PyInstaller.__main__.run(args)
print("\nBuilt: dist/Xite.exe")
