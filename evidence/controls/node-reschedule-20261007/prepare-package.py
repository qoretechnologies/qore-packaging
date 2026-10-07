# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json
import shutil

root = Path('work/node-reschedule-native-20261007')
records = json.loads((root / 'instrumented-status.json').read_text())
assert len(records) == 8 and all(r['exit_code'] == r['expected'] for r in records)
for name in ('fixed', 'fixed-instrumented'):
    log = (root / (name + '-seven-valgrind.log')).read_text()
    assert 'ERROR SUMMARY: 0 errors from 0 contexts' in log
    assert 'All heap blocks were freed' in log
shutil.copy2(root / 'proposed.patch', 'dependencies/nodejs24-reschedule-end.patch')
shutil.copy2(root / 'control.cc', 'dependencies/nodejs24-reschedule-test.cc')
p = Path('dependencies/nodejs24-libnode.spec')
source = p.read_text()
assert 'nodejs24-reschedule-end.patch' not in source
source = source.replace('Source21: nodejs24-external-string-resource-test.cc\n',
    'Source21: nodejs24-external-string-resource-test.cc\n'
    'Source22: nodejs24-reschedule-test.cc\nSource23: nodejs24-reschedule-test.py\n')
source = source.replace('Patch17: nodejs24-external-string-resource.patch\n',
    'Patch17: nodejs24-external-string-resource.patch\nPatch18: nodejs24-reschedule-end.patch\n')
source = source.replace('%check\n', '%check\n'
    '# Exercise the actual native compiler archives and their generated snapshot.\n'
    'python3 %{SOURCE23} --source . --test-source %{SOURCE22} \\\n'
    '    --output out/reschedule-control\n', 1)
source = source.replace('- Initialize the V8 verifier result for forwarded one-byte external resources.\n',
    '- Complete V8 terminal graph processing before reading nonexistent block state.\n'
    '- Test seven graph shapes with the native compiler and generated snapshot.\n'
    '- Initialize the V8 verifier result for forwarded one-byte external resources.\n', 1)
p.write_text(source)
p = Path('dependencies/sources.json')
data = json.loads(p.read_text())
entry = data['nodejs24-libnode']
key = next(k for k, v in entry.items() if isinstance(v, list) and 'nodejs24-external-string-resource.patch' in v)
entry[key].extend(['nodejs24-reschedule-end.patch', 'nodejs24-reschedule-test.cc', 'nodejs24-reschedule-test.py'])
p.write_text(json.dumps(data, indent=2) + '\n')
p = Path('dependencies/nodejs24-libnode.rst')
source = p.read_text()
anchor = "Leap's resolver checker mistakes"
index = source.index(anchor)
source = source[:index] + '''The next candidate also fixes uninitialized terminal-block state in V8's
``RawMachineAssembler``. The end block merges incoming return/throw controls
and then stops; it has no successors requiring an effect/control pair.
Seven native graph shapes pass 700 cases, including loops, merges, switches
and deferred throws. Diagnostic Memcheck requests expose 1,200 reads in the
original and none after the fix; both fixed runs free all allocations.
The RPM regression uses the package's actual compiler archives and generated
snapshot. It uses native sections of the fat archives with matching ABI,
feature, hardening and warning flags; the runtime retains its normal LTO.
Complete updated RPM and native architecture qualification remain required.

''' + source[index:]
p.write_text(source)
print('Prepared terminal-block fix, native graph regression and package check.')
