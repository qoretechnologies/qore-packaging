# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
%global source_date_epoch_from_changelog 1
%global use_source_date_epoch_as_buildtime 1
%if v"%{rpmversion}" >= v"4.20"
%global build_mtime_policy clamp_to_source_date_epoch
%else
%global clamp_mtime_to_source_date_epoch 1
%endif
Name: cyrus-sasl-digestmd5
Version: 2.1.28
Release: 160000.3.2.qore%{?dist}
Summary: Cyrus SASL DIGEST-MD5 compatibility with private OpenSSL 3 providers
License: BSD-4-Clause
URL: https://github.com/cyrusimap/cyrus-sasl
Source0: https://github.com/cyrusimap/cyrus-sasl/releases/download/cyrus-sasl-%{version}/cyrus-sasl-%{version}.tar.gz
Source1: cyrus-sasl-digestmd5-test.c
Source2: cyrus-sasl-digestmd5.rst
Patch0: cyrus-sasl-digestmd5-openssl3.patch
Patch1: cyrus-sasl-digestmd5-build.patch
BuildRequires: gcc
BuildRequires: make
BuildRequires: pkgconfig(openssl) >= 3.0
BuildRequires: gdbm-devel
BuildRequires: valgrind
Requires: cyrus-sasl = %{version}
Provides: cyrus-sasl-digestmd5(openssl3-private-provider) = 1
Conflicts: cyrus-sasl-bdb-digestmd5

%description
A compatible DIGEST-MD5 plugin for Leap 16's system Cyrus SASL 2.1.28.
Backports upstream initialization error handling and openSUSE's OpenSSL 3
compatibility, with complete cleanup of partial cipher contexts. Providers
are loaded in a private library context; system crypto configuration is
unchanged. Only the DIGEST-MD5 plugin is installed.

%prep
%autosetup -n cyrus-sasl-%{version} -p1
cp %{SOURCE1} test-digest-cipher.c
cp %{SOURCE2} RPM-NOTES.rst
# The patch updates build-system sources and their generated release files
# together. Restore their dependency ordering after patch application.
touch aclocal.m4
touch configure config.h.in
find . -name Makefile.in -exec touch {} +

%build
%set_build_flags
export CFLAGS="$CFLAGS -fPIC"
export LDFLAGS="$LDFLAGS -Wl,-z,relro,-z,now"
mkdir build
cd build
../configure --build=%{_build} --host=%{_host} --prefix=%{_prefix} \
  --libdir=%{_libdir} --with-plugindir=%{_libdir}/sasl2 \
  --disable-static --disable-sample --with-saslauthd=no \
  --disable-gssapi --disable-krb4 --disable-otp --disable-srp \
  --disable-scram --disable-sql --disable-ldapdb --without-pam \
  --with-dblib=gdbm --without-sphinx-build
%make_build -C common
%make_build -C plugins libdigestmd5.la

%install
install -Dm755 build/plugins/.libs/libdigestmd5.so.3.0.0 \
  %{buildroot}%{_libdir}/sasl2/libdigestmd5.so.3.0.0
ln -s libdigestmd5.so.3.0.0 %{buildroot}%{_libdir}/sasl2/libdigestmd5.so.3
ln -s libdigestmd5.so.3.0.0 %{buildroot}%{_libdir}/sasl2/libdigestmd5.so

%check
%set_build_flags
# Assertions remain active regardless of the distribution's optimization flags.
%{__cc} $CPPFLAGS $CFLAGS -UNDEBUG -Ibuild -Iinclude -Ibuild/include -Icommon -Ilib \
  test-digest-cipher.c build/common/.libs/libplugin_common.a \
  $LDFLAGS -lcrypto -lresolv -o build/test-digest-cipher
valgrind --default-suppressions=no --error-exitcode=97 --leak-check=full \
  --show-leak-kinds=definite,indirect,possible \
  --errors-for-leak-kinds=definite,indirect,possible build/test-digest-cipher

%files
%license COPYING
%doc RPM-NOTES.rst
%{_libdir}/sasl2/libdigestmd5.so*

%changelog
* Fri Oct 02 2026 David Nichols <david@qore.org> - 2.1.28-160000.3.2.qore
- Backport private OpenSSL 3 provider loading and initialization error handling.
- Free fetched ciphers and partial contexts on every failure path.
- Exercise encrypted round trips, nine failure points and repeated cleanup under Valgrind.
