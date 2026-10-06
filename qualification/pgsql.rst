PostgreSQL installed qualification
=================================

Copyright 2026 Qore Technologies, s.r.o.

The PostgreSQL manifests install signed native RPMs with the qualified Qore
core. The runtime phase runs all four suites against a private PostgreSQL
cluster on a Unix socket; it requires no compiler. Fedora installs pgvector
and requires extension creation before testing, so vector coverage cannot skip.

The SDK phase repeats all 32 cases, then compiles and runs a typed binding and
transaction example in another private cluster. The example matches the
established Debian compiler check. The fixture shuts down its server even when
the command fails and never modifies a system database or opens a TCP listener.

RPM inputs remain pinned to the release 2 source. Fixtures use its subsequent
compiler-test commit; that commit changes no driver or RPM payload. Every
fixture and RPM is pinned by SHA256 and an immutable source revision.

Select ``RPM_NATIVE_QUALIFICATION=pgsql`` and optionally
``RPM_NATIVE_TARGET=fedora``, ``leap`` or ``el10``. AlmaLinux's local command
controls pass; its manifest now pins the completed native dependency rebuild.
Native architecture qualification and repository lifecycle checks remain
publication gates.

OBS revision 3 adds changelog metadata generated from the unchanged release 2
spec. Its Fedora and Leap native builds pass with the build-environment epoch
warnings removed. The manifests pin the resulting signed RPMs for installed
qualification; the earlier revision 2 results remain recorded separately.

Pipeline 59632 passed the revision 3 installed runtime/SDK jobs on Fedora and
Leap ARM: 32 cases per phase, with 382 Fedora or 336 Leap assertions. Signed
RPM integrity, core SDK checks and the compiled PostgreSQL example also pass.
AlmaLinux native inputs are ready; signed installed checks remain pending.
