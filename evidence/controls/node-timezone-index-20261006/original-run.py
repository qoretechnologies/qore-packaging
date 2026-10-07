from pathlib import Path
import json,shlex,subprocess
out=Path('/work');flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','icu-i18n','icu-uc'],text=True));records=[]
commands=[('compile',['g++','-std=c++20','-O2','-g','-Wall','-Wextra','/work/original.cc',*flags,'-o','/work/original']),('normal',['/work/original']),('memory',['valgrind','--error-exitcode=99','--leak-check=full','--errors-for-leak-kinds=all','--log-file=/work/valid-valgrind.log','/work/original']),('negative',['valgrind','--error-exitcode=99','--track-origins=yes','--leak-check=full','--log-file=/work/negative-valgrind.log','/work/original','-1'])]
for name,command in commands:
 with (out/(name+'.log')).open('x') as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=120)
 records.append(dict(name=name,exit_code=r.returncode,command=command));(out/'status.json').write_text(json.dumps(records,indent=2)+'\n')
 if name!='negative':r.check_returncode()
