# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,subprocess
root=Path.cwd();out=root/'results/parquet-read-api-traces-20261008';out.mkdir()
def run(target):
    previous=root/'results/parquet-read-api-final-20261008'/target
    if target=='fedora': previous=root/'results/parquet-read-api-complete-20261008'/target
    rows=json.loads((previous/'status.json').read_text());row=next(r for r in rows if r['name'].startswith('valgrind'))
    cmd=row['command'].copy()
    if target=='fedora':
        idx=cmd.index('sha256:a437efbf23f3bf7b180f7d58a5ad3dd70d524372ae60a57380dff115a2b5feda');cmd[idx]='sha256:1d0b9746139ba0ac3822952a6b7248cb54ab48f7241d879d9cf55ff84c02d7d0'
    else:
        trace=root/'results/parquet-read-api-complete-20261008'/target/'trace.so'
        if target=='leap':
            cmd[2:2]=['-v',str(trace)+':/trace.so:ro'];cmd.insert(cmd.index('env')+1,'LD_PRELOAD=/trace.so')
        else:cmd.insert(cmd.index('env')+1,'LD_PRELOAD='+str(trace))
    with (out/(target+'.log')).open('x') as log:
        p=subprocess.run(cmd,cwd=root,stdout=log,stderr=subprocess.STDOUT)
    result={'exit_code':p.returncode,'command':cmd};(out/(target+'.json')).write_text(json.dumps(result,indent=2)+'\n');print(target,p.returncode,flush=True)
    return target,p.returncode
with ThreadPoolExecutor(max_workers=3) as pool: result=dict(pool.map(run,['leap','fedora','release','debug']))
(out/'status.json').write_text(json.dumps(result,indent=2)+'\n')
