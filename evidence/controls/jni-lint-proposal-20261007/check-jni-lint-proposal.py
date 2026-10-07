# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json
import re
import subprocess
import urllib.request
import xml.etree.ElementTree as ET

root = Path.cwd()
out = root / 'results/jni-lint-proposal-2-20261007'
out.mkdir()
patterns = []
proposal = root / 'work/jni-proposed-rpmlintrc'
exec(compile(proposal.read_text(), str(proposal), 'exec'),
     {'addFilter': lambda value: patterns.append(re.compile(value))})
assert len(patterns) == 1
checked = 0
for package in ('tools', 'kotlin'):
    message = f'qore-jni-{package}.noarch: E: devel-dependency java-21-openjdk-devel'
    assert patterns[0].search(message)
    checked += 1
    for modified in (message.replace(package + '.', 'other.'),
                     message.replace('noarch', 'x86_64'),
                     message.replace('21', '25'),
                     message.replace('openjdk', 'other'),
                     message.replace('E:', 'W:'),
                     message.replace('devel-dependency', 'missing-dependency'),
                     'other: ' + message, message + '.unexpected'):
        assert not patterns[0].search(modified), modified
        checked += 1
original_lint = (root / 'results/jni-rpm-metadata-candidate-lint-20261007.log').read_text()
messages = [line for line in original_lint.splitlines() if re.search(r': [EW]: ', line)]
matched = [line for line in messages if patterns[0].search(line)]
assert len(matched) == 2 and len(messages) == 15
public = []
listing = ET.parse(root / 'results/jni-metadata-source-listing-20261007.xml').getroot()
for name in ('qore-jni-module-2.7.0.tar.xz', 'qore-jni-vendor-2.7.0.tar.xz'):
    url = 'https://api.opensuse.org/public/source/home:davidnichols:qore:testing/qore-jni-module/' + name
    with urllib.request.urlopen(urllib.request.Request(url, method='HEAD'), timeout=60) as response:
        assert response.status == 200
        entry = next(item for item in listing if item.get('name') == name)
        length = response.headers.get('Content-Length')
        if length is not None:
            assert int(length) == int(entry.get('size'))
        public.append({'url': url, 'status': response.status, 'listing_bytes': int(entry.get('size')),
                       'response_length': length, 'listing_md5': entry.get('md5')})
build = root / 'results/leap-jni-rpm-metadata-candidate-20261007'
rpms = [p for p in sorted((build / 'rpmbuild').glob('RPMS/*/*.rpm')) if 'debug' not in p.name]
rpms += sorted((build / 'rpmbuild/SRPMS').glob('*.src.rpm'))
assert len(rpms) == 5
command = ['docker', 'run', '--rm', '--init', '--network', 'none', '-v', str(build) + ':/rpms:ro',
           '-v', str(proposal) + ':/control/jni-rpmlintrc:ro',
           'qore-rpm-keep:leap-debugedit-lint-1', 'rpmlint', '-r', '/control/jni-rpmlintrc',
           *[str(Path('/rpms') / p.relative_to(build)) for p in rpms]]
with (out / 'lint.log').open('x') as log:
    lint = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=600)
text = (out / 'lint.log').read_text()
assert '0 errors, 13 warnings' in text, text
assert sorted(line for line in text.splitlines() if re.search(r': [EW]: ', line)) == sorted(
    line for line in messages if line not in matched)
(out / 'status.json').write_text(json.dumps({'filter_checks': checked, 'filter_matched': matched,
    'other_diagnostics_preserved': len(messages) - len(matched), 'public_sources': public,
    'lint_command': command, 'lint_exit_code': lint.returncode,
    'status': 'Proposal only; no filter registered in the module recipe.'}, indent=2) + '\n')
print('Exact compiler-package filter passes', checked, 'scope checks; all 13 other diagnostics remain visible')
