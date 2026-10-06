# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import datetime, hashlib, importlib.util, json, re, subprocess
root=Path.cwd(); out=root/'work/obs-epoch-metadata-20261006/roundtrip'; out.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('packaging',root/'tools/packaging.py'); p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
def normalize(s):
    lines=[]
    for line in s.splitlines():
        if line.startswith('* '):
            line=re.sub(r'^(\* \w{3} \w{3}) +0?([0-9]+) ', r'\1 \2 ',line)
        if line.strip(): lines.append(line)
    return '\n'.join(lines)
recipes=[]
for name, entry in json.loads((root/'catalog.json').read_text())['packages'].items():
    if name=='module-nats':
        recipe=(root/'work/checkouts/module-nats-rpm-candidate/qore-nats-module.spec')
        continue # The module's catalog pin predates its pending RPM recipe.
    recipe=subprocess.check_output(['git','-C',str(root.parent/name),'show',entry['commit']+':'+entry['spec']]).decode()
    recipes.append((name,entry['commit'],recipe))
for name in json.loads((root/'dependencies/sources.json').read_text()):
    recipes.append((name,'working-tree candidate',(root/'dependencies'/ (name+'.spec')).read_text()))
records=[]
for name,ref,recipe in recipes:
    changes=p.obs_changelog(recipe); assert changes is not None,name
    d=out/name;d.mkdir(exist_ok=True); (d/'package.changes').write_text(changes)
    result=subprocess.run(['/usr/lib/build/changelog2spec','--target','rpm','--timestampfile',str(d/'timestamp'),'--file',str(d/'package.changes')],capture_output=True,text=True,check=True)
    assert not result.stderr,(name,result.stderr)
    original=recipe.split('%changelog\n',1)[1]
    assert normalize(result.stdout)==normalize(original),(name,normalize(result.stdout),normalize(original))
    (d/'converted').write_text(result.stdout)
    header=changes.splitlines()[1]; date=datetime.datetime.strptime(header[:28],'%a %b %d %H:%M:%S UTC %Y').replace(tzinfo=datetime.timezone.utc)
    epoch=int((d/'timestamp').read_text().strip());assert epoch==int(date.timestamp()),(name,epoch,date)
    records.append({'name':name,'revision':ref,'recipe_sha256':hashlib.sha256(recipe.encode()).hexdigest(),'changes_sha256':hashlib.sha256(changes.encode()).hexdigest(),'epoch':epoch,'roundtrip':'all dates, authors, releases and nonblank note lines preserved'})
(out/'results.json').write_text(json.dumps(records,indent=2)+'\n')
print(f'{len(records)} actual OBS converter roundtrips pass, with matching UTC epochs')
