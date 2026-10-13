#!/usr/bin/env bash
# ============================================================
#  OpenEVSE Firmware Flasher - macOS / Linux Build Script
#  Produces a standalone program (no Python needed to run it):
#    macOS:  OpenEVSE_Flasher-macos.zip   (OpenEVSE Flasher.app)
#    Linux:  OpenEVSE_Flasher-linux.tar.gz
#  Requires:  Python 3.8+ with tkinter, pip, and avrdude
#             (brew install avrdude / sudo apt install avrdude)
#  avrdude and its libraries are packed inside the program.
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
"$PYTHON" -c "import tkinter" 2>/dev/null || {
    echo " ERROR: tkinter missing (Debian/Ubuntu: sudo apt install python3-tk)"; exit 1; }

if [ ! -f avrdude/avrdude ] && ! command -v avrdude &>/dev/null; then
    echo " ERROR: avrdude not found."
    echo "   macOS:  brew install avrdude"
    echo "   Linux:  sudo apt install avrdude"
    exit 1
fi

# ── Install / upgrade PyInstaller ────────────────────────────
echo ""
echo " Installing PyInstaller..."
"$PYTHON" -m pip install --upgrade pyinstaller --quiet

# ── Clean previous build ─────────────────────────────────────
rm -rf dist build

# ── Build executable ─────────────────────────────────────────
echo ""
echo " Building executable..."
"$PYTHON" -m PyInstaller --noconfirm openevse_flasher.spec

# ── Package ──────────────────────────────────────────────────
echo ""
if [ "$PLATFORM" = "macos" ]; then
    OUT="OpenEVSE_Flasher-macos.zip"
    rm -f "$OUT"
    ditto -c -k --keepParent "dist/OpenEVSE Flasher.app" "$OUT"
else
    OUT="OpenEVSE_Flasher-linux.tar.gz"
    rm -rf pkg && mkdir -p pkg/OpenEVSE_Flasher
    cp dist/OpenEVSE_Flasher pkg/OpenEVSE_Flasher/
    chmod +x pkg/OpenEVSE_Flasher/OpenEVSE_Flasher
    tar -czf "$OUT" -C pkg OpenEVSE_Flasher
    rm -rf pkg
fi

echo " Done!  Output: $OUT"
echo ""
