#!/usr/bin/env bash
# ============================================================
#  OpenEVSE Firmware Flasher  -  macOS / Linux launcher
#  Run:  bash run.sh
# ============================================================

set -e

# ── Find Python 3 ────────────────────────────────────────────
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

if [ -z "$PYTHON" ]; then
    echo ""
    echo "  Python 3 not found."
    echo "  macOS:  brew install python  (or https://www.python.org)"
    echo "  Ubuntu: sudo apt install python3"
    echo "  Fedora: sudo dnf install python3"
    echo ""
    exit 1
fi

echo "Using $($PYTHON --version)"

# ── Linux: remind about USBasp udev rules ────────────────────
if [[ "$(uname)" == "Linux" ]]; then
    if ! groups | grep -qwE "plugdev|dialout"; then
        echo ""
        echo "  Note: USBasp on Linux may need a udev rule."
        echo "  Create /etc/udev/rules.d/99-usbasp.rules containing:"
        echo '    SUBSYSTEM=="usb", ATTR{idVendor}=="16c0", ATTR{idProduct}=="05dc", MODE="0666"'
        echo "  Then run: sudo udevadm control --reload-rules"
        echo ""
    fi
fi

# ── Launch ───────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Starting OpenEVSE Firmware Flasher..."
"$PYTHON" "$SCRIPT_DIR/openevse_flasher.py"
