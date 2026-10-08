# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib, json, os, re, shlex, shutil, subprocess, sys
root = Path.cwd()
repo = root.parent / 'qore'
out = root / 'results/parquet-read-api-complete-20261008'
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
        fixture = dest / 'tests'
        shutil.copytree(hostlink.parents[5] / 'modules/dataframe/test', fixture)
        shutil.copy2(repo / test, fixture / Path(test).name)
        prefix = ['docker', 'run', '--rm', '--init', '--network', 'none', '--user', str(os.getuid()) + ':' + str(os.getgid()),
            '-v', str(previous) + ':/work:ro', '-v', str(repo) + ':/source:ro', '-v', str(dest) + ':/out',
            '-v', str(fixture) + ':' + str(testfile.parent) + ':ro',
            '-e', 'RPM_ARCH=x86_64', '-e', 'RPM_PACKAGE_NAME=qore', '-e', 'RPM_PACKAGE_VERSION=3.0.0~git20261008.22', '-e', 'RPM_PACKAGE_RELEASE=22', '-w', str(build / 'modules/dataframe'), image]
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
        ('parquet-existing', runenv + qore + [str(checkout / 'modules/dataframe/test/dataframe.qtest'), '--include=parquetTest']),
        ('valgrind', runenv + ['valgrind', '--error-exitcode=99', '--leak-check=full', '--show-leak-kinds=all', '--errors-for-leak-kinds=definite,indirect,possible'] + qore + [str(testfile)])]
    prior = root / 'results/parquet-read-api-final-20261008' / target
    records = json.loads((prior / 'status.json').read_text())
    assert records[0]['exit_code'] == 0
    shutil.copy2(prior / 'df_parquet.cpp.o', dest / 'df_parquet.cpp.o')
    shutil.copy2(prior / 'compile.log', dest / 'compile.log')
    rows = records[:1]
    steps = steps[1:]
    if host or target == 'leap':
        assert all(r['exit_code'] == 0 for r in records[:4])
        for name in ['dataframe-api-2.0.qmod', 'link.log', 'regression.log', 'parquet-existing.log']:
            shutil.copy2(prior / name, dest / name)
        rows = records[:4]
        steps = steps[4:]
    shutil.copy2(root / 'evidence/controls/core-separated-pcre-20261008/trace.c', dest / 'trace.c')
    trace_compile = ['gcc', '-shared', '-fPIC', '-Wall', '-Werror', str(container_out / 'trace.c'), '-ldl', '-o', str(container_out / 'trace.so')]
    steps.insert(0, ('trace-compile', trace_compile))
    for idx, (name, args) in enumerate(steps):
        if name == 'valgrind':
            args.insert(args.index('env') + 1, 'LD_PRELOAD=' + str(container_out / 'trace.so'))
            steps[idx] = ('valgrind-traced', args)
    if target == 'leap':
        original_compile = compile_command.copy()
        original_compile[original_compile.index(str(changed))] = str(checkout / source)
        original_compile[-1] = str(container_out / 'original.o')
        with (dest / 'original-compile.log').open('x') as log:
            result = subprocess.run(prefix + original_compile, cwd=hostmodule, stdout=log, stderr=subprocess.STDOUT)
        assert result.returncode != 0
        log = (dest / 'original-compile.log').read_text()
        assert log.count('error:') == 4 and log.count('is deprecated: Deprecated in 24.0.0.') == 4
        (dest / 'original-negative.json').write_text(json.dumps({'exit_code': result.returncode, 'deprecated_api_errors': 4}) + '\n')
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
