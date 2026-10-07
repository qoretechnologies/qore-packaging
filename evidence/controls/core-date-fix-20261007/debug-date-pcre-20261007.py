# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import os
import subprocess

root = Path.cwd()
repo = root.parent / 'qore'
build = repo / 'build-debug'
out = root / 'results/core-date-pcre-debug-20261007'
out.mkdir()
env = os.environ.copy()
env.pop('LD_PRELOAD', None)
env['LD_LIBRARY_PATH'] = str(build)
env['QORE_BINARY'] = str(build / 'qore')
env['QORE_MODULE_DIR_ONLY'] = '1'
env['QORE_INCLUDE_DIR'] = ''
env['QORE_MODULE_DIR'] = ':'.join([str(repo / 'qlib'),
    *(str(p) for p in sorted((build / 'modules').iterdir()) if p.is_dir()),
    str(repo.parent / 'module-xml/build')])
prefix = '/tmp/qore-date-vgdb-20261007'
command = ['valgrind', '--vgdb-error=1', '--vgdb-prefix=' + prefix,
    '--keep-debuginfo=yes', '--track-origins=yes', '--leak-check=no',
    str(build / 'qore'), '-b', '--enable-debug',
    str(repo / 'examples/test/qore/vars/date-add-native.qtest')]
with (out / 'program.log').open('x') as log:
    process = subprocess.Popen(command, cwd=repo, env=env, stdout=log, stderr=subprocess.PIPE, text=True)
    try:
        attached = False
        for line in process.stderr:
            log.write(line)
            log.flush()
            if '(action on error)' in line:
                assert not attached
                attached = True
                debugger = ['gdb', '-q', '-nx', '-nh', '-batch', str(build / 'qore'),
                    '-ex', 'set debuginfod enabled off', '-ex', 'set pagination off', '-ex',
                    'target remote | vgdb --vgdb-prefix=' + prefix + ' --pid=' + str(process.pid),
                    '-ex', 'bt 24', '-ex', 'x/s $r13', '-ex', 'x/s $rsi',
                    '-ex', 'x/48bx $rsi', '-ex', 'x/24i $pc-36',
                    '-ex', 'info registers', '-ex', 'monitor v.set vgdb-error 999999', '-ex', 'detach']
                with (out / 'gdb.log').open('x') as stream:
                    subprocess.run(debugger, stdout=stream, stderr=subprocess.STDOUT, check=True, timeout=120)
        assert process.wait() == 0 and attached
    finally:
        if process.returncode is None:
            process.kill()
            process.wait()
        process.stderr.close()
print('Captured the reported condition and JIT instructions without suppressing it')
