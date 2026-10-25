#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
: "${APT_SIGNING_FINGERPRINT:?Set APT_SIGNING_FINGERPRINT}"
repo=build/apt-repo
rm -rf -- "$repo"
mkdir -p "$repo/pool/main" "$repo/dists/stable/main/binary-amd64"
cp dist/usb-camera-preview_*_amd64.deb "$repo/pool/main/"
gpg --batch --export "$APT_SIGNING_FINGERPRINT" > "$repo/apt-key.gpg"
test -s "$repo/apt-key.gpg"
(
    cd "$repo"
    apt-ftparchive packages pool > dists/stable/main/binary-amd64/Packages
    gzip -n -9 -c dists/stable/main/binary-amd64/Packages > dists/stable/main/binary-amd64/Packages.gz
    apt-ftparchive \
        -o APT::FTPArchive::Release::Origin='leavs Camera' \
        -o APT::FTPArchive::Release::Label='USB Camera Preview' \
        -o APT::FTPArchive::Release::Suite=stable \
        -o APT::FTPArchive::Release::Codename=stable \
        -o APT::FTPArchive::Release::Architectures=amd64 \
        -o APT::FTPArchive::Release::Components=main \
        release dists/stable > dists/stable/Release
    gpg --batch --yes --local-user "$APT_SIGNING_FINGERPRINT" --digest-algo SHA256 \
        --clearsign --output dists/stable/InRelease dists/stable/Release
    gpg --batch --yes --local-user "$APT_SIGNING_FINGERPRINT" --digest-algo SHA256 \
        --armor --detach-sign --output dists/stable/Release.gpg dists/stable/Release
    gpgv --keyring "$PWD/apt-key.gpg" dists/stable/InRelease
)
cp packaging/apt-index.html "$repo/index.html"
touch "$repo/.nojekyll"
echo "APT repository: $repo"
