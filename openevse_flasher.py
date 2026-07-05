#!/usr/bin/env python3
"""
OpenEVSE AVR Firmware Flasher
Downloads and flashes OpenEVSE controller firmware via USBasp.
Programmer=usbasp, MCU=atmega328p. No serial port needed.
avrdude must be placed in an 'avrdude/' sub-folder next to this script.
Firmware fetched from: https://github.com/OpenEVSE/open_evse/releases
"""

import sys, os, subprocess, threading, json, tempfile, platform, zipfile, urllib.request
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
AVR_REPO        = "OpenEVSE/open_evse"
GH_API          = "https://api.github.com/repos/{repo}/releases"
MCU             = "atmega328p"
PROGRAMMER      = "usbasp"
USBASP_VID      = "16c0"
USBASP_PID      = "05dc"
ZADIG_URL       = "https://github.com/pbatard/libwdi/releases/download/v1.5.1/zadig-2.9.exe"
ZADIG_FILENAME  = "zadig-2.9.exe"
EEPROM_FILENAME = "eeprom_24.bin"
FUSE_ARGS       = ["-Ulfuse:w:0xFF:m", "-Uhfuse:w:0xDF:m", "-Uefuse:w:0xFF:m"]
UDEV_RULE_PATH  = "/etc/udev/rules.d/99-usbasp.rules"
UDEV_RULE_TEXT  = (
    "# USBasp programmer\n"
    'SUBSYSTEM=="usb", ATTR{idVendor}=="16c0", '
    'ATTR{idProduct}=="05dc", MODE="0666", GROUP="plugdev"\n'
)
ZADIG_INI = (
    "# Zadig config for OpenEVSE Flasher\n"
    "[general]\n"
    "  advanced_mode = false\n"
    "  exit_on_success = true\n"
    "  log_level = 1\n\n"
    "[device]\n"
    "  list_all = true\n"
    "  include_hubs = false\n"
    "  trim_whitespaces = true\n\n"
    "[driver]\n"
    "  default_driver = 0\n"
    "  extract_only = false\n"
)

BLUE    = "#1565C0"
LBLUE   = "#1E88E5"
BG      = "#F5F5F5"
CONS_BG = "#1e1e1e"
CONS_FG = "#d4d4d4"
GREEN   = "#2E7D32"
ORANGE  = "#E65100"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def script_dir():
    return os.path.dirname(os.path.abspath(__file__))

def find_avrdude():
    exe     = "avrdude.exe" if platform.system() == "Windows" else "avrdude"
    bundled = os.path.join(script_dir(), "avrdude", exe)
    if os.path.isfile(bundled):
        return bundled
    import shutil
    return shutil.which("avrdude")

def find_zadig():
    for name in (ZADIG_FILENAME, "zadig.exe"):
        p = os.path.join(script_dir(), "drivers", name)
        if os.path.isfile(p):
            return p
    return None

def find_eeprom():
    p = os.path.join(script_dir(), EEPROM_FILENAME)
    return p if os.path.isfile(p) else None

def ensure_zadig_ini(drivers_dir):
    with open(os.path.join(drivers_dir, "zadig.ini"), "w") as f:
        f.write(ZADIG_INI)

def check_usbasp_driver_windows():
    """Returns: 'winusb' | 'other' | 'missing' | 'unknown'"""
    try:
        ps = (
            "Get-PnpDevice | "
            "Where-Object { $_.InstanceId -match 'VID_16C0.*PID_05DC' } | "
            "Select-Object -ExpandProperty DriverProvider"
        )
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
            capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            out = r.stdout.strip().lower()
            if not out:
                return "missing"
            if "microsoft" in out or "winusb" in out:
                return "winusb"
            return "other"
    except Exception:
        pass
    try:
        import winreg
        path = r"SYSTEM\CurrentControlSet\Enum\USB\VID_16C0&PID_05DC"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
            for i in range(winreg.QueryInfoKey(key)[0]):
                sub = winreg.EnumKey(key, i)
                try:
                    with winreg.OpenKey(key, sub) as sk:
                        svc, _ = winreg.QueryValueEx(sk, "Service")
                        return "winusb" if "winusb" in svc.lower() else "other"
                except FileNotFoundError:
                    pass
            return "missing"
    except FileNotFoundError:
        return "missing"
    except Exception:
        return "unknown"

def usbasp_on_bus_linux():
    try:
        out = subprocess.check_output(["lsusb"], text=True, stderr=subprocess.DEVNULL)
        return (USBASP_VID + ":" + USBASP_PID) in out.lower()
    except Exception:
        return False

def fetch_releases(repo):
    url = GH_API.format(repo=repo)
    req = urllib.request.Request(url, headers={"User-Agent": "OpenEVSE-Flasher/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

def get_asset_url(releases, tag, name):
    for rel in releases:
        if rel["tag_name"] == tag:
            for a in rel.get("assets", []):
                if a["name"] == name:
                    return a["browser_download_url"]
    return None

def best_asset(names, exts):
    for ext in exts:
        for n in names:
            if n.lower().endswith(ext):
                return n
    return names[0] if names else ""

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

class OpenEVSEFlasher(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("OpenEVSE Firmware Flasher")
        self.geometry("720x620")
        self.minsize(640, 520)
        self.configure(bg=BG)
        self.releases     = []
        self.local_fw     = None
        self.tmp_dir      = tempfile.mkdtemp(prefix="openevse_")
        self._task_thread = None
        self._win_driver  = None
        self.do_fuses     = tk.BooleanVar(value=True)
        self.do_eeprom    = tk.BooleanVar(value=True)

        self._style()
        self._build_header()
        self._build_usb_panel()
        self._build_firmware_panel()
        self._build_console()
        self._build_statusbar()
        self.after(100, self._startup)

    # --- style ---------------------------------------------------------------

    def _style(self):
        s = ttk.Style(self)
        try:
            s.theme_use("clam")
        except Exception:
            pass
        s.configure("TFrame",            background=BG)
        s.configure("TLabel",            background=BG)
        s.configure("TLabelframe",       background=BG)
        s.configure("TLabelframe.Label", background=BG, font=("Helvetica", 9, "bold"))
        s.configure("Big.TButton",       font=("Helvetica", 10, "bold"))

    # --- header --------------------------------------------------------------

    def _build_header(self):
        h = tk.Frame(self, bg=BLUE, pady=14)
        h.pack(fill="x")
        tk.Label(h, text="OpenEVSE",
                 font=("Helvetica", 20, "bold"), bg=BLUE, fg="white").pack()
        tk.Label(h, text="Firmware Flasher",
                 font=("Helvetica", 11), bg=BLUE, fg="#BBDEFB").pack()

    # --- USB panel -----------------------------------------------------------

    def _build_usb_panel(self):
        self.usb_frame = ttk.LabelFrame(self, text="OpenEVSE Programmer", padding=10)
        self.usb_frame.pack(fill="x", padx=12, pady=(10, 4))
        plat = platform.system()
        if plat == "Windows":
            self._usb_windows(self.usb_frame)
        elif plat == "Darwin":
            self.usb_frame.pack_forget()
        else:
            self._usb_linux(self.usb_frame)

    # Windows -----------------------------------------------------------------

    def _usb_windows(self, parent):
        self.win_driver_lbl = ttk.Label(parent,
            text="Checking USB driver...", foreground="gray")
        self.win_driver_lbl.grid(row=0, column=0, sticky="w")

        self.win_install_btn = ttk.Button(parent, text="Install Driver",
                                          command=self._zadig_run)
        self.win_install_btn.grid(row=0, column=1, padx=(12, 0))
        self.win_install_btn.grid_remove()

        self.win_reinstall_btn = ttk.Button(parent, text="Reinstall Driver",
                                            command=self._zadig_run)
        self.win_reinstall_btn.grid(row=0, column=2, padx=(8, 0))
        self.win_reinstall_btn.grid_remove()

        threading.Thread(target=self._win_check_driver, daemon=True).start()

    def _win_check_driver(self):
        status = check_usbasp_driver_windows()
        self._win_driver = status
        self.after(0, lambda: self._win_apply_status(status))

    def _win_apply_status(self, status):
        if status == "winusb":
            self.win_driver_lbl.config(
                text="USB Driver installed -- ready to flash.",
                foreground=GREEN)
            self.win_reinstall_btn.grid()
            self.win_install_btn.grid_remove()
        elif status == "missing":
            self.win_driver_lbl.config(
                text="USB Driver not found.",
                foreground=ORANGE)
            self.win_install_btn.config(text="Install Driver")
            self.win_install_btn.grid()
            self.win_reinstall_btn.grid_remove()
        elif status == "other":
            self.win_driver_lbl.config(
                text="USB Driver needs to be updated.",
                foreground=ORANGE)
            self.win_install_btn.config(text="Update Driver")
            self.win_install_btn.grid()
            self.win_reinstall_btn.grid_remove()
        else:
            self.win_driver_lbl.config(
                text="USB Driver status unknown -- install if flashing fails.",
                foreground="gray")
            self.win_install_btn.config(text="Install Driver")
            self.win_install_btn.grid()
            self.win_reinstall_btn.grid_remove()

    def _win_driver_ok(self):
        return self._win_driver == "winusb"

    def _zadig_run(self, recheck=True):
        messagebox.showinfo(
            "Installing USB Driver",
            "The driver installer will open.\n\n"
            "Steps:\n"
            "  1. Select 'USBasp' from the device dropdown\n"
            "     (if not listed: Options > List All Devices)\n"
            "  2. Make sure 'WinUSB' is shown in the driver box\n"
            "  3. Click Install Driver\n\n"
            "The installer will close automatically when done.")
        def task():
            drivers_dir = os.path.join(script_dir(), "drivers")
            os.makedirs(drivers_dir, exist_ok=True)
            path = find_zadig()
            if not path:
                self._log("Downloading driver installer...")
                dest = os.path.join(drivers_dir, ZADIG_FILENAME)
                try:
                    req = urllib.request.Request(
                        ZADIG_URL, headers={"User-Agent": "OpenEVSE-Flasher/1.0"})
                    with urllib.request.urlopen(req, timeout=60) as resp:
                        total = int(resp.getheader("Content-Length", 0))
                        done  = 0
                        with open(dest, "wb") as fh:
                            while True:
                                chunk = resp.read(16384)
                                if not chunk:
                                    break
                                fh.write(chunk)
                                done += len(chunk)
                                if total:
                                    self._log(
                                        "  %d%%  (%s/%s bytes)" % (
                                            done * 100 // total,
                                            format(done, ","), format(total, ",")),
                                        overwrite=True)
                    path = dest
                    self._log("Download complete.")
                except Exception as e:
                    self._log("Download failed: " + str(e))
                    return
            ensure_zadig_ini(drivers_dir)
            self._log("Opening driver installer...")
            try:
                os.startfile(path)
            except Exception as e:
                self._log("Could not open installer: " + str(e))
                return
            if recheck:
                import time; time.sleep(5)
                self._log("Re-checking driver...")
                self._win_check_driver()
        self._run_task(task)

    # Linux -------------------------------------------------------------------

    def _usb_linux(self, parent):
        self.udev_lbl = ttk.Label(parent, text="Checking...", foreground="gray")
        self.udev_lbl.grid(row=0, column=0, sticky="w")

        self.udev_install_btn = ttk.Button(parent, text="Install Driver",
                                           command=self._udev_install)
        self.udev_install_btn.grid(row=0, column=1, padx=(12, 0))
        self.udev_install_btn.grid_remove()

        ttk.Button(parent, text="Check USB Connection",
                   command=self._check_usb_linux).grid(row=0, column=2, padx=(8, 0))

        threading.Thread(target=self._udev_check, daemon=True).start()

    def _udev_check(self):
        installed = os.path.isfile(UDEV_RULE_PATH)
        self.after(0, lambda: self._udev_apply_status(installed))

    def _udev_apply_status(self, installed):
        if installed:
            self.udev_lbl.config(
                text="USB access enabled -- ready to flash.", foreground=GREEN)
            self.udev_install_btn.grid_remove()
        else:
            self.udev_lbl.config(
                text="USB Driver not found.", foreground=ORANGE)
            self.udev_install_btn.grid()

    def _udev_install(self):
        def task():
            self._log("Installing USB access rule...")
            with tempfile.NamedTemporaryFile("w", suffix=".rules", delete=False) as tf:
                tf.write(UDEV_RULE_TEXT)
                tmp = tf.name
            ok = False
            for elev in [["pkexec"], ["sudo"]]:
                try:
                    r = subprocess.run(
                        elev + ["sh", "-c",
                            "cp '%s' '%s' && chmod 644 '%s' && "
                            "udevadm control --reload-rules && udevadm trigger"
                            % (tmp, UDEV_RULE_PATH, UDEV_RULE_PATH)],
                        capture_output=True, text=True)
                    if r.returncode == 0:
                        ok = True
                        break
                    self._log("  %s: %s" % (elev[0], r.stderr.strip()))
                except FileNotFoundError:
                    pass
            try:
                os.unlink(tmp)
            except Exception:
                pass
            if ok:
                self._log("USB access enabled.")
                self.after(0, lambda: self._udev_apply_status(True))
            else:
                self._log("Automatic install failed. Run manually:")
                self._log("  sudo tee " + UDEV_RULE_PATH + " << 'EOF'")
                self._log(UDEV_RULE_TEXT.strip())
                self._log("EOF")
                self._log("  sudo udevadm control --reload-rules")
        self._run_task(task)

    def _check_usb_linux(self):
        def task():
            self._log("Scanning USB for OpenEVSE programmer...")
            if usbasp_on_bus_linux():
                self._log("Programmer detected -- ready to flash.")
            else:
                self._log("Programmer not found -- check the USB connection.")
        self._run_task(task)

    # --- firmware panel ------------------------------------------------------

    def _build_firmware_panel(self):
        f = ttk.LabelFrame(self, text="Firmware", padding=12)
        f.pack(fill="x", padx=12, pady=4)
        G = dict(sticky="w", padx=(0, 8), pady=5)

        ttk.Label(f, text="Release:").grid(row=0, column=0, **G)
        self.rel_var = tk.StringVar()
        self.rel_cb  = ttk.Combobox(f, textvariable=self.rel_var, width=30, state="readonly")
        self.rel_cb.grid(row=0, column=1, sticky="w", pady=5)
        self.rel_cb.bind("<<ComboboxSelected>>", self._on_release)
        ttk.Button(f, text="Refresh", width=7,
                   command=self._reload_releases).grid(row=0, column=2, padx=(6, 0))

        ttk.Label(f, text="Firmware file:").grid(row=1, column=0, **G)
        self.asset_var = tk.StringVar()
        self.asset_cb  = ttk.Combobox(f, textvariable=self.asset_var, width=50)
        self.asset_cb.grid(row=1, column=1, columnspan=2, sticky="w", pady=5)

        self.local_lbl = ttk.Label(f, text="", foreground=LBLUE, wraplength=560)
        self.local_lbl.grid(row=2, column=1, columnspan=2, sticky="w")

        # Options
        opts = ttk.Frame(f)
        opts.grid(row=3, column=0, columnspan=3, sticky="w", pady=(4, 2))
        ttk.Checkbutton(opts, text="Burn fuse bits",
                        variable=self.do_fuses).pack(side="left", padx=(0, 20))
        ttk.Checkbutton(opts, text="Write Defaults",
                        variable=self.do_eeprom).pack(side="left")

        bf = ttk.Frame(f)
        bf.grid(row=4, column=0, columnspan=3, sticky="w", pady=(6, 2))
        ttk.Button(bf, text="Flash Firmware", style="Big.TButton",
                   command=self._flash).pack(side="left", padx=(0, 20))
        ttk.Separator(bf, orient="vertical").pack(side="left", fill="y", padx=8)
        ttk.Button(bf, text="Browse local file...",
                   command=self._browse).pack(side="left", padx=(8, 0))

    # --- console -------------------------------------------------------------

    def _build_console(self):
        cf = ttk.LabelFrame(self, text="Output", padding=4)
        cf.pack(fill="both", expand=True, padx=12, pady=(0, 4))
        self.console = scrolledtext.ScrolledText(
            cf, font=("Courier New", 9),
            bg=CONS_BG, fg=CONS_FG, insertbackground=CONS_FG,
            relief="flat", state="disabled")
        self.console.pack(fill="both", expand=True)
        self.progress = ttk.Progressbar(cf, mode="indeterminate")
        self.progress.pack(fill="x", pady=(4, 0))

    # --- status bar ----------------------------------------------------------

    def _build_statusbar(self):
        bar = tk.Frame(self, bg="#E0E0E0", pady=3)
        bar.pack(fill="x", side="bottom")
        ttk.Button(bar, text="Clear log",
                   command=self._clear_log).pack(side="left", padx=6)
        ttk.Button(bar, text="Open download folder",
                   command=lambda: self._open_folder(self.tmp_dir)).pack(side="left")
        self.status_lbl = tk.Label(bar, text="Starting...",
                                   bg="#E0E0E0", font=("Helvetica", 9), fg="gray")
        self.status_lbl.pack(side="right", padx=8)

    # --- startup -------------------------------------------------------------

    def _startup(self):
        threading.Thread(target=self._check_avrdude,  daemon=True).start()
        threading.Thread(target=self._fetch_releases, daemon=True).start()

    def _check_avrdude(self):
        self._log("Checking avrdude...")
        path = find_avrdude()
        if path:
            r   = subprocess.run([path, "-v"], capture_output=True, text=True)
            ver = next((l.strip() for l in r.stderr.splitlines()
                        if "avrdude" in l.lower()), "")
            self._log("Found: " + path)
            if ver:
                self._log("  " + ver)
        else:
            self._log("avrdude not found.")
            self._log("  Place it in the 'avrdude/' folder next to this script.")

    def _fetch_releases(self):
        self._status("Fetching releases from GitHub...")
        self.after(0, self.progress.start)
        try:
            rels  = fetch_releases(AVR_REPO)
            self.releases = rels
            names = [r["tag_name"] for r in rels]
            self._log("Found %d release(s) for %s" % (len(rels), AVR_REPO))
            self.after(0, lambda: self._populate_releases(names))
        except Exception as e:
            self._log("Could not fetch releases: " + str(e))
            self._log("  Check your internet connection, then press Refresh.")
        self.after(0, self.progress.stop)
        self._status("Ready")

    def _reload_releases(self):
        self.releases = []
        self.rel_cb["values"] = []
        self.rel_var.set("")
        self.asset_cb["values"] = []
        self.asset_var.set("")
        threading.Thread(target=self._fetch_releases, daemon=True).start()

    def _populate_releases(self, names):
        self.rel_cb["values"] = names
        if names:
            self.rel_var.set(names[0])
            self._on_release()

    def _on_release(self, *_):
        tag = self.rel_var.get()
        rel = next((r for r in self.releases if r["tag_name"] == tag), None)
        if not rel:
            return
        assets = [a["name"] for a in rel.get("assets", [])
                  if a["name"].lower().endswith(".hex")]
        self.asset_cb["values"] = assets
        self.asset_var.set(best_asset(assets, [".hex"]))
        self.local_fw = None
        self.local_lbl.config(text="")

    # --- firmware ------------------------------------------------------------

    def _resolve_firmware(self):
        if self.local_fw:
            return self.local_fw
        tag   = self.rel_var.get()
        asset = self.asset_var.get()
        if not tag or not asset:
            raise ValueError("Select a release and firmware file first.")
        url = get_asset_url(self.releases, tag, asset)
        if not url:
            raise ValueError("No download URL found for '%s'." % asset)
        return self._download_fw(url, asset)

    def _download_fw(self, url, filename):
        dest = os.path.join(self.tmp_dir, filename)
        if os.path.exists(dest):
            self._log("Using cached: " + dest)
            return dest
        self._log("Downloading " + filename)
        req = urllib.request.Request(url, headers={"User-Agent": "OpenEVSE-Flasher/1.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            total = int(resp.getheader("Content-Length", 0))
            done  = 0
            with open(dest, "wb") as fh:
                while True:
                    chunk = resp.read(16384)
                    if not chunk:
                        break
                    fh.write(chunk)
                    done += len(chunk)
                    if total:
                        self._log(
                            "  %d%%  (%s/%s bytes)" % (
                                done * 100 // total,
                                format(done, ","), format(total, ",")),
                            overwrite=True)
        self._log("Saved: " + dest)
        return dest

    # --- flash ---------------------------------------------------------------

    def _flash(self):
        if platform.system() == "Windows" and not self._win_driver_ok():
            if self._win_driver == "missing":
                msg = "The USB driver is not installed.\n\nInstall it now?"
            elif self._win_driver == "other":
                msg = "The USB driver needs to be updated.\n\nUpdate it now?"
            else:
                msg = "Could not confirm the USB driver is installed.\n\nInstall it now?"
            if messagebox.askyesno("Driver Required", msg, icon="warning"):
                self._zadig_run(recheck=False)
                return
        self._do_flash()

    def _do_flash(self):
        def task():
            avrdude = find_avrdude()
            if not avrdude:
                self._log("avrdude not found -- see instructions above.")
                return
            try:
                fw  = self._resolve_firmware()
                fmt = "i" if fw.lower().endswith(".hex") else "r"
                cmd = [avrdude, "-p", MCU, "-c", PROGRAMMER,
                       "-Uflash:w:%s:%s" % (fw, fmt), "-v"]
                self._log("--- Flashing firmware ---")
                self._run_cmd(cmd)
                self._log("Firmware flashed OK.")

                if self.do_fuses.get():
                    fuse_cmd = [avrdude, "-p", MCU, "-c", PROGRAMMER] + FUSE_ARGS + ["-v"]
                    self._log("--- Burning fuse bits ---")
                    self._run_cmd(fuse_cmd)
                    self._log("Fuses written OK.")

                if self.do_eeprom.get():
                    eeprom = find_eeprom()
                    if not eeprom:
                        self._log("EEPROM file not found: " + EEPROM_FILENAME)
                        self._log("  Place it next to openevse_flasher.py to enable.")
                    else:
                        eeprom_cmd = [avrdude, "-p", MCU, "-c", PROGRAMMER,
                                      "-Ueeprom:w:%s:r" % eeprom, "-v"]
                        self._log("--- Writing EEPROM defaults ---")
                        self._run_cmd(eeprom_cmd)
                        self._log("EEPROM written OK.")

                self._log("Done! Disconnect and reconnect the device.")
                if platform.system() == "Windows":
                    threading.Thread(target=self._win_check_driver, daemon=True).start()
            except Exception as e:
                self._log("Flash failed: " + str(e))
        self._run_task(task)

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Select firmware file",
            filetypes=[("Firmware", "*.hex"), ("All files", "*.*")])
        if path:
            self.local_fw = path
            self.asset_var.set(os.path.basename(path))
            self.local_lbl.config(text="Local file: " + path)
            self._log("Local firmware: " + path)

    # --- task runner ---------------------------------------------------------

    def _run_task(self, fn):
        if self._task_thread and self._task_thread.is_alive():
            messagebox.showwarning("Busy", "A task is already running -- please wait.")
            return
        self.progress.start(12)
        self._status("Working...")
        def runner():
            try:
                fn()
            finally:
                self.after(0, self.progress.stop)
                self.after(0, lambda: self._status("Ready"))
        self._task_thread = threading.Thread(target=runner, daemon=True)
        self._task_thread.start()

    def _run_cmd(self, cmd):
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in proc.stdout:
            self._log(line.rstrip())
        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError("avrdude exited with code %d" % proc.returncode)

    # --- console -------------------------------------------------------------

    def _log(self, text, overwrite=False):
        def _do():
            self.console.config(state="normal")
            if overwrite:
                self.console.delete("end-2l linestart", "end-1c")
            self.console.insert("end", text + "\n")
            self.console.see("end")
            self.console.config(state="disabled")
        self.after(0, _do)

    def _clear_log(self):
        self.console.config(state="normal")
        self.console.delete("1.0", "end")
        self.console.config(state="disabled")

    def _status(self, msg):
        self.after(0, lambda: self.status_lbl.config(text=msg))

    def _open_folder(self, path):
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", path])

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = OpenEVSEFlasher()
    app.mainloop()
