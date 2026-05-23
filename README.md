# slimbook-executive-minimal

Two-package driver bundle for the **Slimbook Executive** on **Fedora
Sway Atomic 44**. Nothing else.

## What it offers

| Component | What it does |
|---|---|
| `qc71_laptop.ko.xz` | Kernel platform driver for the QC71 Embedded Controller. Without it, userspace cannot see or change: keyboard backlight (color/brightness), fan curve and fan mode, battery charge thresholds (e.g. stop charging at 80%), airplane-mode toggle, super-key lock, fn-lock. |
| `libslimbook1` | The userspace side. Ships: `slimbookctl` (CLI to read/write all of the above), `slimbook-settings.service` (systemd oneshot that re-applies your saved settings on boot, triggered by a udev rule when the kernel module loads), and a `/usr/lib/systemd/system-sleep/` hook that saves EC state before suspend and restores it after resume (the QC71 EC drops settings like the battery charge limit across S3). |

That's it. No GTK3 tray indicator, no Python daemons, no akmods build
toolchain, no RGB-keyboard packages from other Slimbook models, no
AMD-only grub fixes, no Motorcomm-Ethernet driver, no
notifications/feedparser/zmq/X11/icon-themes/codec-libs.

## Layered on top of Fedora Sway Atomic 44

```
$ rpm-ostree status                                # official setup
LayeredPackages: slimbook-meta-common slimbook-meta-executive
                 # → 142 packages added to the layer

$ rpm-ostree status                                # this package
LocalPackages:   slimbook-executive-minimal-2.0.0-1.fc44.x86_64
                 # → 2 packages added to the layer (libslimbook1 + this)
```

Full captures: `artifacts/rpm-ostree-status-{official,minimal}.txt`.
Full per-package diffs: `artifacts/db-diff-{official,minimal}.txt`.

## Install

Build the RPM first (see *Build* below — pinned to your running kernel),
then:

```bash
# 1. Enable the upstream Slimbook repo (one curl, only needed for the libslimbook1 dependency)
sudo curl -L -o /etc/yum.repos.d/home:Slimbook.repo \
    https://download.opensuse.org/repositories/home:/Slimbook/Fedora_44/home:Slimbook.repo

# 2. Layer the RPM you just built
sudo rpm-ostree install ~/rpmbuild/RPMS/x86_64/slimbook-executive-minimal-*.rpm

# 3. Reboot
sudo systemctl reboot
```

After reboot, `lsmod | grep qc71_laptop` should show the module loaded
and `slimbookctl info` should print the detected hardware profile.

## Kernel-upgrade caveat

The `.ko.xz` is built against a **specific kernel version** (currently
`7.0.9-205.fc44.x86_64`) and the RPM has
`Requires: kernel-core-uname-r = 7.0.9-205.fc44.x86_64`.

When `rpm-ostree upgrade` brings in a newer kernel, the layered package
will fail to apply on the new deployment until a matching RPM is built.
Two options:

  * **Manual:** rebuild the RPM against the new kernel version (see
    "Build" below) and re-layer it.
  * **Pin the kernel:** `sudo rpm-ostree override replace …` to hold
    the kernel at the current version until you're ready.

If you want hands-off auto-rebuild and don't mind the 130-package build
toolchain in the layer, the official `slimbook-meta-{common,executive}`
route is what you want — that's exactly what akmods buys you.

## Build

The module is built once against the Atomic kernel, then packaged as a
binary blob. Reproduce:

```bash
# Inside any Fedora 44 system with kernel-devel matching the target Atomic kernel:
sudo dnf install -y kernel-devel-7.0.9-205.fc44 gcc make rpm-build

# Pull the QC71 source from the Slimbook src.rpm
rpm -i https://download.opensuse.org/repositories/home:/Slimbook/Fedora_44/src/slimbook-qc71-kmod-1.0.1-1.1.src.rpm
# (extracts to ~/rpmbuild/SOURCES/)

# Build the module against the target kernel
KVER=7.0.9-205.fc44.x86_64
cd ~/rpmbuild/SOURCES
tar -xf qc71_laptop-*.tar.gz
cd qc71_laptop-*
make -C /usr/src/kernels/$KVER M=$PWD
xz qc71_laptop.ko                # → qc71_laptop.ko.xz

# Build the RPM
cp qc71_laptop.ko.xz ~/rpmbuild/SOURCES/
cp <this-repo>/rpm/slimbook-executive-minimal.spec ~/rpmbuild/SPECS/
cp <this-repo>/rpm/README.md ~/rpmbuild/SOURCES/
rpmbuild --define "dist .fc44" -ba ~/rpmbuild/SPECS/slimbook-executive-minimal.spec
```

If you want a different target kernel, edit the `%global kver …` line at
the top of `rpm/slimbook-executive-minimal.spec` and rebuild.

## Files in this repo

```
rpm/
  slimbook-executive-minimal.spec                         ← source of truth; edit kver here
  README.md                                               ← shipped inside the RPM
artifacts/
  rpm-ostree-status-{clean,official,minimal}.txt          ← VM-captured proof of layer contents
  db-diff-{official,minimal}.txt                          ← exact per-package lists for each layer
notes/
  01-upstream-repo-cataloged.md                           ← background: what's in the Slimbook repo
```

RPMs are deliberately not checked in (`*.rpm` is in `.gitignore`). The
spec is the source of truth — build per-kernel.
