Fedora RPM file post-processing fixes
====================================

Copyright 2026 Qore Technologies, s.r.o.

Fedora 44's add-determinism 0.7.3 has two defects exposed by Qore's documentation
size in OBS. The parallel normalizer excludes its own temporary files only if
their names end in ``.tmp``, but creates them without that suffix. The directory
walk consequently discovers files that another worker removes. The patch makes
temporary output names match the existing exclusion rule, including check mode.
The deterministic regression keeps output open during a walk and verifies that
only the original document is counted, its bytes remain unchanged and cleanup
removes the temporary output.

The linkdupes sorter retains an open descriptor whenever two files differ in an
initial hash chunk. Thousands of distinct documents exhaust OBS's descriptor
limit, even though linkdupes raises its soft limit to the hard limit. The patch
retains the next read offset and reopens a file only for an uncached chunk. Each
read closes on success or failure; cached hashes and metadata comparisons remain
unchanged. The regression uses a hard limit of 64 descriptors, hundreds of
file pairs and lengths around hash chunk boundaries. It checks distinct groups,
complete content, hardlink identity and idempotence. Upstream tests cover error
paths and metadata comparisons. SELinux context checks stay enabled.

The fixes are local patches against upstream tag v0.7.3, commit
``af17df2c477a48d4a7268c7b9c5ab91a0a19e507``. They have not been submitted
upstream. The normal Fedora BRP programs and RPM macros are retained.

Offline dependencies
--------------------

``add-determinism-Cargo.lock`` pins every crate checksum. The vendor archive is
generated from that lock, rather than downloaded from the component's metadata
URL (which identifies the committed lock). Recreate it in a clean extraction of
the pinned upstream archive with these commands::

    cp /path/to/add-determinism-Cargo.lock Cargo.lock
    cargo vendor --locked vendor > vendor-config.toml
    tar --sort=name --mtime=@1790812800 --owner=0 --group=0 --numeric-owner \
        -cJf add-determinism-0.7.3-vendor.tar.xz vendor

Compare the archive SHA-256 with ``sources.json`` before using it. Cargo verifies
registry checksums while vendoring; all build and test commands use both
``--frozen`` and ``--offline``. The original license texts, crate metadata and
checksum manifests are retained in both binary packages. The license inventory
is in ``add-determinism-vendor-licenses.json``. Tests use the release binaries
with SELinux support and cannot download dependencies.

SELinux policy dependency
-------------------------

The SELinux-enabled linkdupes executable needs the targeted file-context
database, including in an OBS VM with no active SELinux enforcement. Both its
runtime RPM and the build recipe require selinux-policy-targeted. Without it,
libselinux cannot initialize its label lookup and correctly refuses to compare
files. The dependency preserves those checks for every consumer of the tool.
