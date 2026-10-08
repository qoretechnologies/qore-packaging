# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'results/xml-metadata-payload2-20261008'
OUT.mkdir(exist_ok=False)
SCRIPT = OUT / 'inspect.py'
SCRIPT.write_text('''from pathlib import Path, PurePosixPath
import hashlib,json,stat,subprocess,sys
out=Path('/results')
def extract(rpm,label):
 directory=out/label;directory.mkdir()
 with subprocess.Popen(['rpm2cpio',rpm],stdout=subprocess.PIPE,stderr=subprocess.PIPE) as producer:
  result=subprocess.run(['cpio','--extract','--make-directories','--no-preserve-owner','--no-absolute-filenames','--quiet','./usr/share/qore/metadata/xml/*','./usr/share/qore/i18n/*'],cwd=directory,stdin=producer.stdout,capture_output=True)
  producer.stdout.close();errors=producer.stderr.read();code=producer.wait()
 assert code==0 and result.returncode==0 and not errors and not result.stderr,(code,result.returncode,errors,result.stderr)
 return directory
before=extract(sys.argv[1],'before');after=extract(sys.argv[2],'after')
def inventory(root):
 result={}
 for path in root.rglob('*'):
  assert not path.is_symlink(),path
  if path.is_file():
   json.loads(path.read_text()) if path.suffix=='.json' else None
   result[str(path.relative_to(root))]=(hashlib.sha256(path.read_bytes()).hexdigest(),stat.S_IMODE(path.stat().st_mode))
 return result
old=inventory(before);new=inventory(after);assert old.keys()==new.keys()
relocations={}
old_nvr=subprocess.check_output(['rpm','-qp','--qf','%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH}',sys.argv[1]],text=True)
new_nvr=subprocess.check_output(['rpm','-qp','--qf','%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH}',sys.argv[2]],text=True)
old_prefix='/usr/src/debug/'+old_nvr+'/src/'
new_prefix='/usr/src/debug/'+new_nvr+'/src/'
for name,record in old.items():
 assert record[1]==new[name][1]
 if record[0]==new[name][0]:continue
 assert name.startswith('usr/share/qore/metadata/xml/') and name.endswith('.meta.json'),name
 old_data=(before/name).read_text();new_data=(after/name).read_text()
 old_json=json.loads(old_data);new_json=json.loads(new_data)
 assert [key for key in old_json.keys()|new_json.keys() if old_json.get(key)!=new_json.get(key)]==['source_file']
 previous=old_json['source_file'];current=new_json['source_file']
 assert previous.startswith(old_prefix) and current==new_prefix+previous[len(old_prefix):]
 assert old_data.replace('"source_file":'+json.dumps(previous),'"source_file":'+json.dumps(current),1)==new_data
 relocations[name]={'old':previous,'new':current}
assert len(relocations) in (0,11)
metadata=after/'usr/share/qore/metadata/xml'
modules=sorted(p.name for p in metadata.glob('*.qm.meta.json'));assert len(modules)==17
duplicates=['SoapClientIo.qm.meta.json','WebContentUtil.qm.meta.json','WebDavClientIo.qm.meta.json']
assert len({(metadata/name).stat().st_ino for name in duplicates})==1
catalog=after/'usr/share/qore/i18n'
manifest,=list((catalog/'.qore-catalog-manifests').iterdir());assert manifest.name=='qore-xml-module.manifest'
paths=[line for line in manifest.read_text().splitlines() if line and not line.startswith('#')]
assert paths==sorted(set(paths))
assert all(not PurePosixPath(p).is_absolute() and '..' not in PurePosixPath(p).parts and str(PurePosixPath(p))==p for p in paths)
actual=sorted(str(p.relative_to(catalog)) for p in catalog.rglob('*.json'));assert paths==actual and paths
record={'metadata_files':len(list(metadata.iterdir())),'module_metadata':modules,'shared_metadata_files':duplicates,'new_file_hashes_and_modes':new,'release_source_path_updates':relocations,'catalog_count':len(paths),'ownership_manifest':manifest.read_text(),'checks':'All catalog and module metadata bytes and modes match; the only native metadata changes are exact release-specific source_file paths; known duplicate metadata files share one inode; ownership manifest safely and exactly covers all catalogs.'}
(out/'payload.json').write_text(json.dumps(record,indent=2)+'\\n')
print(json.dumps({'files':len(new),'metadata':record['metadata_files'],'catalogs':len(paths)}))
''')


def run(target):
    folder = OUT / target
    folder.mkdir()
    paths = []
    command = ['docker', 'run', '--rm', '--init', '--network', 'none', '--user', '1019:100',
               '-v', str(SCRIPT) + ':/inspect.py:ro', '-v', str(folder) + ':/results']
    inputs = {}
    for label, build in (('old', ROOT / f'results/{target}-xml-final-build-2'),
                         ('new', ROOT / f'results/{target}-xml-metadata-candidate-20261008')):
        state = json.loads((build / 'build.json').read_text())
        assert state['exit_code'] == 0
        name, = [p for p in state['artifacts'] if '/RPMS/' in p and Path(p).name.startswith('qore-xml-module-2.')]
        path = build / name
        with path.open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == state['artifacts'][name]
        paths.append('/' + label + '/' + name)
        command.extend(['-v', str(build) + ':/' + label + ':ro'])
        inputs[label] = {'rpm': str(path.relative_to(ROOT)), 'sha256': state['artifacts'][name]}
    command.extend(['sha256:e9f88fde9890db694ae37058e1bc41b34385ea5d04fc4c6cba1d666bd23c0887',
                    'python3', '-B', '-W', 'error', '/inspect.py', *paths])
    with (folder / 'checks.log').open('w') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    record = {'exit_code': result.returncode, 'command': command, 'inputs': inputs}
    (folder / 'status.json').write_text(json.dumps(record, indent=2) + '\n')
    return target, record


with ThreadPoolExecutor(max_workers=3) as pool:
    results = dict(pool.map(run, ('fedora', 'leap', 'el10')))
(OUT / 'status.json').write_text(json.dumps(results, indent=2) + '\n')
assert all(r['exit_code'] == 0 for r in results.values()), results
print(json.dumps({t: r['exit_code'] for t, r in results.items()}))
