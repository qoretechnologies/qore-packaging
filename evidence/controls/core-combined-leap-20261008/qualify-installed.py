# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

root = Path('/home/david/src/qore/git/qore-packaging')
os.chdir(root)
target = sys.argv[1]
launch = {'output': f'results/{target}-core-fixes-combined-candidate-20261008'}
result = Path(f'results/{target}-core-combined-candidate-installed-20261008.json')
status = {'source_build': launch['output'], 'steps': {}, 'pid': os.getpid(), 'qualification_only': True}


def save():
    temporary = result.with_suffix('.tmp')
    temporary.write_text(json.dumps(status, indent=2) + '\n')
    temporary.replace(result)


def run(step, command):
    stem = f'{target}-core-combined-candidate-{step}-20261008'
    Path(f'results/{stem}-command.json').write_text(json.dumps(command, indent=2) + '\n')
    with Path(f'results/{stem}.log').open('w') as log:
        completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    status['steps'][step] = {'exit_code': completed.returncode, 'log': f'results/{stem}.log'}
    save()
    completed.check_returncode()


try:
    build_dir = (root / launch['output']).resolve()
    build = json.loads((build_dir / 'build.json').read_text())
    assert build.get('exit_code') == 0, build.get('exit_code')
    assert build['source']['commit'] == 'd740af66e7fcff19433b94aca94ad5aa41e656f1'
    assert build['source']['candidate'] is True
    assert len(build['source']['source_overlay']) == 65
    status['source'] = build['source']
    status['artifacts'] = build['artifacts']
    for name, expected in build['artifacts'].items():
        with (build_dir / name).open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == expected, name
    source_dir = root / f'work/{target}-core-combined-candidate-fixtures-3'
    source_dir.mkdir()
    bundle = root / 'work/core-fixes-combined-candidate-20261008'
    manifest = json.loads((bundle / 'source-manifest.json').read_text())
    assert manifest == build['source']
    archive_name, = [name for name in manifest['sources'] if name.endswith('.tar.xz')]
    with (bundle / archive_name).open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == manifest['sources'][archive_name]
    with tarfile.open(bundle / archive_name) as archive:
        members = [member for member in archive.getmembers()
                   if '/rpm/tests-installed/' in member.name
                   or member.name.endswith('/modules/ml/test/data/test_linear.onnx')]
        archive.extractall(source_dir, members=members, filter='data')
    source, = source_dir.iterdir()
    packages = {Path(name).name.rsplit('-', 2)[0]: '/rpms/' + name
                for name in build['artifacts'] if '/RPMS/' in name}
    library = 'libqore20' if target == 'leap' else 'libqore'
    previous = json.loads(Path(f'results/{target}-core-policy-21-installed-3.json').read_text())
    assert previous['exit_code'] == 0
    bases = {target: (previous['sdk_image'], previous['runtime_image'])}
    install = ('zypper --non-interactive --no-refresh --no-gpg-checks install --no-recommends --allow-unsigned-rpm'
               if target == 'leap' else 'dnf -y --setopt=install_weak_deps=False install')
    common = ['docker', 'run', '--init', '-v', str(build_dir) + ':/rpms:ro', '-v', str(source) + ':/source:ro']
    for mode, base in zip(('sdk', 'runtime'), bases[target]):
        names = ['qore', library, 'qore-stdlib']
        if mode == 'sdk':
            names += ['qore-devel', 'qore-rpm-macros', 'qore-misc-tools', 'qore-debug-tools']
        container = f'qore-{target}-combined-core22-{mode}-install-3'
        script = 'set -eu\n' + install + ' "$@"\n'
        script += 'rpm -V ' + ' '.join(names) + '\n'
        if mode == 'sdk':
            script += 'rpm -q --whatprovides \"qore-devel(module-doc-peers)\"\n'
        script += 'getent passwd 1019 || useradd -u 1019 -g 100 -M qoretester\n'
        if mode == 'runtime':
            script += 'for package in qore-devel gcc gcc-c++; do if rpm -q "$package"; then exit 1; fi; done\n'
        run(mode + '-install', common + ['--name', container, base, 'sh', '-c', script, mode,
                                         *[packages[name] for name in names]])
        image = subprocess.check_output(['docker', 'commit', container, f'qore-rpm-keep:{target}-combined-core22-{mode}'], text=True).strip()
        subprocess.run(['docker','container','rm',container],check=True,capture_output=True)
        status[mode + '_image'] = image
        save()
        tests = ['runtime', 'development', 'tools', 'remote-debuggers'] if mode == 'sdk' else ['runtime']
        script = 'set -eu\nfor test in "$@"; do\n QORE_RPM_TEST_TMP=$(mktemp -d /tmp/qore-installed-$test.XXXXXX)\n export QORE_RPM_TEST_TMP\n /source/rpm/tests-installed/$test\ndone\n'
        run(mode + '-tests', common + ['--name', f'qore-{target}-combined-core22-{mode}-tests-3', '--network', 'none',
                                      '--user', '1019:100', image, 'sh', '-c', script, 'tests', *tests])
        subprocess.run(['docker','container','rm',f'qore-{target}-combined-core22-{mode}-tests-3'],check=True,capture_output=True)
    status['exit_code'] = 0
except BaseException as error:
    status['exit_code'] = 1
    status['error'] = str(error)
    raise
finally:
    save()
