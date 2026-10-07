# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json
import subprocess
source=Path('work/nats-prepared-45/nats-server-2.15.0');out=Path('work/nats-stream-create-trace-242-20261007');out.mkdir()
texts={name:(source/'server'/name).read_text() for name in ['jetstream_api.go','jetstream_cluster.go','jetstream_cluster_2_test.go']}
def change(file,name,transform):
    text=texts[file];a=text.index(name);b=text.index('\nfunc ',a+1)
    texts[file]=text[:a]+transform(text[a:b])+text[b:]
def requests(text):
    lines=text.splitlines(True);result=[]
    for index,line in enumerate(lines):
        result.append(line)
        if index==0:
            result.append('\tif subject == "$JS.API.STREAM.CREATE.TEST2" { fmt.Printf("CREATE-TRACE entry server=%q subject=%q reply=%q\\n", s.Name(), subject, reply) }\n')
        if line.strip()=='return':
            result.insert(len(result)-1,'\tif subject == "$JS.API.STREAM.CREATE.TEST2" { fmt.Printf("CREATE-TRACE return server=%q reply=%q branch='+str(index)+'\\n", s.Name(), reply) }\n')
    return ''.join(result)
change('jetstream_api.go','func (s *Server) jsStreamCreateRequest(',requests)
change('jetstream_cluster.go','func (s *Server) jsClusteredStreamRequest(',requests)
for name in ['sendAPIResponse','sendAPIHdrResponse','sendAPIErrResponse']:
    def response(text):
        a=text.index('\n')+1
        return text[:a]+'\tif subject == "$JS.API.STREAM.CREATE.TEST2" { fmt.Printf("CREATE-TRACE response server=%q reply=%q body=%s\\n", s.Name(), reply, response) }\n'+text[a:]
    change('jetstream_api.go','func (s *Server) '+name+'(',response)
def assignment(text):
    marker='\t// Remove this stream from the inflight proposals'
    assert text.count(marker)==1
    return text.replace(marker,'\tif stream == "TEST2" { fmt.Printf("CREATE-TRACE assignment server=%q reply=%q member=%v responded=%v recovering=%v peers=%v\\n", s.Name(), sa.Reply, isMember, sa.hasResponded(), sa.recovering, sa.Group.Peers) }\n'+marker)
change('jetstream_cluster.go','func (js *jetStream) processStreamAssignment(',assignment)
def leader(text):
    marker='\tstreamName := mset.name()\n';assert text.count(marker)==1
    return text.replace(marker,marker+'\tif streamName == "TEST2" { fmt.Printf("CREATE-TRACE leader server=%q reply=%q leader=%v responded=%v term=%d err=%v\\n", s.Name(), reply, isLeader, hasResponded, term, err) }\n')
change('jetstream_cluster.go','func (js *jetStream) processStreamLeaderChange(',leader)
def test(text):
    marker='\t_, err = js.AddStream(&nats.StreamConfig{Name: "TEST2"})'
    assert text.count(marker)==1
    return text.replace(marker,'\tt.Logf("CREATE-TRACE request ingress=%q", nc.ConnectedServerId())\n'+marker+'\n\tt.Logf("CREATE-TRACE completed err=%v", err)')
change('jetstream_cluster_2_test.go','func TestJetStreamClusterDeleteAndRestoreAndRestart(',test)
for name,text in texts.items():
    path=out/name;path.write_text(text);subprocess.run(['gofmt','-w',str(path)],check=True)
cases=[]
for target in ['fedora','leap','el10']:
    cases.append({'name':target+'-nats-stream-create-trace-242','target':target,'count':30,'race':True,
                  'pattern':'^TestJetStreamClusterDeleteAndRestoreAndRestart$',
                  'sublist':str(source/'server/sublist.go'),
                  'overlays':{str(out/name):'server/'+name for name in texts}})
Path('work/nats-stream-create-trace-242.json').write_text(json.dumps({'source':str(source),'workers':3,'cases':cases},indent=2)+'\n')
print('Prepared diagnostic-only overlays for the verified failing stream-create operation; no production patch proposed')
