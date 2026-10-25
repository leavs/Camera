#!/bin/sh
set -eu
exec 9>"${XDG_RUNTIME_DIR:-/tmp}/usb-camera-preview-$(id -u).lock"
flock -n 9 || exit 0
exec /opt/usb-camera-preview/usb-camera-preview "$@"
