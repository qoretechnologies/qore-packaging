# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import importlib.util,json,subprocess,sys
spec=importlib.util.spec_from_file_location('wrapper','/control/run-sandbox-errors.py');wrapper=importlib.util.module_from_spec(spec);spec.loader.exec_module(wrapper)
result=Path('/output');records=[]
def run(name,command,status=0,warning=False):
 p=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 (result/(name+'.stdout')).write_text(p.stdout);(result/(name+'.stderr')).write_text(p.stderr)
 assert p.returncode==status,(name,p.returncode,p.stderr)
 if warning: assert wrapper.QUNIT_XML_FALLBACK.fullmatch(p.stderr),(name,p.stderr)
 else: assert not p.stderr,(name,p.stderr)
 records.append({'name':name,'command':command,'exit_code':p.returncode})
user=['setpriv','--reuid=1019','--regid=100','--clear-groups','--reset-env']
subprocess.run(['rpm','-U','--replacepkgs','/zmq.rpm'],check=True)
assert subprocess.run(['rpm','-q','qore-xml-module'],stdout=subprocess.DEVNULL).returncode==1
run('without-xml',user+['qore','-b','--enable-debug','/control/load.qr'])
base=user+['python3','-B','-W','error','/control/run-sandbox-errors.py','--module','/usr/lib64/qore-modules/zmq-api-2.0.qmod']
run('without-xml-sandbox',base)
subprocess.run(['rpm','-U','/xml.rpm'],check=True)
subprocess.run(['rpm','-V','qore-xml-module'],check=True)
run('with-xml',user+['qore','-b','--enable-debug','/control/load.qr'],warning=True)
run('with-xml-sandbox-allowance',base+['--allow-qunit-xml-fallback'],warning=True)
(result/'checks.json').write_text(json.dumps(records,indent=2)+'\n')
