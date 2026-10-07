# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import concurrent.futures
import hashlib
import importlib.util
import json
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET

root = Path.cwd()
project = 'home:davidnichols:qore:testing'
output = root / 'results/jni-native-inputs-20261007'
output.mkdir(exist_ok=True)
sys.path.insert(0, str(root / 'tools'))
spec = importlib.util.spec_from_file_location('qualify', root / 'tools/qualify-installed.py')
qualify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qualify)
catalog = json.loads((root / 'catalog.json').read_text())['packages']

def api(path):
    return subprocess.check_output(['osc', '--setopt', 'http_retries=1', 'api', path], timeout=180)

sources = {}
for name in ('jni', 'xml', 'python', 'process'):
    base = f'/source/{project}/qore-{name}-module'
    manifest = json.loads(api(base + '/source-manifest.json'))
    listing = api(base)
    (output / (name + '-source.xml')).write_bytes(listing)
    assert manifest['commit'] == catalog['module-' + name]['commit'] and not manifest.get('candidate')
    sources[name] = {'commit': manifest['commit'], 'srcmd5': ET.fromstring(listing).get('srcmd5')}

def fixture(path):
    commit = sources['jni']['commit']
    expected = subprocess.check_output(['git', '-C', str(root.parent / 'module-jni'), 'show', commit + ':' + path])
    url = f'https://raw.githubusercontent.com/qoretechnologies/module-jni/{commit}/{path}'
    with urllib.request.urlopen(url, timeout=60) as response:
        data = response.read()
    assert data == expected, path
    return {'path': path, 'url': url, 'sha256': hashlib.sha256(data).hexdigest()}

with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    fixtures = list(pool.map(fixture, sorted(qualify.MODULE_FIXTURES['jni'])))

def prepare(item):
    target, repository, arch = item
    manifest = json.loads((root / f'qualification/core21-{target}-aarch64.json').read_text())
    manifest['arch'] = arch
    directory = output / (target + '-' + arch)
    directory.mkdir(exist_ok=True)
    groups = {}
    for entry in manifest['packages']:
        group = entry['url'].split('/')[-2]
        groups.setdefault(group, {})[entry['name']] = entry['phase']
    for name in ('jni', 'xml', 'python', 'process'):
        groups['qore-' + name + '-module'] = {'qore-' + name + '-module': 'runtime'}
    groups['qore-jni-module'].update({'qore-jni-tools': 'sdk', 'qore-jni-kotlin': 'sdk'})
    packages = []
    for group, names in groups.items():
        base = f'/build/{project}/{repository}/{arch}/{group}'
        listing = api(base)
        (directory / (group + '-binaries.xml')).write_bytes(listing)
        if group == 'qore' or group.startswith('qore-'):
            history = api(base + '/_history')
            (directory / (group + '-history.xml')).write_bytes(history)
            expected = manifest['obs_srcmd5'] if group == 'qore' else sources[group[5:-7]]['srcmd5']
            assert ET.fromstring(history)[-1].get('srcmd5') == expected, (target, arch, group)
        for name, phase in names.items():
            candidates = [entry.get('filename') for entry in ET.fromstring(listing)
                          if entry.get('filename', '').endswith(('.' + arch + '.rpm', '.noarch.rpm'))
                          and entry.get('filename', '').rsplit('-', 2)[0] == name]
            assert len(candidates) == 1, (target, arch, name, candidates)
            filename = candidates[0]
            data = api(base + '/' + filename)
            (directory / filename).write_bytes(data)
            packages.append({'name': name, 'url': 'https://api.opensuse.org/public' + base + '/' + filename,
                             'filename': filename, 'sha256': hashlib.sha256(data).hexdigest(), 'phase': phase})
    manifest['packages'] = packages
    manifest['modules'] = [{'name': 'jni', 'commit': sources['jni']['commit'], 'fixtures': fixtures}]
    qualify.validate(manifest)
    destination = (root / 'qualification' if arch == 'aarch64' else root / 'work') / f'jni-{target}-{arch}.json'
    destination.write_text(json.dumps(manifest, indent=2) + '\n')
    return str(destination.relative_to(root))

items = [(target, repo, arch) for arch in ('aarch64', 'x86_64')
         for target, repo in (('fedora', 'Fedora_44'), ('leap', 'openSUSE_Leap_16.0'), ('el10', 'AlmaLinux_10'))]
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    for path in pool.map(prepare, items):
        print(path, flush=True)
(output / 'sources.json').write_text(json.dumps(sources, indent=2) + '\n')
