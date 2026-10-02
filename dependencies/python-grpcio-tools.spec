#
# spec file for package python-grpcio-tools
#
# Copyright (c) 2026 SUSE LLC and contributors
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


%define pythons python313
%global source_date_epoch_from_changelog 1
%global use_source_date_epoch_as_buildtime 1
%if v"%{rpmversion}" >= v"4.20"
%global build_mtime_policy clamp_to_source_date_epoch
%else
%global clamp_mtime_to_source_date_epoch 1
%endif
# 1.68.1 generates Protobuf 5.28.1 code accepted by Leap's 5.28.3 runtime.
%define         modname grpcio_tools
%{?sle15_python_module_pythons}
Name:           python-grpcio-tools
Version:        1.68.1
Release:        1.qore%{?dist}
Summary:        Protobuf code generator for gRPC
License:        Apache-2.0 AND BSD-3-Clause AND MIT
Group:          Development/Languages/Python
URL:            https://grpc.io
Source:         https://files.pythonhosted.org/packages/source/g/grpcio-tools/grpcio_tools-%{version}.tar.gz
Source1:        grpcio-tools-GRPC-LICENSE
Source2:        grpcio-tools-PROTOBUF-LICENSE
Source3:        grpcio-tools-ABSEIL-LICENSE
Source4:        grpcio-tools-UTF8-LICENSE
Source5:        grpcio-tools-license-sources.json
Source6:        grpcio-tools-test-sources.json
Source7:        grpcio-tools-runtime-test.py
Source8:        grpcio-tools-protoc_test.py
Source9:        grpcio-tools-simple.proto
Source10:        grpcio-tools-simpler.proto
Source11:        grpcio-tools-simplest.proto
Source12:        grpcio-tools-complicated.proto
Source13:        grpcio-tools-flawed.proto
Patch0:         grpcio-tools-build-declarations.patch
BuildRequires:  %{python_module Cython >= 3.0}
BuildRequires:  %{python_module devel >= 3.10}
BuildRequires:  %{python_module pip}
BuildRequires:  %{python_module setuptools >= 77}
BuildRequires:  %{python_module wheel}
BuildRequires:  fdupes
BuildRequires:  gcc-c++
BuildRequires:  python-rpm-macros
Requires:       python-grpcio >= %{version}
Requires:       python-protobuf >= 5.28.1
Requires:       python-protobuf < 6
Requires:       python-setuptools
# SECTION test requirements
BuildRequires:  %{python_module grpcio >= %{version}}
BuildRequires:  %{python_module protobuf >= 5.28.1}
BuildRequires:  %{python_module pytest}
# /SECTION
Provides:       bundled(protobuf) = 28.1
Provides:       bundled(abseil-cpp) = 20240722.0
Provides:       bundled(utf8_range)
%python_subpackages

%description
This package provides a python-based Protobuf code generator for gRPC.

%prep
%autosetup -p1 -n %{modname}-%{version}
# Drop a hashbang from anon-exec script
sed -i "1{/\/usr\/bin\/env python/d}" grpc_tools/protoc.py

mkdir -p rpm-licenses
cp %{SOURCE1} rpm-licenses/
cp %{SOURCE2} rpm-licenses/
cp %{SOURCE3} rpm-licenses/
cp %{SOURCE4} rpm-licenses/
cp %{SOURCE5} rpm-licenses/
cp %{SOURCE6} rpm-licenses/

%build
%{?set_build_flags}
export GRPC_PYTHON_BUILD_WITH_CYTHON=true
export GRPC_PYTHON_BUILD_EXT_COMPILER_JOBS=%{_smp_build_ncpus}
export CFLAGS="%{optflags}"
%pyproject_wheel

%install
%pyproject_install
%python_expand %fdupes %{buildroot}%{$python_sitearch}

%check
# Run upstream dynamic/static compiler tests and real installed gRPC calls.
mkdir -p build/package-tests/tools/distrib/python/grpcio_tools/grpc_tools/test
fixture="$PWD/build/package-tests/tools/distrib/python/grpcio_tools/grpc_tools/test"
cp %{SOURCE7} "$fixture/runtime-test.py"
cp %{SOURCE8} "$fixture/protoc_test.py"
cp %{SOURCE9} "$fixture/simple.proto"
cp %{SOURCE10} "$fixture/simpler.proto"
cp %{SOURCE11} "$fixture/simplest.proto"
cp %{SOURCE12} "$fixture/complicated.proto"
cp %{SOURCE13} "$fixture/flawed.proto"
%{python_expand export PYTHONPATH=%{buildroot}%{$python_sitearch}
export PYTHONDONTWRITEBYTECODE=1
(
  cd build/package-tests
  fixture=tools/distrib/python/grpcio_tools/grpc_tools/test
  $python -W error -m grpc_tools.protoc -I"$fixture" --python_out="$fixture" --grpc_python_out="$fixture" \
    "$fixture/simple.proto" "$fixture/simpler.proto" "$fixture/simplest.proto" "$fixture/complicated.proto"
  $python -W error "$fixture/protoc_test.py" -v
  $python -W error "$fixture/runtime-test.py"
)
}

%files %{python_files}
%license rpm-licenses/*
%doc README.rst
%{python_sitearch}/grpc_tools
%{python_sitearch}/grpcio_tools-%{version}.dist-info

%changelog
* Fri Oct 02 2026 David Nichols <david@qore.org> - 1.68.1-1.qore
- Supply Leap fixtures compatible with its gRPC 1.69 and Protobuf 5.28 runtimes.
- Retain bundled component licenses and run pinned upstream and loopback tests.
