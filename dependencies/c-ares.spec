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
%global libname libcares2
%else
%global libname c-ares
%endif
Name: c-ares
Version: 1.34.8
%if 0%{?suse_version}
# Leap's same-version system package uses an SLE release prefix. Retain it
# so the patched package upgrades normally without --oldpackage or an epoch.
%if 0%{?sle_version}
Release: %{sle_version}.2.qore%{?dist}
%else
# Leap 16's container macros define suse_version but not sle_version.
Release: %{expr:0%{?suse_version} * 100}.2.qore%{?dist}
%endif
%else
Release: 2.qore%{?dist}
%endif
Summary: Asynchronous DNS resolver with Qore query life cycle fixes
License: MIT
URL: https://c-ares.org/
Source0: https://launchpad.net/ubuntu/+archive/primary/+sourcefiles/c-ares/%{version}-1/c-ares_%{version}.orig.tar.gz#/c-ares-%{version}.tar.gz
Source1: c-ares-rpmlintrc
Patch0: c-ares-lost-query.patch
Patch1: c-ares-test-language.patch
Patch2: c-ares-timeout-test.patch
BuildRequires: cmake
BuildRequires: gcc-c++
BuildRequires: make
BuildRequires: pkgconfig(gtest)
BuildRequires: pkgconfig(gmock)
BuildRequires: valgrind
%if 0%{?suse_version}
BuildRequires: fdupes
# getaddrinfo service-name tests need the distribution services database.
BuildRequires: netcfg
%description
Asynchronous DNS resolver with the query life cycle fixes required by Qore.

%package -n %{libname}
Summary: Asynchronous DNS resolver with Qore query life cycle fixes
%endif
Provides: c-ares(qore-query-lifecycle-fixes)%{?_isa} = 1
Provides: c-ares(qore-query-lifecycle-fixes) = 1

%description -n %{libname}
Asynchronous DNS resolver, including fixes for lost queries and query-ID reuse.

%package devel
Summary: Development files for c-ares
Requires: %{libname}%{?_isa} = %{version}-%{release}
%description devel
Headers, compiler discovery and CMake files for the asynchronous DNS resolver.

%if 0%{?suse_version}
%post -n %{libname} -p /sbin/ldconfig
%postun -n %{libname} -p /sbin/ldconfig
%endif

%prep
%autosetup -p1
%build
%{?set_build_flags}
cmake -S . -B build -G 'Unix Makefiles' -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_FLAGS_RELEASE=-DNDEBUG -DCMAKE_CXX_FLAGS_RELEASE=-DNDEBUG \
  -DCMAKE_INSTALL_PREFIX=%{_prefix} -DCMAKE_INSTALL_LIBDIR=%{_lib} \
  -DCARES_STATIC=OFF -DCARES_SHARED=ON -DCARES_BUILD_TESTS=ON \
  -DCARES_BUILD_TOOLS=OFF -DCARES_BUILD_CONTAINER_TESTS=OFF
cmake --build build -- %{?_smp_mflags}
%install
DESTDIR=%{buildroot} cmake --install build
%if 0%{?suse_version}
%fdupes %{buildroot}%{_mandir}
%endif
%check
# Public-DNS Live tests require Internet access and are a separate connected
# qualification gate. Mock servers, parsers and the fuzz corpus run offline.
GTEST_FILTER='-*Live*' ctest --test-dir build --output-on-failure --timeout 300
valgrind --error-exitcode=99 --leak-check=full --errors-for-leak-kinds=definite \
  build/bin/arestest --gtest_filter='*TimeoutValue*'
%files -n %{libname}
%license LICENSE.md
%{_libdir}/libcares.so.*
%files devel
%{_includedir}/ares*.h
%{_libdir}/libcares.so
%{_libdir}/pkgconfig/libcares.pc
%{_libdir}/cmake/c-ares/
%{_mandir}/man3/ares*.3*
%changelog
* Thu Oct 01 2026 David Nichols <david@qore.org> - 1.34.8-2.qore
- Carry both DNS query lifecycle fixes required by Qore.
