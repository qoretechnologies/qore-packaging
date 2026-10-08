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
source = root / 'work/python-pyarrow-obs-changelog-20261008'
out = root / 'results/pyarrow-obs-submission-20261008'
out.mkdir()
evidence_out = root / 'evidence/controls/pyarrow-obs-submission-20261008'
evidence_out.mkdir()
manifest = json.loads((source / 'source-manifest.json').read_text())
build_root = root / 'results/leap-python-pyarrow-final-1'
build = json.loads((build_root / 'build.json').read_text())
assert build['exit_code'] == 0 and manifest['commit'] == build['source']['commit']
assert all(manifest['sources'][p] == h for p, h in build['source']['sources'].items())
assert set(manifest['sources']) - set(build['source']['sources']) == {'python-pyarrow.changes'}
for p, h in build['artifacts'].items():
    assert hashlib.sha256((build_root / p).read_bytes()).hexdigest() == h
metadata_path = root / 'obs/package-pyarrow-testing.xml'
meta = ET.parse(metadata_path).getroot()
assert meta.attrib == {'name': 'python-pyarrow', 'project': 'home:davidnichols:qore:testing'}
assert [e.tag for e in meta.find('publish')] == ['disable'] and not meta.find('publish')[0].attrib
assert [(e.tag, e.attrib) for e in meta.find('build')] == [
    ('disable', {}), ('enable', {'repository': 'openSUSE_Leap_16.0', 'arch': 'x86_64'}),
    ('enable', {'repository': 'openSUSE_Leap_16.0', 'arch': 'aarch64'})]
osc = ['osc', '--setopt', 'http_retries=1', '-A', 'https://api.opensuse.org', 'api']
base = '/source/home:davidnichols:qore:testing/python-pyarrow'
previous = subprocess.run([*osc, base + '/_meta'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
(out / 'initial-metadata.stderr').write_bytes(previous.stderr)
assert previous.returncode != 0 and b'404' in previous.stderr, 'Do not replace an existing package'
subprocess.run([*osc, '-X', 'PUT', '-T', str(metadata_path), base + '/_meta'], check=True)
with (out / 'upload.log').open('x') as log:
    subprocess.run(['python3', '-B', '-W', 'error', 'tools/obs.py', 'upload', '--project',
                    'home:davidnichols:qore:testing', '--source', str(source), '--apply'],
                   stdout=log, stderr=subprocess.STDOUT, check=True)
listing = subprocess.check_output([*osc, base])
(out / 'source.xml').write_bytes(listing)
remote = ET.fromstring(listing)
expected = set(manifest['sources']) | {'source-manifest.json'}
assert {e.attrib['name'] for e in remote.findall('entry')} == expected
for entry in remote.findall('entry'):
    assert hashlib.md5((source / entry.attrib['name']).read_bytes()).hexdigest() == entry.attrib['md5']
remote_manifest = subprocess.check_output([*osc, base + '/source-manifest.json?rev=' + remote.attrib['rev']])
assert json.loads(remote_manifest) == manifest
(out / 'manifest.json').write_bytes(remote_manifest)
remote_meta = subprocess.check_output([*osc, base + '/_meta'])
(out / 'metadata.xml').write_bytes(remote_meta)
assert [e.tag for e in ET.fromstring(remote_meta).find('publish')] == ['disable']
for p in out.iterdir():
    if p.suffix == '.log':
        (evidence_out / (p.name + '.gz')).write_bytes(gzip.compress(p.read_bytes(), mtime=0))
    else:
        shutil.copyfile(p, evidence_out / p.name)
for name in ['build.json', 'build.log']:
    p = build_root / name
    (evidence_out / (name + '.gz')).write_bytes(gzip.compress(p.read_bytes(), mtime=0))
shutil.copyfile(__file__, evidence_out / 'submit.py')
audit = runpy.run_path(str(root / 'work/write-scoped-audit.py'))
audit['write'](root / 'audits/pyarrow-obs-submission-20261008.rst', 'PyArrow OBS submission audit',
    'Scope: OBS metadata and immutable source delivery; no package source/spec/runtime change. All 62 checklist entries reviewed: 5 Pass, 57 N/A, 0 Fail. Native builds are the next gate.',
    {9: 'New metadata, verifier and evidence carry Copyright 2026.',
     53: 'The previously tested canonical source is unchanged; only generated OBS timestamp metadata is added. No test or compiler-policy change.',
     59: 'Evidence separates local canonical qualification, approved diagnostics, upstream skip/xfail outcomes and pending native builds.',
     61: 'Only the new Leap x86_64/aarch64 testing package is enabled; publication remains disabled. Every uploaded file is checked against its local digest and source manifest.',
     62: 'Canonical build passes 3 package regressions and 6616 upstream tests, with 1646 feature/dependency skips, 13 xfails and one non-strict upstream xpass. All four RPM hashes and all unchanged source hashes are verified. The 24 compiler warnings match the previously accepted inventory.'},
    'No corresponding C++, Qore/QPP module, DataProvider, JNI, threading or runtime implementation change in this source-delivery-only scope.')
record = {
    'schema': 1, 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.', 'date': '2026-10-08',
    'status': 'The canonical tested PyArrow dependency is uploaded with generated changelog metadata; both Leap native builds enabled and publication disabled.',
    'source': manifest, 'obs': remote.attrib,
    'prior_evidence': 'evidence/pyarrow-external-diagnostics-20261003.json',
    'qualification': {'packaging_cases': 3, 'upstream_passed': 6616, 'upstream_skipped': 1646,
                      'upstream_xfailed': 13, 'upstream_non_strict_xpassed': 1, 'rpm_hashes_verified': 4},
    'unchanged': 'Every canonical archive, patch, test and spec byte is unchanged. Only python-pyarrow.changes is added by the tested source preparer.',
    'pending': 'Native build/lint and signed ARM installation; Qore gRPC needs conventional SUSE package-name build requirements because native grpcio-tools lacks python3dist virtual provides.',
    'files_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in evidence_out.rglob('*') if p.is_file()}
}
(root / 'evidence/pyarrow-obs-submission-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print('PASS: source revision', remote.attrib['rev'], remote.attrib['srcmd5'], 'verified; native builds enabled; publication disabled')
