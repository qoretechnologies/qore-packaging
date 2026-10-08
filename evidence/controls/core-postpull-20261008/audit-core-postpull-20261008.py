# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Refresh the complete reviews against the post-pull implementation and actual results."""
from pathlib import Path
import json
import re
import runpy

root = Path(__file__).resolve().parent.parent
repo = root.parent / 'qore'
write = runpy.run_path(str(root / 'work/write-scoped-audit.py'))['write']
assert json.loads((root / 'results/core-postpull-20261008/status.json').read_text())['exit_code'] == 0


def previous_passes(path):
    rows = re.findall(r'   \* - (\d+)\.[^\n]*\n     - (Pass|N/A)\n     - ([^\n]*)', path.read_text())
    assert len(rows) == 62
    return {int(n): evidence for n, status, evidence in rows if status == 'Pass'}


hash_path = repo / 'examples/test/qore/misc/audits/hash-lookup-native.rst'
passes = previous_passes(hash_path)
passes.update({
    53: 'The remote 9f94a962f QoreHashKeyHelper is retained. This local fix assigns false to exists on conversion and invalid-member errors; it adds no alternate lookup or suppression.',
    54: 'QoreHashKeyHelper owns converted storage; failures return before lookup. Native fixtures use ReferenceHolder, unique_ptr and TypedHashDeclHolder and check exception sinks.',
    57: 'Only a bool output assignment is added on existing error paths. Key conversion and successful lookup costs remain those of the pulled implementation.',
    62: 'On 9f94a962f, each mode passes 348 native checks, 18 Qore cases/2023 assertions across four hash suites, and clean native Valgrind. The remote encoding suite covers AST/IR/JIT/tiered/AOT. Historical negative controls reproduce the two remaining error-output defects; post-pull documentation examples also pass.'})
write(hash_path, 'Hash lookup error output audit',
    'Scope: local changes to lib/QoreHashNode.cpp, include/qore/QoreHashNode.h, CMakeLists.txt, release notes and the native regression after pulling 9f94a962f. '
    'All 62 checks reviewed: 19 Pass, 43 N/A, 0 implementation failures. '
    'Raw post-pull qualification: qore-packaging/results/core-postpull-20261008 and core-hash-docs-postpull-20261008. '
    'The previously approved GCC/Valgrind DW_AT_abstract_origin diagnostic remains visible. '
    'Commit acceptance still awaits the two exact optional ngtcp2 backend configure diagnostics in evidence/ngtcp2-backend-diagnostics-20261008.json. '
    'Full updated RPM/OBS qualification is a later gate.', passes,
    'No corresponding new module, QPP class, DataProvider, JNI, sandbox helper or runtime cancellation operation in this lookup scope.')

loader_path = repo / 'examples/test/qore/misc/module-loader/audits/separated-module-path.rst'
passes = previous_passes(loader_path)
passes[62] = ('On 9f94a962f both builds pass 25 loader cases/73 assertions and eight Valgrind runs with zero memory errors or lost allocations. '
              'Valgrind uses the separately documented regex interpreter setting; ordinary tests use default JIT. '
              'The original source reproduces the wrong module filename. Default-JIT diagnostic controls are retained separately, pending exact acceptance.')
write(loader_path, 'Separated module path audit',
    'Scope: ModuleManager.cpp normalization, separated-module-path.qtest and corresponding design/release notes, reviewed after pulling 9f94a962f. '
    'All 62 checks reviewed: 16 Pass, 46 N/A, 0 implementation failures. '
    'Raw qualification: qore-packaging/results/core-postpull-20261008; prior integration and negative evidence remains in evidence/core-separated-path-fix-20261008.json. '
    'Commit acceptance still awaits evidence/core-separated-pcre-diagnostic-20261008.json and evidence/ngtcp2-backend-diagnostics-20261008.json. '
    'No production regex setting or warning filter changes.', passes,
    'No corresponding new installed module, QPP class, DataProvider, JNI, C++ loop/blocking operation or public API change in this loader scope.')
print('Refreshed both complete 62-check reviews against 9f94a962f')
