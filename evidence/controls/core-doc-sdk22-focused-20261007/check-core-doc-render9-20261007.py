# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import collections,hashlib,json,os,select,re,xml.etree.ElementTree as E
from html.parser import HTMLParser
root=Path.cwd();out=root/'results/core-doc-corrections-render9-20261007'
fds=[]
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:
  argv=(proc/'cmdline').read_bytes().decode().split('\0')
  if 'work/render-core-doc-corrections9-20261007.py' in argv:fds.append(os.pidfd_open(int(proc.name)))
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
assert len(fds)<=1
if fds:select.select(fds,[],[]);os.close(fds[0])
status=json.loads((out/'status.json').read_text());diagnostics=[]
for p in sorted((out/'logs').glob('*.log')):
 for line in p.read_text(errors='replace').splitlines():
  if re.search(r'(?:warning:|error:|unhandled QORE|exception thrown)',line):diagnostics.append({'log':p.name,'line':line})
class Page(HTMLParser):
 def __init__(self):super().__init__();self.fragments=0;self.data=[];self.ids=set()
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  if tag=='div' and attrs.get('class')=='fragment':self.fragments+=1
  if 'id' in attrs:self.ids.add(attrs['id'])
  if 'name' in attrs:self.ids.add(attrs['name'])
 def handle_data(self,data):self.data.append(data)
checks={}
for mod in ['ConfluenceRestClient','Hl7v2Util','SqlUtil']:
 p=out/'docs/modules'/mod/'html'/('sql_operations.html' if mod=='SqlUtil' else 'index.html');parsed=Page();parsed.feed(p.read_text());text=''.join(parsed.data)
 if mod=='ConfluenceRestClient':checks[mod]=parsed.fragments>0 and 'ConfluenceRestClientIo conf' in text and '@code' not in text
 elif mod=='Hl7v2Util':checks[mod]=parsed.fragments>=2 and '\\r' in text and '\\F\\' in text and '@code' not in text and 'MSH|^~' in text
 else:checks[mod]='select_option_orderby_no_unique' in parsed.ids
indexes={mod:len(E.parse(out/(mod+'.tag')).getroot().findall('compound')) for mod in status['modules']}
record={'modules':len(status['modules']),'phase_exit_codes':{k:dict(collections.Counter(v.values())) for k,v in status.items() if isinstance(v,dict)},'diagnostics':diagnostics,'rendered_page_checks':checks,'parsed_indexes':indexes,'source_token_review':'results/core-doc-corrections-token-review3-20261007.json','limits':['This targeted render uses installed Leap SDK22 and a complete frozen seed-index set. A full canonical RPM build on all distributions is still required.']}
(root/'results/core-doc-render9-review-20261007.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items() if k not in ['parsed_indexes','limits','source_token_review']},indent=2));assert not diagnostics and all(checks.values()) and all(code==0 for phase in ['index','render'] for code in status[phase].values())
