# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
%global source_date_epoch_from_changelog 1
%global use_source_date_epoch_as_buildtime 1
%if v"%{rpmversion}" >= v"4.20"
%global build_mtime_policy clamp_to_source_date_epoch
%else
%global clamp_mtime_to_source_date_epoch 1
%endif
%if 0%{?fedora}
# GDB indexes overlap for Go zero-size globals. Preserve full DWARF and DWZ.
# Approved in evidence/nats-debug-packaging-20261004.json.
%undefine _include_gdb_index
%endif
Name: nats-server
Version: 2.15.0
Release: 1.qore%{?dist}
Summary: NATS messaging and JetStream server
License: Apache-2.0 AND MIT AND BSD-3-Clause
URL: https://github.com/nats-io/nats-server
Source0: https://github.com/nats-io/nats-server/archive/refs/tags/v%{version}.tar.gz#/nats-server-%{version}.tar.gz
# Reproducible generated input, served with this OBS source package. Its exact
# digest and regeneration procedure are recorded in sources.json and the guide.
Source1: https://api.opensuse.org/public/source/home:davidnichols:qore:testing/nats-server/nats-server-%{version}-vendor.tar.xz
Source2: nats-server-vendor-licenses.json
Source3: nats-server-GO-LICENSE
Source4: nats-server-tests.py
Source5: test_nats_server_tests.py
Source6: nats-server-example.conf
Source7: nats-server.1
Patch0: nats-server-syslog-tests.patch
Patch1: nats-server-log-rotation-tests.patch
Patch2: nats-server-replica-tests.patch
Patch3: nats-server-election-tests.patch
Patch4: nats-server-watcher-tests.patch
Patch5: nats-server-ttl-tests.patch
Patch6: nats-server-route-interest-tests.patch
Patch7: nats-server-purge-tests.patch
Patch8: nats-server-auth-expiration-tests.patch
Patch9: nats-server-offline-peer-tests.patch
Patch10: nats-server-fetch-tests.patch
Patch11: nats-server-candidate-term-tests.patch
Patch12: nats-server-sublist-notification.patch
Patch13: nats-server-delivery-interest-tests.patch
Patch14: nats-server-websocket-tests.patch
Patch15: nats-server-storage-recovery-tests.patch
Patch16: nats-server-snapshot-config-tests.patch
Patch17: nats-server-consumer-pause-tests.patch
Patch18: nats-server-no-interest-election-tests.patch
Patch19: nats-server-shutdown-drain.patch
Patch20: nats-server-ack-batch-tests.patch
Patch21: nats-server-consumer-completion-tests.patch
Patch22: nats-server-leaf-slow-consumer-tests.patch
Patch23: nats-server-batch-sequence-routes.patch
Patch24: nats-server-paging-budget-tests.patch
Patch25: nats-server-memory-setup-tests.patch
Patch26: nats-server-account-gateway-tests.patch
Patch27: nats-server-route-disconnect-tests.patch
Patch28: nats-server-route-pong-capacity.patch
Patch29: nats-server-route-duplicate-budget-tests.patch
Patch30: nats-server-revocation-completion-tests.patch
Patch31: nats-server-websocket-restart-tests.patch
Patch32: nats-server-slow-route-recovery-tests.patch
Patch33: nats-server-leaf-drain-completion-tests.patch
Patch34: nats-server-consumer-resume.patch
Patch35: nats-server-storage-observer-tests.patch
Patch36: nats-server-mqtt-completion-tests.patch
Patch37: nats-server-rescale-completion-tests.patch
Patch38: nats-server-cluster-readiness-tests.patch
Patch39: nats-server-process-memory.patch
Patch40: nats-server-performance-tests.patch
Patch41: nats-server-ocsp-completion-tests.patch
Patch42: nats-server-batch-workqueue-readiness-tests.patch
Patch43: nats-server-consumer-state-batch-tests.patch
Patch44: nats-server-reply-gateway-readiness-tests.patch
Patch45: nats-server-sublist-counts.patch
Patch46: nats-server-leaf-origin-count-tests.patch
Patch47: nats-server-catchup-abort.patch
Patch48: nats-server-health-tests.patch
Patch49: nats-server-mqtt-readiness.patch
Patch50: nats-server-implicit-route-pending.patch
Patch51: nats-server-route-retry-capacity.patch
Patch52: nats-server-consumer-store-stop.patch
Patch53: nats-server-consumer-move-tests.patch
Patch54: nats-server-client-close-tests.patch
Patch55: nats-server-cluster-api-fixtures.patch
Patch56: nats-server-consumer-info-startup.patch
Patch57: nats-server-mqtt-retained-fixtures.patch
Patch58: nats-server-sparse-delivery-tests.patch
Patch59: nats-server-service-expiry-tests.patch
Patch60: nats-server-gateway-dns-listener-tests.patch
Patch61: nats-server-raft-progress-tests.patch
Patch62: nats-server-mqtt-subscribe-completion.patch
Patch63: nats-server-proxy-tunnel-buffer.patch
Patch64: nats-server-auth-service-ready.patch
Patch65: nats-server-connection-count.patch
Patch66: nats-server-latency-expiry-tests.patch
Patch67: nats-server-route-tls-name-tests.patch
Patch68: nats-server-leaf-queue-completion.patch
Patch69: nats-server-consumer-signal-tests.patch
Patch70: nats-server-advisory-store-completion-tests.patch
Patch71: nats-server-retained-observer-tests.patch
Patch72: nats-server-trace-gateway-completion-tests.patch
Patch73: nats-server-ocsp-rejection-tests.patch
Patch74: nats-server-failure-context-tests.patch
Patch75: nats-server-gateway-listener-lifetimes-tests.patch
Patch76: nats-server-consumer-audit-completion-tests.patch
Patch77: nats-server-state-batch-completion-tests.patch
Patch78: nats-server-producer-stall-clock-tests.patch
Patch79: nats-server-consumer-purge-readiness-tests.patch
Patch80: nats-server-leaf-protocol-completion-tests.patch
Patch81: nats-server-ocsp-unknown-completion-tests.patch
Patch82: nats-server-mapping-workqueue-completion-tests.patch
Patch83: nats-server-consumer-quorum-fault-tests.patch
Patch84: nats-server-gateway-stream-observation-tests.patch
Patch85: nats-server-trace-response-dispatch.patch
Patch86: nats-server-cluster-route-fixtures.patch
Patch87: nats-server-mqtt-session-recovery.patch
Patch88: nats-server-latency-ocsp-fixtures.patch
Patch89: nats-server-consumer-info-removal.patch
Patch90: nats-server-pinned-account-lifetimes-tests.patch
Patch91: nats-server-unknown-delivery-readiness-tests.patch
Patch92: nats-server-reverse-subject-bounds.patch
Patch93: nats-server-consumer-info-lifetime.patch
Patch94: nats-server-compression-test-accounting.patch
Patch95: nats-server-mirror-pull-interest-tests.patch
Patch96: nats-server-kv-lookup-benchmark-tests.patch
Patch97: nats-server-ghost-replay-lifetime-tests.patch
Patch98: nats-server-ocsp-delegate-rejection-tests.patch
Patch99: nats-server-rollup-completion-tests.patch
Patch100: nats-server-tls-warning-listeners-tests.patch
Patch101: nats-server-expiration-boundary-tests.patch
Patch102: nats-server-meta-completion-tests.patch
Patch103: nats-server-publication-completion-tests.patch
Patch104: nats-server-purge-route-tests.patch
Patch105: nats-server-peer-removal-startup-tests.patch
Patch106: nats-server-purge-replica-completion-tests.patch
Patch107: nats-server-snapshot-application-tests.patch
Patch108: nats-server-meta-api-ready-tests.patch
Patch109: nats-server-failtracking-meta-ready-tests.patch
Patch110: nats-server-extended-info-interest-tests.patch
Patch111: nats-server-consumer-info-apply.patch
BuildRequires: gcc
BuildRequires: gdb
BuildRequires: glibc-devel
BuildRequires: python3 >= 3.11
%if 0%{?suse_version}
BuildRequires: go1.26 >= 1.26.0
BuildRequires: procps
BuildRequires: util-linux
%else
BuildRequires: golang >= 1.26.0
BuildRequires: procps-ng
BuildRequires: util-linux-core
%endif
Provides: bundled(golang(github.com/antithesishq/antithesis-sdk-go)) = 0.8.0~default.no.op
Provides: bundled(golang(github.com/google/go-tpm)) = 0.9.8
Provides: bundled(golang(github.com/klauspost/compress)) = 1.20.0
Provides: bundled(golang(github.com/minio/highwayhash)) = 1.0.4
Provides: bundled(golang(github.com/nats-io/jwt/v2)) = 2.8.2
Provides: bundled(golang(github.com/nats-io/nats.go)) = 1.51.0
Provides: bundled(golang(github.com/nats-io/nkeys)) = 0.4.16
Provides: bundled(golang(github.com/nats-io/nuid)) = 1.0.1
Provides: bundled(golang(golang.org/x/crypto)) = 0.57.0
Provides: bundled(golang(golang.org/x/sys)) = 0.48.0
Provides: bundled(golang(golang.org/x/time)) = 0.16.0

%description
NATS server with core messaging, authenticated and encrypted connections,
and JetStream persistence. Includes the command-line server and sample
configuration. No service is started during installation. Dependencies are
pinned by upstream go.mod/go.sum and compiled from bundled source offline.

%prep
%autosetup -p1
%{__tar} -xf %{SOURCE1}
python3 - '%{SOURCE2}' <<'PY'
import hashlib, json, shutil, sys
from pathlib import Path
manifest = json.loads(Path(sys.argv[1]).read_text())
assert manifest['version'] == '%{version}'
for name, digest in manifest['licenses_sha256'].items():
    path = Path(name)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
    target = Path('vendor-licenses') / path.relative_to('vendor')
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, target)
PY
cp %{SOURCE3} GO-LICENSE
cp %{SOURCE4} %{SOURCE5} .
cp %{SOURCE6} nats-server.conf
%build
%{?set_build_flags}
# Go's distribution-supplied FIPS module is copied into GOPATH even with
# vendoring. Keep that private cache writable for RPM's unprivileged cleanup.
export GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off GOFLAGS='-mod=vendor -modcacherw'
%if 0%{?suse_version}
# Match Fedora/RHEL's DWARF4 compatibility with RPM debugedit and dwz.
# Approved in evidence/nats-debug-packaging-20261004.json.
export GOEXPERIMENT=nodwarf5
%endif
export GOPATH="$PWD/.gopath" GOCACHE="$PWD/.gocache"
export CGO_ENABLED=1 CGO_CFLAGS="$CFLAGS" CGO_LDFLAGS="$LDFLAGS"
export GOMAXPROCS=%{_smp_build_ncpus}
mkdir -p build
# Keep source paths until RPM debugedit remaps and collects them. Leave DWARF
# uncompressed for debugedit/dwz; RPM packaging handles the final compression.
/usr/bin/go build -buildvcs=false -buildmode=pie -ldflags='-linkmode=external -compressdwarf=false' -o build/nats-server .
%install
# Use the full debugger for any distribution-enabled symbol processing.
export GDB=%{_bindir}/gdb
install -Dm755 build/nats-server %{buildroot}%{_bindir}/nats-server
install -Dm644 %{SOURCE7} %{buildroot}%{_mandir}/man1/nats-server.1
install -d %{buildroot}%{_licensedir}/%{name}
cp -a LICENSE GO-LICENSE vendor-licenses %{buildroot}%{_licensedir}/%{name}/
# Preserve each dependency's notice path while sharing identical notice data.
hardlink -t -O %{buildroot}%{_licensedir}/%{name}
%check
export GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off GOFLAGS='-mod=vendor -modcacherw'
%if 0%{?suse_version}
export GOEXPERIMENT=nodwarf5
%endif
export GOPATH="$PWD/.gopath" GOCACHE="$PWD/.gocache" CGO_ENABLED=1
export GOMAXPROCS=%{_smp_build_ncpus}
./build/nats-server --version
./build/nats-server -t -c nats-server.conf
# Match upstream's separate family budgets while enumerating every compiled
# unit test, example and fuzz seed case; no newly added test can be omitted.
python3 -B -W error -m unittest -v test_nats_server_tests.py
python3 -B -W error nats-server-tests.py
%files
%license %{_licensedir}/%{name}/
%doc README.md RELEASES.md nats-server.conf
%{_bindir}/nats-server
%{_mandir}/man1/nats-server.1*
%changelog
* Thu Oct 08 2026 David Nichols <david@qore.org> - 2.15.0-1.qore
- Re-evaluate consumer information after pending metadata deletions apply.
- Bound retained requests and release them on application, term changes and shutdown.
- Join consumer pull-handler interest before the extended-info fixture fetch.
- Join metadata API readiness before the post-restart replica update.
- Join metadata API leadership before stream creation after a server restart.
- Verify cancellation and cleanup of temporary metadata traffic observers.

* Wed Oct 07 2026 David Nichols <david@qore.org> - 2.15.0-1.qore
- Clone TLS fixtures before server mutation and join remote metadata application.
- Verify JWT expiration at exact boundaries using the unchanged expiration step.
- Join ghost-replay fixture workers and observe real metadata restart readiness.
- Verify delegated OCSP rejection independently of TLS alert/write ordering.
- Join route interest and follower store/purge completion in rollup tests.
- Observe mirrored pull interest before the first fetch.
- Calibrate cold/warm KV lookup costs with unchanged performance budgets.
- Revalidate startup consumer-info assignments before serializing fallback replies.
- Join revoked-client closure and route readiness in cluster fixtures.
- Bound reverse subject scans after proving the removed upper range is empty.
- Serialize compression-test byte snapshots with writes; test partial and failed writes.

* Tue Oct 06 2026 David Nichols <david@qore.org> - 2.15.0-1.qore
- Let current cluster authority answer consumer-info requests after local peer removal.
- Preserve standalone and metadata-authoritative not-found responses.

* Tue Oct 06 2026 David Nichols <david@qore.org> - 2.15.0-1.qore
- Join local and routed service subscriptions before latency requests.
- Verify fresh latency metrics and duplicate-response completion without sleeps.
- Check cached OCSP revocation and server rejection instead of TLS transport text.

* Tue Oct 06 2026 David Nichols <david@qore.org> - 2.15.0-1.qore
- Recover legacy MQTT sessions after a lost creation reply or interrupted migration.
- Preserve concurrent/newer records and unrelated streams; retry failed cleanup safely.
- Synchronize three cluster fixtures with stream and consumer route readiness.

* Tue Oct 06 2026 David Nichols <david@qore.org> - 2.15.0-1.qore
- Retain service trace response mappings until dispatch finishes adding hops.

* Tue Oct 06 2026 David Nichols <david@qore.org> - 2.15.0-1.qore
- Observe transient stream-info errors during the existing gateway recovery deadline.

* Tue Oct 06 2026 David Nichols <david@qore.org> - 2.15.0-1.qore
- Keep metadata leadership intact when injecting consumer destination quorum loss.

* Tue Oct 06 2026 David Nichols <david@qore.org> - 2.15.0-1.qore
- Join MQTT retained-consumer updates and pull-request completion events.

* Tue Oct 06 2026 David Nichols <david@qore.org> - 2.15.0-1.qore
- Join leaf subscription and OCSP certificate decisions in protocol fixtures.
- Remove a duplicate CONNECT and test its additional protocol responses.

* Tue Oct 06 2026 David Nichols <david@qore.org> - 2.15.0-1.qore
- Join request-subscription propagation before the consumer purge regression.

* Tue Oct 06 2026 David Nichols <david@qore.org> - 2.15.0-1.qore
- Join consumer route and partial-batch completion before assertions.
- Check producer stall budgets with virtual time and retain network integration.
- Capture bounded debug logs if atomic stream creation fails.

* Tue Oct 06 2026 David Nichols <david@qore.org> - 2.15.0-1.qore
- Correct gateway listener lifetimes and join consumer route readiness in tests.
- Join missing-consumer lookup fanout and cover delayed-peer audit responses.

* Tue Oct 06 2026 David Nichols <david@qore.org> - 2.15.0-1.qore
- Join consumer, retained-message, gateway and TLS decision completion in tests.
- Capture unresolved audit, migration and sparse-delivery failure context.

* Mon Oct 05 2026 David Nichols <david@qore.org> - 2.15.0-1.qore
- Use the released migration implementation to resolve immediate reverse-move stalls.
- Preserve reviewed lifecycle and routing fixes with their regression controls.
- Count distinct leaf origins and cached/wildcard subscription interest correctly.
- Join gateway responder readiness and fetch complete consumer-state batches.

* Fri Oct 02 2026 David Nichols <david@qore.org> - 2.14.7-1.qore
- Build the NATS test broker from pinned source and vendored Go dependencies.
- Preserve dependency notices and run upstream offline unit/integration tests.
- Serialize interest notification registration with subscription transitions.
- Observe snapshot delivery interest and check every restore chunk response.
- Consume complete batches in consumer-pause assertions.
- Bound WebSocket integrity-test traffic and verify every subscriber is ready.
- Observe stream signal, ack and route-interest completion in fixtures.
- Exercise leaf write timeout before/after CONNECT with deterministic TCP closure.
- Wait for stream and consumer route interest in batch/sequence fixtures.
- Separate the paging fixture request budget from its transport pending limit.
- Complete memory stream setup before publishing and check every acknowledgement.
- Flush responder interest and observe gateway protocol and route-disconnect completion.
- Recheck negotiated route capacity after delayed PONGs and reconnects.
- Coalesce implicit route attempts through handshake completion and release failed reservations.
- Preserve explicit reconnect metadata when an incoming replacement wins.
- Use the approved topology-based duplicate-close test budget and retain storm controls.
- Preserve collectable source paths and leave DWARF compression to RPM tooling.
- Ship and validate a loopback-only JetStream example configuration.
- Keep the distribution FIPS module cache writable for unprivileged RPM cleanup.
- Use approved Leap DWARF4 and retain full Fedora DWARF without the rejected optional index.
- Add a command manual, preserve identical license notices as hard links, and document the generated source URL.
- Wake pending consumer delivery when a pause deadline changes or clears.
- Observe revocation closure, drained queue members and retained-message application in fixtures.
- Verify an exact partial route-write timeout and recovery on the same connection.
- Observe the current Raft stream generation and storage completion after rescaling.
- Preserve account byte accounting when observing file and memory stores.
- Join consumer persistence and retain shutdown write errors.
- Read current Linux process counters and test interval CPU semantics.
- Complete cluster/OCSP fixtures and retain calibrated performance bounds.
- Answer consumer-info requests throughout initial assignment propagation.
- Join client teardown, MQTT retained application and route/advisory delivery in tests.
- Calibrate sparse delivery with the original workload and performance bound.
- Preserve HTTP CONNECT tunnel data read together with response headers.
- Join Raft, queue, MQTT, authentication and remote accounting completion in tests.
