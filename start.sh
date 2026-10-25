#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
exec 9>"${XDG_RUNTIME_DIR:-/tmp}/usb-camera-preview-${UID}.lock"
flock -n 9 || exit 0
if [ ! -x .venv/bin/python ]; then
    python3 -m venv .venv
fi
if ! .venv/bin/python -c 'import PySide6.QtMultimediaWidgets' >/dev/null 2>&1; then
    .venv/bin/python -m pip install -r requirements.txt
fi
exec .venv/bin/python camera_preview.py "$@"
