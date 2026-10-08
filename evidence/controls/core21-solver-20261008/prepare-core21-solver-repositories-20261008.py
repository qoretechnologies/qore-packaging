# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Prepare local signed metadata for the six pinned baseline package sets."""
from pathlib import Path
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'results/core21-solver-repositories-20261008'
REPOS = ROOT / 'work/core21-solver-repositories-20261008'
REVISION = '1791417600'
NS = {'repo': 'http://linux.duke.edu/metadata/repo', 'common': 'http://linux.duke.edu/metadata/common'}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def run(command, log):
    with log.open('x') as stream:
        result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT)
    result.check_returncode()


def check_metadata(directory, manifest):
    root = ET.parse(directory / 'repodata/repomd.xml').getroot()
    assert root.findtext('repo:revision', namespaces=NS) == REVISION
    primary = None
    for entry in root.findall('repo:data', NS):
        checksum = entry.find('repo:checksum', NS)
        assert checksum.get('type') == 'sha256'
        relative = Path(entry.find('repo:location', NS).get('href'))
        assert not relative.is_absolute() and '..' not in relative.parts and relative.parts[0] == 'repodata'
        path = directory / relative
        assert digest(path) == checksum.text
        if entry.get('type') == 'primary':
            primary = ET.fromstring(gzip.decompress(path.read_bytes()))
    assert primary is not None and int(primary.get('packages')) == len(manifest['packages'])
    actual = {}
    for entry in primary.findall('common:package', NS):
        name = entry.findtext('common:name', namespaces=NS)
        checksum = entry.find('common:checksum', NS)
        assert checksum.get('type') == 'sha256' and name not in actual
        actual[name] = (entry.find('common:location', NS).get('href'), checksum.text)
    assert actual == {e['name']: ('Packages/' + e['filename'], e['sha256']) for e in manifest['packages']}
    return len(actual)


OUT.mkdir()
REPOS.mkdir()
results = {}
with tempfile.TemporaryDirectory(prefix='core21-qualification-key-', dir=ROOT / 'work') as temporary:
    signer = Path(temporary)
    signer.chmod(0o700)
    gpg = ['gpg', '--batch', '--homedir', str(signer)]
    run([*gpg, '--pinentry-mode', 'loopback', '--passphrase', '', '--quick-generate-key',
         'Qore local repository qualification <rpm-qualification@example.invalid>', 'rsa3072', 'sign', '1d'],
        OUT / 'key-generation.log')
    listing = subprocess.check_output([*gpg, '--with-colons', '--list-keys'], text=True)
    fingerprints = [line.split(':')[9] for line in listing.splitlines() if line.startswith('fpr:')]
    assert len(fingerprints) == 1 and re.fullmatch('[0-9A-F]{40}', fingerprints[0])
    fingerprint = fingerprints[0]
    public_key = subprocess.check_output([*gpg, '--armor', '--export', fingerprint])
    (OUT / 'metadata-public-key.asc').write_bytes(public_key)
    for source in sorted((ROOT / 'results/core21-upgrade-baseline-20261008').glob('*/manifest.json')):
        name = source.parent.name
        manifest = json.loads(source.read_text())
        cache = ROOT / 'work/core21-upgrade-baseline-20261008' / name
        directory = REPOS / name
        packages = directory / 'Packages'
        packages.mkdir(parents=True)
        record = OUT / name
        record.mkdir()
        for entry in manifest['packages']:
            path = cache / entry['filename']
            assert digest(path) == entry['sha256']
            os.link(path, packages / entry['filename'])
        (directory / 'metadata-public-key.asc').write_bytes(public_key)
        shutil.copyfile(cache / 'key.asc', directory / 'package-public-key.asc')
        assert digest(directory / 'package-public-key.asc') == manifest['signing_key']['sha256']
        command = ['createrepo_c', '--checksum', 'sha256', '--general-compress-type', 'gz',
                   '--revision', REVISION, '--set-timestamp-to-revision', '--workers', '2', str(directory)]
        run(command, record / 'createrepo.log')
        count = check_metadata(directory, manifest)
        repomd = directory / 'repodata/repomd.xml'
        signature = repomd.with_suffix('.xml.asc')
        run([*gpg, '--armor', '--local-user', fingerprint, '--output', str(signature),
             '--detach-sign', str(repomd)], record / 'sign.log')
        (directory / 'repodata/repomd.xml.key').write_bytes(public_key)
        run([*gpg, '--verify', str(signature), str(repomd)], record / 'verify.log')
        altered = record / 'altered-repomd.xml'
        altered.write_bytes(repomd.read_bytes() + b'\n<!-- tampered metadata negative control -->\n')
        process = subprocess.run([*gpg, '--verify', str(signature), str(altered)], capture_output=True, text=True)
        (record / 'tampered-verification.log').write_text(process.stdout + process.stderr)
        assert process.returncode == 1 and 'BAD signature' in process.stderr
        shutil.copyfile(repomd, record / 'repomd.xml')
        shutil.copyfile(signature, record / 'repomd.xml.asc')
        results[name] = {'packages': count, 'repository': str(directory.relative_to(ROOT)),
                         'manifest': str(source.relative_to(ROOT)), 'manifest_sha256': digest(source),
                         'repomd_sha256': digest(repomd), 'signature_sha256': digest(signature),
                         'tampered_metadata_rejected': True,
                         'metadata_files': {str(p.relative_to(directory)): digest(p)
                                            for p in sorted((directory / 'repodata').iterdir()) if p.is_file()}}
    run(['gpgconf', '--homedir', str(signer), '--kill', 'gpg-agent'], OUT / 'agent-stop.log')
record = {'schema': 1, 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
          'targets': results, 'temporary_metadata_key_fingerprint': fingerprint,
          'metadata_public_key_sha256': digest(OUT / 'metadata-public-key.asc'),
          'private_key_retained': False,
          'scope': 'Local solver fixtures only. RPMs retain their original OBS signatures; metadata uses an ephemeral test key. No OBS configuration/publication change or production repository signature claim.'}
(OUT / 'status.json').write_text(json.dumps(record, indent=2) + '\n')
print('PASS: six local signed repositories, 86 exact package checksums and six tampered-metadata rejections')
