# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
#!BuildConstraint: hardware:physicalmemory:size unit=G 16
#!BuildConstraint: hardware:disk:size unit=G 24
%global source_date_epoch_from_changelog 1
%global use_source_date_epoch_as_buildtime 1
%if v"%{rpmversion}" >= v"4.20"
%global build_mtime_policy clamp_to_source_date_epoch
%else
%global clamp_mtime_to_source_date_epoch 1
%endif
%global soname 137
Name: nodejs24-libnode
Version: 24.18.1
Release: 1.qore%{?dist}
Summary: Shared NodeJS 24 library for embedded JavaScript
License: MIT AND BSD-2-Clause AND BSD-3-Clause AND Apache-2.0 AND ISC AND BlueOak-1.0.0 AND CC0-1.0 AND blessing
URL: https://nodejs.org/
Source0: https://nodejs.org/dist/v%{version}/node-v%{version}.tar.xz
Source1: https://api.opensuse.org/public/source/home:davidnichols:qore:testing/%{name}/node-v24.18.1-doc-deps.tar.xz
Source2: nodejs24-doc-deps.json
Source3: nodejs24-localizationData-v77.1.json
Source4: nodejs24-detached-thread-counter.c
Source5: nodejs24-inspector-lifetimes.cc
Source6: nodejs24-ada-conversion-test.cc
Source7: nodejs24-sqlite-test.c
Source8: nodejs24-SQLITE-LICENSE
Source9: nodejs24-rpm-symbols.py
Source10: nodejs24-libnode-rpmlintrc
Source11: nodejs24-platform-priority-test.cc
Patch0: nodejs24-cxx-visibility.patch
Patch1: nodejs24-cppgc-realm-lifetime.patch
Patch2: nodejs24-compression-cleanup.patch
Patch3: nodejs24-inspector-environments.patch
Patch4: nodejs24-ada-conversion-result.patch
Patch5: nodejs24-sqlite-types.patch
Patch6: nodejs24-sqlite-lengths.patch
Patch7: nodejs24-crypto-test-types.patch
Patch8: nodejs24-platform-priority.patch
BuildRequires: gcc-c++
BuildRequires: make
BuildRequires: python3
BuildRequires: python3-setuptools
BuildRequires: pkgconfig(openssl)
BuildRequires: pkgconfig(zlib)
BuildRequires: pkgconfig(icu-i18n)
BuildRequires: pkgconfig(libcares) >= 1.34.8
BuildRequires: pkgconfig(libnghttp2) >= 1.70.0
BuildRequires: pkgconfig(libbrotlidec)
BuildRequires: pkgconfig(libbrotlienc)
BuildRequires: pkgconfig(libzstd)
BuildRequires: procps
BuildRequires: timezone
BuildRequires: openssl

%description
Shared NodeJS runtime and matching headers for applications embedding V8 and
Node APIs. This source package complements the distribution's Node executable.

%package -n libnode%{soname}
Summary: Shared NodeJS 24 runtime
Provides: bundled(ada) = 3.4.4
Provides: bundled(libuv) = 1.52.1
Provides: bundled(llhttp) = 9.4.3
Provides: bundled(merve) = 1.2.2
Provides: bundled(node-acorn) = 8.16.0
Provides: bundled(node-acorn-walk) = 8.3.5
Provides: bundled(node-amaro) = 1.1.9
Provides: bundled(node-minimatch) = 10.2.5
Provides: bundled(node-undici) = 7.29.0
Provides: bundled(simdjson) = 4.6.4
Provides: bundled(sqlite) = 3.53.1
Provides: bundled(uvwasi) = 0.0.23
Provides: bundled(v8) = 13.6.233.17
%description -n libnode%{soname}
NodeJS and V8 shared library, including built-in TypeScript transformation.
TLS, ICU, compression, HTTP/2 and DNS use system shared libraries.
SQLite uses Node's private build with the complete Node SQL feature set.
Bundled components retain their upstream notices in the complete LICENSE file.

%package -n libnode-devel
Summary: Development headers for the NodeJS 24 shared runtime
Requires: libnode%{soname} = %{version}-%{release}
%description -n libnode-devel
Matching development headers and linker files for embedding the shared NodeJS
runtime in native applications.

%prep
%autosetup -p1 -n node-v%{version}
cp %{SOURCE8} SQLITE-LICENSE
# Locked documentation tools also generate the native addon example tests.
%{__tar} -xf %{SOURCE1} -C tools/doc
cp %{SOURCE2} tools/doc/QORE-DEPENDENCIES.json
# Upstream versioned ICU fixture for the Leap system library.
cp %{SOURCE3} test/fixtures/icu/localizationData-v77.1.json
# The complete dependency tree is supplied as source; mark the Make target
# current against its package.json prerequisite to keep the build offline.
touch -r tools/doc/package.json tools/doc/node_modules

%build
export CFLAGS="%{optflags}"
export CXXFLAGS="%{optflags}"
export LDFLAGS="%{?build_ldflags}"
python3 configure --shared --prefix=%{_prefix} --libdir=%{_lib} \
    --without-npm --without-corepack --shared-openssl --shared-zlib \
    --shared-cares --shared-nghttp2 --shared-brotli --shared-zstd \
    --with-intl=system-icu --openssl-use-def-ca-store
%make_build

%install
install -D -m 0755 out/Release/libnode.so.%{soname} %{buildroot}%{_libdir}/libnode.so.%{soname}
ln -s libnode.so.%{soname} %{buildroot}%{_libdir}/libnode.so
python3 tools/install.py install --headers-only --dest-dir=%{buildroot} --prefix=%{_prefix}

%check
# Keep the c-ares lint exception safe for every architecture and source update.
python3 %{SOURCE9} out/Release/libnode.so.%{soname}
# Node's SQLite implementation must not interpose on an embedding application's
# independently loaded SQLite library. Its upstream target uses hidden symbols.
nm -D --defined-only out/Release/libnode.so.%{soname} > out/Release/exported-symbols.txt
if grep -Eq '[[:space:]]sqlite3_[[:alnum:]_]+' out/Release/exported-symbols.txt; then
    echo 'Node private SQLite symbols escaped into the shared ABI' >&2
    exit 1
fi
# Run the native and JavaScript groups from test-ci, including addon examples.
# The locked documentation tools are supplied in Source1 for offline builds.
%make_build test-build bench-addons-build
out/Release/cctest
# Test the real inline platform priority mapper, including invalid int indexes.
g++ %{optflags} -std=c++20 -Wall -Werror=return-type -Ideps/v8 -Ideps/v8/include \
    %{SOURCE11} -Lout/Release -Wl,-rpath,"$PWD/out/Release" -lnode -pthread -o out/platform-priority-control
out/platform-priority-control
python3 - <<'PRIORITYCHECK'
import resource, subprocess
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
for index in ('-1', '3', '256', '257', '258', '2147483647', '-2147483648'):
    result = subprocess.run(['out/platform-priority-control', index], capture_output=True, text=True)
    if result.returncode >= 0 or 'unreachable code' not in result.stderr:
        raise AssertionError((index, result.returncode, result.stderr))
    print('Invalid priority index rejected:', index)
PRIORITYCHECK
# Compile the bundled SQLite source with its actual feature definitions.
# Cover RTree dimensions, session length overflow, truncated varints and OOM.
python3 - %{SOURCE7} <<'SQLITECHECK'
import ast, shlex, subprocess, sys
from pathlib import Path
config = ast.literal_eval(Path('deps/sqlite/sqlite.gyp').read_text())
defines = config['targets'][0]['defines']
subprocess.run(['gcc', *shlex.split('%{optflags}'), '-Wall', '-Wextra',
                '-Wno-unused-parameter', '-Werror', '-D_GNU_SOURCE',
                *['-D' + value for value in defines], '-Ideps/sqlite',
                sys.argv[1], '-lm', '-ldl', '-pthread', '-o', 'out/sqlite-control'],
               check=True)
SQLITECHECK
out/sqlite-control
# Exercise the bundled Ada conversion in both supported implementation modes.
# Failed conversion must preserve the original label, including surrounding labels.
mkdir -p out/ada-control
for mode in simd scalar; do
    ada_flags=
    ada_sources=
    if test "$mode" = simd; then
        ada_flags=-DADA_USE_SIMDUTF
        ada_sources=deps/v8/third_party/simdutf/simdutf.cpp
    fi
    g++ %{optflags} -std=c++20 -Wall -Wextra -Werror $ada_flags \
        -Ideps/ada -Ideps/v8/third_party/simdutf \
        deps/ada/ada.cpp $ada_sources %{SOURCE6} -o out/ada-control/$mode
    out/ada-control/$mode
done
# Repeated embedding must share the signal watchdog; concurrent environments
# must remain independent. Count successful detached-thread creation directly.
mkdir -p out/inspector-control
gcc %{optflags} -UNDEBUG -fPIC -shared %{SOURCE4} \
    -o out/inspector-control/counter.so -ldl -pthread
g++ %{optflags} -UNDEBUG -std=c++20 -isystem src -isystem deps/v8/include \
    -isystem deps/uv/include %{SOURCE5} -Lout/Release -Lout/inspector-control \
    -Wl,-rpath,"$PWD/out/Release:$PWD/out/inspector-control" \
    -l:counter.so -l:libnode.so.%{soname} -pthread -o out/inspector-control/control
LD_PRELOAD="$PWD/out/inspector-control/counter.so" out/inspector-control/control serial 100
LD_PRELOAD="$PWD/out/inspector-control/counter.so" out/inspector-control/control concurrent 10
python3 tools/test.py -j %{_smp_build_ncpus} -p tap --mode=release \
    --flaky-tests=run default pummel addons ffi js-native-api node-api embedding benchmark

%post -n libnode%{soname} -p /sbin/ldconfig
%postun -n libnode%{soname} -p /sbin/ldconfig

%files -n libnode%{soname}
%license LICENSE SQLITE-LICENSE
%{_libdir}/libnode.so.%{soname}

%files -n libnode-devel
%license LICENSE SQLITE-LICENSE
%{_includedir}/node/
%{_libdir}/libnode.so

%changelog
* Mon Oct 05 2026 David Nichols <david@qore.org> - 24.18.1-1.qore
- Define the V8 worker priority boundary and reject narrowing-invalid indexes.
- Install SQLite's exact blessing notice and identify generated source downloads.
- Check resolver imports before applying the approved exact library lint filter.

* Sat Oct 03 2026 David Nichols <david@qore.org> - 24.18.1-1.qore
- Build the shared Node 24 runtime and matching embedding headers for Leap.
- Retain system dependencies, upstream runtime tests and bundled notices.
- Backport CppGC wrapper cleanup and per-environment inspector ownership fixes.
- Verify bounded watchdog creation and simultaneous embedding environments.
