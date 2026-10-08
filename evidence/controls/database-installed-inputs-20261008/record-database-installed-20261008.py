# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip
import hashlib
import json
import re
import shutil
import xml.etree.ElementTree as ET

root = Path.cwd()
out = root / 'evidence/controls/database-installed-inputs-20261008'
out.mkdir()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
sources = json.loads((root / 'results/database-obs-changelogs-20261008/status.json').read_text())
pins = {r['module']: r for r in sources}
builds = []
logs = root / 'results/database-changelog-builds-20261008'
readers = json.loads((logs / 'reader-status.json').read_text())
assert len(readers) == 12 and not any(readers.values())
for name in ('freetds', 'mysql'):
    results = ET.parse(root / f'results/database-arm-final-inputs-20261008/{name}-results.xml')
    assert len(results.findall('result')) == 6
    assert all(r.find('status').attrib['code'] == 'succeeded' for r in results.findall('result'))
for p in sorted(logs.glob('*.log')):
    name, repository, arch = p.stem.split('-')
    info = ET.parse(p.with_name(p.stem + '-buildinfo.xml'))
    assert info.findtext('srcmd5') == pins[name]['srcmd5']
    assert info.findtext('rev') == pins[name]['revision']
    text = p.read_text()
    tests = [tuple(map(int, row)) for row in re.findall(r'Ran (\d+) test cases, (\d+) succeeded \((\d+) assertions\)', text)]
    assert tests == ([(4, 4, 14)] if name == 'freetds' else [(6, 6, 47), (12, 12, 50), (16, 16, 106)])
    assert 'no value for $SOURCE_DATE_EPOCH' not in text
    assert not re.search(r'(?m)^.*\.(?:cc|cpp|c|h):\d+.*(?:warning|error):', text)
    assert not re.search(r'(?m)^.*\s[WE]: ', text)
    diagnostic_lines = [line for line in text.splitlines() if re.search(r'(?i)(warning:|error:|failed to|\[warning\])', line) and not re.match(r'^\[\s*\d+s\]\s*\+', line)]
    builds.append({'module': name, 'repository': repository, 'arch': arch,
                   'revision': info.findtext('rev'), 'srcmd5': info.findtext('srcmd5'),
                   'tests': tests, 'log_sha256': sha(p), 'diagnostic_lines': diagnostic_lines})

commands = json.loads((root / 'results/database-installed-commands-20261008/status.json').read_text())
assert len(commands) == 12 and all(step['exit_code'] == 0 for c in commands for step in c['steps'])
for c in commands:
    p = root / 'results/database-installed-commands-20261008' / ('-'.join([c['target'], c['module'], c['phase'], 'tests']) + '.log')
    counts = [tuple(map(int, row)) for row in re.findall(r'Ran (\d+) test cases, (\d+) succeeded \((\d+) assertions\)', p.read_text())]
    assert counts == ([(4, 4, 14)] if c['module'] == 'freetds' else [(6, 6, 47), (12, 12, 50), (16, 16, 106)])
    c['cases'] = sum(row[0] for row in counts)
    c['assertions'] = sum(row[2] for row in counts)
    c['log_sha256'] = sha(p)
lint = json.loads((root / 'results/database-installed-ci-lint-20261008/status.json').read_text())
assert lint == {'valid': True, 'errors': [], 'warnings': []}
unit = root / 'results/database-installed-final-tests-20261008.log'
assert 'Ran 227 tests' in unit.read_text() and unit.read_text().rstrip().endswith('OK')

folders = ['database-changelog-builds-20261008', 'database-obs-changelogs-20261008',
           'database-arm-final-inputs-20261008', 'database-arm-final-initial-transition-20261008',
           'database-installed-commands-20261008', 'database-installed-ci-lint-20261008']
for folder in folders:
    base = root / 'results' / folder
    for p in sorted(base.rglob('*')):
        if not p.is_file() or p.suffix == '.rpm':
            continue
        dest = out / folder / p.relative_to(base)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if p.suffix == '.log':
            dest.with_suffix(dest.suffix + '.gz').write_bytes(gzip.compress(p.read_bytes(), mtime=0))
        else:
            shutil.copyfile(p, dest)
(out / 'unit-tests.log.gz').write_bytes(gzip.compress(unit.read_bytes(), mtime=0))
for name in ['record-database-installed-20261008.py', 'test-database-installed-commands-20261008.py',
             'refresh-database-obs-changelogs-20261008.py', 'prepare-database-arm-final-manifests-20261008.py']:
    shutil.copyfile(root / 'work' / name, out / name)

paths = ['tools/qualify-installed.py', 'tests/test_installed_qualification.py', '.gitlab-ci.yml',
         'qualification/databases.rst', 'audits/database-installed-tools-20261008.rst']
paths += [f'qualification/databases-{t}-aarch64.json' for t in ('fedora', 'leap', 'el10')]
evidence = {
    'schema': 1, 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.', 'date': '2026-10-08',
    'result': 'All twelve refreshed native builds and all twelve installed command integration runs pass. The three new native clean-install jobs are prepared, not yet executed.',
    'sources': sources, 'native_builds': builds, 'installed_command_runs': commands,
    'installed_command_scope': 'Existing qualified x86_64 runtime/SDK images, unprivileged and offline. Fresh signed ARM installation remains a separate next gate.',
    'qualification_manifests': json.loads((root / 'results/database-arm-final-inputs-20261008/status.json').read_text()),
    'unit_tests': {'passed': 227, 'warnings': 0}, 'gitlab_lint': lint,
    'audit': {'pass': 10, 'not_applicable': 52, 'fail': 0, 'path': 'audits/database-installed-tools-20261008.rst'},
    'diagnostics': {
        'package': 'No compiler or rpmlint diagnostics. MySQL retains only the previously approved MAC-address and negative-authentication fixture messages; FreeTDS tests have none.',
        'infrastructure': 'Existing OBS VM console startup/read-only accounting, AlmaLinux bootstrap nologin ordering and optional mkbaselibs notices remain outside package tests. Exact Leap polkit bootstrap diagnostic was approved.',
        'references': ['evidence/process-state-qualification-20261003.json', 'evidence/obs-polkit-bootstrap-diagnostic-20261006.json', 'evidence/obs-changelog-metadata-20261006.json'],
        'fixed': 'Adding generated .changes removes missing changelog/SOURCE_DATE_EPOCH messages. Canonical archive preparation also removes group/other write bits; source bytes, specs and all other archive fields match the previous uploads.'
    },
    'handoff': 'The initial manifest preparation refused OBS finished/scheduling status before signing finalized. That snapshot is preserved. A subsequent independent snapshot confirms all twelve succeeded; no builds were restarted and no guard was weakened.',
    'publication': 'disabled',
    'limits': ['FreeTDS offline behavior only; no live SQL Server/ASE/OCS claim.', 'Native clean ARM runtime/SDK installation still pending.', 'Repository lifecycle and publication gates remain open.'],
    'qualified_files_sha256': {p: sha(root / p) for p in paths},
    'files_sha256': {str(p.relative_to(root)): sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
}
(root / 'evidence/database-installed-inputs-20261008.json').write_text(json.dumps(evidence, indent=2) + '\n')
print('PASS: 12 native builds, 12 installed command runs, 227 unit tests, full audit and CI lint archived')
