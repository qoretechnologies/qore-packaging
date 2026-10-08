gRPC installed qualification
============================

Copyright 2026 Qore Technologies, s.r.o.

The native ARM jobs install checksum-pinned OBS RPMs after verifying their
signatures. Both a minimal runtime installation and an SDK installation run
the complete 13-suite gRPC, Arrow IPC, Arrow Flight and Salesforce Pub/Sub
fixture set. Fixtures are pinned to the same reviewed module source revision.
The SDK phase additionally compiles and executes the installed Arrow/provider
consumer. Core qualification includes the ONNX-enabled ML check.

All native and AOT modules are resolved from the installed RPM inventory.
Incomplete inventories, ambiguous module paths and mixed module directories
are rejected. Fixture dependencies are Python gRPC, its protocol compiler,
PyArrow Flight and the Qore process module. None requires a compiler or SDK
during runtime qualification. Private Leap dependency RPMs are pinned in its
manifest; Fedora and AlmaLinux use distribution Python packages.

The runner generates Python protocol stubs, checks imports and required
process support, and runs every suite with debugging enabled and signals
disabled. It retains each suite's full output. Python fixture deprecations
remain visible and are covered only by the existing diagnostic approval.
Salesforce integration uses its local protocol fixtures; live organization
tests retain their explicit credential-dependent skips.

Select these jobs with ``RPM_NATIVE_QUALIFICATION=grpc``.
``RPM_NATIVE_TARGET`` optionally selects ``fedora``, ``leap`` or ``el10``.
Ordinary packaging commits do not start native qualification. These jobs
verify installed functionality; repository upgrade, removal, dependency
resolution and publication remain separate gates.
