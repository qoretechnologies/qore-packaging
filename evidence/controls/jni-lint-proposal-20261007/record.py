# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip
import hashlib
import json
import re
import shutil
import subprocess
import zipfile

root = Path.cwd()
out = root / 'evidence/controls/jni-lint-proposal-20261007'
out.mkdir(exist_ok=True)
controls = root / 'results/jni-manifest-controls-20261007'
records = json.loads((controls / 'status.json').read_text())
assert {row['target']: row['exit_code'] for row in records} == dict.fromkeys(['fedora', 'leap', 'el10'], 0)
for target in ('fedora', 'leap', 'el10'):
    text = (controls / (target + '.log')).read_text()
    assert 'PASS: 67 private JAR and JDK XML API checks' in text
    assert not re.search(r'warning|error|exception', text, re.I)
    shutil.copy2(controls / (target + '.log'), out / (target + '-manifest.log'))
proposal = json.loads((root / 'results/jni-lint-proposal-2-20261007/status.json').read_text())
assert proposal['filter_checks'] == 18 and proposal['other_diagnostics_preserved'] == 13
image = json.loads((root / 'results/leap-jni-metadata-candidate-installed-2-20261007/status.json').read_text())['sdk_image']
script = '''import hashlib,json,pathlib,zipfile
root=pathlib.Path('/usr/share/qore-modules/OdsDataProvider/jar')
paths=[root/'java-rdfa-1.0.0-BETA1.jar',root/'serializer-2.7.3.jar']
paths += [pathlib.Path('/usr/share/qore/java/kotlin/lib')/n for n in ('kotlin-compiler.jar','kotlin-runner.jar')]
records=[]
for path in paths:
 with zipfile.ZipFile(path) as z:
  manifest=z.read('META-INF/MANIFEST.MF').decode().replace('\\r\\n','\\n').replace('\\n ','')
  entry=next(line.split(': ',1)[1] for line in manifest.splitlines() if line.startswith('Class-Path: '))
  targets={name:(path.parent/name).is_file() for name in entry.split()}
  if 'kotlin' in str(path):assert all(targets.values()),targets
  records.append({'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'manifest_class_path':targets})
print(json.dumps(records,indent=2))
'''
command = ['docker', 'run', '--rm', '--network', 'none', image, 'python3', '-c', script]
manifests = json.loads(subprocess.check_output(command, text=True))
(out / 'installed-manifests.json').write_text(json.dumps(manifests, indent=2) + '\n')
sources = next((root / 'results/leap-jni-rpm-metadata-candidate-20261007/rpmbuild/BUILD').glob('*/*/vendor/sources'))
with zipfile.ZipFile(next(sources.glob('odfdom*sources.jar'))) as jar:
    callsites = {}
    for name in jar.namelist():
        if not name.endswith('.java'):
            continue
        data = jar.read(name).decode()
        assert 'net.rootdev.javardfa.ParserFactory' not in data, name
        if 'net.rootdev' in data:
            callsites[name] = {'sha256': hashlib.sha256(jar.read(name)).hexdigest(),
                              'references': [line for line in data.splitlines() if 'net.rootdev' in line]}
assert len(callsites) == 6
(out / 'odf-rdfa-source-review.json').write_text(json.dumps(callsites, indent=2) + '\n')
for source, name in [
        (root / 'work/JniManifestControl.java', 'JniManifestControl.java'),
        (root / 'work/check-jni-manifests-20261007.py', 'check-jni-manifests.py'),
        (root / 'work/check-jni-lint-proposal-20261007.py', 'check-jni-lint-proposal.py'),
        (root / 'work/jni-proposed-rpmlintrc', 'proposed-rpmlintrc'),
        (root / 'results/jni-lint-proposal-2-20261007/lint.log', 'lint.log'),
        (root / 'results/jni-lint-proposal-2-20261007/status.json', 'lint-status.json'),
        (root / 'results/jni-source-url-recipe-tests-20261007.json', 'source-url-recipe-tests.json'),
        (root / 'results/jni-layout-helper-tests-2-20261007.log', 'helper-tests.log'),
        (root / 'work/jni-rpm-integration-1/qore-jni-module.spec', 'proposed-spec'),
        (controls / 'status.json', 'manifest-status.json'),
        (Path(__file__), 'record.py')]:
    shutil.copy2(source, out / name)
lint = (root / 'results/jni-rpm-metadata-candidate-lint-20261007.log').read_text()
messages = [line for line in lint.splitlines() if re.search(r': [EW]: ', line)]
scopes = {
    'compiler_dependencies': [line for line in messages if 'devel-dependency' in line],
    'license_and_catalog_metadata': [line for line in messages if 'invalid-license' in line or 'hidden-file-or-dir' in line],
    'vendor_manifests': [line for line in messages if 'class-path-in-manifest' in line]
}
assert {key: len(value) for key, value in scopes.items()} == {
    'compiler_dependencies': 2, 'license_and_catalog_metadata': 7, 'vendor_manifests': 4}
record = {
    'schema': 1, 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.', 'date': '2026-10-07',
    'status': 'Concrete tested lint exception proposal; no new exception approved and no filter registered.',
    'scopes': scopes,
    'proposal': {
        'compiler_dependencies': 'One anchored filter accepts only the two exact java-21-openjdk-devel errors for qore-jni-tools.noarch and qore-jni-kotlin.noarch. They deliver compilers and need the JDK. The installed compiler and qjava2jar tests already pass on all three distributions.',
        'license_and_catalog_metadata': 'Retain five exact LicenseRef vocabulary warnings with the complete pinned upstream notices, plus two exact hidden catalog ownership-directory messages. No warning filter or behavior change.',
        'vendor_manifests': 'Retain the four exact Class-Path warnings. All Kotlin targets exist. Qore declares its ODF classpath explicitly, including Jena 4.10; XML APIs are supplied by java.xml. The ODF source uses its SAX RDFa parser and never references the optional java-rdfa HTML ParserFactory. No JAR rewriting, dependency removal or warning filter.'
    },
    'validation': {'manifest_controls_per_distribution': 67, 'manifest_controls_total': 201,
        'manifest_distributions': ['fedora', 'leap', 'el10'], 'filter_scope_checks': 18,
        'unrelated_lint_diagnostics_preserved': 13, 'helper_tests': 24,
        'candidate_package_evidence': 'evidence/jni-rpm-metadata-candidate-20261007.json',
        'source_urls': proposal['public_sources']},
    'limits': ['The Java controls cover Qore ODF RDFa metadata and XML serialization, not java-rdfa standalone HTML command-line use, which is not an exposed Qore module feature.',
        'Installed JAR byte identity, Kotlin compiler/runner execution, and complete notice provenance are covered by the candidate package evidence.',
        'The first lint harness used obsolete rpmlint -f. It exited before linting; the recorded complete run uses rpmlint 2.7 -r.',
        'Two source-URL warnings in the existing RPM disappear only after a new canonical source package is generated; all three distributions parse the new source URLs without changing build/install/check commands.',
        'Canonical committed-source builds, native ARM and final core22 integration remain required.'],
    'approval': {name: {'status': 'requested'} for name in scopes},
    'files_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}
}
(root / 'evidence/jni-lint-proposal-20261007.json').write_text(json.dumps(record, indent=2) + '\n')
print('JNI lint proposal recorded: 201 functional checks, 18 filter checks, exact scopes preserved')
