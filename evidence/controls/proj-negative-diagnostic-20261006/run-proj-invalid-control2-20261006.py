# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,subprocess
root=Path.cwd();images=json.loads((root/'results/proj-sdk21-debugedit51-images-20261006.json').read_text())
images['fedora']=subprocess.check_output(['docker','image','inspect','qore-rpm-keep:fedora-proj-sdk21-valgrind-20261006','--format','{{.Id}}'],text=True).strip()
def run(target):
 out=root/f'results/{target}-proj-invalid-control2-20261006';out.mkdir()
 (out/'control.c').write_bytes((root/'work/proj-invalid-control2-20261006.c').read_bytes())
 script='''set -eu
cc -Wall -Wextra -Werror -O2 -g -UNDEBUG control.c $(pkg-config --cflags --libs proj) -o control
./control > normal.txt 2> normal.stderr
valgrind --error-exitcode=91 --leak-check=full --show-leak-kinds=all --errors-for-leak-kinds=all --log-file=valgrind.txt ./control > valgrind.stdout 2> valgrind.stderr
'''
 cmd=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}','-v',str(out)+':/control','-w','/control',images[target],'sh','-ec',script]
 with (out/'tests.log').open('x') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
 (out/'status.json').write_text(json.dumps({'exit_code':r.returncode,'command':cmd},indent=2)+'\n');return target,r.returncode
with ThreadPoolExecutor(max_workers=3) as pool:print(dict(pool.map(run,images)))
