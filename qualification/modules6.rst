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

Signed ARM manifests and a dedicated pipeline selector will be added after
ZeroMQ's socket-close fixture correction is rebuilt. These runner changes alone
do not constitute ARM qualification or enable publication.
