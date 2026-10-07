import json,subprocess
from pathlib import Path
w=Path('/fixture');count=0
for name,line,old,new in json.loads((w/'comments.json').read_text()):
 outputs=[]
 for kind,content in [('original',old),('fixed',new)]:
  r=subprocess.run(['g++','-E','-P','-x','c++','-Wcomment',*(['-Werror'] if kind=='fixed' else []),'-'],input=content,capture_output=True,text=True)
  assert r.returncode==0,(name,line,kind,r.stderr)
  if kind=='fixed':assert not r.stderr,(name,line,r.stderr)
  outputs.append(r.stdout)
 assert outputs[0]==outputs[1],(name,line,outputs)
 count+=1
print(count,'comment chains preserve preprocessed tokens and compile without warnings',flush=True)
flags=json.loads((w/'flags.json').read_text())
for kind in ['positive','negative']:
 r=subprocess.run([*flags,'-c',str(w/(kind+'.cc')),'-o',str(w/(kind+'.o'))],capture_output=True,text=True)
 (w/(kind+'.log')).write_text(r.stdout+r.stderr)
 if kind=='positive':assert r.returncode==0 and not r.stderr,(r.returncode,r.stderr)
 else:
  assert r.returncode and 'Should use BitcastTaggedToWordForTagAndSmiBits instead.' in r.stderr,(r.returncode,r.stderr)
  assert 'no return statement' not in r.stderr and 'control reaches end' not in r.stderr,r.stderr
 print(kind,'CodeAssembler compile expectation passed',flush=True)
