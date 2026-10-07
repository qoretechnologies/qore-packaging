set -eu
# Link controls to the built file: Node does not create an unversioned build-tree
# symlink, and an installed libnode-devel must never satisfy these link inputs.
# Reject invalid native metadata and exercise all upstream Wasm deoptimization suites.
python3 /sources/nodejs24-wasm-deopt-test.py --source . --test-source /sources/nodejs24-wasm-deopt-test.cc \
    --native-helper /sources/nodejs24-reschedule-test.py --tests wasm-deopt-tests --output out/wasm-deopt-control
# Exercise the actual native compiler archives and their generated snapshot.
python3 /sources/nodejs24-reschedule-test.py --source . --test-source /sources/nodejs24-reschedule-test.cc \
    --output out/reschedule-control
# Verify actual external resources and their forwarded one-byte representation.
g++ -O2 -Wall -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=3 -fstack-protector-strong -funwind-tables -fasynchronous-unwind-tables -fstack-clash-protection -Werror=return-type -flto=auto -g -std=c++20 -Wall -Werror=return-type -Ideps/v8/include \
    /sources/nodejs24-external-string-resource-test.cc -Lout/Release -Wl,-rpath,"$PWD/out/Release" \
    out/Release/libnode.so.137 -licuuc -lcrypto -ldl -pthread -o out/external-string-resource-control
out/external-string-resource-control ordinary
out/external-string-resource-control shared
python3 - <<'EXTERNALCHECK'
import resource, subprocess
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
for mode in ('ordinary', 'shared'):
    result = subprocess.run(['out/external-string-resource-control', mode, 'negative'],
                            capture_output=True, text=True)
    if result.returncode >= 0 or 'expected == value' not in result.stderr:
        raise AssertionError((mode, result.returncode, result.stderr))
    print('Incorrect external string resource rejected:', mode)
EXTERNALCHECK
# Negative internal timezone indexes must fail a CHECK before enumeration.
python3 /sources/nodejs24-timezone-index-test.py --source . --output out/timezone-index-control --cxxflags="-O2 -Wall -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=3 -fstack-protector-strong -funwind-tables -fasynchronous-unwind-tables -fstack-clash-protection -Werror=return-type -flto=auto -g"
# Keep the same distribution flags when test-build regenerates native targets.
. ./node-build-flags.sh
# Keep the c-ares lint exception safe for every architecture and source update.
python3 /sources/nodejs24-rpm-symbols.py out/Release/libnode.so.137
# Node's SQLite implementation must not interpose on an embedding application's
# independently loaded SQLite library. Its upstream target uses hidden symbols.
nm -D --defined-only out/Release/libnode.so.137 > out/Release/exported-symbols.txt
if grep -Eq '[[:space:]]sqlite3_[[:alnum:]_]+' out/Release/exported-symbols.txt; then
    echo 'Node private SQLite symbols escaped into the shared ABI' >&2
    exit 1
fi
# Run the native and JavaScript groups from test-ci, including addon examples.
# The locked documentation tools are supplied in Source1 for offline builds.
make -j2 test-build bench-addons-build
out/Release/cctest
# Exercise default/forced compaction, heap integrity and optional verbose tracing.
python3 -B -W error /sources/nodejs24-compaction-trace-test.py out/Release/node
# Test the real inline platform priority mapper, including invalid int indexes.
g++ -O2 -Wall -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=3 -fstack-protector-strong -funwind-tables -fasynchronous-unwind-tables -fstack-clash-protection -Werror=return-type -flto=auto -g -std=c++20 -Wall -Werror=return-type -Ideps/v8 -Ideps/v8/include \
    /sources/nodejs24-platform-priority-test.cc -Lout/Release -Wl,-rpath,"$PWD/out/Release" out/Release/libnode.so.137 -pthread -o out/platform-priority-control
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
# Exercise the actual allocator status implementation, including unnamed values.
g++ -O2 -Wall -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=3 -fstack-protector-strong -funwind-tables -fasynchronous-unwind-tables -fstack-clash-protection -Werror=return-type -flto=auto -g -std=c++20 -Wall -Werror=return-type -ffunction-sections -fdata-sections \
    -Ideps/v8 -Ideps/v8/include deps/v8/src/base/bounded-page-allocator.cc \
    /sources/nodejs24-allocation-status-test.cc -Lout/Release -Wl,-rpath,"$PWD/out/Release" -Wl,--gc-sections \
    out/Release/libnode.so.137 -pthread -o out/allocation-status-control
out/allocation-status-control
python3 - <<'STATUSCHECK'
import resource, signal, subprocess
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
for status in ('-1', '4', '255', '256', '2147483647', '-2147483648'):
    result = subprocess.run(['out/allocation-status-control', status], capture_output=True, text=True)
    if result.returncode != -signal.SIGABRT or 'unreachable code' not in result.stderr:
        raise AssertionError((status, result.returncode, result.stderr))
    print('Invalid allocation status rejected:', status)
STATUSCHECK
g++ -O2 -Wall -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=3 -fstack-protector-strong -funwind-tables -fasynchronous-unwind-tables -fstack-clash-protection -Werror=return-type -flto=auto -g -std=c++20 -Wall -Werror=return-type -ffunction-sections -fdata-sections \
    -Ideps/v8 -Ideps/v8/include deps/v8/src/base/virtual-address-space.cc \
    /sources/nodejs24-page-permissions-test.cc -Lout/Release -Wl,-rpath,"$PWD/out/Release" -Wl,--gc-sections \
    out/Release/libnode.so.137 -pthread -o out/page-permissions-control
out/page-permissions-control
python3 - <<'PERMISSIONCHECK'
import resource, signal, subprocess
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
for value in ('-1', '5', '255', '256', '2147483647', '-2147483648'):
    for pair in ((value, '0'), ('0', value)):
        result = subprocess.run(['out/page-permissions-control', *pair], capture_output=True, text=True)
        if result.returncode != -signal.SIGABRT or 'unreachable code' not in result.stderr:
            raise AssertionError((pair, result.returncode, result.stderr))
        print('Invalid page permissions rejected:', pair)
PERMISSIONCHECK
g++ -O2 -Wall -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=3 -fstack-protector-strong -funwind-tables -fasynchronous-unwind-tables -fstack-clash-protection -Werror=return-type -flto=auto -g -std=c++20 -Wall -Werror=return-type -Ideps/v8 -Ideps/v8/include \
    -Ideps/v8/third_party/abseil-cpp /sources/nodejs24-torque-abort-test.cc -Lout/Release \
    -Wl,-rpath,"$PWD/out/Release" out/Release/libnode.so.137 -pthread -o out/torque-abort-control
out/torque-abort-control
python3 - <<'TORQUECHECK'
import resource, signal, subprocess
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
for kind in ('-1', '3', '255', '256', '2147483647', '-2147483648'):
    result = subprocess.run(['out/torque-abort-control', kind], capture_output=True, text=True)
    if result.returncode != -signal.SIGABRT or 'unreachable code' not in result.stderr:
        raise AssertionError((kind, result.returncode, result.stderr))
    print('Invalid Torque abort kind rejected:', kind)
TORQUECHECK
g++ -O2 -Wall -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=3 -fstack-protector-strong -funwind-tables -fasynchronous-unwind-tables -fstack-clash-protection -Werror=return-type -flto=auto -g -std=c++20 -Wall -Werror=return-type -ffunction-sections -fdata-sections \
    -Ideps/v8 -Ideps/v8/include -Ideps/v8/third_party/abseil-cpp \
    deps/v8/src/torque/types.cc /sources/nodejs24-torque-handle-test.cc -Lout/Release \
    -Wl,-rpath,"$PWD/out/Release" -Wl,--gc-sections out/Release/libnode.so.137 -pthread -o out/torque-handle-control
out/torque-handle-control
python3 - <<'HANDLECHECK'
import resource, signal, subprocess
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
for kind in ('-1', '2', '255', '256', '2147483647', '-2147483648'):
    result = subprocess.run(['out/torque-handle-control', kind], capture_output=True, text=True)
    if result.returncode != -signal.SIGABRT or 'unreachable code' not in result.stderr:
        raise AssertionError((kind, result.returncode, result.stderr))
    print('Invalid Torque handle kind rejected:', kind)
HANDLECHECK
g++ -O2 -Wall -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=3 -fstack-protector-strong -funwind-tables -fasynchronous-unwind-tables -fstack-clash-protection -Werror=return-type -flto=auto -g -std=c++20 -Wall -Werror=return-type -ffunction-sections -fdata-sections \
    -Ideps/v8 -Ideps/v8/include -Ideps/v8/third_party/abseil-cpp \
    /sources/nodejs24-torque-prefix-test.cc -Lout/Release -Wl,-rpath,"$PWD/out/Release" \
    -Wl,--gc-sections out/Release/libnode.so.137 -pthread -o out/torque-prefix-control
out/torque-prefix-control
python3 - <<'PREFIXCHECK'
import resource, signal, subprocess
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
for kind in ('-1', '2', '255', '256', '2147483647', '-2147483648'):
    result = subprocess.run(['out/torque-prefix-control', kind], capture_output=True, text=True)
    if result.returncode != -signal.SIGABRT or 'unreachable code' not in result.stderr:
        raise AssertionError((kind, result.returncode, result.stderr))
    print('Invalid Torque diagnostic kind rejected:', kind)
PREFIXCHECK
g++ -O2 -Wall -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=3 -fstack-protector-strong -funwind-tables -fasynchronous-unwind-tables -fstack-clash-protection -Werror=return-type -flto=auto -g -std=c++20 -Wall -Werror=return-type -Ideps/v8 -Ideps/v8/include \
    -Ideps/v8/third_party/abseil-cpp /sources/nodejs24-torque-stack-test.cc -Lout/Release \
    -Wl,-rpath,"$PWD/out/Release" out/Release/libnode.so.137 -pthread -o out/torque-stack-control
out/torque-stack-control
python3 - <<'STACKCHECK'
import resource, signal, subprocess
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
for count in ('5', '255', '4294967295', '18446744073709551615'):
    result = subprocess.run(['out/torque-stack-control', count], capture_output=True, text=True)
    if result.returncode != -signal.SIGABRT or 'elements_.size() >= count' not in result.stderr:
        raise AssertionError((count, result.returncode, result.stderr))
    print('Invalid Torque pop count rejected:', count)
STACKCHECK
# Compile the bundled SQLite source with its actual feature definitions.
# Cover RTree dimensions, session length overflow, truncated varints and OOM.
python3 - /sources/nodejs24-sqlite-test.c <<'SQLITECHECK'
import ast, shlex, subprocess, sys
from pathlib import Path
config = ast.literal_eval(Path('deps/sqlite/sqlite.gyp').read_text())
defines = config['targets'][0]['defines']
subprocess.run(['gcc', *shlex.split('-O2 -Wall -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=3 -fstack-protector-strong -funwind-tables -fasynchronous-unwind-tables -fstack-clash-protection -Werror=return-type -flto=auto -g'), '-Wall', '-Wextra',
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
    g++ -O2 -Wall -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=3 -fstack-protector-strong -funwind-tables -fasynchronous-unwind-tables -fstack-clash-protection -Werror=return-type -flto=auto -g -std=c++20 -Wall -Wextra -Werror $ada_flags \
        -Ideps/ada -Ideps/v8/third_party/simdutf \
        deps/ada/ada.cpp $ada_sources /sources/nodejs24-ada-conversion-test.cc -o out/ada-control/$mode
    out/ada-control/$mode
done
# Repeated embedding must share the signal watchdog; concurrent environments
# must remain independent. Count successful detached-thread creation directly.
mkdir -p out/inspector-control
gcc -O2 -Wall -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=3 -fstack-protector-strong -funwind-tables -fasynchronous-unwind-tables -fstack-clash-protection -Werror=return-type -flto=auto -g -UNDEBUG -fPIC -shared /sources/nodejs24-detached-thread-counter.c \
    -o out/inspector-control/counter.so -ldl -pthread
g++ -O2 -Wall -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=3 -fstack-protector-strong -funwind-tables -fasynchronous-unwind-tables -fstack-clash-protection -Werror=return-type -flto=auto -g -UNDEBUG -std=c++20 -isystem src -isystem deps/v8/include \
    -isystem deps/uv/include /sources/nodejs24-inspector-lifetimes.cc -Lout/Release -Lout/inspector-control \
    -Wl,-rpath,"$PWD/out/Release:$PWD/out/inspector-control" \
    -l:counter.so out/Release/libnode.so.137 -pthread -o out/inspector-control/control
LD_PRELOAD="$PWD/out/inspector-control/counter.so" out/inspector-control/control serial 100
LD_PRELOAD="$PWD/out/inspector-control/counter.so" out/inspector-control/control concurrent 10
python3 tools/test.py -j 2 -p tap --mode=release \
    --flaky-tests=run default pummel addons ffi js-native-api node-api embedding benchmark
