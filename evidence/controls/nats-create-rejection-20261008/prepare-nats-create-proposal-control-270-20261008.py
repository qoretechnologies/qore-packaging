# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
root=Path.cwd();source=root/'work/nats-prepared-50/nats-server-2.15.0';trace=root/'work/nats-memory-create-trace-268-20261008';out=root/'work/nats-create-proposal-control-270-20261008';out.mkdir()
s=(source/'server/jetstream_cluster_2_test.go').read_text()
s+=r'''
// Copyright 2026 Qore Technologies, s.r.o.; Apache-2.0.
// Diagnostic-only control: a real request and actual metadata leader transfer.
type rpmCreateProposalGate struct {
 rpmCreationLogger
 entered chan struct{}
 resume chan struct{}
 once sync.Once
}
func (l *rpmCreateProposalGate) Debugf(format string, values ...any) {
 l.rpmCreationLogger.Debugf(format, values...)
 if strings.HasPrefix(format,"RPM_CREATE stage=propose stream=") {
  l.once.Do(func() {close(l.entered); <-l.resume})
 }
}
func TestRPMStreamCreateProposalLeadershipWindow(t *testing.T) {
 for _, transfer := range []bool{false,true} {
  t.Run(fmt.Sprintf("transfer=%v",transfer),func(t *testing.T) {
   c:=createJetStreamClusterExplicit(t,"CREATE-WINDOW",3)
   defer c.shutdown()
   meta:=c.leader();require_NotNil(t,meta)
   node:=meta.getJetStream().getMetaGroup()
   log:=&rpmCreateProposalGate{entered:make(chan struct{}),resume:make(chan struct{})}
   meta.SetLogger(log,true,false)
   var release sync.Once
   resume:=func(){release.Do(func(){close(log.resume)})}
   defer resume()
   subject:=fmt.Sprintf(JSApiStreamCreateT,"TEST")
   finished:=make(chan *Server,3)
   for _, server:=range c.servers {
    api:=server.getJetStream().apiSubs
    matches:=api.Match(subject).psubs;require_Equal(t,len(matches),1)
    original:=matches[0]
    replacement:=&subscription{subject:append([]byte(nil),original.subject...),icb:func(sub *subscription,client *client,acc *Account,subject,reply string,msg []byte) {
     original.icb(sub,client,acc,subject,reply,msg)
     finished<-server
    }}
    require_NoError(t,api.Remove(original));require_NoError(t,api.Insert(replacement))
    defer func(){require_NoError(t,api.Remove(replacement));require_NoError(t,api.Insert(original))}()
   }
   nc,js:=jsClientConnect(t,meta);defer nc.Close()
   ctx,cancel:=context.WithTimeout(context.Background(),30*time.Second)
   defer cancel()
   result:=make(chan error,1)
   var workers sync.WaitGroup;workers.Add(1)
   // Release the gate before joining even on an assertion failure.
   defer func(){resume();cancel();workers.Wait()}()
   go func(){defer workers.Done();_,err:=js.AddStream(&nats.StreamConfig{Name:"TEST",Storage:nats.MemoryStorage,Subjects:[]string{"foo"},Replicas:3},nats.Context(ctx));result<-err}()
   select {case <-log.entered:case <-ctx.Done():t.Fatal("request did not enter proposal gate")}
   // Both nonleaders already handled and discarded this exact request. No
   // later leader can independently answer its original fanout copy.
   for range 2 {
    select {case server:=<-finished:require_True(t,server!=meta);case <-ctx.Done():t.Fatal("nonleader handlers did not complete")}
   }
   if transfer {require_NoError(t,node.StepDown());require_True(t,!node.Leader())}
   resume()
   err:=<-result
   log.mu.Lock();lines:=append([]string(nil),log.lines...);log.mu.Unlock()
   rejected:=false
   for _,line:=range lines {
    if strings.Contains(line,"RPM_CREATE") {t.Log(line)}
    if strings.Contains(line,"stage=propose-error") && strings.Contains(line,"not leader") {rejected=true}
   }
   if transfer {
    require_True(t,rejected)
    require_Error(t,err,context.DeadlineExceeded)
    for _,server:=range c.servers {_,lookupErr:=server.GlobalAccount().lookupStream("TEST");require_Error(t,lookupErr,NewJSStreamNotFoundError())}
    t.Log("real rejected proposal generated no API reply and no stream; original 30-second request deadline expired")
   } else {require_NoError(t,err);require_True(t,!rejected)}
  })
 }
}
'''
(out/'jetstream_cluster_2_test.go').write_text(s)
subprocess.run(['gofmt','-w',str(out/'jetstream_cluster_2_test.go')],check=True)
cases=[]
for target in ('fedora','leap','el10'):
 overlays={str((trace/x).relative_to(root)):'server/'+x for x in ('jetstream_api.go','jetstream_cluster.go')};overlays[str((out/'jetstream_cluster_2_test.go').relative_to(root))]='server/jetstream_cluster_2_test.go'
 cases.append({'name':target+'-nats-create-proposal-control-270','target':target,'count':1,'race':True,'pattern':'^TestRPMStreamCreateProposalLeadershipWindow$','sublist':str(source.relative_to(root)/'server/sublist.go'),'overlays':overlays})
(root/'work/nats-create-proposal-control-270.json').write_text(json.dumps({'source':str(source.relative_to(root)),'workers':3,'cases':cases},indent=2)+'\n')
print('Prepared real request/leadership-transfer diagnostic control; no package patch changed.')
