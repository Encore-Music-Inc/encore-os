#!/bin/bash -e
# Log straight into the desktop (B4), on Wayland with labwc (W2 on Trixie)
on_chroot << EOF2
	SUDO_USER="${FIRST_USER_NAME}" raspi-config nonint do_boot_behaviour B4
	SUDO_USER="${FIRST_USER_NAME}" raspi-config nonint do_wayland W2
EOF2
install -v -o 1000 -g 1000 -d "${ROOTFS_DIR}/home/${FIRST_USER_NAME}/.local/share/applications"
install -v -o 1000 -g 1000 -d "${ROOTFS_DIR}/home/${FIRST_USER_NAME}/.local/share/desktop-directories"
