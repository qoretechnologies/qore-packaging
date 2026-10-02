Leap gRPC compiler fixture
==========================

Copyright 2026 Qore Technologies, s.r.o.

``python313-grpcio-tools`` provides the Python compiler fixture required by
Qore gRPC's interoperability suites. Version 1.68.1 generates Protobuf 5.28.1
code accepted by Leap 16's Protobuf 5.28.3 and gRPC 1.69 runtime. The newer
compiler's generated-code version requirement exceeds the distribution runtime.
Use the upstream entry point::

    python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. service.proto

The source pin comes from the PyPI sdist. The sdist contains its compiler's
Protobuf 28.1, Abseil 20240722.0 and utf8_range sources. Their original notices
and exact upstream revisions are retained in ``grpcio-tools-license-sources.json``;
the source package and installed RPM both include these notices. The recipe is
adapted from openSUSE Factory's Python package but targets only Python 3.13.

The build patch corrects four metadata/compiler declarations: the license is
an SPDX expression, the nonexistent manifest entry is removed, Cython's existing
Python 3 semantics are explicit, and C++ RTTI flags are restricted to C++ sources.
Three Protobuf definitions marked ``always_inline`` also declare ``inline`` as
GCC requires. Their bodies are unchanged. No warning filter is added.

Qualification runs seven pinned upstream compiler tests and two generated-stub
loopback tests, including malformed input, Unicode, oneof serialization and RPC
error propagation. All nine pass with Python warnings treated as errors. The
patched RPM build emits none of the ten diagnostics from the initial candidate.
A standalone C++ consumer links the installed compiler extension and invokes its
actual compiler entry point, then releases Protobuf's global caches through
``ShutdownProtobufLibrary``. Valid and malformed input pass Valgrind with zero
memory errors, lost allocations or suppressions. Exploratory whole-interpreter
logs are retained separately; the native result does not claim that CPython's
shutdown allocations disappear.

Candidate evidence is in ``evidence/grpcio-tools-candidate-20261003.json``.
Canonical source rebuild and OBS qualification remain required before publishing.
