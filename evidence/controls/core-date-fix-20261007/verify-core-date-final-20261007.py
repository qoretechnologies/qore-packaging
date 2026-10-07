# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib
import json
import os
import re
import select

root = Path.cwd()
repo = root.parent / 'qore'
# Join the exact running qualifier through a process descriptor, without polling.
for p in Path('/proc').iterdir():
    if not p.name.isdigit():
        continue
    try:
        argv = (p / 'cmdline').read_bytes().decode().split('\0')
        if argv[:4] == ['python3', '-B', '-W', 'error'] and argv[4] == 'work/qualify-core-date-add-final3-20261007.py':
            fd = os.pidfd_open(int(p.name))
            try:
                select.select([fd], [], [])
            finally:
                os.close(fd)
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        pass

base = root / 'results/core-date-add-final3-tests-20261007'
records = []
for mode in ('debug', 'release'):
    target = base / mode
    rows = json.loads((target / 'status.json').read_text())
    assert [r['name'] for r in rows] == ['native', 'native-valgrind', 'date-add-native', 'date', 'date-utc-offset', 'date_durations']
    assert all(r['exit_code'] == 0 for r in rows)
    build = (target / 'native-build.log').read_text()
    assert 'Built target qore-date-add-test' in build and not re.search(r'(?i)warning:|error:', build)
    suites = []
    for row in rows:
        name = row['name']
        output = (target / (name + '.log')).read_text()
        if name.startswith('native'):
            assert 'PASS: 1836 DateTime addition cases' in output
        if name == 'native-valgrind':
            assert 'ERROR SUMMARY: 0 errors' in output
            for kind in ('definitely', 'indirectly', 'possibly'):
                assert re.search(kind + r' lost:\s+0 bytes in 0 blocks', output)
            lib = repo / ('build-debug' if mode == 'debug' else 'build') / 'libqore.so.20.0.0'
            for warning in re.findall(r'(?im)^.*warning:.*$', output):
                assert 'Warning: zero subprog, missing DW_AT_abstract_origin in DW_TAG_inlined_subroutine in ' + str(lib) in warning
        elif name != 'native':
            assert not re.search(r'(?i)warning:|error:|FAIL', output)
            skips = re.findall(r'^Skipped:.*$', output, re.M)
            assert skips == (['Skipped: WindowsTimeZoneTests: 0 assertions (skipping because the test is not run on Windows)'] if name == 'date' else [])
            match = re.search(r'Ran (\d+) test cases?, \1 succeeded \((\d+) assertions\)', output)
            assert match, output
            suites.append({'name': name, 'cases': int(match[1]), 'assertions': int(match[2]), 'platform_skips': skips})
    records.append({'mode': mode, 'native_cases': 1836, 'suites': suites})

matrix = root / 'results/core-relative-sign-matrix3-20261007'
rows = json.loads((matrix / 'status.json').read_text())
assert [r['name'] for r in rows] == ['original-build', 'original', 'fixed-build', 'fixed', 'valgrind', 'ubsan-build', 'ubsan']
assert all(r['exit_code'] == (1 if r['name'] == 'original' else 0) for r in rows)
for name in ['fixed', 'ubsan']:
    assert (matrix / (name + '.log')).read_text() == 'PASS: 679 signed-duration boundary cases\n'
vg = (matrix / 'valgrind.log').read_text()
assert 'ERROR SUMMARY: 0 errors' in vg
language = root / 'results/core-date-language-valgrind2-driver-20261007.log'
assert language.read_text().startswith('PASS: 2 cases / 29 assertions; zero lost allocations;')
files = ['CMakeLists.txt', 'lib/DateTime.cpp', 'include/qore/intern/qore_date_private.h', 'include/qore/DateTime.h',
         'examples/test/qore/vars/date_add.cpp', 'examples/test/qore/vars/date-add-native.qtest',
         'examples/test/qore/vars/date-add-native.rst', 'doxygen/lang/900_release_notes.dox.tmpl']
result = {'schema': 1, 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
          'result': 'pass', 'builds': records, 'normalization_control_cases': 679,
          'source_sha256': {name: hashlib.sha256((repo/name).read_bytes()).hexdigest() for name in files},
          'diagnostics': ['Existing GCC/Valgrind DW_AT_abstract_origin exception; exact library path verified.',
                          'Existing Fedora PCRE2 10.47 QUnit suffix-scan exception; exact JIT branch independently inspected under GDB.'],
          'harness_correction': 'The running qualifier expected plural test cases for the single-case duration suite; every child completed successfully. This verifier accepts QUnit singular/plural summaries and validates all recorded exit codes, checks and diagnostics without rerunning successful tests.'}
(root / 'results/core-date-final-verification-20261007.json').write_text(json.dumps(result, indent=2)+'\n')
print('PASS: both builds, 1836 native cases each, four Qore suites each, Valgrind and 679 UBSan/Valgrind boundary cases')
