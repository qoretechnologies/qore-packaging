SSH2 and PROJ installed qualification
====================================

Copyright 2026 Qore Technologies, s.r.o.

The installed-package runner supports SSH2 and PROJ fixtures pinned to immutable
source revisions. Every RPM and fixture has a SHA256 digest. PROJ additionally
requires a pinned GEOS runtime RPM before any installation begins.

SSH2 runs all eight suites against a private, unprivileged SSH server with
fresh host/client keys and an isolated home directory. It preloads the installed
native and four AOT modules. The SDK phase repeats those cases, then compiles
and runs the constructor/provider example from ``debian/tests/compiler``.

PROJ preloads the installed ProjGeos AOT module and runs coordinate, geometry
and optional Python interoperability suites. The Python case explicitly skips
when the external Python module is absent. The SDK phase also compiles and runs
a geographic/projected coordinate round trip. Four deliberately invalid CRS
inputs retain the three exact distribution-library messages approved on
2026-10-06; other diagnostics remain qualification failures.

The local command controls exercise both phases outside the checkout on all
three distributions. They use SDK images to validate the commands and fixtures;
clean minimal-runtime separation and signed native ARM RPM verification remain
separate CI gates. Native manifest jobs will be added once the updated OBS
artifacts have completed and their bytes have been verified.

Both packages retain full AOT DWARF, debug sources and compiler metadata while
omitting the optional LLVM name indexes, as approved on 2026-10-06. Paired
controls and all resulting debug RPMs support source lookup and breakpoints.
See ``evidence/ssh2-proj-debugger-proposal-20261006.json`` and
``evidence/proj-negative-diagnostic-20261006.json`` for exact scope and limits.
