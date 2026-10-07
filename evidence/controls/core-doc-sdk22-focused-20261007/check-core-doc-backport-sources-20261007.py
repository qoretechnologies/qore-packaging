# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import importlib.util,json
repo=Path('work/checkouts/qore-documentation-sdk-20261006').resolve()
loader=importlib.util.spec_from_file_location('guides',repo/'doxygen/check-guide-refs.py');m=importlib.util.module_from_spec(loader);loader.loader.exec_module(m)
sources=m.repository_sources(repo)
application=json.loads(Path('results/core-doc-backports-application-20261007.json').read_text())
for row in application['changes']:
 path=repo/row['file']
 if path.parts[len(repo.parts)] in m.SOURCE_DIRS and path.suffix in m.SOURCE_SUFFIXES:
  sources[path]=path.read_text(errors='replace')
findings=m.check_sources(sources)
result={'source_files':len(sources),'findings':[{'file':str(p.relative_to(repo)),'line':line,'obsolete':old,'replacement':new} for p,line,old,new in findings]}
Path('results/core-doc-backport-guide-source-check-20261007.json').write_text(json.dumps(result,indent=2)+'\n')
print(result['source_files'],'source files;',len(findings),'obsolete guide references')
for row in result['findings'][:25]:print(row)
raise SystemExit(bool(findings))
