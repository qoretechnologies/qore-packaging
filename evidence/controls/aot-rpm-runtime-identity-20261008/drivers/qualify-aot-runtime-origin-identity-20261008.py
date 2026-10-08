# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib, importlib.util, json, os, re, subprocess, sys
root=Path.cwd();source=root/'work/checkouts/qore-aot-runtime-dependencies-20261008';mode=sys.argv[1];assert mode in ('release','debug')
build=source/('build' if mode=='release' else 'build-debug');out=root/f'results/aot-runtime-origin-{mode}-identity-20261008';out.mkdir();modules=out/'modules';modules.mkdir();fixtures=out/'source';fixtures.mkdir()
loader=importlib.util.spec_from_file_location('aot_identity',source/'rpm/qore_aot_identity.py');identity=importlib.util.module_from_spec(loader);loader.loader.exec_module(identity)
env=dict(os.environ,LD_LIBRARY_PATH=str(build),QORE_LIBDIR=str(build),QORE_MODULE_DIR=str(modules))
for key in list(env):
 if key.startswith('QORE_AOT_TEST_'):del env[key]
qore=str(build/'qore');qcc=str(build/'qcc');records=[]
def run(name,args,extra=None,expected=0):
 e=env|dict(extra or {});p=subprocess.run(args,env=e,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);(out/(name+'.log')).write_text(p.stdout);r={'name':name,'args':args,'exit_code':p.returncode,'expected':expected};records.append(r);(out/'steps.json').write_text(json.dumps(records,indent=2)+'\n');assert p.returncode==expected,(r,p.stdout[-2000:]);return p.stdout
version=run('compiler-version',[qcc,'--version']);digest,=re.findall(r'^AOT runtime identity: ([0-9a-f]{64})$',version,re.M)
with (build/'libqore.so.20.0.0').open('rb') as f:assert identity.read_identity(f)==('runtime',digest)
source_file=fixtures/'RpmIdentityProbe.qm';source_file.write_text('%modern\nmodule RpmIdentityProbe { version = "1.0"; desc = "RPM identity qualification"; author = "Qore"; license = "MIT"; }\npublic int sub rpm_identity_answer() { return 42; }\n')
vg=['valgrind','--error-exitcode=99','--leak-check=full','--show-leak-kinds=all','--errors-for-leak-kinds=definite,indirect,possible','--track-fds=yes']
for label,override in [('matching',None),('mismatching','a'*64)]:
 directory=modules/label;directory.mkdir();module=directory/'RpmIdentityProbe.qmod';extra={'QORE_AOT_TEST_RUNTIME_IDENTITY':override} if override else {}
 text=run(label+'-compile',[qore,'-b','--enable-debug','--compile-module','--output',str(module),str(source_file)],extra)
 with module.open('rb') as f:assert identity.read_identity(f)==('module',override or digest)
 for valgrind in [False,True]:
  args=[qore,'-b','--enable-debug','-l',str(module),'-nX','rpm_identity_answer()'];log=run(label+('-load-valgrind' if valgrind else '-load'),(vg if valgrind else [])+args,expected=2 if override else 0)
  if override:
   assert digest in log and override in log and 'rebuild' in log.lower() and 'LOAD-MODULE-ERROR' in log
  elif not valgrind:assert log.strip()=='42',log
  if valgrind:assert 'ERROR SUMMARY: 0 errors' in log
directory=modules/'valgrind-compiled';directory.mkdir();module=directory/'RpmIdentityProbe.qmod';log=run('compiler-valgrind',vg+[qore,'-b','--enable-debug','--compile-module','--output',str(module),str(source_file)]);assert 'ERROR SUMMARY: 0 errors' in log
with module.open('rb') as f:assert identity.read_identity(f)==('module',digest)
assert run('valgrind-compiled-load',[qore,'-b','--enable-debug','-l',str(module),'-nX','rpm_identity_answer()']).strip()=='42'
(out/'status.json').write_text(json.dumps({'exit_code':0,'mode':mode,'digest':digest,'checks':len(records),'library_sha256':hashlib.sha256((build/'libqore.so.20.0.0').read_bytes()).hexdigest()},indent=2)+'\n');print(mode,'actual identity/load/compile Valgrind checks passed')
