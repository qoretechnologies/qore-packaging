# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import collections
import gzip
import hashlib
import json
import re
import runpy
import shutil

root = Path.cwd()
output = root / 'evidence/controls/jni-native-runner-20261007'
output.mkdir(exist_ok=True)
expected_aot = {'QUnit', 'DataProvider', 'RestSchemaValidator', 'DataStreamUtil',
                'Swagger', 'OpenApi3', 'RestClient', 'RestClientIo'}
records = {}
for target in ('fedora', 'leap', 'el10'):
    directory = root / ('results/' + target + '-jni-native-final-20261007')
    status = json.loads((directory / 'status.json').read_text())
    assert status['exit_code'] == 0 and all(row['exit_code'] == 0 for row in status['steps'])
    for name, digest in status['code_sha256'].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
    records[target] = {'steps': status['steps'], 'phases': {}, 'bootstrap_image': status['bootstrap_image']}
    bundles = []
    for phase in ('sdk', 'runtime'):
        path = directory / phase
        result = json.loads((path / 'qualification.json').read_text())
        assert result['exit_code'] == 0 and result['machine'] == 'x86_64'
        assert all(row['exit_code'] == 0 for row in result['steps'])
        bundles.append(result['jni_fixture_bundle'])
        counts = []
        aot = collections.Counter()
        awt = 0
        for log in path.glob(phase + '-jni-*.log'):
            text = log.read_text()
            assert 'Fontconfig error:' not in text, str(log)
            counts += [(int(a), int(b), int(c)) for a, b, c in re.findall(
                r'Ran (\d+) test cases?, (\d+) succeeded \((\d+) assertions?\)', text)]
            lines = text.splitlines()
            for index, line in enumerate(lines):
                if line.startswith('warning:'):
                    match = re.search(r"for feature '([^']+)'", line)
                    assert match and match[1] in expected_aot and 'AOT-MODULE-STALE:' in line, (log, line)
                    assert re.search(r"optional module 'xml(?: >= 1\.3)?' was not available, but it is available now; rebuild the binary module$", line), (log, line)
                    aot[match[1]] += 1
                elif line.startswith('WARNING in native method:'):
                    assert line == 'WARNING in native method: JNI call made without checking exceptions when required to from CallObjectMethodV'
                    assert index + 1 < len(lines) and '\tat sun.font.SunLayoutEngine.shape(' in lines[index + 1]
                    assert target in ('leap', 'el10')
                    awt += 1
                elif re.search(r'(?i)^(?:warning|error|fatal):', line):
                    raise AssertionError((log, line))
        assert counts and all(a == b for a, b, _ in counts)
        assert len(counts) == (37 if phase == 'sdk' else 23), (target, phase, len(counts))
        assert sum(a for a, _, _ in counts) == (632 if phase == 'sdk' else 478)
        previous = (root / ('results/' + target + '-jni-installed-final-3') / (phase + '-tests.log')).read_text()
        prior_counts = [tuple(map(int, values)) for values in re.findall(
            r'Ran (\d+) test cases?, (\d+) succeeded \((\d+) assertions?\)', previous)]
        assert sorted(counts) == sorted(prior_counts), (target, phase)
        if phase == 'runtime':
            inventory = (path / 'runtime-inventory.log').read_text().splitlines()
            names = {line.split()[0] for line in inventory}
            assert not names & {'qore-devel', 'gcc', 'gcc-c++', 'qore-jni-tools', 'qore-jni-kotlin'}
            assert not any(re.fullmatch(r'java-.*-devel', name) for name in names), names
            assert not any(row['name'].startswith('sdk-') for row in result['steps'])
        records[target]['phases'][phase] = {
            'exit_code': 0, 'suites': len(counts), 'cases': sum(row[0] for row in counts),
            'assertions': sum(row[2] for row in counts), 'approved_aot_diagnostics': dict(aot),
            'approved_awt_diagnostics': awt, 'font_cache_diagnostics': 0,
        }
        for file in sorted(path.iterdir()):
            if file.suffix in ('.log', '.json'):
                destination = output / (target + '-' + phase + '-' + file.name)
                if file.suffix == '.log':
                    destination = destination.with_suffix(destination.suffix + '.gz')
                    destination.write_bytes(gzip.compress(file.read_bytes(), mtime=0))
                else:
                    shutil.copy2(file, destination)
    assert bundles[0] == bundles[1]
    records[target]['fixture_bundle'] = bundles[0]
    shutil.copy2(directory / 'status.json', output / (target + '-status.json'))
for name in ('jni-native-all-tools-tests-final-20261007.log', 'jni-native-ci-lint-20261007.log',
             'jni-native-ci-simulation-20261007.log'):
    shutil.copy2(root / 'results' / name, output / name)
assert 'Ran 211 tests' in (output / 'jni-native-all-tools-tests-final-20261007.log').read_text()
for name in ('test-jni-native-final-20261007.py', 'prepare-jni-native-20261007.py'):
    shutil.copy2(root / 'work' / name, output / name)
record = {
    'schema': 1, 'date': '2026-10-07',
    'status': 'Separate SDK/runtime runner passes clean x86_64 integration on three distributions; native ARM CI execution remains required.',
    'implementation': ['SDK jobs build three first-party JARs and a native Qore consumer; a full-manifest SHA-256 binding controls the runtime handoff.',
                       'Fresh runtime jobs install no compiler or Java development package. Fixtures run unprivileged with private writable home/cache directories.',
                       '97 source fixtures and signed JNI/XML/Python/process RPMs are pinned; core runtime/ONNX and SDK checks remain enabled.'],
    'tool_tests': 211, 'counting': 'Accept singular and plural QUnit summaries; all per-suite case/assertion totals match the raw prior installed logs (632 SDK cases, 478 runtime cases).', 'ci_lint': 'passed static validation and pipeline-creation simulation',
    'targets': records,
    'diagnostic_approvals': ['evidence/qunit-xml-aot-diagnostic-20261006.json',
                           'evidence/xml-library-aot-diagnostics-20261006.json',
                           'evidence/jni-awt-diagnostic-20261003.json'],
    'limits': ['Earlier retained image IDs had been removed by cleanup; no test ran in those attempts.',
               'The first fresh-container attempt used ARM-specific Fedora/Leap image pins; x86_64 validation uses separately resolved native image digests.',
               'Initial fresh tests exposed an unwritable inherited home. Final runs use the corrected private home and have zero Fontconfig cache errors.',
               'The superseded exploratory Leap runtime job was stopped after its SDK passed; only the complete final runs qualify the changed runner.',
               'JMS external-broker checks, final core22 combined installation and repository lifecycle remain separate gates.'],
    'files_sha256': {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(output.iterdir())},
}
(root / 'evidence/jni-native-runner-20261007.json').write_text(json.dumps(record, indent=2) + '\n')
passes = {
    9: 'All new helper, tests, manifests and documentation carry 2026 copyright.',
    53: 'The runner supplies actual SDK-built fixtures to a fresh runtime and fixes the missing writable home; no test or diagnostic is disabled.',
    54: 'Bundle metadata is published last; complete provenance validation precedes copies and installation. Temporary fixture directories clean up on failure.',
    55: 'Native jobs share only immutable pinned inputs and a verified completed artifact. Separate containers and per-run directories isolate mutable test state.',
    56: 'Exact artifact inventories, native architecture, source revisions, phases, hashes and installed binary paths are validated.',
    57: 'The bundle contains only four reviewed artifacts; runtime requires no compilation. CI dependencies enforce completion without polling.',
    58: 'Tests cover tampering, wrong source/architecture, missing files, symlinks, partial copies, destination preservation, failed downloads and phase boundaries.',
    59: 'qualification/JNI.rst explains job ordering, command examples, fixture provenance, private caches and remaining external gates.',
    61: 'RPM signatures and hashes remain mandatory; manifests contain no credentials or arbitrary commands. Source/path and compiler absence checks remain enabled.',
    62: '211 tool tests, CI validation/simulation and six fresh installed phases pass, including core ONNX, JNI/Python interoperability and native consumer execution.',
}
runpy.run_path(str(root / 'work/write-scoped-audit.py'))['write'](
    root / 'evidence/jni-native-runner-20261007.audit.rst', 'JNI native installed-package runner audit',
    'Scope: Python runner/helper, fixture inventory, pinned manifests, CI jobs, regression tests and documentation. 10 Pass, 52 N/A, 0 Fail.',
    passes, 'No Qore module source, C++, QPP, DataProvider registration, sandbox or runtime JAR implementation is changed.',
)
print('JNI runner qualified: 211 tool tests and six fresh installed phases')
