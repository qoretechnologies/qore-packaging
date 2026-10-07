# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,shlex,subprocess
root=Path('/work/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1');out=Path('/control')
line=next(l for l in Path('/work/build.log').read_text().splitlines() if l.strip().startswith('g++ -o ') and 'raw-machine-assembler.o ' in l)
args=shlex.split(line);args[2]='/control/control.o';args[3]='/control/control.cc'
# Retain ABI/feature definitions; use native sections from the fat LTO archives.
args=[a for a in args if not a.startswith('-flto=') and a!='-ffat-lto-objects'];args += ['-fno-lto']; args[args.index('-MF')+1]='/control/control.d'
cmd=args
with (out/'compile.log').open('x') as log:r=subprocess.run(cmd,cwd=root/'out',stdout=log,stderr=subprocess.STDOUT)
(out/'compile-status.json').write_text(json.dumps({'command':cmd,'exit_code':r.returncode},indent=2)+'\n');r.check_returncode()
