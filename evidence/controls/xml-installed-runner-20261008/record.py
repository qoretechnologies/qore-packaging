# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip
import hashlib
import json
import re
import shutil

ROOT = Path(__file__).resolve().parent.parent
CHECKOUT = ROOT / 'work/checkouts/packaging-xml-installed-20261008'
DEST = CHECKOUT / 'evidence/controls/xml-installed-runner-20261008'
DEST.mkdir(parents=True, exist_ok=False)


def archive(source, name):
    destination = DEST / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.suffix == '.gz':
        destination.write_bytes(gzip.compress(source.read_bytes(), mtime=0))
        assert gzip.decompress(destination.read_bytes()) == source.read_bytes()
    else:
        shutil.copyfile(source, destination)


local = ROOT / 'results/xml-installed-runner-20261008'
assert json.loads((local / 'status.json').read_text()) == dict.fromkeys(('fedora', 'leap', 'el10'), 0)
allowed_features = {'DataProvider', 'RestSchemaValidator', 'Swagger', 'OpenApi3', 'RestClient'}
approval = json.loads((ROOT / 'evidence/xml-library-aot-diagnostics-20261006.json').read_text())
assert allowed_features <= set(approval['features'])
targets = {}
for target in ('fedora', 'leap', 'el10'):
    phases = json.loads((local / target / 'status.json').read_text())
    archive(local / target / 'status.json', target + '/status.json')
    for phase in ('runtime', 'sdk'):
        assert phases[phase]['exit_code'] == 0
        folder = local / target / phase
        steps = json.loads((folder / 'status.json').read_text())
        assert [s['name'] for s in steps] == (['tests'] if phase == 'runtime' else ['tests', 'compiler'])
        assert all(s['exit_code'] == 0 for s in steps)
        text = (folder / 'tests.log').read_text()
        assert text.count('Package test suites passed: 304') == 1
        assert 'WebDAV CLI: PUT/GET/PROPFIND/DELETE and SIGTERM passed' in text
        reported = re.findall(r'^Ran (\d+) test cases?, (\d+) succeeded \((\d+) assertions?(?:, (\d+) succeeded)?\)$', text, re.M)
        assert len(reported) == 304 and all(a == b for a, b, _, _ in reported)
        skips = [s for s in text.splitlines() if s.startswith('Skipped:')]
        assert len(skips) == 2 and all('Salesforce' in s for s in skips)
        unexpected = [s for s in text.splitlines() if re.match(r'^(?:warning:|WARNING:|ERROR:|FAIL:|Traceback|Unhandled)', s)]
        assert not unexpected, unexpected
        entry = {'exit_code': 0, 'suites': 304, 'reported_cases': sum(int(s[0]) for s in reported),
                 'reported_assertions': sum(int(s[2]) for s in reported),
                 'external_service_skips': skips, 'image': phases[phase]['image']}
        if phase == 'sdk':
            warnings = [s for s in (folder / 'compiler.log').read_text().splitlines() if s.startswith('warning:')]
            assert len(warnings) == 10
            assert {re.search(r"for feature '([^']+)'", s)[1] for s in warnings} == allowed_features
            assert all('AOT-MODULE-STALE:' in s and "optional module 'xml" in s for s in warnings)
            entry['compiler'] = {'exit_code': 0, 'approved_aot_diagnostic_occurrences': 10,
                                 'features': sorted(allowed_features)}
        targets.setdefault(target, {})[phase] = entry
        for source in folder.iterdir():
            if source.suffix in ('.log', '.json'):
                archive(source, target + '/' + phase + '/' + source.name + ('.gz' if source.suffix == '.log' else ''))

units = ROOT / 'results/xml-fixture-final-distribution-units-20261008'
unit_result = json.loads((units / 'status.json').read_text())
assert all(t['exit_code'] == 0 for t in unit_result['targets'].values())
for target in targets:
    text = (units / (target + '.log')).read_text()
    assert 'Ran 10 tests' in text and text.rstrip().endswith('OK')
    archive(units / (target + '.log'), 'units/' + target + '.log.gz')
archive(units / 'status.json', 'units/status.json')
host = ROOT / 'results/xml-installed-runner-final-units-20261008.log'
assert 'Ran 260 tests' in host.read_text() and host.read_text().rstrip().endswith('OK')
archive(host, 'units/host.log.gz')
for name in ('xml-final-fixture-inventory-20261008.json',):
    archive(ROOT / 'results' / name, name)
for name in ('xml-native-signatures-20261008/status.json', 'xml-native-signatures-20261008/signatures.log',
             'xml-arm-inputs-20261008/status.json', 'xml-native-ci-lint-20261008/response3.json'):
    archive(ROOT / 'results' / name, name + ('.gz' if name.endswith('.log') else ''))
ci = json.loads((ROOT / 'results/xml-native-ci-lint-20261008/response3.json').read_text())
assert ci['valid'] and not ci['errors'] and not ci['warnings']
signed = json.loads((ROOT / 'results/xml-native-signatures-20261008/status.json').read_text())
assert signed['exit_code'] == 0 and signed['signed_rpms'] == 58
archive(ROOT / 'work/qualify-xml-installed-runner-20261008.py', 'qualify.py')
archive(Path(__file__), 'record.py')
source_files = ['tools/installed_xml.py', 'tools/qualify-installed.py', 'tests/test_installed_xml.py',
                'tests/test_installed_qualification.py', '.gitlab-ci.yml', 'docs/source-and-build-workflow.rst',
                'audits/xml-installed-runner-20261008.rst', 'qualification/xml-fixtures.json',
                *('qualification/xml-' + t + '-aarch64.json' for t in targets)]
record = {
    'schema': 1, 'date': '2026-10-08', 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
    'status': 'Installed XML runner implementation qualified locally on Fedora, Leap and AlmaLinux; native installed jobs and final metadata revision remain pending.',
    'source_commit': 'd32601505b85b07823f98cc006fe438baa6dd3bc',
    'obs_revision': 'd672a36fd359885da3559de45cb2482d',
    'source_archive_sha256': '1be5b414fec3dae283823aa8985f2d4704d538fb059842c20f692e71131aa297',
    'fixtures': {'files': 1721, 'bytes': 91940823, 'top_level_suites': 304},
    'targets': targets,
    'units': {'host_methods': 260, 'final_xml_helper_methods_per_distribution': 10, 'distributions': 3},
    'native_inputs': {'signed_rpms': 58, 'fedora': 16, 'leap': 23, 'el10': 19,
                      'signature_check_exit_code': 0, 'ci_lint_valid': True},
    'audit': {'path': 'audits/xml-installed-runner-20261008.rst', 'pass': 9, 'not_applicable': 53, 'fail': 0},
    'diagnostic_approval': 'evidence/xml-library-aot-diagnostics-20261006.json; only the five recorded features appear in these SDK runs.',
    'limits': [
        'Local images use the earlier retained core baseline. Native manifests use core21 and require clean signed ARM runtime/SDK qualification.',
        'Two Salesforce tests explicitly skip without the separately provisioned service/proprietary WSDL fixtures; external Salesforce/Java integration remains a separate gate.',
        'Reported QUnit assertion totals include intentional negative comparison probes; the complete suite return codes and case results pass.',
        'The full local run began with stricter extension-based fixture modes. The final helper preserves archive executable bits; every final fixture byte/mode and final helper unit suite was independently checked. Native jobs must use the final helper.',
        'Existing XML RPM hidden-directory/duplicate-metadata lint diagnostics are not approved by this runner audit. The Release2 metadata candidate is qualified separately.',
        'No native installed job or repository publication is claimed by this record.',
    ],
    'implementation_sha256': {name: hashlib.sha256((CHECKOUT / name).read_bytes()).hexdigest() for name in source_files},
    'files_sha256': {str(p.relative_to(CHECKOUT)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted(DEST.rglob('*')) if p.is_file()},
}
(CHECKOUT / 'evidence/xml-installed-runner-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'phases': 6, 'suite_runs': 1824, 'signed_inputs': 58, 'files': len(record['files_sha256'])}))
