SSH and VSS installed ARM qualification
=======================================

Copyright 2026 Qore Technologies, s.r.o.

Pipeline 59562 passes on all three native ARM targets with the corrected SSH
client dependency. Each runtime and SDK phase runs 1,483 Qore cases across the
core and sixteen modules. Assertion totals are 10,522 on Fedora, 10,518 on Leap
and 10,505 on AlmaLinux. The pinned results and complete log hashes are in
``evidence/modules5-native-arm-results-20261006.json``.

Run a pipeline on the committed packaging revision with
``RPM_NATIVE_QUALIFICATION=modules5``. Optionally set ``RPM_NATIVE_TARGET`` to
``fedora``, ``leap`` or ``el10``. The three ``modules5-*-aarch64.json`` manifests
extend the fourteen-module graphics/Git batch with SSH and VSS.

Each job verifies the pinned OBS signing key, RPM signatures, package hashes and
fixture hashes before testing. Fixtures come from immutable source commits;
manifest entries cannot supply arbitrary commands. Both modules run as an
unprivileged user in the minimal runtime phase and again after SDK installation.

SSH exercises fourteen installed-module suites and six examples using local
SSH/SFTP services and public fixture keys. The runtime fixture installs
``openssh-clients`` for the real SSH/SFTP client commands, without pulling in a
compiler or SDK. The fixture inventory also contains
``Scaffold.qtest`` because the module's runner verifies its complete source test
inventory; that source-layout check applies only to source builds and is omitted
by the runner's installed mode. All four packaged AOT modules are loaded
explicitly. The SDK phase additionally compiles and executes the key-generation
and virtual-filesystem example.

VSS exercises all seven suites with the packaged loader and DataProvider AOT
modules. Fixtures include nested specifications, overlays, custom units and
JSON/YAML telemetry. The runtime script requires both JSON and YAML support
before running tests. The SDK phase compiles and runs an example covering
loading, unit conversion, validation and DataProvider registration.

Core qualification retains the ONNX-backed ML checks in both phases. Existing
approved optional-module source-fallback diagnostics remain visible. These jobs
do not enable repository publication; repository lifecycle qualification remains
a separate requirement.
