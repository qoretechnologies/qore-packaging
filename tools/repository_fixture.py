# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Temporary signed repositories for native package-manager qualification."""
from contextlib import contextmanager, ExitStack
import gzip
import hashlib
from pathlib import Path
import re
import shutil
import tempfile
import xml.etree.ElementTree as ET

NS = {'repo': 'http://linux.duke.edu/metadata/repo', 'pkg': 'http://linux.duke.edu/metadata/common'}


def check_metadata(directory, packages):
    """Require the generated index to describe exactly the pinned package bytes."""
    metadata = ET.parse(directory / 'repodata/repomd.xml').getroot()
    primary = None
    for entry in metadata.findall('repo:data', NS):
        checksum = entry.find('repo:checksum', NS)
        location = Path(entry.find('repo:location', NS).get('href'))
        if not location.parts or location.is_absolute() or '..' in location.parts or location.parts[0] != 'repodata':
            raise ValueError('Unsafe repository metadata location')
        path = directory / location
        if checksum.get('type') != 'sha256' or hashlib.sha256(path.read_bytes()).hexdigest() != checksum.text:
            raise ValueError('Repository metadata checksum mismatch')
        if entry.get('type') == 'primary':
            if primary is not None:
                raise ValueError('Duplicate primary repository index')
            primary = ET.fromstring(gzip.decompress(path.read_bytes()))
    if primary is None:
        raise ValueError('Missing primary repository index')
    actual = {}
    for entry in primary.findall('pkg:package', NS):
        name = entry.findtext('pkg:name', namespaces=NS)
        checksum = entry.find('pkg:checksum', NS)
        if name in actual or checksum.get('type') != 'sha256':
            raise ValueError('Duplicate package or unsupported package checksum')
        actual[name] = (entry.find('pkg:location', NS).get('href'), checksum.text)
    expected = {entry['name']: (entry['filename'], entry['sha256']) for entry in packages}
    if actual != expected or int(primary.get('packages')) != len(packages):
        raise ValueError('Repository contents differ from the pinned package manifest')


def refresh_command(family, alias):
    if family == 'suse':
        return ['zypper', '--non-interactive', 'refresh', '--force', alias]
    return ['dnf', '-y', '--disablerepo=*', '--enablerepo=' + alias, 'makecache', '--refresh']


def check_signature_rejection(returncode, text):
    if returncode == 0 or not re.search(
            r'Bad PGP signature|Signature verification failed for (?:file .)?repomd\.xml', text, re.I):
        raise ValueError('Package manager did not reject the altered metadata signature')


def requested_packages(manifest, phase):
    if phase == 'runtime':
        return ['qore', *['qore-' + module['name'] + '-module' for module in manifest.get('modules', [])]]
    return [entry['name'] for entry in manifest['packages'] if entry['phase'] == 'sdk']


def verify_selected_versions(packages, directory, run):
    """Compare all installed identities with the exact downloaded RPM headers."""
    fmt = '%{NAME} %{EPOCHNUM}:%{VERSION}-%{RELEASE}.%{ARCH}\n'
    for entry in packages:
        name = entry['name']
        expected = run('repository-header-' + name,
                       ['rpm', '-qp', '--qf', fmt, str(directory / entry['filename'])])
        actual = run('repository-selected-' + name, ['rpm', '-q', '--qf', fmt, name])
        if not expected.startswith(name + ' ') or len(expected.splitlines()) != 1 or actual != expected:
            raise ValueError('Repository solver selected an unexpected build of ' + name)


def _write_config(directory, alias, repository, metadata_key, package_key, stack):
    path = directory / (alias + '.repo')
    with path.open('x') as stream:
        stack.callback(path.unlink)
        stream.write(f'[{alias}]\nname=Qore signed repository qualification\n'
                     f'baseurl={repository.as_uri()}\nenabled=1\ngpgcheck=1\nrepo_gpgcheck=1\n'
                     f'pkg_gpgcheck=1\nskip_if_unavailable=0\n'
                     f'gpgkey={metadata_key.as_uri()} {package_key.as_uri()}\n')
    return path


@contextmanager
def signed_repository(manifest, directory, key, output, run, environment, config_directory=None):
    """Expose verified RPMs through signed metadata; always remove fixture configs."""
    directory = directory.resolve()
    output = output.resolve()
    family = manifest['family']
    config_directory = config_directory or Path('/etc/zypp/repos.d' if family == 'suse' else '/etc/yum.repos.d')
    run('repository-create', ['createrepo_c', '--checksum', 'sha256', '--general-compress-type', 'gz',
                             '--revision', '1', '--set-timestamp-to-revision', '--workers', '2', str(directory)])
    check_metadata(directory, manifest['packages'])
    public_key = directory.parent / 'metadata-public-key.asc'
    repomd = directory / 'repodata/repomd.xml'
    with tempfile.TemporaryDirectory(prefix='qore-fixture-key-', dir=directory.parent) as temporary:
        signer = Path(temporary)
        signer.chmod(0o700)
        gpg = ['gpg', '--batch', '--homedir', str(signer)]
        try:
            run('repository-key-create', [*gpg, '--pinentry-mode', 'loopback', '--passphrase', '',
                '--quick-generate-key', 'Qore repository qualification <rpm-test@example.invalid>',
                'rsa3072', 'sign', '30d'])
            keys = run('repository-key-list', [*gpg, '--with-colons', '--list-keys'])
            fingerprints = [line.split(':')[9] for line in keys.splitlines() if line.startswith('fpr:')]
            if len(fingerprints) != 1 or not re.fullmatch('[A-F0-9]{40}', fingerprints[0]):
                raise ValueError('Expected exactly one fixture signing key')
            run('repository-key-export', [*gpg, '--armor', '--output', str(public_key), '--export', fingerprints[0]])
            run('repository-sign', [*gpg, '--armor', '--output', str(repomd) + '.asc', '--detach-sign', str(repomd)])
            run('repository-verify', [*gpg, '--verify', str(repomd) + '.asc', str(repomd)])
        finally:
            run('repository-agent-stop', ['gpgconf', '--homedir', str(signer), '--kill', 'gpg-agent'])
    # Keep only public evidence after signing; private key material is already removed.
    shutil.copyfile(public_key, directory / 'repodata/repomd.xml.key')
    shutil.copytree(directory / 'repodata', output / 'repodata')
    shutil.copyfile(public_key, output / public_key.name)
    run('repository-import-key', ['rpm', '--import', str(public_key)])
    alias = 'qore-qualification-' + directory.parent.name
    with ExitStack() as configs:
        _write_config(config_directory, alias, directory, public_key, key, configs)
        with tempfile.TemporaryDirectory(prefix='bad-repository-', dir=directory.parent) as temporary:
            bad = Path(temporary)
            shutil.copytree(directory / 'repodata', bad / 'repodata')
            with (bad / 'repodata/repomd.xml').open('ab') as stream:
                stream.write(b'\n<!-- signature negative control -->\n')
            with ExitStack() as bad_config:
                _write_config(config_directory, alias + '-bad', bad, public_key, key, bad_config)
                run('repository-reject-tampered', refresh_command(family, alias + '-bad'),
                    env=environment, reject_signature=True)
        run('repository-refresh', refresh_command(family, alias), env=environment)
        yield {'alias': alias, 'metadata_key_fingerprint': fingerprints[0],
               'metadata_public_key_sha256': hashlib.sha256(public_key.read_bytes()).hexdigest(),
               'private_key_retained': False, 'metadata_signature': 'ephemeral fixture key; not production publication'}
