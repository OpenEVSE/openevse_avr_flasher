# OpenEVSE Firmware Flasher

A simple graphical tool for loading firmware onto OpenEVSE AVR controller boards. No command-line knowledge required.

---

## Requirements

- **Python 3.7 or later** — [python.org/downloads](https://www.python.org/downloads/)
  - Windows: tick **"Add Python to PATH"** during installation
- **OpenEVSE Programmer** (USBasp) connected via USB
- Internet connection (to fetch firmware from GitHub)

---

## Folder Structure

```
openevse_flasher/
├── openevse_flasher.py   # Main application
├── run.bat               # Windows launcher — double-click to start
├── run.sh                # macOS / Linux launcher
├── avrdude/
│   └── avrdude.exe       # avrdude binary (Windows)
│   └── avrdude           # avrdude binary (macOS/Linux)
├── drivers/
│   └── zadig-2.9.exe     # Downloaded automatically on first use (Windows)
│   └── zadig.ini         # Pre-configured driver settings
└── eeprom_24.bin         # Optional — EEPROM defaults file
```

---

## Getting Started

### Windows
Double-click **`run.bat`**.

### macOS / Linux
Open a terminal in the folder and run:
```bash
bash run.sh
```

---

## USB Driver (Windows only)

The OpenEVSE programmer requires the **WinUSB** driver on Windows. The app checks this automatically on startup.

- **Green status** — driver is installed, ready to flash
- **Orange status** — driver missing or needs updating

Click **Install Driver** to open the Zadig driver installer. A step-by-step popup will guide you through the process. The installer closes automatically when done.

Linux and macOS do not require a driver.

---

## Flashing Firmware

1. Plug in the OpenEVSE programmer via USB
2. Connect the programmer to the OpenEVSE controller board (10-pin to 6-pin cable)
3. Select a **Release** from the dropdown — the latest is selected automatically
4. Select the **Firmware file** (`.hex`)
5. Choose options:
   - **Burn fuse bits** — programs the correct fuse settings for the ATmega328P (recommended, on by default)
   - **Write Defaults** — writes EEPROM defaults from `eeprom_24.bin` if the file is present (on by default)
6. Click **Flash Firmware**

The output log shows progress. When complete you will see:

```
Done! Disconnect and reconnect the device.
```

---

## Using a Local Firmware File

Click **Browse local file...** to select a `.hex` file from your computer instead of downloading one from GitHub. Fuse and EEPROM options still apply.

---

## Flash Sequence

When all options are enabled, the tool runs three operations in order:

1. **Flash firmware** — writes the `.hex` file to program flash
2. **Burn fuse bits** — sets `lfuse=0xFF`, `hfuse=0xDF`, `efuse=0xFF`
3. **Write Defaults** — writes `eeprom_24.bin` to EEPROM (if file is present)

Each step is logged separately. Any failure stops the sequence and reports the error.

---

## avrdude Setup

The app looks for avrdude in the `avrdude/` subfolder first, then falls back to any system-installed version.

**Windows** — place `avrdude.exe` (and its config file if required) in the `avrdude/` folder.

**macOS** — install via Homebrew:
```bash
brew install avrdude
```

**Linux** — install via package manager:
```bash
sudo apt install avrdude        # Debian/Ubuntu
sudo dnf install avrdude        # Fedora
```

---

## Linux USB Access

On Linux, a udev rule is needed to allow non-root USB access. The app checks for this on startup and shows an **Install Driver** button if the rule is missing. Clicking it installs the rule automatically (you will be prompted for your password).

To install manually:
```bash
sudo tee /etc/udev/rules.d/99-usbasp.rules << 'EOF'
SUBSYSTEM=="usb", ATTR{idVendor}=="16c0", ATTR{idProduct}=="05dc", MODE="0666", GROUP="plugdev"
EOF
sudo udevadm control --reload-rules
```

---

## Programmer Specs

| Item | Value |
|---|---|
| Programmer | USBasp |
| MCU | ATmega328P |
| Interface | USB (no serial port needed) |
| USB VID/PID | 16C0 / 05DC |
| Firmware source | github.com/OpenEVSE/open_evse |

---

## Troubleshooting

**App does not start**
Confirm Python 3 is installed and added to PATH. Run `python --version` in a terminal to check.

**"avrdude not found"**
Place the avrdude binary in the `avrdude/` folder next to `openevse_flasher.py`.

**"USB Driver not found" (Windows)**
Click **Install Driver** and follow the popup instructions. Make sure the programmer is plugged in before clicking Install Driver in Zadig.

**Flash fails with "initialization failed"**
- Check the USB cable and the 10-pin to 6-pin connector seating
- On Windows, confirm the driver status shows green before flashing
- On Linux, confirm the udev rule is installed and try unplugging and replugging the programmer

**No releases listed**
Check your internet connection and click **Refresh**.
