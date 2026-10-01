# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
#!BuildConstraint: hardware:physicalmemory:size unit=G 16
#!BuildConstraint: hardware:disk:size unit=G 20
# Data interchange features used by Qore's DataFrame module.
%global source_date_epoch_from_changelog 1
%global use_source_date_epoch_as_buildtime 1
%if v"%{rpmversion}" >= v"4.20"
%global build_mtime_policy clamp_to_source_date_epoch
%else
%global clamp_mtime_to_source_date_epoch 1
%endif
%global soname 2500
%global arrow_testing_commit 9ff285c88565f0f6abc855918c6a342e70e4909c
%global parquet_testing_commit e74785d85a4ecee829e1e405444d6a1b24b8bc9c
Name: apache-arrow
Version: 25.0.1
Release: 1.qore%{?dist}
Summary: Arrow columnar data interchange and Parquet libraries
License: Apache-2.0 AND BSD-2-Clause AND BSD-3-Clause AND MIT AND Zlib
URL: https://arrow.apache.org/
Source0: https://archive.apache.org/dist/arrow/arrow-%{version}/apache-arrow-%{version}.tar.gz
Source1: https://github.com/apache/arrow-testing/archive/%{arrow_testing_commit}.tar.gz#/arrow-testing-%{arrow_testing_commit}.tar.gz
Source2: https://github.com/apache/parquet-testing/archive/%{parquet_testing_commit}.tar.gz#/parquet-testing-%{parquet_testing_commit}.tar.gz
Source3: https://github.com/xtensor-stack/xsimd/archive/14.2.0.tar.gz#/xsimd-14.2.0.tar.gz
# Upstream GH-50542: compile SSE4.2 kernels separately from the baseline ISA.
Patch0: apache-arrow-runtime-sse42.patch
BuildRequires: cmake >= 3.25
BuildRequires: make
BuildRequires: tar
BuildRequires: gcc-c++
BuildRequires: python3
BuildRequires: timezone
BuildRequires: libboost_filesystem-devel
BuildRequires: libboost_process-devel
BuildRequires: libboost_system-devel
BuildRequires: libboost_date_time-devel
BuildRequires: libboost_context-devel
BuildRequires: pkgconfig(gflags)
BuildRequires: pkgconfig(gtest)
BuildRequires: pkgconfig(gmock)
BuildRequires: pkgconfig(RapidJSON)
BuildRequires: cmake(Snappy)
BuildRequires: pkgconfig(thrift)
BuildRequires: pkgconfig(openssl)
BuildRequires: pkgconfig(libbrotlienc)
BuildRequires: pkgconfig(libbrotlidec)
BuildRequires: pkgconfig(liblz4)
BuildRequires: pkgconfig(libzstd)
BuildRequires: pkgconfig(zlib)
BuildRequires: libbz2-devel

%description
Columnar arrays, IPC, CSV/JSON, local file systems and Parquet I/O. Common
compression algorithms and Parquet encryption are enabled. Sources and upstream
test fixtures are pinned for offline builds.

%package -n libarrow%{soname}
Summary: Arrow data interchange shared library
Provides: bundled(xsimd) = 14.2.0
%description -n libarrow%{soname}
Columnar arrays, IPC, CSV/JSON and local file system APIs with CPU dispatch.

%package -n libparquet%{soname}
Summary: Parquet columnar file format shared library
%description -n libparquet%{soname}
Parquet reading and writing with compression and encryption support.

%package devel
Summary: Arrow development headers and build metadata
Requires: libarrow%{soname}%{?_isa} = %{version}-%{release}
%description devel
Arrow C++ headers, compiler discovery and CMake metadata.

%package -n apache-parquet-devel
Summary: Parquet development headers and build metadata
Requires: libparquet%{soname}%{?_isa} = %{version}-%{release}
Requires: %{name}-devel%{?_isa} = %{version}-%{release}
%description -n apache-parquet-devel
Parquet C++ headers, compiler discovery and CMake metadata.

%if 0%{?suse_version}
%post -n libarrow%{soname} -p /sbin/ldconfig
%postun -n libarrow%{soname} -p /sbin/ldconfig
%post -n libparquet%{soname} -p /sbin/ldconfig
%postun -n libparquet%{soname} -p /sbin/ldconfig
%endif

%prep
%autosetup -p1
# autosetup's option forwarding retains only the final repeated -a argument.
# Extract every pinned auxiliary archive explicitly.
tar -xf %{SOURCE1}
tar -xf %{SOURCE2}
tar -xf %{SOURCE3}

%build
%{?set_build_flags}
# Only xsimd needs a version newer than Leap's base; use Arrow's own hash-
# checked local archive support. All other dependencies must come from the SDK.
export ARROW_XSIMD_URL=%{SOURCE3}
cmake -S cpp -B build -G 'Unix Makefiles' \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_FLAGS_RELEASE=-DNDEBUG -DCMAKE_CXX_FLAGS_RELEASE=-DNDEBUG \
  -DCMAKE_INSTALL_PREFIX=%{_prefix} -DCMAKE_INSTALL_LIBDIR=%{_lib} \
  -DCMAKE_INSTALL_DOCDIR=%{_docdir}/arrow \
  -DCMAKE_SKIP_INSTALL_RPATH=ON -DCMAKE_BUILD_RPATH_USE_ORIGIN=ON \
  -DARROW_DEPENDENCY_SOURCE=SYSTEM -Dxsimd_SOURCE=BUNDLED \
  -DARROW_BUILD_SHARED=ON -DARROW_BUILD_STATIC=OFF -DARROW_BUILD_TESTS=ON \
  -DARROW_BUILD_BENCHMARKS=OFF -DARROW_BUILD_EXAMPLES=OFF \
  -DARROW_BUILD_UTILITIES=OFF -DARROW_BUILD_INTEGRATION=OFF \
  -DARROW_COMPUTE=OFF -DARROW_DATASET=OFF -DARROW_CSV=ON -DARROW_JSON=ON \
  -DARROW_FILESYSTEM=ON -DARROW_IPC=ON -DARROW_PARQUET=ON \
  -DARROW_FLIGHT=OFF -DARROW_S3=OFF -DARROW_GCS=OFF -DARROW_AZURE=OFF \
  -DARROW_JEMALLOC=OFF -DARROW_MIMALLOC=OFF \
  -DARROW_WITH_BROTLI=ON -DARROW_WITH_BZ2=ON -DARROW_WITH_LZ4=ON \
  -DARROW_WITH_SNAPPY=ON -DARROW_WITH_ZLIB=ON -DARROW_WITH_ZSTD=ON \
  -DARROW_USE_OPENSSL=ON -DPARQUET_REQUIRE_ENCRYPTION=ON \
  -DARROW_SIMD_LEVEL=NONE -DARROW_RUNTIME_SIMD_LEVEL=MAX
cmake --build build -- %{?_smp_mflags}

%install
DESTDIR=%{buildroot} cmake --install build
# Upstream installs its private testing SDK alongside public headers. Keep
# these build-only artifacts out of the consumer development packages.
rm -f %{buildroot}%{_libdir}/libarrow_testing.so* \
  %{buildroot}%{_libdir}/pkgconfig/arrow-testing.pc
rm -rf %{buildroot}%{_libdir}/cmake/ArrowTesting \
  %{buildroot}%{_includedir}/arrow/testing

%check
export PYTHON=/usr/bin/python3
export ARROW_TEST_DATA=$PWD/arrow-testing-%{arrow_testing_commit}/data
export PARQUET_TEST_DATA=$PWD/parquet-testing-%{parquet_testing_commit}/data
test -d "$ARROW_TEST_DATA"
test -d "$PARQUET_TEST_DATA"
ctest --test-dir build --output-on-failure --parallel 2 --timeout 600

%files -n libarrow%{soname}
%license LICENSE.txt NOTICE.txt xsimd-14.2.0/LICENSE
%{_libdir}/libarrow.so.*
%files -n libparquet%{soname}
%license LICENSE.txt NOTICE.txt
%{_libdir}/libparquet.so.*
%files devel
%{_includedir}/arrow/
%{_libdir}/libarrow.so
%{_libdir}/pkgconfig/arrow.pc
%{_libdir}/pkgconfig/arrow-csv.pc
%{_libdir}/pkgconfig/arrow-filesystem.pc
%{_libdir}/pkgconfig/arrow-json.pc
%{_libdir}/cmake/Arrow/
%dir %{_datadir}/arrow
%{_datadir}/arrow/gdb/
%{_datadir}/gdb/auto-load%{_libdir}/libarrow.so.*-gdb.py
%doc %{_docdir}/arrow/
%files -n apache-parquet-devel
%{_includedir}/parquet/
%{_libdir}/libparquet.so
%{_libdir}/pkgconfig/parquet.pc
%{_libdir}/cmake/Parquet/

%changelog
* Thu Oct 01 2026 David Nichols <david@qore.org> - 25.0.1-1.qore
- Supply Leap data interchange libraries with pinned offline test fixtures.
