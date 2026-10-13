# OpenEVSE Firmware Flasher

A simple graphical tool for loading firmware onto OpenEVSE AVR controller boards. No command-line knowledge required, and **nothing else to install** — the download includes everything it needs.

---

## What You Need

- A Windows, macOS, or Linux computer
- An **OpenEVSE Programmer** (USBasp) and its USB cable
- An internet connection (to fetch firmware from GitHub)

---

## Download

Go to the **[latest release](https://github.com/OpenEVSE/openevse_avr_flasher/releases/latest)** and download the file for your computer:

| Your computer | Download |
|---|---|
| Windows 10 / 11 | `OpenEVSE_Flasher-windows.exe` |
| Mac with Apple chip (M1, M2, M3, M4…) | `OpenEVSE_Flasher-macos-apple-silicon.zip` |
| Mac with Intel chip | `OpenEVSE_Flasher-macos-intel.zip` |
| Linux (64-bit PC) | `OpenEVSE_Flasher-linux-x86_64.tar.gz` |

Not sure which Mac you have? Click the Apple menu  → **About This Mac** and look at **Chip** (Apple) or **Processor** (Intel).

---

## Starting the App

### Windows
1. Double-click **`OpenEVSE_Flasher-windows.exe`**.
2. The first time, Windows may show **"Windows protected your PC"**. Click **More info** → **Run anyway**.
   (The app is safe but is not code-signed, so Windows does not recognise it yet.)

### macOS
1. Double-click the downloaded `.zip` to unzip it. You get **OpenEVSE Flasher**.
2. Drag **OpenEVSE Flasher** into your **Applications** folder (optional).
3. The first time, macOS will say it *cannot verify the developer*:
   - **macOS 15 (Sequoia) and later:** click **Done**, then open **System Settings → Privacy & Security**, scroll down and click **Open Anyway** next to *"OpenEVSE Flasher was blocked"*, then confirm.
   - **macOS 14 and earlier:** right-click (or Control-click) the app, choose **Open**, then click **Open** again.

   You only need to do this once.

### Linux
1. Extract the download (double-click it in your file manager, or `tar -xzf OpenEVSE_Flasher-linux-x86_64.tar.gz`).
2. Open the **OpenEVSE_Flasher** folder and double-click **OpenEVSE_Flasher**, or run `./OpenEVSE_Flasher` in a terminal.
   If nothing happens, right-click it → **Properties** → **Permissions** and tick **Allow executing file as program**.

---

## USB Driver

### Windows

The OpenEVSE programmer requires the **WinUSB** driver on Windows. The app checks this automatically on startup.

- **Green status** — driver is installed, ready to flash
- **Orange status** — driver missing or needs updating

Click **Install Driver** to open the Zadig driver installer (included in the app). A step-by-step popup will guide you through the process. The installer closes automatically when done.

### Linux

A USB permission rule is needed so the app can talk to the programmer. The app checks for this on startup and shows an **Install Driver** button if the rule is missing. Clicking it installs the rule automatically (you will be prompted for your password). Unplug and replug the programmer afterwards.

To install manually:
```bash
sudo tee /etc/udev/rules.d/99-usbasp.rules << 'EOF'
SUBSYSTEM=="usb", ATTR{idVendor}=="16c0", ATTR{idProduct}=="05dc", MODE="0666", GROUP="plugdev"
EOF
sudo udevadm control --reload-rules
```

### macOS

No driver is needed.

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

To use **Write Defaults**, place `eeprom_24.bin` in the same folder as the app (next to the `.exe`, next to **OpenEVSE Flasher.app**, or next to the Linux program).

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

**Windows: "Windows protected your PC"**
Click **More info** → **Run anyway**. See [Starting the App](#starting-the-app).

**macOS: "cannot be opened because the developer cannot be verified" / "OpenEVSE Flasher was blocked"**
Use **System Settings → Privacy & Security → Open Anyway** (macOS 15+), or right-click → **Open** (macOS 14 and earlier).

**macOS: "not supported on this type of Mac"**
You downloaded the Apple-chip version on an Intel Mac. Download `OpenEVSE_Flasher-macos-intel.zip` instead. (The Intel version also runs on Apple-chip Macs.)

**macOS: "OpenEVSE Flasher is damaged and can't be opened"**
Usually the zip was unpacked by a tool other than Finder. Re-download it and unzip by double-clicking in Finder. If it still happens, open **Terminal** and run:
```bash
xattr -dr com.apple.quarantine "/Applications/OpenEVSE Flasher.app"
```

**Linux: app does not start**
Make sure the file is allowed to run as a program (see [Linux](#linux)). Run `./OpenEVSE_Flasher` from a terminal to see any error message.

**"USB Driver not found" (Windows)**
Click **Install Driver** and follow the popup instructions. Make sure the programmer is plugged in before clicking Install Driver in Zadig.

**Flash fails with "initialization failed"**
- Check the USB cable and the 10-pin to 6-pin connector seating
- On Windows, confirm the driver status shows green before flashing
- On Linux, confirm the udev rule is installed and try unplugging and replugging the programmer

**No releases listed**
Check your internet connection and click **Refresh**.

---

## For Developers

### Running from source

Requires **Python 3.8+** with tkinter (Debian/Ubuntu: `sudo apt install python3-tk`) and avrdude.

- **Windows:** double-click `run.bat` (uses `avrdude/avrdude.exe` from this repo)
- **macOS / Linux:** install avrdude (`brew install avrdude`, `sudo apt install avrdude`, `sudo dnf install avrdude`), then run `bash run.sh`

The app looks for avrdude in the `avrdude/` subfolder first, then falls back to any system-installed version.

### Folder structure

```
openevse_avr_flasher/
├── openevse_flasher.py      # Main application
├── openevse_flasher.spec    # PyInstaller build recipe (all platforms)
├── run.bat / run.sh         # Run from source
├── build.bat / build.sh     # Build a standalone executable locally
├── avrdude/
│   ├── avrdude.exe          # avrdude binary (Windows)
│   └── avrdude.conf         # its config file
├── drivers/
│   ├── zadig-2.9.exe        # WinUSB driver installer (Windows)
│   ├── zadig.ini            # Pre-configured driver settings
│   └── usbasp.cfg           # Zadig device preset
├── scripts/
│   └── smoke_test.py        # CI checks for the built executables
└── eeprom_24.bin            # Optional — EEPROM defaults file
```

### Building the executables

The standalone programs are built with [PyInstaller](https://pyinstaller.org/) from `openevse_flasher.spec`, which packs Python, tkinter, avrdude (with its `avrdude.conf` and shared libraries) and, on Windows, the Zadig driver installer into a single download.

- **Windows:** `build.bat` → `OpenEVSE_Flasher-windows.exe`
- **macOS:** `brew install avrdude`, then `bash build.sh` → `OpenEVSE_Flasher-macos.zip` (for the Mac type you build on)
- **Linux:** `sudo apt install avrdude python3-tk`, then `bash build.sh` → `OpenEVSE_Flasher-linux.tar.gz`. Build on an older distro for the widest compatibility.

Files placed next to the built program (`avrdude/`, `drivers/`, `eeprom_24.bin`) override the built-in copies.

### Releases

The [Build & Release](.github/workflows/release.yml) workflow builds all four downloads, smoke-tests each one (the app launches, and on macOS the bundled avrdude runs with Homebrew's copy removed), and attaches them to the GitHub Release.

- **New release:** `git tag v1.1.0 && git push origin v1.1.0`
- **Add or refresh downloads on an existing release:** *Actions → Build & Release → Run workflow*, and enter the tag (e.g. `v1.0.0`)

Pushes to `main` and pull requests run the same builds and tests without publishing.
