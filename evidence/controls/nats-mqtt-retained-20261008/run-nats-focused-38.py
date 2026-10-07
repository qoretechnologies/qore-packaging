# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import concurrent.futures, importlib.util, json, subprocess, sys
root=Path.cwd();config=json.loads(Path(sys.argv[1]).read_text())
loader=importlib.util.spec_from_file_location('builder',root/'tools/build-local.py');builder=importlib.util.module_from_spec(loader);loader.loader.exec_module(builder)
images={'fedora':'sha256:f1f889474f303ffe6f98b381e3061e812daa34e9018a00c4a25cb65f9a82fee9','leap':'sha256:2b44d9f9636b4e454c93b06c95cd9ff9f23136b159e80ac2ded68b32d7f1190b','el10':'sha256:0bc68ce99e4cd1340c79149a0601d7496351acd655a537ddae23116f036370c5'}
def run(case):
 out=root/'results'/case['name'];out.mkdir()
 with builder.build_network('docker',True) as (network,info):
  cmd=['docker','run','--rm','--init','--network',network,'--tmpfs','/tmp:rw,exec,size=4g,mode=1777','--user','1019:100','-e','GOMAXPROCS='+str(case.get('gomaxprocs',2)),'-e','GOTOOLCHAIN=local','-e','GOPROXY=off','-e','GOSUMDB=off','-e','GOFLAGS=-mod=vendor','-e','GOCACHE=/cache','-e','GOPATH=/gopath','-v',str(root/case.get('source',config.get('source','work/nats-prepared-18/nats-server-2.14.7')))+':/source:'+('rw' if case.get('writable_disk') else 'ro'),'-v',str(root/'work/nats-go-cache')+':/cache','-v',str(root/'work/nats-go-path')+':/gopath','-v',str(root/case.get('sublist','work/nats-sublist-notification-1/sublist.go'))+':/source/server/sublist.go:ro']
  for host,guest in case.get('overlays',{}).items():cmd+=['-v',str(root/host)+':/source/'+guest+':ro']
  cmd+=['-w','/source',images[case['target']]]
  if case.get('writable_copy'):
   cmd+=['sh','-c','cp -a /source /tmp/source && cd /tmp/source && exec "$@"','nats-focused']
  cmd+=['go','test',*(['-race'] if case.get('race') else []),'-v','-short','-count='+str(case['count']),'-timeout=20m','-run',case['pattern'],case.get('package','./server')]
  with (out/'tests.log').open('w') as log:result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
  (out/'status.json').write_text(json.dumps({'exit_code':result.returncode,'command':cmd,'network':info},indent=2)+'\n')
 return case['name'],result.returncode
with concurrent.futures.ThreadPoolExecutor(max_workers=config.get('workers',3)) as pool:print(dict(pool.map(run,config['cases'])))
