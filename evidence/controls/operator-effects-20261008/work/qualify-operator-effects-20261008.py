# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib,json,os,shlex,subprocess
root=Path.cwd();repo=root/'work/checkouts/qore-operator-effects-20261008';out=root/'results/operator-effects-final-20261008';out.mkdir()
files=['include/qore/intern/QoreOperatorNode.h','lib/AbstractQoreNode.cpp','examples/test/cmake/operator_root_effect.cpp','examples/test/cmake/test_operator_root_effect.py'];pins={p:hashlib.sha256((repo/p).read_bytes()).hexdigest() for p in files};(out/'source-hashes.json').write_text(json.dumps(pins,indent=2)+'\n')
def qualify(target):
 dest=out/target;dest.mkdir();env=os.environ.copy();libpin=None
 if target.startswith('host-'):
  build=root.parent/'qore'/('build-debug' if target=='host-debug' else 'build')
  lib=build/'libqore.so.20.0.0';libpin=hashlib.sha256(lib.read_bytes()).hexdigest()
  env.update(QORE_TEST_BUILD_DIR=str(build),QORE_TEST_OUTPUT_DIR=str(dest/'test'),QORE_TEST_VALGRIND='1',QORE_TEST_CXXFLAGS='-Og -g -DDEBUG' if target=='host-debug' else '-O3 -g -DNDEBUG')
  command=['python3','-B','-W','error',str(repo/'examples/test/cmake/test_operator_root_effect.py'),'-v']
 else:
  previous=root/f'results/{target}-core-fixes-combined-candidate-20261008';record=json.loads((previous/'build.json').read_text());image=record['command'][record['command'].index('sh')-1]
  if target=='fedora':image='sha256:1d0b9746139ba0ac3822952a6b7248cb54ab48f7241d879d9cf55ff84c02d7d0'
  flags=next(previous.glob('rpmbuild/BUILD/**/build/CMakeFiles/libqore.dir/flags.make'));hostbuild=flags.parents[2];build=Path('/work')/hostbuild.relative_to(previous)
  cxxflags=next(s.split(' = ',1)[1] for s in flags.read_text().splitlines() if s.startswith('CXX_FLAGS = '))
  command=['docker','run','--rm','--init','--network','none','--user',str(os.getuid())+':'+str(os.getgid()),'-e','LC_ALL=C','-e','RPM_ARCH=x86_64','-e','RPM_PACKAGE_NAME=qore','-e','RPM_PACKAGE_VERSION=3.0.0~git20261008.22','-e','RPM_PACKAGE_RELEASE=22',
   '-e','QORE_TEST_BUILD_DIR='+str(build),'-e','QORE_TEST_INCLUDE_DIR='+str(build.parent/'include'),'-e','QORE_TEST_OUTPUT_DIR=/out/test','-e','QORE_TEST_VALGRIND=1','-e','QORE_TEST_CXXFLAGS=-O3 -g -DNDEBUG',
   '-v',str(previous)+':/work:ro','-v',str(repo)+':/source:ro','-v',str(dest)+':/out','-w','/source',image,'python3','-B','-W','error','examples/test/cmake/test_operator_root_effect.py','-v']
 with (dest/'unit.log').open('x') as f:p=subprocess.run(command,env=env,stdout=f,stderr=subprocess.STDOUT)
 if libpin:assert libpin==hashlib.sha256(lib.read_bytes()).hexdigest(),str(lib)+' changed during qualification'
 (dest/'status.json').write_text(json.dumps({'command':command,'exit_code':p.returncode,'host_runtime_sha256':libpin},indent=2)+'\n');print(target,p.returncode,flush=True);return target,p.returncode
with ThreadPoolExecutor(max_workers=3) as pool:results=dict(pool.map(qualify,['fedora','leap','el10','host-release','host-debug']))
assert pins=={p:hashlib.sha256((repo/p).read_bytes()).hexdigest() for p in files};(out/'status.json').write_text(json.dumps(results,indent=2)+'\n');raise SystemExit(any(results.values()))
