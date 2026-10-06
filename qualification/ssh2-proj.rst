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
separate CI gates. The Fedora, Leap and AlmaLinux ARM manifests pin the completed OBS
artifacts, including GEOS, and the exact source fixtures. Set
``RPM_NATIVE_QUALIFICATION=ssh2-proj`` to run the native installed-package jobs,
or also set ``RPM_NATIVE_TARGET=fedora`` ``leap`` or ``el10`` to select one distribution.
These jobs start from clean distribution images, verify signatures and hashes,
and run runtime checks before installing development packages. AlmaLinux ARM inputs include the completed dependency rebuild; its signed
installed qualification is now ready to run.

Both packages retain full AOT DWARF, debug sources and compiler metadata while
omitting the optional LLVM name indexes, as approved on 2026-10-06. Paired
controls and all resulting debug RPMs support source lookup and breakpoints.
See ``evidence/ssh2-proj-debugger-proposal-20261006.json`` and
``evidence/proj-negative-diagnostic-20261006.json`` for exact scope and limits.

Pipeline 59662 passed both signed native ARM jobs: 96 functional cases in
each runtime and SDK phase on each distribution (384 total), plus compiled
examples and core runtime/SDK checks. Each phase explicitly skips the optional
PROJ/Python namespace case until the Python module is included in the combined
installation. All package signatures, hashes and RPM payload checks pass.
