#
# spec file for package debugedit
#
# Copyright (c) 2026 SUSE LLC
# Copyright (c) 2026 Qore Technologies, s.r.o. (Leap qualification changes)
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via https://bugs.opensuse.org/
#


%global source_date_epoch_from_changelog 1
%global use_source_date_epoch_as_buildtime 1
%global build_mtime_policy clamp_to_source_date_epoch
Name:           debugedit
Version:        5.1
Release:        1.qore%{?dist}
Summary:        Debug information extraction
License:        GPL-3.0-or-later
Group:          System/Packages
#Git-Clone:     https://sourceware.org/git/debugedit.git
URL:            https://www.sourceware.org/debugedit
Source0:        https://sourceware.org/ftp/%{name}/%{version}/%{name}-%{version}.tar.xz
Source1:        https://sourceware.org/ftp/%{name}/%{version}/%{name}-%{version}.tar.xz.sig
Source2:        %{name}.keyring
Patch0:         debugedit-finddebuginfo.patch
Patch1:         debugedit-finddebuginfo-absolute-links.patch
Patch2:         debugedit-debugsubpkg.patch
Patch3:         debugedit-debuglink.patch
Patch4:         debugedit-debuginfo-mono.patch
Patch5:         debugedit-workaround-missing-linked-file.patch
BuildRequires:  autoconf
BuildRequires:  automake
BuildRequires:  help2man
BuildRequires:  pkgconfig(libdw)
BuildRequires:  pkgconfig(libelf)
BuildRequires:  pkgconfig(libxxhash)
# /usr/bin/gdb-add-index is optional
Suggests:       gdb
Requires:       binutils
Requires:       coreutils
Requires:       dwz
Requires:       elfutils
Requires:       findutils
Requires:       gawk
Requires:       grep
Requires:       sed
Requires:       xz

%description
debugedit provides programs and scripts for creating debug information and
source file distributions. It collects build IDs and rewrites source paths
in DWARF data for debugging, tracing and profiling.

%prep
%autosetup -p1

%build
autoreconf -fiv
export CFLAGS="%{optflags} -fPIE"
export LDFLAGS="%{?build_ldflags} -pie"
%configure
%make_build

%check
make check

%install
%make_install
mkdir -p %{buildroot}/usr/lib/rpm
mv %{buildroot}%{_bindir}/{find-debuginfo,sepdebugcrcfix} %{buildroot}/usr/lib/rpm
ln -s ../../bin/debugedit %{buildroot}/usr/lib/rpm

%files
%license COPYING3
%doc README
%{_bindir}/debugedit
/usr/lib/rpm/debugedit
/usr/lib/rpm/find-debuginfo
/usr/lib/rpm/sepdebugcrcfix
%{_mandir}/man1/debugedit.1%{?ext_man}
%{_mandir}/man1/find-debuginfo.1%{?ext_man}
%{_mandir}/man1/sepdebugcrcfix.1%{?ext_man}

%changelog
* Sat Oct 03 2026 David Nichols <david@qore.org> - 5.1-1.qore
- Backport the distribution recipe with indexed DWARF5 support for Clang runtime objects.
- Run the upstream test suite before packaging and enable PIE hardening.
