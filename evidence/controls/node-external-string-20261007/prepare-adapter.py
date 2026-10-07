# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
out=Path('/control');root=Path('/work/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1')
s=(out/'fixed.cc').read_text();a=s.index('v8::String::ExternalStringResourceBase* GetExternalResourceFromForwardingTable(');b=s.index('\n}\n',a)+3
s=s[:a]+'''// Test adapter: the public getter accesses this same forwarding table in the
// packaged runtime. Hidden isolate globals prevent linking the internal helper
// from an executable into the distribution's shared libnode.
v8::String::ExternalStringResourceBase* GetExternalResourceFromForwardingTable(
    const v8::String* api_string, i::Tagged<i::String>, uint32_t, bool* is_one_byte) {
  v8::String::Encoding encoding;
  auto resource = api_string->GetExternalStringResourceBase(v8::Isolate::GetCurrent(), &encoding);
  *is_one_byte = encoding == v8::String::ONE_BYTE_ENCODING;
  return resource;
}
'''+s[b:]
s=s.replace('          str, raw_hash_field, &is_one_byte);','          this, str, raw_hash_field, &is_one_byte);')
(out/'fixed-adapter.cc').write_text(s)
# A second control has the original incomplete assignment, using the same adapter.
old='''      expected = is_one_byte
                     ? nullptr
                     : reinterpret_cast<const ExternalStringResource*>(resource);'''
new='''      if (!is_one_byte) {
        expected = reinterpret_cast<const ExternalStringResource*>(resource);
      }'''
assert s.count(old)==1;(out/'original-adapter.cc').write_text(s.replace(old,new))
records=[]
for mode in ('original','fixed'):
 compile=json.loads((out/'fixed-status.json').read_text())[0]['command']
 compile=[x.replace('/control/fixed.', '/control/'+mode+'-adapter.') for x in compile]
 link=json.loads((out/'fixed-status.json').read_text())[1]['command']
 link=[x.replace('/control/fixed.o','/control/'+mode+'-adapter.o').replace('/control/fixed','/control/'+mode+'-adapter') if x=='/control/fixed' else x.replace('/control/fixed.o','/control/'+mode+'-adapter.o') for x in link]
 for name,cmd in [(mode+'-adapter-compile',compile),(mode+'-adapter-link',link),(mode+'-adapter-ordinary',['/control/'+mode+'-adapter','ordinary']),(mode+'-adapter-shared',['/control/'+mode+'-adapter','shared'])]:
  with (out/(name+'.log')).open('x') as log:r=subprocess.run(cmd,cwd=root/'out',stdout=log,stderr=subprocess.STDOUT)
  records.append(dict(name=name,command=cmd,exit_code=r.returncode));(out/'adapter-status.json').write_text(json.dumps(records,indent=2)+'\n')
  if 'compile' in name or 'link' in name or mode=='fixed':r.check_returncode()
