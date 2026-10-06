# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
import json, re, subprocess
from pathlib import Path
w=Path('/fixture');flags=json.loads((w/'flags.json').read_text())
cmd=[*flags,'/fixture/control.cc','-Wl,--gc-sections','-lnode','-o','/fixture/control']
r=subprocess.run(cmd,capture_output=True,text=True)
(w/'compile.log').write_text(r.stdout+r.stderr)
assert r.returncode==0,(r.returncode,r.stderr[-6000:])
warnings = [line for line in r.stderr.splitlines() if 'warning:' in line]
assert all('[-Wmaybe-uninitialized]' in line for line in warnings),warnings
print(str(len(warnings)) + ' guarded-state compiler diagnostics; no other warnings',flush=True)
subprocess.run(['/fixture/control'],check=True)
subprocess.run(['valgrind','--error-exitcode=99','--leak-check=full','--show-leak-kinds=all','--errors-for-leak-kinds=definite,indirect,possible','--log-file=/fixture/valgrind.log','/fixture/control'],check=True)
