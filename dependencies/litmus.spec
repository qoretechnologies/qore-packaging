# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
%global source_date_epoch_from_changelog 1
%global use_source_date_epoch_as_buildtime 1
%if v"%{rpmversion}" >= v"4.20"
%global build_mtime_policy clamp_to_source_date_epoch
%else
%global clamp_mtime_to_source_date_epoch 1
%endif
Name: litmus
Version: 0.18
Release: 3.qore%{?dist}
Summary: WebDAV server compliance tests
License: GPL-2.0-or-later
URL: https://notroj.github.io/litmus/
Source0: https://notroj.github.io/litmus/litmus-%{version}.tar.gz
Source1: GPL-2.0-current.txt
Source2: litmus-httpd-test.py
Source3: litmus-httpd-fixture-test.py
BuildRequires: gcc
BuildRequires: make
BuildRequires: pkgconfig(neon) >= 0.29
BuildRequires: help2man
%if 0%{?suse_version}
BuildRequires: apache2 >= 2.4.55
%else
BuildRequires: httpd >= 2.4.55
%if 0%{?fedora}
# Resolve httpd's two equivalent logo providers in minimal OBS build roots.
BuildRequires: fedora-logos-httpd
%endif
%endif
BuildRequires: python3
%description
Checks WebDAV servers with tests for file operations, properties, locks,
authentication and HTTP behavior. Uses the distribution's shared neon library.

%prep
%autosetup
cp %{SOURCE1} COPYING.current
%build
# Litmus uses plain Autoconf without Automake dependency-tracking options.
%set_build_flags
export CFLAGS="$CFLAGS -fPIE"
export LDFLAGS="$LDFLAGS -pie -Wl,-z,relro,-z,now"
./configure --build=%{_build} --host=%{_host} --prefix=%{_prefix} \
    --bindir=%{_bindir} --libdir=%{_libdir} --libexecdir=%{_libexecdir} --mandir=%{_mandir} \
    --with-neon=%{_prefix}
%make_build
help2man --no-info --name='WebDAV server compliance tests' ./litmus > litmus.1
%install
%make_install
install -Dm644 litmus.1 %{buildroot}%{_mandir}/man1/litmus.1
%check
./litmus --version
./litmus --help
python3 -B -W error %{SOURCE3} -v
python3 -B -W error %{SOURCE2} "$PWD/litmus"
%files
%license COPYING.current
%doc README.md NEWS TODO
%{_bindir}/litmus
%{_libexecdir}/litmus/
%{_mandir}/man1/litmus.1*
%changelog
* Thu Oct 01 2026 David Nichols <david@qore.org> - 0.18-3.qore
- Resolve Apache from system directories under restricted build-user PATHs.
- Select Fedora's httpd logo provider explicitly for OBS dependency resolution.

* Thu Oct 01 2026 David Nichols <david@qore.org> - 0.18-2.qore
- Enable PIE and full RELRO on distributions whose default flags omit them.

* Thu Oct 01 2026 David Nichols <david@qore.org> - 0.18-1.qore
- Build WebDAV qualification tools with the system neon library.
- Run default suites against an isolated unprivileged Apache server.
