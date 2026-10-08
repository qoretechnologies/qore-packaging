# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Read-only reconciliation of catalog pins against OBS source manifests."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET

root = Path.cwd()
out = root / 'results/obs-catalog-delivery-20261008'
out.mkdir(exist_ok=True)
catalog = json.loads((root / 'catalog.json').read_text())['packages']
project = 'home:davidnichols:qore:testing'
osc = ['osc', '--setopt', 'http_retries=1', '-A', 'https://api.opensuse.org', 'api']

def get(path, filename):
    cached = out / filename
    if cached.is_file():
        error = out / (filename + ".stderr")
        stderr = error.read_bytes() if error.is_file() else b""
        return subprocess.CompletedProcess([*osc, path], 1 if b"404" in stderr else 0, cached.read_bytes(), stderr)
    result = subprocess.run([*osc, path], capture_output=True)
    (out / filename).write_bytes(result.stdout)
    if result.stderr:
        (out / (filename + '.stderr')).write_bytes(result.stderr)
    return result

def check(item):
    name, entry = item
    recipe_result = subprocess.run(['git', 'show', entry['commit'] + ':' + entry['spec']],
                                   cwd=root.parent / name, text=True, capture_output=True)
    if recipe_result.returncode:
        assert entry['status'] == 'inventory' and 'not in' in recipe_result.stderr, recipe_result.stderr
        # Inventory-only entries have no pinned spec yet; query the declared candidate name.
        package = Path(entry['spec']).stem
    else:
        names = re.findall(r'^Name:\s+([a-zA-Z0-9+._-]+)\s*$', recipe_result.stdout, re.M)
        assert len(names) == 1, (name, names)
        package = names[0]
    base = f'/source/{project}/{package}'
    result = get(base, package + '-source.xml')
    if result.returncode:
        assert b'404' in result.stderr, result.stderr.decode()
        return name, {'package': package, 'catalog_commit': entry['commit'], 'status': 'not uploaded'}
    source = ET.fromstring(result.stdout)
    revision = source.attrib['rev']
    manifest_result = get(base + '/source-manifest.json?rev=' + revision, package + '-manifest.json')
    assert manifest_result.returncode == 0, manifest_result.stderr.decode()
    manifest_entry = source.find("entry[@name='source-manifest.json']")
    assert manifest_entry is not None
    assert hashlib.md5(manifest_result.stdout).hexdigest() == manifest_entry.attrib['md5']
    manifest = json.loads(manifest_result.stdout)
    actual = {element.attrib['name']: element.attrib['md5'] for element in source.findall('entry')}
    assert set(actual) == set(manifest['sources']) | {'source-manifest.json'}, package
    meta_result = get(base + '/_meta', package + '-meta.xml')
    assert meta_result.returncode == 0, meta_result.stderr.decode()
    metadata = ET.fromstring(meta_result.stdout)
    publish = metadata.find('publish')
    assert publish is None or all(flag.tag == 'disable' for flag in publish), package
    flags = [dict(action=flag.tag, **flag.attrib) for flag in metadata.findall('build/*')]
    return name, {'package': package, 'catalog_commit': entry['commit'], 'obs_commit': manifest['commit'],
                  'revision': revision, 'srcmd5': source.attrib['srcmd5'], 'build_flags': flags,
                  'manifest_md5_verified': True,
                  'status': 'matching pin' if entry['commit'] == manifest['commit'] else 'pin mismatch'}

with ThreadPoolExecutor(max_workers=5) as pool:
    records = dict(pool.map(check, catalog.items()))
project_result = get('/source/' + project + '/_meta', 'project-meta.xml')
assert project_result.returncode == 0
publish = ET.fromstring(project_result.stdout).find('publish')
assert len(publish) == 1 and publish[0].tag == 'disable' and not publish[0].attrib
snapshot = ET.parse(root / 'results/obs-current-20261008.xml').getroot()
for result in snapshot.findall('result'):
    for status in result.findall('status'):
        for record in records.values():
            if record['package'] == status.attrib.get('package'):
                record.setdefault('recorded_build_states', {})[result.attrib['repository'] + '/' + result.attrib['arch']] = status.attrib['code']
report = {'date': '2026-10-08', 'project': project, 'publication': 'disabled',
          'scope': 'Catalog pins and exact source-manifest MD5; source archive SHA-256 and installed tests remain governed by qualification records.',
          'build_snapshot': 'results/obs-current-20261008.xml; this inventory makes no new build-status poll',
          'packages': records}
(out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'packages': len(records), 'matching_pins': sum(r['status'] == 'matching pin' for r in records.values()),
                  'exceptions': {n: r['status'] for n, r in records.items() if r['status'] != 'matching pin'}}, indent=2))
