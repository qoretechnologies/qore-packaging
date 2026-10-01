# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
#!BuildConstraint: hardware:physicalmemory:size unit=G 24
#!BuildConstraint: hardware:disk:size unit=G 40
# CPU backport uses upstream's pinned sources and local-mirror support.
# Use the pinned source epoch for RPM headers and installed file timestamps.
%global source_date_epoch_from_changelog 1
%global use_source_date_epoch_as_buildtime 1
%if v"%{rpmversion}" >= v"4.20"
%global build_mtime_policy clamp_to_source_date_epoch
%else
%global clamp_mtime_to_source_date_epoch 1
%endif
%if 0%{?suse_version}
%global libname libonnxruntime1
%else
%global libname onnxruntime
%endif
Name: onnxruntime
Version: 1.22.2
Release: 1.qore%{?dist}
Summary: ONNX model inference runtime with the CPU execution provider
License: MIT AND Apache-2.0 AND BSL-1.0 AND BSD-2-Clause AND BSD-3-Clause AND MPL-2.0
URL: https://onnxruntime.ai/
Source0: https://github.com/microsoft/onnxruntime/archive/v%{version}/onnxruntime-%{version}.tar.gz
Source1: onnxruntime-components.json
Source2: onnxruntime-mirror.py
Patch0: onnxruntime-test-conversion.patch
Patch1: onnxruntime-softsign.patch
Patch2: onnxruntime-gcc15.patch
Patch3: onnxruntime-build-rpath.patch
Source3: https://github.com/abseil/abseil-cpp/archive/refs/tags/20240722.0.zip#/onnxruntime-1.22.2-abseil_cpp.zip
Source4: https://github.com/jarro2783/cxxopts/archive/3c73d91c0b04e2b59462f0a741be8c07024c1bc0.zip#/onnxruntime-1.22.2-cxxopts.zip
Source5: https://github.com/HowardHinnant/date/archive/refs/tags/v3.0.1.zip#/onnxruntime-1.22.2-date.zip
Source6: https://github.com/dmlc/dlpack/archive/5c210da409e7f1e51ddf445134a4376fdbd70d7d.zip#/onnxruntime-1.22.2-dlpack.zip
Source7: https://github.com/eigen-mirror/eigen/archive/1d8b82b0740839c0de7f1242a3585e3390ff5f33/eigen-1d8b82b0740839c0de7f1242a3585e3390ff5f33.zip#/onnxruntime-1.22.2-eigen.zip
Source8: https://github.com/google/flatbuffers/archive/refs/tags/v23.5.26.zip#/onnxruntime-1.22.2-flatbuffers.zip
Source9: https://github.com/Maratyszcza/FP16/archive/0a92994d729ff76a58f692d3028ca1b64b145d91.zip#/onnxruntime-1.22.2-fp16.zip
Source10: https://github.com/google/googletest/archive/refs/tags/v1.15.0.zip#/onnxruntime-1.22.2-googletest.zip
Source11: https://github.com/nlohmann/json/archive/refs/tags/v3.11.3.zip#/onnxruntime-1.22.2-json.zip
Source12: https://github.com/microsoft/GSL/archive/refs/tags/v4.0.0.zip#/onnxruntime-1.22.2-microsoft_gsl.zip
Source13: https://github.com/boostorg/mp11/archive/refs/tags/boost-1.82.0.zip#/onnxruntime-1.22.2-mp11.zip
Source14: https://github.com/onnx/onnx/archive/refs/tags/v1.17.0.zip#/onnxruntime-1.22.2-onnx.zip
Source15: https://github.com/protocolbuffers/protobuf/archive/refs/tags/v21.12.zip#/onnxruntime-1.22.2-protobuf.zip
Source16: https://github.com/Maratyszcza/psimd/archive/072586a71b55b7f8c584153d223e95687148a900.zip#/onnxruntime-1.22.2-psimd.zip
Source17: https://github.com/pytorch/cpuinfo/archive/8a1772a0c5c447df2d18edf33ec4603a8c9c04a6.zip#/onnxruntime-1.22.2-pytorch_cpuinfo.zip
Source18: https://github.com/google/re2/archive/refs/tags/2024-07-02.zip#/onnxruntime-1.22.2-re2.zip
Source19: https://github.com/dcleblanc/SafeInt/archive/refs/tags/3.0.28.zip#/onnxruntime-1.22.2-safeint.zip
BuildRequires: cmake >= 3.28
BuildRequires: gcc-c++
BuildRequires: make
BuildRequires: python3
BuildRequires: patch
%if 0%{?suse_version}
BuildRequires: util-linux
%else
BuildRequires: util-linux-core
%endif
BuildRequires: pkgconfig(zlib)
%if 0%{?suse_version}
BuildRequires: glibc-locale
%else
BuildRequires: glibc-langpack-en
BuildRequires: glibc-langpack-de
BuildRequires: glibc-langpack-fr
%endif
%if 0%{?suse_version}
%description
ONNX Runtime provides C and C++ inference APIs for ONNX models.

%package -n %{libname}
Summary: ONNX inference shared library
%endif
# Internal dependency versions are pinned in Source1 and retained in the SRPM.
Provides: bundled(abseil-cpp) = 20240722.0
Provides: bundled(date) = 3.0.1
Provides: bundled(eigen) = 3.4.90^git1d8b82b
Provides: bundled(flatbuffers) = 23.5.26
Provides: bundled(mp11) = 1.82.0
Provides: bundled(nlohmann-json) = 3.11.3
Provides: bundled(onnx) = 1.17.0
Provides: bundled(protobuf) = 21.12
Provides: bundled(re2) = 20240702
Provides: bundled(SafeInt) = 3.0.28
Provides: bundled(Microsoft.GSL) = 4.0.0
Provides: bundled(cpuinfo) = 0^git8a1772a
Provides: bundled(fp16) = 0^git0a92994
Provides: bundled(psimd) = 0^git072586a

%description -n %{libname}
CPU inference for ONNX models, including standard, machine-learning and
contributed operators. This package builds its version-matched internal
sources offline and preserves C and C++ APIs for Qore's ML module.

%package devel
Summary: Headers and build metadata for ONNX Runtime
Requires: %{libname}%{?_isa} = %{version}-%{release}
%description devel
C and C++ headers, compiler discovery and CMake metadata for ONNX Runtime.

%package tools
Summary: ONNX model conformance runner
Requires: %{libname}%{?_isa} = %{version}-%{release}
Provides: bundled(cxxopts) = 0^git3c73d91
%description tools
The upstream model test runner for checking ONNX model input/output fixtures.

%if 0%{?suse_version}
%post -n %{libname} -p /sbin/ldconfig
%postun -n %{libname} -p /sbin/ldconfig
%endif

%prep
%autosetup -p1
# Upstream marks this C++ source executable; debugsource preserves that mode.
chmod 644 onnxruntime/core/optimizer/bias_softmax_fusion.cc
python3 %{SOURCE2} . %{SOURCE1} %{_sourcedir}

%build
%{?set_build_flags}
# NEVER prevents opportunistic selection of incompatible system development
# packages; source inputs come only from the checked local mirror.
# MLAS assembly has no GNU-stack notes. Explicitly mark assembler objects as
# data-stack-only instead of inheriting the linker's executable-stack default.
cmake -S cmake -B build -G 'Unix Makefiles' \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_C_FLAGS_RELEASE=-DNDEBUG -DCMAKE_CXX_FLAGS_RELEASE=-DNDEBUG \
    -DCMAKE_INSTALL_PREFIX=%{_prefix} -DCMAKE_INSTALL_LIBDIR=%{_lib} \
    -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
    -DCMAKE_ASM_FLAGS=-Wa,--noexecstack \
    -DCMAKE_EXE_LINKER_FLAGS="${LDFLAGS:-} -pie" \
    -DCMAKE_SKIP_INSTALL_RPATH=ON -DCMAKE_BUILD_RPATH_USE_ORIGIN=ON \
    -DFETCHCONTENT_TRY_FIND_PACKAGE_MODE=NEVER \
    -DFETCHCONTENT_UPDATES_DISCONNECTED=ON \
    -Donnxruntime_BUILD_SHARED_LIB=ON -Donnxruntime_BUILD_UNIT_TESTS=ON \
    -Donnxruntime_ENABLE_PYTHON=OFF -Donnxruntime_BUILD_BENCHMARKS=OFF \
    -Donnxruntime_ENABLE_TRAINING=OFF -Donnxruntime_USE_CUDA=OFF \
    -Donnxruntime_USE_TENSORRT=OFF -Donnxruntime_USE_ROCM=OFF \
    -Donnxruntime_BUILD_FOR_NATIVE_MACHINE=OFF
cmake --build build -- %{?_smp_mflags}
mkdir third-party-licenses
for component in build/_deps/*-src; do
    test -d "$component" || continue
    name="${component##*/}"
    mkdir "third-party-licenses/$name"
    for license in "$component"/LICENSE* "$component"/COPYING* "$component"/Copyright*; do
        test -f "$license" || continue
        cp -p "$license" "third-party-licenses/$name/"
    done
done
hardlink -t -O third-party-licenses

%install
DESTDIR=%{buildroot} cmake --install build

%check
ctest --test-dir build --output-on-failure --parallel 2 --timeout 600

%files -n %{libname}
%license LICENSE ThirdPartyNotices.txt third-party-licenses/
%{_libdir}/libonnxruntime.so.*
%{_libdir}/libonnxruntime_providers_shared.so*

%files devel
%{_includedir}/onnxruntime/
%{_libdir}/libonnxruntime.so
%{_libdir}/pkgconfig/libonnxruntime.pc
%{_libdir}/cmake/onnxruntime/

%files tools
%{_bindir}/onnx_test_runner

%changelog
* Thu Oct 01 2026 David Nichols <david@qore.org> - 1.22.2-1.qore
- Build CPU inference and upstream tests from verified offline sources.
