# Copyright 2026 Qore Technologies, s.r.o.
from pathlib import Path
import concurrent.futures, hashlib, json, os, select, subprocess, tarfile, sys

root = Path.cwd()
import importlib.util
_loader = importlib.util.spec_from_file_location('builder', root / 'tools/build-local.py')
builder = importlib.util.module_from_spec(_loader)
_loader.loader.exec_module(builder)
fds = []
for pid in map(int, sys.argv[1:]):
    try:
        fds.append(os.pidfd_open(pid))
    except ProcessLookupError:
        pass
while fds:
    ready, _, _ = select.select(fds, [], [])
    for fd in ready:
        fds.remove(fd)
        os.close(fd)

def qualify(target):
    build = root / f'results/{target}-jni-rpm-metadata-candidate-20261007'
    manifest = json.loads((build / 'build.json').read_text())
    assert manifest['exit_code'] == 0, target
    out = root / f'results/{target}-jni-metadata-candidate-installed-2-20261007'
    out.mkdir()
    fixtures = root / f'work/{target}-jni-metadata-candidate-installed-2-20261007'
    fixtures.mkdir()
    archive = root / 'work/jni-rpm-metadata-candidate-20261007/qore-jni-module-2.7.0.tar.xz'
    with tarfile.open(archive) as tar:
        members = [m for m in tar.getmembers() if
                   m.name.startswith('qore-jni-module-2.7.0/test/') or
                   m.name in ('qore-jni-module-2.7.0/debian/tests/fixtures.py', 'qore-jni-module-2.7.0/debian/tests/compiler')]
        tar.extractall(fixtures, members=members, filter='data')
    fixtures = fixtures / 'qore-jni-module-2.7.0'
    process_root = root / 'results' / {'fedora': 'fedora-final-9-process', 'leap': 'leap-wave-2-process', 'el10': 'el10-wave-1-process'}[target]
    process_build = json.loads((process_root / 'build.json').read_text())
    assert process_build['exit_code'] == 0
    process_rpms = []
    for rel, digest in process_build['artifacts'].items():
        p = process_root / rel
        if '/RPMS/' in rel and p.name.rsplit('-', 2)[0] == 'qore-process-module':
            with p.open('rb') as stream:
                assert hashlib.file_digest(stream, 'sha256').hexdigest() == digest
            process_rpms.append('/process/' + rel)
    assert len(process_rpms) == 1
    runtime_names = {'qore-jni-module', 'qore-jni-module-doc'}
    sdk_names = runtime_names | {'qore-jni-tools', 'qore-jni-kotlin'}
    packages = {}
    for rel, digest in manifest['artifacts'].items():
        p = build / rel
        with p.open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == digest
        name = p.name.rsplit('-', 2)[0]
        if '/RPMS/' in rel and name in sdk_names:
            packages[name] = '/rpms/' + rel
    assert packages.keys() == sdk_names
    record = {'build': manifest, 'steps': []}

    def save():
        (out / 'status.json').write_text(json.dumps(record, indent=2) + '\n')

    def run(name, command):
        with (out / (name + '.log')).open('w') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=1800)
        record['steps'].append({'name': name, 'command': command, 'exit_code': result.returncode})
        save()
        result.check_returncode()

    env_script = '''set -eu
unset QORE_MODULE_DIR QORE_MODULE_DIR_ONLY QORE_INCLUDE_DIR LD_LIBRARY_PATH LD_PRELOAD
unset CLASSPATH QORE_CLASSPATH QORE_JNI_CLASSPATH JAVA_TOOL_OPTIONS JDK_JAVA_OPTIONS _JAVA_OPTIONS
export QORE_MODULE_DIR=$(/usr/bin/qore --module-path)
export QORE_MODULE_DIR_ONLY=1
export QORE_JNI_CLASSPATH=/usr/share/qore/java/qore-jni.jar:/usr/share/qore/java/qore-jni-compiler.jar
export QORE_JNI_JVM_ARGS=-Xcheck:jni
export HOME="$PWD"
export AUTOPKGTEST_TMP="$PWD"
export XDG_CACHE_HOME="$PWD/.cache"
export KOTLIN_HOME=/usr/share/qore/java/kotlin
rpm -V qore-jni-module qore-jni-module-doc
'''
    try:
        runtime = json.loads((root / f'results/{target}-core-policy-21-installed-3.json').read_text())['runtime_image']
        for mode, base in [('sdk', manifest['image']), ('runtime', runtime)]:
            names = sdk_names if mode == 'sdk' else runtime_names
            container = f'qore-{target}-jni-metadata-candidate-installed-2-20261007-{mode}'
            installer = ('zypper --non-interactive --no-gpg-checks install --no-recommends' if target == 'leap'
                         else 'dnf -y --setopt=install_weak_deps=False install')
            install = 'set -eu\n' + installer + ' "$@"\nrpm -U --replacepkgs --includedocs /rpms/rpmbuild/RPMS/noarch/qore-jni-module-doc-*.rpm\n'
            run(mode + '-install', ['docker', 'run', '--init', '--name', container, '-v', str(build)+':/rpms:ro', '-v', str(process_root)+':/process:ro',
                base, 'sh', '-c', install, 'install', *[packages[n] for n in sorted(names)], *(process_rpms if mode == 'sdk' else [])])
            image = subprocess.check_output(['docker', 'commit', container], text=True).strip()
            record[mode + '_image'] = image
            save()
            subprocess.run(['docker', 'rm', container], check=True, stdout=subprocess.DEVNULL)
            if mode == 'sdk':
                script = env_script + '''python3 -B -W error debian/tests/fixtures.py
qkotlinc -q -jvm-target 21 -d test/kotlin-test.jar test/KotlinQoreApiTest.kt test/KotlinTestClass.kt
for suite in test/*.qtest; do
  case "$suite" in test/jms.qtest) continue ;; esac
  timeout 600 qore -b --enable-debug -l jni "$suite" -v
done
python3 -B -W error test/test-headless-class-import.py --qore /usr/bin/qore --module /usr/lib64/qore-modules/jni-api-2.0.qmod
cat > consumer.qr <<'QORE'
%requires jni
%requires ExcelDataProvider
%requires OdsDataProvider
%requires DataProvider
%module-cmd(jni) import java.lang.StringBuilder
StringBuilder text();
text.append("packaged Java");
if (text.toString() != "packaged Java" || DataProvider::getFactory("excelread").getInfo().name != "excelread"
        || DataProvider::getFactory("odsread").getInfo().name != "odsread") {
    throw "PACKAGE-TEST-ERROR", "Installed JNI bridge or provider failed";
}
printf("installed JNI consumer passed\\n");
QORE
qcc -o consumer consumer.qr
./consumer
sh debian/tests/compiler
qjavac -h
qjava2jar -h
qjava-migrate-imports -h
qkotlinc -h
'''
            else:
                script = env_script + '''for package in qore-devel qore-jni-tools qore-jni-kotlin gcc gcc-c++; do
  if rpm -q "$package"; then exit 1; fi
done
for suite in test/*DataProvider.qtest test/jni-reference-safety.qtest test/jni-exception-location.qtest; do
  timeout 600 qore -b --enable-debug -l jni "$suite" -v
done
QORE_JNI_JVM_ARGS="-Xcheck:jni -Djava.awt.headless=true" qore -b --enable-debug -l jni test/headless-class-import.qr
./consumer
'''
            with builder.build_network('docker', True) as (network, info):
                record.setdefault('test_networks', {})[mode] = info
                run(mode + '-tests', ['docker', 'run', '--rm', '--init', '--network', network, '--user',
                    f'{os.getuid()}:{os.getgid()}', '-v', str(fixtures)+':/fixture', '-w', '/fixture',
                    image, 'sh', '-c', script])
        record['exit_code'] = 0
    except BaseException as error:
        record.update(exit_code=1, error=repr(error))
        raise
    finally:
        save()

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    list(pool.map(qualify, ['fedora', 'leap', 'el10']))
