# Schritt 1 — Was steckt im Slimbook-Repo für Fedora 44?

Datum: 2026-05-22.  Repo-URL: `https://download.opensuse.org/repositories/home:/Slimbook/Fedora_44/`

## Verzeichnisstruktur

- `noarch/` — Meta-Pakete, Python-Module, kmod-common-Pakete
- `x86_64/` — kompilierte Binaries, akmod- und kmod-RPMs, GRUB-Fixes, Quirks
- `src/` — Source-RPMs
- `repodata/` — DNF-Metadaten
- `home:Slimbook.repo` — fertige Repo-Konfig zum Einbinden

## Inhalt nach Funktion

### Hardware-Treiber für QC71-Plattform (Executive nutzt QC71-Mainboard)

| Paket | Arch | Funktion |
|---|---|---|
| `slimbook-qc71-kmod-common-1.0.1-1.1` | noarch | Spec/kmodtool-Beilage, kein Payload |
| `akmod-slimbook-qc71-1.0.1-1.1` | x86_64 | Src-RPM des Moduls in `/usr/src/akmods/`. `akmods` baut beim Boot |
| `kmod-slimbook-qc71-1.0.1-1.1` | x86_64 | Meta ohne Payload — pinnt ein vorgebautes Modul |

Das Modul exportiert sich als `qc71_laptop`. Doku im RPM-Summary: *"Slimbook qc71 platform module for ProX, Executive and Hero laptops"*. → **Pflicht für Executive.**

### libslimbook1 (Userspace-Hardware-Integration)

`libslimbook1-1.23.0-2.1.x86_64.rpm` enthält:

- `/usr/lib64/libslimbook.so.1` — C-Library
- `/usr/bin/slimbookctl` — CLI (`config-load`, `config-store`, etc.)
- `/usr/bin/slimbook-hello` — Welcome-Banner (Shell-Script, harmlos)
- `/usr/lib/systemd/system/slimbook-settings.service` — Oneshot, lädt Settings beim Boot
- `/usr/lib/udev/rules.d/99-slimbook-settings.rules` — Triggert die Unit, sobald `qc71_laptop` oder `clevo_platform` Modul geladen ist
- `/usr/lib/systemd/system-sleep/slimbook-sleep` — Speichert vor Suspend, lädt nach Resume
- `/usr/libexec/slimbook/report-pack` + report.d/* — Diagnose-Helper (Slimbook-Support)

Echtes Hardware-Werk. Keine GUI-Abhängigkeit. → **Pflicht für Executive.**

### slimbook-service (GUI-Tray-Daemon — DESKTOP-spezifisch)

`slimbook-service-1.0.10-3.1.noarch.rpm`:

- `/usr/bin/slimbookindicator` — GTK3 + AppIndicator-Tray-App
- `/usr/share/slimbook/event-notify.py` — systemd-Service, sendet Events via ZMQ
- `/usr/share/slimbook/client.py` — GTK3-Frontend
- `/etc/xdg/autostart/slimbook-client-autostart.desktop` — XDG-Autostart

Requires: `gtk3`, `adwaita-icon-theme`, `libappindicator-gtk3`, `libnotify`, `python3-dateutil`, `python3-evdev`, `python3-feedparser`, `python3-pyudev`, `python3-requests`, `python3-zmq`, `python3-slimbook`.

Funktionalität: Touchpad-Lock-Hotkey, Power-Profile-Switching (delegiert an `powerprofilesctl`/`tuned-adm`), AC-Notifications.

Auf Sway:
- Es gibt keinen XDG-Tray; das Indicator-Icon erscheint nicht.
- Power-Profile lassen sich auch direkt mit `powerprofilesctl` schalten.
- Der GTK3-Stack ist auf einem reinen Sway-System sonst nicht installiert.

→ **Für Sway-Executive überflüssig. Streichen.**

### python3-slimbook

Python-Bindings für libslimbook (`slimbook.qc71`, `slimbook.smbios`, `slimbook.kbd`, …). Wird nur vom `slimbookindicator` benutzt. Ohne `slimbook-service` ist es funktionslos.

→ **Streichen.**

### Modellfremde Meta-Pakete

`slimbook-meta-creative`, `-elemental`, `-evo`, `-excalibur`, `-hero`, `-hero-s`, `-nas`, `-one`, `-prox`, `-zero`. Nicht installieren — anderer Hardware-Kontext.

### Desktop-Environment-Pakete

`slimbook-meta-gnome` zieht `gnome-extensions-app` + `gnome-shell-extension-appindicator`. `slimbook-meta-plasma` ist leer (vermutlich Versionsfehler). Auf Sway irrelevant. **Streichen.**

### Optionale x86_64-Tools, nicht in `slimbook-meta-executive`

| Paket | Zweck | Für Executive? |
|---|---|---|
| `intel-undervolt-1.7` | Intel-CPU-Undervolting | Optional, kein Default; manueller Schritt |
| `ryzenadj` | AMD-CPU-Tuning | Nein — Executive ist Intel |
| `slimbook-rgb-keyboard`, `python3-ite8291r3-ctl`, `hid-ite8291r3-kmod*` | RGB-Keyboard (Gaming-Modelle, ITE8291R3-Controller) | Nein |
| `slimbook-keyboard-kmod*`, `akmod-slimbook-keyboard` | Slimbook-Keyboard-Treiber (anderes Chassis) | Nein |
| `slimbook-yt6801-kmod*`, `akmod-slimbook-yt6801` | Motorcomm-YT6801-Ethernet (Slimbook Pro X / NAS) | Vermutlich nein. In VM verifizieren |
| `slimbook-quirk-i8042-reset` | Sleep-Hook: rebindet `serio0/atkbd` nach Resume | Nicht in `slimbook-meta-executive` aufgeführt |
| `slimbook-quirk-i8042-wakeup` | Udev: deaktiviert atkbd-Wakeup | Nicht in `slimbook-meta-executive` aufgeführt |
| `slimbook-grub-fix-amd-iommu` | `iommu=pt`, AMD | Nein — Intel |
| `slimbook-grub-fix-ecwake` | `acpi.ec_no_wakeup=1` | Nicht in meta-executive; AMD-typisches Problem |
| `slimbook-grub-fix-gpiowake` | `gpiolib_acpi.ignore_wake=AMDI0030...` | AMD-only |
| `slimbook-grub-fix-psr` | `amdgpu.dcdebugmask=0x610` | AMD-only |

**Wichtige Beobachtung zu den `grub-fix`-Paketen:** Ihre postinstall-Scripts hängen Strings an `/etc/default/grub` und rufen `grub2-mkconfig` auf. Auf rpm-ostree wird die Kernel-Commandline aber über `rpm-ostree kargs` verwaltet — `grub2-mkconfig`-Aufrufe vom Layer-Scriptlet wirken **nicht**. Selbst wenn man diese Pakete für Executive bräuchte (tut man laut Slimbook nicht), wären sie auf Atomic der falsche Mechanismus.

## Was `rpm-ostree install slimbook-meta-common slimbook-meta-executive` als Layer hinzufügt

Direkte Slimbook-Pakete:

1. `slimbook-meta-common` (noarch, 0 B Inhalt)
2. `slimbook-meta-executive` (noarch, 0 B Inhalt)
3. `libslimbook1` (≈333 KB installiert)
4. `python3-slimbook` (≈30 KB)
5. `slimbook-service` (≈178 KB)
6. `slimbook-qc71-kmod-common` (noarch, 0 B Inhalt)
7. `akmod-slimbook-qc71` (≈42 KB) — oder gleichwertig `kmod-slimbook-qc71`

Plus indirekt aus dem Fedora-Repo, falls noch nicht im Basisimage:
- `akmods`, `kmodtool` (Build-bei-Boot-Infrastruktur)
- `gtk3`, `libappindicator-gtk3`, `libnotify`, `adwaita-icon-theme`
- `python3-dateutil`, `python3-evdev`, `python3-feedparser`, `python3-pyudev`, `python3-requests`, `python3-zmq`

Auf einem Sway-Atomic-Image sind die GTK3-/Indicator-Pakete typischerweise **nicht** im Basisimage. Das macht den Layer beim offiziellen Weg signifikant größer.

## Schlussfolgerung für das schlanke RPM

Ein Meta-RPM mit nur zwei Requires reicht für den Executive auf Sway:

```
Requires: libslimbook1
Requires: akmod-slimbook-qc71
```

Damit landen im Layer: das Meta-RPM selbst + `libslimbook1` + `akmod-slimbook-qc71` + `slimbook-qc71-kmod-common` + `akmods` + `kmodtool` (+ deren wenige deps wie `mokutil`). Kein GTK3, kein Python-Stack, kein Indicator.

Die Annahmen — kein GTK-Stack im Sway-Basisimage, keine Hardware-Anforderung für i8042-Quirks oder GRUB-Fixes — werden gegen eine echte Atomic-Sway-VM gegengeprüft (nächster Schritt).
