Litmus WebDAV qualification dependency
=====================================

Copyright 2026 Qore Technologies, s.r.o.

Litmus 0.18 is pinned to the upstream release archive with SHA-256 verification.
It links the distribution's shared neon library. The upstream bundled neon copy
is not compiled or installed. The GPL-2.0-or-later notice uses GNU's current
GPLv2 text; its exact source and checksum are recorded in sources.json.

The RPM check runs all 106 tests from the five default suites against a private,
unprivileged Apache server on loopback, with no external networking or system
service changes. Startup is an event from Apache's log stream. Cleanup sends a
process-group signal and reaps the server on success, test failure and startup
failure. A shutdown timeout kills and reaps the process group and fails the run.
Seven fixture tests cover incomplete/failed suites, unexpected diagnostics,
readiness, startup failure/deadline and cleanup failure. No tests are skipped.
The installed package is tested through its installed executable and libexec
paths, separately from the build tree.

Approved Apache diagnostics
---------------------------

On 2026-10-01 the user explicitly approved these three external Apache 2.4.68
protocol diagnostics as exceptions to the warning-free test requirement. The
Litmus tests still pass; the harness preserves each diagnostic and rejects any
new diagnostic. This exception is limited to Litmus qualification against the
distribution Apache fixture. It does not waive Qore XML WebDAV compliance tests.

* COPY with an absolute-path Destination returns 400. Apache's
  ``dav_method_copymove`` calls ``dav_lookup_uri`` with ``must_be_absolute=1``;
  the latter rejects a missing URI scheme. RFC4918 section 10.3 also permits
  an absolute path. Source: https://github.com/apache/httpd/blob/2.4.68/modules/dav/main/mod_dav.c
  and https://github.com/apache/httpd/blob/2.4.68/modules/dav/main/util.c
* A corrupted lock token yields 400 instead of Litmus's expected 423. Apache's
  ``dav_fs_parse_locktoken`` rejects the invalid UUID before evaluating the
  lock condition. Source: https://github.com/apache/httpd/blob/2.4.68/modules/dav/fs/lock.c
* LOCK on an unmapped URL returns 200 instead of 201. Apache's
  ``dav_method_lock`` unconditionally sets ``HTTP_OK`` after successful lock
  creation. Source: https://github.com/apache/httpd/blob/2.4.68/modules/dav/main/mod_dav.c

Leap Apache 2.4.66 and EL10 Apache 2.4.63 produce the same three diagnostics from
the same code paths; all 106 tests pass on each distribution.
Its statically compiled prefork MPM and unixd module are detected with httpd -l,
while Fedora loads its shared event MPM.

The fixture resolves Apache in the standard system executable directories even
when OBS gives the unprivileged build account a PATH without /usr/sbin. Fedora's
recipe explicitly selects fedora-logos-httpd to resolve httpd's alternative logo
providers. Neither setting changes the server's protocol behavior.

These are hard-coded server behaviors, not configuration errors. The test tool,
neon client and server code are unchanged. Fixing the distribution's Apache is
outside this packaging exception; no warning is hidden or rewritten.

Run the same installed validation unprivileged in the prepared image::

    python3 -B -W error litmus-httpd-test.py /usr/bin/litmus --installed
