# ENCORE. OS

A music studio that boots up ready to play. ENCORE. OS is Raspberry Pi OS
(64-bit, Trixie) with ENCORE. on top: ENCORE. Basement Studio, the ENCORE.
plugins, ENCORE. in its own window, audio set up for music, and the ENCORE.
look from the first power-on.

Copyright (C) 2026 Encore Music, Inc. Licensed under the GNU Affero General
Public License v3 (see `LICENSE`). The ENCORE. name and logo are not licensed
(see `TRADEMARKS.md`). Third-party code: `THIRD-PARTY-NOTICES.md`. Outside
contributions are not accepted (see `CONTRIBUTING.md`).
Contact: support@encoremusic.studio

## What's on it

- **ENCORE. Basement Studio**, the DAW, with the ENCORE. plugins built in.
- **The ENCORE. plugins** (Vox, Verb, Equalize, Master, Strum) as VST3 and LV2
  in `/usr/lib/vst3` and `/usr/lib/lv2`, for other music apps on the Pi too.
- **ENCORE.**: a tile that opens encoremusic.studio in its own window (your
  account, your music, your fans). It needs the internet; nothing of the
  website is installed.
- **Audio set up for music**: PipeWire set for low latency
  (`image/stage-encore/01-audio/files/90-encore-low-latency.conf`), real-time priority for the `audio` group, JACK apps through PipeWire, and the
  CPU kept at full speed so audio doesn't drop out.
- **ENCORE. Home** (big tiles for your apps, on every login), a first-login
  **Welcome** (a short video, then picking your audio interface), and the dark
  ENCORE. look everywhere: boot animation, login screen, panel, windows.
- **Everyday apps**: Chromium, VLC, Hydrogen (drum machine), LibreOffice
  Writer, Calc and Impress, and Files.
- No default password: you choose the user name and password in Raspberry Pi
  Imager or on the Pi's first-start screen. SSH is off unless you turn it on.
  The Pi is called `encore` on your network.

## Which Pi

| Pi | |
|---|---|
| Pi 4, Pi 400, Pi 5, Pi 500, Pi 500+ (2 GB or more) | Supported |
| Pi 4 or Pi 5 with 1 GB | Not supported: too little memory |
| Pi 3 (every model) | Not supported: too little memory (1 GB or less) |
| Pi Zero 2 W | Not supported: too little memory (512 MB) |
| Pi 1, Pi 2, Pi Zero, Zero W | Not supported: 32-bit only |

Use a 16 GB or bigger SD card. To record you need a USB
audio interface or USB microphone: no Pi has a microphone input.

## Put it on an SD card

Each release (under Releases on this repo) has the image
(`ENCORE-OS-<version>-arm64.img.xz`, with its `.sha256`) and a list for
Raspberry Pi Imager (`os_list_encore.json`).

With **Raspberry Pi Imager** (version 2 or newer, from
[raspberrypi.com/software](https://www.raspberrypi.com/software/)):

1. Open Imager, click **App Options**, then next to **Content Repository**
   click **Edit**.
2. Choose **Use custom URL** and paste
   `https://github.com/Encore-Music-Inc/encore-os/releases/latest/download/os_list_encore.json`,
   then click **Apply & Restart**.
3. Pick your Pi, then **ENCORE. OS**, then your SD card.
4. On the customisation screen, set a user name and password, your Wi-Fi, your
   time zone and keyboard. Write the card, put it in the Pi, power on.

If you skip customisation, the Pi asks for all of this on its first start
instead.

To try an image from a build (before it's on a release): download the build's
`encore-os` file from GitHub Actions, unzip it, run `python make-local-list.py`
in that folder, then double-click the `ENCORE-local.rpi-imager-manifest` it
makes.

**Tips**

- Choose your audio interface by right-clicking the speaker icon at the top of
  the screen.
- Clicks or dropouts: use the official power supply, plug the interface
  straight into the Pi (not a hub).
- Don't want ENCORE. Home at login? `touch ~/.config/encore-os/no-home`
  (delete that file to undo). See the Welcome again: `encore-welcome --again`.
- Prefer the normal CPU speed (cooler, quieter)?
  `sudo systemctl disable --now encore-performance`
- Updates for the system come from Raspberry Pi OS as usual
  (`sudo apt update && sudo apt full-upgrade`).

## Change what ENCORE. OS is: `defaults.conf`

One file decides the version, the apps, the Home screen, the look and the
Welcome:

| Section | What it does |
|---|---|
| `[os]` | name, **version** (the release version, kept only here), codename, hostname, `login = password` (the ENCORE. login screen every time) or `automatic` |
| `[look]` | colours, fonts, wallpaper, `boot_animation = encore` or `pix` |
| `[apps]` | Debian packages that come with it, and arrive on existing systems with the next update |
| `[remove]` | packages Raspberry Pi OS ships that ENCORE. OS leaves out |
| `[home]` | the Home screen's rows and tiles, in order |
| `[welcome]` | the welcome video, and the ENCORE. page it offers |

On a running system it's `/etc/encore-os/defaults.conf`; Home and Welcome read
it from there, so tiles can change without a rebuild.

## What is here

```
defaults.conf              what ENCORE. OS is (see above)
pins.conf                  what it's built from: each a release, with its SHA-256
build-deb.sh               builds the encore-os package (art drawn fresh each time)
package/                   the files encore-os installs: Home, Welcome, the theme, panel,
                           login screen setup (DEBIAN/postinst), the ENCORE. tile
art/                       everything visual, drawn by code: boot animation, welcome video
                           and its music, wallpapers, sounds, icons, fonts (DM Sans, Space Mono)
image/                     the image: pi-gen settings (config), the ENCORE. stage
                           (stage-encore), check-image.sh, screenshots.sh
imager/                    the Raspberry Pi Imager list (make-os-list.py) and its icon
```

## Pinned releases

ENCORE. OS is built from published releases only, each named once, in
`pins.conf`, with the SHA-256 of the exact file (or, for pi-gen, the commit of
Raspberry Pi OS's tag). The image build checks each file before using it, and
CI (`.github/pins/check.sh`) checks each one is a published release, that the
SHA-256 is the one that release published, and that this table matches.

<!-- pinned-releases:start -->
| What | Repository | Release | Exactly |
|---|---|---|---|
| encore-vst | [Encore-Music-Inc/encore-vst](https://github.com/Encore-Music-Inc/encore-vst) | `v0.6.1` | `ENCORE-VST-0.6.1-linux-arm64.tar.gz`, SHA-256 `2651688fa3fd` |
| encore-basement-studio | [Encore-Music-Inc/encore-basement-studio](https://github.com/Encore-Music-Inc/encore-basement-studio) | `v0.6.0` | `encore-basement-studio_0.6.0_arm64.deb`, SHA-256 `88b35e8a17c2` |
| pi-gen | [RPi-Distro/pi-gen](https://github.com/RPi-Distro/pi-gen) | `2026-10-06-raspios-trixie-arm64` | the tag, at commit `b2cd98a` |
<!-- pinned-releases:end -->

ENCORE. Basement Studio's .deb has the plugins built in; the ENCORE. VST files
are the same plugins for other music apps. The ENCORE. tile opens
encoremusic.studio, so nothing from encoremusic is pinned.

To move a pin: change its line in `pins.conf`, update the table
(`.github/pins/check.sh --table` prints it), and open a pull request titled
"Use <repository> vX.Y.Z (was vA.B.C)".

## Build

**The package** (on Debian or Ubuntu): install `ffmpeg python3-pil
python3-numpy python3-fonttools librsvg2-bin dpkg-dev`, then
`./build-deb.sh dist`. Try it on a Pi you already have (64-bit Raspberry Pi
OS with the desktop): `sudo apt install ./encore-os_*.deb`, then log out and
back in (reboot to see the boot animation).

**The image** is built by CI (below): pi-gen needs a privileged container on
an arm64 machine.

## CI

`.github/workflows/ci.yml`:

| When | What runs |
|---|---|
| Pull request, push to `main`, or a manual run | the pins check; the encore-os package (scripts checked, art drawn, package built); then the image on GitHub's arm64 runner: pi-gen's stages 0 to 3 (the Raspberry Pi desktop, without stage 4's applications) and the ENCORE. stage, with the releases `pins.conf` names. `image/check-image.sh` mounts the finished image, checks everything is in place (packages, the ENCORE. tile, the plugins, audio settings, no password, the boot animation) and runs ENCORE. Basement Studio's self-test inside it. Screenshots of the real desktop are taken on a virtual screen. The image is compressed, and the Imager list written with its sizes and checksums. Kept as workflow artifacts (`encore-os`, `screenshots`) |
| `v*` tag | no build: the files from the successful `main` build of the tag's commit are attached to the Release, with its title and notes |

- A pull request or push that only changes `*.md`, `LICENSE` or
  `.github/CODEOWNERS` skips the builds (skipped counts as passing). So does a
  pull request that only changes the version line in `defaults.conf` and
  `CHANGELOG.md`; the push to `main` after merging builds and checks the image.
- "CI passed" is the one check to require.
- Every action is pinned to a commit, with its version in a comment.
  Dependabot proposes updates (`.github/dependabot.yml`).

## Releases

Versions are `vMAJOR.MINOR.PATCH`. The version lives in `defaults.conf`
(`[os] version`) and nowhere else. A release's notes are written in
`CHANGELOG.md` in the pull request that changes the version; CI fails until
they're there.

A person at Encore Music, Inc. creates each release in GitHub: Releases, Draft
a new release, choose a new tag `vX.Y.Z` on `main`, leave the title and
description empty, Publish. The tag starts CI, which doesn't rebuild: it takes
the image from the successful `main` build of that exact commit, attaches it
with its `.sha256` and the Imager list, and sets the title and notes from
`CHANGELOG.md`. Workflow artifacts expire, so release a commit while its
build's files are still there.
