# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
import hashlib,json,os,stat,subprocess
from datetime import datetime,timezone
from pathlib import Path
root=Path.cwd().resolve()
targets=[root/'work/node-wasm-deopt-review-20261007/original',root/'work/node-wasm-deopt-review-20261007/fixed',root/'work/node-full-snapshot-helper-20261007/reschedule',root/'work/node-snapshot-copy-control-20261007/control']
evidence=['node-wasm-deopt-fix-20261007','node-snapshot-copy-diagnostic-20261007','node-reschedule-fix-20261007']
verified=0
for name in evidence:
 v=json.loads((root/'evidence'/(name+'.json')).read_text())
 maps=[v['files_sha256']]
 if 'full_snapshot_helper_qualification' in v:maps.append(v['full_snapshot_helper_qualification']['files_sha256'])
 for mapping in maps:
  for f,h in mapping.items():assert hashlib.sha256((root/f).read_bytes()).hexdigest()==h,f;verified+=1
for d in {p.parent for p in targets}:
 rows=json.loads((d/'status.json').read_text())
 for row in rows:
  exp=row.get('expected',0)
  assert row['exit_code']==(-6 if exp=='fatal' else exp),(d,row)
# Retain every source, object, command receipt, log, package and linked build archive.
for p in targets:
 assert p.resolve()==p and p.is_relative_to(root/'work')
 assert p.lstat().st_uid==os.getuid() and stat.S_ISREG(p.lstat().st_mode) and p.stat().st_nlink==1
 with p.open('rb') as f:assert f.read(4)==b'\x7fELF'
 assert not subprocess.check_output(['git','ls-files','--',str(p.relative_to(root))],cwd=root)
# Use a read-only privileged inventory for same-user non-dumpable processes.
scan = r"""
from pathlib import Path
import json,os,sys
targets=json.loads(sys.argv[1]);uid=int(sys.argv[2]);references=[];denied=[]
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:
  if proc.stat().st_uid!=uid:continue
  for link in [proc/'exe',proc/'cwd',*list((proc/'fd').iterdir())]:
   try:dest=os.readlink(link)
   except FileNotFoundError:continue
   if dest in targets:references.append(str(link))
  if any(p in (proc/'maps').read_text() for p in targets):references.append(str(proc/'maps'))
 except (FileNotFoundError,ProcessLookupError):continue
 except PermissionError:denied.append(str(proc))
print(json.dumps({'references':references,'denied':denied}))
assert not references and not denied
"""
receipt=json.loads(subprocess.check_output(['sudo','-n','python3','-c',scan,json.dumps([str(p) for p in targets]),str(os.getuid())],text=True))
assert not receipt['references'] and not receipt['denied']
rows=[]
for p in targets:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
 st=p.stat();rows.append({'path':str(p.relative_to(root)),'size':st.st_size,'allocated_bytes':st.st_blocks*512,'sha256':h.hexdigest(),'inode':st.st_ino,'device':st.st_dev})
before=os.statvfs(root);before_free=before.f_bavail*before.f_frsize
record={'schema':1,'date':datetime.now(timezone.utc).isoformat(),'copyright':'Copyright 2026 Qore Technologies, s.r.o.','status':'manifest prepared','authorization':'User requested removal of unneeded build artifacts. Only the four completed, reproducible ELF control executables listed here are selected.','files':rows,'verified_evidence_files':verified,'limits':'Sources, object files, scripts, logs, RPMs, current Node/core compiled trees, Docker images and volumes retained. No live process references any selected executable.','free_before_bytes':before_free}
out=root/'evidence/node-control-cleanup-20261008.json';assert not out.exists();out.write_text(json.dumps(record,indent=2)+'\n')
for row,p in zip(rows,targets):
 st=p.stat();assert (st.st_ino,st.st_dev,st.st_size)==(row['inode'],row['device'],row['size'])
 p.unlink()
after=os.statvfs(root);record.update(status='completed',removed_allocated_bytes=sum(r['allocated_bytes'] for r in rows),free_after_bytes=after.f_bavail*after.f_frsize)
record['observed_free_increase_bytes']=record['free_after_bytes']-before_free
out.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:record[k] for k in ['status','removed_allocated_bytes','free_after_bytes','observed_free_increase_bytes','verified_evidence_files']},indent=2))
