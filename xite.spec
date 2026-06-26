# -*- mode: python ; coding: utf-8 -*-
# Xite – PyInstaller spec for Windows .exe
# Build: pyinstaller xite.spec
block_cipher = None

a = Analysis(
    ['xite.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('xpp_core', 'xpp_core'),
        ('examples', 'examples'),
        ('xp.tmLanguage.json', '.'),
        ('language-configuration.json', '.'),
    ],
    hiddenimports=['lark', 'lark.parsers', 'lark.lexer', 'requests', 'xpp_core', 'xpp_core.cli', 'xpp_core.fast_transpiler', 'xpp_core.strict_compiler', 'xpp_core.strict_vm', 'xpp_core.ast_parser', 'xpp_core.ai_engine'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Xite',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='xite.ico'  # optional – add your own .ico, else remove this line
)
