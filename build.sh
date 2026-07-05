#!/usr/bin/env bash
# ============================================================
#  OpenEVSE Firmware Flasher - macOS / Linux Build Script
#  Produces:  OpenEVSE_Flasher-<platform>.zip
#  Requires:  Python 3.7+, pip
# ============================================================
set -e

PLATFORM=""
case "$(uname -s)" in
    Darwin) PLATFORM="macos" ;;
    Linux)  PLATFORM="linux" ;;
    *)      echo "Unsupported platform: $(uname -s)"; exit 1 ;;
esac

echo ""
echo " OpenEVSE Firmware Flasher - Build ($PLATFORM)"
echo " ================================================"
echo ""

# ── Find Python ──────────────────────────────────────────────
PYTHON=""
for candidate in python3 python; do
    if command -v "$candidate" &>/dev/null; then
        VER=$("$candidate" -c "import sys; print(sys.version_info.major)")
        if [ "$VER" = "3" ]; then
            PYTHON="$candidate"
            break
        fi
    fi
done
[ -z "$PYTHON" ] && { echo " ERROR: Python 3 not found."; exit 1; }
echo " Using $($PYTHON --version)"

# ── Install / upgrade PyInstaller ────────────────────────────
echo ""
echo " Installing PyInstaller..."
"$PYTHON" -m pip install --upgrade pyinstaller --quiet

# ── Clean previous build ─────────────────────────────────────
rm -rf dist build release

# ── Build executable ─────────────────────────────────────────
echo ""
echo " Building executable..."
"$PYTHON" -m PyInstaller openevse_flasher.spec

# ── Assemble release folder ──────────────────────────────────
echo ""
echo " Assembling release folder..."
mkdir -p release/avrdude release/drivers

cp dist/OpenEVSE_Flasher release/
chmod +x release/OpenEVSE_Flasher

if [ -f "avrdude/avrdude" ]; then
    cp avrdude/avrdude release/avrdude/
    chmod +x release/avrdude/avrdude
    echo " Bundled avrdude from local avrdude/ folder."
else
    # Try system avrdude as fallback
    AVRDUDE_BIN=$(command -v avrdude 2>/dev/null || true)
    if [ -n "$AVRDUDE_BIN" ]; then
        cp "$AVRDUDE_BIN" release/avrdude/avrdude
        chmod +x release/avrdude/avrdude
        echo " Bundled system avrdude from $AVRDUDE_BIN"
    else
        echo " NOTE: avrdude not found -- add it to avrdude/ before distributing."
    fi
fi

[ -f drivers/zadig.ini  ] && cp drivers/zadig.ini  release/drivers/
[ -f drivers/usbasp.cfg ] && cp drivers/usbasp.cfg release/drivers/
[ -f eeprom_24.bin      ] && cp eeprom_24.bin       release/
[ -f README.md          ] && cp README.md            release/

# ── Zip release ──────────────────────────────────────────────
ZIP_NAME="OpenEVSE_Flasher-${PLATFORM}.zip"
echo ""
echo " Creating ${ZIP_NAME}..."
cd release && zip -r "../${ZIP_NAME}" . && cd ..

echo ""
echo " Done!  Output: ${ZIP_NAME}"
echo ""
