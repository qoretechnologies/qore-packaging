JNI installed-package qualification
===================================

Copyright 2026 Qore Technologies, s.r.o.

Start a GitLab pipeline with ``RPM_NATIVE_QUALIFICATION=jni``. Optionally set
``RPM_NATIVE_TARGET`` to ``fedora``, ``leap`` or ``el10``. Each selected target
runs two native ARM jobs using the same pinned manifest:

* ``rpm-jni-<target>-sdk-arm64`` installs the SDK and builds first-party Java
  and Kotlin fixtures. It runs the bridge and provider suites, headless class
  import, Java compiler tools and a compiled Qore consumer.
* ``rpm-jni-<target>-runtime-arm64`` starts in a fresh distribution container
  and imports that SDK job's fixture bundle. It runs provider and native safety
  suites, headless import and the compiled consumer without installing Qore
  development packages, Java development packages or compiler tools.

The reviewed inventory in ``jni-fixtures.json`` pins test inputs to the JNI
module's Git revision. XML, Python and process module RPMs are pinned alongside
JNI, so cross-module imports exercise installed packages. The SDK's complete
test inventory includes embedded Python interoperability. JMS requires its
separate external-broker qualification and is not part of this local fixture.
Both phases retain the core runtime/ONNX checks; the SDK also exercises the
core development, utility and debugger checks.

Only three first-party fixture JARs and ``jni-smoke`` cross the job boundary.
``bundle.json`` binds their SHA-256 digests to the complete qualification
manifest, including architecture, source revisions and RPM digests. The runner
rejects missing, modified, symlinked or mismatched fixtures before installing
runtime packages. It never imports arbitrary files listed by an artifact.
Provider dependency JARs come from the installed RPMs.
Each JNI phase uses its private writable fixture directory as its home and
font-cache location; no host or root-user cache enters the test environment.

For local reproduction, use two fresh native distribution containers with
the same manifest and a shared artifact directory. Never run this installer
directly on a workstation. With the repository mounted at ``/code`` and an
empty writable results directory mounted at ``/results``, the SDK command is::

    python3 -B -W error /code/tools/qualify-installed.py \
      /code/qualification/jni-fedora-aarch64.json \
      --output /results/sdk --jni-phase sdk \
      --jni-fixtures /results/jni-fixtures

After that command succeeds, the fresh runtime container runs::

    python3 -B -W error /code/tools/qualify-installed.py \
      /code/qualification/jni-fedora-aarch64.json \
      --output /results/runtime --jni-phase runtime \
      --jni-fixtures /results/jni-fixtures

The architecture must match the manifest. Package signatures, package payloads
and dependency resolution are verified by the common runner. Logs, inventories
and fixture provenance are retained as CI artifacts. These installation checks
do not replace native RPM build checks or repository lifecycle qualification.

Pipeline 59874 passes all six native ARM jobs on Fedora, Leap and AlmaLinux.
Each distribution reports 37 SDK suites (632 cases, 8,662 assertions) and
23 runtime suites (478 cases, 4,336 assertions). The reports preserve existing
external-service skips; these totals do not imply live database, JMS or hardware
qualification. Each fresh runtime executes the verified SDK-built consumer
without compiler or development packages. Core runtime/ONNX and SDK checks pass.

Only the already approved XML-triggered AOT source-fallback messages and
OpenJDK 21 SunLayoutEngine diagnostics remain. There are no font-cache errors.
Exact manifests, signatures, artifact hashes, inventories and all logs are
recorded in ``evidence/jni-native-results-20261007.json``. The final core22
combined installation, outstanding package-lint review, external-service tests
and repository lifecycle remain separate delivery gates.
