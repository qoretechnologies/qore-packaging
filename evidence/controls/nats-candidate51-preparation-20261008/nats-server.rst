NATS server dependency
======================

Copyright 2026 Qore Technologies, s.r.o.

Candidate 51 combines upstream 2.15.0 with 114 patches. The full combined RPM
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
deduplicated messages. The corrected fixture passes 30 race-enabled runs
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
