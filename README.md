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

```bash
# 1. Enable the upstream Slimbook repo (one-off, needed for the libslimbook1 dependency)
sudo curl -L -o /etc/yum.repos.d/home:Slimbook.repo \
    https://download.opensuse.org/repositories/home:/Slimbook/Fedora_44/home:Slimbook.repo

# 2. Build (see above)
./scripts/build-rpm.sh

# 3. Layer the RPM you just built
sudo rpm-ostree install ./artifacts/slimbook-executive-minimal-*.rpm
sudo systemctl reboot
```

After reboot, `lsmod | grep qc71_laptop` shows the module loaded and
`slimbookctl info` prints the detected hardware profile.

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

Use `scripts/build-rpm.sh`. It spins up a disposable Fedora 44
container with rootless **podman**, installs `kernel-devel` + `gcc` +
`rpm-build` inside it, builds the module, and drops the RPM into
`artifacts/`. Nothing is layered onto your Atomic host.

```bash
# Default: build against the latest kernel-devel available in F44 repos
./scripts/build-rpm.sh

# Target a specific kernel (e.g. one that an upgrade is about to bring)
./scripts/build-rpm.sh 7.0.9-205.fc44.x86_64
```

Output: `artifacts/slimbook-executive-minimal-2.0.0-1.fc44.x86_64.rpm`.

The resulting RPM has only two declared dependencies:
`Requires: libslimbook1` and `Requires: kernel-core-uname-r = <kver>`.

## Upgrades

When a kernel upgrade comes through `rpm-ostree update`, the pinned
`Requires: kernel-core-uname-r = <old>` makes the transaction refuse to
apply — your system stays on the old, working deployment. To move
forward, rebuild the RPM for the new kernel and do the upgrade and the
kmod swap in one transaction.

`scripts/upgrade.sh` does this:

```bash
sudo ./scripts/upgrade.sh
```

It probes `rpm-ostree update`, parses the new kernel version out of the
depsolve error, calls `build-rpm.sh` for that kernel, then stages
`rpm-ostree update --uninstall slimbook-executive-minimal --install <new.rpm>`
as one transaction. You reboot when it's done.

For a deeper walkthrough including the verbatim VM outputs at each step,
see `UPGRADE.md`.

## Files in this repo

```
scripts/
  build-rpm.sh                                            ← podman build, output → artifacts/
  upgrade.sh                                              ← rpm-ostree update + swap in one go
rpm/
  slimbook-executive-minimal.spec                         ← source of truth; spec auto-detects kver
  README.md                                               ← shipped inside the RPM
artifacts/
  rpm-ostree-status-{clean,official,minimal}.txt          ← VM-captured proof of layer contents
  db-diff-{official,minimal}.txt                          ← exact per-package lists for each layer
notes/
  01-upstream-repo-cataloged.md                           ← background: what's in the Slimbook repo
UPGRADE.md                                                ← step-by-step verified upgrade walkthrough
```

RPMs are deliberately not checked in (`*.rpm` is in `.gitignore`). The
spec is the source of truth — build per-kernel.
