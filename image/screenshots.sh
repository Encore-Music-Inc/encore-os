#!/usr/bin/env bash
# ENCORE. OS: screenshots of the real desktop, from a finished image, without a Pi.
#
#   sudo image/screenshots.sh <image.img> <out dir> [encore-os.deb]
#
# With a .deb, that encore-os is installed over the image's first (in memory only), so a
# change to the look can be photographed without rebuilding the image.
#
# On an arm64 machine: mounts the image (changes go to memory, the image is untouched), then
# starts its own desktop session (labwc, panel, desktop, autostart) as the first user on a
# virtual screen and photographs it with grim:
#   1-welcome.png   the first login (the Welcome; its video page)
#   2-gear.png      the Welcome's audio page
#   3-home.png      every login after that (ENCORE. Home)
#   4-desktop.png   the desktop itself, with the panel
#   5-menu.png      the panel's main menu
# Needs grim on the host. Best effort: a shot that doesn't come out is reported, not fatal.
set -uo pipefail
img=$(readlink -f "$1"); out=$(mkdir -p "$2" && cd "$2" && pwd)
[ "$(uname -m)" = aarch64 ] || { echo "screenshots need an arm64 machine"; exit 0; }

loop=$(losetup --show --find --partscan --read-only "$img")
base=$(mktemp -d); lower=$base/lower; upper=$base/rw; m=$base/root
mkdir -p "$lower" "$upper" "$m"
mount -t tmpfs tmpfs "$upper"; mkdir -p "$upper/u" "$upper/w"
cleanup() {
	pkill -f "labwc" 2>/dev/null; sleep 1
	for d in run/user/1000 tmp dev/shm dev/pts dev proc sys; do umount -l "$m/$d" 2>/dev/null; done
	umount -l "$m" "$upper" "$lower" 2>/dev/null; losetup -d "$loop" 2>/dev/null
}
trap cleanup EXIT
udevadm settle 2>/dev/null || true
mount -o ro,noload "${loop}p2" "$lower"
mount -t overlay overlay -o "lowerdir=$lower,upperdir=$upper/u,workdir=$upper/w" "$m"
mount -t proc proc "$m/proc"; mount -t sysfs sys "$m/sys"
mount --bind /dev "$m/dev"; mount --bind /dev/pts "$m/dev/pts"; mount -t tmpfs tmpfs "$m/tmp"
mount -t tmpfs -o mode=1777 tmpfs "$m/dev/shm"   # Wayland apps share their pixels through here
user=$(awk -F: '$3 == 1000 { print $1 }' "$m/etc/passwd"); home="/home/$user"
mkdir -p "$m/run/user/1000"; mount -t tmpfs -o mode=700,uid=1000,gid=1000 tmpfs "$m/run/user/1000"
if [ -n "${3:-}" ] && [ -f "$3" ]; then
	cp "$3" "$m/tmp/encore-os.deb"
	chroot "$m" env DEBIAN_FRONTEND=noninteractive ENCORE_OS_BUILDING=1 dpkg -i /tmp/encore-os.deb > "$out/install.log" 2>&1 		&& echo "installed $(basename "$3")" || { echo "::warning title=screenshots::installing $(basename "$3") failed"; tail -n 20 "$out/install.log"; }
fi
# what decides the panel's menu icon (for making it ENCORE.)
{ grep -rn -i -B2 -A6 'icon' "$m"/usr/share/wf-panel-pi/metadata/smenu.xml 2>/dev/null | head -n 60
  find "$m"/usr/share/icons -iname '*rpi*' -o -iname '*raspberry*' -o -iname '*start-here*' 2>/dev/null | sed "s|$m||" | head -n 40
  ls "$m"/usr/share/wf-panel-pi/metadata/ 2>/dev/null; } > "$out/panel-menu-icon.txt"
# which fonts the system finds (for checking the ENCORE. type)
{ echo "== fc-list DM Sans"; chroot "$m" fc-list : family style weight file | grep -i "dm sans"
  for w in regular medium bold extrabold; do echo "== fc-match DM Sans:$w"; chroot "$m" fc-match "DM Sans:weight=$w" family style weight file; done
  echo "== gsettings font"; grep -h font-name "$m"/usr/share/glib-2.0/schemas/*.override
  echo "== pango"; chroot "$m" dpkg-query -W -f='${Version}
' libpango-1.0-0
  cp "$(dirname "$0")/font-probe.py" "$m/tmp/font-probe.py"
  echo "== pango straight"; chroot "$m" python3 /tmp/font-probe.py; } > "$out/fonts.txt" 2>&1
# not the first-boot wizard: pretend the account is already set up
rm -f "$m/etc/xdg/autostart/piwiz.desktop"
echo "screenshots as $user ($home)"

session() {   # start the desktop, wait for it, leave it running
	chroot "$m" /usr/bin/env -i HOME="$home" USER="$user" LOGNAME="$user" XDG_RUNTIME_DIR=/run/user/1000 \
		PATH=/usr/local/bin:/usr/bin:/bin XDG_SESSION_TYPE=wayland XDG_CURRENT_DESKTOP=wlroots LANG=en_US.UTF-8 \
		WLR_BACKENDS=headless WLR_RENDERER=pixman WLR_LIBINPUT_NO_DEVICES=1 WLR_HEADLESS_OUTPUTS=1 \
		setpriv --reuid=1000 --regid=1000 --init-groups \
		dbus-run-session -- sh -c 'if command -v labwc-pi >/dev/null; then exec labwc-pi; else exec labwc -m; fi' \
		> "$out/session-$1.log" 2>&1 &
	for i in $(seq 1 30); do [ -S "$m/run/user/1000/wayland-0" ] && break; sleep 1; done
	sleep "${2:-14}"
}
stop() { pkill -f "labwc" 2>/dev/null; sleep 2; pkill -9 -f "labwc" 2>/dev/null; rm -f "$m"/run/user/1000/wayland-*; sleep 1; }
shot() {
	if WAYLAND_DISPLAY="$m/run/user/1000/wayland-0" timeout 20 grim "$out/$1.png" 2>>"$out/grim.log"; then
		echo "shot $1.png"
	else
		echo "::warning title=screenshot::$1 didn't come out"
	fi
}

# 1-2: first login, the Welcome (video, then its audio page)
session welcome 6; shot 1-welcome
chroot "$m" pkill -f welcome.py 2>/dev/null
chroot "$m" setpriv --reuid=1000 --regid=1000 --init-groups env -i HOME="$home" XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 \
	GDK_BACKEND=wayland PATH=/usr/bin:/bin sh -c 'encore-welcome --again --page 1 >/dev/null 2>&1 &'
sleep 6; shot 2-gear
stop

# 3: every login after that, ENCORE. Home
install -d -o 1000 -g 1000 "$m$home/.config/encore-os"; echo 1 > "$m$home/.config/encore-os/welcome-done"
session home 14; shot 3-home; stop

# 4-5: the desktop itself (Home left closed), and the main menu
echo 1 > "$m$home/.config/encore-os/no-home"
session desktop 12; shot 4-desktop
chroot "$m" setpriv --reuid=1000 --regid=1000 --init-groups env -i HOME="$home" XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 \
	PATH=/usr/bin:/bin sh -c 'command -v wfpanelctl >/dev/null && wfpanelctl smenu menu' 2>/dev/null
sleep 3; shot 5-menu
stop
ls -l "$out"
