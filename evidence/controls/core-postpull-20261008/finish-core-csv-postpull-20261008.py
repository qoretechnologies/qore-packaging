# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Apply and qualify the CSV diagnostic fix after the current qualification exits."""
from pathlib import Path
import hashlib
import json
import os
import re
import select
import subprocess

root = Path(__file__).resolve().parent.parent
repo = root.parent / 'qore'
out = root / 'results/core-csv-postpull-20261008'
out.mkdir()
prerequisite = root / 'results/core-postpull-20261008/status.json'
if not prerequisite.exists():
    pid = 419643
    assert b'work/qualify-core-postpull-20261008.py' in Path(f'/proc/{pid}/cmdline').read_bytes()
    descriptor = os.pidfd_open(pid)
    try:
        select.select([descriptor], [], [])
    finally:
        os.close(descriptor)
assert json.loads(prerequisite.read_text())['exit_code'] == 0
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip().startswith('9f94a962f')

source = repo / 'qlib/CsvUtil/CsvProfiler.qc'
text = source.read_text()
old = '            convert_encoding(binary_to_string(data, "UTF-8"), "UTF-16LE");'
assert text.count(old) == 1
text = text.replace(old, '''            # A different target encoding validates the bytes; tagging a string as UTF-8 does not.
            string validated = convert_encoding(binary_to_string(data, "UTF-8"), "UTF-16LE");
            @assert(validated.encoding() == "UTF-16LE");''')
source.write_text(text)
test = repo / 'examples/test/qlib/CsvUtil/CsvProfiler.qtest'
text = test.read_text()
text = text.replace('# -*- mode: qore; indent-tabs-mode: nil -*-',
    '# -*- mode: qore; indent-tabs-mode: nil -*-\n# Copyright 2026 Qore Technologies, s.r.o.\n# SPDX-License-Identifier: MIT')
for name in ('QUnit', 'FsUtil', 'DataProvider', 'CsvUtil'):
    text = text.replace('%requires ' + name + '\n', '%requires ../../../../qlib/' + name + '.qm\n')
marker = '        addTestCase("line endings", \\lineEndings());'
assert text.count(marker) == 1
text = text.replace(marker, '''        addTestCase("valid UTF-8 boundaries", \\validUtf8());
        addTestCase("invalid UTF-8 fallback and recovery", \\invalidUtf8());
''' + marker)
marker = '    lineEndings() {'
assert text.count(marker) == 1
text = text.replace(marker, '''    private validUtf8() {
        # Empty input and the endpoints of each UTF-8 length, including both sides of the surrogate gap.
        hash<TabularTextFormat> empty = CsvProfiler::sniffTextFormat(binary());
        assertEq("UTF-8", empty.encoding);
        assertFalse(empty.bom);
        foreach binary payload in ((<00>, <41>, <7f>, <c280>, <dfbf>, <e0a080>, <ed9fbf>, <ee8080>,
                <efbfbf>, <f0908080>, <f48fbfbf>)) {
            binary data = binary("value,count\\n\\\"") + payload + binary("\\\",1\\n");
            hash<TabularWorkbookGrid> grid = CsvProfiler::readGrid(data);
            assertEq("UTF-8", grid.text_format.encoding, payload.toString());
            assertFalse(grid.text_format.bom);
            assertEq(payload, binary(grid.sheets[0].rows[1][0]), "the original UTF-8 bytes survive CSV decoding");
            assertEq("1", grid.sheets[0].rows[1][1]);
        }
    }

    private invalidUtf8() {
        # Lone continuations, truncated sequences, overlong forms, surrogate code points and values above Unicode.
        foreach binary payload in ((<80>, <bf>, <c2>, <e0a0>, <f09080>, <c080>, <e08080>, <f0808080>,
                <eda080>, <edbfbf>, <f4908080>, <ff>, <c220>, <e028a1>, <f0288cbc>)) {
            hash<TabularTextFormat> format = CsvProfiler::sniffTextFormat(payload);
            assertEq("ISO-8859-1", format.encoding, payload.toString());
            assertFalse(format.bom);
            binary data = binary("value,count\\n\\\"") + payload + binary("\\\",1\\n");
            hash<TabularWorkbookGrid> grid = CsvProfiler::readGrid(data);
            assertEq("ISO-8859-1", grid.text_format.encoding);
            assertEq(payload, binary(convert_encoding(grid.sheets[0].rows[1][0], "ISO-8859-1")),
                "fallback preserves every byte as a Latin-1 character");
            assertEq("1", grid.sheets[0].rows[1][1]);
            assertEq("UTF-8", sniff("Město;Množství\\nPraha;5\\n").encoding,
                "a rejected sample does not affect the next valid sample");
        }
    }

''' + marker)
test.write_text(text)
test.chmod(test.stat().st_mode | 0o111)
guide = repo / 'examples/test/qore/misc/hash-lookup-native.rst'
text = guide.read_text()
old = 'and declaration arguments run the three groups separately; each group fails\nagainst the original implementation.'
new = ('and declaration arguments run the three groups separately. The conversion and\n'
       'declaration groups reproduce unset error outputs before this fix; the encoded\n'
       'group also guards the key-conversion behavior fixed in commit 9f94a962f.')
assert old in text
guide.write_text(text.replace(old, new))
paths = [str(p.relative_to(repo)) for p in (source, test, guide)]
pins = {p: hashlib.sha256((repo / p).read_bytes()).hexdigest() for p in paths}
(out / 'source.json').write_text(json.dumps(pins, indent=2) + '\n')
records = []
result = {'exit_code': 1}
try:
    for mode, folder in [('debug', 'build-debug'), ('release', 'build')]:
        build = repo / folder
        env = os.environ.copy()
        env.update(LD_LIBRARY_PATH=str(build), QORE_BINARY=str(build / 'qore'), QORE_BIN=str(build / 'qore'),
                   QORE_LIBDIR=str(build), QORE_MODULE_DIR=':'.join([str(repo / 'qlib'),
                   *[str(p) for p in (build / 'modules').iterdir() if p.is_dir()]]))
        directory = out / mode
        directory.mkdir()
        commands = [('build', ['cmake', '--build', str(build), '--target', 'CsvUtil-qmod', '-j2'])]
        commands += [(p.stem, [str(build / 'qore'), '-b', '--enable-debug', str(p), '-v'])
                     for p in sorted((repo / 'examples/test/qlib/CsvUtil').glob('*.qtest'))]
        for name, command in commands:
            with (directory / (name + '.log')).open('x') as stream:
                process = subprocess.run(command, cwd=repo, env=env, stdout=stream, stderr=subprocess.STDOUT)
            records.append({'mode': mode, 'name': name, 'exit_code': process.returncode, 'command': command})
            (out / 'steps.json').write_text(json.dumps(records, indent=2) + '\n')
            print(mode, name, process.returncode, flush=True)
            process.check_returncode()
            log = (directory / (name + '.log')).read_text()
            assert not re.search(r'(?im)(warning encountered|^warning:|^error:|CMake Warning|CMake Error)', log)
            if name != 'build':
                assert re.search(r'Ran \d+ test cases?, \d+ succeeded \(\d+ assertions\)', log), name
    assert pins == {p: hashlib.sha256((repo / p).read_bytes()).hexdigest() for p in paths}
    result['exit_code'] = 0
except BaseException as error:
    result['error'] = repr(error)
    raise
finally:
    (out / 'status.json').write_text(json.dumps(result, indent=2) + '\n')
