# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip, hashlib, json, re, runpy, shutil, statistics

root = Path.cwd()
out = root / 'evidence/controls/nats-sparse-index-20261008'
out.mkdir()
fixed = root / 'work/nats-sparse-index-280-20261008'
results = []
controls = []
timings = {}

def save(name, expected=0):
    p = root / 'results' / name
    status = json.loads((p / 'status.json').read_text())
    log = (p / 'tests.log').read_text()
    assert status['exit_code'] == expected, name
    assert not re.search(r'WARNING|\[ERR\]|\[WRN\]|DATA RACE', log), name
    passes = len(re.findall(r'^\s*--- PASS:', log, re.M))
    failures = len(re.findall(r'^\s*--- FAIL:', log, re.M))
    skips = len(re.findall(r'^\s*--- SKIP:', log, re.M))
    if expected == 0:
        assert failures == skips == 0, name
    shutil.copy2(p / 'status.json', out / (name + '-status.json'))
    (out / (name + '.log.gz')).write_bytes(gzip.compress(log.encode(), mtime=0))
    return {'name': name, 'exit_code': expected, 'race': '-race' in status['command'],
            'reported_passes': passes, 'reported_failures': failures, 'reported_skips': skips}, log

for target in ['fedora', 'leap', 'el10']:
    for number, kind, expected in [(279, 'avl', 21), (280, 'memstore', 46), (280, 'perf', 9), (281, 'broad', 249)]:
        result, log = save(f'{target}-nats-sparse-index-{number}-{kind}')
        assert result['reported_passes'] == expected, result
        results.append(result)
        if kind == 'perf':
            values = re.findall(r'sparse delivery calibrated: (\d+) samples, ([\d.]+)(µs|ms)/op', log)
            assert len(values) == 6
            timings[target] = [{'storage': ['memory', 'file'][i % 2], 'samples': int(n),
                                'microseconds_per_operation': float(value) * (1000 if unit == 'ms' else 1)}
                               for i, (n, value, unit) in enumerate(values)]
            assert all(row['microseconds_per_operation'] < 500000 for row in timings[target])
    result, log = save(f'{target}-nats-avl-high-negative-279', 1)
    assert result['reported_failures'] == 1
    assert 'stored high sequence 18446744073709551615 cannot be found' in log
    controls.append(result)
    result, log = save(f'{target}-nats-sparse-profile-273')
    assert result['reported_passes'] == 6
    controls.append(result)
    p = root / 'results' / result['name']
    shutil.copy2(p / 'cpu-top.txt', out / (target + '-baseline-cpu-top.txt'))
    for profile in p.glob('*.pprof'):
        shutil.copy2(profile, out / (target + '-' + profile.name))

# The AVL source is identical in the separately qualified package and final
# memory-store candidate. This avoids repeating an unchanged successful suite.
assert (fixed / 'seqset.go').read_bytes() == (root / 'work/nats-sparse-index-279-20261008/seqset.go').read_bytes()
assert (fixed / 'seqset_test.go').read_bytes() == (root / 'work/nats-sparse-index-279-20261008/seqset_test.go').read_bytes()

storage = {}
for mode in ['original', 'indexed']:
    result, log = save('fedora-nats-sparse-storage-282-' + mode)
    controls.append(result)
    rows = re.findall(r'BenchmarkMemStoreSparseIndexStorage/subjects=(\d+)-2\s+\d+\s+(\d+) ns/op\s+(\d+) B/op\s+(\d+) allocs/op', log)
    assert len(rows) == 9
    storage[mode] = {str(subjects): {
        'median_ns_per_10000_stores': statistics.median(int(ns) for s, ns, _, _ in rows if int(s) == subjects),
        'median_allocated_bytes_per_10000_stores': statistics.median(int(b) for s, _, b, _ in rows if int(s) == subjects),
        'median_allocations_per_10000_stores': statistics.median(int(a) for s, _, _, a in rows if int(s) == subjects),
    } for subjects in [1, 16, 10000]}

for name in ['memstore.go', 'memstore_test.go', 'store_test.go', 'seqset.go', 'seqset_test.go']:
    (out / (name + '.gz')).write_bytes(gzip.compress((fixed / name).read_bytes(), mtime=0))
shutil.copy2(fixed / 'nats-server-memory-subject-sequences.patch', out / 'nats-server-memory-subject-sequences.patch')
for name in ['nats-sparse-delivery-profile-273.json', 'run-nats-sparse-profile-273.py',
             'nats-sparse-index-279.json', 'nats-sparse-index-280.json', 'nats-sparse-index-281.json',
             'nats-sparse-storage-282.json', 'run-nats-sparse-storage-282.py',
             'nats-sparse-index-storage-benchmark-282.go', 'run-nats-focused-38.py',
             'record-nats-sparse-index-20261008.py']:
    shutil.copy2(root / 'work' / name, out / name)
(out / 'profile-overlay.go.gz').write_bytes(gzip.compress(
    (root / 'work/nats-sparse-delivery-profile-273-20261008/norace_1_test.go').read_bytes(), mtime=0))
(out / 'storage-benchmark-overlay.go.gz').write_bytes(gzip.compress(
    (root / 'work/nats-sparse-index-storage-282-20261008/memstore_test.go').read_bytes(), mtime=0))

audit = runpy.run_path(root / 'work/write-scoped-audit.py')
passes = {
    9: 'New tests, patches and qualification scripts carry copyright 2026; upstream notices are preserved.',
    53: 'The runtime indexes subject sequences to remove unrelated-message scans. Original workloads, deadlines, compiler flags and lazy-bound semantics remain unchanged. No suppression or fixture workaround is introduced.',
    54: 'Go owns subject indexes with their subject-tree entries; purge/reset replace the tree and final deletion releases the entry. No new goroutines, timers, external resources or fallible callbacks are introduced.',
    55: 'The owning memory-store mutex guards insertion, deletion and successor lookup. All 948 final store/sequence-set results pass under the Go race detector.',
    56: 'The private subject state embeds the existing SimpleState; external copies retain that type. SequenceSet.Ceil returns uint64 plus an explicit found flag, preserving valid zero sequences.',
    57: 'Literal delivery replaces a linear unrelated-message scan with an AVL lower-bound lookup. Storage controls measure allocation/throughput cost for dense and singleton subjects. Single-message subjects initially allocate no sequence tree.',
    58: 'Empty/nil sets, absent successors, duplicate insertion, deletion, maximum uint64 sequences, randomized store mutations, purges, compaction, truncation, limits and reinsertion are covered. Guarded subtraction avoids the reproduced unsigned upper-bound overflow.',
    59: 'The new successor API documents its result and bounds. Evidence records the precise optimization scope, memory cost, baseline profiling limits and remaining combined/native gates.',
    61: 'Successor bitmap access is bounded by numEntries and bitsPerBucket; shifts stay within uint64 width. Tests use isolated offline networks and no external credentials.',
    62: 'Successors are checked against an independently sorted reference; filtered delivery is checked against live-message scans. All 975 final results pass across three distributions. The original maximum-sequence control fails on each target.',
}
audit['write'](out / 'audit.rst', 'NATS memory-subject sequence audit',
               'Scope: compressed per-subject memory-store index, AVL successor lookup and unsigned-range correction, regression tests and packaging evidence. All 62 checks: 10 Pass, 52 N/A, 0 Fail. Combined RPM and native qualification remain required.',
               passes, 'No corresponding Qore module/QPP/DataProvider/JNI, C++ implementation or Qore-language test change in this scope.')

record = {
    'schema': 1, 'date': '2026-10-08', 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
    'status': 'Sparse literal delivery index and sequence-range correction focused-qualified; candidate integration, complete RPM/native and installed qualification remain required.',
    'root_cause': 'The memory store narrows literal delivery only to first/last subject bounds, then looks up every intervening sequence. Four matching messages separated by two million unrelated messages cause two million map probes per delivery. Delivery-benchmark-only CPU profiles attribute 62.36-74.73 percent of sampled CPU to this scan.',
    'fix': 'Maintain a compressed AVL sequence set after a subject first contains two messages, update it on every removal, and seek the next matching sequence during literal delivery. Existing subject bounds remain lazy and external SimpleState copies remain unchanged.',
    'additional_defect': 'SequenceSet compared seq >= base + numEntries; the upper bound overflows in the last uint64 block. Guarded seq-base comparisons correct insertion, lookup and deletion. Original code fails the exact maximum-sequence regression on all three targets.',
    'qualification': {'results': results, 'race_results': sum(x['reported_passes'] for x in results if x['race']),
                      'nonrace_results': sum(x['reported_passes'] for x in results if not x['race']), 'delivery_timings': timings},
    'controls': controls, 'storage_cost': storage, 'audit': {'pass': 10, 'na': 52, 'fail': 0},
    'limits': [
        'The original historical 502/571 ms failures have no original CPU/scheduler trace. Current baseline profiles establish the linear delivery cost; they do not reconstruct those exact historical runs.',
        'Profiling excludes publication of the two million unrelated messages but includes consumer creation/deletion around the benchmark timer. Map scanning remains the dominant sampled cost.',
        'Optimization applies to literal filtered delivery. Wildcard and multi-filter behavior is regression-tested but remains algorithmically unchanged.',
        'Storage microbenchmarks are x86_64 Fedora controls with three samples per case, run sequentially on a shared host. Their allocation counts quantify overhead; timings do not prove absence of regression for every workload.',
        'Prototype 274 first failed compilation because a shared test accessed the old private state type; 275 preserved results but eagerly changed lazy-bound internals, so that change was withdrawn. 276-278 did not start tests because new bind-mount destinations were absent on a read-only source tree. Tests were merged into existing files for final qualification.',
        'The final sparse test retains both stores, two million unrelated messages, four delivered messages and the original 500 ms bound. Full combined RPM/native, installed client/module and repository lifecycle gates remain open.',
    ],
    'source_sha256': {name: hashlib.sha256((fixed / name).read_bytes()).hexdigest()
                      for name in ['memstore.go', 'memstore_test.go', 'store_test.go', 'seqset.go', 'seqset_test.go']},
    'files_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())},
}
assert record['qualification']['race_results'] == 948
assert record['qualification']['nonrace_results'] == 27
(root / 'evidence/nats-sparse-index-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'qualification': record['qualification'], 'storage_cost': storage}, indent=2))
