# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET

root = Path.cwd()
project = 'home:davidnichols:qore:testing'
package = 'nodejs24-libnode'
source = root / 'work/nodejs24-libnode-built-library-20261007'
previous = root / 'work/nodejs24-libnode-canonical-final-20261007'
manifest = json.loads((source / 'source-manifest.json').read_text())
old = json.loads((previous / 'source-manifest.json').read_text())
qualification = json.loads((root / 'evidence/node-built-library-20261007.json').read_text())
for relative, digest in qualification['files_sha256'].items():
    assert hashlib.sha256((root / relative).read_bytes()).hexdigest() == digest, relative
assert manifest['commit'] == '1d5ee90745fd2c422f85e2fe1be068afc6f022c4' and not manifest.get('candidate')
assert manifest['sources'].keys() == old['sources'].keys()
changed = sorted(name for name in manifest['sources'] if manifest['sources'][name] != old['sources'][name])
assert changed == ['nodejs24-libnode.changes', 'nodejs24-libnode.spec'], changed
assert (source / 'nodejs24-libnode.spec').read_bytes() == (root / 'evidence/controls/node-built-library-20261007/nodejs24-libnode.spec').read_bytes()
remote_git = subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/main'], text=True).split()[0]
assert remote_git == manifest['commit'], remote_git
osc = ['osc', '--setopt', 'http_retries=1', '-A', 'https://api.opensuse.org']
out = root / 'evidence/controls/node-built-library-obs-20261007'
out.mkdir()


def get(path, name):
    data = subprocess.check_output([*osc, 'api', path])
    (out / name).write_bytes(data)
    return ET.fromstring(data)


project_meta = get('/source/' + project + '/_meta', 'project-meta-before.xml')
publish = project_meta.find('publish')
assert publish is not None and len(publish) == 1 and publish[0].tag == 'disable' and not publish[0].attrib
package_meta = get(f'/source/{project}/{package}/_meta', 'package-meta-before.xml')
expected = ET.parse(root / 'obs/package-nodejs24-libnode-testing.xml').getroot()
for flag in ('build', 'publish'):
    def flags(meta):
        return {(child.tag, tuple(sorted(child.attrib.items()))) for child in meta.find(flag)}
    assert flags(package_meta) == flags(expected), flag
with (out / 'upload.log').open('x') as log:
    subprocess.run(['python3', '-B', '-W', 'error', 'tools/obs.py', 'upload', '--project', project,
                    '--source', str(source), '--apply'], stdout=log, stderr=subprocess.STDOUT, check=True)
remote = get(f'/source/{project}/{package}', 'source-listing.xml')
expected_md5 = {name: hashlib.md5((source / name).read_bytes()).hexdigest()
                for name in [*manifest['sources'], 'source-manifest.json']}
assert {entry.get('name'): entry.get('md5') for entry in remote.findall('entry')} == expected_md5
after = get(f'/source/{project}/{package}/_meta', 'package-meta-after.xml')
assert ET.tostring(after) == ET.tostring(package_meta)
get(f'/build/{project}/_result?package={package}', 'scheduler-after-upload.xml')
(out / 'source-manifest.json').write_bytes((source / 'source-manifest.json').read_bytes())
(out / 'upload.py').write_bytes(Path(__file__).read_bytes())
record = {'schema': 1, 'at_utc': datetime.now(timezone.utc).isoformat(),
          'status': 'Tested link-input correction uploaded and all OBS source checksums verified; native builds remain required.',
          'project': project, 'package': package, 'revision': remote.get('rev'), 'srcmd5': remote.get('srcmd5'),
          'commit': manifest['commit'], 'changed_sources': changed, 'source_files_verified': len(expected_md5),
          'qualification': 'evidence/node-built-library-20261007.json',
          'publication_disabled': True, 'native_targets': ['openSUSE_Leap_16.0/x86_64', 'openSUSE_Leap_16.0/aarch64'],
          'files_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}}
(root / 'evidence/node-built-library-obs-20261007.json').write_text(json.dumps(record, indent=2) + '\n')
print('Verified OBS revision', record['revision'], 'srcmd5', record['srcmd5'], 'files', len(expected_md5))
