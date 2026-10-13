#!/usr/bin/env python3
"""
Smoke tests for a built OpenEVSE Flasher, run by CI on each platform.

  smoke_test.py app <program>
      Launch the GUI and check it is still running after a few seconds
      (catches missing modules / libraries that crash a frozen app on start).

  smoke_test.py avrdude <avrdude> [avrdude.conf]
      Run the bundled avrdude without a programmer attached. It must load
      (all shared libraries found) and get as far as looking for the USBasp.
"""
import subprocess
import sys
import time


def smoke_app(program, seconds=15):
    proc = subprocess.Popen([program])
    time.sleep(seconds)
    code = proc.poll()
    if code is not None:
        sys.exit("FAIL: %s exited early with code %d" % (program, code))
    proc.kill()
    proc.wait()
    print("OK: %s still running after %ds" % (program, seconds))


def smoke_avrdude(avrdude, conf=None):
    cmd = [avrdude] + (["-C", conf] if conf else []) + \
          ["-p", "atmega328p", "-c", "usbasp", "-n"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    out = (r.stdout + r.stderr).lower()
    print(r.stdout + r.stderr)
    for bad in ("library not loaded", "error while loading shared libraries",
                "can't open config file", "cannot open config file"):
        if bad in out:
            sys.exit("FAIL: " + bad)
    # e.g. "cannot find USB device with vid=0x16c0 ... product='USBasp'"
    if "usbasp" not in out:
        sys.exit("FAIL: avrdude did not reach the USB programmer stage")
    print("OK: avrdude loads and looks for the USBasp")


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("app", "avrdude"):
        sys.exit(__doc__)
    if sys.argv[1] == "app":
        smoke_app(sys.argv[2])
    else:
        smoke_avrdude(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
