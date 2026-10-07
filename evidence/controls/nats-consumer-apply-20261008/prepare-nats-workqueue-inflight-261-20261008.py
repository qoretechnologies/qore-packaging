# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json
import subprocess

root = Path.cwd()
prior = root / 'work/nats-workqueue-inflight-260-20261008'
out = root / 'work/nats-workqueue-inflight-261-20261008'
out.mkdir()
for name in ['jetstream_api.go', 'jetstream_cluster.go', 'jetstream_cluster_2_test.go']:
 s = (prior / name).read_text()
 if name == 'jetstream_api.go':
  s = s.replace('applied, quit := inflight.applied, cc.qch', 'applied, quit, meta := inflight.applied, cc.qch, cc.meta')
  s = s.replace('s := js.srv\n\trmsg = copyBytes(rmsg)', 's := js.srv\n\tmetaQuit := meta.QuitC()\n\trmsg = copyBytes(rmsg)')
  s = s.replace('''			if replay {
				js.apiDispatch''', '''			if replay {
				select {
				case <-quit:
					return
				case <-metaQuit:
					return
				case <-s.quitCh:
					return
				default:
				}
				js.apiDispatch''')
  s = s.replace('''			replay = true
		case <-quit:
		case <-s.quitCh:''', '''			replay = true
		case <-quit:
		case <-metaQuit:
		case <-s.quitCh:''')
 if name == 'jetstream_cluster_2_test.go':
  a = s.index('func TestJetStreamConsumerInfoPendingDeleteLifecycle(')
  body = s[a:]
  body = body.replace('[]string{"applied", "term_reset", "shutdown", "start_rejected"}', '[]string{"live_consumer", "applied", "term_reset", "shutdown", "start_rejected"}')
  body = body.replace('client := &client{', 'requestClient := &client{').replace('client.pa.', 'requestClient.pa.').replace('(nil, client,', '(nil, requestClient,')
  body = body.replace('if completion == "applied" {', 'if completion == "live_consumer" {',1)
  body = body.replace('''			mjs.mu.Lock()
			require_Equal(t, cc.pendingConsumerInfos, int64(2))
			inflight :=''', '''			mjs.mu.Lock()
			pendingBefore := cc.pendingConsumerInfos
			inflight :=''')
  body = body.replace('''			mjs.mu.Unlock()
			select {
			case <-applied:''', '''			mjs.mu.Unlock()
			require_Equal(t, pendingBefore, int64(2))
			select {
			case <-applied:''')
  body = body.replace('''			if completion == "term_reset" {
				mjs.mu.Lock()
				cc.clearInflightConsumerProposals()
				mjs.mu.Unlock()''', '''			if completion == "term_reset" || completion == "applied" {
				mjs.mu.Lock()
				if completion == "applied" {
					cc.removeInflightConsumerProposal(globalAccountName, "TEST", "C")
				} else {
					cc.clearInflightConsumerProposals()
				}
				mjs.mu.Unlock()''')
  s = s[:a] + body
 (out / name).write_text(s)
 subprocess.run(['gofmt', '-w', str(out / name)], check=True)
base = json.loads((root / 'work/nats-workqueue-inflight-260.json').read_text())
for c in base['cases']:
 c['name'] = c['name'].replace('260','261')
 c['overlays'] = {str(p.relative_to(root)): 'server/' + p.name for p in out.glob('*.go')}
(root / 'work/nats-workqueue-inflight-261.json').write_text(json.dumps(base,indent=2)+'\n')
print('Prepared refined lifetime checks and metadata-node shutdown cancellation')
