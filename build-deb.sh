#!/usr/bin/env bash
# Builds the encore-os package: everything that makes a Raspberry Pi OS (or Debian) desktop
# into ENCORE. OS. The boot animation, welcome video, sounds and wallpapers are drawn fresh
# from art/ each time.
#
#   ./build-deb.sh <out dir>
#
# Needs: python3 with Pillow and numpy, ffmpeg, rsvg-convert, dpkg-deb.
set -euo pipefail
OS="$(cd "$(dirname "$0")" && pwd)"
OUT="$(mkdir -p "$1" && cd "$1" && pwd)"
VERSION=$(sed -nE 's/^version *= *([0-9.]+)/\1/p' "$OS/defaults.conf" | head -n 1)
[ -n "$VERSION" ] || { echo "no [os] version in defaults.conf" >&2; exit 1; }
REV="${ENCORE_OS_REV:-1}"
PKG="$OUT/stage"
rm -rf "$PKG"
cp -r "$OS/package" "$PKG"
find "$PKG" \( -name .gitkeep -o -name __pycache__ -o -name "*.pyc" \) -prune -exec rm -rf {} +

art() { (cd "$OS/art" && python3 "$@"); }
echo "== art"
art make-boot.py "$PKG/usr/share/plymouth/themes/encore"
art make-video.py "$PKG/usr/share/encore-os/welcome.mp4"
art make-sounds.py "$PKG/usr/share/encore-os"
art make-wallpapers.py "$PKG/usr/share/rpd-wallpaper"
install -d "$PKG/usr/share/fonts/truetype/encore" "$PKG/usr/share/doc/encore-os"
# DM Sans as fixed weights (older font stacks, like Bookworm's, only find the variable font's
# default weight), Space Mono as is
python3 - "$OS/art/fonts/DMSans.ttf" "$PKG/usr/share/fonts/truetype/encore" <<'PY'
import sys
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
src, out = sys.argv[1], sys.argv[2]
for name, wght in [("Regular", 400), ("Medium", 500), ("Bold", 700), ("ExtraBold", 800)]:
    f = instantiateVariableFont(TTFont(src), {"wght": wght, "opsz": 14}, updateFontNames=True)
    f.save(f"{out}/DMSans-{name}.ttf")
PY
cp "$OS"/art/fonts/SpaceMono-*.ttf "$PKG/usr/share/fonts/truetype/encore/"
# the ENCORE. icon theme: the ENCORE. mark where Raspberry Pi's logo was (the panel's menu
# button), everything else from Raspberry Pi's own icons
it="$PKG/usr/share/icons/ENCORE"
for s in 16 22 24 32 48 64 96 128; do
	install -d "$it/${s}x${s}/places" "$it/${s}x${s}/apps"
	for n in places/rpi-logo places/start-here apps/rpi; do
		rsvg-convert -w $s -h $s "$OS/art/icons/encore-menu.svg" -o "$it/${s}x${s}/$n.png"
	done
done
dirs=$(for s in 16 22 24 32 48 64 96 128; do printf '%sx%s/places,%sx%s/apps,' $s $s $s $s; done | sed 's/,$//')
{
	printf '[Icon Theme]
Name=ENCORE
Comment=ENCORE. OS: Raspberry Pi icons with the ENCORE. mark
Inherits=PiXtrix,PiXflat,hicolor
Directories=%s
' "$dirs"
	for s in 16 22 24 32 48 64 96 128; do
		for c in places apps; do printf '
[%sx%s/%s]
Size=%s
Context=%s
Type=Fixed
' $s $s $c $s "$( [ $c = places ] && echo Places || echo Applications )"; done
	done
} > "$it/index.theme"
cp "$OS"/art/fonts/OFL-*.txt "$PKG/usr/share/doc/encore-os/"
for svg in "$OS"/art/icons/*.svg; do
	n=$(basename "$svg" .svg)
	install -D -m 644 "$svg" "$PKG/usr/share/icons/hicolor/scalable/apps/$n.svg"
	for s in 48 128 256; do
		install -d "$PKG/usr/share/icons/hicolor/${s}x${s}/apps"
		rsvg-convert -w $s -h $s "$svg" -o "$PKG/usr/share/icons/hicolor/${s}x${s}/apps/$n.png"
	done
done
rsvg-convert -w 256 -h 256 "$OS/art/icons/encore-os.svg" -o "$PKG/usr/share/encore-os/login-logo.png"
install -D -m 644 "$OS/defaults.conf" "$PKG/etc/encore-os/defaults.conf"
# apps from [apps] become Recommends: installed with ENCORE. OS, and new ones arrive with its
# updates, but removing one doesn't remove ENCORE. OS
apps=$(awk '/^\[/{s=$0; next} s=="[apps]" && $0 !~ /^[[:space:]]*(#|$)/ {gsub(/[[:space:]]/,""); printf "%s%s", (n++ ? ", " : ""), $0}' "$OS/defaults.conf")
installed=$(du -sk "$PKG" | cut -f1)
cat > "$PKG/DEBIAN/control" <<EOF
Package: encore-os
Version: $VERSION-$REV
Architecture: all
Maintainer: Encore Music, Inc. <support@encoremusic.studio>
Installed-Size: $installed
Section: sound
Priority: optional
Depends: python3, python3-gi, gir1.2-gtk-3.0, fontconfig
Recommends: $apps, plymouth, encore-basement-studio
Homepage: https://github.com/Encore-Music-Inc/encore-os
Description: ENCORE. OS: a music studio that boots up ready to play
 Turns a Raspberry Pi OS desktop into ENCORE. OS: the ENCORE. boot animation, login
 screen and dark ENCORE. look everywhere, ENCORE. Home (big tiles for your apps), a
 first-login Welcome with video and audio setup, and ENCORE. (encoremusic.studio) in its
 own window.
EOF
echo "/etc/encore-os/defaults.conf" > "$PKG/DEBIAN/conffiles"
find "$PKG" -path "$PKG/DEBIAN" -prune -o -type f -print0 | xargs -0 chmod 644
chmod 755 "$PKG"/DEBIAN/postinst "$PKG"/usr/bin/* "$PKG"/usr/lib/encore-os/*.py "$PKG"/usr/lib/encore-os/keep-boot-theme "$PKG"/usr/lib/encore-os/apply-login "$PKG"/usr/lib/encore-os/apply-look
find "$PKG" -type d -exec chmod 755 {} +
deb="$OUT/encore-os_${VERSION}-${REV}_all.deb"
dpkg-deb --root-owner-group -Zxz --build "$PKG" "$deb" >/dev/null
rm -rf "$PKG"
echo "== $(basename "$deb") ($(( $(stat -c %s "$deb") / 1024 )) KB)"
