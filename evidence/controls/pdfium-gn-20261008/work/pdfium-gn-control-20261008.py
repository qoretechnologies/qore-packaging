# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
import hashlib,importlib.util,json,os,subprocess,sys,difflib
from pathlib import Path
loader=importlib.util.spec_from_file_location('helper',Path('rpm/build.py'));helper=importlib.util.module_from_spec(loader);loader.loader.exec_module(helper)
record=Path('/control/final');record.mkdir(exist_ok=True)
actual_run=subprocess.run;commands=[]
def run(command,**kwargs):
 commands.append(command)
 if command[:2]==['python3','build/gen.py'] or command[0]=='ninja':
  return subprocess.CompletedProcess(command,0)
 if command[:2]==['gn-src/out/gn','gen']:
  return subprocess.CompletedProcess(command,0)
 return actual_run(command,**kwargs)
helper.subprocess.run=run
os.environ.update(CFLAGS='-O2 -g -flto=auto',CXXFLAGS='-O2 -g -flto=auto',LDFLAGS='-flto=auto -Wl,-z,relro')
helper.configure(2,bundled_freetype=sys.argv[1]=='el10')
helper.subprocess.run=actual_run
fixed=commands[-1];assert fixed[:4]==['gn-src/out/gn','gen','out/Release','--fail-on-unused-args']
assert all(x not in fixed[-1] for x in ['use_allocator_shim','use_partition_alloc_as_malloc'])
def call(name,cmd,expected):
 p=actual_run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 Path(record,name+'.log').write_text(p.stdout);Path(record,name+'.command.json').write_text(json.dumps(cmd,indent=2)+'\n')
 assert p.returncode==expected,(name,p.returncode,p.stdout)
 return p.stdout
def graph():
 return {str(p.relative_to('out/Release')):p.read_bytes() for p in Path('out/Release').rglob('*.ninja')}
rows=[]
for cpu in ['x64','arm64']:
 cmd=[*fixed[:-1],fixed[-1].replace('target_cpu="x64"','target_cpu="'+cpu+'"')]
 baseline=[x for x in cmd if x!='--fail-on-unused-args'];baseline[-1]+=' use_allocator_shim=false use_partition_alloc_as_malloc=false'
 log=call(cpu+'-baseline',baseline,0)
 assert 'Build argument has no effect' in log
 before=graph()
 strict=[*baseline[:3],'--fail-on-unused-args',*baseline[3:]]
 assert 'Build argument has no effect' in call(cpu+'-baseline-strict',strict,1)
 corrected=call(cpu+'-fixed',cmd,0)
 assert 'WARNING' not in corrected and 'ERROR' not in corrected,corrected
 after=graph();assert before.keys()==after.keys()
 differences=[n for n in before if before[n]!=after[n]]
 assert differences==['build.ninja'],differences
 old_line=b'  command = ../../gn-src/out/gn --root=../.. -q --regeneration gen .\n'
 new_line=b'  command = ../../gn-src/out/gn --root=../.. -q --fail-on-unused-args --regeneration gen .\n'
 assert before['build.ninja'].count(old_line)==1
 assert before['build.ninja'].replace(old_line,new_line)==after['build.ninja']
 (record/(cpu+'-build-before.ninja')).write_bytes(before['build.ninja'])
 (record/(cpu+'-build-fixed.ninja')).write_bytes(after['build.ninja'])
 for obsolete in ['use_allocator_shim','use_partition_alloc_as_malloc']:
  single=cmd.copy();single[-1]+=' '+obsolete+'=false'
  assert 'The variable "'+obsolete+'"' in call(cpu+'-reject-'+obsolete,single,1)
 negative=cmd.copy();negative[-1]+=' qore_unrecognized_build_option=true'
 assert 'qore_unrecognized_build_option' in call(cpu+'-negative',negative,1)
 call(cpu+'-restore',cmd,0)
 rows.append({'cpu':cpu,'identical_ninja_files':len(before)-1,'only_graph_difference':'build.ninja regeneration command adds --fail-on-unused-args; every compilation/link rule is byte-identical','ninja_sha256':{n:hashlib.sha256(data).hexdigest() for n,data in before.items()},'baseline_warning_reproduced':True,'baseline_strict_rejected':True,'fixed_strict_clean':True,'unknown_argument_rejected':True})
(record/'result.json').write_text(json.dumps({'target':sys.argv[1],'configurations':rows,'limits':'GN generation only; no native ARM compilation or new PDFium runtime build. Reuses bootstrap executable after comparing all GN source files to the pinned archive. Helper bootstrap calls bypassed; all compiler probes and GN executions are real.'},indent=2)+'\n')
print('PASS:',sys.argv[1],len(rows),'configurations',flush=True)
