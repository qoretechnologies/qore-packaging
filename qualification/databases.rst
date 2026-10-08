FreeTDS and MySQL installed qualification
=========================================

Copyright 2026 Qore Technologies, s.r.o.

The installed runner verifies signed FreeTDS and MySQL RPMs before installation,
then exercises each driver in both a minimal runtime and an SDK installation.
All fixture URLs and file hashes are pinned to the qualified source commits.
FreeTDS fixtures come from module-sybase, the repository that produces the
qore-freetds-module package; other repository substitutions are rejected.

FreeTDS uses its existing four-case offline suite, covering driver capabilities,
invalid options and controlled connection failures. Its SDK phase also compiles
and executes the packaged consumer example. It does not claim live SQL Server,
ASE or proprietary Sybase OCS integration coverage.

MySQL uses its existing unprivileged MariaDB fixture over a private Unix socket.
All three suites run, including error information and native bulk loading; the
SDK phase compiles and executes the SQL consumer against the same server. Only
the previously approved MAC-address startup diagnostic and deliberate negative-
authentication log entry are accepted by that fixture. Unexpected diagnostics
remain errors. Runtime fixture dependencies include the distribution's MariaDB
server and client, with no compiler or development headers added.

Select the three native ARM jobs explicitly with
``RPM_NATIVE_QUALIFICATION=databases``. ``RPM_NATIVE_TARGET`` optionally selects
``fedora``, ``leap`` or ``el10``. Ordinary packaging commits do not start them.
The ``databases-*-aarch64.json`` manifests pin the OBS packages and core SDK,
including ONNX-enabled ML verification. Repository installation, upgrade,
removal and publication remain separate qualification gates.
