Python bridge installed qualification
=====================================

Copyright 2026 Qore Technologies, s.r.o.

These manifests install the signed Python bridge and XML RPMs with the
qualified Qore runtime. All RPMs, the signing key and test fixtures have
SHA-256 pins. Fixtures come from the module's committed RPM source revision.

The runtime phase runs all 30 embedded Python cases, standalone qoreloader
conversion and callback tests, and retained-callable shutdown checks. It also
verifies that Python loads the extension belonging to the installed bridge.
The runner rejects a missing XML RPM before installation. Tests run as an
unprivileged user with ambient module, Python and loader overrides cleared.

The SDK phase repeats those checks and compiles and executes a PythonProgram
consumer using named arguments and list conversion. Runtime installation must
leave Qore headers and C/C++ compilers absent. The two optional JNI cases may
skip here; JNI/Python interoperability remains a separate qualification gate.

Select ``RPM_NATIVE_QUALIFICATION=python`` and optionally
``RPM_NATIVE_TARGET=fedora``, ``leap`` or ``el10``. Native ARM results and the
whole-repository installation, upgrade and removal checks remain publication
gates. No diagnostic filter or compiler policy is changed by this runner.
