# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import os,json,subprocess,hashlib
root=Path.cwd();repo=root.parent/'qore';out=root/'results/qcc-optional-20261008';out.mkdir()
source=repo/'examples/test/ir/AOTOptionalModules.qtest';pin=hashlib.sha256(source.read_bytes()).hexdigest()
def run(mode):
 dest=out/mode;dest.mkdir();build=repo/('build' if mode=='release' else 'build-debug')
 env=os.environ.copy();env.update(LD_LIBRARY_PATH=str(build),QORE_LIBDIR=str(build),QORE_BIN=str(build/'qore'),QCC=str(build/'qcc'),QORE_MODULE_DIR=':'.join([str(repo/'qlib'),*[str(p) for p in (build/'modules').iterdir() if p.is_dir()]]))
 cmd=[str(build/'qore'),'-b','--enable-debug',str(source),'-v']
 with (dest/'native.log').open('x') as f:p=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,cwd=repo)
 (dest/'status.json').write_text(json.dumps({'command':cmd,'exit_code':p.returncode,'source_sha256':pin,'environment':{k:env[k] for k in ['LD_LIBRARY_PATH','QORE_LIBDIR','QORE_BIN','QCC','QORE_MODULE_DIR']}},indent=2)+'\n')
 return mode,p.returncode
with ThreadPoolExecutor(max_workers=2) as pool:results=dict(pool.map(run,['release','debug']))
assert hashlib.sha256(source.read_bytes()).hexdigest()==pin
(out/'status.json').write_text(json.dumps(results,indent=2)+'\n');print(results);raise SystemExit(any(results.values()))
