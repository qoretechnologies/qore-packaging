# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,shlex,subprocess
root=Path.cwd();repo=root.parent/'qore';out=root/'results/bson-array-final-targets-20261008';out.mkdir()
paths=['modules/mongodb/src/bson_conversion.cpp','modules/mongodb/test/bson-array.cpp']
pins={p:hashlib.sha256((repo/p).read_bytes()).hexdigest() for p in paths};(out/'source-hashes.json').write_text(json.dumps(pins,indent=2)+'\n')
def qualify(target):
    dest=out/target;dest.mkdir()
    previous=root/f'results/{target}-core-fixes-combined-candidate-20261008'
    record=json.loads((previous/'build.json').read_text());image=record['command'][record['command'].index('sh')-1]
    hostlink=next(previous.glob('rpmbuild/BUILD/**/build/modules/mongodb/CMakeFiles/mongodb.dir/link.txt'))
    hostbuild=hostlink.parents[4];build=Path('/work')/hostbuild.relative_to(previous);checkout=build.parent
    prefix=['docker','run','--rm','--init','--network','none','--user',str(os.getuid())+':'+str(os.getgid()),
        '-e','RPM_ARCH=x86_64','-e','RPM_PACKAGE_NAME=qore','-e','RPM_PACKAGE_VERSION=3.0.0~git20261008.22','-e','RPM_PACKAGE_RELEASE=22',
        '-v',str(previous)+':/work:ro','-v',str(repo)+':/source:ro','-v',str(dest)+':/out','-w',str(build/'modules/mongodb'),image]
    defs={}
    for line in (hostlink.parent/'flags.make').read_text().splitlines():
        if ' = ' in line:
            k,v=line.split(' = ',1);defs[k]=shlex.split(v)
    link=shlex.split(hostlink.read_text());compiler=link[0]
    compile_flags=[*defs['CXX_DEFINES'],*defs['CXX_INCLUDES'],*defs['CXX_FLAGS'],'-Wall','-Werror=deprecated-declarations']
    converter=[compiler,*compile_flags,'-c','/source/'+paths[0],'-o','/out/bson_conversion.cpp.o']
    fixture=[compiler,*compile_flags,'-c','/source/'+paths[1],'-o','/out/bson-array.cpp.o']
    obj_end=max(i for i,a in enumerate(link) if a.endswith('.o'))
    native_link=[a for a in link[:link.index('-o')] if a!='-shared' and not a.startswith('-Wl,--dependency-file=')]
    native_link+=['-o','/out/bson-array-test','/out/bson-array.cpp.o','/out/bson_conversion.cpp.o',
        'CMakeFiles/mongodb.dir/QC_ObjectId.cpp.o',str(build/'libqore.so'),*link[obj_end+1:]]
    env=['env','LD_LIBRARY_PATH='+str(build)]
    steps=[('converter-compile',converter),('fixture-compile',fixture),('link',native_link),('native',env+['/out/bson-array-test']),
        ('valgrind',env+['valgrind','--error-exitcode=99','--leak-check=full','--show-leak-kinds=definite,indirect,possible','--errors-for-leak-kinds=definite,indirect,possible','/out/bson-array-test'])]
    if target=='leap':
        original=converter.copy();original[original.index('/source/'+paths[0])]=str(checkout/paths[0]);original[-1]='/out/original.o'
        with (dest/'original-compile.log').open('x') as log:p=subprocess.run(prefix+original,stdout=log,stderr=subprocess.STDOUT)
        s=(dest/'original-compile.log').read_text();assert p.returncode and s.count('error:')==1 and 'bson_append_array_begin' in s
        (dest/'original-negative.json').write_text(json.dumps({'exit_code':p.returncode,'deprecated_calls':1})+'\n')
    rows=[]
    for name,args in steps:
        run_prefix=prefix.copy()
        if target=='fedora' and name=='valgrind':run_prefix[-1]='sha256:1d0b9746139ba0ac3822952a6b7248cb54ab48f7241d879d9cf55ff84c02d7d0'
        command=run_prefix+args
        with (dest/(name+'.log')).open('x') as log:p=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
        rows.append({'name':name,'command':command,'exit_code':p.returncode});(dest/'status.json').write_text(json.dumps(rows,indent=2)+'\n');print(target,name,p.returncode,flush=True)
        if p.returncode:return target,p.returncode
    return target,0
with ThreadPoolExecutor(max_workers=3) as pool:result=dict(pool.map(qualify,['fedora','leap','el10']))
assert pins=={p:hashlib.sha256((repo/p).read_bytes()).hexdigest() for p in paths}
(out/'status.json').write_text(json.dumps(result,indent=2)+'\n');raise SystemExit(any(result.values()))
