# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import os,subprocess,json
root=Path.cwd();out=root/'results/grpc-layout-controls-20261008';staged=out/'staged';source=out/'source/qore-grpc-module-1.0.0';test=source/'test/test-rpm-layout.py'
cmd=['python3','-B','-W','error',str(test),'--root',str(staged),'--license-dir','/usr/share/licenses','--data-dir','/usr/share','--doc-dir','/usr/share/doc/packages','-v'];records={}
def run(name,expected):
 r=subprocess.run(cmd,capture_output=True,text=True);(out/(name+'.log')).write_text(r.stdout+r.stderr);assert r.returncode==expected,(name,r.stderr);records[name]=r.returncode
run('positive',0)
p=staged/'usr/share/doc/packages/qore-grpc-module-doc/examples/interop/.gitignore';p.write_text('test_pb2*\n')
try:run('negative-version-control-file',1)
finally:p.unlink()
p=staged/'usr/share/doc/packages/qore-grpc-module-doc/examples/grpc.qtest';old=p.read_bytes();p.write_bytes(old.replace(b'#!/usr/bin/qore\n',b'#!/usr/bin/env qore\n',1))
try:run('negative-interpreter',1)
finally:p.write_bytes(old)
mode=p.stat().st_mode;p.chmod(0o644)
try:run('negative-nonexecutable',1)
finally:p.chmod(mode)
p=staged/'usr/share/licenses/qore-grpc-module/COPYING.MIT';old=p.read_bytes();p.unlink();p.write_bytes(old)
try:run('negative-duplicate-license',1)
finally:p.unlink();p.hardlink_to(p.with_name('LICENSE'))
p=staged/'usr/share/qore/metadata/grpc/GrpcUtil.qm.meta.json';peer=p.with_name('SalesforcePubSubDataProvider.qm.meta.json');assert peer.read_bytes()==p.read_bytes();old=p.read_bytes();p.unlink();p.write_bytes(old)
try:run('negative-duplicate-metadata',1)
finally:p.unlink();p.hardlink_to(peer)
p=staged/'usr/share/licenses/qore-grpc-module/Apache-2.0.txt';old=p.read_bytes();p.unlink()
try:run('negative-missing-license',1)
finally:p.write_bytes(old);p.chmod(0o644)
run('restored',0)
(out/'status.json').write_text(json.dumps(records,indent=2)+'\n');print(records)
