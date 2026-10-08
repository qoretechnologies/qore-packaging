# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import collections
import gzip
import hashlib
import json
import re
import runpy
import shutil
import subprocess
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent.parent
out = root / 'evidence/controls/node-native-rev7-x86-20261008'
out.mkdir()
osc = ['osc', '--setopt', 'http_retries=1', '-A', 'https://api.opensuse.org', 'api']
base = '/build/home:davidnichols:qore:testing/openSUSE_Leap_16.0/x86_64/nodejs24-libnode'
info = subprocess.check_output([*osc, base + '/_buildinfo'])
parsed = ET.fromstring(info)
assert parsed.findtext('srcmd5') == '68633aee6138c8992573ca51eddf282f' and parsed.findtext('rev') == '7'
(out / 'buildinfo.xml').write_bytes(info)
state = (root / 'results/node-native-rev7-final-state-20261008.xml').read_bytes()
leap = [r for r in ET.fromstring(state).findall('result') if r.get('repository') == 'openSUSE_Leap_16.0']
assert {r.get('arch') for r in leap} == {'x86_64', 'aarch64'}
assert all(r.find('status').get('code') == 'succeeded' for r in leap)
(out / 'state.xml').write_bytes(state)
(out / 'binaries.xml').write_bytes(subprocess.check_output([*osc, base]))
previous = root / 'results/node-native-rev7-live2-20261008/x86_64.log'
suffix = root / 'results/node-native-rev7-live3-20261008/x86_64-suffix.log'
receipt = json.loads((suffix.parent / 'x86_64-reader-status.json').read_text())
assert receipt['reader_exit_code'] == 0 and receipt['overlap_verified'] == 256
assert previous.read_bytes()[-256:] == suffix.read_bytes()[:256]
full = previous.read_bytes() + suffix.read_bytes()[256:]
log = re.sub(r'^\[\s*\d+s\] ?', '', full.decode(), flags=re.M)
assert 'finished "build nodejs24-libnode.spec"' in log
assert '[  PASSED  ] 192 tests.' in log and 'All tests passed.' in log
assert '0 errors, 0 warnings, 15 filtered, 0 badness' in log
assert not re.search(r'^not ok ', log, re.M)
rows = re.findall(r'^ok (\d+) (.*)$', log, re.M)
assert [int(n) for n, _ in rows] == list(range(1, 5250))
old = re.sub(r'^\[\s*\d+s\] ?', '',
             (root / 'results/node-native-rev6-live-20261008/x86_64.log').read_text(), flags=re.M)
before = collections.Counter(x for x in old.splitlines() if ': warning:' in x)
after = collections.Counter(x for x in log.splitlines() if ': warning:' in x)
assert before == after and len(after) == 571 and sum(after.values()) == 4755
assert len(re.findall(r'^PASS: test/mjsunit/wasm/deopt/', log, re.M)) == 31
(out / 'compiler-warnings.json').write_text(json.dumps(after, indent=2) + '\n')
(out / 'build.log.gz').write_bytes(gzip.compress(full, mtime=0))
(out / 'reader-status.json').write_text(json.dumps(receipt, indent=2) + '\n')
shutil.copyfile(Path(__file__), out / Path(__file__).name)
audit = runpy.run_path(str(root / 'work/write-scoped-audit.py'))
audit['write'](out / 'audit.rst', 'Node revision 7 native x86_64 evidence audit',
    'Scope: record the completed source-pinned native build. All 62 checks reviewed: eight Pass, 54 N/A. '
    'No runtime/recipe changes and no diagnostic exception inferred.',
    {9: 'New recorder and evidence carry copyright 2026; raw external logs are preserved.',
     53: 'No bypass, suppression, compiler-policy change or substitute result.',
     54: 'Assertions reject incomplete/mismatched inputs before writing final evidence.',
     57: 'Join existing stream fragments once; do not rebuild or copy RPM binaries.',
     58: 'Source revision, overlap, terminal state, exact test numbering and all compiler-warning occurrence counts are verified.',
     59: 'Evidence lists skipped/TODO results and pending VM/ARM diagnostics separately from functional success.',
     61: 'Read-only OBS metadata; no credentials or signing secrets included.',
     62: '192 native tests, 5249 reported JS results, 31 Wasm scripts, unchanged 571 warning lines/4755 occurrences, and zero lint errors/warnings.'},
    'No Qore/C++/QPP/module/DataProvider/JNI implementation change in this recording scope.')
record = {'schema': 1, 'date': '2026-10-08', 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
    'status': 'Both revision 7 native builds succeed. x86_64 functional/lint checks pass with an identical compiler diagnostic inventory; the previously requested exact diagnostic approvals remain pending.',
    'project': 'home:davidnichols:qore:testing', 'package': 'nodejs24-libnode',
    'source_commit': '0997787ef8c0c8564640b9faa7bea71166ec206e', 'revision': 7,
    'srcmd5': '68633aee6138c8992573ca51eddf282f', 'arch': 'x86_64',
    'native_tests': 192, 'javascript_reported_results': len(rows),
    'upstream_skips': [v for _, v in rows if '# skip' in v.lower()],
    'upstream_todos': [v for _, v in rows if '# todo' in v.lower()],
    'wasm_deoptimization_scripts': 31,
    'lint': {'errors': 0, 'warnings': 0, 'existing_approved_filters': 15},
    'compiler_diagnostics': {'unique': len(after), 'occurrences': sum(after.values()), 'identical_to_revision6': True},
    'arm_evidence': 'evidence/node-native-rev7-arm-20261008.json',
    'pending_diagnostics': ['evidence/node-vm-notice-20261008.json', 'evidence/node-arm-pio2-diagnostic-20261008.json',
                            'evidence/node-arm-bti-diagnostic-20261008.json'],
    'limits': ['5249 upstream ok results include 81 skips and 11 TODO results; those are not counted as executed passing tests.',
               'Installed libnode/V8 module checks, repository lifecycle and publication remain separate gates.',
               'Native build success does not itself approve retained diagnostics.'],
    'files_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted(out.iterdir()) if p.is_file()}}
(root / 'evidence/node-native-rev7-x86-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print('PASS: both native Node rev7 builds; x86_64 192 native tests and 5249 reported JS results; diagnostic inventory unchanged')
