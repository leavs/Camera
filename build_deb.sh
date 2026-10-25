#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
version="${1:-1.0.0}"
if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo 'Version must have the form 1.0.0' >&2
    exit 1
fi
architecture="$(dpkg --print-architecture)"
python_bin="${BUILD_PYTHON:-.venv/bin/python}"
if [ ! -x "$python_bin" ]; then
    python3 -m venv .venv
fi
"$python_bin" -m pip install -r requirements-build.txt
"$python_bin" -m PyInstaller --noconfirm --clean --onedir \
    --name usb-camera-preview --distpath build/bundle --workpath build/pyinstaller \
    --specpath build camera_preview.py
stage="build/deb-root"
rm -rf -- "$stage"
install -d "$stage/DEBIAN" "$stage/opt" "$stage/usr/bin" \
    "$stage/usr/share/applications" "$stage/usr/share/icons/hicolor/scalable/apps" \
    "$stage/usr/share/doc/usb-camera-preview"
cp -a build/bundle/usb-camera-preview "$stage/opt/"
install -m 755 packaging/launcher.sh "$stage/usr/bin/usb-camera-preview"
install -m 644 packaging/usb-camera-preview.desktop "$stage/usr/share/applications/"
install -m 644 camera-icon.svg "$stage/usr/share/icons/hicolor/scalable/apps/usb-camera-preview.svg"
install -m 644 README.md "$stage/usr/share/doc/usb-camera-preview/README.md"
size="$(du -sk "$stage" | cut -f1)"
cat > "$stage/DEBIAN/control" <<EOF
Package: usb-camera-preview
Version: $version
Section: video
Priority: optional
Architecture: $architecture
Maintainer: Liu Xiaoqiang <leavs_o@126.com>
Installed-Size: $size
Depends: libc6 (>= 2.39), libstdc++6, libgcc-s1, libglib2.0-0t64, libgl1, libegl1, libx11-6, libx11-xcb1, libxext6, libxrender1, libxi6, libxcb1, libxcb-cursor0, libxcb-icccm4, libxcb-image0, libxcb-keysyms1, libxcb-randr0, libxcb-render0, libxcb-render-util0, libxcb-shape0, libxcb-shm0, libxcb-sync1, libxcb-xfixes0, libxcb-xkb1, libxkbcommon0, libxkbcommon-x11-0, libfontconfig1, libfreetype6, libdbus-1-3, libsm6, libice6, zlib1g, util-linux
Homepage: https://github.com/leavs/Camera
Description: Floating USB camera live preview
 Always-on-top draggable camera preview with work-area boundaries,
 camera selection and desktop integration. Bundles Python and Qt.
 Built for Ubuntu 24.04 and compatible systems with glibc 2.39 or newer.
EOF
mkdir -p dist
output="dist/usb-camera-preview_${version}_${architecture}.deb"
dpkg-deb --root-owner-group -Zxz --build "$stage" "$output"
sha256sum "$output" > "$output.sha256"
echo "Built: $output"
