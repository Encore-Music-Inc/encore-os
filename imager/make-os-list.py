#!/usr/bin/env python3
"""Writes the Raspberry Pi Imager list (os_list_encore.json) for one ENCORE. OS image.

Used by .github/workflows/ci.yml after it builds and compresses the image. The format is
Imager's os_list (https://github.com/raspberrypi/rpi-imager/blob/main/doc/schema-notes.md).
"""
import argparse
import json

ICON = "https://raw.githubusercontent.com/Encore-Music-Inc/encore-os/main/imager/encore-icon-40.png"

p = argparse.ArgumentParser()
p.add_argument("--url", required=True, help="where the .img.xz is downloaded from")
p.add_argument("--extract-size", type=int, required=True)
p.add_argument("--extract-sha256", required=True)
p.add_argument("--download-size", type=int, required=True)
p.add_argument("--download-sha256", required=True)
p.add_argument("--release-date", required=True)
p.add_argument("--basement", default="", help="ENCORE. Basement Studio version in the image")
p.add_argument("--out", required=True)
a = p.parse_args()

desc = ("A music studio that boots up ready to play: ENCORE. Basement Studio, the ENCORE. "
        "plugins, ENCORE. in its own window, low-latency audio, all in the dark ENCORE. look. "
        "For Raspberry Pi 4, 400, 5, 500 and 500+ (2 GB or more).")
entry = {
    "name": "ENCORE. OS",
    "description": desc,
    "icon": ICON,
    "website": "https://github.com/Encore-Music-Inc/encore-os#readme",
    "url": a.url,
    "extract_size": a.extract_size,
    "extract_sha256": a.extract_sha256,
    "image_download_size": a.download_size,
    "image_download_sha256": a.download_sha256,
    "release_date": a.release_date,
    "init_format": "systemd",
    "architecture": "arm64",
    "devices": ["pi5-64bit", "pi4-64bit"],
}
with open(a.out, "w", encoding="utf-8", newline="\n") as f:
    json.dump({"os_list": [entry]}, f, indent=2)
    f.write("\n")
print(f"wrote {a.out} (Basement {a.basement or 'unknown'})")
