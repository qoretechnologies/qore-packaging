# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Preserve signed core21 inputs locally before OBS replaces their binary URLs."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from packaging import fetch_source

spec = importlib.util.spec_from_file_location('installed', ROOT / 'tools/qualify-installed.py')
installed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installed)
OUT = ROOT / 'results/core21-upgrade-baseline-20261008'
CACHE = ROOT / 'work/core21-upgrade-baseline-20261008'
OSC = ['osc', '--setopt', 'http_retries=1', '-A', 'https://api.opensuse.org', 'api']
PROJECT = 'home:davidnichols:qore:testing'
TARGETS = {'fedora': 'Fedora_44', 'leap': 'openSUSE_Leap_16.0', 'el10': 'AlmaLinux_10'}


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def choose_binary(package, arch, names):
    matches = [name for name in names if re.fullmatch(
        re.escape(package) + r'-[0-9][A-Za-z0-9+._~:-]*\.(?:' + arch + r'|noarch)\.rpm', name)]
    if len(matches) != 1:
        raise ValueError(f'Expected one binary for {package}/{arch}: {matches}')
    return matches[0]


def verify_identity(path, name, arch, db):
    actual = subprocess.check_output(
        ['rpm', '--dbpath', str(db), '-qp', '--qf', '%{NAME}\n%{ARCH}\n%{VERSION}\n', str(path)], text=True).splitlines()
    if len(actual) != 3 or actual[0] != name or actual[1] not in (arch, 'noarch'):
        raise ValueError(f'Unexpected RPM identity: {actual}')
    return actual


def preserve(pair):
    target, arch = pair
    record = OUT / f'{target}-{arch}'
    cache = CACHE / f'{target}-{arch}'
    record.mkdir()
    cache.mkdir(parents=True)
    origin = ROOT / f'qualification/core21-{target}-aarch64.json'
    manifest = installed.validate(json.loads(origin.read_text()))
    manifest = copy.deepcopy(manifest)
    manifest['arch'] = arch
    key = fetch_source(manifest['signing_key']['url'], manifest['signing_key']['sha256'], cache / 'key.asc')
    db = cache / 'rpmdb'
    subprocess.run(['rpm', '--dbpath', str(db), '--initdb'], check=True, capture_output=True)
    subprocess.run(['rpmkeys', '--dbpath', str(db), '--import', str(key)], check=True, capture_output=True)
    listings = {}
    sources = {}
    counts = 0
    total_bytes = 0
    for entry in manifest['packages']:
        source_package = entry['url'].split('/')[-2]
        base = f'/build/{PROJECT}/{TARGETS[target]}/{arch}/{source_package}'
        if source_package not in listings:
            info = subprocess.check_output([*OSC, base + '/_buildinfo'])
            (record / (source_package + '-buildinfo.xml')).write_bytes(info)
            parsed = ET.fromstring(info)
            if source_package == 'qore' and parsed.findtext('srcmd5') != manifest['obs_srcmd5']:
                raise ValueError('Core OBS source has changed')
            sources[source_package] = {'srcmd5': parsed.findtext('srcmd5'), 'revision': parsed.findtext('rev')}
            listing = subprocess.check_output([*OSC, base])
            (record / (source_package + '-binaries.xml')).write_bytes(listing)
            listings[source_package] = [x.attrib['filename'] for x in ET.fromstring(listing).findall('binary')]
        if arch == 'aarch64':
            if entry['filename'] not in listings[source_package]:
                raise ValueError('Previously qualified ARM artifact is no longer available')
            path = fetch_source(entry['url'], entry['sha256'], cache / entry['filename'])
        else:
            entry['filename'] = choose_binary(entry['name'], arch, listings[source_package])
            entry['url'] = 'https://api.opensuse.org/public' + base + '/' + entry['filename']
            path = cache / entry['filename']
            with tempfile.TemporaryDirectory(prefix='.download-', dir=cache) as temp:
                candidate = Path(temp) / 'candidate.rpm'
                with urllib.request.urlopen(entry['url'], timeout=60) as response, candidate.open('xb') as stream:
                    while block := response.read(1024 * 1024):
                        stream.write(block)
                verify_identity(candidate, entry['name'], arch, db)
                signature = subprocess.check_output(
                    ['rpmkeys', '--dbpath', str(db), '--checksig', '--verbose', str(candidate)], text=True)
                installed.require_rpm_signature(signature)
                os.link(candidate, path)
            entry['sha256'] = sha(path)
        actual = verify_identity(path, entry['name'], arch, db)
        if source_package == 'qore' and actual[2] != '3.0.0~git20261003.21':
            raise ValueError('Unexpected core baseline version')
        signature = subprocess.check_output(
            ['rpmkeys', '--dbpath', str(db), '--checksig', '--verbose', str(path)], text=True)
        installed.require_rpm_signature(signature)
        (record / (entry['filename'] + '.signature.txt')).write_text(signature)
        counts += 1
        total_bytes += path.stat().st_size
    for entry in manifest['fixtures']:
        fetch_source(entry['url'], entry['sha256'], cache / 'fixtures' / entry['path'])
    installed.validate(manifest)
    (record / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    result = {'target': target, 'arch': arch, 'packages': counts, 'bytes': total_bytes,
              'source_manifest_sha256': sha(origin), 'sources': sources,
              'cache': str(cache.relative_to(ROOT)),
              'scope': 'Signed snapshot only; upgrade/removal tests remain required.'}
    (record / 'status.json').write_text(json.dumps(result, indent=2) + '\n')
    return f'{target}-{arch}', result


def check_selection():
    names = ['qore-3.0.0~git20261003.21-21.1.x86_64.rpm',
             'qore-devel-3.0.0~git20261003.21-21.1.x86_64.rpm',
             'qore-3.0.0~git20261003.21-21.1.aarch64.rpm']
    assert choose_binary('qore', 'x86_64', names) == names[0]
    for invalid in [[], ['../qore-1-1.x86_64.rpm'], [names[2]], [names[0], names[0]],
                    ['qore-devel-1-1.x86_64.rpm']]:
        try:
            choose_binary('qore', 'x86_64', invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f'Invalid selection accepted: {invalid}')
    print('PASS: exact package selection and five ambiguous/unsafe/wrong-architecture controls')


if __name__ == '__main__':
    check_selection()
    OUT.mkdir()
    CACHE.mkdir()
    state = subprocess.check_output([*OSC, f'/build/{PROJECT}/_result?package=qore'])
    (OUT / 'core-state.xml').write_bytes(state)
    parsed = ET.fromstring(state)
    assert len(parsed.findall('result')) == 6
    assert all(x.find('status').get('code') == 'succeeded' for x in parsed.findall('result'))
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = dict(pool.map(preserve, [(t, a) for t in TARGETS for a in ('aarch64', 'x86_64')]))
    (OUT / 'status.json').write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps({key: {'packages': value['packages'], 'bytes': value['bytes']}
                      for key, value in results.items()}, indent=2))
