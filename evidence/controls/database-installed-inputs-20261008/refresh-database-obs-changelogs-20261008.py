# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import importlib.util
import json
import subprocess
import tarfile
import hashlib
import sys
import xml.etree.ElementTree as ET

root = Path.cwd()
sys.path.insert(0, str(root / 'tools'))
import packaging
out = root / 'results/database-obs-changelogs-20261008'
out.mkdir(exist_ok=True)
rows = []
for name, repository, spec in [('freetds', 'module-sybase', 'qore-sybase-modules.spec'),
                                ('mysql', 'module-mysql', 'qore-mysql-module.spec')]:
    old = json.loads((root / f'results/obs-catalog-delivery-20261008/qore-{name}-module-manifest.json').read_text())
    source = root / f'work/{name}-obs-changelog-20261008'
    new = (json.loads((source / 'source-manifest.json').read_text()) if source.exists() else
           packaging.prepare_source(root.parent / repository, old['commit'], old['name'], old['version'],
                                    source, exclusions=old['exclusions'], spec_path=spec))
    archive = old['name'] + '-' + old['version'] + '.tar.xz'
    previous = root / ('work/freetds-source-final-1' if name == 'freetds' else 'work/mysql-final-source-2')
    for path, digest in old['sources'].items():
        assert hashlib.sha256((previous / path).read_bytes()).hexdigest() == digest, path
        if path != archive:
            assert new['sources'][path] == digest
    permission_changes = []
    with tarfile.open(previous / archive) as a, tarfile.open(source / archive) as b:
        left, right = {m.name: m for m in a}, {m.name: m for m in b}
        assert set(left) == set(right)
        for path in sorted(left):
            x, y = left[path], right[path]
            for field in ['uid', 'gid', 'uname', 'gname', 'mtime', 'linkname', 'type', 'pax_headers', 'size']:
                assert getattr(x, field) == getattr(y, field), (path, field)
            if x.mode != y.mode:
                assert y.mode == x.mode & ~0o022, (path, x.mode, y.mode)
                permission_changes.append({'path': path, 'before': oct(x.mode), 'after': oct(y.mode)})
            if x.isfile():
                assert a.extractfile(x).read() == b.extractfile(y).read(), path
    (out / (name + '-archive-permission-changes.json')).write_text(json.dumps(permission_changes, indent=2) + '\n')
    assert set(new['sources']) - set(old['sources']) == {old['name'] + '.changes'}
    assert {k: v for k, v in old.items() if k != 'sources'} == {k: v for k, v in new.items() if k != 'sources'}
    command = ['python3', '-B', '-W', 'error', 'tools/obs.py', 'upload', '--project',
               'home:davidnichols:qore:testing', '--source', str(source), '--apply']
    with (out / (name + '-upload.log')).open('x') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    assert result.returncode == 0
    api = ['osc', '--setopt', 'http_retries=1', '-A', 'https://api.opensuse.org', 'api']
    base = '/source/home:davidnichols:qore:testing/' + old['name']
    listing = subprocess.check_output([*api, base])
    (out / (name + '-source.xml')).write_bytes(listing)
    info = ET.fromstring(listing)
    remote = subprocess.check_output([*api, base + '/source-manifest.json?rev=' + info.attrib['rev']])
    assert json.loads(remote) == new
    (out / (name + '-manifest.json')).write_bytes(remote)
    metadata = subprocess.check_output([*api, base + '/_meta'])
    (out / (name + '-meta.xml')).write_bytes(metadata)
    assert [e.tag for e in ET.fromstring(metadata).find('publish')] == ['disable']
    rows.append({'module': name, 'source_commit': old['commit'], 'revision': info.attrib['rev'],
                 'srcmd5': info.attrib['srcmd5'], 'source_bytes_and_spec_unchanged': True, 'normalized_archive_permissions': len(permission_changes),
                 'change': 'Add the generated .changes sidecar; current canonical preparation also removes group/other write permission from source archive entries. All source bytes, other metadata and spec are unchanged.', 'source': str(source.relative_to(root))})
    print(name, 'uploaded revision', info.attrib['rev'], info.attrib['srcmd5'], flush=True)
(out / 'status.json').write_text(json.dumps(rows, indent=2) + '\n')
