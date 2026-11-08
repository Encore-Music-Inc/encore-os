#!/usr/bin/env bash
# ENCORE. OS: checks a finished image without booting it.
#
#   sudo image/check-image.sh <image.img>
#
# Mounts the image read-only and checks that everything ENCORE. adds is in
# place, then (on an arm64 machine) runs the installed ENCORE. Basement Studio's
# self-test inside the image, on a virtual screen, using the image's own libraries.
# Writes GitHub Actions ::notice:: / ::error:: lines; exits non-zero on any failure.
set -uo pipefail

img=$(readlink -f "$1")
fails=0
ok()   { echo "PASS $*"; }
bad()  { echo "::error title=image check::$*"; fails=$((fails + 1)); }
note() { echo "::notice title=$1::$2"; }

loop=$(losetup --show --find --partscan --read-only "$img") || { echo "::error::losetup failed"; exit 1; }
m=$(mktemp -d)
cleanup() {
	pkill -f "Xvfb :77" 2>/dev/null || true
	for d in tmp/.X11-unix tmp dev/pts dev proc sys boot/firmware; do umount -l "$m/$d" 2>/dev/null || true; done
	umount -l "$m" 2>/dev/null || true
	losetup -d "$loop" 2>/dev/null || true
}
trap cleanup EXIT
udevadm settle 2>/dev/null || true
mount -o ro,noload "${loop}p2" "$m" || { echo "::error::cannot mount the root partition"; exit 1; }
mount -o ro "${loop}p1" "$m/boot/firmware" || bad "cannot mount the boot partition"

f() { [ -e "$m$1" ] && ok "$1" || bad "missing $1"; }

# ENCORE. Basement Studio
ver=$(chroot "$m" dpkg-query -W -f='${Status} ${Version}' encore-basement-studio 2>/dev/null)
case "$ver" in "install ok installed "*) ok "encore-basement-studio ${ver##* }" ;; *) bad "encore-basement-studio is not installed ($ver)" ;; esac
f "/opt/encore-basement-studio/ENCORE Basement Studio"
f /usr/bin/encore-basement-studio
f /usr/share/applications/encore-basement-studio.desktop
file -b "$m/opt/encore-basement-studio/ENCORE Basement Studio" | grep -q "ARM aarch64" && ok "app is arm64" || bad "app is not an arm64 program"

# ENCORE. OS
ver=$(chroot "$m" dpkg-query -W -f='${Status} ${Version}' encore-os 2>/dev/null)
case "$ver" in "install ok installed "*) ok "encore-os ${ver##* }" ;; *) bad "encore-os is not installed ($ver)" ;; esac
for p in /etc/encore-os/defaults.conf /etc/encore-os/release /usr/bin/encore-home /usr/bin/encore-welcome /usr/bin/encore-session 	/usr/bin/encore-music /usr/share/applications/encore-music.desktop /etc/xdg/autostart/encore-session.desktop /usr/share/encore-os/welcome.mp4 /usr/share/encore-os/encore.css 	/usr/share/plymouth/themes/encore/encore.script /usr/share/rpd-wallpaper/encore-dark.png /usr/share/rpd-wallpaper/encore-login.png 	/usr/share/fonts/truetype/encore/DMSans-Regular.ttf /usr/share/fonts/truetype/encore/DMSans-ExtraBold.ttf /usr/share/icons/ENCORE/index.theme /usr/share/icons/ENCORE/32x32/places/rpi-logo.png /usr/share/themes/ENCORE/gtk-3.0/gtk.css /etc/xdg/labwc/themerc-override 	/etc/skel/.local/share/themes/PiXonyx/gtk-3.0/gtk.css /etc/skel/.config/wf-panel-pi.ini /etc/chromium/policies/managed/encore.json; do f "$p"; done
# the ENCORE. tile opens the website; no copy of anything from encoremusic is in the image
grep -q '^Exec=encore-music$' "$m/usr/share/applications/encore-music.desktop" && grep -q '"https://encoremusic.studio"' "$m/usr/bin/encore-music" \
	&& ok "ENCORE. tile opens https://encoremusic.studio" || bad "the ENCORE. tile doesn't open https://encoremusic.studio"
grep -q '^encore-music.desktop' "$m/etc/encore-os/defaults.conf" && ok "ENCORE. tile on Home" || bad "the ENCORE. tile isn't on Home (defaults.conf)"
[ ! -e "$m/usr/share/encore-os/green-room" ] && [ ! -e "$m/usr/bin/encore-green-room" ] && ok "no Green Room copy in the image" || bad "a Green Room copy is in the image"
theme=$(chroot "$m" plymouth-set-default-theme 2>/dev/null)
[ "$theme" = encore ] && ok "boot animation: encore" || bad "boot animation is '$theme', not encore"
for ird in "$m"/boot/firmware/initramfs*; do
	n=$(basename "$ird")
	(cd "$(mktemp -d)" && (unmkinitramfs "$ird" . 2>/dev/null || true) && find . -path '*plymouth/themes/encore/encore.script' | grep -q .) 		&& ok "$n has the ENCORE. boot animation" || bad "$n doesn't have the ENCORE. boot animation in it"
done
grep -qw splash "$m/boot/firmware/cmdline.txt" && grep -qw logo.nologo "$m/boot/firmware/cmdline.txt" && ok "cmdline: splash, no logo" || bad "cmdline.txt lacks splash/logo.nologo"
grep -q '^disable_splash=1' "$m/boot/firmware/config.txt" && ok "no rainbow square" || bad "config.txt doesn't disable the rainbow square"
grep -q '^gtk-theme-name=ENCORE' "$m/etc/lightdm/pi-greeter.conf" 2>/dev/null && ok "login screen in ENCORE. colours" || bad "pi-greeter.conf not set to ENCORE"
grep -q "encore-login.png" "$m/etc/lightdm/pi-greeter.conf" 2>/dev/null && ok "login wallpaper" || bad "login wallpaper not set"
[ -L "$m/etc/systemd/system/multi-user.target.wants/encore-os-login.service" ] && ok "login setting service enabled" || bad "encore-os-login.service not enabled"
grep -qE "gtk-theme='(PiXonyx|PiXnoir)'" "$m"/usr/share/glib-2.0/schemas/99_encore-os.gschema.override && ok "dark theme default" || bad "no dark theme default"
# the desktop's settings, one folder per session (rpd-labwc on Trixie, LXDE-pi on Bookworm)
wp=$(grep -l "encore-dark.png" "$m"/etc/xdg/pcmanfm/*/desktop-items-0.conf 2>/dev/null | head -n 1)
[ -n "$wp" ] && ok "desktop wallpaper (${wp#$m})" || bad "desktop wallpaper not set in /etc/xdg/pcmanfm/*/desktop-items-0.conf"
home=$(ls -d "$m"/home/* 2>/dev/null | head -n 1)
[ -f "$home/.local/share/themes/PiXonyx/gtk-3.0/gtk.css" ] && [ "$(stat -c %u "$home/.local/share/themes/PiXonyx/gtk-3.0/gtk.css")" = 1000 ] 	&& ok "first user has the ENCORE. colours (${home#$m})" || bad "first user is missing the ENCORE. colours"
for p in vlc hydrogen libreoffice-writer gstreamer1.0-gtk3; do
	chroot "$m" dpkg-query -W -f='${Status}' "$p" 2>/dev/null | grep -q "install ok installed" && ok "app $p" || bad "app $p not installed"
done
for p in audacity musescore3; do
	chroot "$m" dpkg-query -W -f='${Status}' "$p" 2>/dev/null | grep -q "install ok installed" && bad "$p is installed (left out of ENCORE. OS)" || ok "$p left out"
done
[ -f "$m/usr/share/doc/encore-os/SOURCE-CODE.txt" ] && ok "source-code notice for the open-source parts" || bad "no /usr/share/doc/encore-os/SOURCE-CODE.txt"
chroot "$m" python3 -c "import sys; sys.path.insert(0, '/usr/lib/encore-os'); import ast; [ast.parse(open('/usr/lib/encore-os/' + f).read()) for f in ('home.py', 'welcome.py', 'encore_os.py')]" 	&& ok "Home and Welcome parse with the image's Python" || bad "Home/Welcome don't parse with the image's Python"
[ -f "$m/etc/xdg/autostart/piwiz.desktop" ] && note "first boot" "the setup wizard (piwiz) starts on first boot unless Imager set things up; first user: $(awk -F: '$3 == 1000 { print $1 }' "$m/etc/passwd")" || note "first boot" "no piwiz autostart entry"
browser=$(ls "$m"/usr/bin/chromium "$m"/usr/bin/chromium-browser 2>/dev/null | head -n 1)
[ -n "$browser" ] && ok "browser ${browser#$m}" || bad "no Chromium"

# Audio
f /etc/security/limits.d/audio.conf
grep -q "rtprio" "$m/etc/security/limits.d/audio.conf" 2>/dev/null && ok "rtprio limit" || bad "no rtprio limit"
f /etc/pipewire/pipewire.conf.d/90-encore-low-latency.conf
f /etc/pipewire/jack.conf.d/90-encore-jack.conf
f /etc/systemd/system/user@.service.d/encore-audio.conf
[ -L "$m/etc/systemd/system/multi-user.target.wants/encore-performance.service" ] && ok "performance mode enabled" || bad "encore-performance.service not enabled"
ls "$m"/etc/ld.so.conf.d/pipewire-jack-*.conf >/dev/null 2>&1 && ok "JACK through PipeWire" || bad "pipewire-jack ld.so.conf missing"
for p in pipewire wireplumber pipewire-jack rtkit pavucontrol rpd-wayland-core piwiz labwc; do
	chroot "$m" dpkg-query -W -f='${Status}' "$p" 2>/dev/null | grep -q "install ok installed" && ok "package $p" || bad "package $p not installed"
done

# Users, passwords, name
user=$(awk -F: '$3 == 1000 { print $1 }' "$m/etc/passwd")
grep -qE "^audio:.*\b$user\b" "$m/etc/group" && ok "$user is in the audio group" || bad "$user is not in the audio group"
for u in root "$user"; do
	hash=$(awk -F: -v u="$u" '$1 == u { print $2 }' "$m/etc/shadow")
	case "$hash" in '!'*|'*'*|'') ok "$u has no usable password" ;; *) bad "$u has a password baked in" ;; esac
done
host=$(cat "$m/etc/hostname")
[ "$host" = encore ] && ok "hostname encore" || bad "hostname is $host"
grep -q "ENCORE. OS" "$m/etc/issue" && ok "console says ENCORE. OS" || bad "/etc/issue doesn't say ENCORE. OS"
grep -q "systemd.run" "$m/boot/firmware/cmdline.txt" && bad "cmdline.txt already has a first-run hook" || ok "cmdline.txt clean: $(cat "$m/boot/firmware/cmdline.txt")"
# Raspberry Pi Imager's settings (user name, password, Wi-Fi) arrive through cloud-init on Trixie
chroot "$m" dpkg-query -W -f='${Status}' cloud-init 2>/dev/null | grep -q "install ok installed" \
	&& [ -f "$m/boot/firmware/user-data" ] && [ -f "$m/boot/firmware/meta-data" ] && [ -f "$m/boot/firmware/network-config" ] \
	&& ok "Imager customisation: cloud-init and its files on the boot partition" || bad "cloud-init or its boot-partition files are missing (Imager customisation would not work)"

# Plugins
# the five ENCORE. plugins, as VST3 and LV2 (ENCORE. VST's release), for other music apps
for p in Vox Verb Equalize Master Strum; do
	[ -d "$m/usr/lib/vst3/ENCORE $p.vst3" ] && ok "VST3 ENCORE. $p" || bad "no /usr/lib/vst3/ENCORE $p.vst3"
	[ -d "$m/usr/lib/lv2/ENCORE $p.lv2" ] && ok "LV2 ENCORE. $p" || bad "no /usr/lib/lv2/ENCORE $p.lv2"
done

# Run it: libraries resolve, and the self-test passes, inside the image
if [ "$(uname -m)" = aarch64 ]; then
	mount -t tmpfs tmpfs "$m/tmp"
	mount --bind /dev "$m/dev"; mount --bind /dev/pts "$m/dev/pts"
	mount -t proc proc "$m/proc"; mount -t sysfs sys "$m/sys"
	missing=$(chroot "$m" ldd "/opt/encore-basement-studio/ENCORE Basement Studio" | grep "not found" || true)
	[ -z "$missing" ] && ok "all libraries found" || bad "libraries missing: $missing"
	while IFS= read -r -d '' so; do
		so="${so#$m}"
		missing=$(chroot "$m" ldd "$so" | grep "not found" || true)
		[ -z "$missing" ] && ok "plugin libraries found: $so" || bad "plugin $so is missing: $missing"
	done < <(find "$m/usr/lib/vst3" "$m/usr/lib/lv2" -name '*.so' -print0 2>/dev/null)
	mkdir -p "$m/tmp/.X11-unix"
	Xvfb :77 -screen 0 1920x1080x24 -nolisten tcp &
	for i in $(seq 1 20); do [ -e /tmp/.X11-unix/X77 ] && break; sleep 0.5; done
	mount --bind /tmp/.X11-unix "$m/tmp/.X11-unix"
	code=0
	chroot "$m" /usr/bin/env -i HOME=/tmp/home DISPLAY=:77 PATH=/usr/bin:/bin \
		sh -c 'mkdir -p /tmp/home && timeout 300 encore-basement-studio --selftest /tmp/selftest' || code=$?
	cat "$m/tmp/selftest/selftest.log" 2>/dev/null || true
	passed=$(grep -c '^PASS' "$m/tmp/selftest/selftest.log" 2>/dev/null || echo 0)
	note "self-test inside the image" "exit $code, $passed checks passed, $(tail -n 1 "$m/tmp/selftest/selftest.log" 2>/dev/null)"
	[ "$code" -eq 0 ] && ok "self-test in the image" || bad "ENCORE. Basement Studio's self-test failed inside the image (exit $code)"
fi

echo "image check: $fails problem(s)"
[ "$fails" -eq 0 ]
