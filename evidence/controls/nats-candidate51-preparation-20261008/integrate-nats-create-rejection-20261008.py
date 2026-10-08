# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,json,shutil
root=Path.cwd();e=json.loads((root/'evidence/nats-create-rejection-20261008.json').read_text());assert e['qualification']['race_enabled_results_including_subtests']==138 and e['qualification']['nonrace_full_memory_restart_results']==3
for p,h in e['files_sha256'].items():assert hashlib.sha256((root/p).read_bytes()).hexdigest()==h,p
name='nats-server-stream-create-rejection.patch';shutil.copy2(root/'evidence/controls/nats-create-rejection-20261008'/name,root/'dependencies'/name)
p=root/'dependencies/nats-server.spec';s=p.read_text();needle='Patch112: nats-server-mqtt-restart-storage-tests.patch\n';assert s.count(needle)==1;s=s.replace(needle,needle+'Patch113: '+name+'\n')
needle='%changelog\n* Thu Oct 08 2026 David Nichols <david@qore.org> - 2.15.0-1.qore\n';assert s.count(needle)==1;s=s.replace(needle,needle+'- Reply with the existing availability error when stream creation loses metadata authority before proposal.\n- Cover real leader transfer, absent rejected state and successful fresh creation.\n');p.write_text(s)
p=root/'dependencies/sources.json';s=json.loads(p.read_text());s['nats-server']['extra_sources'].append(name);p.write_text(json.dumps(s,indent=2)+'\n')
p=root/'dependencies/nats-server.rst';s=p.read_text();head=s[:s.index('Candidate 50')];rest=s[s.index('Metadata API readiness after restart'):]
head+='''Candidate 51 combines upstream 2.15.0 with 114 patches. The full combined RPM
matrix, native OBS builds and installed-package qualification remain required.
Candidate 46 finished with 10,144 passing results, 72 upstream skips and one
failure on each distribution. Qualified fixes cover the Fedora pull-interest
and AlmaLinux MQTT failures. Leap's initial 250-stream creation timeout remains
open, together with the historical atomic-create and sparse-performance gates.
See ``evidence/nats-candidate46-final-20261008.json``.

The upstream release supplies the migration implementation qualified by 20
race-enabled reverse-migration runs per distribution. Its go.mod/go.sum are
byte-identical to the prior verified vendored input. Sources and all vendored
licenses are pinned by the dependency manifest.

The patch stack includes qualified consumer-information lifetime/startup fixes,
route-capacity and accounting corrections, storage and shutdown fixes, and
fixture changes that join the required protocol or storage event. Original
workloads and performance thresholds remain in force. The sections below
explain the latest changes and link their focused qualification evidence.

Distributed assignment response ownership retains upstream behavior. Earlier
proposals that changed its ``responded`` flag were withdrawn after they repeated
creation advisories and sourcing resets. Their synthetic controls did not
establish a real pending-request defect; see
``evidence/nats-reply-withdrawal-20261007.json``. The rejected-proposal correction
below leaves that ownership unchanged.

'''
rest=rest.replace('The clean original fixture passes 30 race-enabled runs','The corrected fixture passes 30 race-enabled runs')
rest+='''
Stream creation rejected during a metadata leader transfer
----------------------------------------------------------

The metadata term can change after a stream-create request passes its API
leadership check. If Raft rejects the proposal, there is no assignment that can
reply later. The handler now returns the existing cluster-unavailable error
(code 503, JetStream error 10008), allowing the caller to handle the failure
immediately. It records no inflight assignment for a rejected proposal.

A real request/leader-transfer control reproduces the old 30-second timeout on
all three distributions. The permanent regression gates entry to the real Raft
implementation, checks the exact error and absence of rejected state, and
verifies a fresh request after API leadership recovers. All 138 race-enabled
results from the focused controls and 17 broader suites pass, as do the three
full 250-stream publication, snapshot and rolling-restart tests.

This does not establish the exact interleaving of the earlier untraced creation
timeouts or guarantee transparent completion through failover. Those release
gates remain open. See ``evidence/nats-create-rejection-20261008.json`` for the
source, audit, negative controls and qualification limits.
'''
p.write_text(head+rest)
print('Integrated Patch113 and current dependency documentation; 114 patches total.')
