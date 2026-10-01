# RPM adaptation (C) 2026 Qore Technologies, s.r.o.
# Derived from Fedora nghttp2 packaging (MIT).
# Use the pinned source epoch for RPM headers and installed file timestamps.
%global source_date_epoch_from_changelog 1
%global use_source_date_epoch_as_buildtime 1
%if v"%{rpmversion}" >= v"4.20"
%global build_mtime_policy clamp_to_source_date_epoch
%else
%global clamp_mtime_to_source_date_epoch 1
%endif
%if 0%{?suse_version}
%global libname libnghttp2-14
%else
%global libname libnghttp2
%endif

Summary: Experimental HTTP/2 client, server and proxy
Name: nghttp2
Version: 1.70.0
Release: 1.qore%{?dist}

# Parts of ruby bindings are additionally under GPL-2.0-or-later, MIT and
# HPND-Kevlin-Henney but they are NOT shipped.
License: MIT

URL: https://nghttp2.org/
Source0: https://github.com/tatsuhiro-t/nghttp2/releases/download/v%{version}/nghttp2-%{version}.tar.gz
Patch0: nghttp2-build-fixes.patch
Source1: nghttp2-daemon-check.py


BuildRequires: c-ares-devel
BuildRequires: gcc-c++
BuildRequires: libev-devel
BuildRequires: libxml2-devel
BuildRequires: make
BuildRequires: openssl-devel
BuildRequires: python3-devel
BuildRequires: valgrind
BuildRequires: systemd-rpm-macros
BuildRequires: systemd-devel
BuildRequires: zlib-devel


Requires: %{libname}%{?_isa} = %{version}-%{release}
%{?systemd_requires}

BuildRequires: pkgconfig(libnghttp3) >= 1.18.0
BuildRequires: pkgconfig(libngtcp2_crypto_ossl) >= 1.25.0


%description
This package contains the HTTP/2 client, server and proxy programs.


%package -n %{libname}
Summary: A library implementing the HTTP/2 protocol

%description -n %{libname}
libnghttp2 is a library implementing the Hypertext Transfer Protocol
version 2 (HTTP/2) protocol in C.


%package -n libnghttp2-devel
Summary: Files needed for building applications with libnghttp2
Requires: %{libname}%{?_isa} = %{version}-%{release}
Requires: pkgconfig

%description -n libnghttp2-devel
The libnghttp2-devel package includes libraries and header files needed
for building applications with libnghttp2.


%if 0%{?suse_version}
%post -n %{libname} -p /sbin/ldconfig
%postun -n %{libname} -p /sbin/ldconfig
%endif

%prep
%autosetup -p1

%build
%if 0%{?suse_version}
# Link installed command-line programs as position-independent executables.
export CFLAGS="%{optflags} -fPIE" CXXFLAGS="%{optflags} -fPIE"
%endif
mkdir build
pushd build
%define _configure ../configure
%configure PYTHON=%{__python3}              \
    --disable-hpack-tools                   \
    --disable-static                        \
    --enable-http3                          \
    --with-libxml2

%if 0%{?suse_version}
# Only src/ builds executables; applying -pie globally would also affect the
# shared C library. Keep all configure-provided application linker flags.
sed -i '/^AM_LDFLAGS =/ s/$/ -pie/' src/Makefile
%endif

# avoid using rpath
sed -i libtool                              \
    -e 's/^runpath_var=.*/runpath_var=/'    \
    -e 's/^hardcode_libdir_flag_spec=".*"$/hardcode_libdir_flag_spec=""/'

%make_build
popd



%install
pushd build
%make_install
install -D -m0444 -p contrib/nghttpx.service \
    "$RPM_BUILD_ROOT%{_unitdir}/nghttpx.service"
popd
install -D -m0644 -p nghttpx.conf.sample \
    "$RPM_BUILD_ROOT%{_sysconfdir}/nghttpx/nghttpx.conf"

# not needed on Fedora/RHEL
rm -f "$RPM_BUILD_ROOT%{_libdir}/libnghttp2.la"

# will be installed via %%doc
rm -f "$RPM_BUILD_ROOT%{_datadir}/doc/nghttp2/README.rst"

%if 0%{?suse_version}
%pre
%service_add_pre nghttpx.service
%post
%service_add_post nghttpx.service
%preun
%service_del_preun nghttpx.service
%postun
%service_del_postun nghttpx.service
%else
%post
%systemd_post nghttpx.service
%preun
%systemd_preun nghttpx.service
%postun
%systemd_postun_with_restart nghttpx.service
%endif


%check
# test the just built library instead of the system one, without using rpath
export "LD_LIBRARY_PATH=$RPM_BUILD_ROOT%{_libdir}:$LD_LIBRARY_PATH"
pushd build
%make_build check
python3 %{SOURCE1} src/.libs/nghttpx
python3 %{SOURCE1} src/.libs/nghttpx --valgrind
popd

%files
%{_bindir}/h2load
%{_bindir}/nghttp
%{_bindir}/nghttpd
%{_bindir}/nghttpx
%{_mandir}/man1/h2load.1*
%{_mandir}/man1/nghttp.1*
%{_mandir}/man1/nghttpd.1*
%{_mandir}/man1/nghttpx.1*
%{_unitdir}/nghttpx.service
%dir %{_sysconfdir}/nghttpx
%config(noreplace) %{_sysconfdir}/nghttpx/nghttpx.conf

%files -n %{libname}
%{_libdir}/libnghttp2.so.*
%license COPYING

%files -n libnghttp2-devel
%{_includedir}/nghttp2
%{_libdir}/pkgconfig/libnghttp2.pc
%{_libdir}/libnghttp2.so
%doc README.rst




%changelog
* Thu Oct 01 2026 David Nichols <david@qore.org> - 1.70.0-1.qore
- Update native libraries and applications together for Qore.
