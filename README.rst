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

Thirty-one external modules have committed RPM packaging and pass builds and
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
debugger and minimal-runtime ONNX checks on all three distributions. Native
OBS completion and ARM installed-package checks remain separate gates;
see ``evidence/core19-local-installed-20261002.json``,
``evidence/core-close-rpm-qualification-20261002.json``,
``evidence/proxy-shutdown-fix-20261002.json`` and
``evidence/core17-local-installed-20261002.json``.

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

Preparing and building
----------------------

The orchestration tools and RPM helpers require Python 3.11 or newer.

Run the inexpensive orchestration tests before changing a source pin::

    python3 -B -W error -m unittest discover -s tests -v
    python3 tools/packaging.py order

Prepare a source bundle from a committed revision::

    python3 tools/packaging.py prepare --repo ../qore --ref COMMIT \
      --name qore --version 3.0.0~gitYYYYMMDD.SERIAL \
      --spec qore.spec-multi --output work/qore-source

The source archive, rendered spec and manifest are reproducible. The manifest
contains the commit, timestamp and SHA-256 of each input. Working-tree changes
and ignored build outputs are not read. ``--packaging-overlay`` can include
spec files and ``rpm/`` from a separate directory for pre-commit testing. Such
bundles are explicitly marked ``candidate`` and must not be published.

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

The GitLab jobs ``rpm-fedora-arm64`` and ``rpm-leap-arm64`` run only when a
pipeline is explicitly started with ``RPM_NATIVE_QUALIFICATION=core19``.
Set ``RPM_NATIVE_TARGET=fedora`` or ``RPM_NATIVE_TARGET=leap`` to run only
one target. They use native ARM runners and pinned distribution images. Their manifests
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
