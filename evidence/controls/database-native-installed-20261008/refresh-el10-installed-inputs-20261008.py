# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET

root = Path.cwd()
out = root / 'results/el10-installed-refreshed-inputs-20261008'
out.mkdir(exist_ok=True)
sys.path.insert(0, str(root / 'tools'))
spec = importlib.util.spec_from_file_location('installed', root / 'tools/qualify-installed.py')
installed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installed)
paths = [root / f'qualification/{n}-el10-aarch64.json' for n in ['core21', 'databases', 'pgsql']]
manifests = {p: json.loads(p.read_text()) for p in paths}
osc = ['osc', '--setopt', 'http_retries=1', '-A', 'https://api.opensuse.org', 'api']
entries = {}
for manifest in manifests.values():
    for p in manifest['packages']:
        base = urlsplit(p['url']).path.rsplit('/', 1)[0]
        assert base.startswith('/public/build/home:davidnichols:qore:testing/AlmaLinux_10/aarch64/')
        entries.setdefault(base, {})[p['name']] = p

def refresh(item):
    base, entries = item
    source_package = base.rsplit('/', 1)[1]
    folder = out / source_package
    folder.mkdir(exist_ok=True)
    api_base = base.removeprefix('/public')
    info = ((folder / 'buildinfo.xml').read_bytes() if (folder / 'buildinfo.xml').exists()
            else subprocess.check_output([*osc, api_base + '/_buildinfo']))
    (folder / 'buildinfo.xml').write_bytes(info)
    parsed = ET.fromstring(info)
    if source_package == 'qore':
        assert parsed.findtext('srcmd5') == next(iter(manifests.values()))['obs_srcmd5']
    listing = ((folder / 'binaries.xml').read_bytes() if (folder / 'binaries.xml').exists()
               else subprocess.check_output([*osc, api_base]))
    (folder / 'binaries.xml').write_bytes(listing)
    names = [b.attrib['filename'] for b in ET.fromstring(listing).findall('binary')]
    updated = {}
    for name, old in entries.items():
        matches = [n for n in names if re.fullmatch(re.escape(name) + r'-[0-9].*\.(aarch64|noarch)\.rpm', n)]
        assert len(matches) == 1, (name, matches)
        filename, = matches
        url = 'https://api.opensuse.org' + base + '/' + filename
        if (folder / filename).exists():
            data = (folder / filename).read_bytes()
        else:
            with urllib.request.urlopen(url, timeout=120) as response:
                data = response.read()
        (folder / filename).write_bytes(data)
        updated[name] = {**old, 'filename': filename, 'url': url, 'sha256': hashlib.sha256(data).hexdigest()}
    return base, {'source_package': source_package, 'revision': parsed.findtext('rev'),
                  'srcmd5': parsed.findtext('srcmd5'), 'packages': updated}

with ThreadPoolExecutor(max_workers=4) as pool:
    results = dict(pool.map(refresh, entries.items()))
(out / 'sources.json').write_text(json.dumps(results, indent=2) + '\n')
for path, manifest in manifests.items():
    for i, entry in enumerate(manifest['packages']):
        base = urlsplit(entry['url']).path.rsplit('/', 1)[0]
        manifest['packages'][i] = results[base]['packages'][entry['name']]
    for module in manifest.get('modules', []):
        # Fixture-only follow-up commits can be newer than the packaged source.
        # Preserve the separately qualified immutable fixture revision.
        for fixture in module['fixtures']:
            with urllib.request.urlopen(fixture['url'], timeout=90) as response:
                data = response.read()
            fixture['sha256'] = hashlib.sha256(data).hexdigest()
            repository = 'module-' + installed.MODULE_REPOSITORIES.get(module['name'], module['name'])
            repo = root.parent / repository
            local = subprocess.check_output(['git', '-C', str(repo), 'show', module['commit'] + ':' + fixture['path']])
            assert data == local
    installed.validate(manifest)
    path.write_text(json.dumps(manifest, indent=2) + '\n')
print('PASS: every RPM downloaded and hashed; immutable fixture bytes verified; three EL10 manifests refreshed')
