#!/usr/bin/env python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Transfer built JNI test fixtures between isolated native SDK/runtime jobs."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


FIXTURES = set(json.loads((Path(__file__).resolve().parents[1]
                          / 'qualification/jni-fixtures.json').read_text()))
ARTIFACTS = ('test/qore-jni-test.jar', 'test/opcua-test-server.jar',
             'test/kotlin-test.jar', 'jni-smoke')


def manifest_digest(manifest):
    return hashlib.sha256(json.dumps(manifest, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def regular_file(root, relative):
    path = root / relative
    if (not path.is_file() or path.is_symlink() or root.is_symlink()
            or any(parent.is_symlink() for parent in path.parents if parent.is_relative_to(root))
            or not path.resolve().is_relative_to(root.resolve())):
        raise ValueError('Fixture must be a regular file inside its bundle: ' + relative)
    return path


def export_bundle(directory, output, manifest):
    """Only publish a manifest after every reviewed artifact has been copied."""
    directory, output = Path(directory), Path(output)
    files = {name: regular_file(directory, name) for name in ARTIFACTS}
    output.mkdir(parents=True, exist_ok=False)
    record = {'schema': 1, 'arch': manifest['arch'],
              'qualification_manifest_sha256': manifest_digest(manifest), 'files': {}}
    for name, source in files.items():
        destination = output / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        destination.chmod(0o755 if name == 'jni-smoke' else 0o644)
        record['files'][name] = hashlib.sha256(destination.read_bytes()).hexdigest()
    (output / 'bundle.json').write_text(json.dumps(record, indent=2) + '\n')
    return record


def verify_bundle(bundle, manifest):
    bundle = Path(bundle)
    metadata = regular_file(bundle, 'bundle.json')
    record = json.loads(metadata.read_text())
    if (not isinstance(record, dict) or record.get('schema') != 1 or record.get('arch') != manifest['arch']
            or record.get('qualification_manifest_sha256') != manifest_digest(manifest)
            or not isinstance(record.get('files'), dict)
            or set(record['files']) != set(ARTIFACTS)):
        raise ValueError('JNI fixture bundle does not match the qualification manifest')
    for name in ARTIFACTS:
        source = regular_file(bundle, name)
        if hashlib.sha256(source.read_bytes()).hexdigest() != record['files'][name]:
            raise ValueError('JNI fixture digest mismatch: ' + name)
    return record


def import_bundle(bundle, directory, manifest):
    """Verify the complete bundle before copying executable test artifacts."""
    verify_bundle(bundle, manifest)
    for name in ARTIFACTS:
        destination = Path(directory) / name
        if (destination.exists() or destination.is_symlink()
                or not destination.resolve().is_relative_to(Path(directory).resolve())
                or Path(directory).is_symlink()
                or any(parent.is_symlink() for parent in destination.parents
                       if parent.is_relative_to(Path(directory)))):
            raise ValueError('Refusing to replace an existing JNI fixture: ' + name)
    for name in ARTIFACTS:
        destination = Path(directory) / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(bundle) / name, destination)
        destination.chmod(0o755 if name == 'jni-smoke' else 0o644)


def runtime_layout(directory):
    """Match first-party test classpaths to the installed provider JARs."""
    directory = Path(directory)
    for source in sorted(Path('/usr/share/qore-modules').glob('*/jar')):
        target = directory / 'qlib' / source.parent.name / 'jar'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(source, target_is_directory=True)


def commands(phase, directory, binary):
    directory = Path(directory)
    environment = ['env']
    for variable in ('CLASSPATH', 'QORE_CLASSPATH', 'QORE_JNI_CLASSPATH',
                     'JAVA_TOOL_OPTIONS', 'JDK_JAVA_OPTIONS', '_JAVA_OPTIONS'):
        environment += ['-u', variable]
    environment += ['HOME=' + str(directory), 'XDG_CACHE_HOME=' + str(directory / '.cache'),
                    'QORE_JNI_CLASSPATH=/usr/share/qore/java/qore-jni.jar:'
                    '/usr/share/qore/java/qore-jni-compiler.jar',
                    'QORE_JNI_JVM_ARGS=-Xcheck:jni',
                    'KOTLIN_HOME=/usr/share/qore/java/kotlin']
    result = []
    if phase == 'sdk':
        if binary is None or not Path(binary).is_absolute():
            raise ValueError('JNI SDK checks require the installed binary module path')
        result += [('build-java-fixtures', ['python3', '-B', '-W', 'error',
                                           str(directory / 'debian/tests/fixtures.py')]),
                   ('build-kotlin-fixture', ['qkotlinc', '-q', '-jvm-target', '21',
                                            '-d', 'test/kotlin-test.jar',
                                            'test/KotlinQoreApiTest.kt', 'test/KotlinTestClass.kt'])]
    elif phase == 'runtime':
        result.append(('fixture-layout', ['python3', '-B', '-W', 'error',
                                         str(Path(__file__).resolve()), str(directory)]))
    else:
        raise ValueError('Unsupported JNI phase')
    suites = sorted(name for name in FIXTURES if name.endswith('.qtest'))
    for path in suites:
        if phase == 'runtime' and not (path.endswith('DataProvider.qtest')
                or path in ('test/jni-reference-safety.qtest', 'test/jni-exception-location.qtest')):
            continue
        result.append((Path(path).stem, ['timeout', '600', 'qore', '-b', '--enable-debug',
                                        '-l', 'jni', str(directory / path), '-v']))
    if phase == 'sdk':
        result.extend([
            ('headless', ['python3', '-B', '-W', 'error', str(directory / 'test/test-headless-class-import.py'),
                          '--qore', '/usr/bin/qore', '--module', str(binary)]),
            ('compiler', ['/bin/sh', str(directory / 'debian/tests/compiler')]),
        ])
    else:
        result.extend([
            ('headless', ['env', 'QORE_JNI_JVM_ARGS=-Xcheck:jni -Djava.awt.headless=true',
                          'qore', '-b', '--enable-debug', '-l', 'jni',
                          str(directory / 'test/headless-class-import.qr')]),
            ('compiled-consumer', [str(directory / 'jni-smoke')]),
        ])
    return [(name, environment + command) for name, command in result]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    runtime_layout(args.directory)
