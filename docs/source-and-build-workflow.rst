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
