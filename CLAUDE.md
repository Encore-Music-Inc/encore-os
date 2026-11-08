# Notes for Claude (and whoever is driving it)

This is ENCORE. OS: Raspberry Pi OS (64-bit, Trixie) with ENCORE. on top, as an
SD card image, and the encore-os package that makes the ENCORE. layer. Notes
from ENCORE.'s other and older repositories do not apply here; this file does.

## Decisions (already made, don't revisit)

- Licence: GNU AGPLv3 (`LICENSE`). Copyright holder: Encore Music, Inc.
- The repo is public. Outside contributions are not accepted
  (`CONTRIBUTING.md`). The ENCORE. name and logo are not licensed (`TRADEMARKS.md`).
- Contact: support@encoremusic.studio
- Always write ENCORE. (capitals and the period) in anything people read, and
  "ENCORE. OS" with a space, never "ENCORE.OS". File and package names
  (`encore-os`, `ENCORE-OS-<version>-arm64.img.xz`) leave out the period.
- No long dashes in any text. Use commas, periods or parentheses.
- Don't write "DSP" in names, titles or prose for people. Say "audio processing".
- Anything third-party goes in `THIRD-PARTY-NOTICES.md`, and the image's own
  notice is `package/usr/share/doc/encore-os/SOURCE-CODE.txt`.
- Built on Raspberry Pi OS Trixie (64-bit), with pi-gen, Raspberry Pi's own
  image builder. Never fork the OS: Raspberry Pi and Debian keep doing the
  kernel, drivers and security updates.
- The ENCORE. tile opens https://encoremusic.studio in a Chromium app window
  (`package/usr/bin/encore-music`). Nothing of encoremusic is copied into the
  image or pinned here: no Green Room copy, no offline web app.
- What it's built from is named once, in `pins.conf`: the ENCORE. VST and
  ENCORE. Basement Studio release files by SHA-256, and pi-gen by Raspberry Pi
  OS's tag and its commit. Release files only, never a build artifact.
- Upkeep (security updates, rebuilding on newer Raspberry Pi OS every few
  months) belongs to Jimmy after the handover.

## Layout

| Path | What |
|---|---|
| `defaults.conf` | what ENCORE. OS is: `[os]` name and version (the release version, kept only here), apps, Home tiles, look, Welcome |
| `pins.conf` | what it's built from, each a release, with its SHA-256 (pi-gen: its commit) |
| `build-deb.sh` | builds the encore-os package; draws the art from `art/` each time |
| `package/` | the files encore-os installs (Home, Welcome, look, login screen, the ENCORE. tile, `DEBIAN/postinst`) |
| `art/` | the boot animation, welcome video, wallpapers, sounds, icons, fonts (DM Sans, Space Mono; OFL) |
| `image/` | pi-gen settings (`config`), the ENCORE. stage (`stage-encore`), `check-image.sh`, `screenshots.sh` |
| `imager/` | the Raspberry Pi Imager list (`make-os-list.py`, `make-local-list.py`) and its icon |
| `.github/pins/check.sh` | CI's check of `pins.conf` (published releases, published SHA-256s) and the README table |
| `.github/fetch-pin.sh` | gets one thing `pins.conf` names and checks it before use |
| `CHANGELOG.md` | every release's notes, newest first; the release job copies the version's section onto the GitHub release |
| `.github/release-notes.sh` | prints a version's notes from `CHANGELOG.md`, and fails if they're missing (CI runs it on every build) |
| `.github/workflows/ci.yml` | pull requests, main and manual runs: pins check, the package, the image (pi-gen on arm64, `check-image.sh` with Basement Studio's self-test inside the image, screenshots, Imager list) as artifacts; `v*` tags: attach main's image to the Release, no rebuild; "CI passed" is the one check to require |

## How ENCORE.'s repositories fit together

```
encore-audio-processing ──▶ JUCE                        (the JUCE version for all of ENCORE.)
encore-vst              ──▶ encore-audio-processing     (brings JUCE with it)
encore-basement-studio  ──▶ encore-vst                  (brings the sound engine and JUCE with it)
                        ──▶ Tracktion Engine
encore-os               ──▶ encore-vst and encore-basement-studio releases, pi-gen
                            (opens encoremusic.studio; pins nothing from it)
Green Room (encoremusic)──▶ master.wasm from encore-audio-processing, by its SHA-256
```

- Each repository pins each thing it uses in one place, and only to a
  published release. Here that place is `pins.conf`, and the README's Pinned
  releases table must match it (CI checks).
- Nothing is pinned twice: the plugins in Basement Studio come from its .deb;
  the ENCORE. VST files are the same plugins for other music apps.
- Changes travel up one repository at a time, each through a release:
  encore-audio-processing, then encore-vst, then encore-basement-studio, then
  encore-os. A repository moves to a new release only when something changes
  for its own users, and picks its own version number by what its users notice.
- Pull request titles: "Use <repository> vX.Y.Z (was vA.B.C)" in the repository
  that moves a pin; "Release vX.Y.Z" only for the repository's own version.

## Building and testing

- Actions in `ci.yml` are pinned to commits (version in a comment); Dependabot
  proposes updates. Keep new ones pinned the same way.
- Package: `./build-deb.sh <out dir>` with the system Python (it needs Pillow,
  numpy and fontTools) plus ffmpeg and rsvg-convert. Look at what the art
  scripts draw (boot frames, wallpapers, video frames) after changing them.
- Image: CI only (pi-gen in a privileged `debian:trixie` container on
  `ubuntu-24.04-arm`, about an hour). `image/check-image.sh` must pass; it
  runs Basement Studio's self-test inside the image.
- Trixie package names differ from Bookworm's (the desktop is `rpd-*`
  metapackages from pi-gen's stage3; raspi-config's labwc option is `W2`).
  Check a package exists in Raspberry Pi's or Debian's Trixie archive before
  adding it to `defaults.conf` or a stage.

## Versioning and releases

- Semantic versioning, tags `vMAJOR.MINOR.PATCH`. MAJOR for anything that
  breaks what people set up (their accounts, files or settings don't carry
  over); MINOR for new apps, features or a newer Raspberry Pi OS; PATCH for
  fixes and newer pinned releases that only fix things.

## Release process

1. The version lives in exactly one place: `[os] version` in `defaults.conf`.
2. Changing it is its own small pull request ("Release vX.Y.Z"), so a person sees the
   number before it's built. It adds the release notes to `CHANGELOG.md` (see
   Release notes below); CI fails until they're there.
3. Merging builds everything on `main`: the package, the image, its check and
   screenshots, and the Imager list, as workflow artifacts.
4. After the `main` build of that commit has passed, a person publishes the release in
   GitHub. Never a Claude session. Releases, Draft a new release; tag `vX.Y.Z` (Create
   new tag) with target `main` at the "Release vX.Y.Z" commit; leave the title and the
   description empty, don't click Generate release notes and don't attach files (the
   release job fills all of them in); Publish. Never publish an old draft release:
   publishing creates its tag on whatever its target is at that moment.
5. The tag's CI run doesn't rebuild. It checks that the tag matches the version, finds
   the successful `main` build of that exact commit and attaches its image with its
   `.sha256`, `os_list_encore.json` and `make-local-list.py`, and sets its title
   (`ENCORE. OS vX.Y.Z`) and notes (the version's section of `CHANGELOG.md`). If either
   check fails, nothing is attached. If that commit was docs-only (its build was
   skipped), run CI by hand on `main` (Actions, CI, Run workflow) and then re-run the
   release job.

- Claude sessions can't push tags: the push is refused with HTTP 403. Don't try, and
  don't look for another way (the API, a workflow, a different remote). When a
  release is due, open the version pull request, then tell your human the version
  number, why that number, and what changed since the last release, and wait for
  them to publish it.
- Tags `v*` should be protected (a tag ruleset, as on encore-vst): they can't be
  moved or deleted (an org admin can, in an emergency).

## Release notes

Every release's notes use this format, so they read the same in every ENCORE.
repository:

```
<One or two sentences: what this release is.>

### What's new        (a repository's first release: "What's in it")
### Downloads         (the files attached, and what each is for)
### Built on          (exactly what pins.conf pinned for this release)

Questions or problems: support@encoremusic.studio
```

- The title is `ENCORE. OS vX.Y.Z`; the tag stays `vX.Y.Z`.
- The notes describe the release as it is on the day it's published: no links
  to or mentions of later releases, and no promises ("coming soon", "will
  support"). If a limitation matters to people, state the limitation, not a plan.
- They live in `CHANGELOG.md`, newest first, one `## vX.Y.Z` section each,
  written once, in plain language, in the "Release vX.Y.Z" pull request. CI
  (`.github/release-notes.sh`) fails while the version has no section, or the
  section has no Downloads, Built on or Questions line. The release job copies
  the section onto the GitHub release, so nobody pastes notes.
- A published section isn't edited except to fix a factual error. Then fix it
  in a pull request and make the same fix on the GitHub release (Edit), so the
  two stay the same.
- "Built on" names each pin's release (ENCORE. VST, ENCORE. Basement Studio,
  Raspberry Pi OS), and what it brings in brackets when that matters to people.

## Changes

- main only changes through pull requests. Never push to main directly. (The one
  exception was the first commit, the licence, which created `main`.)
