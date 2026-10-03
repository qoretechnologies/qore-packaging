PDFium dependency
=================

Copyright 2026 Qore Technologies, s.r.o.

``qore-pdfium.spec`` builds PDFium 148.0.7778 from the pinned source repack
maintained in ``module-pdf/packaging/pdfium``. The repack's
``QORE-SOURCE-MANIFEST.json`` records all 19 repository revisions and exclusions.
``sources.json`` pins the archive and every additional test/font source by hash.
The build uses distribution Clang, compiler-rt and GN built from source, with
the distribution RPM optimization and hardening flags. Builds run offline.

The exported C API uses ``libpdfium-qore148.so.0`` and the
``pdfium-qore`` pkg-config name. Implementation C++ and private FreeType symbols
are hidden; the package check rejects exported implementation symbols. A future
PDFium milestone requires an explicit ABI/package-name review. JavaScript, XFA
and Skia are disabled. Qore's PDF package requires this renderer.

Fedora and openSUSE use system FreeType 2.14.2 or newer. Enterprise Linux uses
the exact FreeType commit pinned by PDFium's DEPS because its distribution
FreeType 2.13 produces different glyph rasterization from the upstream test
fixtures. That private copy retains its license and a bundled dependency
provide. All other selected image, color, compression and Unicode libraries
come from the distribution. openSUSE explicitly selects libjpeg8-devel to match
the ABI used by its QPDF and TIFF libraries.

The standalone library uses upstream's ``pdf_use_partition_alloc=false`` option.
Its distribution allocator releases allocations when a caller repeatedly loads
and unloads the library. PDFium's default process-lifetime PartitionAlloc pools
leave registry allocations behind on unload. This choice and its allocator
hardening tradeoff were explicitly approved in
``evidence/pdfium-packaging-decisions-20261003.json``. The same record covers
full DWARF 5 debug information without optional incompatible precomputed
debugger indexes; source-level debugging remains available.

``pdfium-COPYRIGHT`` carries the complete third-party notices. The two custom
LicenseRef identifiers describe the original AGG 2.3 license and the public-domain
bigint notice; they must not be replaced with an inaccurate familiar license
identifier. The approved rpmlint rule recognizes only those two identifiers on
the exact PDFium package names. Negative tests protect other diagnostics.

The test font archives include corresponding editable sources for Garuda and
Mukti Narrow. ``pdfium-test-font-sources.json`` records all 32 fonts and their
source/license correspondence. The Garuda SFD is corresponding editable source,
not a claim that modern font tools regenerate the historical TTF byte for byte.

Prepare and build a committed source bundle::

    python3 tools/prepare-dependency.py --ref COMMIT --name qore-pdfium \
      --cache cache --output work/pdfium-source
    python3 tools/build-local.py --source work/pdfium-source \
      --image TARGET_CLANG_SDK_IMAGE --output results/pdfium-build --jobs 3

The recipe runs all 989 unit tests, all 830 embedder tests and a C API regression
covering text extraction, rendered pixels and invalid input. Distribution
portability patches compare decompressed content, reference-count changes and
font-subset relationships while retaining their original behavioral assertions.
Installed-package qualification additionally checks directory ownership,
symbol visibility, debugger source/variables, and Valgrind controls for ordinary
use and repeated library unload. Native architecture builds are required before
publishing an architecture; cross-platform source compatibility is not binary
compatibility.
