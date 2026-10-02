Leap DIGEST-MD5 compatibility
============================

Copyright 2026 Qore Technologies, s.r.o.

Scope and root cause
--------------------

Leap 16.0's cyrus-sasl-digestmd5 2.1.28-160000.3.1 attempts to initialize RC4
through OpenSSL 3's default context, where the cipher is unavailable. Its
client and server continue after initialization fails, causing ldapwhoami to
crash on an encrypted LDAP connection. This package replaces only that plugin
and keeps the distribution's libsasl2 ABI and other plugins.

The backport combines upstream error propagation (commit 887dbc0435056ec58ee48c4d803f110ade1e4c39)
with openSUSE Factory's private provider context. Review additionally found
unreleased fetched cipher references and unowned contexts on failed cipher
initialization. Both are corrected and covered by failure injection. Global
OpenSSL providers and the system's cryptographic configuration are unchanged.

References:

* https://github.com/cyrusimap/cyrus-sasl/commit/887dbc0435056ec58ee48c4d803f110ade1e4c39
* https://api.opensuse.org/source/openSUSE:Factory/cyrus-sasl/cyrus-sasl-make-digestmd5-work-ssl3.patch

Tests
-----

The RPM runs the actual plugin implementation with nine allocation/provider/
initialization failures, an encrypted round trip, repeated cleanup and a check
that RC4 remains unavailable in the global OpenSSL context. Valgrind runs with
no default suppressions and rejects memory errors and definite, indirect or
possible losses. Qore's separate OpenLDAP integration fixture verifies
DIGEST-MD5, CRAM-MD5, 86 module cases and certificate-verified StartTLS.

The ten OpenSSL 3 deprecation diagnostics from unchanged DES/3DES call sites
remain visible when compiling the plugin or its test. The user approved this
narrow build-diagnostic exception on 2026-10-02; it does not permit runtime
warnings, test failures or memory errors. No deprecated cipher implementation
is rewritten or disabled as part of this compatibility fix.
