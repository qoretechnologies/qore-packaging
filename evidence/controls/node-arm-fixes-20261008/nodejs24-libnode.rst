Node 24 embedding library for Leap
=================================

Copyright 2026 Qore Technologies, s.r.o.

``nodejs24-libnode.spec`` builds ``libnode137`` and ``libnode-devel`` for
openSUSE Leap 16. The distribution's Node executable remains separately
managed. Qore's V8 module uses the shared library and matching headers,
including Node's TypeScript transformation support.

The source manifest pins Node 24.18.1 and the offline documentation-tool tree.
The latter follows the upstream lockfile integrity records; its license and
preparation inventory is in ``nodejs24-doc-deps.json``. System libraries supply
TLS, ICU, DNS, HTTP/2 and compression. Node retains its private SQLite feature
set and hidden symbols. Both binary packages install the upstream notices
and SQLite's exact ``blessing`` notice.

The recipe includes tested fixes for CppGC realm teardown, OpenSSL compression
entry ownership, inspector environment lifetime, Ada Unicode conversion, SQLite length overflow, and worker-priority index validation. The CppGC, inspector and Ada patches identify their
upstream origins. Visibility flags apply to the correct source language, and
type/fallthrough changes retain existing values and behavior.

Every full RPM build runs the 192 native cases and upstream JavaScript groups,
including addon and embedding tests. Candidate 6 reported 5,249 JavaScript
results with no failures; upstream skips remain recorded. Additional controls
cover 2,129 Unicode cases in each conversion mode, truncated and oversized
SQLite values, allocation failures, 100 serial inspector lifetimes and ten
concurrent lifetimes. Focused Valgrind and UBSan results, installed Qore V8
runtime/SDK tests, and exact approved external diagnostics are recorded in
``evidence/node-*.json`` and ``evidence/v8-node6-installed-20261004.json``.

The current native-build update also validates V8's internal timezone index
before enumerating ICU zones. Negative indexes previously skipped the loop
and read an uninitialized pointer; they now fail V8's invariant check. The
package regression extracts the actual method, checks every ICU zone and UTC,
and exercises invalid boundaries. Release and Debug controls pass Valgrind;
this internal defect has not been demonstrated through JavaScript input.
The same update fixes verbose tracing of forced compaction so its reported
heuristic is initialized for every mode. The complete updated RPM and native Valgrind controls pass; native OBS
qualification remains required.

The package also fixes a missing pointer assignment in V8's external
string verifier. For a forwarded one-byte resource, the two-byte getter returns
null; the verifier now agrees with that result. The packaged baseline aborts
for this valid input. Native controls cover both encodings, ordinary and shared
storage, complete resource disposal and deliberate wrong-resource rejection.
Focused qualification and the complete updated RPM pass; native OBS
qualification remains required before publication.

The package also fixes uninitialized terminal-block state in V8's
``RawMachineAssembler``. The end block merges incoming return/throw controls
and then stops; it has no successors requiring an effect/control pair.
Seven native graph shapes pass 700 cases, including loops, merges, switches
and deferred throws. Diagnostic Memcheck requests expose 1,200 reads in the
original and none after the fix; both fixed runs free all allocations.
The RPM regression uses the package's actual compiler archives and generated
snapshot. It uses native sections of the fat archives with matching ABI,
feature, hardening and warning flags; the runtime retains its normal LTO.
The complete updated RPM passes; native architecture qualification remains required.

Leap's resolver checker mistakes ``ares_gethostbyaddr`` for a libc resolver
call. The approved filter covers only ``libnode137`` on x86_64/aarch64 and
``/usr/lib64/libnode.so.137``. Every build independently rejects all six
obsolete libc resolver imports before applying that filter. Negative tests
cover versioned symbols and unrelated lint messages. Other compiler and
memory diagnostics are accepted only at their recorded sites; normal flags
and raw logs remain enabled.

Prepare a reproducible source bundle from committed packaging::

    python3 -B tools/prepare-dependency.py --name nodejs24-libnode \
        --ref COMMITTED_REVISION --cache cache --output work/node-source

Only complete canonical RPM builds can be submitted. The metadata-only
short-circuit artifacts used during lint review are disposable and must not be
distributed. The canonical full build also passes the installed Leap SDK consumer and all
14 Qore V8 suites. OBS revision 1 has verified source hashes, including the
public generated-source download. Native revision 1 failed on GCC 13 at an incomplete priority return path.
The corrected mapper passes 90,000 checks, seven invalid-index cases and
Valgrind. Its canonical complete build and native qualification remain
required; publication is disabled. See ``evidence/node-canonical-qualification-20261005.json``.

The priority regression and compiler-specific reproduction are recorded in
``evidence/node-priority-boundary-20261005.json``. Normal compiler flags remain
enabled; out-of-range indexes are rejected before any narrowing conversion.

Offline DNS fixture qualification
---------------------------------

The pending-query and DNS heap-snapshot tests use a bound loopback DNS server.
An unreachable distribution resolver can complete a query synchronously, so the
original tests could observe no pending query or task list. The fixture responds
only after those assertions, checks the returned address and closes after query
completion. No sleeps, retries or resolver implementation changes are used.

Candidate 7 passed all 192 native tests but failed those two JavaScript fixtures.
Candidate 8 was not started. Candidate 10 passes the full RPM suite with the
qualified fixture, external-string and raw-graph fixes; native ARM
qualification remains required.

Wasm deoptimization metadata
---------------------------

Candidate 9 passes all 192 native and 5,249 JavaScript test results, plus
installed Qore/V8 runtime and SDK checks. Final compiler review exposed a
signed narrowing in Wasm metadata allocation and the missing assembly-result
check documented in upstream V8 change ``a548b49ac382``. Candidate 10 backports
that change: deoptimization points are not cloned, failed code generation is
rejected, and metadata counts, entry indexes and restored value kinds are
checked in release builds. A count bound is checked before conversion to int.

The native regression covers 1,969,500 valid allocation/serialization checks
and six rejected invalid states. Both original and corrected positive controls
have zero Valgrind errors and free all allocations; only the corrected source
rejects all six invalid states. The actual standalone generator compilation
is clean in both variants, so it does not reproduce the full LTO allocation
warning. The complete candidate-10 RPM/LTO build now passes and emits no Wasm
allocation warning; native ARM validation remains a gate.

The RPM also runs all 31 V8 13.6.233.17 Wasm deoptimization scripts. Their
unchanged sources and BSD license are supplied in a reproducible, hash-pinned
archive; ``nodejs24-wasm-deopt-tests.json`` records every upstream URL and hash.
The Node adapter implements only d8's file-loading and print conveniences.
No compiler warnings, checks or runtime features are disabled by this fix.

The final retained candidate-10 build passes 192 native tests, 5,249 reported
JavaScript results and all 31 additional Wasm deoptimization scripts. All five
native memory controls are qualified. Three free every allocation; both string
controls retain only the six previously approved process-lifetime records
(216 reachable bytes), with no lost allocations or invalid accesses. All 571
unique compiler diagnostics match their reviewed, approved scope. Raw logs,
including the two expected Valgrind exit codes of 99, remain in
``evidence/node-candidate10-final-20261007.json`` and its control directory.

Native control link inputs
--------------------------

Node produces ``out/Release/libnode.so.137`` without an unversioned development
symlink. Every shared-library control links that exact file. This makes the
controls independent of an installed ``libnode-devel`` package and rejects a
missing build output instead of selecting a library from the build host.
``tests/test_node_link_inputs.py`` exercises each recipe link input with a
versioned-only library, a competing installed library, and a missing build
output. The regression also demonstrates how the original ``-lnode`` input
could select the installed development library.

Private V8 controls also use the bundled Abseil include directory explicitly.
V8's mutex header includes Abseil unconditionally; an installed
``abseil-cpp-devel`` package previously masked three missing include paths in
the local builder. The same recipe then failed in clean native OBS. The header
regression exercises all seven private-header consumers without system headers
and with an incompatible competing system header, and verifies both failure
modes of the original search path. Complete check-phase qualification removes
both Node and Abseil development packages from the disposable build container.

Loopback hosts and credential fixtures
--------------------------------------

On openSUSE, ``netcfg`` is an explicit build dependency. Its hosts file supplies
both IPv4 and IPv6 localhost names, which the offline socket and diagnostic-report
tests require. OBS's fallback hosts file contains only IPv4; the build system
preserves the distribution file when the package is installed. The proposed
build dependencies resolve ``netcfg`` on both native architectures.

The effective-user regression matches the error code and message separately.
Both a denied change to an existing ``nobody`` account and a missing account are
valid outcomes for an unprivileged test process. Matching the whole formatted
exception previously rejected the error-code annotation in the missing-account
case. Paired controls exercise both account states; negative assertion controls
reject unrelated codes, messages, users and missing exceptions. No account,
resolver or error behavior is changed in the installed runtime.

ARM header and CPU-feature declarations
---------------------------------------

The ARM regexp header no longer constructs an ``Operand`` default argument
without its inline definition. The existing implementation call now supplies
the same zero operand explicitly, where that definition is available. Native
ARM builds compile the header independently with warnings treated as errors,
then run 4,491 checks on the real immediate, shifted-register and extended-register
operands, including copying, assignment, zero and signed integer boundaries.
The standalone checks preserve the build's ABI and hardening flags. Local
host compilation with V8's ARM target types produces identical regexp object
code before and after this change, and the operand control passes Valgrind
with no errors or retained allocations. Native ARM execution remains required.

V8's private zlib CPU-feature helper is compiled only when an ARM platform
selects its caller. A generic ARM build previously emitted an unused empty
function. Seven configuration controls produce identical object code and data
before and after the guard correction; both NEON macro spellings reproduce
the original warning and compile cleanly after correction. Runtime compiler
flags and CPU feature behavior remain unchanged.

An additional 48 preprocessing configurations cover the Android, Linux,
Fuchsia, Windows, iOS and macOS selectors, both NEON spellings, ARM32/ARM64
and disabled SIMD. All retain identical source tokens. Unavailable platform
SDK headers are placeholders in these preprocessing controls; these checks do
not claim compilation or execution against those operating-system SDKs.
