# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
%global source_date_epoch_from_changelog 1
%global use_source_date_epoch_as_buildtime 1
%global build_mtime_policy clamp_to_source_date_epoch
Name: add-determinism
Version: 0.7.3
Release: 3.qore%{?dist}
Summary: Normalize files for reproducible RPM builds
License: GPL-3.0-or-later AND MIT AND Apache-2.0 AND BSD-3-Clause AND ISC AND Unicode-3.0 AND CC0-1.0
URL: https://github.com/keszybz/add-determinism
Source0: https://github.com/keszybz/add-determinism/archive/v%{version}/%{name}-%{version}.tar.gz
Source1: %{name}-%{version}-vendor.tar.xz
Source2: add-determinism-Cargo.lock
Source3: add-determinism-regression.py
Source4: add-determinism-vendor-licenses.json
Source5: add-determinism.1
Source6: linkdupes.1
Patch0: add-determinism-files.patch
BuildRequires: cargo
BuildRequires: rust
BuildRequires: gcc
BuildRequires: clang-devel
BuildRequires: pkgconfig(libselinux)
BuildRequires: pkgconfig(zlib)
BuildRequires: python3
BuildRequires: util-linux-core
Provides: add-determinism(qore-tempfile-fix) = 1

%description
Normalize archive, byte code and documentation metadata for reproducible RPMs.
Includes fixes for temporary-file discovery during concurrent processing.
All normal handlers and file normalization checks remain enabled.

%package -n linkdupes
Summary: Link identical files while respecting SELinux contexts
Provides: linkdupes(qore-bounded-descriptors) = 1
%description -n linkdupes
Link identical files while checking their metadata and SELinux contexts.
Uses bounded file descriptors while comparing large documentation trees.

%package -n build-reproducibility-srpm-macros
Summary: RPM macros for deterministic file processing
BuildArch: noarch
Requires: add-determinism = %{version}-%{release}
Requires: linkdupes = %{version}-%{release}
%description -n build-reproducibility-srpm-macros
Standard RPM macros invoking matching file normalization and hard link tools.

%prep
%autosetup -p1
tar -xf %{SOURCE1}
cp %{SOURCE2} Cargo.lock
mkdir -p .cargo
cat > .cargo/config.toml <<'EOF'
[source.crates-io]
replace-with = "vendored-sources"
[source.vendored-sources]
directory = "vendor"
EOF
# Retain every vendored license and the exact crate metadata and checksums.
python3 - <<'PY_LICENSES'
from pathlib import Path
import shutil
root = Path("vendor-licenses")
for crate in sorted(Path("vendor").iterdir()):
    dest = root / crate.name
    dest.mkdir(parents=True)
    for p in sorted(crate.rglob("*")):
        if p.is_file() and (p.name.lower().startswith(("license", "licence", "copying", "notice", "copyright"))
                            or p.name in ("Cargo.toml", ".cargo-checksum.json")):
            target = dest / p.relative_to(crate)
            if target.name == ".cargo-checksum.json":
                target = target.with_name("Cargo-checksum.json")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, target)
PY_LICENSES
cp %{SOURCE4} vendor-licenses/manifest.json

%build
export CARGO_HOME="$PWD/.cargo"
export CARGO_PROFILE_RELEASE_DEBUG=2
export CARGO_PROFILE_RELEASE_STRIP=none
cargo build --frozen --offline --release --features selinux -j%{_smp_build_ncpus}

%install
install -Dpm755 target/release/add-det %{buildroot}%{_bindir}/add-det
ln -s add-det %{buildroot}%{_bindir}/add-determinism
install -Dpm755 target/release/linkdupes %{buildroot}%{_bindir}/linkdupes
install -Dpm644 rpm/macros.build-reproducibility %{buildroot}%{_rpmconfigdir}/macros.d/macros.build-reproducibility
install -Dpm644 %{SOURCE5} %{buildroot}%{_mandir}/man1/add-det.1
ln -s add-det.1 %{buildroot}%{_mandir}/man1/add-determinism.1
install -Dpm644 %{SOURCE6} %{buildroot}%{_mandir}/man1/linkdupes.1
for package in add-determinism linkdupes; do
    install -d %{buildroot}%{_licensedir}/$package
    cp -a LICENSE.GPL3 vendor-licenses %{buildroot}%{_licensedir}/$package/
    hardlink -t -O %{buildroot}%{_licensedir}/$package
done

%check
export CARGO_HOME="$PWD/.cargo"
export CARGO_PROFILE_RELEASE_DEBUG=2
export CARGO_PROFILE_RELEASE_STRIP=none
cargo test --frozen --offline --release --features selinux -j%{_smp_build_ncpus}
python3 -B -W error %{SOURCE3} target/release

%files
%license %{_licensedir}/add-determinism/
%doc README.md
%{_mandir}/man1/add-det.1*
%{_mandir}/man1/add-determinism.1*
%{_bindir}/add-det
%{_bindir}/add-determinism
%files -n linkdupes
%license %{_licensedir}/linkdupes/
%doc README.md
%{_mandir}/man1/linkdupes.1*
%{_bindir}/linkdupes
%files -n build-reproducibility-srpm-macros
%doc README.md
%license LICENSE.GPL3
%{_rpmconfigdir}/macros.d/macros.build-reproducibility
%changelog
* Thu Oct 01 2026 David Nichols <david@qore.org> - 0.7.3-3.qore
- Exclude live temporary files from parallel normalization walks.
- Bound descriptor usage during incremental file comparison.
- Preserve SELinux checks and run upstream and low-descriptor regression tests.
