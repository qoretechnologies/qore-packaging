# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import subprocess

command = ['valgrind', '--vgdb-error=1', '--vgdb-prefix=/work/vgdb-amqp',
    '--keep-debuginfo=yes', '--track-origins=yes', '--leak-check=no',
    'qore', '-b', '--enable-debug', '-l',
    '/usr/lib64/qore-modules/AmqpDataProvider/AmqpDataProvider.qmod',
    '-e', 'printf("AMQP loaded\\n");']
with Path('/work/debug-program.log').open('w') as log:
    process = subprocess.Popen(command, stdout=log, stderr=subprocess.PIPE, text=True)
    try:
        attached = False
        for line in process.stderr:
            log.write(line)
            log.flush()
            if '(action on error)' in line:
                assert not attached
                attached = True
                args = ['gdb', '-q', '-nx', '-batch', '/usr/bin/qore',
                    '-ex', 'set pagination off', '-ex',
                    'target remote | vgdb --vgdb-prefix=/work/vgdb-amqp --pid=' + str(process.pid) + ' 2>/work/vgdb-stderr.log',
                    '-ex', 'bt 24', '-ex', 'info sharedlibrary', '-ex', 'info proc mappings', '-ex', 'x/s $r13', '-ex', 'x/s $rsi',
                    '-ex', 'x/48bx $rsi', '-ex', 'x/20i $pc-24',
                    '-ex', 'info registers', '-ex', 'monitor v.set vgdb-error 999999',
                    '-ex', 'detach']
                with Path('/work/debug-gdb.log').open('w') as output:
                    subprocess.run(args, stdout=output, stderr=subprocess.STDOUT, check=True, timeout=90)
        assert process.wait() == 0 and attached
    finally:
        if process.returncode is None:
            process.kill()
            process.wait()
        process.stderr.close()
