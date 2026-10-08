Source preparation and durable local builds
==========================================

Copyright 2026 Qore Technologies, s.r.o.

Vendor components
-----------------

Module RPMs with external source components keep ``rpm/vendor-sources.json``
in the module repository. The manifest uses this structure::

    {
      "schema": 1,
      "components": [{
        "name": "minizip-ng",
        "version": "4.2.2",
        "archive": "minizip-ng-4.2.2.tar.xz",
        "top": "minizip-ng-4.2.2",
        "url": "https://codeload.github.com/zlib-ng/minizip-ng/tar.gz/refs/tags/4.2.2",
        "sha256": "71af7b9799856d8b03619df3949e9c1be9703f8de0795af71399ba283cb27aac",
        "licenses": ["LICENSE"],
        "excluded": ["doc", "test", ".github"]
      }]
    }

``top`` is the original archive root. ``archive`` is the resulting normalized
RPM source name. ``retained_paths`` can select a subset instead of exclusions.
Every named license must survive as a nonempty regular file. Inputs use HTTPS,
are pinned by SHA-256, and are cached under that digest. The source manifest
records the original pins and hashes of the resulting archives.

Prepare the module and its components from one committed revision::

    python3 tools/packaging.py prepare --repo ../module-zip --ref COMMIT \
      --name qore-zip-module --version 1.0.0 --spec qore-zip-module.spec \
      --vendor-manifest rpm/vendor-sources.json --cache cache \
      --output work/zip-source

Preparation ignores dirty files. Explicit packaging overlays can test candidate
vendor manifests; these bundles are marked candidates and cannot be uploaded
by the OBS tool. Corrupt downloads, missing licenses, unsafe paths and filename
collisions fail before a completed output directory is exposed.

OBS changelog metadata
----------------------

Both source preparation tools generate ``PACKAGE.changes`` from the spec's
``%changelog``. OBS reads this sidecar before running RPM to provide
``BUILD_CHANGELOG_TIMESTAMP`` to the distribution's build environment. This
lets Leap set its reproducible build timestamps during shell initialization.

Entries retain their dates, authors, releases and complete notes. For example,
``* Tue Oct 06 2026 Author <author@example.invalid> - 1.0-2`` becomes
``Tue Oct 06 00:00:00 UTC 2026 - Author <author@example.invalid> - 1.0-2``.
The date has an explicit UTC timezone; preparation never uses the current
clock. The spec and source archive remain byte for byte unchanged, and the
source manifest pins the additional file's SHA-256 alongside the other inputs.

Malformed dates, mismatched weekdays, empty entries and entries ordered from
oldest to newest fail preparation before an output bundle is published.
Dependency sidecars explicitly listed as sources must match the generated
metadata. Recipes without a changelog retain their previous behavior and do
not gain a sidecar. Existing OBS source revisions acquire the metadata when
they are prepared and uploaded again; adding it creates a new OBS revision.

Long builds
-----------

Use a persistent driver when the terminal or calling tool may be interrupted::

    python3 tools/build-local.py --background --source work/zip-source \
      --image TARGET_SDK_IMAGE --output results/zip-build --jobs 2

The launcher validates the bundle, resolves the immutable image, and starts a
new process session with file-backed output and no terminal input. The returned
PID confirms launch only. ``results/zip-build/build.json`` records completion
in ``exit_code`` and the artifact hashes; a missing exit code is unfinished,
never a successful build. ``build.log`` contains RPM output, and the adjacent
``zip-build-driver.log`` captures driver errors. Reusing a build output or its
driver log is rejected to prevent competing builds from overwriting evidence.
Foreground operation remains available for CI and short commands.

Signed native installed-package checks
-------------------------------------

See `repository-installation.rst <repository-installation.rst>`_ for qualified
package-name installation commands, openSUSE vendor selection and the distinction
between local signed repository checks and production publication.

``RPM_NATIVE_QUALIFICATION=core21-solver`` explicitly selects the three native ARM
repository-install jobs. They use the same pinned core21 inputs as the ordinary
installed-package jobs. ``RPM_NATIVE_TARGET`` can select one distribution.
Locally, the equivalent mode is::

    python3 -B -W error tools/qualify-installed.py qualification/core21-fedora-aarch64.json \
        --repository-install --output results/native-installed

Run this only in a disposable container of the matching native architecture.
In addition to the normal fixture tools, the mode requires ``createrepo_c``,
``gpg`` and ``gpgconf``. It verifies every download and RPM signature, builds
temporary repository metadata, signs it with a disposable key, and requires
the package manager to reject tampered metadata. It then installs by package
name and checks every selected RPM's name, epoch, version, release and
architecture before running the usual runtime/SDK tests. Private signing
material is removed before installation; temporary repository configurations
are removed on success or failure. The public metadata and key remain in the
qualification output. No production signing key or repository is changed.

Add ``--core-lifecycle`` to that command to qualify removal and reinstall after
the clean runtime and SDK phases. This option requires repository mode and a
core-only manifest containing the seven pinned Qore runtime/SDK packages. The
fixture requires RPM to reject removing the library while dependents remain,
then removes all seven packages through the distribution package manager.
It checks every non-directory payload path, including dangling symlinks, and
requires every unrelated package to retain its exact epoch/version/release and
architecture. It reinstalls by package name from the verified repository,
requires the original package inventory and clean ``rpm -V`` results, and
repeats runtime, ONNX, SDK, tool and debugger tests as the unprivileged test user.
Temporary repository configuration is removed even if a lifecycle check fails.

``RPM_NATIVE_QUALIFICATION=core21-lifecycle`` explicitly selects the corresponding
three native ARM jobs; ``RPM_NATIVE_TARGET`` can select one distribution. These
jobs qualify same-version removal/reinstall. Cross-version upgrade from the
preserved core21 baseline to the new core build remains a separate gate.

``tools/qualify-installed.py`` consumes a reviewed manifest from
``qualification/``. It checks every downloaded checksum and RPM signature before
installation, tests a minimal runtime, then installs the SDK and tests compiler
consumers. Module fixtures come from the exact source revision used by OBS;
they run without checkout module paths or preloaded libraries.

For example, run the five-module ARM qualification through an explicitly
requested GitLab pipeline with ``RPM_NATIVE_QUALIFICATION=modules2``. This covers
Markdown, sysconf, magic, SQLite and Kalman on Fedora, Leap and AlmaLinux.
``RPM_NATIVE_TARGET=fedora`` optionally selects one distribution. Ordinary
packaging commits do not start these native jobs.

Each module runs its complete selected runtime suite again after SDK installation.
The SDK phase compiles and executes a consumer for each module. SQLite tests use
a private database; magic retains its image fixtures; Kalman runs all four suites.
The manifest validator rejects missing fixtures, cross-repository URLs, mutable
revisions, duplicate modules and incorrect package phases before installation.
Native results and raw logs are retained as pipeline artifacts. A passing build
or local command check alone does not qualify the native installed packages.
Fixture output uses a pipe owned by the test user, streamed into the runner's
log. Tests can save and restore stdout without permission failures or overwriting
earlier log entries; nonzero exit statuses still fail qualification.

``RPM_NATIVE_QUALIFICATION=modules3`` retains those five modules and adds
filesystem events, TAR, ZIP, ncurses and MessagePack. AOT providers are resolved
from each installed RPM's file inventory and loaded explicitly; missing or
ambiguous providers fail qualification. The archive checks use installed CLI
programs, exercise every advertised ZIP compression/encryption combination,
and check interoperability with distribution ``unzip``. The ncurses fixture
uses a virtual terminal, runs all eleven suites and verifies that its compiled
magic dependency cannot be removed. Runtime phases do not invoke the compiler.
The previously approved ProviderIndexUtil diagnostic is expected when
MessagePack changes its optional-module availability; logs retain that message.

``RPM_NATIVE_QUALIFICATION=modules4`` adds Cairo, GEOS, Git and ImageMagick.
It covers installed AOT data providers, image rendering and conversion CLIs,
geometry operations, and local and virtual Git repositories. Graphics fixtures
declare their font dependencies explicitly. Every module repeats its runtime
tests after SDK installation and compiles and executes a consumer. ZeroMQ
qualification follows separately after its sandbox error-ownership fix.

The installed-package runner also accepts ``amqp`` module entries. Pin the
AMQP runtime RPM and its XML dependency in the runtime phase: the compiled
helpers require XML even though source-module loading supports optional XML.
The runner rejects manifests that omit XML or defer it to SDK installation.
Pin all five Qore test suites, ``rpm/tests-installed-runtime`` and
``debian/tests/compiler`` from the same AMQP source commit. The offline runner
copies tests outside the checkout, clears broker settings and development
paths, and explicitly loads the installed AOT helpers. The SDK phase also
compiles and runs the message-conversion and provider-registration consumer.
These offline checks do not replace connected broker and TLS/mTLS qualification.

PDF qualification pins the PDFium runtime and development RPMs separately,
alongside eight fixture files from the module revision used to build the RPM.
Both runtime and SDK phases execute all seven PDF suites against the installed
native module and compiled ``PdfDataProvider``. The runner requires PDFium
rendering, clears the optional font-mode override, and installs the image and
font tools needed to exercise JPEG and font fixtures. Duplicate module paths
or native and provider modules from different directories are rejected.

The SDK phase additionally compiles and runs the module's Qore consumer and a
C consumer using only the installed ``pdfium-qore`` pkg-config interface.
The C consumer creates a document, extracts text, renders pixels, rejects a
malformed document, and releases every handle. It also runs under Valgrind
with invalid accesses and definite, indirect or possible losses treated as
failures. No suppression is used. All Qore suites enable debugging and run
as the unprivileged fixture user; the runtime phase excludes both the compiler
and PDFium development headers. These runner checks do not replace the final
signed RPM manifests, native ARM jobs or repository lifecycle qualification.

``RPM_NATIVE_QUALIFICATION=pdf`` selects the three native ARM PDF installation
jobs. ``RPM_NATIVE_TARGET`` optionally selects ``fedora``, ``leap`` or ``el10``.
Every RPM and fixture is hash-pinned, and RPM signatures are checked against
the pinned OBS project key. Ordinary packaging commits do not run native
installation jobs. These module checks use the qualified core revision 21
baseline; final integration with the updated core candidate remains required.

V8 qualification pins its process and UUID module dependencies and all 21
fixture files from the module revision used to build the RPM. Both runtime and
SDK phases run the command-line check and all 14 JavaScript/TypeScript suites.
The runner resolves the native V8 module and its two AOT helpers from the RPM
inventory, rejects duplicate or mismatched module paths, and clears Node and
provider environment settings before invoking the installed modules. Tests run
as the unprivileged fixture user; runtime qualification does not install a
compiler. The separately built TypeScript app catalog and source-only injected
failure hooks retain their explicit test skips.

The SDK phase also compiles and runs the module's consumer example and the
multiple-inheritance reference-lifetime control. The latter checks 1,001 object
destructions and runs under Valgrind, rejecting invalid accesses and definite,
indirect or possible losses. The known GCC 16 speculative-deletion diagnostic
is retained for review under the existing documented compiler exception; the
runner does not suppress warnings or weaken Valgrind checks. These local checks
do not replace signature verification and qualification on native ARM runners.

``RPM_NATIVE_QUALIFICATION=v8`` selects the three native ARM V8 jobs;
``RPM_NATIVE_TARGET`` optionally selects ``fedora``, ``leap`` or ``el10``.
They import the pinned OBS signing key and verify every RPM signature before
installing packages into fresh distribution containers. Leap additionally pins
the private shared Node library. Ordinary packaging commits do not start these
jobs. Source revision 1 inputs qualify runtime behavior while the example
interpreter metadata correction is being prepared; final acceptance requires
refreshing the manifests to the corrected native RPMs.


``RPM_NATIVE_QUALIFICATION=xml`` selects the three native ARM XML jobs.
The runtime and SDK phases execute all 304 module suites, mandatory Litmus
WebDAV compliance, and CLI startup/shutdown checks. The SDK also compiles and
runs the XML consumer. Manifests pin the XML, Process, UUID and Litmus RPMs
before installing the minimal runtime; the compiler is introduced only in the
SDK phase. Salesforce and separately provisioned Java peers retain their
explicit external-service gates.

XML's 1,721 fixture files are taken from the immutable OBS source archive used
for its RPM build. ``tools/installed_xml.py`` pins the archive revision and
SHA-256; ``qualification/xml-fixtures.json`` records the complete reviewed
inventory. Extraction rejects missing or additional tests, unsafe paths,
duplicates, links, special files and excessive expansion before making fixtures
available. It preserves ordinary executable bits while removing privileged
permissions. Only tests, documentation examples and the four installed-test
entry files are extracted; checkout modules and build binaries are excluded.
Changing the XML source pin requires updating and reviewing this fixture
inventory. The installed runner verifies loaded module paths and keeps loader
diagnostics visible; a successful source fallback is recorded, not suppressed.
