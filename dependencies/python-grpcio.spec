#
# spec file for package python-grpcio
#
# Copyright (c) 2026 SUSE LLC and contributors
# Copyright (c) 2026 Qore Technologies, s.r.o. (shared-library coexistence)
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
%global modname grpcio
%{?sle15_python_module_pythons}
Name:           python-grpcio
Version:        1.69.0
Release:        160000.2.3.qore%{?dist}
Summary:        HTTP/2-based Remote Procedure Call implementation
License:        Apache-2.0 AND BSD-2-Clause AND BSD-3-Clause AND MIT
Group:          Development/Languages/Python
URL:            https://grpc.io
Source:         https://files.pythonhosted.org/packages/source/g/grpcio/grpcio-%{version}.tar.gz
# PATCH-FIX-SLE xxhash-avoid-armv6-unaligned-access.patch alarrosa@suse.com -- do not expect unaligned accesses to work on armv6
Patch1:         grpcio-xxhash-avoid-armv6-unaligned-access.patch
# PATCH-FIX-SLE xxhash-ppc64le-gcc7.patch boo#1208794 alarrosa@suse.com -- fix build failure on ppc64le when using gcc 7
Patch2:         grpcio-xxhash-ppc64le-gcc7.patch
Patch3:         grpcio-fix-return-values.patch
Patch4:         grpcio-lifecycle-build.patch
# Upstream 5c18ce423ae0: yield to draining workers during pool shutdown.
Patch5:         grpcio-thread-pool-shutdown.patch
# Upstream a6292134a53c: replace deprecated Cython compile-time IF.
Patch6:         grpcio-cython-if.patch
# Keep native operation buffers until Core completes, including cancellation.
Patch7:         grpcio-aio-batch-ownership.patch
Patch8:         grpcio-aio-queue-release.patch
Patch9:         grpcio-native-types.patch
Patch10:        grpcio-aio-wakeup.patch
Patch11:        grpcio-poll-init-cleanup.patch
Patch12:        grpcio-unused-priority.patch
Patch13:        grpcio-manifest-sources.patch
Patch14:        grpcio-license-metadata.patch
BuildRequires:  %{python_module Cython >= 0.29.8}
BuildRequires:  %{python_module devel >= 3.7}
BuildRequires:  %{python_module pip}
BuildRequires:  %{python_module setuptools >= 77.0.0}
BuildRequires:  %{python_module wheel >= 0.29}
# The embedded gRPC core and its Abseil flag registry must stay private together.
# Sharing only Abseil collides with libgrpc loaded by Arrow Flight.
Provides:       bundled(abseil-cpp) = 20240722.0
Provides:       bundled(upb)
Provides:       bundled(utf8_range)
Provides:       bundled(xxhash)
Provides:       bundled(address_sorting)
BuildRequires:  %{python_module coverage}
BuildRequires:  %{python_module pytest}
BuildRequires:  pkgconfig(grpc)
BuildRequires:  ca-certificates
BuildRequires:  fdupes
BuildRequires:  gcc-c++
BuildRequires:  binutils
BuildRequires:  pkgconfig
BuildRequires:  python-rpm-macros
BuildRequires:  python-rpm-packaging
BuildRequires:  pkgconfig(libcares)
BuildRequires:  pkgconfig(openssl)
BuildRequires:  pkgconfig(re2)
BuildRequires:  pkgconfig(zlib)
Requires:       ca-certificates
Source1:        https://github.com/grpc/grpc/archive/refs/tags/v%{version}.tar.gz#/grpc-v%{version}.tar.gz
Source2:        grpcio-coexistence-test.py
Source3:        grpcio-ABSEIL-LICENSE
Source4:        grpcio-UPB-LICENSE
Source5:        grpcio-UTF8-LICENSE
Source6:        grpcio-XXHASH-LICENSE
Source7:        grpcio-ADDRESS-LICENSE
Source8:        grpcio-license-sources.json
Source9:        grpcio-native-types-test.cc
Source10:       grpcio-wakeup-test.cc
Source11:       grpcio-wakeup-inject.c
Source12:       grpcio-wakeup-test.py
Source13:       grpcio-poll-init-test.cc
%python_subpackages

%description
gRPC is a remote procedure call (RPC) framework. gRPC enables client
and server applications to communicate, and enables the building of
connected systems.

%prep
%setup -q -n grpcio-%{version}
tar -xf %{SOURCE1}
%autopatch -p1
mkdir -p rpm-licenses
cp %{SOURCE3} rpm-licenses/
cp %{SOURCE4} rpm-licenses/
cp %{SOURCE5} rpm-licenses/
cp %{SOURCE6} rpm-licenses/
cp %{SOURCE7} rpm-licenses/
cp %{SOURCE8} rpm-licenses/


%build
export GRPC_BUILD_WITH_BORING_SSL_ASM=false
unset GRPC_PYTHON_BUILD_SYSTEM_ABSL
export GRPC_PYTHON_BUILD_SYSTEM_CARES=true
export GRPC_PYTHON_BUILD_SYSTEM_OPENSSL=true
export GRPC_PYTHON_BUILD_SYSTEM_RE2=true
export GRPC_PYTHON_BUILD_SYSTEM_ZLIB=true
export GRPC_PYTHON_BUILD_WITH_CYTHON=true
# System RE2 exposes std::string_view; C++17 keeps the bundled Abseil headers
# ABI-compatible while preserving the upstream hidden-symbol/exception policy.
export CFLAGS="%{optflags}"
export GRPC_PYTHON_CFLAGS="-std=c++17 -fvisibility=hidden -fno-wrapv -fno-exceptions"
export GRPC_PYTHON_BUILD_EXT_COMPILER_JOBS=%{_smp_build_ncpus}
%pyproject_wheel

%install
%pyproject_install
%python_expand %fdupes %{buildroot}%{$python_sitearch}
# a symlink to the shared system certificates is used
%{python_expand $python - "%{buildroot}%{$python_sitearch}/grpc/_cython/_credentials/roots.pem" <<'PYLINK'
import os, sys
link = sys.argv[1]
target = os.path.relpath("%{buildroot}%{_localstatedir}/lib/ca-certificates/ca-bundle.pem", os.path.dirname(link))
os.unlink(link)
os.symlink(target, link)
PYLINK
}

%check
mkdir -p build/package-tests
# Reuse the exact private Abseil objects built for this extension. Number the
# archive members so equal basenames in different directories remain distinct.
python3 - <<'PYABSL'
from pathlib import Path
import runpy, shutil, subprocess
sources = runpy.run_path('src/python/grpcio/grpc_core_dependencies.py')['CORE_SOURCE_FILES']
sources = [Path(p) for p in sources if p.startswith('third_party/abseil-cpp/')]
assert sources
objects = []
for index, source in enumerate(sources):
    matches = list(Path('pyb').glob('temp.*/' + str(source.with_suffix('.o'))))
    assert len(matches) == 1, (source, matches)
    target = Path('build/package-tests') / (str(index) + '.o')
    shutil.copyfile(matches[0], target)
    objects.append(str(target))
subprocess.run(['ar', 'rcs', 'build/package-tests/absl.a', *objects], check=True)
PYABSL
%{__cxx} %{optflags} -std=c++17 -UNDEBUG -Wall -Wextra \
    -Werror=sign-compare -Werror=class-memaccess -ffunction-sections -fdata-sections \
    -I. -Iinclude -Ithird_party/abseil-cpp %{SOURCE9} \
    src/core/lib/event_engine/tcp_socket_utils.cc src/core/lib/event_engine/resolved_address.cc \
    src/core/ext/transport/chttp2/transport/decode_huff.cc \
    src/core/ext/transport/chttp2/transport/huffsyms.cc \
    build/package-tests/absl.a -Wl,--gc-sections -pthread -o build/package-tests/native-types
build/package-tests/native-types
# Exercise the actual poll implementation with injected wakeup-init failures.
# A thin archive preserves unique object paths and avoids duplicating the core.
python3 - <<'PYCORE'
from pathlib import Path
import subprocess
roots = list(Path('pyb').glob('temp.*'))
assert len(roots) == 1, roots
objects = [str(path) for path in roots[0].rglob('*.o')
           if path.name != 'cygrpc.o'
           and path.relative_to(roots[0]).as_posix() != 'src/core/lib/iomgr/ev_poll_posix.o']
assert objects and (roots[0] / 'src/core/lib/iomgr/ev_poll_posix.o').is_file()
subprocess.run(['ar', 'rcsT', 'build/package-tests/core.a', *sorted(objects)], check=True)
PYCORE
%{__cxx} %{optflags} -std=c++17 -DNDEBUG -Wall -Wextra \
    -ffunction-sections -fdata-sections -I. -Iinclude -Ithird_party/abseil-cpp \
    %{SOURCE13} build/package-tests/core.a -Wl,--gc-sections \
    -lssl -lcrypto -lcares -lre2 -lz -ldl -pthread -o build/package-tests/poll-init
build/package-tests/poll-init
python3 - <<'PYWAKE'
from pathlib import Path
source = Path('src/python/grpcio/grpc/_cython/_cygrpc/aio/completion_queue.pxd.pxi').read_text()
Path('build/package-tests/grpcio-wakeup-impl.h').write_text(source.split('"""', 2)[1])
PYWAKE
%{__cxx} %{optflags} -std=c++17 -UNDEBUG -Wall -Wextra -Werror \
    -Ibuild/package-tests %{SOURCE10} -o build/package-tests/wakeup
build/package-tests/wakeup
%{__cc} %{optflags} -std=c11 -Wall -Wextra -Werror -fPIC -shared \
    %{SOURCE11} -o build/package-tests/wakeup-inject.so
cp %{SOURCE2} build/package-tests/grpcio-coexistence-test.py
%{python_expand export PYTHONPATH=%{buildroot}%{$python_sitearch}
export PYTHONDONTWRITEBYTECODE=1
export GRPC_TEST_ROOT="$PWD/grpc-%{version}/src/python/grpcio_tests/tests/unit"
$python -W error -m pytest -v build/package-tests/grpcio-coexistence-test.py
for mode in 1 2 3; do
    LD_PRELOAD="$PWD/build/package-tests/wakeup-inject.so" $python -B -W error %{SOURCE12} "$mode"
done
(
    cd grpc-%{version}/src/python/grpcio_tests
    $python -W error -m unittest -v tests.unit._server_test tests.unit._channel_args_test \
        tests.unit._channel_connectivity_test tests.unit._channel_ready_future_test \
        tests.unit._rpc_part_1_test tests.unit._rpc_part_2_test \
        tests.unit._metadata_code_details_test tests.unit._metadata_flags_test \
        tests.unit._metadata_test tests.unit._abort_test tests.unit._utilities_test \
        tests.unit._cython._fork_test.ForkPosixTester.testForkManagedThread
)
}

%files %{python_files}
%doc README.md
%license LICENSE rpm-licenses/*
%{python_sitearch}/grpc/
%{python_sitearch}/%{modname}-%{version}.dist-info

%changelog
* Sat Oct 03 2026 David Nichols <david@qore.org> - 1.69.0-160000.2.3.qore
- Isolate the embedded gRPC core and its Abseil flag registry with upstream visibility.
- Retain system TLS, DNS, regular expressions and compression dependencies.
- Test both shared-library import orders and upstream client/server RPC behavior.
- Release never-started server resources and initialize inactive executor pointers.
- Apply C++ options only to C++ sources and correct inline/union attributes.
- Free TLS credential arrays and backport upstream thread-pool shutdown fix.
- Backport upstream Cython conditional compilation migration; test fork state and async RPC.
- Release async batch resources after Core completion or synchronous rejection.
- Release the idle global completion queue after its final async user.
- Use value initialization for resolved addresses and unsigned Huffman masks.
- Compare exhaustive short/random Huffman inputs with the upstream reference decoder.
- Retry EINTR on async wakeup writes and dispatch queued completions on notification failure.
- Verify interrupted, failed and zero-byte wakeups with native and injected RPC tests.
- Clear failed poll-worker handles and release uninitialized wakeup resources.
- Test failure, recovery, cached reuse and destruction with and without fork tracking.
- Remove an unused private priority method and obsolete source-manifest patterns.
- Use SPDX license metadata and include bundled-component notices in the wheel.
- Retain binary exclusions, including stale egg-info entries.
