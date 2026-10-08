# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess,os
root=Path.cwd();repo=root.parent/'qore';out=root/'results/qcc-optional-20261008/control2';out.mkdir()
opt=out/'optional';opt.mkdir();art=out/'artifacts';art.mkdir()
source=art/'PackagingOptionalControl.qm';source.write_bytes((root/'results/qcc-optional-20261008/control/artifacts/PackagingOptionalControl.qm').read_bytes())
build=repo/'build';env=os.environ.copy();env.update(LD_LIBRARY_PATH=str(build),QORE_LIBDIR=str(build),QORE_MODULE_DIR=str(art)+':'+str(opt))
steps=[]
def run(name,args):
 r=subprocess.run(args,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 (out/(name+'.stdout')).write_text(r.stdout);(out/(name+'.stderr')).write_text(r.stderr)
 steps.append({'name':name,'command':args,'exit_code':r.returncode});assert r.returncode==0,(name,r.stderr)
 return r
compile_cmd=[str(build/'qcc'),'-m','--depfile='+str(out/'control.d'),'-o',str(art/'PackagingOptionalControl.qmod'),str(source)]
r=run('absent-compile',compile_cmd);expected="qcc: warning: optional module 'PackagingOptionalFixture' is not available during compilation\nqcc:          'PackagingOptionalFixture'-dependent functionality will be disabled in the compiled module\n"
assert r.stderr==expected,repr(r.stderr)
cmd=[str(build/'qore'),'-b','--enable-debug','-ne','%requires PackagingOptionalControl\nprint(PackagingOptionalControl::mode());']
r=run('absent-runtime',cmd);assert r.stdout=='absent' and not r.stderr
(opt/'PackagingOptionalFixture.qm').write_text('''# Copyright 2026 Qore Technologies, s.r.o.
%modern
module PackagingOptionalFixture { version = "1.0"; desc = "Optional fixture"; author = "Qore"; license = "MIT"; }
public namespace PackagingOptionalFixture { public string sub mode() { return "present"; } }
''')
r=run('installed-runtime',cmd);assert r.stdout=='present'
assert "was compiled when optional module 'PackagingOptionalFixture' was not available" in r.stderr,r.stderr
r=run('present-compile',compile_cmd);assert not r.stderr,r.stderr
r=run('present-runtime',cmd);assert r.stdout=='present' and not r.stderr
(out/'status.json').write_text(json.dumps({'steps':steps,'checks':7,'result':'pass','scope':'Synthetic module exercises the unchanged availability detector and source fallback; no real extension functionality is inferred.','harness_correction':'First control expected a newline from Qore print(), which deliberately emits none. Only expected stdout was corrected; initial logs retained.'},indent=2)+'\n')
print('Paired optional compilation/runtime control passed')
