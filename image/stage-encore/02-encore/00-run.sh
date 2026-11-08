#!/bin/bash -e
# ENCORE. OS: ENCORE. Basement Studio and the ENCORE. plugins (the releases pins.conf names)

shopt -s nullglob
debs=(files/*.deb)
if [ ${#debs[@]} -eq 0 ]; then
	echo "[encore] ERROR: no ENCORE. Basement Studio .deb in $(pwd)/files"
	exit 1
fi
install -d "${ROOTFS_DIR}/tmp/encore"
cp -v "${debs[@]}" "${ROOTFS_DIR}/tmp/encore/"
on_chroot << EOF2
set -e
apt-get -o Acquire::Retries=3 install -y --no-remove /tmp/encore/*.deb
dpkg-query -W -f='[encore] installed \${Package} \${Version}\n' encore-basement-studio
EOF2
rm -rf "${ROOTFS_DIR}/tmp/encore"

# The ENCORE. plugins (VST3 and LV2) for other music apps, in the standard
# system-wide folders every Linux host looks in
for kind in VST3:vst3 LV2:lv2; do
	src="files/plugins/${kind%%:*}"
	dst="${ROOTFS_DIR}/usr/lib/${kind##*:}"
	if [ -d "$src" ] && [ -n "$(ls -A "$src")" ]; then
		install -d "$dst"
		cp -r "$src"/. "$dst"/
		chmod -R u=rwX,go=rX "$dst"
		echo "[encore] plugins ${kind%%:*}: $(ls "$src" | tr '\n' ' ')"
	else
		echo "[encore] ERROR: no ${kind%%:*} plugins to install (ENCORE. VST's release files)"
		exit 1
	fi
done

# No default password anywhere: the login is set by Raspberry Pi Imager or
# the first-boot wizard. pi-gen gives root the password "root"; lock it.
on_chroot << EOF2
usermod -p '!' root
EOF2
