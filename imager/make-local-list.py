#!/usr/bin/env python3
"""Makes Raspberry Pi Imager flash a downloaded ENCORE. OS image WITH its
"customise" screen (user name, password, Wi-Fi), before the image is on a release.

Put this file, os_list_encore.json and the .img.xz in the same folder (the build's
"ENCORE-OS" download has all three), then run:

    python make-local-list.py

It writes ENCORE-local.rpi-imager-manifest next to them, pointing at the .img.xz on your
computer. Double-click that file to open it in Raspberry Pi Imager 2, or in Imager go to
App Options > Content Repository > Edit > Use custom file and pick it.
"""
import json
import pathlib

here = pathlib.Path(__file__).resolve().parent
data = json.loads((here / "os_list_encore.json").read_text(encoding="utf-8"))
images = sorted(here.glob("*.img.xz"))
if not images:
    raise SystemExit(f"No .img.xz found in {here}")
for entry in data["os_list"]:
    entry["url"] = images[-1].as_uri()
    entry["name"] += " (on this computer)"
out = here / "ENCORE-local.rpi-imager-manifest"
out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {out}")
print(f"It points at {images[-1].name}. Double-click it to open it in Raspberry Pi Imager.")
