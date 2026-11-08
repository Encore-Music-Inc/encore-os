#!/bin/bash -e
# ENCORE. for Raspberry Pi: starts from the previous stage (stage3, the base desktop)
if [ ! -d "${ROOTFS_DIR}" ]; then
	copy_previous
fi
