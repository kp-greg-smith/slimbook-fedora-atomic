%global kver 7.0.9-205.fc44.x86_64
%global kshort 7.0.9-205.fc44
%global modpath /usr/lib/modules/%{kver}/extra

Name:           slimbook-executive-minimal
Version:        2.0.0
Release:        1%{?dist}
Summary:        Slimbook Executive driver bundle for Fedora Atomic — pre-built, no build toolchain
License:        MIT
URL:            https://github.com/kape-greg/slimbook-fedora-atomic
BuildArch:      x86_64

Source0:        qc71_laptop.ko.xz
Source1:        README.md

Requires:       libslimbook1
Requires:       kernel-core-uname-r = %{kver}

%description
Minimal driver bundle for the Slimbook Executive on Fedora Atomic 44.
Ships a pre-built qc71_laptop.ko.xz pinned to kernel %{kver} plus a
hard Requires on libslimbook1 (slimbookctl + systemd unit + udev
rule). Does NOT pull in akmods, kmodtool, gcc, kernel-devel,
kernel-headers, perl, python, or any SRPM macros.

Manual step on kernel upgrade: after rpm-ostree upgrade to a new
kernel version, install the matching slimbook-executive-minimal RPM
from this repo (or rebuild). Until then the qc71_laptop module won't
load on the new kernel.

%prep
# nothing — we only ship a binary blob

%build
# nothing

%install
mkdir -p %{buildroot}%{modpath}
install -m 0644 %{SOURCE0} %{buildroot}%{modpath}/qc71_laptop.ko.xz
mkdir -p %{buildroot}%{_docdir}/%{name}
install -m 0644 %{SOURCE1} %{buildroot}%{_docdir}/%{name}/README.md

%post
/usr/sbin/depmod -a %{kver} >/dev/null 2>&1 || :

%postun
/usr/sbin/depmod -a %{kver} >/dev/null 2>&1 || :

%files
%{modpath}/qc71_laptop.ko.xz
%doc %{_docdir}/%{name}/README.md

%changelog
* Sat May 23 2026 Greg Smith <greg.smith@kape.com> - 2.0.0-1
- Ship pre-built qc71_laptop.ko.xz instead of akmod source. Drops the
  entire build-toolchain layer (gcc, kernel-devel, perl-*, python3-*,
  rust-/qt-/zig-srpm-macros, rpm-build, akmods, kmodtool) — ~130
  fewer packages on the rpm-ostree layer. Pinned to kernel %{kver};
  user updates the RPM on kernel upgrade.
