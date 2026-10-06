ZeroMQ installed qualification
===============================

Copyright 2026 Qore Technologies, s.r.o.

The installed runner supports ZeroMQ's complete five-suite test inventory in
both runtime and SDK phases. Its feature check requires draft socket APIs,
steerable proxies and CURVE key generation. A separate sandbox wrapper loads
the exact installed native module and requires empty stderr after repeatedly
catching denied operations. Missing or ambiguous installed modules fail before
the wrapper runs. The SDK phase compiles and executes a binary/string multipart
message round trip using the installed metadata.

Signed ARM manifests and a dedicated pipeline selector will be added after the
final license-payload rebuild. The runner changes alone do not constitute ARM
qualification or enable publication.
