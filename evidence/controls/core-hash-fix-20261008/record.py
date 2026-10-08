# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip
import hashlib
import json
import re
import shutil
import subprocess

root = Path.cwd()
repo = root.parent / 'qore'
base = root / 'results/core-hash-lookup-final-20261008'
out = root / 'evidence/controls/core-hash-fix-20261008'
out.mkdir(exist_ok=True)
pins = json.loads((base / 'source-hashes.json').read_text())
for name, digest in pins.items():
    assert hashlib.sha256((repo / name).read_bytes()).hexdigest() == digest, name
assert json.loads((base / 'status.json').read_text()) == {'debug': 0, 'release': 0}
records = []
for mode in ['debug', 'release']:
    folder = base / mode
    steps = json.loads((folder / 'status.json').read_text())
    assert len(steps) == 7 and all(step['exit_code'] == 0 for step in steps)
    assert (folder / 'native.log').read_text() == 'PASS: 348 hash lookup checks\n'
    valgrind = (folder / 'native-valgrind.log').read_text()
    assert 'ERROR SUMMARY: 0 errors from 0 contexts' in valgrind
    for kind in ['definitely', 'indirectly', 'possibly']:
        assert re.search(kind + r' lost: 0 bytes in 0 blocks', valgrind)
    diagnostics = [line for line in valgrind.splitlines() if 'Warning:' in line]
    assert len(diagnostics) == 1 and 'zero subprog, missing DW_AT_abstract_origin' in diagnostics[0]
    suites = []
    for name, count, assertions in [('hash-lookup-native', 1, 2), ('hash', 1, 2), ('hashdecl', 13, 298)]:
        text = (folder / (name + '.log')).read_text()
        expected = f'Ran {count} test case' + ('s' if count > 1 else '') + f', {count} succeeded ({assertions} assertions)'
        assert expected in text
        assert not re.search(r'(?i)warn|error|fail|skip', text)
        suites.append({'name': name, 'cases': count, 'assertions': assertions})
    assert not re.search(r'warning:|error:', (folder / 'build.log').read_text())
    records.append({'mode': mode, 'native_checks': 348, 'valgrind_errors': 0,
                    'lost_bytes': 0, 'suites': suites, 'steps': steps})
negative = json.loads((root / 'results/core-hash-lookup-original-20261008/status.json').read_text())
assert [row['exit_code'] for row in negative] == [0, 1, 1, 1]
for name, message in [('encoded', 'encoded key not found'), ('conversion', 'conversion failure did not clear existence output'),
                      ('declaration', 'invalid hashdecl member did not clear existence output')]:
    assert message in (root / 'results/core-hash-lookup-original-20261008' / (name + '.log')).read_text()
docs = json.loads((root / 'results/core-hash-docs-20261008/status.json').read_text())
assert len(docs) == 4 and all(row['exit_code'] == 0 for row in docs)
for mode in ['debug', 'release']:
    assert (root / 'results/core-hash-docs-20261008' / (mode + '-run.log')).read_text() == 'Account balance: 73\n'
for directory in ['core-hash-lookup-final-20261008', 'core-hash-lookup-original-20261008',
                  'core-hash-lookup-20261008', 'core-hash-docs-20261008']:
    source = root / 'results' / directory
    for path in sorted(source.rglob('*')):
        if not path.is_file() or path.suffix not in ['.log', '.json', '.cpp']:
            continue
        dest = out / directory / path.relative_to(source)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == '.log':
            dest.with_suffix('.log.gz').write_bytes(gzip.compress(path.read_bytes(), mtime=0))
        else:
            shutil.copy2(path, dest)
for name in ['qualify-core-hash-lookup-20261008.py', 'qualify-core-hash-lookup-final-20261008.py', 'check-core-hash-docs-20261008.py']:
    shutil.copy2(root / 'work' / name, out / name)
shutil.copy2(repo / 'examples/test/qore/misc/audits/hash-lookup-native.rst', out / 'main-audit.rst')
shutil.copy2(Path(__file__), out / 'record.py')
record = {'schema': 1, 'date': '2026-10-08', 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
          'status': 'Runtime fix and all affected tests pass; ngtcp2 configure diagnostic decision pending. Not committed.',
          'base_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip(),
          'root_causes': ['Both exception-aware QoreString lookup overloads ignored the converted key and used the original encoded bytes.',
                         'Conversion and invalid-hashdecl-member errors could return without assigning the exists output.'],
          'fixes': ['Use the temporary default-encoding key for both lookup APIs.', 'Assign false to exists on both error paths.'],
          'qualification': records, 'source_sha256': pins, 'negative_controls': negative,
          'documentation_example': docs, 'audit': {'pass': 19, 'not_applicable': 43, 'fail': 0},
          'diagnostics': ['Previously approved GCC/Valgrind DW_AT_abstract_origin site; exact library path verified.',
                          'Two alternative ngtcp2 backend configure warnings: evidence/ngtcp2-backend-diagnostics-20261008.json; approval pending.'],
          'limits': ['No full updated RPM or native OBS qualification is claimed.',
                     'The initial make target-dispatch failure was corrected by explicit CMake configuration; no source or test change.',
                     'A preliminary -Wextra build rejected unused parameters in unchanged public virtual method headers; native fixture compilation uses normal -Wall -Werror.'],
          'files_sha256': {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
                           for path in sorted(out.rglob('*')) if path.is_file()}}
(root / 'evidence/core-hash-fix-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print('PASS: both modes, source hashes, all expected negative controls and documentation examples verified and archived')
