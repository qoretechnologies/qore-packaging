# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
w=Path('/fixture')
for name,line,old,new in json.loads((w/'comments.json').read_text()):
 outputs=[]
 for kind,content in [('original',old),('fixed',new)]:
  r=subprocess.run(['g++','-E','-P','-x','c++','-Wcomment',*(['-Werror'] if kind=='fixed' else []),'-'],input=content,capture_output=True,text=True)
  assert r.returncode==0,(name,line,kind,r.stderr)
  if kind=='fixed':assert not r.stderr,(name,line,r.stderr)
  else:assert 'warning: multi-line comment' in r.stderr,(name,line,r.stderr)
  outputs.append(r.stdout)
 assert outputs[0]==outputs[1],(name,line,outputs)
print('Six original comment warnings reproduced; corrected comments preserve tokens with no warnings')
