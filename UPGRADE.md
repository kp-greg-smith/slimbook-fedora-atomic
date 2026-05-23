# Install and upgrade workflow

Every command in this file was tested in a QEMU Fedora Sway Atomic 44
VM. What this says works is what actually happened in the VM.

## One-time setup on the Atomic host

```bash
# Slimbook repo (needed for libslimbook1 dep)
sudo curl -L -o /etc/yum.repos.d/home:Slimbook.repo \
    https://download.opensuse.org/repositories/home:/Slimbook/Fedora_44/home:Slimbook.repo

# Toolbox container for the kmod build (keeps the host layer slim)
toolbox create -y -i registry.fedoraproject.org/fedora-toolbox:44 fedora44-build
toolbox run -c fedora44-build sudo dnf install -y \
    --setopt=install_weak_deps=False \
    rpm-build gcc make xz kernel-devel curl
```

The toolbox's `kernel-devel` will be the latest available in the F44
repos. Confirm it matches what your Atomic deployment is shipping:

```bash
$ rpm-ostree status | grep -A1 booted | head        # host kernel via rpm-ostree
$ toolbox run -c fedora44-build rpm -q kernel-devel  # toolbox kernel headers
```

If they don't match, install the matching version explicitly:
`toolbox run -c fedora44-build sudo dnf install -y "kernel-devel-uname-r = <KVER>"`.

## Build the RPM

The toolbox shares your home dir, so the resulting RPM appears in
`~/rpmbuild/RPMS/x86_64/` on the host.

```bash
toolbox run -c fedora44-build bash <<'EOF'
set -e
REPO=/path/to/this/repo

mkdir -p ~/rpmbuild/{SPECS,SOURCES}
cp $REPO/rpm/slimbook-executive-minimal.spec ~/rpmbuild/SPECS/
cp $REPO/rpm/README.md ~/rpmbuild/SOURCES/

cd /tmp
curl -sLO https://download.opensuse.org/repositories/home:/Slimbook/Fedora_44/src/slimbook-qc71-kmod-1.0.1-1.1.src.rpm
rpm2archive < slimbook-qc71-kmod-1.0.1-1.1.src.rpm | \
    tar -xzf - --strip-components=1 -C ~/rpmbuild/SOURCES/ ./qc71_laptop-1.0.1.tar.gz

KVER=$(rpm -q --qf "%{VERSION}-%{RELEASE}.%{ARCH}\n" kernel-devel | tail -1)
rpmbuild --define "kver $KVER" -ba ~/rpmbuild/SPECS/slimbook-executive-minimal.spec
EOF
```

## First install

```bash
sudo rpm-ostree install ~/rpmbuild/RPMS/x86_64/slimbook-executive-minimal-*.rpm
sudo systemctl reboot
```

After reboot: `lsmod | grep qc71_laptop`, `slimbookctl info`.

Verified VM output of `rpm-ostree status` after this:

```
● ostree-unverified-registry:quay.io/fedora-ostree-desktops/sway-atomic:44
   ...
   LocalPackages: slimbook-executive-minimal-2.0.0-1.fc44.x86_64
```

## When a kernel upgrade comes (the swap)

Atomic releases a new kernel inside a new base image. Your layered RPM
pins to the **old** kernel via
`Requires: kernel-core-uname-r = <old-version>`.

### 1. See if an update is pending

```bash
$ sudo rpm-ostree update --check
```

Possible outputs (verified):
- `No updates available.` — nothing to do.
- Anything else — read the version info and proceed.

### 2. Try the upgrade

```bash
$ sudo rpm-ostree update
```

If the new base has the **same** kernel version, this just works.

If the new base has a **different** kernel, you'll get (verified
verbatim with a synthetic test):

```
error: Could not depsolve transaction; 1 problem detected:
 Problem: conflicting requests
  - nothing provides kernel-core-uname-r = <NEW_KVER> needed by
    slimbook-executive-minimal-X.Y-Z.fc44.x86_64
```

This is the **safety net**, not a failure: rpm-ostree refused to stage a
broken deployment. Note the `<NEW_KVER>` shown in the error.

### 3. Rebuild the kmod for the new kernel + swap in one transaction

```bash
# In the toolbox: install matching kernel-devel and rebuild
toolbox run -c fedora44-build bash -c '
    sudo dnf install -y "kernel-devel-uname-r = <NEW_KVER>"
    rpmbuild --define "kver <NEW_KVER>" -ba ~/rpmbuild/SPECS/slimbook-executive-minimal.spec
'

# On the Atomic host: one transaction = base upgrade + remove old kmod + install new kmod
sudo rpm-ostree update \
     --uninstall slimbook-executive-minimal \
     --install ~/rpmbuild/RPMS/x86_64/slimbook-executive-minimal-*.rpm
sudo systemctl reboot
```

Verified VM output of the swap transaction:

```
Resolving dependencies...done
...
Upgraded:
  slimbook-executive-minimal 2.0.0-1.fc44 -> 2.0.0-2.fc44
Run "systemctl reboot" to start a reboot
```

The old deployment (with the old kernel and old kmod) is kept around as
the rollback target. Once you've rebooted into the new deployment and
confirmed things work, `sudo rpm-ostree cleanup -r` reclaims the space.

## Why no hook / no automation?

I'd considered a systemd unit that watches `rpm-ostreed`'s D-Bus signals
and triggers a rebuild. The hook itself is straightforward — what isn't
straightforward is **where the build runs**. You'd need one of:

  - `kernel-devel` + `gcc` + `make` + `rpm-build` inside the layer
    (defeats the whole point of this repo).
  - Remote CI that publishes per-kernel RPMs (overkill for one laptop).
  - A pre-installed toolbox plus a script (which is exactly the manual
    procedure above, just wrapped). At that point a hook saves you the
    one-line `rpm-ostree update` call but adds a script you have to
    maintain.

The block-on-mismatch behavior is a useful signal — it tells you
*before* a reboot that a kernel is changing. Two commands per kernel
update (`toolbox run … rpmbuild …` and `sudo rpm-ostree update
--uninstall … --install …`) is small enough that the automation isn't
worth the moving parts.
