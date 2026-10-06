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
