Leap Python gRPC dependency
==========================

Copyright 2026 Qore Technologies, s.r.o.

Leap 16's Python 3.13 gRPC extension embeds gRPC 1.69.0 while Arrow Flight loads
the distribution's shared gRPC 1.60.0. Sharing Abseil between these different
cores registers incompatible flags and aborts the process. The RPM restores
upstream's private Abseil and hidden-symbol policy for the embedded core.
OpenSSL, c-ares, RE2 and zlib remain distribution shared libraries. The recipe
retains the SUSE package layout and replaces python313-grpcio at the same
upstream version with a higher release.

The Leap OBS release policy preserves the complete spec release and appends
the build counter (``<SPEC_REL>.<B_CNT>``). For example,
``160000.2.3.qore.2`` upgrades the distribution's ``160000.2.2`` and the previous
``160000.2.3.qore.1`` build. Leap's inherited ``lp160`` prefix would sort below
the distribution package. Apply ``obs/project-testing.conf`` when configuring
the testing project and carry the policy into a future stable project.

The build explicitly requires ``ca-certificates-mozilla`` because OBS omits
recommendations from the minimal build environment. The certificate-management
package alone creates no usable trust roots. This preserves pip's verified TLS
context; runtime installations retain the distribution certificate-store policy.
The offline removal/recovery control is in evidence/grpcio-ca-store-20261004.json.

The source archives, component notices and recipe inputs are SHA-256 pinned
in sources.json. SPDX wheel metadata records all linked component licenses;
the RPM and wheel both carry the notices. Prepare committed sources with::

    python3 -B tools/prepare-dependency.py --name python-grpcio \
        --ref COMMITTED_REVISION --cache cache --output work/grpcio-source

After the testing repository is published and configured, an installation and
coexistence check is::

    zypper install python313-grpcio python313-pyarrow
    python3.13 -c 'import grpc, pyarrow.flight; print(grpc.__version__)'
    python3.13 -c 'import pyarrow.flight, grpc; print(grpc.__version__)'

The backport also fixes defects found during native qualification: ownership
of never-started servers and TLS credentials, async batch cleanup on rejection
or cancellation, the idle global completion queue, failed wakeup notification,
failed poll-worker initialization, address value initialization and unsigned
Huffman masks. The thread-pool shutdown and Cython conditional-compilation
changes are identified upstream backports. Compiler options are applied to
their correct source language; dead private code and obsolete source patterns
are removed. Binary exclusions remain and reject stale egg-info entries.

Every RPM build runs 13 packaging tests and 102 upstream results (101 passes,
one upstream skip), both shared-library import orders, 300 fault-injected async
RPCs, 200 failed/recovered poll-worker initializations, five wakeup cases,
65,793 exhaustive short Huffman inputs, 4,000 random/encoded inputs, 2,256
roundtrips and 30 address mapping/negative cases. Python warnings are errors.
Installed runtime and SDK Qore integration each pass 13 suites and 1,768
assertions, including Flight interoperability. The final local extension is
byte-identical to the native Valgrind-qualified candidate; the source and
artifact identities are in evidence/grpcio-rpm-candidate14b-20261004.json.

Retained diagnostics have explicit, narrow approvals. The records
grpcio-api-deprecations-20261003.json, grpcio-context-diagnostics-20261003.json
and grpcio-remaining-diagnostics-20261004.json in evidence describe the exact
API/compiler/message sites and reproduction limits. The additional OBS GCC 13
reports were accepted after 60,000 sequence-ownership checks and 100,000 deep
clones, all with zero Valgrind errors or lost allocations; see
grpcio-gcc13-diagnostics-20261004.json. Earlier Python, Cython
and Abseil records identify bounded external allocations; the gRPC lifecycle
controls exclude additional native leaks and invalid accesses. No blanket
suppression or reduced compiler flags are used. The final compiler, Cython
and manifest scopes were accepted on 2026-10-04.

On 2026-10-05, the two exact Python 3.13 extension paths on Leap were approved
for a resolver lint exception. Leap's checker matches ``ares_gethostbyname``
as though it were the obsolete libc function. Both native RPMs import c-ares
and have no obsolete libc resolver import. ``python-grpcio-rpmlintrc`` matches
only the recorded warning, package, ABI and architecture. A single expression
uses an architecture backreference, so each native source/binary lint run uses
the approved path without an unused filter for the other architecture. Negative
tests leave other diagnostics and mismatched architecture pairs visible. Recheck the ELF imports when upgrading this source.
See ``evidence/grpcio-rpmlint-diagnostic-20261004.json``.

OBS builds are limited to Leap 16 x86_64 and aarch64. Publication remains
disabled while native OBS qualification and the repository-wide installation
checks are completed. Fedora and Enterprise Linux use their distribution
Python gRPC packages.
