# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
# Leap's base repository does not provide the MongoDB C SDK.
%global source_date_epoch_from_changelog 1
%global use_source_date_epoch_as_buildtime 1
%if v"%{rpmversion}" >= v"4.20"
%global build_mtime_policy clamp_to_source_date_epoch
%else
%global clamp_mtime_to_source_date_epoch 1
%endif
Name: mongo-c-driver
Version: 2.5.5
Release: 2.qore%{?dist}
Summary: MongoDB C driver and BSON libraries
License: Apache-2.0 AND ISC AND MIT AND Zlib
URL: https://github.com/mongodb/mongo-c-driver
Source0: https://github.com/mongodb/mongo-c-driver/archive/%{version}.tar.gz#/%{name}-%{version}.tar.gz
Patch0: mongo-c-driver-tests.patch
Patch1: mongo-c-driver-bson-alias.patch
Source1: mongo-c-driver-proc-ctl-test.py
%if 0%{?suse_version}
# Runtime platform identification and its tests read the distribution release file.
BuildRequires: distribution-release
%endif
BuildRequires: cmake >= 3.25
BuildRequires: make
BuildRequires: gcc-c++
BuildRequires: python3
BuildRequires: openssl
BuildRequires: pkgconfig(openssl)
BuildRequires: pkgconfig(libsasl2)
BuildRequires: pkgconfig(libzstd)
BuildRequires: pkgconfig(snappy)
BuildRequires: pkgconfig(zlib)

%description
MongoDB C client libraries with TLS, SASL and compression support.
Live-server integration tests are separate from the offline RPM build.

%package -n libmongoc2
Summary: MongoDB C client shared library
Provides: bundled(libutf8proc) = 2.11.3
Provides: bundled(uthash) = 2.3.0
%description -n libmongoc2
MongoDB C client API with TLS, SASL and compression support.

%package -n libbson2
Summary: BSON serialization shared library
Provides: bundled(jsonsl)
%description -n libbson2
BSON document creation, validation, iteration and serialization APIs.

%package devel
Summary: MongoDB C driver development files
Requires: libmongoc2%{?_isa} = %{version}-%{release}
Requires: bson-devel%{?_isa} = %{version}-%{release}
%description devel
Headers, compiler flags and CMake metadata for the MongoDB C driver.

%package -n bson-devel
Summary: BSON development files
Requires: libbson2%{?_isa} = %{version}-%{release}
%description -n bson-devel
Headers, compiler flags and CMake metadata for BSON applications.

%if 0%{?suse_version}
%post -n libbson2 -p /sbin/ldconfig
%postun -n libbson2 -p /sbin/ldconfig
%post -n libmongoc2 -p /sbin/ldconfig
%postun -n libmongoc2 -p /sbin/ldconfig
%endif

%prep
%autosetup -p1

%build
%{?set_build_flags}
cmake -S . -B build -G 'Unix Makefiles' \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
  -DCMAKE_EXE_LINKER_FLAGS:STRING="${LDFLAGS:-} -pie" \
  -DCMAKE_C_FLAGS_RELEASE=-DNDEBUG -DCMAKE_CXX_FLAGS_RELEASE=-DNDEBUG \
  -DCMAKE_INSTALL_PREFIX=%{_prefix} -DCMAKE_INSTALL_LIBDIR=%{_lib} \
  -DCMAKE_SKIP_INSTALL_RPATH=ON -DCMAKE_BUILD_RPATH_USE_ORIGIN=ON \
  -DBUILD_VERSION=%{version} -DENABLE_MONGOC=ON -DENABLE_BSON=ON \
  -DENABLE_STATIC=BUILD_ONLY -DENABLE_STATIC_LIBBSON_INSTALL=OFF -DENABLE_TESTS=ON \
  -DENABLE_SSL=OPENSSL -DENABLE_SASL=CYRUS -DENABLE_ZLIB=SYSTEM \
  -DENABLE_SNAPPY=ON -DENABLE_ZSTD=ON -DENABLE_CLIENT_SIDE_ENCRYPTION=OFF
cmake --build build -- %{?_smp_mflags}
cmake --build build --target mongo_c_driver_tests -- %{?_smp_mflags}

%install
DESTDIR=%{buildroot} cmake --install build
# Keep the standard RPM license/doc copies, not upstream's uninstall helper.
rm -f %{buildroot}%{_datadir}/mongo-c-driver/%{version}/uninstall.sh \
  %{buildroot}%{_datadir}/mongo-c-driver/%{version}/COPYING \
  %{buildroot}%{_datadir}/mongo-c-driver/%{version}/NEWS \
  %{buildroot}%{_datadir}/mongo-c-driver/%{version}/README.rst \
  %{buildroot}%{_datadir}/mongo-c-driver/%{version}/THIRD_PARTY_NOTICES

%check
python3 -B -W error %{SOURCE1} "$PWD/build/proc-ctl.py"
# Upstream's flag retains local unit/mock tests and excludes external MongoDB
# servers, cloud credentials and network-dependent topology integration.
MONGOC_TEST_SKIP_LIVE=on ctest --test-dir build --output-on-failure --parallel 2 --timeout 300

%files -n libmongoc2
%license COPYING THIRD_PARTY_NOTICES
%{_libdir}/libmongoc2.so.*
%files -n libbson2
%license COPYING THIRD_PARTY_NOTICES
%{_libdir}/libbson2.so.*
%files devel
%doc NEWS README.rst
%{_bindir}/mongoc2-stat
%{_includedir}/mongoc-%{version}/
%{_libdir}/libmongoc2.so
%{_libdir}/pkgconfig/mongoc2.pc
%{_libdir}/cmake/mongoc-%{version}/
%files -n bson-devel
%{_includedir}/bson-%{version}/
%{_libdir}/libbson2.so
%{_libdir}/pkgconfig/bson2.pc
%{_libdir}/cmake/bson-%{version}/

%changelog
* Thu Oct 01 2026 David Nichols <david@qore.org> - 2.5.5-2.qore
- Correct BSON storage aliasing and qualify staged SDK imports with GCC 13 LTO.

* Thu Oct 01 2026 David Nichols <david@qore.org> - 2.5.5-1.qore
- Supply the Leap SDK with offline upstream unit and mock tests.
