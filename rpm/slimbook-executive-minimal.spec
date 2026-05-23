# By default target the kernel running on the build host.
# Override with: rpmbuild --define "kver 7.0.9-205.fc44.x86_64" -ba …
%{!?kver: %global kver %(uname -r)}
%global modpath /usr/lib/modules/%{kver}/extra
%global qc71_version 1.0.1

Name:           slimbook-executive-minimal
Version:        2.0.0
Release:        1%{?dist}
Summary:        Slimbook Executive driver bundle for Fedora Atomic — no akmods, no GUI
License:        GPL-2.0-only
URL:            https://github.com/kp-greg-smith/slimbook-fedora-atomic
BuildArch:      x86_64

# Upstream QC71 platform driver source (Slimbook fork). Extracted from
# the Slimbook src.rpm at https://download.opensuse.org/repositories/home:/Slimbook/Fedora_44/src/
# Download into ~/rpmbuild/SOURCES/ before building. See README.
Source0:        qc71_laptop-%{qc71_version}.tar.gz
Source1:        README.md

# Build needs the matching kernel-devel for the target kernel.
BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  xz
BuildRequires:  kernel-devel-uname-r = %{kver}

# Runtime needs libslimbook1 (slimbookctl + systemd unit + udev rule) and
# the exact target kernel.
Requires:       libslimbook1
Requires:       kernel-core-uname-r = %{kver}

%description
Minimal driver bundle for the Slimbook Executive on Fedora Sway Atomic.
Builds the qc71_laptop platform driver from upstream source pinned to
kernel %{kver}, packages just the resulting qc71_laptop.ko.xz, and
declares libslimbook1 as the only userspace dependency.

No akmods, no kmodtool, no GUI tray, no Python bindings.

When you rpm-ostree upgrade past the pinned kernel, rebuild this RPM
against the new kernel and re-layer it.

%prep
tar -xzf %{SOURCE0}
mv qc71_laptop-%{qc71_version} qc71_src

%build
cd qc71_src
make -C /usr/src/kernels/%{kver} M=$PWD modules
# The kernel's in-tree xz decompressor only accepts CRC32 integrity checks.
# Default xz uses CRC64/SHA-256, which the kernel rejects with status 6
# ("decompression failed") and modprobe reports as -EINVAL.
xz --check=crc32 -f qc71_laptop.ko

%install
mkdir -p %{buildroot}%{modpath}
install -m 0644 qc71_src/qc71_laptop.ko.xz %{buildroot}%{modpath}/qc71_laptop.ko.xz

mkdir -p %{buildroot}%{_docdir}/%{name}
install -m 0644 %{SOURCE1} %{buildroot}%{_docdir}/%{name}/README.md

%post
/usr/sbin/depmod -a %{kver} >/dev/null 2>&1 || :

%postun
/usr/sbin/depmod -a %{kver} >/dev/null 2>&1 || :

%files
%{modpath}/qc71_laptop.ko.xz
%doc %{_docdir}/%{name}/README.md
%license qc71_src/LICENSE

%changelog
* Sat May 23 2026 Greg Smith <greg.smith@kape.com> - 2.0.0-1
- Build the qc71_laptop module from upstream source against the running
  kernel by default. Override with --define "kver <version>". Drops the
  hardcoded kernel version. Ships the .ko.xz only — no akmods, no
  kmodtool, no slimbook-service GUI stack.
