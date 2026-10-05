Qore RPM packaging
==================

Copyright 2026 Qore Technologies, s.r.o.

This repository prepares pinned sources and coordinates RPM qualification for
Qore and its external modules. The canonical specs belong to the individual
source repositories; Qore uses ``qore.spec-multi``. The Fedora and openSUSE
spec names in Qore are compatibility symlinks to that file.

Current status
--------------

The rollout is in pilot qualification. No target is yet qualified for a
stable release. ``evidence/`` records the checks actually completed; local
full logs, containers and RPMs are retained under ignored ``results/`` and
``work/`` directories. Do not interpret a successfully prepared SRPM as a
successful binary build.

Thirty-four external modules have committed RPM packaging and pass builds and
installed-runtime suites on Fedora 44, Leap 16.0 and EL10. PostgreSQL includes
mandatory Fedora pgvector coverage. ZeroMQ includes draft sockets and CURVE.
The original twenty-one modules now have x86_64 OBS builds enabled on all three
distributions and Fedora aarch64 builds enabled, with publication disabled.

Core revision 16 passes all 400 local suites plus SDK, compiler, debugger and
minimal-runtime ONNX qualification on all three distributions. Native OBS builds
pass all 400 suites on all six x86_64/aarch64 targets. The earlier Fedora ARM
HttpClientHttpsProxy timeout did not recur; its diagnostic evidence is retained.
Native ARM installed-package checks remain required before publication. Evidence
is recorded in ``evidence/core16-native-installed-20261002.json``. Revision 17
passes all 400 local suites and installed checks on all three targets with the
binary-module metadata ownership fix. A recurring native ARM proxy fixture
shutdown hang was reproduced locally and root-caused: readiness can disappear
before a blocking accept, while shutdown previously joined the thread before
closing the listener. The fix closes the listener first and passes all four
fixture consumers plus 40 optimized single-CPU stress runs. Revision 18 passes
all three x86_64 OBS builds, but all native ARM targets exposed a second race:
an accept submitted between cancellation and descriptor close never receives
kernel readiness. Revision 19 explicitly wakes these late operations, releases
context resources on I/O-thread resizing, and retains descriptor-owning HTTP
notification objects until their completion actions finish. It also includes
the independently committed resident-memory accounting fix. Debug and optimized
builds pass 866 native assertions, twelve functional suites, 900 shutdown cycles
at one/two/four I/O threads, and seven Valgrind suites with zero memory/descriptor
errors or lost allocations. The user-approved GCC/Valgrind debug-symbol warning
is reproduced by a standalone C++ control. The native CI pipeline passes all
21 jobs. Revision 19 now passes all 400 local suites and installed SDK, compiler,
debugger and minimal-runtime ONNX checks on all three distributions. Revision 19
also passes all six native OBS builds and installed-package qualification on
Fedora, Leap and AlmaLinux ARM runners. Those checks include minimal-runtime
ONNX inference, SDK consumers, tools, remote debuggers and RPM file verification;
see ``evidence/core19-local-installed-20261002.json``,
``evidence/core19-native-arm-installed-20261002.json``,
``evidence/core-close-rpm-qualification-20261002.json``,
``evidence/proxy-shutdown-fix-20261002.json`` and
``evidence/core17-local-installed-20261002.json``.

Core release 20 now passes all 400 local suites and installed runtime/SDK,
ONNX, compiler, tools and debugger checks on all three x86_64 distributions.
The canonical source is ``2a7afda675225f639a698ec289bc218560800485``; it is
recorded separately from the earlier release-20 candidate in
``evidence/core20-local-installed-20261002.json``. OBS revision 15 has matching
source checksums and passes all 400 suites on all six native targets, with
publication disabled. Native ARM installed qualification also passes on Fedora,
Leap and AlmaLinux: minimal-runtime ONNX inference, SDK consumers, tools, remote
debuggers and RPM verification. See ``evidence/core20-native-builds-20261003.json``
and ``evidence/core20-native-arm-installed-20261003.json``.

Release 21's packaging change names openSUSE's versioned LLVM 19 SDK, so adding
PDFium's LLVM 21 toolchain cannot switch Qore to a newer default SDK. All 24
target metadata/dependency tests pass and OBS resolves the required headers.
Canonical builds pass all 400 suites on each distribution; installed runtime/SDK
upgrades, ONNX, compiler, tools and debugger checks also pass. Source ``d58eec0b2``
on ``rpm/llvm19-sdk`` retains the qualified release-20 runtime sources. OBS
revision 16 has matching checksums and passes all 400 suites on all six native
OBS targets. Native ARM installed-package checks pass on Fedora, Leap and
AlmaLinux, covering minimal-runtime ONNX inference, SDK consumers, tools,
remote debuggers and RPM verification. Publication remains disabled. Existing
core build diagnostics are unchanged after normalizing source and temporary
paths. See ``evidence/llvm-sdk-dependency-20261003.json``,
``evidence/core21-local-installed-20261003.json``,
``evidence/core21-native-builds-20261003.json`` and
``evidence/core21-native-arm-installed-20261003.json``.

The process module fixes a Linux PID-inspection race exposed by Fedora ARM:
a concurrent waiter can reap a child between its existence check and reading
``/proc/PID/stat``. The fix recognizes dead tasks and revalidates disappeared
PIDs while retaining conservative handling of permissions and unavailable proc
filesystems. Canonical RPMs and installed runtime/SDK checks pass all 70 cases
and 468 assertions on each distribution. Thirteen deterministic Valgrind cases
are clean; three affected existing cases retain only approved external
diagnostics. Normal native CI passes. OBS revision 2 has verified sources and
publication disabled. All six native OBS targets pass the same 70
cases and 468 assertions. Native ARM installed runtime/SDK checks now pass on
all three distributions, including compiler smoke tests and PID regressions. See
``evidence/process-state-qualification-20261003.json`` and its complete audit.

UUID release 3 uses committed source ``c910cec``. Canonical builds, seven staged
uninstall regressions, all 14 UUID cases, installed runtime/SDK tests and package
lint pass on Fedora, Leap and AlmaLinux. OBS revision 3 sources and the public
archive SHA-256 are verified; all six native builds pass 14 cases and 227
assertions plus seven uninstall regressions. Native ARM installed runtime/SDK
and compiler checks also pass on all three distributions in pipeline 59373. See
``evidence/uuid-rpm-maintenance-20261005.json`` and
``evidence/modules1-native-arm-installed-final-20261005.json``. Signed repository
installation remains a separate gate; the current pinned-artifact installer
records signing-key and LLVM manual-page setup notices separately from tests.

Fedora ARM XML passes 3,758 cases and 171,685 assertions. Fedora ARM Python
passes 30 cases and 270 assertions, and JNI passes 632 cases and 8,662 assertions;
these bridge installed-package checks remain pending. Leap and AlmaLinux ARM
XML builds are enabled with verified dependency/source inputs. Leap gRPC
revision 3 passes both native architectures, including source/runtime RPM lint
with zero errors or warnings. It combines the two approved resolver paths in
one architecture-correlated expression.
Publication remains disabled for every package.

JNI native fixes and the latest Excel/ODS changes are committed. Release/Debug
reference, exception and cleanup suites pass; strict documentation and the new
checked-JNI headless regression pass. The latter corrects a static Java method
that was incorrectly called through the instance JNI API during spreadsheet
compilation. Source and AOT spreadsheet suites pass 782 assertions. Valgrind
has no unclassified contexts or native losses; only the previously approved
JVM/glibc and CPython origins remain. Evidence is in
``evidence/jni-native-final-qualification-20261002.json`` and
``evidence/jni-headless-merge-20261002.json``. JNI canonical builds and installed
runtime/SDK/artifact checks pass on all three targets from ``33367ce``. Every build
and SDK run passes 37 suites (632 cases, 8,662 assertions); the minimal runtime
passes 23 suites (478 cases, 4,336 assertions). All 22 AOT providers, debug symbols
and sources, 195 JAR copies and 176 provenance records are verified. The OpenJDK 21 font-layout
exception was accepted on 2026-10-03, with standalone Java controls retained in
``evidence/jni-awt-diagnostic-20261003.json``. Final results are recorded in
``evidence/jni-rpm-final-20261003.json``. Installed tests use an isolated bridge
without external routing, supplying the hardware address required by Netty; the
earlier loopback-only fixture warning is fixed. JNI is included in the local
qualified-module count; OBS and native ARM checks remain separate.

The testing project's build configuration explicitly chooses CPU onnxruntime
for qore-stdlib's ELF dependencies. Fedora provides those capabilities from
several runtime, development, ROCm and Python packages; OBS otherwise refuses
to choose. Verified buildinfo selects the CPU runtime with the revision 15 SDK.
The project also maps ``/usr/bin/qore`` and the GEOS documentation index
``/usr/share/qore/tags/geos.tag`` to their owning packages and selects the
qualified libgit2 development provider for each target. OBS omits repository
file lists from dependency solving; these mappings follow its documented
``FileProvides`` and ``Prefer`` configuration rules:
https://openbuildservice.org/help/manuals/obs-user-guide/cha-obs-prjconfig.

PROJ release 4 uses the literal GEOS documentation-index path in its spec.
OBS does not expand ``%{_datadir}`` in this file dependency. All three local
canonical builds and installed runtime/SDK checks pass; OBS revision 6 has
verified matching sources. Installed Python interoperation now passes in both
import orders in runtime and SDK images on all three targets; the full PROJ and
GEOS suites and compiler smoke test pass in the same combined installations.

SSH, MySQL and tree-sitter now pass canonical builds and installed runtime/SDK
checks against revision 15 on all three targets. SSH includes runnable installed
documentation examples. Its confinement regression now owns both its allowed
directory and the outside-root file, so it also works in OBS build roots that
lack ``/etc/hostname``. MySQL runs all 34 cases against an isolated MariaDB,
allowing only the two approved fixture diagnostics. Final tree-sitter testing
exposed a borrowed-tree lifetime bug; its fix retains trees for nodes/cursors,
corrects copied-node source and cursor reset behavior, and adds ownership and
concurrency regressions. All 99 cases / 371 assertions pass normally and under
Valgrind on all three targets, with zero errors, losses or suppressions.

SSH2 and OpenLDAP now pass canonical builds and installed-runtime checks on
all three distributions and are included in the qualified count. OpenLDAP
also passes SDK/compiler and seven installed-reference checks. Each target runs
all 86 LDAP cases / 501 assertions, SASL, CLI and verified StartTLS checks.
Its Leap fixture exposed a distribution DIGEST-MD5 initialization crash; the
committed plugin backport uses a private OpenSSL context and complete cleanup.
Both its candidate and canonical RPM checks pass Valgrind with zero errors or
lost allocations. The ten unchanged DES/3DES deprecation call sites retain
their explicitly approved build-diagnostic exception. Native OBS builds of
that dependency are enabled for Leap with publication disabled.

XML now passes canonical RPM builds and all 304 installed suites on all three
targets, including 106 Litmus cases against Qore and installed WebDAV CLI checks.
Its separate native Valgrind and strict-documentation evidence is retained.
XML and XML Security are included in the thirty-one qualified local modules.
XML Security passes canonical builds, installed runtime/SDK tests, documentation,
and 13 native cases / 65 assertions under Valgrind on all three targets. Its
parser options and errors are now isolated per document, including worker threads.

Python native qualification now covers Python 3.12, 3.13 and 3.14 on the three
targets, plus free-threaded Python 3.14. The bridge fixes interpreter ownership,
finalization, wrapper references and retained callable metadata. Each default
interpreter passes 30 cases / 270 assertions in Release and Debug/Valgrind;
standalone shutdown regressions also pass. Explicitly approved exceptions cover
CPython shutdown retention, GCC bug 125913 and an independently reproduced
40-byte glibc loader allocation. Raw Valgrind diagnostics remain recorded; no
invalid access or additional native leak is accepted. Canonical RPM builds and
installed minimal-runtime/SDK tests now pass on all three targets, including
strict documentation, the versioned CPython extension alias and compiler use.
Python is included in the qualified count and uploaded to OBS with publication
disabled. JNI/Python and native ARM qualification remain separate gates. See
``evidence/python-rpm-final-20261002.json``,
``evidence/python-native-qualification-20261002.json`` and
``evidence/python-external-diagnostics-20261002.json``.

FreeTDS packaging now passes canonical builds and installed runtime/SDK checks
on all three targets. Its offline suite covers driver capabilities, invalid
protocol and missing-username errors, and unopened-connection cleanup (four
cases, fourteen assertions). Strict documentation and compiler checks also pass.
OBS has verified the canonical sources with publication disabled. Live SQL
Server/ASE behavior and proprietary Sybase OCS remain separate integration gates.
See ``evidence/freetds-rpm-final-20261002.json``.

Markdown packaging passes canonical builds and installed runtime/SDK checks
on all three targets. Each run covers eight cases and 55 assertions, including
800 concurrent conversions; RPM checks also verify safe staged uninstall.
Strict documentation and a compiled SDK consumer pass. Native Debug/Release
and Valgrind checks pass with zero errors or lost allocations. The source
archive excludes historical tracked build files and an editor swap file, and
retains the verified Sundown/Houdini source and license notices. OBS has the
verified canonical sources with publication disabled. See
``evidence/markdown-rpm-final-20261002.json``.

JNI qualification exposed JDBC transaction, cursor-reference and batch-reuse
bugs, plus inaccurate Flyway action output types. The fixes are committed and
pass the module's Alpine and Ubuntu CI jobs. Targeted PostgreSQL, failure-injection
and source/AOT Flyway tests pass; canonical RPM and installed checks pass on all three targets. The approved
JVM/glibc diagnostics retain their raw Valgrind logs and standalone controls in
``evidence/jni-external-diagnostics-20261002.json``. The corresponding Qore PostgreSQL native-array versus
JDBC-batch correction is recorded in
``evidence/core-pgsql-bulk-protocols-20261002.json`` and is included in the
canonical release-20 core RPMs.

gRPC packaging is committed and passes canonical builds and installed runtime/SDK
checks on Fedora 44 and EL10. Each installation runs 13 suites and 1,768 assertions,
including required Python gRPC and PyArrow Flight interoperation. Compiled consumers
run without the SDK; AOT trailers, separate symbols and Qore debug sources are
verified. The distribution grpc_tools deprecation retains its approved exception.
OBS sources are verified with publication disabled. Leap now also passes the
canonical Qore module build and installed runtime/SDK/artifact checks against
candidate 14b of its repaired grpcio dependency. Each phase runs the same 13
suites and 1,768 assertions. The remaining local diagnostic scopes were accepted
on 2026-10-04. Dependency commit ``0e466c5`` is uploaded as OBS revision 1;
all 29 source payloads match the qualified candidate. Both Leap architecture
builds pass 13 packaging tests and 102 upstream results (one upstream skip).
Artifact review found that OBS's inherited release prefix prevents a normal
upgrade from Leap's package. The corrected Leap policy preserves the spec
release and appends the OBS build counter; Fedora and AlmaLinux retain their
existing policies. The tested project configuration is now applied remotely.
The four OBS GCC 13 reports were reproduced with exact sources and accepted
after 60,000 ownership checks and 100,000 deep clones passed Valgrind.
Certificate-store and resolver-lint packaging checks remain before the next
build and installed qualification. Publication remains disabled. See
``evidence/grpc-rpm-final-20261002.json`` and
``evidence/grpc-leap-installed-20261003.json``.

Leap's Python gRPC compiler fixture now passes a canonical RPM build and all
nine upstream/generated-stub tests without warnings. Installed checks pass;
the canonical compiler ELF is identical to the native Valgrind-qualified build.
OBS revision 1 has verified sources with publication disabled. PyArrow Flight
and its Compute/Acero/Dataset dependencies pass candidate qualification:
95 Arrow test groups, 17,527 Cython tests, and 6,616 PyArrow tests plus three API
regressions. The upstream/compiler diagnostic exceptions were explicitly accepted
on 2026-10-03. Canonical Arrow/PyArrow rebuilds and installed Qore interoperation now pass.
The grpcio dependency has completed local compiler and installed-package review.
Candidate 12 also fixes failed poll-worker initialization: the exact native
fault-injection binary passes 100 failures and recovery cycles without memory
or descriptor errors, and all nine installed native controls retain only
approved external allocation sites. Both installed Qore runtime/SDK suites
pass with this RPM. See ``evidence/grpcio-poll-init-20261003.json``.
Candidate 14b also passes all 13 packaging tests, 101 upstream tests (one skip)
and both installed Qore bridge suites. Its stripped native extension is
byte-identical to Valgrind-qualified candidate 13. SPDX metadata now includes
all bundled-component notices and removes the license-classifier deprecation;
source-manifest negative tests still reject stale binary files. Ten native
compiler diagnostics, two Cython diagnostics and two manifest-message forms
were explicitly accepted on 2026-10-04. The scope excludes new sites, growing
allocations and native errors. See ``dependencies/grpcio.rst``,
``evidence/grpcio-rpm-candidate14b-20261004.json`` and
``evidence/grpcio-remaining-diagnostics-20261004.json``.
Submission identity is in ``evidence/grpcio-obs-submission-20261004.json``.
See ``dependencies/arrow-flight.rst`` and
``evidence/grpcio-tools-rpm-final-20261003.json``.

The Cython update supplies OBS's missing Python dependency generator and corrects
the imported Cythonize module's executable mode. Its complete local suite passes
(17,533 reported tests across eight workers, 49 skips), as do installed compiler
positive/negative cases and ABI checks. Only the exact approved compiler-template
classification rules are applied; unrelated lint errors remain visible. See
``evidence/cython-package-classification-20261003.json``.

V8 canonical RPMs from ``664eaf58`` pass Fedora and AlmaLinux builds and
installed runtime/SDK qualification. Each target completes 14 suites (138
executed cases, 10 explicit skips, 1,153 assertions), compiler and CLI consumers,
AOT metadata, separate debug symbols/sources, and directory ownership. Eight
source-only fault-injection cases are covered by the separate source-proxy run;
two cases require the separately built HubSpot app catalogue. Seven native
Valgrind regressions retain only the approved distribution Node/V8 diagnostics.
The TypeScript experimental-API notice is explicitly accepted. See
``evidence/v8-rpm-final-20261003.json`` and
``evidence/v8-integration-20261003.json``. Leap needs the libnode dependency;
OBS revision 1 has verified source checksums and publication disabled.
Fedora and AlmaLinux x86_64 OBS builds succeeded.
Leap now also passes the canonical build and installed runtime/SDK checks,
including five native Valgrind runs with only the approved conservative-GC
diagnostic family and no unsuppressed lost allocations. The custom Node RPM
passes 192 native cases and 5,249 reported JavaScript results (including upstream
skips). Node compiler diagnostics and native ARM qualification remain open. See
``evidence/v8-leap-installed-20261003.json``.
The inspector frame-vector and uvwasi timestamp compiler diagnostics are
explicitly accepted after standalone functional and Valgrind checks; the scope
is recorded in ``evidence/node-compiler-controls-20261003.json``. Other compiler
diagnostic families remain separate release gates.
The final local Node candidate also includes the tested Ada Unicode-conversion
and SQLite length-overflow fixes. Its complete RPM check again passes all 192
native cases and 5,249 reported JavaScript results; four exact optimizer
diagnostics remain pending approval. See
``evidence/node-rpm-candidate6-20261004.json``.
Installing this final Node RPM also passes the Leap SDK consumer, all 14 V8
suites (148 reported cases, 1,153 assertions), and five Valgrind controls.
All 25 reported GC contexts match previously qualified sites; no unsuppressed
lost allocations or additional file descriptors occur. See
``evidence/v8-node6-installed-20261004.json``.

The NATS broker candidate now fixes lost shutdown events caused by closing
cluster sockets with unread TCP input. All three distributions pass twenty
race-detector repetitions of the affected cluster test and eleven socket
regressions, plus three runs of nineteen existing shutdown/TLS/buffer tests.
The consumer-election fixture also passes both storage modes on all targets.
Candidate 17 exposed further asynchronous fixture assumptions. The next
candidate observes consumer-signal, acknowledgement and account-route
completion, and checks intentional slow-leaf closure using actual TCP sockets.
Four affected/new top-level tests and six subtests pass 100 repetitions on each
distribution with Go's race detector; three batch/NAK tests and eighteen subtests
also pass twenty repetitions on each. All original state assertions remain.
Candidate 18 exposed two further route-interest assumptions and the large-page
transport limit. Route fixes pass all 480 top-level/subtest executions across
the three targets, including exact success/conflict checks for concurrent
publications. The paging failure is reproduced without the race detector:
its soft default page budget can exceed the hard transport limit once headers
are added. The fixture with explicit, separate limits passes 39 runs.
The unchanged upstream default-budget behavior and this test exception were
explicitly accepted on 2026-10-04; production defaults remain unchanged.
See ``evidence/nats-routes-paging-20261004.json``.
Candidate 18 completed all test groups on all three targets, with roughly 9,500
top-level/subtest results per target, but each RPM check failed. The complete
failure inventory is in ``evidence/nats-candidate18-review-20261004.json``.
The responder, legacy gateway and route-disconnect fixture corrections now
pass 900 repeated cases across all targets under the race detector. Memory
stream setup retains the original concurrency/timeouts and passes nine runs.
Duplicate-route count review and another complete RPM qualification remain.
See ``evidence/nats-account-gateway-20261004.json`` and
``evidence/nats-consumer-completion-20261004.json``,
``evidence/nats-shutdown-drain-20261003.json`` and
``evidence/nats-no-interest-fixture-20261003.json``.

Combined installation exposes the designed ProviderIndexUtil source-selection
diagnostic when msgpack is added. Its qualification diagnostic exception is
explicitly approved and documented. The remaining modules, target matrix and
release gates still need qualification.

The EL10 OBS path uses ``Fedora:EPEL:10.2`` alongside AlmaLinux 10.2.
The unversioned EPEL 10 path follows the leading CentOS Stream minor release;
its newer OpenLDAP server requires a library version absent from AlmaLinux.
When advancing the Enterprise Linux baseline, update this explicit minor-version
path and requalify dependency resolution together.

The target matrix is Fedora 44, AlmaLinux 10 as the Enterprise Linux baseline,
and openSUSE Leap 16.0, initially x86_64. aarch64 requires native qualification
before publication. ``targets/`` pins the base image digests. Build dependency
images additionally need an exact installed-package inventory and immutable
image ID, both captured by the local builder.

ONNX-enabled ML is required. The Qore spec enables both
``QORE_WITH_ONNXRUNTIME`` and ``QORE_REQUIRE_ONNXRUNTIME`` and checks the built
ML capabilities before its tests. Fedora's ONNX Runtime 1.22.2 is a candidate
for qualification; its availability alone does not qualify inference. EL and
Leap dependency qualification remains separate. Both backports have passed
seven CTest groups and installed SDK inference. Leap reports zero lost bytes;
EL reproduces only the documented cpuinfo startup allocation described below.
OBS has also built the Leap backport on x86_64 and aarch64. Qore integration
remains a separate gate.
No target may silently omit
ONNX to produce an apparently successful package.

PDF packaging now requires the pinned PDFium renderer and retains the private
PoDoFo library with complete notices. Canonical x86_64 builds and installed
runtime/SDK/artifact checks pass on all three distributions: 79 cases and
616 assertions per distribution. Serialization, split-error and content-view
ownership fixes have separate native regression/Valgrind evidence. See
``evidence/pdf-rpm-candidate-20261003.json`` and
``evidence/pdf-native-fixes-20261003.json``. Sources are staged in OBS with
publication disabled; native OBS and ARM module qualification remain pending.
PDFium itself has passed all 1,819 upstream tests on both AlmaLinux OBS
architectures. Fedora's previously missing OBS dependencies are now retrievable
and verified on both architectures; a single rebuild was triggered. See
``evidence/fedora-pdfium-obs-retrieval-20261003.json``. Leap's bootstrap now
selects its matching LLVM archiver/linker with the full OBS LTO flags;
all 1,819 upstream tests and installed API, debugger and Valgrind checks pass
on all three local targets. The committed rebuilds and installed checks also
pass, including source and binary lint. The exact sources are staged as OBS
revision 2 with publication disabled. Both Leap and AlmaLinux native
architectures pass all 1,819 upstream tests. Fedora's two builds still fail
before compilation because OBS cannot retrieve dependency RPMs, despite their
verified availability upstream. The single explicit rebuild reproduced that
infrastructure failure. See ``evidence/pdfium-lto-qualification-20261003.json``.
A further retrieval review verifies exact binary header IDs through OBS itself,
including batch/public CPIO and binary-version APIs. Workers still fail on the
same four inputs before compilation; no dependency bypass is applied. See
``evidence/pdfium-obs-recovery-20261003.json``.

Oracle now has canonical local RPM builds and offline runtime/SDK checks on all
three distributions, including source/AOT extensions, compiler metadata,
debug-source lookup, removal and reinstallation. All build diagnostics and
source/runtime/doc lint are clean. Oracle's signed Instant Client 23 RPMs remain
an external dependency. Only the open-source module sources are staged in OBS;
builds and publication are disabled. An existing home-project client package
does not confirm a hosting exception: OBS explicitly lists oracle-instantclient
as not approved for normal hosting. A confirmed exception or separate permitted
client route is required. Live Oracle server and native ARM qualification remain
outstanding. See ``evidence/oracle-rpm-qualification-20261003.json`` and
``evidence/oracle-debugger-configuration-20261003.json``.

Preparing and building
----------------------

The orchestration tools and RPM helpers require Python 3.11 or newer.

Run the inexpensive orchestration tests before changing a source pin::

    python3 -B -W error -m unittest discover -s tests -v
    python3 tools/packaging.py order

Check package directory ownership in the matching target SDK before uploading
to OBS. Supply the runtime, development, tools and documentation RPMs from one
build together; their dependencies must be installed in that SDK::

    python3 -B -W error tools/check-rpm-directories.py /rpms/runtime.rpm /rpms/tools.rpm

The command reports unowned parent directories per RPM and fails if any remain.
It queries the target RPM database without installing or changing packages.
Leave automatic debuginfo/debugsource RPMs to the separate debug-artifact gate,
matching openSUSE's ``50-check-filelist`` application-package scope. This check
catches missing ``%dir`` entries such as a license directory's parent; dependency
resolution, file verification and installed functionality have separate checks.

Prepare a source bundle from a committed revision::

    python3 tools/packaging.py prepare --repo ../qore --ref COMMIT \
      --name qore --version 3.0.0~gitYYYYMMDD.SERIAL \
      --spec qore.spec-multi --output work/qore-source

The source archive, rendered spec and manifest are reproducible. The manifest
contains the commit, timestamp and SHA-256 of each input. Working-tree changes
and ignored build outputs are not read. ``--packaging-overlay`` can include
spec files and ``rpm/`` from a separate directory for pre-commit testing. Such
bundles are explicitly marked ``candidate`` and must not be published.
Archive permissions use a fixed Git ``tar.umask=0022`` so a developer's local
Git configuration cannot change the source bundle or make committed package
files group-writable. Executable bits and safe symlink targets are retained.

Recipe identity and source declarations are checked in the RPM preamble.
Metadata in descriptions or generated files, such as a pkg-config ``Version``
field in ``%install``, is preserved without treating it as package metadata.

Prepare dependencies in a disposable target container, then save that
container as a build image. Builds use only its installed dependencies::

    python3 tools/build-local.py --source work/qore-source \
      --image BUILD_DEPENDENCY_IMAGE --output results/qore-build --jobs 2

The builder resolves the image to its immutable ID, verifies all source hashes,
runs unprivileged with loopback-only networking by default, and records the command, installed
RPMs, log, exit status and artifact hashes. Use a new output directory for each
build. ``--source-only`` checks SRPM preparation without requiring the target
SDK. Build images used for runtime tests must define the invoking UID/GID as a
normal account, since Qore also tests system user lookup.
Use ``--background`` for durable local builds that can outlive the launching
terminal. It returns the driver PID, immutable image and output paths; the
completed ``build.json`` records the exit status and artifact hashes.
The container runs with ``--init`` so orphaned child processes are reaped.
Running ``rpmbuild`` itself as PID 1 leaves zombies after interrupted process
groups and makes the system/backquote cleanup tests fail.

Tests that measure free disk space can use ``--tmpfs-mib 4096`` to give each
build a private 4 GiB ``/tmp``. Concurrent host builds then cannot change that
test volume's capacity. The bound is recorded in ``build.json`` and applies in
foreground and background modes. Files consume memory as they are written;
choose a limit appropriate for the test workload. Execution is enabled for
Go's temporary test binaries, with ``nosuid`` and ``nodev`` retained. The mount
disappears with the container. Unit tests cover invalid sizes and both launch
modes; the real mount and RPM check can be run with::

    python3 -B -W error tests/check_tmpfs.py --image BUILD_DEPENDENCY_IMAGE \
      --output results/tmpfs-probe --background

For tests that enumerate non-loopback interfaces, Docker builds can use
``--internal-interface``. Each build creates a private internal bridge with
IPv4/IPv6 gateway mode ``isolated``, verifies the effective configuration, and
records its immutable ID and metadata. No ports are published and no default
route or host bridge address is provided. The network is removed after success
or failure. Unsupported engines or gateway modes fail rather than enabling
external access. See Docker's gateway-mode documentation:
https://docs.docker.com/engine/network/port-publishing/#gateway-modes.

Run the real container/RPM regression separately from the unit suite::

    python3 -B -W error tests/check_internal_network.py \
      --image BUILD_DEPENDENCY_IMAGE --output results/internal-network-probe

The image needs Python 3 and the normal RPM build tools. The check exercises
non-loopback bind/connect, rejects an external destination with ``ENETUNREACH``,
verifies the resulting RPM and confirms network cleanup. NATS's wildcard
gateway and monitor-bind tests require this interface; their assertions remain
unchanged.

Dependency sources and vendoring
-------------------------------

A module's vendor manifest may describe a locally assembled component with
``generated_from`` instead of ``url``. This maps repository paths to SHA-256
pins for its generator and input manifests. Preparation verifies those files
against the selected commit (or explicit candidate overlay), requires the
generated archive in the checksum-addressed cache, and verifies its hash and
retained license files. It never downloads a missing generated component.
This supports JNI's aggregate of pinned Java/Kotlin archives while preserving
the original per-dependency URLs, sources and notices inside the component.

Leap's PDFium toolchain needs debugedit 5.1 for indexed DWARF in Clang runtime
objects. The openSUSE backport preserves the distribution helper layout and
passes 35 upstream tests, installed lint, hardlink/debug-index controls and
Valgrind with no errors or lost allocations. Both executables use PIE. See
``evidence/debugedit-leap-20261003.json``. The canonical local build passes;
OBS revision 1 source files are verified with publication disabled.

``dependencies/sources.json`` pins upstream dependency downloads. The nghttp2
backport preserves the client/server applications and their matching library;
ngtcp2 preserves matching OpenSSL and GnuTLS providers. c-ares carries both
Qore query lifecycle fixes. Its explicit RPM capability prevents an unpatched
same-version system library from satisfying Qore's requirement accidentally.

Prepare a dependency from a committed packaging revision and a verified cache::

    python3 tools/prepare-dependency.py --ref COMMIT --name ngtcp2 \
      --cache cache --output work/ngtcp2-source

Use ``--candidate`` instead of ``--ref`` to test uncommitted dependency
packaging locally. Candidate manifests cannot be uploaded by the OBS tool.
The source bundle includes all declared patches and auxiliary test sources;
the same offline builder handles Qore, modules and dependency backports.

The c-ares timeout selection test uses its existing local mock fixture.
Public-DNS ``Live`` tests are excluded from offline RPM builds and belong to
connected qualification; mock DNS, parser and fuzz tests run during the build.
The changed timeout test also runs under Valgrind.

Leap additionally needs MongoDB C 2.5.5 and Arrow/Parquet 25.0.1 SDKs. MongoDB
builds its static libraries for upstream tests but installs only shared SDKs.
Its test patch answers the driver's current reconnect-and-close behavior,
checks the returned TLS error, classifies a default-server test as live, and
registers static import checks only when those SDKs install. Local unit and
mock tests remain enabled. Arrow uses system dependencies plus its pinned
xsimd 14.2.0 archive and the exact upstream test-data submodules. Its upstream
GH-50542 patch preserves a portable baseline with runtime CPU dispatch.

EL and Leap use ONNX Runtime 1.22.2 with pinned, hash-verified offline component
archives. CPU inference and the upstream unit suite stay enabled. The test
conversion patch backports upstream 15c255499f65 for GCC's packet-bounds
diagnostic on small buffers; it changes test utilities only. The separate
Softsign patch carries reviewed upstream PR 32222 (not yet merged), correcting
reciprocal underflow on EL10's x86-64-v3 baseline. Its existing extreme-value
regression stays enabled. Upstream f7619dc9 supplies the explicit integer-type
include needed by GCC 15. Backport build and memory-check results are recorded
separately from Qore ML qualification.

The user approved a documented exception on 2026-10-01 for bundled cpuinfo's
512-byte process-startup allocation in the EL LTO build. A zero-test baseline
has the same allocation; all 32 affected tests pass with no additional memory
errors. Upstream reverted its cleanup because it broke thread safety
(https://github.com/pytorch/cpuinfo/pull/411). This exception does not waive
Qore's ONNX inference checks or suppress other memory errors.

Recipes clamp file timestamps and RPM build headers to ``SOURCE_DATE_EPOCH``.
RPM 4.20 and newer use ``build_mtime_policy``; older RPM uses the corresponding
legacy clamp macro. The real RPM integration test checks both header and file
timestamps on each target.

Vendor components must retain their license texts and use verified source
archives. The ZIP pilot uses the pin and exclusions recorded in its Debian
vendor manifest; it never populates minizip-ng from a developer checkout.
Each RPM vendor manifest lists the exact archive root, SHA-256, output name,
retained license files, and optional exclusions. Read it from the same committed
revision as the module and use a checksum-addressed download cache::

    python3 tools/packaging.py prepare --repo ../module-zip --ref COMMIT \
      --name qore-zip-module --version 1.0.0 --spec qore-zip-module.spec \
      --vendor-manifest rpm/vendor-sources.json --cache cache \
      --output work/zip-source

All vendor inputs are checked before the completed source bundle is exposed.
Missing licenses, corrupt downloads, unsafe paths, and filename collisions
fail preparation. The manifest records both original and repacked hashes.
Every declared Source and Patch must be present; preparation, local builds and
OBS uploads all enforce completeness before exposing output or making changes.
See ``design/source-bundles.rst`` for the supported recipe syntax.

Oracle client redistribution and the PDFium, JNI, XML, tree-sitter and ZMQ
source components each require their own reviewed source manifest.

Qualification and publication
-----------------------------

Qore and its modules are being qualified with source preparation, binary builds,
installed runtime and SDK use, module dependencies, AOT metadata after RPM
stripping, separate debug symbols, and module feature/CLI interoperability.
Qore's installed runtime test performs actual ONNX inference and session-pool
inference; its SDK test compiles both C++ embedding and standalone/module AOT
programs outside the source checkout.

Before promoting a target, also check clean installation and removal, upgrades
from previous packages, dependency closure, reproducibility, RPM policy/lint,
and signed repository metadata. Qore's existing ABI release qualification is
a separate prerequisite for stable promotion. Preserve normal debug package
generation; the Qore helper wraps the distro post-install pipeline and restores
the QAMD/QPCM/QAOM trailers that strip/objcopy discard.

``obs/project-testing.xml`` and ``obs/project-stable.xml`` target subprojects
under ``home:davidnichols``. They start with builds and publication disabled;
enable only prepared package/target combinations after their prerequisites are
available. This leaves the existing home project's older repositories intact.
Both subprojects were created on 2026-10-01. OBS returned HTTP 500 after each
creation, but authenticated metadata reads and backend result queries confirmed
all six repository/architecture combinations and the disabled flags. The write
errors are recorded in the qualification evidence; do not blindly repeat a
failed remote mutation without checking the resulting state first.
OBS manages separate RSA-4096 signing keys for these projects. Both public
keys are stored under ``obs/keys`` and import successfully on all three target
distributions. Verify the relevant fingerprint before enabling a repository:

* testing: ``3C3E 3E9E 0EAD DE7C 47E4 9C54 9960 899F 10DF 018C``
* stable: ``C173 403E E2D8 FB52 D61A 6D77 243F A61D 0D37 0E2E``

Committed dependency sources are uploaded with verified remote checksums.
Their package metadata enables only the target repositories requiring each
backport, including native aarch64 builds; publication remains disabled.
``evidence/obs-dependency-sources-20261001.json`` records each upload and enable
operation. Module builds remain disabled until their SDK is available.

The parent home project's existing key is unchanged.

Credentials stay in the user's osc configuration/keyring. Never put passwords,
API tokens, private signing keys, or webhook trigger tokens in this repository.
Packaging-only source commits use ``[skip ci]``. Runtime or build-system fixes
that affect existing CI are separate commits and run normal CI. Do not force
push when synchronizing GitHub and GitLab.

This repository's GitLab job runs only the lightweight Python tooling tests
when tooling, tests or CI configuration changes. Spec-only and documentation
changes do not launch that job. Distribution package builds and installation
checks are separate qualification steps; a tooling pipeline does not replace
them.

Native installed RPM qualification
---------------------------------

The GitLab jobs ``rpm-fedora-arm64``, ``rpm-leap-arm64`` and ``rpm-el10-arm64``
run only when a pipeline is explicitly started with
``RPM_NATIVE_QUALIFICATION=core21``. Set ``RPM_NATIVE_TARGET`` to ``fedora``,
``leap`` or ``el10`` to select one target. They use native ARM runners and pinned
distribution images. Their manifests
pin each OBS binary and core test fixture by SHA-256; no OBS credentials or
published repository are needed. Package installation in these disposable
containers accepts the pinned, unpublished testing RPMs. Public release
signature and repository qualification remain separate gates.

``tools/qualify-installed.py`` verifies every artifact before installation,
checks the runner architecture, installs the minimal runtime without weak
optional dependencies, verifies RPM payloads, and runs ONNX and module tests
as an unprivileged user. It then adds the SDK and exercises CMake, pkg-config,
qcc, metadata extraction, utilities and debugger startup. Logs and package
inventories are retained as CI artifacts. Never run this installation tool
on a workstation; use a fresh disposable distribution container.

For the first external-module wave, start a pipeline with
``RPM_NATIVE_QUALIFICATION=modules1`` (and optionally ``RPM_NATIVE_TARGET``).
The ``rpm-modules-*-arm64`` jobs use the same qualified core and add SHA-256
pinned UUID and process RPMs. Fixture inventories are complete and bound to
each module's immutable Git revision. Both runtime and SDK phases run the UUID
and process functional suites with debugging enabled; the SDK also runs each
module's qcc smoke test and all 13 process PID-state fault-injection cases.
Those injected cases compile a C fixture and therefore run only after the SDK
is installed. Download verification completes before any package installation.
The runner rejects unknown suites, duplicate or missing fixtures, crossed
repository revisions, unsafe paths and missing runtime packages. The existing
core ONNX inference and SDK tests still run in these combined installations.

Release 21 native ARM evidence is recorded in
``evidence/core21-native-arm-installed-20261003.json``. Fedora 44, Leap 16 and
AlmaLinux 10 all passed the 400 OBS suites and installed runtime/SDK qualification,
including ONNX inference. Combined-module and repository release gates remain
pending; OBS testing publication remains disabled.
