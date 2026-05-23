#!/usr/bin/env bash
# Atomic upgrade + slimbook kmod swap in one transaction.
#
# Flow:
#   1. Probe for a pending OS update.
#   2. If the new base wants a different kernel, find out which.
#   3. Build a new slimbook-executive-minimal RPM for that kernel (via build-rpm.sh).
#   4. Stage one rpm-ostree transaction: pull new base + uninstall old kmod RPM + install new kmod RPM.
#   5. Print the reboot instruction.
#
# Usage: sudo scripts/upgrade.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS="$REPO_ROOT/artifacts"

if [[ $EUID -ne 0 ]]; then
    echo "Run with sudo (rpm-ostree commands need root)." >&2
    exit 1
fi

PKG=slimbook-executive-minimal

echo ">>> probing for pending update"
OUT=$(rpm-ostree update 2>&1 || true)

if grep -qiE "No (upgrade|update)s? available" <<<"$OUT"; then
    echo ">>> no update pending."
    exit 0
fi

# Extract target kernel from the depsolve error, if any.
TARGET_KVER=$(grep -oP 'nothing provides kernel-core-uname-r = \K[A-Za-z0-9._+-]+' <<<"$OUT" | head -1)

if [[ -z "$TARGET_KVER" ]]; then
    if grep -qE "Run \"?systemctl reboot|Staging deployment" <<<"$OUT"; then
        echo ">>> update staged without kernel-pin conflict. Reboot to apply:"
        echo "    sudo systemctl reboot"
        exit 0
    fi
    echo ">>> unexpected output from rpm-ostree update:" >&2
    echo "$OUT" >&2
    exit 1
fi

echo ">>> new kernel pending: $TARGET_KVER"
echo ">>> building $PKG for $TARGET_KVER"
sudo -u "${SUDO_USER:-$USER}" "$REPO_ROOT/scripts/build-rpm.sh" "$TARGET_KVER"

NEW_RPM=$(ls -t "$ARTIFACTS"/${PKG}-*.rpm 2>/dev/null | head -1)
if [[ -z "$NEW_RPM" ]]; then
    echo ">>> build did not produce an RPM in $ARTIFACTS" >&2
    exit 1
fi

echo ">>> staging combined transaction: base upgrade + swap to $NEW_RPM"
rpm-ostree update --uninstall "$PKG" --install "$NEW_RPM"

echo
echo ">>> done. Reboot to apply:"
echo "    sudo systemctl reboot"
