# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import os
import subprocess

root = Path.cwd()
repo = root.parent / 'qore'
out = root / 'results/core-hash-lookup-20261008'
out.mkdir()
sources = ['lib/QoreHashNode.cpp', 'include/qore/QoreHashNode.h', 'CMakeLists.txt',
           'examples/test/qore/misc/hash_lookup.cpp', 'examples/test/qore/misc/hash-lookup-native.qtest',
           'examples/test/qore/misc/hash-lookup-native.rst', 'doxygen/lang/900_release_notes.dox.tmpl']
pins = {name: hashlib.sha256((repo / name).read_bytes()).hexdigest() for name in sources}
(out / 'source-hashes.json').write_text(json.dumps(pins, indent=2) + '\n')

def qualify(mode):
    folder = 'build-debug' if mode == 'debug' else 'build'
    build = repo / folder
    cache = (build / 'CMakeCache.txt').read_text()
    assert 'CMAKE_INSTALL_PREFIX:PATH=/usr\n' in cache
    assert 'CMAKE_BUILD_TYPE:STRING=' + ('Debug' if mode == 'debug' else 'Release') + '\n' in cache
    target = out / mode
    target.mkdir()
    records = []
    env = os.environ.copy()
    env['LD_LIBRARY_PATH'] = str(build)
    env['QORE_BINARY'] = str(build / 'qore')
    env['QORE_MODULE_DIR'] = ':'.join([str(repo / 'qlib'), *[str(path) for path in (build / 'modules').iterdir() if path.is_dir()], str(root.parent / 'module-xml/build')])
    steps = [('build', ['cmake', '--build', str(build), '--target', 'qore', 'qore-hash-lookup-test', '-j2']),
             ('native', [str(build / 'qore-hash-lookup-test')]),
             ('native-valgrind', ['valgrind', '--error-exitcode=99', '--leak-check=full', '--show-leak-kinds=all',
                                  '--errors-for-leak-kinds=definite,indirect,possible', str(build / 'qore-hash-lookup-test')])]
    for name in ['hash-lookup-native', 'hash', 'hashdecl']:
        steps.append((name, [str(build / 'qore'), '-b', '--enable-debug', str(repo / 'examples/test/qore/misc' / (name + '.qtest'))]))
    for name, command in steps:
        with (target / (name + '.log')).open('x') as log:
            result = subprocess.run(command, cwd=repo, env=env, stdout=log, stderr=subprocess.STDOUT)
        records.append({'name': name, 'command': command, 'exit_code': result.returncode})
        (target / 'status.json').write_text(json.dumps(records, indent=2) + '\n')
        print(mode, name, result.returncode, flush=True)
        if result.returncode:
            return mode, result.returncode
    return mode, 0

with ThreadPoolExecutor(max_workers=2) as pool:
    result = dict(pool.map(qualify, ['debug', 'release']))
assert pins == {name: hashlib.sha256((repo / name).read_bytes()).hexdigest() for name in sources}
(out / 'status.json').write_text(json.dumps(result, indent=2) + '\n')
print(result, flush=True)
raise SystemExit(any(result.values()))
