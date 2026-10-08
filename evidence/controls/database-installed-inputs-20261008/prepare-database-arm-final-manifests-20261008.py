# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET

root = Path.cwd()
sys.path.insert(0, str(root / 'tools'))
spec = importlib.util.spec_from_file_location('installed', root / 'tools/qualify-installed.py')
installed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installed)
out = root / 'results/database-arm-final-inputs-20261008'
out.mkdir()
osc = ['osc', '--setopt', 'http_retries=1', '-A', 'https://api.opensuse.org', 'api']
project = 'home:davidnichols:qore:testing'
modules = {'freetds': ('2b35358523ff5f397e415203e0df37d38825e8eb', '0a6609cafba14c4f8565406398891349'),
           'mysql': ('c7ba6b020d76a463d047608eafee5218da0f3c97', '7dc222c580734eedded83d7b861dda4c')}
for name in modules:
    data = subprocess.check_output([*osc, f'/build/{project}/_result?package=qore-{name}-module'])
    (out / (name + '-results.xml')).write_bytes(data)
    result = ET.fromstring(data)
    assert len(result.findall('result')) == 6
    assert all(r.find('status').attrib['code'] == 'succeeded' for r in result.findall('result')), data
fixtures = {}
for name, (commit, _) in modules.items():
    repository = 'module-' + installed.MODULE_REPOSITORIES.get(name, name)
    fixtures[name] = []
    for path in sorted(installed.MODULE_FIXTURES[name]):
        local = subprocess.check_output(['git', 'show', commit + ':' + path], cwd=root.parent / repository)
        url = f'https://raw.githubusercontent.com/qoretechnologies/{repository}/{commit}/{path}'
        with urllib.request.urlopen(url, timeout=90) as response:
            assert response.read() == local, url
        fixtures[name].append({'path': path, 'url': url, 'sha256': hashlib.sha256(local).hexdigest()})


def prepare(pair):
    target, repository = pair
    folder = out / target
    folder.mkdir()
    manifest = json.loads((root / f'qualification/core21-{target}-aarch64.json').read_text())
    assert 'modules' not in manifest
    manifest['modules'] = []
    sources = {}
    for name, (commit, expected) in modules.items():
        base = f'/build/{project}/{repository}/aarch64/qore-{name}-module'
        info = subprocess.check_output([*osc, base + '/_buildinfo'])
        (folder / (name + '-buildinfo.xml')).write_bytes(info)
        assert ET.fromstring(info).findtext('srcmd5') == expected
        listing = subprocess.check_output([*osc, base])
        (folder / (name + '-binaries.xml')).write_bytes(listing)
        names = [row.attrib['filename'] for row in ET.fromstring(listing).findall('binary')]
        for package in ['qore-' + name + '-module', 'qore-' + name + '-module-doc']:
            matches = [n for n in names if re.fullmatch(re.escape(package) + r'-[0-9].*\.(aarch64|noarch)\.rpm', n)]
            assert len(matches) == 1, (package, matches)
            filename = matches[0]
            url = 'https://api.opensuse.org/public' + base + '/' + filename
            with urllib.request.urlopen(url, timeout=90) as response:
                data = response.read()
            (folder / filename).write_bytes(data)
            manifest['packages'].append({'name': package, 'url': url, 'filename': filename,
                                        'sha256': hashlib.sha256(data).hexdigest(), 'phase': 'runtime'})
        manifest['modules'].append({'name': name, 'commit': commit, 'fixtures': fixtures[name]})
        sources[name] = {'commit': commit, 'srcmd5': expected, 'build_revision': ET.fromstring(info).findtext('rev')}
    installed.validate(manifest)
    path = root / f'qualification/databases-{target}-aarch64.json'
    path.write_text(json.dumps(manifest, indent=2) + '\n')
    return target, {'manifest': str(path.relative_to(root)), 'sources': sources}

with ThreadPoolExecutor(max_workers=3) as pool:
    results = dict(pool.map(prepare, [('fedora', 'Fedora_44'), ('leap', 'openSUSE_Leap_16.0'), ('el10', 'AlmaLinux_10')]))
(out / 'status.json').write_text(json.dumps(results, indent=2) + '\n')
print('PASS: six native source builds per module; fixture URLs verified; three signed-package qualification manifests prepared')
