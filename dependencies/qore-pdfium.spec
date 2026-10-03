# Copyright 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
%global toolchain clang
%global source_date_epoch_from_changelog 1
%global use_source_date_epoch_as_buildtime 1
%if v"%{rpmversion}" >= v"4.20"
%global build_mtime_policy clamp_to_source_date_epoch
%else
%global clamp_mtime_to_source_date_epoch 1
%endif
# Keep full DWARF 5 and debugsource without optional precomputed indexes:
# distribution GDB rejects LLVM's augmentation and generates overlapping GNU
# index entries. The debugger reads the complete DWARF information directly.
# Approved and qualified in evidence/pdfium-packaging-decisions-20261003.json.
%undefine _include_gdb_index
%global _find_debuginfo_dwz_opts %{nil}
Name: qore-pdfium
Version: 148.0.7778
Release: 1.qore%{?dist}
Summary: PDFium C API for Qore PDF rendering and text extraction
License: BSD-3-Clause AND Apache-2.0 AND MIT AND LicenseRef-AGG-2.3 AND LicenseRef-Public-Domain
URL: https://pdfium.googlesource.com/pdfium/
# Reproducible repack: all 19 pinned repositories and exclusions are recorded
# in QORE-SOURCE-MANIFEST.json, with full redistribution notices in COPYRIGHT.
Source0: qore-pdfium_148.0.7778+ds.orig.tar.xz
Source1: pdfium-rpm-build.py
Source2: pdfium-COPYRIGHT
Source3: pdfium-api-test.c
Source4: pdfium-test-fonts-cd96fc55.tar.gz
Source5: pdfium-test-resources-72ea487e.tar.xz
# Corresponding editable sources for the two GPL-covered test fonts.
Source6: fonts-tlwg-0.6.3.tar.xz
Source7: MuktiNarrow-0.94.tar.bz2
Source8: pdfium-test-font-sources.json
# Exact PDFium DEPS revision, used privately on Enterprise Linux because its
# FreeType 2.13 glyph rasterization differs from the upstream image fixtures.
Source9: pdfium-freetype-99b479dc.tar.xz
Source10: pdfium-rpmlintrc
Patch0: pdfium-rpm-shared-library.patch
Patch1: pdfium-rpm-tests.patch
Patch2: pdfium-system-freetype-hinting.patch
ExclusiveArch: x86_64 aarch64
%if 0%{?suse_version}
BuildRequires: debugedit >= 5.1
BuildRequires: glibc-locale
BuildRequires: clang21
BuildRequires: llvm21
BuildRequires: lld21
BuildRequires: libclang_rt21
BuildRequires: ninja
BuildRequires: python3-Jinja2
%else
BuildRequires: libatomic
BuildRequires: glibc-langpack-da
BuildRequires: clang >= 21
BuildRequires: llvm >= 21
BuildRequires: lld >= 21
BuildRequires: compiler-rt >= 21
BuildRequires: ninja-build
BuildRequires: python3-jinja2
%endif
BuildRequires: gcc-c++
BuildRequires: python3
BuildRequires: pkgconfig
%if !0%{?rhel}
BuildRequires: pkgconfig(freetype2) >= 2.14.2
%endif
BuildRequires: pkgconfig(icu-uc)
BuildRequires: pkgconfig(lcms2)
BuildRequires: pkgconfig(libopenjp2)
# Match the JPEG ABI used by openSUSE QPDF and TIFF.
%if 0%{?suse_version}
BuildRequires: libjpeg8-devel
%else
BuildRequires: pkgconfig(libjpeg)
%endif
BuildRequires: pkgconfig(libpng)
BuildRequires: pkgconfig(libtiff-4)
BuildRequires: pkgconfig(zlib)
BuildRequires: pkgconfig(libbrotlidec)
BuildRequires: pkgconfig(glib-2.0)

%description
PDFium renders PDF pages and extracts text using distribution font, image,
color, compression and Unicode libraries. Enterprise Linux uses the pinned
private FreeType renderer to match PDFium's glyph rasterization.
The distribution allocator supports repeated shared-library unloads without
retaining PDFium's process-lifetime PartitionAlloc registry.
JavaScript, XFA and Skia are disabled.
The exported C API has a milestone-specific SONAME; C++ implementation symbols
remain private to the library.

%package -n libpdfium-qore148-0
Summary: PDFium milestone 148 shared C API
%if 0%{?rhel}
License: BSD-3-Clause AND Apache-2.0 AND MIT AND LicenseRef-AGG-2.3 AND LicenseRef-Public-Domain AND FTL
Provides: bundled(freetype) = 2.14.2
%endif
%description -n libpdfium-qore148-0
Shared PDF rendering, document editing and text extraction API for Qore.

%package -n libpdfium-qore-devel
Summary: Development files for the Qore PDFium C API
Requires: libpdfium-qore148-0%{?_isa} = %{version}-%{release}
%description -n libpdfium-qore-devel
Public C headers, the shared library link and build metadata for PDFium.

%prep
%autosetup -p1 -n qore-pdfium-%{version}+ds
%{__tar} -xf %{SOURCE4} -C third_party/test_fonts
%{__tar} -xf %{SOURCE5}
mkdir -p rpm/test-font-sources
%{__tar} -xf %{SOURCE6} -C rpm/test-font-sources
%{__tar} -xf %{SOURCE7} -C rpm/test-font-sources
cp %{SOURCE8} rpm/test-font-sources/manifest.json
%if 0%{?rhel}
mkdir -p third_party/freetype/src
%{__tar} -xf %{SOURCE9} -C third_party/freetype/src
%endif
cp %{SOURCE1} rpm/build.py
cp %{SOURCE2} COPYRIGHT
cp %{SOURCE3} rpm/api-test.c

%build
export LC_ALL=C.UTF-8 TZ=UTC
export CFLAGS="%{optflags}"
export CXXFLAGS="%{optflags}"
export LDFLAGS="%{?build_ldflags}"
python3 rpm/build.py --jobs %{_smp_build_ncpus} %{?rhel:--bundled-freetype}
ninja -C out/Release -j %{_smp_build_ncpus} pdfium pdfium_unittests pdfium_embeddertests

%check
export LD_LIBRARY_PATH="$PWD/out/Release"
# No private C++ or FreeType symbols may escape through the public C ABI.
rpm/toolchain/bin/llvm-nm -D --defined-only out/Release/libpdfium-qore148.so.0 > out/Release/exported-symbols.txt
if grep -Eq '[[:space:]](_Z|FT_|ft_)' out/Release/exported-symbols.txt; then
    echo 'PDFium private implementation symbols escaped into the C ABI' >&2
    exit 1
fi
out/Release/pdfium_unittests
out/Release/pdfium_embeddertests
rpm/toolchain/bin/clang %{optflags} -UNDEBUG -DFPDF_SHARED -Ipublic rpm/api-test.c \
    -Lout/Release -l:libpdfium-qore148.so.0 %{?build_ldflags} -o out/Release/api-test
out/Release/api-test

%install
install -D -m 0755 out/Release/libpdfium-qore148.so.0 \
    %{buildroot}%{_libdir}/libpdfium-qore148.so.0
ln -s libpdfium-qore148.so.0 %{buildroot}%{_libdir}/libpdfium-qore148.so
install -d %{buildroot}%{_includedir}/pdfium-qore %{buildroot}%{_libdir}/pkgconfig
install -m 0644 public/*.h %{buildroot}%{_includedir}/pdfium-qore/
cat > %{buildroot}%{_libdir}/pkgconfig/pdfium-qore.pc <<'PKGCONFIG'
prefix=%{_prefix}
libdir=%{_libdir}
includedir=%{_includedir}/pdfium-qore

Name: PDFium for Qore
Description: PDFium milestone 148 C API
Version: %{version}
Libs: -L${libdir} -lpdfium-qore148
Cflags: -I${includedir} -DFPDF_SHARED
PKGCONFIG

%post -n libpdfium-qore148-0 -p /sbin/ldconfig
%postun -n libpdfium-qore148-0 -p /sbin/ldconfig

%files -n libpdfium-qore148-0
%license LICENSE COPYRIGHT
%if 0%{?rhel}
%license third_party/freetype/FTL.TXT
%endif
%doc QORE-SOURCE-MANIFEST.json
%{_libdir}/libpdfium-qore148.so.0

%files -n libpdfium-qore-devel
%license LICENSE COPYRIGHT
%{_includedir}/pdfium-qore/
%{_libdir}/libpdfium-qore148.so
%{_libdir}/pkgconfig/pdfium-qore.pc

%changelog
* Sat Oct 03 2026 David Nichols <david@qore.org> - 148.0.7778-1.qore
- Package the pinned PDFium source with a private C ABI and system libraries.
- Use distribution Clang and compiler-rt paths with normal RPM build flags.
- Run upstream unit/embedder tests and the installed C API regression.
