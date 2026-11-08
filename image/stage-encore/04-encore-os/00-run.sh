#!/bin/bash -e
# ENCORE. OS: the apps from defaults.conf, then the encore-os package (the look, boot
# animation, login screen, Home, Welcome, the ENCORE. tile), then boot settings.

shopt -s nullglob
debs=(files/encore-os_*.deb)
[ ${#debs[@]} -gt 0 ] || { echo "[encore] ERROR: no encore-os .deb in $(pwd)/files"; exit 1; }
defaults=files/defaults.conf
section() { awk -v s="[$1]" '/^\[/{on = ($0 == s); next} on && $0 !~ /^[[:space:]]*(#|$)/ {gsub(/[[:space:]]/, ""); print}' "$defaults"; }
apps=$(section apps | tr '\n' ' ')
remove=$(section remove | tr '\n' ' ')
echo "[encore] apps: $apps"

install -d "${ROOTFS_DIR}/tmp/encore-os"
cp -v "${debs[@]}" "${ROOTFS_DIR}/tmp/encore-os/"
# --no-remove: an app that clashes with the desktop fails the build here, instead of apt
# quietly removing the desktop to make room (pcmanfm did that: Trixie has pcmanfm-pi).
on_chroot << EOF2
set -e
export DEBIAN_FRONTEND=noninteractive ENCORE_OS_BUILDING=1
apt-get -o Acquire::Retries=3 install -y --no-remove $apps
apt-get -o Acquire::Retries=3 install -y --no-remove /tmp/encore-os/*.deb
if [ -n "$remove" ]; then apt-get purge -y $remove; apt-get autoremove -y; fi
dpkg-query -W -f='[encore] installed \${Package} \${Version}\n' encore-os
echo "[encore] boot animation: \$(plymouth-set-default-theme)"
EOF2
rm -rf "${ROOTFS_DIR}/tmp/encore-os"

# Boot: no rainbow square, no raspberries, no scrolling text, the ENCORE. animation instead.
# (The image build makes the boot files (initramfs) at the very end, with this theme in them.)
cmd="${ROOTFS_DIR}/boot/firmware/cmdline.txt"
for o in quiet splash plymouth.ignore-serial-consoles logo.nologo vt.global_cursor_default=0 loglevel=3; do
	grep -qw -- "$o" "$cmd" || sed -i "1 s/\$/ $o/" "$cmd"
done
echo "[encore] cmdline.txt: $(cat "$cmd")"
cfg="${ROOTFS_DIR}/boot/firmware/config.txt"
grep -q '^disable_splash=1' "$cfg" || printf '\n# ENCORE. OS: no rainbow square at power-on\ndisable_splash=1\n' >> "$cfg"

# What this is, for anyone (or any script) who asks
os_name=$(sed -nE 's/^name *= *(.*)/\1/p' "$defaults" | head -n 1)
os_ver=$(sed -nE 's/^version *= *(.*)/\1/p' "$defaults" | head -n 1)
os_code=$(sed -nE 's/^codename *= *(.*)/\1/p' "$defaults" | head -n 1)
base=$(. "${ROOTFS_DIR}/etc/os-release" && echo "${VERSION_CODENAME:-unknown}")
printf 'NAME="%s"\nVERSION="%s (%s)"\nBUILD_DATE=%s\nBASED_ON="Raspberry Pi OS (64-bit, %s)"\n' "$os_name" "$os_ver" "$os_code" "$(date -u +%Y-%m-%d)" "$base" \
	> "${ROOTFS_DIR}/etc/encore-os/release"
cat > "${ROOTFS_DIR}/etc/issue" <<EOF3
$os_name $os_ver \n \l

EOF3
echo "[encore] $(tr '\n' ' ' < "${ROOTFS_DIR}/etc/encore-os/release")"
