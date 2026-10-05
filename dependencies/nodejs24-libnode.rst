Node 24 embedding library for Leap
=================================

Copyright 2026 Qore Technologies, s.r.o.

``nodejs24-libnode.spec`` builds ``libnode137`` and ``libnode-devel`` for
openSUSE Leap 16. The distribution's Node executable remains separately
managed. Qore's V8 module uses the shared library and matching headers,
including Node's TypeScript transformation support.

The source manifest pins Node 24.18.1 and the offline documentation-tool tree.
The latter follows the upstream lockfile integrity records; its license and
preparation inventory is in ``nodejs24-doc-deps.json``. System libraries supply
TLS, ICU, DNS, HTTP/2 and compression. Node retains its private SQLite feature
set and hidden symbols. Both binary packages install the upstream notices
and SQLite's exact ``blessing`` notice.

The recipe includes tested fixes for CppGC realm teardown, OpenSSL compression
entry ownership, inspector environment lifetime, Ada Unicode conversion, and
SQLite length overflow. The CppGC, inspector and Ada patches identify their
upstream origins. Visibility flags apply to the correct source language, and
type/fallthrough changes retain existing values and behavior.

Every full RPM build runs the 192 native cases and upstream JavaScript groups,
including addon and embedding tests. Candidate 6 reported 5,249 JavaScript
results with no failures; upstream skips remain recorded. Additional controls
cover 2,129 Unicode cases in each conversion mode, truncated and oversized
SQLite values, allocation failures, 100 serial inspector lifetimes and ten
concurrent lifetimes. Focused Valgrind and UBSan results, installed Qore V8
runtime/SDK tests, and exact approved external diagnostics are recorded in
``evidence/node-*.json`` and ``evidence/v8-node6-installed-20261004.json``.

Leap's resolver checker mistakes ``ares_gethostbyaddr`` for a libc resolver
call. The approved filter covers only ``libnode137`` on x86_64/aarch64 and
``/usr/lib64/libnode.so.137``. Every build independently rejects all six
obsolete libc resolver imports before applying that filter. Negative tests
cover versioned symbols and unrelated lint messages. Other compiler and
memory diagnostics are accepted only at their recorded sites; normal flags
and raw logs remain enabled.

Prepare a reproducible source bundle from committed packaging::

    python3 -B tools/prepare-dependency.py --name nodejs24-libnode \
        --ref COMMITTED_REVISION --cache cache --output work/node-source

Only complete canonical RPM builds can be submitted. The metadata-only
short-circuit artifacts used during lint review are disposable and must not be
distributed. Native ARM builds, installed-package qualification, and public
generated-source download verification remain required before publication.
