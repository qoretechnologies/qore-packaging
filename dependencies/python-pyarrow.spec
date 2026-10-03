# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
#!BuildConstraint: hardware:physicalmemory:size unit=G 16
#!BuildConstraint: hardware:disk:size unit=G 20
%define pythons python313
%global source_date_epoch_from_changelog 1
%global use_source_date_epoch_as_buildtime 1
%if v"%{rpmversion}" >= v"4.20"
%global build_mtime_policy clamp_to_source_date_epoch
%else
%global clamp_mtime_to_source_date_epoch 1
%endif
Name: python-pyarrow
Version: 25.0.1
Release: 1.qore%{?dist}
Summary: Apache Arrow Python bindings with Flight support
License: Apache-2.0
URL: https://arrow.apache.org/
Source0: https://archive.apache.org/dist/arrow/arrow-%{version}/apache-arrow-%{version}.tar.gz
Source1: pyarrow-runtime-test.py
Source2: https://github.com/apache/arrow-testing/archive/9ff285c88565f0f6abc855918c6a342e70e4909c.tar.gz#/arrow-testing-9ff285c88565f0f6abc855918c6a342e70e4909c.tar.gz
Source3: https://github.com/apache/parquet-testing/archive/e74785d85a4ecee829e1e405444d6a1b24b8bc9c.tar.gz#/parquet-testing-e74785d85a4ecee829e1e405444d6a1b24b8bc9c.tar.gz
Patch0: pyarrow-unused-libcst-build-requirement.patch
Patch1: pyarrow-rank-test-deprecation.patch
BuildRequires: %{python_module devel >= 3.10}
BuildRequires: %{python_module Cython >= 3.1}
BuildRequires: %{python_module numpy-devel >= 1.25}
BuildRequires: %{python_module pip}
BuildRequires: %{python_module scikit-build-core}
BuildRequires: %{python_module setuptools_scm >= 8}
BuildRequires: %{python_module pytest}
BuildRequires: %{python_module hypothesis}
BuildRequires: %{python_module pytz}
BuildRequires: %{python_module cffi}
BuildRequires: apache-arrow-devel = %{version}
BuildRequires: apache-arrow-compute-devel = %{version}
BuildRequires: apache-arrow-acero-devel = %{version}
BuildRequires: apache-arrow-dataset-devel = %{version}
BuildRequires: apache-arrow-flight-devel = %{version}
BuildRequires: apache-parquet-devel = %{version}
BuildRequires: cmake >= 3.25
BuildRequires: ninja
BuildRequires: gcc-c++
BuildRequires: gdb
BuildRequires: python-rpm-macros
BuildRequires: fdupes
BuildRequires: timezone
Requires: python-numpy >= 1.25
%python_subpackages

%description
Python APIs for Arrow arrays, compute, IPC, streaming execution, datasets,
Parquet and Flight RPC. The bindings use shared system Arrow libraries.
Cloud storage, CUDA, Gandiva, ORC, HDFS, Substrait and Parquet encryption
bindings are not enabled in this package.

%prep
%autosetup -p1 -n apache-arrow-%{version}
tar -xf %{SOURCE2}
tar -xf %{SOURCE3}
cp %{SOURCE1} rpm-runtime-test.py

%build
%{?set_build_flags}
export CMAKE_BUILD_PARALLEL_LEVEL=%{_smp_build_ncpus}
export SKBUILD_CMAKE_BUILD_TYPE=Release
export SKBUILD_INSTALL_STRIP=false
export SKBUILD_CMAKE_ARGS="-DCMAKE_CXX_FLAGS_RELEASE=-DNDEBUG;-DCMAKE_C_FLAGS_RELEASE=-DNDEBUG"
export PYARROW_BUNDLE_ARROW_CPP=OFF
export PYARROW_WITH_ACERO=ON PYARROW_WITH_DATASET=ON PYARROW_WITH_FLIGHT=ON
export PYARROW_WITH_PARQUET=ON PYARROW_WITH_PARQUET_ENCRYPTION=OFF
export PYARROW_WITH_CUDA=OFF PYARROW_WITH_GANDIVA=OFF PYARROW_WITH_SUBSTRAIT=OFF
export PYARROW_WITH_ORC=OFF PYARROW_WITH_HDFS=OFF
export PYARROW_WITH_AZURE=OFF PYARROW_WITH_GCS=OFF PYARROW_WITH_S3=OFF
cd python
%pyproject_wheel

%install
cd python
%pyproject_install
%python_expand %fdupes %{buildroot}%{$python_sitearch}

%check
export ARROW_TEST_DATA="$PWD/arrow-testing-9ff285c88565f0f6abc855918c6a342e70e4909c/data"
export PARQUET_TEST_DATA="$PWD/parquet-testing-e74785d85a4ecee829e1e405444d6a1b24b8bc9c/data"
export PYTHONDONTWRITEBYTECODE=1
%{python_expand export PYTHONPATH=%{buildroot}%{$python_sitearch}
# Import from the staged wheel, never the unbuilt source package.
$python -W error -m pytest -v rpm-runtime-test.py
# An explicit test directory lets pytest load its conftest options before parsing.
test_dir=$($python -c 'from pathlib import Path; import pyarrow; print(Path(pyarrow.__file__).parent / "tests")')
$python -W error -m pytest -v "$test_dir" \
  --enable-acero --enable-dataset --enable-flight --enable-parquet \
  --enable-numpy
}

%files %{python_files}
%license LICENSE.txt NOTICE.txt
%doc python/README.md
%{python_sitearch}/pyarrow/
%{python_sitearch}/pyarrow-%{version}.dist-info/

%changelog
* Sat Oct 03 2026 David Nichols <david@qore.org> - 25.0.1-1.qore
- Provide system-linked Python Arrow and Flight fixtures for Leap gRPC builds.
- Run installed API regressions and upstream tests with pinned offline data.
