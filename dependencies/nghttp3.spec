# RPM adaptation (C) 2026 Qore Technologies, s.r.o.
# Derived from Fedora nghttp3 packaging (MIT).
# Use the pinned source epoch for RPM headers and installed file timestamps.
%global source_date_epoch_from_changelog 1
%global use_source_date_epoch_as_buildtime 1
%if v"%{rpmversion}" >= v"4.20"
%global build_mtime_policy clamp_to_source_date_epoch
%else
%global clamp_mtime_to_source_date_epoch 1
%endif
%global abi_ver 9
%if 0%{?suse_version}
%global libname libnghttp3-9
%else
%global libname libnghttp3
%endif

Name:           nghttp3
Version:        1.18.0
Release:        1.qore%{?dist}
Summary:        HTTP/3 library written in C

License:        MIT
URL:            https://github.com/ngtcp2/nghttp3
Source:         %{url}/releases/download/v%{version}/%{name}-%{version}.tar.xz

BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  make

%global _description %{expand:
nghttp3 is an implementation of RFC 9114 HTTP/3 mapping over QUIC
and RFC 9204 QPACK in C.
It does not depend on any particular QUIC transport implementation.}

%description %{_description}


%package -n %{libname}
Summary:        HTTP/3 library written in C

%description -n %{libname} %{_description}


%package -n     libnghttp3-devel
Summary:        Development files for libnghttp3
Requires:       %{libname}%{?_isa} = %{version}-%{release}

%description -n libnghttp3-devel %{_description}

The libnghttp3-devel package contains libraries and header files for
developing applications that use libnghttp3.


%if 0%{?suse_version}
%post -n %{libname} -p /sbin/ldconfig
%postun -n %{libname} -p /sbin/ldconfig
%endif

%prep
%autosetup -p1


%build
%configure --disable-static
%make_build


%install
%make_install
find %{buildroot} -name '*.la' -exec rm -f {} ';'
# will be installed via %%doc
rm -f %{buildroot}%{_datadir}/doc/nghttp3/README.rst


%check
%make_build check


%files -n %{libname}
%license COPYING
%doc README.rst
%{_libdir}/libnghttp3.so.%{abi_ver}{,.*}

%files -n libnghttp3-devel
%{_includedir}/nghttp3
%{_libdir}/libnghttp3.so
%{_libdir}/pkgconfig/libnghttp3.pc


%changelog
* Thu Oct 01 2026 David Nichols <david@qore.org> - 1.18.0-1.qore
- Build the shared HTTP/3 library for Qore with offline upstream tests.
