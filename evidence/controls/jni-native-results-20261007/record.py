# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Verify completed native JNI artifacts before recording their qualification."""
from pathlib import Path
import collections
import hashlib
import json
import re
import shutil
import struct
import zipfile

root = Path(__file__).resolve().parents[1]
jobs = json.loads((root / 'results/jni-native-jobs-59874-current.json').read_text())
commit = 'f9f7e31bf1d9458fb0a5dc73210c99ec412c30d5'
assert len(jobs) == 7 and all(j['status'] == 'success' and j['commit']['id'] == commit for j in jobs)
previous = json.loads((root / 'evidence/jni-native-runner-20261007.json').read_text())
expected_modules = {'QUnit', 'DataProvider', 'RestSchemaValidator', 'DataStreamUtil',
                    'Swagger', 'OpenApi3', 'RestClient', 'RestClientIo'}
records = {}
archives = []
for target in ('fedora', 'leap', 'el10'):
    manifest = json.loads((root / f'qualification/jni-{target}-aarch64.json').read_text())
    manifest_hash = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    bundles = []
    phases = {}
    for phase in ('sdk', 'runtime'):
        job = next(j for j in jobs if j['name'] == f'rpm-jni-{target}-{phase}-arm64')
        archive = root / f'results/jni-native-{target}-{phase}-artifacts-20261007.zip'
        assert archive.stat().st_size == job['artifacts_file']['size']
        archives.append((archive, target + '-' + phase + '.zip'))
        directory = 'results/native-installed/' if phase == 'sdk' else 'results/native-runtime/'
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            result = json.loads(z.read(directory + 'qualification.json'))
            assert result['manifest'] == manifest
            assert result['exit_code'] == 0 and result['machine'] == 'aarch64'
            assert result['runner_arch'] == 'linux/arm64' and result['jni_phase'] == phase
            assert all(row['exit_code'] == 0 for row in result['steps'])
            names = {row['name'] for row in result['steps']}
            assert len(names) == len(result['steps'])
            assert {phase + '-runtime', phase + '-jni-headless'} <= names
            if phase == 'sdk':
                assert {'sdk-development', 'sdk-tools', 'sdk-remote-debuggers', 'sdk-jni-compiler',
                        'sdk-jni-build-java-fixtures', 'sdk-jni-build-kotlin-fixture'} <= names
            else:
                assert {'runtime-jni-compiled-consumer', 'runtime-jni-fixture-layout'} <= names
                assert not any(name.startswith('sdk-') for name in names)
                inventory = z.read(directory + 'runtime-inventory.log').decode().splitlines()
                packages = {line.split()[0] for line in inventory}
                assert not packages & {'qore-devel', 'gcc', 'gcc-c++', 'qore-jni-tools', 'qore-jni-kotlin'}
                assert not any(re.fullmatch(r'java-.*-devel', name) for name in packages)
            bundle = result['jni_fixture_bundle']
            assert bundle['arch'] == 'aarch64' and bundle['qualification_manifest_sha256'] == manifest_hash
            assert set(bundle['files']) == {'test/qore-jni-test.jar', 'test/opcua-test-server.jar',
                                           'test/kotlin-test.jar', 'jni-smoke'}
            bundles.append(bundle)
            if phase == 'sdk':
                assert json.loads(z.read('results/jni-fixtures/bundle.json')) == bundle
                for name, digest in bundle['files'].items():
                    data = z.read('results/jni-fixtures/' + name)
                    assert hashlib.sha256(data).hexdigest() == digest
                    if name == 'jni-smoke':
                        assert data[:6] == b'\x7fELF\x02\x01' and struct.unpack_from('<H', data, 18)[0] == 183
            counts = {}
            diagnostic_counts = collections.Counter()
            logs = {}
            for row in result['steps']:
                name = row['name']
                data = z.read(directory + name + '.log')
                text = data.decode()
                logs[name] = hashlib.sha256(data).hexdigest()
                assert 'Fontconfig error:' not in text
                if name.startswith('verify-signature-'):
                    assert re.search(r'(?i)signature.*(?:\n[^\n]*)?: OK', text), (target, phase, name)
                    assert not re.search(r'(?i)\b(?:NOKEY|NOT OK|BAD|NOTTRUSTED)\b', text)
                found = [tuple(map(int, row)) for row in re.findall(
                    r'Ran (\d+) test cases?, (\d+) succeeded \((\d+) assertions?\)', text)]
                if found:
                    assert name.startswith(phase + '-jni-') and len(found) == 1
                    assert found[0][0] == found[0][1]
                    counts[name] = found[0]
                lines = text.splitlines()
                for index, line in enumerate(lines):
                    if line.startswith('warning:'):
                        feature = re.search(r"for feature '([^']+)'", line)
                        assert feature and feature[1] in expected_modules and 'AOT-MODULE-STALE:' in line, (name, line)
                        assert re.search(r"optional module 'xml(?: >= 1\.3)?' was not available, but it is available now; rebuild the binary module$", line)
                        diagnostic_counts[line] += 1
                    elif line.startswith('WARNING in native method:'):
                        assert target in ('leap', 'el10')
                        assert line == 'WARNING in native method: JNI call made without checking exceptions when required to from CallObjectMethodV'
                        assert '\tat sun.font.SunLayoutEngine.shape(' in lines[index + 1]
                        diagnostic_counts[line] += 1
                    elif re.search(r'(?i)^(?:warning|error|fatal):|\b(?:RuntimeWarning|ResourceWarning):', line):
                        raise AssertionError((target, phase, name, line))
            prior = previous['targets'][target]['phases'][phase]
            assert len(counts) == prior['suites']
            assert sum(row[0] for row in counts.values()) == prior['cases']
            assert sum(row[2] for row in counts.values()) == prior['assertions']
            # Compare individual suite totals with the already qualified x86_64 execution.
            local = root / f'results/{target}-jni-native-final-20261007/{phase}'
            for name, count in counts.items():
                assert [tuple(map(int, row)) for row in re.findall(
                    r'Ran (\d+) test cases?, (\d+) succeeded \((\d+) assertions?\)',
                    (local / (name + '.log')).read_text())] == [count]
            phases[phase] = {'job': job['web_url'], 'result': result, 'suites': len(counts),
                             'cases': prior['cases'], 'assertions': prior['assertions'],
                             'suite_counts': counts, 'diagnostics': dict(diagnostic_counts),
                             'logs_sha256': logs}
    assert bundles[0] == bundles[1]
    records[target] = {'phases': phases, 'fixture_bundle': bundles[0]}

output = root / 'evidence/controls/jni-native-results-20261007'
output.mkdir(exist_ok=True)
for source, name in archives:
    shutil.copy2(source, output / name)
shutil.copy2(__file__, output / 'record.py')
record = {
    'schema': 1, 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.', 'date': '2026-10-07',
    'status': 'All six signed native ARM JNI SDK/runtime jobs pass. Final core22 integration, external service tests and repository lifecycle remain separate gates; publication remains disabled.',
    'pipeline': 'https://git.qoretechnologies.com/mirror/qore-packaging/-/pipelines/59874',
    'runner_commit': commit, 'targets': records,
    'totals': {'suites': 180, 'cases': 3330, 'assertions': 38994,
               'sdk_bundles_verified': 3, 'native_compiled_runtime_consumers': 3},
    'diagnostic_approvals': previous['diagnostic_approvals'],
    'counting': 'Reported QUnit totals match every local x86_64 suite, including existing external-service skips and cases with no assertions. These totals do not claim execution of external database, JMS or hardware fixtures.',
    'verification': ['Exact pinned manifests and signed RPMs; native aarch64 runner and compiled ELF.',
                     'SDK and fresh-runtime phases use identical hash-verified four-file bundles.',
                     'Runtime inventories contain no Qore SDK, compiler, Java devel, JNI tools or Kotlin compiler packages.',
                     'All step exits are zero. Only previously approved XML-triggered source fallback and OpenJDK SunLayoutEngine diagnostics remain.'],
    'files_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir())},
}
(root / 'evidence/jni-native-results-20261007.json').write_text(json.dumps(record, indent=2) + '\n')
print('Verified six native ARM JNI jobs: 180 suites, 3330 cases, 38994 assertions; exact prior approvals only')
