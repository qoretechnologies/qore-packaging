Qore RPM packaging
==================

Copyright 2026 Qore Technologies, s.r.o.

This repository coordinates reproducible RPM sources, isolated local builds
and Open Build Service uploads for Qore and its external modules. Canonical
Qore/module specs belong to their individual source repositories.

The rollout is in pilot qualification. No target is qualified for release.
The inventory covers Qore and 37 external modules; the initial targets are
Fedora 44, AlmaLinux 10 and openSUSE Leap 16.0. aarch64 requires native
qualification before publication. ONNX-enabled ML is required.

Tool prerequisites are Python 3.11 or newer, Git, and Docker or Podman for
local builds. OBS operations use osc and its locally configured credentials.

Run the lightweight tooling tests and inspect dependency order::

    python3 -B -W error -m unittest discover -s tests -v
    python3 tools/packaging.py order

Prepare a source bundle from a committed revision::

    python3 tools/packaging.py prepare --repo ../qore --ref COMMIT \
      --name qore --version 3.0.0~gitYYYYMMDD.SERIAL \
      --spec qore.spec-multi --output work/qore-source

The source archive and manifest exclude working-tree changes and record input
hashes and timestamps. An explicit packaging overlay supports local candidate
builds; the OBS uploader rejects candidates and unpinned sources.

Build with an image containing the target's build dependencies::

    python3 tools/build-local.py --source work/qore-source \
      --image BUILD_DEPENDENCY_IMAGE --output results/qore-build --jobs 2

The builder verifies inputs, resolves the image to an immutable ID, runs
unprivileged with networking disabled, and records installed packages, logs,
exit status and artifact hashes. Runtime tests need a normal account matching
the invoking UID/GID in the image. Containers use an init process to reap
orphaned children. A successful SRPM is not binary-package qualification.

OBS templates under obs/ create disabled testing and stable subprojects of
home:davidnichols. Uploads accept committed source pins in testing only, and
refuse to replace unmanaged remote sources. Publication is a separate step
after package and installed-runtime qualification. Public signing keys are
under obs/keys; credentials and private keys must never enter this repository.

CI runs only the inexpensive tooling tests when their inputs change. Qore and
module packaging-only commits use [skip ci]; runtime and build-system fixes
retain normal CI. Dependency recipes and qualification evidence are added
separately after their own tests.
