# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip
import hashlib
import json
import runpy
import shutil
import subprocess
import xml.etree.ElementTree as ET

root = Path.cwd()
out = root / 'results/grpc-native-upload-20261008'
out.mkdir()
source = root / 'work/grpc-native-dependencies-20261008'
manifest = json.loads((source / 'source-manifest.json').read_text())
assert manifest['commit'] == '91714602e4c7d8bda5e7222a9e65dc99a045dbdd'
for path in ['grpc-rpm-dependency-final-tests-20261008.log', 'grpc-rpm-dependency-leap-tests-20261008.log']:
    text = (root / 'results' / path).read_text()
    assert 'Ran 3 tests' in text and text.rstrip().endswith('OK')
tests = (root / 'results/grpc-native-catalog-tests-20261008.log').read_text()
assert 'Ran 227 tests' in tests and tests.rstrip().endswith('OK')
for family in ['Fedora_44', 'AlmaLinux_10']:
    assert ET.parse(root / f'results/grpc-native-prerequisites-20261008/{family}.xml').find('error') is None
osc = ['osc', '--setopt', 'http_retries=1', '-A', 'https://api.opensuse.org', 'api']
base = '/source/home:davidnichols:qore:testing/qore-grpc-module'
before = subprocess.check_output([*osc, base + '/_meta'])
(out / 'metadata-before.xml').write_bytes(before)
old = ET.fromstring(before)
assert [e.tag for e in old.find('publish')] == ['disable']
assert {(e.tag, tuple(sorted(e.attrib.items()))) for e in old.find('build')} == {
    ('disable', ()), ('enable', (('arch', 'x86_64'), ('repository', 'Fedora_44'))),
    ('enable', (('arch', 'x86_64'), ('repository', 'AlmaLinux_10')))}
old_manifest = json.loads(subprocess.check_output([*osc, base + '/source-manifest.json']))
assert old_manifest['commit'] == '49a9c976c918e822b1a6ea6054271f09e443af62'
with (out / 'upload.log').open('x') as log:
    subprocess.run(['python3', '-B', '-W', 'error', 'tools/obs.py', 'upload', '--project',
                    'home:davidnichols:qore:testing', '--source', str(source), '--apply'],
                   stdout=log, stderr=subprocess.STDOUT, check=True)
listing = subprocess.check_output([*osc, base])
(out / 'source.xml').write_bytes(listing)
remote = ET.fromstring(listing)
assert {e.attrib['name'] for e in remote.findall('entry')} == set(manifest['sources']) | {'source-manifest.json'}
for e in remote.findall('entry'):
    assert hashlib.md5((source / e.attrib['name']).read_bytes()).hexdigest() == e.attrib['md5']
remote_manifest = subprocess.check_output([*osc, base + '/source-manifest.json?rev=' + remote.attrib['rev']])
assert json.loads(remote_manifest) == manifest
(out / 'manifest.json').write_bytes(remote_manifest)
metadata = root / 'obs/package-grpc-testing.xml'
expected = ET.parse(metadata).getroot()
assert [e.tag for e in expected.find('publish')] == ['disable']
assert {(e.attrib['repository'], e.attrib['arch']) for e in expected.find('build') if e.tag == 'enable'} == {
    (r, a) for r in ['Fedora_44', 'AlmaLinux_10', 'openSUSE_Leap_16.0'] for a in ['x86_64', 'aarch64']}
subprocess.run([*osc, '-X', 'PUT', '-T', str(metadata), base + '/_meta'], check=True)
after = subprocess.check_output([*osc, base + '/_meta'])
(out / 'metadata-after.xml').write_bytes(after)
actual = ET.fromstring(after)
assert [(e.tag, e.attrib) for e in actual.find('build')] == [(e.tag, e.attrib) for e in expected.find('build')]
assert [e.tag for e in actual.find('publish')] == ['disable']
proof = root / 'evidence/controls/grpc-native-dependencies-20261008'
proof.mkdir()
for p in out.iterdir():
    if p.suffix == '.log':
        (proof / (p.name + '.gz')).write_bytes(gzip.compress(p.read_bytes(), mtime=0))
    else:
        shutil.copyfile(p, proof / p.name)
for name in ['grpc-rpm-dependency-final-tests-20261008.log', 'grpc-rpm-dependency-leap-tests-20261008.log',
             'grpc-native-catalog-tests-20261008.log', 'grpc-original-dependencies-20261008.log',
             'grpc-leap-current-sdk-capabilities-20261008.log', 'grpc-leap-arm-prerequisite-20261008.xml']:
    p = root / 'results' / name
    (proof / (p.name + '.gz')).write_bytes(gzip.compress(p.read_bytes(), mtime=0))
shutil.copyfile(root / 'results/grpc-leap-native-providers-20261008/provides.txt', proof / 'native-grpcio-tools-provides.txt')
shutil.copyfile(__file__, proof / 'upload.py')
audit = runpy.run_path(str(root / 'work/write-scoped-audit.py'))
audit['write'](root / 'audits/grpc-native-dependencies-20261008.rst', 'gRPC native source delivery audit',
    'Scope: catalog pin and OBS testing metadata. All 62 checks: 5 Pass, 57 N/A, 0 Fail. Module packaging audit is committed with source 91714602e4c7d8bda5e7222a9e65dc99a045dbdd; native and installed results remain separate gates.',
    {9: 'Metadata, scripts and evidence carry Copyright 2026.',
     53: 'Use actual SUSE package-name aliases; retain Fedora/EL capabilities. No fake provides, disabled tests, changed deadlines or diagnostic filters.',
     59: 'Module packaging guide and release notes explain the resolver correction; evidence records its exact scope and pending native tests.',
     61: 'All uploaded files match the committed source bundle; only six named testing targets enabled, publication remains disabled.',
     62: '227 packaging tests and the new actual RPM-parser regression pass. Both Fedora and Leap parsers cover all three family branches and test-disabled builds; original SUSE mapping fails the negative control. Native grpcio-tools alias verified directly from its ARM RPM.'},
    'No corresponding runtime C++, Qore/QPP module, DataProvider, JNI, sandbox, cancellation or concurrency change in this source-delivery-only scope.')
record = {'schema': 1, 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.', 'date': '2026-10-08',
    'status': 'Committed corrected fixture requirements uploaded; six native builds enabled; publication disabled.',
    'root_cause': 'Native Leap grpcio-tools provides python3-grpcio-tools but no python3dist(grpcio-tools). The spec requested the absent capability; PyArrow also had not been delivered to OBS.',
    'fix': 'SUSE resolves all three Python fixtures by the normal python3-* package aliases. Fedora/EL preserve their original distribution capabilities. All existing interoperability suites remain enabled.',
    'module_commit': manifest['commit'], 'module_branch': 'rpm/native-dependencies-20261008',
    'module_audit': 'test/audits/rpm-native-dependencies.rst: 11 Pass, 51 N/A, 0 Fail',
    'source': manifest, 'obs': remote.attrib,
    'tests': {'rpm_parser_methods': 3, 'rpm_parser_platforms': ['Fedora', 'Leap'], 'packaging': 227,
              'negative_control': 'The original spec fails exactly the SUSE alias regression.'},
    'harness_correction': 'Cross-family RPM parser controls set the matching dist suffix together with family macros, avoiding the host Fedora suffix referencing an intentionally undefined Fedora macro.',
    'pyarrow': 'evidence/pyarrow-obs-submission-20261008.json',
    'pending': 'Native RPM tests/lint, signed installed ARM qualification and source integration into develop; no publication claim.',
    'files_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in proof.iterdir()}}
(root / 'evidence/grpc-native-dependencies-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print('PASS: uploaded revision', remote.attrib['rev'], remote.attrib['srcmd5'], 'and enabled six testing builds')
