# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for OpenEVSE Firmware Flasher
# Build:  pyinstaller openevse_flasher.spec

a = Analysis(
    ['openevse_flasher.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['_tkinter', 'test', 'unittest'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='OpenEVSE_Flasher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,       # no terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,           # replace with 'icon.ico' (Windows) or 'icon.icns' (macOS) if available
)
