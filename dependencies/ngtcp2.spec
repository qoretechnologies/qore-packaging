# RPM adaptation (C) 2026 Qore Technologies, s.r.o.
# Derived from Fedora ngtcp2 packaging (MIT).
# Use the pinned source epoch for RPM headers and installed file timestamps.
%global source_date_epoch_from_changelog 1
%global use_source_date_epoch_as_buildtime 1
%if v"%{rpmversion}" >= v"4.20"
%global build_mtime_policy clamp_to_source_date_epoch
%else
%global clamp_mtime_to_source_date_epoch 1
%endif
%if 0%{?suse_version}
%global libname libngtcp2-16
%global develname libngtcp2-devel
%global gnutlsname libngtcp2_crypto_gnutls8
%global gnutlsdevel libngtcp2_crypto_gnutls-devel
%global osslname libngtcp2_crypto_ossl0
%global ossldevel libngtcp2_crypto_ossl-devel
%else
%global libname ngtcp2
%global develname ngtcp2-devel
%global gnutlsname ngtcp2-crypto-gnutls
%global gnutlsdevel ngtcp2-crypto-gnutls-devel
%global osslname ngtcp2-crypto-ossl
%global ossldevel ngtcp2-crypto-ossl-devel
%endif

Name:           ngtcp2
Version:        1.25.0
Release:        1.qore%{?dist}
Summary:        Implementation of RFC 9000 QUIC protocol

License:        MIT
URL:            https://github.com/ngtcp2/ngtcp2
VCS:            git:%{url}.git
Source0:        %{url}/releases/download/v%{version}/%{name}-%{version}.tar.xz
# Release does not contain all parts to build documentation
# https://github.com/ngtcp2/ngtcp2/pull/1404

BuildRequires:  autoconf
BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  libtool
BuildRequires:  libev-devel

%if 0%{?suse_version}
%description
QUIC protocol library with matching OpenSSL and GnuTLS providers.

%package -n %{libname}
Summary: Implementation of RFC 9000 QUIC protocol
%endif

%description -n %{libname}
"Call it TCP/2. One More Time."

ngtcp2 project is an effort to implement RFC9000 QUIC protocol.

%package -n %{develname}
Summary:        The ngtcp2 development files
Requires:       %{libname}%{?_isa} = %{version}-%{release}
Suggests:       ngtcp2-crypto-any-devel = %{version}-%{release}

%description -n %{develname}
"Call it TCP/2. One More Time."

ngtcp2 project is an effort to implement RFC9000 QUIC protocol.

Development headers and libraries.

%package -n %{gnutlsname}
Summary:        The ngtcp2 GnuTLS crypto provider
# The provider needs the API it was built against; SONAME-compatible
# runtime updates must remain installable independently.
Requires:       %{libname}%{?_isa} >= %{version}-%{release}

%description -n %{gnutlsname}
"Call it TCP/2. One More Time." RFC9000 QUIC protocol.

GnuTLS library provider.

%package -n %{gnutlsdevel}
Summary:        The ngtcp2 GnuTLS crypto provider headers
Requires:       %{libname}%{?_isa} = %{version}-%{release}
Requires:       %{gnutlsname}%{?_isa} = %{version}-%{release}
BuildRequires:  gnutls-devel >= 3.7.5
Requires:       gnutls-devel >= 3.7.5
Provides:       %{name}-crypto-any-devel = %{version}-%{release}

%description -n %{gnutlsdevel}
"Call it TCP/2. One More Time." RFC9000 QUIC protocol.

GnuTLS library provider headers.

%package -n %{osslname}
Summary:        The ngtcp2 dependency for OpenSSL
# The provider needs the API it was built against; SONAME-compatible
# runtime updates must remain installable independently.
Requires:       %{libname}%{?_isa} >= %{version}-%{release}

%description -n %{osslname}
"Call it TCP/2. One More Time." RFC9000 QUIC protocol.

OpenSSL library provider.

%package -n %{ossldevel}
Summary:        The ngtcp2 dependency for OpenSSL headers
Requires:       %{develname}%{?_isa} = %{version}-%{release}
Requires:       %{osslname}%{?_isa} = %{version}-%{release}
BuildRequires:  pkgconfig(openssl) >= 3.5.0
Requires:       pkgconfig(openssl) >= 3.5.0
Provides:       %{name}-crypto-any-devel = %{version}-%{release}

%description -n %{ossldevel}
"Call it TCP/2. One More Time." RFC9000 QUIC protocol.

OpenSSL library provider headers.

%if 0%{?suse_version}
%post -n %{libname} -p /sbin/ldconfig
%postun -n %{libname} -p /sbin/ldconfig
%post -n %{gnutlsname} -p /sbin/ldconfig
%postun -n %{gnutlsname} -p /sbin/ldconfig
%post -n %{osslname} -p /sbin/ldconfig
%postun -n %{osslname} -p /sbin/ldconfig
%endif

%prep
%autosetup -p1


%build
%configure --with-gnutls --with-openssl --enable-lib-only --disable-static
%make_build



%install
%make_install
# Required on epel9
rm -f ${RPM_BUILD_ROOT}%{_libdir}/lib%{name}*.la
# Upstream uses datarootdir/doc, while SUSE's RPM docdir includes /packages.
# Install this document once, through the runtime subpackage's %%doc entry.
rm -f %{buildroot}%{_datadir}/doc/ngtcp2/README.rst

%check
%make_build check

%files -n %{libname}
%license COPYING
%doc README.rst
#doc SECURITY.md
%doc AUTHORS
%{_libdir}/libngtcp2.so.16*


%files -n %{gnutlsname}
%{_libdir}/libngtcp2_crypto_gnutls.so.8*


%files -n %{osslname}
%{_libdir}/libngtcp2_crypto_ossl.so.0*


%files -n %{develname}
%doc ChangeLog
%{_libdir}/libngtcp2.so
%{_libdir}/pkgconfig/libngtcp2.pc
%{_includedir}/%{name}/
%exclude %{_includedir}/%{name}/ngtcp2_crypto_*.h


%files -n %{gnutlsdevel}
%{_libdir}/libngtcp2_crypto_gnutls.so
%{_libdir}/pkgconfig/libngtcp2_crypto_gnutls.pc
%{_includedir}/%{name}/ngtcp2_crypto_gnutls.h


%files -n %{ossldevel}
%{_libdir}/libngtcp2_crypto_ossl.so
%{_libdir}/pkgconfig/libngtcp2_crypto_ossl.pc
%{_includedir}/%{name}/ngtcp2_crypto_ossl.h



%changelog
* Thu Oct 01 2026 David Nichols <david@qore.org> - 1.25.0-1.qore
- Build matching native QUIC and TLS provider libraries for Qore.
