Leap Arrow and Python Flight fixtures
=====================================

Copyright 2026 Qore Technologies, s.r.o.

Leap 16 uses Apache Arrow 25.0.1 shared libraries for Qore DataFrame and the
Python Flight server used by the Qore gRPC integration suite. The Arrow recipe
now enables Compute, Acero, Dataset and Flight alongside IPC, CSV, JSON and
Parquet. Runtime and development files are separate packages. Dependencies
come from the distribution, except the existing pinned xsimd headers; upstream
testing libraries and private test headers are excluded from the SDK.

The Python 3.13 backport uses these system libraries. It enables NumPy,
Compute, Acero, Dataset, Flight and Parquet. Cloud storage, CUDA, Gandiva,
Substrait, ORC, HDFS and Parquet encryption bindings are disabled. Pandas is
unavailable for this interpreter in the target distribution, so optional Pandas
tests skip. Cython 3.2.9 is a build dependency, backported from the Factory
recipe with the complete upstream test suite enabled.

For example, after configuring the testing repository::

    zypper install python313-pyarrow
    python3 -c 'import pyarrow as pa, pyarrow.compute as pc; print(pc.sum(pa.array([1, None, 3])).as_py())'

Builds use the SHA-256 pins in sources.json and need no network access.
Arrow and Parquet fixture archives are fixed upstream commits. Prepare a
committed recipe with::

    python3 -B tools/prepare-dependency.py --name python-pyarrow \
        --ref COMMITTED_REVISION --cache cache --output work/pyarrow-source

Candidate qualification passes 95 Arrow CTest groups, 17,527 Cython tests,
three PyArrow API regressions and 6,616 upstream PyArrow tests. The latter has
1,646 optional skips, 13 expected failures and one upstream xfail that now
passes (test_sequence_timestamp_nanoseconds). Runtime warnings are errors.
Twelve added cases require the exact legacy ranking FutureWarning and verify
that old and current sort-key APIs produce identical results. Ordinary tests
use Arrow 25's current sort-key API, preserving their value assertions.

Four diagnostic exceptions were explicitly accepted on 2026-10-03. The three
relevant dependency records are evidence/cython-external-diagnostics-20261003.json,
evidence/arrow-external-diagnostics-20261003.json and
evidence/pyarrow-external-diagnostics-20261003.json. They retain the exact warning
inventories, source pins, root-cause review and control results. Cython's
unchanged upstream fixture defects are included in that approval; test success
does not establish that those fixtures are defect-free. Arrow's actual
warning-producing translation units and native Valgrind controls are retained.
No compiler flags or warning filters were added for these exceptions.

Canonical committed-source rebuilds, installed RPM checks, Qore gRPC
interoperation and native ARM qualification are recorded separately. Candidate
success alone does not authorize publication.
