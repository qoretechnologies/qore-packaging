# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,os,subprocess,urllib.request,shlex,hashlib,re
root=Path.cwd();source=root/'work/llvm-ciso646-20261008';out=root/'results/llvm-ciso646-20261008';out.mkdir()
image='sha256:a3a4d38d5db8770fccc4a460aedd5f49f76bf5226825c0d051ecae4422d99b19'
prefix=['docker','run','--rm','--init','--network','none','--user',str(os.getuid())+':'+str(os.getgid()),'-v',str(source)+':/source:ro','-v',str(out)+':/out','-w','/out',image]
header=subprocess.check_output(prefix+['cat','/usr/include/llvm/Support/Threading.h'])
ciso=subprocess.check_output(prefix+['cat','/usr/include/c++/15/ciso646']);(out/'ciso646').write_bytes(ciso)
line=b'#include <ciso646> // So we can check the C++ standard lib macros.\n';assert header.count(line)==1
for variant,contents in [('original',header),('upstream-include-fix',header.replace(line,b''))]:
 p=out/variant/'llvm/Support/Threading.h';p.parent.mkdir(parents=True);p.write_bytes(contents)
for version in ['19.1.7','20.1.0']:
 url=f'https://raw.githubusercontent.com/llvm/llvm-project/llvmorg-{version}/llvm/include/llvm/Support/Threading.h'
 with urllib.request.urlopen(url,timeout=60) as response:data=response.read()
 (out/('upstream-'+version+'.h')).write_bytes(data)
 assert (line in data)==(version=='19.1.7')
flags=shlex.split(subprocess.check_output(prefix+['llvm-config','--cxxflags'],text=True));flags=[f for f in flags if f!='-fno-exceptions']
libs=shlex.split(subprocess.check_output(prefix+['llvm-config','--ldflags','--libs','support','--system-libs'],text=True))
rows=[]
def run(name,args,expected=0):
 with (out/(name+'.log')).open('x') as log:r=subprocess.run(prefix+args,stdout=log,stderr=subprocess.STDOUT)
 rows.append({'name':name,'command':prefix+args,'exit_code':r.returncode});(out/'status.json').write_text(json.dumps(rows,indent=2)+'\n');assert r.returncode==expected,(name,r.returncode);print(name,r.returncode,flush=True)
for variant in ['original','upstream-include-fix']:
 common=['c++','-I/out/'+variant,*flags,'-std=c++20','-Wall','-pthread']
 for mode,options in [('release',['-O2','-DNDEBUG']),('debug',['-O0','-g'])]:
  stem=variant+'-'+mode
  run(stem+'-compile',[*common,*options,'/source/control.cpp',*libs,'-o','/out/'+stem])
  run(stem+'-native',['/out/'+stem])
  run(stem+'-valgrind',['valgrind','--error-exitcode=99','--leak-check=full','--show-leak-kinds=definite,indirect,possible','--errors-for-leak-kinds=definite,indirect,possible','/out/'+stem])
 run(variant+'-preprocess',[*common,'-E','-P','/source/control.cpp','-o','/out/'+variant+'.ii'])
 run(variant+'-macros',[*common,'-E','-dM','/source/control.cpp','-o','/out/'+variant+'.macros'])
 run(variant+'-text',['objcopy','--dump-section','.text=/out/'+variant+'.text','/out/'+variant+'-release','/out/'+variant+'-inspect'])
a=(out/'original.ii').read_text().splitlines();b=(out/'upstream-include-fix.ii').read_text().splitlines()
# ciso646 itself contributes only diagnostic pragmas; all C++ tokens agree.
pragmas=['#pragma GCC diagnostic push','#pragma GCC diagnostic ignored "-Wc++23-extensions"','#pragma GCC diagnostic pop']
normalized=lambda lines:[l for l in lines if l.strip() not in pragmas and l.strip()]
assert normalized(a)==normalized(b),'preprocessed C++ tokens differ'
a=set((out/'original.macros').read_text().splitlines());b=set((out/'upstream-include-fix.macros').read_text().splitlines());assert a-b=={'#define _GLIBCXX_CISO646 '} and not b-a,(a-b,b-a)
assert (out/'original.text').read_bytes()==(out/'upstream-include-fix.text').read_bytes()
(out/'verified.json').write_text(json.dumps({'checks_per_run':8009,'functional_runs':4,'valgrind_runs':4,'preprocessed_cpp_identical':True,'only_macro_difference':'_GLIBCXX_CISO646 include guard','release_machine_code_identical':True,'scope':'Qualification controls only: no installed LLVM header, Qore source or compiler flag changed.'},indent=2)+'\n')
