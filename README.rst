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

Twenty-four external modules have committed RPM packaging and pass builds and
installed-runtime suites on Fedora 44, Leap 16.0 and EL10. PostgreSQL includes
mandatory Fedora pgvector coverage. ZeroMQ includes draft sockets and CURVE.
The original twenty-one modules now have x86_64 OBS builds enabled on all three
distributions and Fedora aarch64 builds enabled, with publication disabled.

Core revision 15 passes all 400 local suites plus SDK, compiler, debugger and
minimal-runtime ONNX qualification on all three distributions. OBS x86_64 builds
also pass on all three. Native aarch64 remains a release gate: Fedora passed
399/400 suites but timed out in HttpClientHttpsProxy; twenty x86_64 stress runs (four at a time)
pass, so the native failure is still under investigation.
Leap and EL10 native results must also be qualified before publication.

The testing project's build configuration explicitly chooses CPU onnxruntime
for qore-stdlib's ELF dependencies. Fedora provides those capabilities from
several runtime, development, ROCm and Python packages; OBS otherwise refuses
to choose. Verified buildinfo selects the CPU runtime with the revision 15 SDK.

SSH, MySQL and tree-sitter now pass canonical builds and installed runtime/SDK
checks against revision 15 on all three targets. SSH includes runnable installed
documentation examples. MySQL runs all 34 cases against an isolated MariaDB,
allowing only the two approved fixture diagnostics. Final tree-sitter testing
exposed a borrowed-tree lifetime bug; its fix retains trees for nodes/cursors,
corrects copied-node source and cursor reset behavior, and adds ownership and
concurrency regressions. All 99 cases / 371 assertions pass normally and under
Valgrind on all three targets, with zero errors, losses or suppressions.

XML and SSH2 have committed recipes and source fixes. SSH2's final builds and
installed suites pass on all three targets. XML passes its final Leap build;
remaining canonical XML runtime/target checks are still running. Their earlier
qualification includes 304 XML suites, 106 Litmus cases against Qore, native
Valgrind and strict documentation. They remain outside the twenty-four count
until their final qualification evidence is recorded separately.

OpenLDAP's strict references pass on all three targets. Its Leap SASL fixture
exposed a distribution DIGEST-MD5 initialization crash. A tested plugin backport
uses a private OpenSSL context and correct cleanup; all 86 LDAP cases pass with
the installed plugin. Only the ten unchanged DES/3DES build-deprecation call
sites have an explicitly approved diagnostic exception. Package qualification
and native architecture coverage are still in progress.

Combined installation exposes the designed ProviderIndexUtil source-selection
diagnostic when msgpack is added. Its qualification diagnostic exception is
explicitly approved and documented. The remaining modules, target matrix and
release gates still need qualification.

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
runs unprivileged with networking disabled, and records the command, installed
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

Dependency sources and vendoring
-------------------------------

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
