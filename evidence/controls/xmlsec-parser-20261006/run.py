# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import subprocess, json
root = Path.cwd()
flags = subprocess.check_output(['pkg-config', '--cflags', '--libs', 'xmlsec1-openssl'], text=True).split()
commands = [
 ['gcc', '-std=c11', '-O2', '-g', '-Wall', '-Wextra', '-Werror', 'control.c', *flags, '-o', 'control'],
 ['./control'],
 ['valgrind', '--error-exitcode=99', '--leak-check=full', '--show-leak-kinds=all', '--errors-for-leak-kinds=all', '--log-file=valgrind.log', './control']]
results = []
for name, command in zip(('compile', 'normal', 'memory'), commands):
 with (root / (name + '.log')).open('w') as log:
  result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
 results.append({'name': name, 'command': command, 'exit_code': result.returncode})
 (root / 'status.json').write_text(json.dumps(results, indent=2) + '\n')
 result.check_returncode()
