# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,re,subprocess
out=Path('/output');features=json.loads(Path('/control/features.json').read_text());records=[]
user=['setpriv','--reuid=1019','--regid=100','--clear-groups','--reset-env']
assert subprocess.run(['rpm','-q','qore-xml-module'],stdout=subprocess.DEVNULL).returncode==1
for installed in (False,True):
 if installed:
  subprocess.run(['rpm','-U','/xml.rpm'],check=True)
  subprocess.run(['rpm','-V','qore-xml-module'],check=True)
 for feature,optional in features.items():
  name=('with-' if installed else 'without-')+'xml-'+feature
  command=user+['qore','-b','--enable-debug','/control/'+feature+'.qr']
  p=subprocess.run(command,capture_output=True,text=True)
  (out/(name+'.stdout')).write_text(p.stdout);(out/(name+'.stderr')).write_text(p.stderr)
  assert p.returncode==0,(name,p.returncode,p.stderr)
  assert p.stdout==feature+' import passed\n',(name,p.stdout)
  diagnostics=[]
  for line in p.stderr.splitlines():
   match=False
   for f,o in features.items():
    source=f+'/'+f if f=='DataProvider' else f
    binary='/usr/lib64/qore-modules/3.0.0/'+source+'.qmod'
    src='/usr/share/qore-modules/3.0.0/'+source+'.qm'
    expected="warning: binary module '"+binary+"' for feature '"+f+"' failed to load; loading source module '"+src+"' instead: AOT-MODULE-STALE: AOT module '"+binary+"' was compiled when optional module '"+o+"' was not available, but it is available now; rebuild the binary module"
    if line==expected: match=True
   assert match,(name,line)
   diagnostics.append(line)
  if not installed: assert not diagnostics,(name,diagnostics)
  else:
   assert any("feature '"+feature+"'" in line and "optional module '"+optional+"'" in line for line in diagnostics),(name,diagnostics)
   for line in diagnostics:
    assert any("feature '"+f+"'" in line and "optional module '"+o+"'" in line for f,o in features.items()),(name,line)
  records.append({'name':name,'command':command,'exit_code':p.returncode,'diagnostics':diagnostics})
(out/'checks.json').write_text(json.dumps(records,indent=2)+'\n')
