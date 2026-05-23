# slimbook-executive-minimal

Two-package Slimbook Executive driver bundle for Fedora Sway Atomic 44.

After `rpm-ostree install` + reboot, two packages are layered:

  - `libslimbook1` — `slimbookctl` CLI, `slimbook-settings.service`
    systemd unit, udev rule that fires when `qc71_laptop` loads, and a
    system-sleep hook that preserves QC71-EC settings across suspend.
  - `slimbook-executive-minimal` — pre-built `qc71_laptop.ko.xz`
    pinned to the target Atomic kernel.

Not included: `slimbook-service` (GTK3 tray), `python3-slimbook`, the
akmods build toolchain, any model-irrelevant Slimbook extras.

On kernel upgrade the RPM needs to be rebuilt against the new kernel.
See the repo `README.md` for the build steps.
