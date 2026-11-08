#!/bin/bash -e
# ENCORE. OS: Chromium bookmarks, one-click desktop icons, a desktop config per screen

# (ENCORE. Home, the ENCORE. tile, the session start-up and the look come from the encore-os
# package, installed by the next step, 04-encore-os)
install -v -m 644 -D files/chromium-managed.json "${ROOTFS_DIR}/etc/chromium/policies/managed/encore.json"
install -v -m 644 -D files/chromium-recommended.json "${ROOTFS_DIR}/etc/chromium/policies/recommended/encore.json"

# Desktop icons open with one double-click, no "execute this file?" question
libfm="${ROOTFS_DIR}/etc/xdg/libfm/libfm.conf"
if [ -f "$libfm" ]; then
	if grep -q '^quick_exec=' "$libfm"; then
		sed -i 's/^quick_exec=.*/quick_exec=1/' "$libfm"
	else
		sed -i '/^\[config\]/a quick_exec=1' "$libfm"
	fi
	echo "[encore] libfm: $(grep quick_exec "$libfm")"
fi

# One desktop config per screen, so the ENCORE. wallpaper (set by encore-os) shows on all of them
if true; then
	shopt -s nullglob
	# the Wayland desktop keeps one file per screen (desktop-items-<screen>.conf);
	# give the usual Pi screens one too, copied from the main one, so every screen gets it
	for d in "${ROOTFS_DIR}"/etc/xdg/pcmanfm/*/; do
		[ -f "$d/desktop-items-0.conf" ] || continue
		for out in HDMI-A-1 HDMI-A-2 DSI-1 DSI-2 Composite-1 NOOP-1; do
			[ -f "$d/desktop-items-$out.conf" ] || cp "$d/desktop-items-0.conf" "$d/desktop-items-$out.conf"
		done
	done
	confs=("${ROOTFS_DIR}"/etc/xdg/pcmanfm/*/desktop-items-*.conf)
	for c in "${confs[@]}"; do
		echo "[encore] desktop config ${c#${ROOTFS_DIR}}"
	done
	[ ${#confs[@]} -gt 0 ] || echo "[encore] WARNING: no pcmanfm desktop-items config found"
fi
