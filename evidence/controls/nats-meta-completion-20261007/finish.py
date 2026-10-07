# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import difflib,json,subprocess
old=Path('work/nats-meta-completion-230-final');out=Path('work/nats-meta-completion-230-final2');out.mkdir();s=(old/'jetstream_cluster_4_test.go').read_text()
s+='''
func TestConsumerCreateReplyPrecedesRemoteMetadataApply(t *testing.T) {
    c:=createJetStreamClusterExplicit(t,"META-CREATE",3)
    defer c.shutdown()
    nc,js:=jsClientConnect(t,c.leader())
    defer nc.Close()
    // R1 pins the consumer to the stream's sole member, keeping the paused
    // metadata peer out of its placement without injecting an assignment.
    _,err:=js.AddStream(&nats.StreamConfig{Name:"TEST",Subjects:[]string{"foo"},Replicas:1})
    require_NoError(t,err)
    awaitClusterMetaApplied(t,c)
    metaLeader,streamLeader:=c.leader(),c.streamLeader(globalAccountName,"TEST")
    var target *Server
    for _,server:=range c.servers {
        if server!=metaLeader && server!=streamLeader {target=server;break}
    }
    require_NotNil(t,target)
    jsTarget:=target.getJetStream()
    meta:=jsTarget.getMetaGroup().(*raft)
    require_NoError(t,meta.PauseApply())
    defer meta.ResumeApply()
    _,err=js.AddConsumer("TEST",&nats.ConsumerConfig{Durable:"C",Replicas:1,AckPolicy:nats.AckExplicitPolicy})
    require_NoError(t,err)
    jsTarget.mu.RLock()
    before:=jsTarget.consumerAssignment(globalAccountName,"TEST","C")
    jsTarget.mu.RUnlock()
    require_True(t,before==nil)
    meta.ResumeApply()
    awaitClusterMetaApplied(t,c)
    jsTarget.mu.RLock()
    after:=jsTarget.consumerAssignment(globalAccountName,"TEST","C")
    jsTarget.mu.RUnlock()
    require_NotNil(t,after)
}
'''
p=out/'jetstream_cluster_4_test.go';p.write_text(s);subprocess.run(['gofmt','-w',str(p)],check=True);s=p.read_text()
original=Path('work/nats-prepared-43/nats-server-2.15.0/server/jetstream_cluster_4_test.go').read_text();(out/'nats-server-meta-completion-tests.patch').write_text('# Copyright 2026 Qore Technologies, s.r.o.; Apache-2.0.\n# Join committed metadata application before reading a remote consumer assignment or retention state.\n'+''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='a/server/jetstream_cluster_4_test.go',tofile='b/server/jetstream_cluster_4_test.go')))
a=s.index('func TestConsumerFilterReplyPrecedesRemoteMetadataApply(');b=s.index('\nfunc ',a+5);body=s[a:b];needle='// The successful update response has arrived, but this real follower remains unchanged.\n\trequire_Equal(t, info.State.Msgs, uint64(10))';assert body.count(needle)==1
negative=s[:a]+body.replace(needle,needle.replace('uint64(10)','uint64(1)'))+s[b:];negative=negative.replace('require_True(t, before == nil)','require_NotNil(t, before)');(out/'negative_jetstream_cluster_4_test.go').write_text(negative)
for variant,count in [('fixed',30),('negative',1)]:
 d=json.loads(Path('work/nats-meta-completion-230-fixed.json').read_text())
 for case in d['cases']:
  case['name']=case['name'].replace('-230-fixed','-230-final2-'+variant);case['count']=count
  names=['TestConsumerFilterReplyPrecedesRemoteMetadataApply','TestConsumerCreateReplyPrecedesRemoteMetadataApply']
  if variant=='fixed':names+=['TestClusteredInterestConsumerFilterEdit','TestJetStreamClusterConsumerRemovalMatchesRenamedGroup']
  case['pattern']='^('+'|'.join(names)+')$';case['overlays']={str(out/('jetstream_cluster_4_test.go' if variant=='fixed' else 'negative_jetstream_cluster_4_test.go')):'server/jetstream_cluster_4_test.go'}
 Path(f'work/nats-meta-completion-230-final2-{variant}.json').write_text(json.dumps(d,indent=2)+'\n')
