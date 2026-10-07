# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import difflib
import json
import subprocess

root = Path.cwd()
source = root / 'work/nats-prepared-46/nats-server-2.15.0/server'
previous = root / 'work/nats-failtracking-meta-250-20261008'
out = root / 'work/nats-failtracking-meta-251-20261008'
out.mkdir()
for name in ['jetstream_cluster.go', 'jetstream_api.go']:
    (out / name).write_bytes((previous / name).read_bytes())
test = (previous / 'jetstream_cluster_3_test.go').read_text()
a = test.index('func TestPackagingFailTrackingMetadataReadiness(')
b = test.index('// Diagnostic-only event join', a)
body = test[a:b]
body = body.replace('func TestPackagingFailTrackingMetadataReadiness(t *testing.T) {', '''func TestPackagingFailTrackingMetadataReadiness(t *testing.T) {
	for _, waitForMetadata := range []bool{false, true} {
		t.Run(fmt.Sprintf("wait=%v", waitForMetadata), func(t *testing.T) {''', 1)
needle = '\trequestContext, cancelRequest := context.WithTimeout(context.Background(), 10*time.Second)\n'
assert body.count(needle) == 1
body = body.replace(needle, needle + '\tobserved := &packagingMetadataWaitContext{Context: requestContext, awaiting: make(chan struct{})}\n')
needle = '\t\tdefer workers.Done()\n'
assert body.count(needle) == 1
body = body.replace(needle, needle + '''		if waitForMetadata {
			if err := awaitMetadataAPILeader(observed, c); err != nil {
				result <- err
				return
			}
		}
''')
a1 = body.index('\tseen := make(map[*Server]bool)')
b1 = body.index('\trelease.Do(func() { close(gate.resume) })', a1)
old = body[a1:b1]
body = body[:a1] + '''	if waitForMetadata {
		select {
		case <-observed.awaiting:
			// Subscriptions are registered and the first readiness check is false.
		case <-requestContext.Done():
			t.Fatal("readiness helper did not enter the event wait")
		}
	} else {
''' + old + '\t}\n' + body[b1:]
a1 = body.index('\trequire_Error(t, <-result, context.DeadlineExceeded)')
b1 = body.index('\t// Verify the original ordered', a1)
old = body[a1:b1]
body = body[:a1] + '''	if waitForMetadata {
		require_NoError(t, <-result)
		select {
		case server := <-gate.requests:
			t.Fatalf("barrier allowed update before metadata readiness on %s", server.Name())
		default:
		}
	} else {
''' + old + '\t}\n' + body[b1:]
body = body.replace('t.Logf("original update timed out before metadata readiness; ready update preserved %d ordered messages", b*bsz)',
    't.Logf("wait=%v: preserved %d ordered messages after metadata-readiness control", waitForMetadata, b*bsz)')
assert body.endswith('}\n\n')
body = body[:-3] + '\t\t})\n\t}\n}\n\n'
body += '''// Witness entry into the helper's event wait without changing that helper.
type packagingMetadataWaitContext struct {
	context.Context
	once sync.Once
	awaiting chan struct{}
}

func (ctx *packagingMetadataWaitContext) Done() <-chan struct{} {
	ctx.once.Do(func() { close(ctx.awaiting) })
	return ctx.Context.Done()
}

'''
test = test[:a] + body + test[b:]
(out / 'jetstream_cluster_3_test.go').write_text(test)
subprocess.run(['gofmt', '-w', str(out / 'jetstream_cluster_3_test.go')], check=True)
config = json.loads((root / 'work/nats-failtracking-meta-250.json').read_text())
for case in config['cases']:
    case['name'] = case['name'].replace('-250', '-251')
    case['overlays'] = {str(p.relative_to(root)): 'server/' + p.name for p in out.iterdir()}
(root / 'work/nats-failtracking-meta-251.json').write_text(json.dumps(config, indent=2) + '\n')

# Clean package proposal: a readiness precondition immediately before UpdateStream.
clean = root / 'work/nats-failtracking-clean-252-20261008'
clean.mkdir()
original = (source / 'jetstream_cluster_3_test.go').read_text()
a = original.index('func TestJetStreamClusterStreamFailTracking(')
b = original.index('\nfunc ', a + 1)
body = original[a:b]
needle = '\t_, err = js.UpdateStream(&nats.StreamConfig{'
assert body.count(needle) == 1
body = body.replace(needle, '''	// Stream leadership and publication can recover before the metadata API.
	ready, cancelReady := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancelReady()
	require_NoError(t, awaitMetadataAPILeader(ready, c))

''' + needle)
qualified = original[:a] + body + original[b:]
assert '\n\t"context"\n' in qualified
(clean / 'jetstream_cluster_3_test.go').write_text(qualified)
subprocess.run(['gofmt', '-w', str(clean / 'jetstream_cluster_3_test.go')], check=True)
qualified = (clean / 'jetstream_cluster_3_test.go').read_text()
patch = '# Copyright 2026 Qore Technologies, s.r.o.; Apache-2.0.\n'
patch += '# Join metadata API readiness after the intentional restart before reducing stream replicas.\n'
patch += ''.join(difflib.unified_diff(original.splitlines(True), qualified.splitlines(True),
    fromfile='a/server/jetstream_cluster_3_test.go', tofile='b/server/jetstream_cluster_3_test.go'))
(clean / 'nats-server-failtracking-meta-ready-tests.patch').write_text(patch)
for case in config['cases']:
    case['name'] = case['name'].replace('meta-251', 'clean-252')
    case['pattern'] = '^TestJetStreamClusterStreamFailTracking$'
    case['count'] = 10
    case['overlays'] = {str((clean / 'jetstream_cluster_3_test.go').relative_to(root)): 'server/jetstream_cluster_3_test.go'}
(root / 'work/nats-failtracking-clean-252.json').write_text(json.dumps(config, indent=2) + '\n')
print('Prepared paired scheduler control and clean replica-update fixture correction')
