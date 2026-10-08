# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json, subprocess
root=Path.cwd(); source=root/'work/nats-prepared-50/nats-server-2.15.0'; out=root/'work/nats-memory-create-trace-268-20261008';out.mkdir(exist_ok=True)
def change(text, old, new):
 assert text.count(old)==1,(old,text.count(old))
 return text.replace(old,new)
a=(source/'server/jetstream_api.go').read_text()
for fn in ('sendAPIResponse','sendAPIErrResponse'):
 sig=f'func (s *Server) {fn}(ci *ClientInfo, acc *Account, subject, reply, request, response string) {{\n'
 a=change(a,sig,sig+'\tif strings.HasPrefix(subject, "$JS.API.STREAM.CREATE.") {\n\t\ts.Debugf("RPM_CREATE stage='+fn+' subject=%q reply=%q response=%s", subject, reply, response)\n\t}\n')
sig='func (s *Server) jsStreamCreateRequest(sub *subscription, c *client, _ *Account, subject, reply string, rmsg []byte) {\n'
a=change(a,sig,sig+'\ts.Debugf("RPM_CREATE stage=handler subject=%q reply=%q apiLeader=%v", subject, reply, s.JetStreamIsLeader())\n\tdefer s.Debugf("RPM_CREATE stage=handler-return subject=%q reply=%q", subject, reply)\n')
(out/'jetstream_api.go').write_text(a)
a=(source/'server/jetstream_cluster.go').read_text()
before, fnbody = a.split('func (js *jetStream) processStreamAssignment(sa *streamAssignment) {', 1)
fnbody, after = fnbody.split('\nfunc ', 1)
fnbody=change(fnbody,'\t// Remove this stream from the inflight proposals\n\tcc.removeInflightStreamProposal(accName, sa.Config.Name)\n','\ts.Debugf("RPM_CREATE stage=apply stream=%q reply=%q member=%v responded=%v recovering=%v", stream, sa.Reply, isMember, sa.hasResponded(), sa.recovering)\n\t// Remove this stream from the inflight proposals\n\tcc.removeInflightStreamProposal(accName, sa.Config.Name)\n')
a=before+'func (js *jetStream) processStreamAssignment(sa *streamAssignment) {'+fnbody+'\nfunc '+after
sig='\tclient, subject, reply := sa.Client, sa.Subject, sa.Reply\n\thasResponded := sa.markResponded()\n'
a=change(a,sig,sig+'\ts.Debugf("RPM_CREATE stage=leader-change stream=%q reply=%q isLeader=%v term=%d previousResponded=%v", sa.Config.Name, reply, isLeader, term, hasResponded)\n')
a=change(a,'\t// Tell stream to switch leader status.\n\tmset.setLeader(isLeader, term)\n','\t// Tell stream to switch leader status.\n\tmset.setLeader(isLeader, term)\n\ts.Debugf("RPM_CREATE stage=set-leader-return stream=%q reply=%q isLeader=%v", streamName, reply, isLeader)\n')
before, fnbody = a.split('func (s *Server) jsClusteredStreamRequest(ci *ClientInfo, acc *Account, subject, reply string, rmsg []byte, config *StreamConfigRequest) {', 1)
fnbody, after = fnbody.split('\nvar (', 1)
fnbody=change(fnbody,'\tif err := cc.meta.Propose(cc.term, encodeAddStreamAssignment(sa)); err != nil {\n\t\treturn\n\t}\n', '\ts.Debugf("RPM_CREATE stage=propose stream=%q reply=%q term=%d group=%q preferred=%q", cfg.Name, reply, cc.term, rg.Name, rg.Preferred)\n\tif err := cc.meta.Propose(cc.term, encodeAddStreamAssignment(sa)); err != nil {\n\t\ts.Debugf("RPM_CREATE stage=propose-error stream=%q reply=%q error=%v", cfg.Name, reply, err)\n\t\treturn\n\t}\n\ts.Debugf("RPM_CREATE stage=propose-return stream=%q reply=%q", cfg.Name, reply)\n')
a=before+'func (s *Server) jsClusteredStreamRequest(ci *ClientInfo, acc *Account, subject, reply string, rmsg []byte, config *StreamConfigRequest) {'+fnbody+'\nvar ('+after
(out/'jetstream_cluster.go').write_text(a)
a=(source/'server/norace_2_test.go').read_text(); start=a.index('func TestNoRaceJetStreamClusterMemoryStreamLastSequenceResetAfterRestart('); end=a.index('\nfunc ',start+1)
orig=a[start:end]
setup='''
	logs := make([]*rpmCreationLogger, len(c.servers))
	for i, srv := range c.servers {
		logs[i] = &rpmCreationLogger{}
		srv.SetLogger(logs[i], true, false)
	}
	defer func() {
		for i, log := range logs {
			log.mu.Lock()
			lines := append([]string(nil), log.lines...)
			dropped := log.dropped
			log.mu.Unlock()
			t.Logf("server %s meta_leader=%v events=%d dropped=%d", c.servers[i].Name(), c.servers[i].JetStreamIsLeader(), len(lines), dropped)
			if t.Failed() {
				for _, line := range lines { t.Log(line) }
			}
		}
	}()
'''
control=orig.replace('TestNoRaceJetStreamClusterMemoryStreamLastSequenceResetAfterRestart','TestNoRaceRPMConcurrentMemoryCreationTrace',1)
control=change(control,'\tdefer c.shutdown()\n','\tdefer c.shutdown()\n'+setup)
control=change(control,'\t\t\tresults <- err\n','\t\t\tif err != nil { err = fmt.Errorf("stream TEST:%d create: %w", n, err) }\n\t\t\tresults <- err\n')
control=change(control,'\t\trequire_NoError(t, <-results)\n\t}\n\tfor i := 1; i <= numStreams; i++ {','\t\tif err := <-results; err != nil { t.Error(err) }\n\t}\n\tif t.Failed() { t.FailNow() }\n\tfor i := 1; i <= numStreams; i++ {')
# This diagnostic control isolates the failing setup; it does not qualify restarts.
control=control[:control.index('\tfor i := 1; i <= numStreams; i++ {\n\t\tawaitStreamRouteInterest')]+ '\tt.Log("all 250 concurrent creates completed")\n}\n'
a+='\n// Copyright 2026 Qore Technologies, s.r.o.; Apache-2.0.\n'+control
(out/'norace_2_test.go').write_text(a)
subprocess.run(['gofmt','-w',*[str(out/x) for x in ('jetstream_api.go','jetstream_cluster.go','norace_2_test.go')]],check=True)
cases=[]
for target in ('fedora','leap','el10'):
 cases.append({'name':target+'-nats-memory-create-trace-268','target':target,'count':5,'race':False,'pattern':'^TestNoRaceRPMConcurrentMemoryCreationTrace$','sublist':str(source.relative_to(root)/'server/sublist.go'),'overlays':{str((out/x).relative_to(root)):'server/'+x for x in ('jetstream_api.go','jetstream_cluster.go','norace_2_test.go')}})
(root/'work/nats-memory-create-trace-268.json').write_text(json.dumps({'source':str(source.relative_to(root)),'workers':3,'cases':cases},indent=2)+'\n')
print('Prepared trace-only overlays; 250 concurrency and 30-second API deadline retained.')
