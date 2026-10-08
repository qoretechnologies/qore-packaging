# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import copy,hashlib,io,json,tarfile,runpy
root=Path.cwd();base=root/'work/grpc-macro-source-20261008';repo=root/'work/checkouts/module-grpc-native-dependencies-20261008';out=root/'work/grpc-credit-layout-candidate-20261008';out.mkdir()
manifest=json.loads((base/'source-manifest.json').read_text())
changes=['test/test-rpm-layout.py','rpm/dependencies.rst','qore-grpc-module.spec','test/salesforce-pubsub.qtest','qlib/SalesforcePubSubDataProvider/SalesforcePubSubSubscription.qc','qlib/SalesforcePubSubDataProvider/SalesforcePubSubDataProvider.qm'];top='qore-grpc-module-1.0.0';archive=top+'.tar.xz';members={}
with tarfile.open(base/archive) as source:
 for item in source:
  members[item.name]=(copy.copy(item),source.extractfile(item).read() if item.isfile() else None)
for name in changes:
 p=repo/name;data=p.read_bytes();item=tarfile.TarInfo(top+'/'+name);item.mode=p.stat().st_mode&0o777;item.size=len(data);item.mtime=manifest['source_date_epoch'];item.uid=item.gid=0;item.uname=item.gname='root';members[item.name]=(item,data)
with tarfile.open(out/archive,'w:xz',format=tarfile.PAX_FORMAT) as dest:
 for name,(item,data) in sorted(members.items()):dest.addfile(item,io.BytesIO(data) if data is not None else None)
recipe=(repo/'qore-grpc-module.spec').read_text();(out/'qore-grpc-module.spec').write_text(recipe)
(out/'qore-grpc-module.changes').write_text(runpy.run_path('tools/packaging.py')['obs_changelog'](recipe))
manifest['candidate']=True;manifest['source_overlay']={name:hashlib.sha256((repo/name).read_bytes()).hexdigest() for name in changes};manifest['sources']={name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in manifest['sources']}
(out/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(out)
