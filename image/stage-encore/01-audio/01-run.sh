#!/bin/bash -e
# ENCORE. for Raspberry Pi: audio set up for music

install -v -m 644 files/audio.conf "${ROOTFS_DIR}/etc/security/limits.d/audio.conf"
install -v -m 644 -D files/90-encore-low-latency.conf "${ROOTFS_DIR}/etc/pipewire/pipewire.conf.d/90-encore-low-latency.conf"
install -v -m 644 -D files/90-encore-jack.conf "${ROOTFS_DIR}/etc/pipewire/jack.conf.d/90-encore-jack.conf"
install -v -m 644 -D files/encore-user-limits.conf "${ROOTFS_DIR}/etc/systemd/system/user@.service.d/encore-audio.conf"
install -v -m 644 files/encore-performance.service "${ROOTFS_DIR}/etc/systemd/system/encore-performance.service"

# limits.d only applies to sessions that use pam_limits: make sure the desktop login does
for f in lightdm lightdm-autologin; do
	p="${ROOTFS_DIR}/etc/pam.d/$f"
	if [ -f "$p" ] && ! grep -q pam_limits "$p"; then
		echo "session required pam_limits.so" >> "$p"
		echo "[encore] added pam_limits to /etc/pam.d/$f"
	fi
done

on_chroot << EOF2
set -e
# JACK apps use PipeWire's JACK library instead of a separate JACK server
ex=\$(ls /usr/share/doc/pipewire/examples/ld.so.conf.d/pipewire-jack-*.conf 2>/dev/null | head -n 1 || true)
if [ -n "\$ex" ]; then
	cp "\$ex" /etc/ld.so.conf.d/
	ldconfig
	echo "[encore] JACK goes through PipeWire (\$(basename "\$ex"))"
else
	echo "[encore] WARNING: no pipewire-jack ld.so.conf example found, JACK apps need pw-jack"
fi
adduser "${FIRST_USER_NAME}" audio
systemctl enable encore-performance.service
EOF2
