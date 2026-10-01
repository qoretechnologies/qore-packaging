# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
# Use the pinned source epoch for RPM headers and installed file timestamps.
%global source_date_epoch_from_changelog 1
%global use_source_date_epoch_as_buildtime 1
%if v"%{rpmversion}" >= v"4.20"
%global build_mtime_policy clamp_to_source_date_epoch
%else
%global clamp_mtime_to_source_date_epoch 1
%endif
%if 0%{?suse_version}
%global libname libtree-sitter0_26
%else
%global libname tree-sitter
%endif
Name: tree-sitter
Version: 0.26.13
Release: 1.qore%{?dist}
Summary: Incremental parsing runtime
License: MIT
URL: https://tree-sitter.github.io/tree-sitter/
Source0: https://github.com/tree-sitter/tree-sitter/archive/refs/tags/v%{version}.tar.gz#/tree-sitter-%{version}.tar.gz
Source1: tree-sitter-runtime.c
BuildRequires: gcc
BuildRequires: make
BuildRequires: pkgconfig

%if 0%{?suse_version}
%description
Incremental parser C runtime and development files.

%package -n %{libname}
Summary: Incremental parsing runtime
%endif
%description -n %{libname}
Tree-sitter builds concrete syntax trees and efficiently updates them as
source files are edited. This package contains the shared C runtime.

%package devel
Summary: Development files for the tree-sitter C runtime
Requires: %{libname}%{?_isa} = %{version}-%{release}
%description devel
Headers and compiler discovery metadata for the tree-sitter C runtime. The Rust
bindings and parser generator are not included in this runtime package.

%if 0%{?suse_version}
%post -n %{libname} -p /sbin/ldconfig
%postun -n %{libname} -p /sbin/ldconfig
%endif

%prep
%autosetup
%build
%{?set_build_flags}
%make_build PREFIX=%{_prefix} LIBDIR=%{_libdir}
%install
%make_install PREFIX=%{_prefix} LIBDIR=%{_libdir}
# The SONAME includes the minor ABI. Never advertise the obsolete ABI-0 link.
ln -sf libtree-sitter.so.0.26 %{buildroot}%{_libdir}/libtree-sitter.so
rm -f %{buildroot}%{_libdir}/libtree-sitter.so.0 %{buildroot}%{_libdir}/libtree-sitter.a
%check
# The upstream Rust/CLI suite downloads grammar fixtures. Check the C ABI
# offline here; Qore's astparser suite separately exercises actual parsing.
ln -sf libtree-sitter.so libtree-sitter.so.0.26
%{__cc} %{optflags} -Wall -Wextra -Werror -Ilib/include %{SOURCE1} \
    -L. -Wl,-rpath,'$ORIGIN' -l:libtree-sitter.so -o runtime-test
./runtime-test
%files -n %{libname}
%license LICENSE
%{_libdir}/libtree-sitter.so.0.26
%files devel
%{_includedir}/tree_sitter/
%{_libdir}/libtree-sitter.so
%{_libdir}/pkgconfig/tree-sitter.pc
%changelog
* Thu Oct 01 2026 David Nichols <david@qore.org> - 0.26.13-1.qore
- Backport the shared C runtime and verify the public C ABI offline.
