# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for OpenEVSE Firmware Flasher
# Build:  pyinstaller openevse_flasher.spec
#
# Produces a standalone program that needs no Python install:
#   Windows  dist/OpenEVSE_Flasher.exe        (single file)
#   Linux    dist/OpenEVSE_Flasher            (single file)
#   macOS    dist/OpenEVSE Flasher.app        (application bundle)
#
# avrdude (and its matching avrdude.conf) is packed inside the program:
#   Windows       avrdude/avrdude.exe + avrdude/avrdude.conf from this repo
#   macOS/Linux   avrdude/avrdude if present, otherwise the system avrdude
#                 (Homebrew / apt). Its shared libraries are collected too,
#                 so the target machine does not need avrdude installed.

import os
import shutil
import sys

NAME     = 'OpenEVSE_Flasher'
APP_NAME = 'OpenEVSE Flasher'
WINDOWS  = sys.platform == 'win32'
MACOS    = sys.platform == 'darwin'

binaries = []
datas    = []


def find_avrdude():
    """Return (avrdude binary, matching avrdude.conf or None)."""
    if WINDOWS:
        exe  = os.path.join('avrdude', 'avrdude.exe')
        conf = os.path.join('avrdude', 'avrdude.conf')
        if not os.path.isfile(exe):
            sys.exit('ERROR: avrdude/avrdude.exe not found')
        return exe, conf if os.path.isfile(conf) else None

    local = os.path.join('avrdude', 'avrdude')
    if os.path.isfile(local):
        conf = os.path.join('avrdude', 'avrdude.conf')
        return local, conf if os.path.isfile(conf) else None

    exe = shutil.which('avrdude')
    if not exe:
        sys.exit('ERROR: avrdude not found -- install it (brew / apt) '
                 'or place it in avrdude/')
    real = os.path.realpath(exe)
    # Same conf the system avrdude uses: <prefix>/etc/avrdude.conf. Check the
    # PATH prefix before the resolved one: Homebrew keeps the conf in
    # $(brew --prefix)/etc, not in the Cellar the binary resolves to.
    prefixes = [os.path.dirname(os.path.dirname(p)) for p in (exe, real)]
    for conf in [os.path.join(p, 'etc', 'avrdude.conf') for p in prefixes] + \
                ['/opt/homebrew/etc/avrdude.conf', '/usr/local/etc/avrdude.conf',
                 '/etc/avrdude.conf']:
        if os.path.isfile(conf):
            return real, conf
    return real, None


avrdude_exe, avrdude_conf = find_avrdude()
print('Bundling avrdude: %s (conf: %s)' % (avrdude_exe, avrdude_conf))
binaries.append((avrdude_exe, 'avrdude'))
if not avrdude_conf:
    sys.exit('ERROR: avrdude.conf not found -- the bundled avrdude '
             'would not start on other machines')
datas.append((avrdude_conf, 'avrdude'))

if WINDOWS:
    for f in ('zadig-2.9.exe', 'zadig.ini', 'usbasp.cfg'):
        p = os.path.join('drivers', f)
        if os.path.isfile(p):
            datas.append((p, 'drivers'))

if os.path.isfile('eeprom_24.bin'):
    datas.append(('eeprom_24.bin', '.'))


a = Analysis(
    ['openevse_flasher.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['test', 'unittest'],
    noarchive=False,
)

pyz = PYZ(a.pure)

if MACOS:
    # macOS: a normal double-clickable .app (onedir inside the bundle)
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=NAME,
        debug=False,
        strip=False,
        upx=False,
        console=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
    coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name=NAME)
    app = BUNDLE(
        coll,
        name=APP_NAME + '.app',
        icon=None,
        bundle_identifier='org.openevse.flasher',
        info_plist={
            'CFBundleDisplayName': APP_NAME,
            'CFBundleShortVersionString': os.environ.get('APP_VERSION') or '1.0.0',
            'NSHighResolutionCapable': True,
        },
    )
else:
    # Windows / Linux: one self-contained executable file
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name=NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,           # UPX-packed exes trigger antivirus false positives
        runtime_tmpdir=None,
        console=False,       # no terminal window
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=None,           # replace with 'icon.ico' if available
    )
