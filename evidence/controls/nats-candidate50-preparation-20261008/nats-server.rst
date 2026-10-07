NATS server dependency
======================

Copyright 2026 Qore Technologies, s.r.o.

Candidate 50 is being prepared from upstream 2.15.0 with 113 patches. It combines
the qualified metadata-apply consumer-information fix, metadata and pull-route
readiness corrections, and the MQTT pre-restart storage correction described
below. Candidate 46 is still collecting its full RPM matrix; combined full
builds follow review of all its results. Historical failure review, native OBS
builds and installed-package qualification remain release gates.
Upstream's released migration implementation passes 20 race-enabled
reverse-migration runs on each distribution, where the 2.14.7 control fails.
The two releases have byte-identical go.mod/go.sum; the verified vendored
input is reused without dependency changes.

A live peer-removal control reproduced a consumer-info race: the old leader
can lose its local stream after its leadership snapshot and falsely answer
"stream not found". The fixed path defers to current cluster authority instead.
The new regression fails against the original code; 252 race-enabled cases
pass across the three distributions, preserving valid standalone and cluster
not-found errors. Diagnostic rendezvous hooks are confined to controls and are
absent from the package patch.

Candidate 36 passed on AlmaLinux but exposed four failures on Fedora/Leap.
Three are addressed by paired controls and regression tests: pinned-account
fixtures now complete server-side client removal before policy reloads; the
unknown-delivery fixture joins its exact pull-request subscription event; and
reverse memory-store lookups skip purged ranges using conservative subject
bounds without recalculating them under a read lock. Original performance
thresholds and acknowledgement assertions remain unchanged. See
``evidence/nats-candidate37-focused-20261007.json`` for the focused results.

A second consumer-info race affects startup fallback responses: an assignment
can be removed or replaced while the handler examines its Raft group. The
fallback now validates the captured assignment against current metadata and
serializes its response under the cluster read lock. A forced deletion
interleaving fails against the original code on all three distributions.
The permanent regression covers live, missing, replaced and deleted assignments;
the workqueue fixture checks every delete, fresh creation timestamps and actual
unacknowledged delivery before removing each consumer.

Candidate 38 passed on Fedora and Leap (10,110 cases each), but AlmaLinux
exposed a race in the compression test's byte counter. A peer can receive the
payload before ``Conn.Write`` returns and updates the counter. The test helper
now holds the same mutex across the write and accounting update, so snapshots
cannot observe that intermediate state. A channel-controlled regression fails
on the original helper and passes on all three distributions, including partial
writes, failed writes and empty payloads. No runtime server code is changed by
this fix.

Candidate 39 passed on AlmaLinux. Leap exposed missing pull-interest readiness
in the mirror fixture and a single-sample KV timing outlier. The mirror test now
observes its exact pull-request subscription. Calibrated Go benchmarks retain
the original 100/200-microsecond budgets and clear the first-key block cache
before every cold measurement. Removing the subject-block index optimization
makes all three negative controls fail the unchanged bound.

A deterministic control also proves that follower transitions consumed a pending
stream response without sending it. Only leader callbacks now claim that response;
180 success/error subtests and 180 existing failover tests pass with the race
detector across all three distributions. This does not yet establish the cause
of Fedora's candidate-39 replica-update timeout, which remains a release gate.

Candidate 40 passes the complete Fedora and Leap RPM suites. AlmaLinux first
failed the ghost-consumer fixture, whose replay workers were neither cancelled
on an early return nor joined. Its one-second metadata readiness deadline was
also below the configured 1.5–3.5-second election delay. The corrected fixture
owns and joins its workers, propagates cancellation into client requests, and
observes real Raft traffic for readiness. Negative cleanup controls fail on all
three distributions; 100 race repetitions and three original workload runs per
target pass. The original soak workload and state assertions remain unchanged.

Candidate 41 exposed regressions in the proposed stream/consumer reply patches:
new leaders could repeat already-completed create actions, including sourcing
consumer resets and duplicate advisories. Controlled comparisons restore the
original callback ownership. The synthetic pending-reply tests had installed
private assignments outside the real replicated lifecycle and do not establish
a production defect. Both proposals are withdrawn from candidate 42.

Candidate 42 retains the qualified ghost-fixture teardown/readiness corrections
and observes the exact invalid-delegate and connection-rejection decisions in
the OCSP fixture. Forty race repetitions plus all 126 OCSP results pass per
distribution; disabling OCSP makes the negative control fail on all three.
Candidate 43 additionally joins stream route interest and follower rollup completion
before creating a randomly placed ephemeral consumer. Deterministic paused-apply
controls cover both storage types, subject/all rollups and already-completed
registration. All 720 race-enabled results pass; 12 deliberately invalid mode
checks fail as expected. The candidate-43 full matrix exposed the four failures described below.
Historical workqueue, atomic-batch and performance gates remain open until their
real request paths are established.

Candidate 43 failed on all three distributions: a reused TLS fixture kept an
assigned random port, JWT expiration was observed before the next valid timer
step, and two consumer tests inspected metadata followers before they applied
the successful operation. Candidate 44 clones fixture options, tests the unchanged
expiration step at exact timestamps, and joins committed metadata application.
All 1,494 focused race-enabled cases pass across the three distributions; stale
port, boundary/update and paused-follower negative controls reject the original
assumptions. See ``nats-tls-warning-20261007.json``,
``nats-expiration-20261007.json`` and ``nats-meta-completion-20261007.json``
in ``evidence/``. The complete 103-patch RPM matrix and historical release gates
remain required.

Metadata API readiness after restart
------------------------------------

The restart fixture joins application-level metadata leadership before creating
another stream. Restored stream and consumer leaders can already answer state
queries while the new metadata leader has not yet enabled its API handler.
A creation request sent during that interval is discarded and times out even
if metadata leadership becomes available shortly afterward.

The fixture observes real Raft traffic until metadata API leadership is ready,
preserves the original request deadline, and removes every temporary observer
on success, cancellation or failure. A controlled restart reproduces the same
delete/recreate history, 22 messages and five acknowledged deliveries while
placing stream, consumer and metadata leadership on the restarted server.
The experiment's scheduler gates are excluded from the RPM patch. The clean
patch and deterministic controls pass the race detector on Fedora, Leap and
AlmaLinux; see ``evidence/nats-meta-readiness-20261008.json``.

The replica-update fixture also joins this readiness boundary after intentionally
restarting a server and before reducing a stream from three replicas to one.
The restarted non-stream leader may also be the metadata leader; stream recovery
and message publication do not establish metadata API readiness. Paired controls
hold the real metadata callback, prove the original update is discarded, and
verify that the corrected first request succeeds while preserving all 25 ordered,
deduplicated messages. The clean original fixture passes 30 race-enabled runs
across the three distributions. See ``evidence/nats-failtracking-meta-20261008.json``
for the source identity, scheduling controls and their limits.

The extended stream-info fixture joins its consumer pull-handler interest before
the first fetch. Consumer creation replies arrive independently on the API route;
they do not prove that the randomly connected server has the pull-request
subscription on its account route. The clean fixture passes 60 race-enabled
runs, and 30 controls remove the exact interest, verify ``nats.ErrNoResponders``,
restore it, then complete the original message and replica checks. See
``evidence/nats-extended-interest-20261008.json``. No request retry or timeout
change is included.

Consumer information during metadata deletion
---------------------------------------------

A consumer leader can acknowledge deletion before the metadata leader has
applied it locally. The latter still sees the old assignment and discards an
information request in favor of a consumer leader that has already stopped.
The client ``AddConsumer`` operation begins with this information probe, so it
can time out without ever sending its creation request.

The metadata leader now retains that request until the outstanding consumer
proposals finish, then re-evaluates it through the normal bounded API queue.
A still-live consumer leader remains free to answer immediately. Retention
uses the configured information-queue limit; complete application, leadership
changes and shutdown release owned request data and accounting. Shutdown
cannot replay requests merely because stepping down Raft closes a term.
There is no retry timer, timeout change or unconditional not-found response.

A real update/delete/recreate control reproduces the timeout against the old
server and verifies five fresh consumer lifetimes with all 40 workqueue
messages preserved against the fix. Separate lifetime tests cover a live
remote consumer, copied request data, capacity rejection, partial application,
term changes, refused goroutine starts and shutdown. All 25 broader named
consumer and metadata suites also pass on each distribution. See
``evidence/nats-consumer-apply-20261008.json`` for the withdrawn immediate-error
proposal, exact controls, audit and historical reproduction limits.

MQTT storage before retained-message recovery
---------------------------------------------

The invalid-DEL recovery fixture joins valid retained-message storage before
closing its QoS0 publisher and restarting the server. Neither a successful socket
write nor PubAck for a different record on an independent NATS connection proves
that this publication has been read and stored. A controlled publisher read path
demonstrates that all those earlier operations can finish while the valid record
is absent. After release and the retained-completion join, the unchanged restart
checks recover the valid payload and reject the invalid DEL subject.

The small fixture change passes 60 clean runs and 15 ordering controls across
Fedora, Leap and AlmaLinux with the race detector. The existing runtime replay
readiness fix remains unchanged and independently necessary. See
``evidence/nats-mqtt-retained-20261008.json`` for the exact failure, control model,
source identity and qualification limits.
