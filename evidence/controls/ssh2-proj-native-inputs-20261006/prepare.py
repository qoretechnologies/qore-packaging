# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib, importlib.util, json, subprocess, sys, urllib.request, xml.etree.ElementTree as E

root = Path.cwd()
out = root / 'results/ssh2-proj-native-inputs-20261006'
out.mkdir()
project = 'home:davidnichols:qore:testing'
sys.path.insert(0, str(root / 'tools'))
spec = importlib.util.spec_from_file_location('q', root / 'tools/qualify-installed.py')
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)
uploads = json.loads((root / 'results/ssh2-proj-final-uploads-20261006/results.json').read_text())

def api(path):
    return subprocess.check_output(['osc', '--setopt', 'http_retries=1', 'api', path], timeout=120)

modules = []
for mod in ('ssh2', 'proj'):
    repo = root / f'work/checkouts/module-{mod}-metadata-20261006'
    commit = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    source = json.loads(api(f'/source/{project}/qore-{mod}-module/source-manifest.json'))
    assert source['commit'] == commit and not source.get('candidate')
    fixtures = []
    for path in sorted(q.MODULE_FIXTURES[mod]):
        url = f'https://raw.githubusercontent.com/qoretechnologies/module-{mod}/{commit}/{path}'
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read()
        assert data == subprocess.check_output(['git', '-C', str(repo), 'show', commit + ':' + path])
        fixtures.append({'path': path, 'url': url, 'sha256': hashlib.sha256(data).hexdigest()})
    modules.append({'name': mod, 'commit': commit, 'fixtures': fixtures})

def prepare(case):
    target, repository = case
    directory = out / target
    directory.mkdir()
    manifest = json.loads((root / f'qualification/pgsql-{target}-aarch64.json').read_text())
    manifest['packages'] = [p for p in manifest['packages'] if p['name'] != 'qore-pgsql-module']
    for mod in ('geos', 'ssh2', 'proj'):
        base = f'/build/{project}/{repository}/aarch64/qore-{mod}-module'
        history = api(base + '/_history')
        (directory / (mod + '-history.xml')).write_bytes(history)
        if mod in uploads:
            assert E.fromstring(history)[-1].get('srcmd5') == uploads[mod]['srcmd5']
        listing = api(base)
        (directory / (mod + '-binaries.xml')).write_bytes(listing)
        name, = [e.get('filename') for e in E.fromstring(listing)
                 if e.get('filename', '').startswith(f'qore-{mod}-module-')
                 and e.get('filename', '').endswith('.aarch64.rpm')
                 and '-debug' not in e.get('filename', '')]
        data = api(base + '/' + name)
        (directory / name).write_bytes(data)
        manifest['packages'].append({'name': f'qore-{mod}-module', 'filename': name,
            'url': 'https://api.opensuse.org/public' + base + '/' + name, 'phase': 'runtime',
            'sha256': hashlib.sha256(data).hexdigest()})
    manifest['modules'] = modules
    q.validate(manifest)
    (root / f'qualification/ssh2-proj-{target}-aarch64.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return target

with ThreadPoolExecutor(max_workers=2) as pool:
    print(list(pool.map(prepare, [('fedora', 'Fedora_44'), ('leap', 'openSUSE_Leap_16.0')])))
