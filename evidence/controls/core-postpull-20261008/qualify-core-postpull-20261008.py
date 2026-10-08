# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Requalify the preserved local fixes after the fast-forward to 9f94a962f."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess

root = Path(__file__).resolve().parent.parent
repo = root.parent / 'qore'
out = root / 'results/core-postpull-20261008'
out.mkdir()
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip()
assert head.startswith('9f94a962f')
paths = subprocess.check_output(['git', 'diff', '--name-only'], cwd=repo, text=True).splitlines()
paths += subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], cwd=repo, text=True).splitlines()
pins = {p: hashlib.sha256((repo / p).read_bytes()).hexdigest() for p in paths}
(out / 'source.json').write_text(json.dumps({'head': head, 'files_sha256': pins}, indent=2) + '\n')


def environment(build):
    env = os.environ.copy()
    env['LD_LIBRARY_PATH'] = str(build)
    env['QORE_BINARY'] = str(build / 'qore')
    env['QORE_BIN'] = str(build / 'qore')
    env['QORE_LIBDIR'] = str(build)
    env['QORE_MODULE_DIR'] = ':'.join([str(repo / 'qlib'),
        *[str(p) for p in (build / 'modules').iterdir() if p.is_dir()], str(root.parent / 'module-xml/build')])
    return env


def run(mode, records, name, command, env):
    directory = out / mode
    with (directory / (name + '.log')).open('x') as log:
        result = subprocess.run(command, cwd=repo, env=env, stdout=log, stderr=subprocess.STDOUT)
    records.append({'name': name, 'command': command, 'exit_code': result.returncode,
                    'regex_engine': 'interpreter' if env.get('QORE_PCRE2_NO_JIT') == '1' else 'default JIT'})
    (directory / 'steps.json').write_text(json.dumps(records, indent=2) + '\n')
    print(mode, name, result.returncode, flush=True)
    result.check_returncode()


def build_mode(mode):
    build = repo / ('build-debug' if mode == 'debug' else 'build')
    cache = (build / 'CMakeCache.txt').read_text()
    kind = 'Debug' if mode == 'debug' else 'Release'
    assert 'CMAKE_INSTALL_PREFIX:PATH=/usr\n' in cache
    assert 'CMAKE_BUILD_TYPE:STRING=' + kind + '\n' in cache
    assert shutil.disk_usage(root).free > 12 * 1024**3
    (out / mode).mkdir()
    records = []
    env = environment(build)
    run(mode, records, 'configure', ['cmake', '-S', str(repo), '-B', str(build),
        '-DCMAKE_BUILD_TYPE=' + kind, '-DCMAKE_INSTALL_PREFIX=/usr'], env)
    run(mode, records, 'build', ['cmake', '--build', str(build), '--target',
        'qore', 'qore-hash-lookup-test', '-j2'], env)
    return mode, records


result = {'head': head, 'exit_code': 1}
try:
    with ThreadPoolExecutor(max_workers=2) as pool:
        all_records = dict(pool.map(build_mode, ('debug', 'release')))
    # Module targets update shared source-tree qmod links; build/test modes sequentially.
    for mode in ('debug', 'release'):
        build = repo / ('build-debug' if mode == 'debug' else 'build')
        env = environment(build)
        records = all_records[mode]
        run(mode, records, 'updated-qlib-build', ['cmake', '--build', str(build), '--target',
            'CsvUtil-qmod', 'DataProvider-qmod', '-j2'], env)
        run(mode, records, 'native', [str(build / 'qore-hash-lookup-test')], env)
        vg = ['valgrind', '--error-exitcode=99', '--leak-check=full', '--show-leak-kinds=all',
              '--errors-for-leak-kinds=definite,indirect,possible']
        run(mode, records, 'native-valgrind', [*vg, str(build / 'qore-hash-lookup-test')], env)
        suites = [
            'examples/test/qore/misc/hash-lookup-native.qtest',
            'examples/test/qore/misc/hash.qtest',
            'examples/test/qore/misc/hashdecl.qtest',
            'examples/test/qore/misc/hash-key-encoding/hash-key-encoding.qtest',
            'examples/test/qlib/CsvUtil/CsvByteOrderMark.qtest',
            'examples/test/qlib/CsvUtil/CsvEncoding.qtest',
            'examples/test/qlib/DataProvider/TabularProfiler.qtest',
            'examples/test/qore/misc/module-loader/separated-module-path.qtest',
            'examples/test/qore/misc/module-loader/separated-module-shadow.qtest',
            'examples/test/qore/misc/module-loader/modules.qtest',
            'examples/test/qore/parser/module-path-directive.qtest']
        for suite in suites:
            command = [str(build / 'qore'), '-b', '--enable-debug', suite, '-v']
            run(mode, records, Path(suite).stem, command, env)
            if suite in suites[-4:]:
                run(mode, records, Path(suite).stem + '-valgrind', [*vg, *command],
                    dict(env, QORE_PCRE2_NO_JIT='1'))
    assert pins == {p: hashlib.sha256((repo / p).read_bytes()).hexdigest() for p in paths}
    result['exit_code'] = 0
except BaseException as error:
    result['error'] = repr(error)
    raise
finally:
    (out / 'status.json').write_text(json.dumps(result, indent=2) + '\n')
