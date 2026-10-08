# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json
import re
import shutil

root = Path.cwd()
out = root / 'work/nats-multiple-filter-interest-286-20261008'
for variant, count in [('clean', 20), ('control', 10)]:
    for target in ['fedora', 'leap', 'el10']:
        run = root / f'results/{target}-nats-multiple-filter-interest-286-{variant}'
        assert json.loads((run / 'status.json').read_text())['exit_code'] == 0
        log = (run / 'tests.log').read_text()
        assert len(re.findall(r'^--- PASS:', log, re.M)) == count
        assert not re.search(r'--- FAIL:|--- SKIP:|WARNING: DATA RACE|panic:', log)
        if variant == 'control':
            assert log.count('Missing stream subscription reproduces no responders') == count
name = 'nats-server-multiple-filter-interest-tests.patch'
shutil.copy2(out / name, root / 'dependencies' / name)
p = root / 'dependencies/nats-server.spec'
s = p.read_text()
needle = 'Patch115: nats-server-create-diagnostics-tests.patch\n'
assert s.count(needle) == 1 and name not in s
s = s.replace(needle, needle + 'Patch116: ' + name + '\n')
needle = '%changelog\n* Thu Oct 08 2026 David Nichols <david@qore.org> - 2.15.0-1.qore\n'
assert s.count(needle) == 1
s = s.replace(needle, needle + '- Join stream route interest before the multiple-filter fixture publishes setup messages.\n')
p.write_text(s)
p = root / 'dependencies/sources.json'
s = json.loads(p.read_text())
assert name not in s['nats-server']['extra_sources']
s['nats-server']['extra_sources'].append(name)
p.write_text(json.dumps(s, indent=2) + '\n')
p = root / 'dependencies/nats-server.rst'
s = p.read_text()
needle = 'Candidate 53 combines upstream 2.15.0 with 116 patches.'
assert needle in s
s = s.replace(needle, 'Candidate 54 combines upstream 2.15.0 with 117 patches.')
s += '''
Multiple-filter setup publication
---------------------------------

The multiple-filter last-per-subject test now joins the existing event-driven
stream route-interest check before publishing its six setup messages. The
stream-creation API reply travels independently from subscription propagation
to the randomly selected client server. Without that ordering the first
publication can correctly receive ``no responders`` before interest arrives.
Production behavior, request deadlines, message counts and consumer assertions
are unchanged.

All 90 focused race-enabled runs pass on Fedora, Leap and AlmaLinux. Thirty
controls temporarily remove the relevant subscription, reproduce the exact
error and restore it before completing the full fixture. These controls model
the ordering boundary; they are not a trace of the original failed schedule.
Candidate 53 remains running to collect all results. Candidate 54 includes the
correction and still requires complete RPM/native qualification.
'''
p.write_text(s)
print('Integrated Patch116 after all 90 race-enabled fixture/control runs passed.')
