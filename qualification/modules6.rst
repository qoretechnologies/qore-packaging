ZeroMQ and XML Security installed qualification
==============================================

Copyright 2026 Qore Technologies, s.r.o.

The installed runner supports ZeroMQ's complete five-suite test inventory in
both runtime and SDK phases. Its feature check requires draft socket APIs,
steerable proxies and CURVE key generation. A separate sandbox wrapper loads
the exact installed native module and requires empty stderr after repeatedly
catching denied operations. Missing or ambiguous installed modules fail before
the wrapper runs. The SDK phase compiles and executes a binary/string multipart
message round trip using the installed metadata.

XML Security runs its packaged-module fixture in both phases and compiles its
encryption smoke test only in the SDK phase. The manifest must also contain a
pinned XML runtime RPM. The runner preloads XML before testing, so a missing
integration dependency fails rather than silently skipping encryption tests.
Its certificate and private key are public test fixtures, isolated in a temporary
directory. The approved wrong-key parser diagnostic remains visible.

The ``modules6-*-aarch64.json`` manifests extend the qualified sixteen-module
set to eighteen suites. They pin XML Security release 3, ZeroMQ release 5 and
the XML integration dependency to the native OBS RPMs and immutable fixture
commits. Every source file is compared with its public Git revision before its
hash is recorded. ZeroMQ release 5 joins monitor shutdown as well as listener
close, with exception-path and subsequent-traffic regressions.

Select these jobs explicitly with ``RPM_NATIVE_QUALIFICATION=modules6``.
``RPM_NATIVE_TARGET`` optionally restricts the run to ``fedora``, ``leap`` or
``el10``. Ordinary packaging commits do not launch the ARM qualification jobs.
Native source builds pass on all six targets; signed installed qualification
and repository lifecycle checks remain separate publication gates.
