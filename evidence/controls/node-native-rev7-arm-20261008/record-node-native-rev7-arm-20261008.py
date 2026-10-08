# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Record the completed ARM build, keeping unapproved diagnostics explicit."""
from pathlib import Path
import collections
import gzip
import hashlib
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent.parent
out = root / 'evidence/controls/node-native-rev7-arm-20261008'
out.mkdir()
osc = ['osc', '--setopt', 'http_retries=1', '-A', 'https://api.opensuse.org', 'api']
base = '/build/home:davidnichols:qore:testing/openSUSE_Leap_16.0/aarch64/nodejs24-libnode'
info = subprocess.check_output([*osc, base + '/_buildinfo'])
parsed = ET.fromstring(info)
assert parsed.findtext('srcmd5') == '68633aee6138c8992573ca51eddf282f'
assert parsed.findtext('rev') == '7'
(out / 'buildinfo.xml').write_bytes(info)
state = subprocess.check_output([*osc, '/build/home:davidnichols:qore:testing/_result?package=nodejs24-libnode'])
arm = [r for r in ET.fromstring(state).findall('result')
       if r.get('repository') == 'openSUSE_Leap_16.0' and r.get('arch') == 'aarch64']
assert len(arm) == 1 and arm[0].find('status').get('code') == 'succeeded'
(out / 'state.xml').write_bytes(state)
(out / 'binaries.xml').write_bytes(subprocess.check_output([*osc, base]))
previous = root / 'results/node-native-rev7-live2-20261008/aarch64.log'
suffix = root / 'results/node-native-rev7-live3-20261008/aarch64-suffix.log'
receipt = json.loads((suffix.parent / 'aarch64-reader-status.json').read_text())
assert receipt['reader_exit_code'] == 0 and receipt['overlap_verified'] == 256
assert previous.read_bytes()[-256:] == suffix.read_bytes()[:256]
full = previous.read_bytes() + suffix.read_bytes()[256:]
log = re.sub(r'^\[\s*\d+s\] ?', '', full.decode(), flags=re.M)
assert 'armv9 finished "build nodejs24-libnode.spec"' in log
assert '[  PASSED  ] 192 tests.' in log and 'All tests passed.' in log
assert '0 errors, 0 warnings, 15 filtered, 0 badness' in log
assert 'PASS: 4491 actual ARM64 Operand checks' in log
assert 'PASS: 459 constructor/copy field checks' in log
assert not re.search(r'^not ok ', log, re.M)
rows = re.findall(r'^ok (\d+) (.*)$', log, re.M)
assert [int(n) for n, _ in rows] == list(range(1, 5246))
old = re.sub(r'^\[\s*\d+s\] ?', '',
             (root / 'results/node-native-rev6-live-20261008/aarch64.log').read_text(), flags=re.M)
before = collections.Counter(x for x in old.splitlines() if ': warning:' in x)
after = collections.Counter(x for x in log.splitlines() if ': warning:' in x)
assert not after - before
inventory = json.loads((root / 'results/node-arm-diagnostics-remaining-20261008.json').read_text())
fixed = [r['diagnostic'] for r in inventory if r['reference'] == 'evidence/node-arm-initialization-fix-20261008.json']
assert len(fixed) == 8 and all(before[x] > 0 and after[x] == 0 for x in fixed)
assert len(re.findall(r'^PASS: test/mjsunit/wasm/deopt/', log, re.M)) == 31
review = {'before_unique': len(before), 'after_unique': len(after),
          'after_occurrences': sum(after.values()), 'removed_occurrences': dict(before - after),
          'new_occurrences': dict(after - before), 'initialization_diagnostics_eliminated': fixed}
(out / 'compiler-delta.json').write_text(json.dumps(review, indent=2) + '\n')
(out / 'build.log.gz').write_bytes(gzip.compress(full, mtime=0))
(out / 'reader-status.json').write_text(json.dumps(receipt, indent=2) + '\n')
shutil.copyfile(Path(__file__), out / Path(__file__).name)
record = {
    'schema': 1, 'date': '2026-10-08', 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
    'status': 'Revision 7 ARM build and all functional/lint checks pass; eight fixed initialization warnings are absent. Existing exact diagnostic approvals remain pending.',
    'project': 'home:davidnichols:qore:testing', 'package': 'nodejs24-libnode',
    'source_commit': '0997787ef8c0c8564640b9faa7bea71166ec206e',
    'revision': 7, 'srcmd5': '68633aee6138c8992573ca51eddf282f', 'arch': 'aarch64',
    'native_tests': 192, 'javascript_reported_results': len(rows),
    'upstream_skips': [v for _, v in rows if '# skip' in v.lower()],
    'upstream_todos': [v for _, v in rows if '# todo' in v.lower()],
    'wasm_deoptimization_scripts': 31, 'arm_operand_checks': 4491, 'arm_constructor_copy_checks': 459,
    'lint': {'errors': 0, 'warnings': 0, 'existing_approved_filters': 15},
    'compiler_review': review,
    'pending_diagnostics': ['evidence/node-arm-pio2-diagnostic-20261008.json',
                            'evidence/node-arm-bti-diagnostic-20261008.json',
                            'evidence/node-vm-notice-20261008.json'],
    'approved_root_load_diagnostic': 'evidence/node-arm-root-load-diagnostic-20261008.json',
    'limits': ['The 5245 upstream ok results include 80 skipped and 12 TODO results; these are not counted as executed passing cases.',
               'The x86_64 revision-7 build remains a separate gate; this evidence does not qualify its unfinished build.',
               'Installed libnode/V8 module qualification, lifecycle testing and publication remain required.',
               'No suppression or new compiler policy was introduced. Full diagnostic acceptance still requires the three existing pending decisions.'],
    'files_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted(out.iterdir()) if p.is_file()}}
(root / 'evidence/node-native-rev7-arm-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print('PASS: ARM revision 7; 192 native tests, 5245 reported JS results; all eight targeted warnings absent')
