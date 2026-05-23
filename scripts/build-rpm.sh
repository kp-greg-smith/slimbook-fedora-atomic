#!/usr/bin/env bash
# Build slimbook-executive-minimal RPM inside a disposable Fedora 44 podman container.
# Usage: scripts/build-rpm.sh [target-kernel-version]
#   - no arg     → build against the latest kernel-devel available in F44 repos
#   - kernel ver → build against the specified version (e.g. 7.0.9-205.fc44.x86_64)
#
# Output: artifacts/slimbook-executive-minimal-*.rpm
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS="$REPO_ROOT/artifacts"
SPEC_DIR="$REPO_ROOT/rpm"
TARGET_KVER="${1:-}"
IMAGE="registry.fedoraproject.org/fedora:44"

mkdir -p "$ARTIFACTS"

podman run --rm \
    -v "$SPEC_DIR:/spec:ro,Z" \
    -v "$ARTIFACTS:/out:Z" \
    -e TARGET_KVER="$TARGET_KVER" \
    "$IMAGE" bash -euo pipefail -c '
        echo ">>> installing build deps"
        dnf install -q -y --setopt=install_weak_deps=False \
            rpm-build gcc make xz curl tar >/dev/null

        if [ -n "${TARGET_KVER}" ]; then
            echo ">>> installing kernel-devel for ${TARGET_KVER}"
            dnf install -q -y "kernel-devel-uname-r = ${TARGET_KVER}" >/dev/null
            KVER="${TARGET_KVER}"
        else
            echo ">>> installing latest kernel-devel"
            dnf install -q -y kernel-devel >/dev/null
            KVER=$(rpm -q --qf "%{VERSION}-%{RELEASE}.%{ARCH}\n" kernel-devel | tail -1)
        fi
        echo ">>> building against kernel ${KVER}"

        mkdir -p /root/rpmbuild/{SPECS,SOURCES}
        cp /spec/slimbook-executive-minimal.spec /root/rpmbuild/SPECS/
        cp /spec/README.md /root/rpmbuild/SOURCES/

        cd /tmp
        curl -sLO https://download.opensuse.org/repositories/home:/Slimbook/Fedora_44/src/slimbook-qc71-kmod-1.0.1-1.1.src.rpm
        rpm2archive < slimbook-qc71-kmod-1.0.1-1.1.src.rpm \
            | tar -xzf - --strip-components=1 -C /root/rpmbuild/SOURCES/ ./qc71_laptop-1.0.1.tar.gz

        rpmbuild --define "kver $KVER" --quiet -ba /root/rpmbuild/SPECS/slimbook-executive-minimal.spec

        cp /root/rpmbuild/RPMS/x86_64/*.rpm /out/
        echo ">>> built:"
        ls -la /out/slimbook-executive-minimal-*.rpm
    '

echo
echo "RPM(s) in $ARTIFACTS/:"
ls -1 "$ARTIFACTS"/slimbook-executive-minimal-*.rpm
