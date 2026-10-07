# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import re
import select
import subprocess

root = Path.cwd()
repo = root.parent / 'qore'
out = root / 'results/core-date-add-final3-tests-20261007'
out.mkdir()
files = ['lib/DateTime.cpp', 'include/qore/intern/qore_date_private.h',
         'examples/test/qore/vars/date_add.cpp', 'examples/test/qore/vars/date-add-native.qtest']
source_hashes = {name: hashlib.sha256((repo / name).read_bytes()).hexdigest() for name in files}


def qualify(mode):
    build_name = 'build-debug' if mode == 'debug' else 'build'
    build = repo / build_name
    process_fds = []
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            argv = (proc / 'cmdline').read_bytes().decode().split('\0')
            if argv[1:6] == ['--build', build_name, '--target', 'qore', 'qore-date-add-test'] and Path(argv[0]).name == 'cmake':
                process_fds.append(os.pidfd_open(int(proc.name)))
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            pass
    assert len(process_fds) <= 1
    try:
        if process_fds:
            select.select(process_fds, [], [])
    finally:
        for fd in process_fds:
            os.close(fd)
    for name, digest in source_hashes.items():
        assert hashlib.sha256((repo / name).read_bytes()).hexdigest() == digest, name
    target = out / mode
    target.mkdir()
    cache = (build / 'CMakeCache.txt').read_text()
    assert 'CMAKE_INSTALL_PREFIX:PATH=/usr\n' in cache
    assert 'CMAKE_BUILD_TYPE:STRING=' + ('Debug' if mode == 'debug' else 'Release') + '\n' in cache
    command = ['cmake', '--build', build_name, '--target', 'qore', 'qore-date-add-test', '-j4']
    with (target / 'native-build.log').open('x') as stream:
        result = subprocess.run(command, cwd=repo, stdout=stream, stderr=subprocess.STDOUT)
    build_log = (target / 'native-build.log').read_text()
    assert result.returncode == 0 and 'Built target qore-date-add-test' in build_log, build_log[-3000:]
    assert not re.search(r'(?im)^.*(?:error:|warning:)', build_log), build_log[-3000:]
    native = build / 'qore-date-add-test'
    assert native.stat().st_mtime > (repo / 'examples/test/qore/vars/date_add.cpp').stat().st_mtime
    env = os.environ.copy()
    env.pop('LD_PRELOAD', None)
    env['LD_LIBRARY_PATH'] = str(build)
    env['QORE_BINARY'] = str(build / 'qore')
    env['QORE_MODULE_DIR_ONLY'] = '1'
    module_paths = [str(repo / 'qlib')]
    module_paths += [str(p) for p in sorted((build / 'modules').iterdir()) if p.is_dir()]
    module_paths += [str(repo.parent / 'module-xml/build')]
    env['QORE_MODULE_DIR'] = ':'.join(module_paths)
    env['QORE_INCLUDE_DIR'] = ''
    rows = []
    commands = [('native', [str(native)]),
                ('native-valgrind', ['valgrind', '--error-exitcode=99', '--leak-check=full',
                    '--show-leak-kinds=all', '--errors-for-leak-kinds=definite,indirect,possible', str(native)])]
    tests = ['qore/vars/date-add-native.qtest', 'qore/vars/date.qtest',
             'qore/vars/date-utc-offset.qtest', 'qore/functions/date_durations.qtest']
    commands += [(Path(name).stem, [str(build / 'qore'), '-b', '--enable-debug',
                                  str(repo / 'examples/test' / name)]) for name in tests]
    for name, command in commands:
        log = target / (name + '.log')
        with log.open('x') as stream:
            result = subprocess.run(command, cwd=repo, env=env, stdout=stream,
                                    stderr=subprocess.STDOUT, timeout=300)
        rows.append({'name': name, 'command': command, 'exit_code': result.returncode})
        (target / 'status.json').write_text(json.dumps(rows, indent=2) + '\n')
        output = log.read_text()
        assert result.returncode == 0, (mode, name, output[-4000:])
        if name.startswith('native'):
            assert 'PASS: 1836 DateTime addition cases' in output
        if name == 'native-valgrind':
            assert 'ERROR SUMMARY: 0 errors' in output
            for kind in ('definitely', 'indirectly', 'possibly'):
                assert re.search(kind + r' lost:\s+0 bytes in 0 blocks', output)
            for warning in re.findall(r'(?im)^.*warning:.*$', output):
                assert 'Warning: zero subprog, missing DW_AT_abstract_origin in DW_TAG_inlined_subroutine in ' + str(build / 'libqore.so.20.0.0') in warning, warning
        else:
            assert not re.search(r'(?i)warning:|error:|FAIL', output), (name, output[-3000:])
            skips = re.findall(r'^Skipped:.*$', output, re.M)
            expected_skips = ['Skipped: WindowsTimeZoneTests: 0 assertions (skipping because the test is not run on Windows)'] if name == 'date' else []
            assert skips == expected_skips, (name, skips)
            if name not in ('native',):
                assert re.search(r'Ran (\d+) test cases, \1 succeeded \(\d+ assertions\)', output), output[-3000:]
        print(mode, name, 'PASS', flush=True)
    return {'mode': mode, 'steps': rows, 'source_hashes': source_hashes}


with ThreadPoolExecutor(max_workers=2) as pool:
    records = list(pool.map(qualify, ('debug', 'release')))
(out / 'status.json').write_text(json.dumps(records, indent=2) + '\n')
print('All Debug/Release date addition checks passed', flush=True)
