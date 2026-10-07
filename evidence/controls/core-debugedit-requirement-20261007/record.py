# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Record verified dependency and paired debugger controls without applying policy."""
from pathlib import Path
import gzip
import hashlib
import json
import re
import shutil
import subprocess
import tarfile

root = Path.cwd()
checkout = root / 'work/checkouts/qore-documentation-sdk-20261006'
commit = subprocess.check_output(['git', '-C', str(checkout), 'rev-parse', 'HEAD'], text=True).strip()
assert commit == 'cc8e5a90e87fe37033fa21a130128b3884cc7a1b'
assert not subprocess.check_output(['git', '-C', str(checkout), 'status', '--porcelain'])


def copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def hashes(directory):
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(directory.rglob('*')) if path.is_file()}


def statuses(path):
    rows = json.loads(path.read_text())
    assert {row['target'] for row in rows} == {'fedora', 'leap', 'el10'}
    assert all(row['exit_code'] == 0 for row in rows)
    return rows


dependency_out = root / 'evidence/controls/core-debugedit-requirement-20261007'
dependency_out.mkdir(exist_ok=True)
dependency_run = root / 'results/core-debugedit-requirement-20261007'
statuses(dependency_run / 'status.json')
for target in ('fedora', 'leap', 'el10'):
    log = dependency_run / target / 'tests.log'
    text = log.read_text()
    assert re.search(r'Ran 10 tests in [\d.]+s\n\nOK\s*$', text)
    assert not re.search(r'warning:|skipped|FAILED', text, re.I)
    copy(log, dependency_out / (target + '-tests.log'))
negative = dependency_run / 'leap/old-dependency.log'
assert 'debugedit >= 5.1' in negative.read_text() and 'FAILED (failures=1)' in negative.read_text()
copy(negative, dependency_out / 'leap-old-dependency.log')
copy(dependency_run / 'status.json', dependency_out / 'status.json')
for name in ('qore.spec-multi', 'rpm/README.rst', 'rpm/tests/test_spec_metadata.py',
             'rpm/tests/debugedit-requirement.audit.rst'):
    copy(checkout / name, dependency_out / name)
copy(root / 'work/test-core-debugedit-requirement-20261007.py', dependency_out / 'test.py')
copy(Path(__file__), dependency_out / 'record.py')
old_control = root / 'results/core-aot-debugger-smoke3-20261007/leap/old'
old_rows = json.loads((old_control / 'checks.json').read_text())
assert len(old_rows) == 1 and old_rows[0]['negative_exit'] == 0
assert 'Unknown DWARF DW_FORM_0x25' in old_rows[0]['diagnostic']
for name in ('checks.json', 'QUnit-old-debugedit.log.gz'):
    copy(old_control / name, dependency_out / ('old-reader-' + name))
dependency = root / 'results/leap-debugedit-final-1/rpmbuild/RPMS/x86_64/debugedit-5.1-1.qore.x86_64.rpm'
dependency_sha = hashlib.sha256(dependency.read_bytes()).hexdigest()
assert dependency_sha == '519b4e707be7b7534c3665d6758d334ced86dc3d3a0ed844b8850bcef8188d95'
record = {
    'schema': 1, 'date': '2026-10-07', 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
    'status': 'Dependency correction committed and pushed on the isolated RPM branch; updated canonical core RPM builds remain required.',
    'source_commit': commit, 'source_branch': 'rpm/documentation-sdk-20261006',
    'root_cause': 'The previous Leap builder still selected debugedit 5.0. It reports an unsupported indexed DWARF form while returning success. The recipe did not require the minimum supported reader.',
    'fix': 'Require debugedit >= 5.1 unconditionally as a build dependency, including when documentation and checks are disabled. No runtime dependency is added.',
    'validation': {'metadata_tests_per_distribution': 10, 'total_metadata_tests': 30,
        'old_leap_dependency_rejected': True, 'impossible_version_rejected_on_all_distributions': True,
        'old_reader_control': 'QUnit reproduces Unknown DWARF DW_FORM_0x25 with exit 0 after optional-index removal.',
        'backport_sha256': dependency_sha, 'backport_qualification': 'evidence/debugedit-leap-20261003.json'},
    'limits': ['This minimum-version correction does not resolve the separate unsupported optional .debug_names index.',
               'No C++ implementation changed. Existing reader backport qualification is reused.'],
    'files_sha256': hashes(dependency_out)
}
(root / 'evidence/core-debugedit-requirement-20261007.json').write_text(json.dumps(record, indent=2) + '\n')

out = root / 'evidence/controls/core-aot-debugger-proposal-20261007'
out.mkdir(exist_ok=True)
run = root / 'results/core-aot-debugger-all2-20261007'
statuses(run / 'status.json')
copy(run / 'status.json', out / 'paired-status.json')
summary = {}
module_names = None
for target in ('fedora', 'leap', 'el10'):
    directory = run / target / 'new'
    checks = json.loads((directory / 'checks.json').read_text())
    names = {row['module'] for row in checks}
    assert len(checks) == len(names) == 390
    if module_names is None:
        module_names = names
    assert names == module_names
    assert sum(row['functions'] for row in checks) == 58398
    for row in checks:
        assert row['symbols_unchanged'] and row['gdb_warning_removed']
        assert not row['metadata_only'] and not row['debugedit_stderr']
        assert row['breakpoint_source'].startswith('/usr/src/debug/qore-aot-control/qlib/')
        assert row['metadata_sha256'] and row['original_sha256']
        retained = row['all_other_dwarf_and_allocated_sections_preserved']
        assert '.debug_info' in retained and '.text' in retained and '.debug_names' not in retained
    # Store the 780 compressed raw logs and section inventories in one deterministic archive.
    archive = out / (target + '-paired-controls.tar.gz')
    with archive.open('wb') as stream:
        with gzip.GzipFile(filename='', mode='wb', fileobj=stream, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode='w') as tar:
                for source in sorted(directory.iterdir()):
                    assert source.is_file()
                    info = tar.gettarinfo(str(source), arcname=source.name)
                    info.uid = info.gid = info.mtime = 0
                    info.uname = info.gname = ''
                    info.mode = 0o644
                    with source.open('rb') as content:
                        tar.addfile(info, content)
    # Verify archived JSON and every raw log against the accepted run.
    with tarfile.open(archive, 'r:gz') as tar:
        assert len(tar.getmembers()) == 781
        for member in tar.getmembers():
            assert tar.extractfile(member).read() == (directory / member.name).read_bytes()
    copy(run / target / 'driver.log', out / (target + '-driver.log'))
    summary[target] = {'modules': len(checks), 'source_indexed_functions': 58398,
                       'source_lookup_and_breakpoint_setup_checks': 390,
                       'metadata_only_exemptions': 0}

recipe_run = root / 'results/core-index-recipe-2-20261007'
statuses(recipe_run / 'status.json')
for source in recipe_run.iterdir():
    copy(source, out / 'recipe' / source.name)
for source in (root / 'results/core-index-recipe-20261007').iterdir():
    copy(source, out / 'recipe-initial-harness-failure' / source.name)
for name in ('core-aot-debugger-control-20261007.py', 'run-core-aot-debugger-20261007.py',
             'check-core-index-recipe-20261007.py'):
    copy(root / 'work' / name, out / name)
copy(Path(__file__), out / 'record.py')
for source in (root / 'work/core-aot-index-proposal-20261007').iterdir():
    copy(source, out / 'proposal' / source.name)
record = {
    'schema': 1, 'date': '2026-10-07', 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
    'status': 'Concrete proposal completely paired-tested; not applied to the source recipe and not yet approved.',
    'source_base_commit': commit,
    'proposal': 'Remove only the optional .debug_names index from the 390 compiled core standard-library modules during RPM installation, through the existing metadata-preservation helper. Add explicit binutils BuildRequires. All full DWARF, runtime sections, symbols, source and Qore trailers remain available.',
    'reason': 'Distribution GDB rejects the LLVM-created name index. Reading the retained full DWARF succeeds without it. This extends the debugger configuration previously approved for PDFium, Oracle and selected external AOT modules.',
    'approval': {'status': 'requested', 'scope': '390 core standard-library AOT modules only; optional .debug_names removal, no blanket diagnostic exception'},
    'validation': {'distributions': summary, 'module_instances': 1170,
        'source_indexed_functions_preserved': 175194,
        'exact_install_commands_passed': 3,
        'exact_recipe_modules_per_distribution': ['QUnit', 'MapperUtil'],
        'negative_scope': 'A module outside the standard-library API directory remains byte-identical.',
        'section_validation': 'Before debugedit rewriting, each other .debug_* section and every allocated runtime section is byte-identical. Symbol listings and exact Qore EOF trailers are preserved. Trailers remain identical after debugedit.',
        'paired_gdb': 'Every original module reproduces the rejected-index warning. Every adjusted module preserves the complete source-indexed function list and passes source lookup and breakpoint setup without that warning.'},
    'limits': ['Breakpoint setup and source lookup are tested, not execution to a breakpoint in a live process.',
        'These are retained x86_64 canonical core22 outputs; new complete RPM builds, installed artifact checks and native aarch64 qualification remain required.',
        'Initial debugger loading may be slower because GDB reads full DWARF instead of a precomputed name index.',
        'The proposal also needs the independently qualified debugedit >= 5.1 dependency correction.',
        'No C++ implementation or runtime section changes; no new Valgrind run is required for this packaging operation.'],
    'control_corrections': [
        'Initial smoke probes omitted the existing trailer-preservation helper and assumed debugedit 5.0 returned failure. They were corrected before acceptance.',
        'Retained modules already contain RPM debug-prefix mapping; the control now derives the actual GDB source prefix before rewriting it.',
        'The first full probe selected only ordinary _qaot_ function names and stopped at MapperUtil, which has constant initializers. The accepted probe compares every source-indexed function; all 390 modules have real functions.',
        'The first exact-recipe probe used only a buildroot macro override; newer RPM versions replace that value. Setting _topdir as well places each actual expanded path in the private container /tmp tree. All three corrected recipe probes pass.'
    ],
    'files_sha256': hashes(out)
}
(root / 'evidence/core-aot-debugger-proposal-20261007.json').write_text(json.dumps(record, indent=2) + '\n')
print('Verified 30 dependency tests and 1170 paired module checks; proposal remains unapplied')
