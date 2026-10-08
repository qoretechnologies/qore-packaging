# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib, json, os, re, shlex, subprocess, sys
root = Path.cwd()
repo = root.parent / 'qore'
out = root / 'results/parquet-read-api-20261008'
out.mkdir()
source = 'modules/dataframe/src/df_parquet.cpp'
test = 'modules/dataframe/test/parquet-read-api.qtest'
pins = {p: hashlib.sha256((repo / p).read_bytes()).hexdigest() for p in [source, test]}
(out / 'source-hashes.json').write_text(json.dumps(pins, indent=2) + '\n')

def qualify(target):
    dest = out / target
    dest.mkdir()
    host = target in ['release', 'debug']
    if host:
        build = repo / ('build' if target == 'release' else 'build-debug')
        checkout = repo
        prefix = []
        container_out = dest
        changed = repo / source
        testfile = repo / test
        env = os.environ.copy()
        assert 'CMAKE_INSTALL_PREFIX:PATH=/usr\n' in (build / 'CMakeCache.txt').read_text()
        assert 'CMAKE_BUILD_TYPE:STRING=' + target.capitalize() + '\n' in (build / 'CMakeCache.txt').read_text()
    else:
        previous = root / ('results/' + target + '-core-fixes-combined-candidate-20261008')
        record = json.loads((previous / 'build.json').read_text())
        image = record['command'][record['command'].index('sh') - 1]
        hostlink = next(previous.glob('rpmbuild/BUILD/**/build/modules/dataframe/CMakeFiles/dataframe.dir/link.txt'))
        build = Path('/work') / hostlink.parents[4].relative_to(previous)
        checkout = build.parent
        container_out = Path('/out')
        changed = Path('/source') / source
        testfile = checkout / test
        prefix = ['docker', 'run', '--rm', '--init', '--network', 'none', '--user', str(os.getuid()) + ':' + str(os.getgid()),
            '-v', str(previous) + ':/work:ro', '-v', str(repo) + ':/source:ro', '-v', str(dest) + ':/out',
            '-v', str(repo / test) + ':' + str(testfile) + ':ro',
            '-w', str(build / 'modules/dataframe'), image]
        env = os.environ.copy()
    hostbuild = build if host else hostlink.parents[4]
    module = build / 'modules/dataframe'
    hostmodule = hostbuild / 'modules/dataframe'
    defs = {}
    for line in (hostmodule / 'CMakeFiles/dataframe.dir/flags.make').read_text().splitlines():
        if ' = ' in line:
            k, v = line.split(' = ', 1)
            defs[k] = shlex.split(v)
    link = shlex.split((hostmodule / 'CMakeFiles/dataframe.dir/link.txt').read_text())
    compiler = link[0]
    compile_command = [compiler, *defs['CXX_DEFINES'], *defs['CXX_INCLUDES'], *defs['CXX_FLAGS'], '-Werror=deprecated-declarations', '-c', str(changed), '-o', str(container_out / 'df_parquet.cpp.o')]
    link[link.index('-o') + 1] = str(container_out / 'dataframe-api-2.0.qmod')
    link = [str(container_out / 'df_parquet.cpp.o') if a == 'CMakeFiles/dataframe.dir/src/df_parquet.cpp.o' else
            '-Wl,--dependency-file=' + str(container_out / 'link.d') if a.startswith('-Wl,--dependency-file=') else a for a in link]
    module_paths = [str(container_out), str(checkout / 'qlib'), *[str(build / 'modules' / p.name) for p in (hostbuild / 'modules').iterdir() if p.is_dir()]]
    runenv = ['env', 'LD_LIBRARY_PATH=' + str(build), 'QORE_MODULE_DIR=' + ':'.join(module_paths)]
    qore = [str(build / 'qore'), '-b', '--enable-debug']
    steps = [('compile', compile_command), ('link', link), ('regression', runenv + qore + [str(testfile)]),
        ('parquet-existing', runenv + qore + [str(checkout / 'modules/dataframe/test/dataframe.qtest'), '-t', 'parquetTest']),
        ('valgrind', runenv + ['valgrind', '--error-exitcode=99', '--leak-check=full', '--show-leak-kinds=all', '--errors-for-leak-kinds=definite,indirect,possible'] + qore + [str(testfile)])]
    rows = []
    for name, args in steps:
        command = prefix + args
        with (dest / (name + '.log')).open('x') as log:
            result = subprocess.run(command, cwd=hostmodule, env=env, stdout=log, stderr=subprocess.STDOUT)
        rows.append({'name': name, 'command': command, 'exit_code': result.returncode})
        (dest / 'status.json').write_text(json.dumps(rows, indent=2) + '\n')
        print(target, name, result.returncode, flush=True)
        if result.returncode:
            return target, result.returncode
    return target, 0
with ThreadPoolExecutor(max_workers=3) as pool:
    result = dict(pool.map(qualify, ['leap', 'fedora', 'el10', 'release', 'debug']))
assert pins == {p: hashlib.sha256((repo / p).read_bytes()).hexdigest() for p in pins}
(out / 'status.json').write_text(json.dumps(result, indent=2) + '\n')
raise SystemExit(any(result.values()))
