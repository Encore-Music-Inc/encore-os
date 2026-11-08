# Changes

Each release's notes, newest first. When a release is published, the release
job puts its section on the GitHub release (see "Release notes" in
`CLAUDE.md`).

## v1.0.0

The first release of ENCORE. OS: a ready-to-flash music studio for Raspberry
Pi 4, 400, 5, 500 and 500+ with 2 GB or more, built on 64-bit Raspberry Pi OS
(Trixie).

### What's in it
- **ENCORE. Basement Studio**, with the ENCORE. plugins built in.
- **The ENCORE. plugins** (Vox, Verb, Equalize, Master, Strum) as VST3 and LV2,
  for other music apps on the Pi too.
- **ENCORE.**: a tile that opens encoremusic.studio in its own window. It needs
  the internet.
- **Audio set up for music**: PipeWire at 256 samples, 48 kHz (about 5 ms),
  real-time priority for recording and playback, JACK apps through PipeWire,
  and the CPU at full speed so audio doesn't drop out.
- **ENCORE. Home** and a first-login **Welcome**, and the dark ENCORE. look
  everywhere: boot animation, login screen, panel and windows.
- **Everyday apps**: Chromium, VLC, Hydrogen, LibreOffice Writer, Calc and
  Impress, and Files.
- No default password and SSH off: you choose the user name and password in
  Raspberry Pi Imager or on the first start.

### Downloads
- `ENCORE-OS-1.0.0-arm64.img.xz`: the SD card image (16 GB card or bigger),
  with `ENCORE-OS-1.0.0-arm64.img.xz.sha256`.
- `os_list_encore.json`: the list for Raspberry Pi Imager. In Imager, App
  Options, Content Repository, Edit, Use custom URL, and paste this file's
  address; then pick your Pi, ENCORE. OS and your SD card, and set your user
  name, password and Wi-Fi on the customisation screen.
- `make-local-list.py`: for flashing a downloaded image with Imager's
  customisation screen (see the README).

To record you need a USB audio interface or USB microphone: no Pi has a
microphone input.

### Built on
Raspberry Pi OS (64-bit, Trixie, Raspberry Pi's 2026-10-06 release), ENCORE.
Basement Studio v0.6.0 and ENCORE. VST v0.6.1 (both with ENCORE. Audio
Processing v1.0.1 and JUCE 9.0.5).

Questions or problems: support@encoremusic.studio
