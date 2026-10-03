# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
#!BuildConstraint: hardware:physicalmemory:size unit=G 16
#!BuildConstraint: hardware:disk:size unit=G 20
# Data interchange features used by Qore DataFrame and gRPC/Flight fixtures.
%global source_date_epoch_from_changelog 1
%global use_source_date_epoch_as_buildtime 1
%if v"%{rpmversion}" >= v"4.20"
%global build_mtime_policy clamp_to_source_date_epoch
%else
%global clamp_mtime_to_source_date_epoch 1
%endif
%global soname 2500
Name: apache-arrow
Version: 25.0.1
Release: 2.qore%{?dist}
Summary: Arrow columnar data interchange and Parquet libraries
License: Apache-2.0 AND BSD-2-Clause AND BSD-3-Clause AND MIT AND Zlib
URL: https://arrow.apache.org/
Source0: https://archive.apache.org/dist/arrow/arrow-%{version}/apache-arrow-%{version}.tar.gz
Source1: https://github.com/apache/arrow-testing/archive/9ff285c88565f0f6abc855918c6a342e70e4909c.tar.gz#/arrow-testing-9ff285c88565f0f6abc855918c6a342e70e4909c.tar.gz
Source2: https://github.com/apache/parquet-testing/archive/e74785d85a4ecee829e1e405444d6a1b24b8bc9c.tar.gz#/parquet-testing-e74785d85a4ecee829e1e405444d6a1b24b8bc9c.tar.gz
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
BuildRequires: pkgconfig(re2)
BuildRequires: pkgconfig(libutf8proc)
BuildRequires: pkgconfig(grpc++)
BuildRequires: pkgconfig(protobuf)
BuildRequires: pkgconfig(openssl)
BuildRequires: pkgconfig(libbrotlienc)
BuildRequires: pkgconfig(libbrotlidec)
BuildRequires: pkgconfig(liblz4)
BuildRequires: pkgconfig(libzstd)
BuildRequires: pkgconfig(zlib)
BuildRequires: libbz2-devel

%description
Columnar arrays, compute kernels, streaming execution, datasets, IPC, CSV/JSON,
local file systems, Flight RPC and Parquet I/O. Common
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

%package -n libarrow-flight%{soname}
Summary: Arrow Flight RPC shared library
%description -n libarrow-flight%{soname}
Arrow Flight RPC client and server APIs using the system gRPC and Protobuf libraries.

%package -n libarrow-compute%{soname}
Summary: Arrow compute kernels shared library
%description -n libarrow-compute%{soname}
Apache Arrow compute kernels with system Arrow libraries.

%package -n apache-arrow-compute-devel
Summary: Arrow compute kernels development files
Requires: libarrow-compute%{soname}%{?_isa} = %{version}-%{release}
Requires: %{name}-devel%{?_isa} = %{version}-%{release}
%description -n apache-arrow-compute-devel
C++ headers, shared library linker name and CMake/pkg-config metadata for
Arrow compute kernels.

%package -n libarrow-acero%{soname}
Summary: Arrow streaming query execution shared library
%description -n libarrow-acero%{soname}
Apache Arrow streaming query execution with system Arrow libraries.

%package -n apache-arrow-acero-devel
Summary: Arrow streaming query execution development files
Requires: libarrow-acero%{soname}%{?_isa} = %{version}-%{release}
Requires: apache-arrow-compute-devel%{?_isa} = %{version}-%{release}
Requires: %{name}-devel%{?_isa} = %{version}-%{release}
%description -n apache-arrow-acero-devel
C++ headers, shared library linker name and CMake/pkg-config metadata for
Arrow streaming query execution.

%package -n libarrow-dataset%{soname}
Summary: Arrow dataset scanning shared library
%description -n libarrow-dataset%{soname}
Apache Arrow dataset scanning with system Arrow libraries.

%package -n apache-arrow-dataset-devel
Summary: Arrow dataset scanning development files
Requires: libarrow-dataset%{soname}%{?_isa} = %{version}-%{release}
Requires: apache-arrow-acero-devel%{?_isa} = %{version}-%{release}
Requires: apache-parquet-devel%{?_isa} = %{version}-%{release}
Requires: %{name}-devel%{?_isa} = %{version}-%{release}
%description -n apache-arrow-dataset-devel
C++ headers, shared library linker name and CMake/pkg-config metadata for
Arrow dataset scanning.

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

%package -n apache-arrow-flight-devel
Summary: Arrow Flight development headers and build metadata
Requires: libarrow-flight%{soname}%{?_isa} = %{version}-%{release}
Requires: %{name}-devel%{?_isa} = %{version}-%{release}
%description -n apache-arrow-flight-devel
Arrow Flight C++ headers, compiler discovery and CMake metadata.

%if 0%{?suse_version}
%post -n libarrow-compute%{soname} -p /sbin/ldconfig
%postun -n libarrow-compute%{soname} -p /sbin/ldconfig
%post -n libarrow-acero%{soname} -p /sbin/ldconfig
%postun -n libarrow-acero%{soname} -p /sbin/ldconfig
%post -n libarrow-dataset%{soname} -p /sbin/ldconfig
%postun -n libarrow-dataset%{soname} -p /sbin/ldconfig
%post -n libarrow-flight%{soname} -p /sbin/ldconfig
%postun -n libarrow-flight%{soname} -p /sbin/ldconfig
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
  -DARROW_COMPUTE=ON -DARROW_ACERO=ON -DARROW_DATASET=ON \
  -DARROW_CSV=ON -DARROW_JSON=ON \
  -DARROW_FILESYSTEM=ON -DARROW_IPC=ON -DARROW_PARQUET=ON \
  -DARROW_FLIGHT=ON -DARROW_S3=OFF -DARROW_GCS=OFF -DARROW_AZURE=OFF \
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
  %{buildroot}%{_libdir}/pkgconfig/arrow-testing.pc \
  %{buildroot}%{_libdir}/libarrow_flight_testing.so* \
  %{buildroot}%{_libdir}/pkgconfig/arrow-flight-testing.pc \
  %{buildroot}%{_includedir}/arrow/flight/test_*.h \
  %{buildroot}%{_includedir}/arrow/acero/test_util.h
rm -rf %{buildroot}%{_libdir}/cmake/ArrowTesting \
  %{buildroot}%{_includedir}/arrow/testing \
  %{buildroot}%{_libdir}/cmake/ArrowFlightTesting

%check
export PYTHON=/usr/bin/python3
export ARROW_TEST_DATA=$PWD/arrow-testing-9ff285c88565f0f6abc855918c6a342e70e4909c/data
export PARQUET_TEST_DATA=$PWD/parquet-testing-e74785d85a4ecee829e1e405444d6a1b24b8bc9c/data
test -d "$ARROW_TEST_DATA"
test -d "$PARQUET_TEST_DATA"
ctest --test-dir build --output-on-failure --parallel 2 --timeout 600

%files -n libarrow-compute%{soname}
%license LICENSE.txt NOTICE.txt
%{_libdir}/libarrow_compute.so.*
%files -n apache-arrow-compute-devel
%{_libdir}/libarrow_compute.so
%{_libdir}/pkgconfig/arrow-compute.pc
%{_libdir}/cmake/ArrowCompute/
%files -n libarrow-acero%{soname}
%license LICENSE.txt NOTICE.txt
%{_libdir}/libarrow_acero.so.*
%files -n apache-arrow-acero-devel
%{_libdir}/libarrow_acero.so
%{_libdir}/pkgconfig/arrow-acero.pc
%{_libdir}/cmake/ArrowAcero/
%files -n libarrow-dataset%{soname}
%license LICENSE.txt NOTICE.txt
%{_libdir}/libarrow_dataset.so.*
%files -n apache-arrow-dataset-devel
%{_libdir}/libarrow_dataset.so
%{_libdir}/pkgconfig/arrow-dataset.pc
%{_libdir}/cmake/ArrowDataset/
%files -n libarrow%{soname}
%license LICENSE.txt NOTICE.txt xsimd-14.2.0/LICENSE
%{_libdir}/libarrow.so.*
%files -n libparquet%{soname}
%license LICENSE.txt NOTICE.txt
%{_libdir}/libparquet.so.*
%files -n libarrow-flight%{soname}
%license LICENSE.txt NOTICE.txt
%{_libdir}/libarrow_flight.so.*
%files -n apache-arrow-flight-devel
%{_includedir}/arrow/flight/
%{_libdir}/libarrow_flight.so
%{_libdir}/pkgconfig/arrow-flight.pc
%{_libdir}/cmake/ArrowFlight/
%files devel
%{_includedir}/arrow/
%exclude %{_includedir}/arrow/flight/
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
* Fri Oct 02 2026 David Nichols <david@qore.org> - 25.0.1-2.qore
- Add system-linked Flight, Compute, Acero and Dataset libraries for PyArrow.
- Enable their upstream suites with pinned offline data.

* Thu Oct 01 2026 David Nichols <david@qore.org> - 25.0.1-1.qore
- Supply Leap data interchange libraries with pinned offline test fixtures.
