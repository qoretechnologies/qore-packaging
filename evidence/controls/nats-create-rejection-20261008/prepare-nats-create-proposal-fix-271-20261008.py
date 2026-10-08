# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
root=Path.cwd();source=root/'work/nats-prepared-50/nats-server-2.15.0';out=root/'work/nats-create-proposal-fix-271-20261008';out.mkdir()
s=(source/'server/jetstream_cluster.go').read_text();sig='func (s *Server) jsClusteredStreamRequest('
a,b=s.split(sig,1);b,c=b.split('\nvar (',1)
old='\tif err := cc.meta.Propose(cc.term, encodeAddStreamAssignment(sa)); err != nil {\n\t\treturn\n\t}\n';assert b.count(old)==1
b=b.replace(old,'\tif err := cc.meta.Propose(cc.term, encodeAddStreamAssignment(sa)); err != nil {\n\t\t// The metadata term can change after this request passed the leader\n\t\t// check. A rejected proposal has no assignment to answer it later.\n\t\tresp.Error = NewJSClusterNotAvailError()\n\t\ts.sendAPIErrResponse(ci, acc, subject, reply, string(rmsg), s.jsonResponse(&resp))\n\t\treturn\n\t}\n')
(out/'jetstream_cluster.go').write_text(a+sig+b+'\nvar ('+c)
s=(source/'server/jetstream_cluster_2_test.go').read_text()
s+=r'''
// Copyright 2026 Qore Technologies, s.r.o.; Apache-2.0.
// Keep the actual Raft implementation and alter only when the first stream
// proposal enters it, so a real API request can overlap a real leader transfer.
type streamCreateProposalGate struct {
 RaftNode
 entered chan struct{}
 resume chan struct{}
 proposed chan error
 once sync.Once
}
func (n *streamCreateProposalGate) Propose(term uint64,data []byte) error {
 observe:=false
 if len(data)>0 && entryOp(data[0])==assignStreamOp {
  n.once.Do(func(){observe=true;close(n.entered);<-n.resume})
 }
 err:=n.RaftNode.Propose(term,data)
 if observe {n.proposed<-err}
 return err
}
func TestJetStreamStreamCreateRejectedProposalResponse(t *testing.T) {
 for _,transfer:=range []bool{false,true} {
  t.Run(fmt.Sprintf("transfer=%v",transfer),func(t *testing.T) {
   c:=createJetStreamClusterExplicit(t,"CREATE-REJECT",3)
   defer c.shutdown()
   meta:=c.leader();require_NotNil(t,meta)
   mjs:=meta.getJetStream();node:=mjs.getMetaGroup()
   gate:=&streamCreateProposalGate{RaftNode:node,entered:make(chan struct{}),resume:make(chan struct{}),proposed:make(chan error,1)}
   mjs.mu.Lock();mjs.cluster.meta=gate;mjs.mu.Unlock()
   var restoreOnce sync.Once
   restore:=func(){restoreOnce.Do(func(){mjs.mu.Lock();mjs.cluster.meta=node;mjs.mu.Unlock()})}
   defer restore()
   var release sync.Once
   resume:=func(){release.Do(func(){close(gate.resume)})}
   defer resume()
   subject:=fmt.Sprintf(JSApiStreamCreateT,"TEST")
   finished:=make(chan *Server,3)
   var observing atomic.Bool;observing.Store(true)
   for _,server:=range c.servers {
    api:=server.getJetStream().apiSubs
    matches:=api.Match(subject).psubs;require_Equal(t,len(matches),1)
    original:=matches[0]
    replacement:=&subscription{subject:append([]byte(nil),original.subject...),icb:func(sub *subscription,client *client,acc *Account,subject,reply string,msg []byte) {
     original.icb(sub,client,acc,subject,reply,msg)
     if observing.Load() {finished<-server}
    }}
    require_NoError(t,api.Remove(original));require_NoError(t,api.Insert(replacement))
    defer func(){require_NoError(t,api.Remove(replacement));require_NoError(t,api.Insert(original))}()
   }
   nc,js:=jsClientConnect(t,meta);defer nc.Close()
   ctx,cancel:=context.WithTimeout(context.Background(),30*time.Second)
   defer cancel()
   type result struct {info *nats.StreamInfo;err error}
   completed:=make(chan result,1)
   var workers sync.WaitGroup;workers.Add(1)
   defer func(){resume();cancel();workers.Wait()}()
   cfg:=&nats.StreamConfig{Name:"TEST",Storage:nats.MemoryStorage,Subjects:[]string{"foo"},Replicas:3}
   go func(){defer workers.Done();info,err:=js.AddStream(cfg,nats.Context(ctx));completed<-result{info,err}}()
   select {case <-gate.entered:case <-ctx.Done():t.Fatal("request did not reach proposal")}
   // Join the actual nonleader handlers before transferring authority. Their
   // fanout copies must not answer this request after the new leader is ready.
   for range 2 {
    select {case server:=<-finished:require_True(t,server!=meta);case <-ctx.Done():t.Fatal("nonleader handlers did not complete")}
   }
   if transfer {require_NoError(t,node.StepDown());require_True(t,!node.Leader())}
   resume()
   proposalErr:=<-gate.proposed
   first:=<-completed
   observing.Store(false)
   restore()
   if transfer {
    require_Error(t,proposalErr,errNotLeader)
    var apiErr *nats.APIError
    require_True(t,errors.As(first.err,&apiErr))
    require_Equal(t,apiErr.Code,503)
    require_Equal(t,int(apiErr.ErrorCode),int(JSClusterNotAvailErr))
    require_True(t,first.info==nil)
    for _,server:=range c.servers {
     js:=server.getJetStream();js.mu.RLock()
     assignment:=js.streamAssignmentOrInflight(globalAccountName,"TEST")
     js.mu.RUnlock();require_True(t,assignment==nil)
     _,err:=server.GlobalAccount().lookupStream("TEST");require_Error(t,err,NewJSStreamNotFoundError())
    }
    // A fresh user request after actual API readiness must succeed, proving
    // rejection leaves no inflight assignment, reservation or stream behind.
    ready,stop:=context.WithTimeout(context.Background(),10*time.Second)
    defer stop();require_NoError(t,awaitMetadataAPILeader(ready,c))
    recovered,err:=js.AddStream(cfg);require_NoError(t,err)
    require_Equal(t,recovered.Config.Name,"TEST")
    require_Equal(t,recovered.Config.Replicas,3)
   } else {
    require_NoError(t,proposalErr);require_NoError(t,first.err)
    require_NotNil(t,first.info);require_Equal(t,first.info.Config.Name,"TEST")
   }
  })
 }
}
'''
(out/'jetstream_cluster_2_test.go').write_text(s)
subprocess.run(['gofmt','-w',str(out/'jetstream_cluster.go'),str(out/'jetstream_cluster_2_test.go')],check=True)
cases=[]
for variant in ('original','fixed'):
 for target in ('fedora','leap','el10'):
  overlays={str((out/'jetstream_cluster_2_test.go').relative_to(root)):'server/jetstream_cluster_2_test.go'}
  if variant=='fixed':overlays[str((out/'jetstream_cluster.go').relative_to(root))]='server/jetstream_cluster.go'
  cases.append({'name':target+'-nats-create-proposal-271-'+variant,'target':target,'count':1 if variant=='original' else 5,'race':True,'pattern':'^TestJetStreamStreamCreateRejectedProposalResponse$','sublist':str(source.relative_to(root)/'server/sublist.go'),'overlays':overlays})
(root/'work/nats-create-proposal-271.json').write_text(json.dumps({'source':str(source.relative_to(root)),'workers':3,'cases':cases},indent=2)+'\n')
print('Prepared minimal explicit rejection response and real-Raft regression controls.')
