# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import concurrent.futures
import json
import subprocess

root = Path.cwd()
output = root / 'results/jni-manifest-controls-20261007'
output.mkdir()


def check(target):
    image = json.loads((root / f'results/{target}-jni-metadata-candidate-installed-2-20261007/status.json').read_text())['sdk_image']
    script = '''set -eu
mkdir /tmp/control
cd /tmp/control
test ! -e /usr/share/qore-modules/OdsDataProvider/jar/jena-iri-3.16.0.jar
test ! -e /usr/share/qore-modules/OdsDataProvider/jar/xml-apis.jar
javac -Werror -cp '/usr/share/qore-modules/OdsDataProvider/jar/*' -d . /control/JniManifestControl.java
java -ea -Djava.awt.headless=true -cp '.:/usr/share/qore-modules/OdsDataProvider/jar/*' JniManifestControl
'''
    command = ['docker', 'run', '--rm', '--init', '--network', 'none', '-v',
               str(root / 'work/JniManifestControl.java') + ':/control/JniManifestControl.java:ro',
               image, 'sh', '-c', script]
    with (output / (target + '.log')).open('x') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=120)
    return {'target': target, 'command': command, 'exit_code': result.returncode}


with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    results = list(pool.map(check, ['fedora', 'leap', 'el10']))
(output / 'status.json').write_text(json.dumps(results, indent=2) + '\n')
print({row['target']: row['exit_code'] for row in results})
assert all(row['exit_code'] == 0 for row in results)
