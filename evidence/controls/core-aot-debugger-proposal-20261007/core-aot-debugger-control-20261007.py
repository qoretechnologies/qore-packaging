# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Paired checks of the optional index and indexed DWARF in real core modules."""
from pathlib import Path
import argparse
import gzip
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--module')
parser.add_argument('--old-debugedit', action='store_true')
args = parser.parse_args()
args.output.mkdir(exist_ok=True)
loader = importlib.util.spec_from_file_location('preserve', args.source / 'rpm/preserve-aot-metadata.py')
preserve = importlib.util.module_from_spec(loader)
loader.loader.exec_module(preserve)
modules = sorted((args.source / 'build/qlib-qmod').rglob('*.qmod'))
assert len(modules) > 300
if args.module:
    modules = [path for path in modules if path.name == args.module + '.qmod']
    assert len(modules) == 1


def run(command):
    return subprocess.run(command, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=120)


def checked(command):
    result = run(command)
    assert result.returncode == 0 and not result.stderr, (command, result.returncode, result.stdout, result.stderr)
    return result.stdout


def sections(path):
    table = checked(['readelf', '-SW', str(path)])
    answer = {}
    with path.open('rb') as stream:
        for line in table.splitlines():
            match = re.match(r'\s*\[\s*\d+\]\s+(\..+)$', line)
            if not match:
                continue
            fields = match[1].split()
            assert len(fields) in (9, 10), line
            name, kind = fields[:2]
            size = int(fields[4], 16)
            flags = fields[6] if len(fields) == 10 else ''
            if kind == 'NOBITS':
                answer[name] = {'kind': kind, 'size': size, 'flags': flags}
            else:
                stream.seek(int(fields[3], 16))
                data = stream.read(size)
                assert len(data) == size
                answer[name] = {'kind': kind, 'size': size, 'flags': flags,
                                'sha256': hashlib.sha256(data).hexdigest()}
    assert '.debug_info' in answer and '.text' in answer
    return answer


def save(name, result):
    (args.output / name).write_bytes(gzip.compress((result.stdout + result.stderr).encode(), mtime=0))


records = []
for module in modules:
    label = module.name.removesuffix('.qmod')
    original_sections = sections(module)
    assert '.debug_names' in original_sections, module
    original_command = ['gdb', '-q', '-nx', '-nh', '-batch', '-ex', 'set debuginfod enabled off',
                        '-ex', 'info functions', str(module)]
    original = run(original_command)
    assert original.returncode == 0, (module, original)
    save(label + '-original.log.gz', original)
    original_text = original.stdout + original.stderr
    assert 'warning: .debug_names not created by gdb; ignoring' in original_text, (module, original_text[-1500:])
    # The retained build tree already contains the RPM debug-prefix mapping.
    prefixes = set(re.findall(r'^File (.+)/qlib/', original.stdout, re.M))
    assert len(prefixes) <= 1, (module, prefixes)
    symbols = checked(['nm', '-a', str(module)])
    metadata_only = not prefixes
    if metadata_only:
        assert not re.search(r'(?m)^[0-9a-f]+\s+[Tt]\s+(?:_qaot_|__const_init)', symbols), module
    debug_base = prefixes.pop() if prefixes else str(args.source)
    with tempfile.TemporaryDirectory(prefix='core-aot-debugger-', dir='/tmp') as temporary:
        temp = Path(temporary)
        fixed = temp / module.name
        shutil.copy2(module, fixed)
        trailers = preserve.read_trailers(module)
        assert trailers, module
        preserve.preserve(temp, ['objcopy', '--remove-section=.debug_names', str(fixed)])
        assert preserve.read_trailers(fixed) == trailers
        fixed_sections = sections(fixed)
        assert '.debug_names' not in fixed_sections
        retained = {name: entry for name, entry in original_sections.items()
                    if name != '.debug_names' and (name.startswith('.debug_') or 'A' in entry['flags'])}
        assert all(fixed_sections[name] == entry for name, entry in retained.items()), module
        assert symbols == checked(['nm', '-a', str(fixed)]), module
        sources = temp / 'sources.list'
        destination = '/usr/src/debug/qore-aot-control'
        edit = run([sys.executable, str(args.source / 'rpm/preserve-aot-metadata.py'), str(temp),
                    'debugedit', '-b', debug_base, '-d', destination, '-i', '-l', str(sources), str(fixed)])
        if args.old_debugedit:
            # Version 5.0 reports the unsupported form but returns success.
            assert edit.returncode == 0 and 'Unknown DWARF DW_FORM_0x25' in edit.stderr, edit
            save(label + '-old-debugedit.log.gz', edit)
            records.append({'module': label, 'negative_exit': edit.returncode, 'diagnostic': edit.stderr,
                            'index_removed': True, 'all_other_dwarf_and_allocated_sections_preserved': retained,
                            'metadata_preserved': True})
            continue
        assert edit.returncode == 0 and not edit.stderr, (module, edit)
        # The real RPM metadata wrapper restores trailers after debugedit.
        assert preserve.read_trailers(fixed) == trailers, module
        options = ['gdb', '-q', '-nx', '-nh', '-batch', '-ex', 'set debuginfod enabled off',
                   '-ex', 'set substitute-path ' + destination + ' ' + str(args.source),
                   '-ex', 'info functions']
        initial = run([*options, str(fixed)])
        assert initial.returncode == 0 and not initial.stderr, (module, initial)
        source = None
        location = None
        for line in initial.stdout.splitlines():
            if line.startswith('File '):
                source = line[5:].removesuffix(':')
            match = re.match(r'(\d+):\s+', line)
            if match and source and source.endswith(('.qm', '.qc')):
                location = source + ':' + match[1]
                break
        if metadata_only:
            assert location is None
            commands = ['-ex', 'break __qore_aot_module_init_impl', '-ex', 'info breakpoints']
        else:
            assert location and location.startswith(destination + '/qlib/'), (module, location)
            commands = ['-ex', 'break ' + location, '-ex', 'info breakpoints', '-ex', 'list ' + location]
        final = run([*options, *commands, str(fixed)])
        final_text = final.stdout + final.stderr
        save(label + '-fixed.log.gz', final)
        assert final.returncode == 0 and not re.search(
            r'warning:|No source file|No line |No symbol|No such file', final_text), (module, final_text[-1500:])
        assert 'Breakpoint 1 at ' in final_text and 'breakpoint     keep y' in final_text, (module, final_text)
        if not metadata_only:
            assert any(re.match(r'\d+\s+\S', line) for line in final_text.splitlines()), (module, final_text)
        functions = lambda text: [line for line in text.splitlines() if re.match(r'\d+:\s+', line)]
        assert functions(original.stdout) == functions(final.stdout), module
        assert bool(functions(final.stdout)) != metadata_only, module
        records.append({'module': label, 'original_sha256': hashlib.sha256(module.read_bytes()).hexdigest(),
                        'all_other_dwarf_and_allocated_sections_preserved': retained,
                        'symbols_unchanged': True, 'metadata_sha256': hashlib.sha256(trailers).hexdigest(),
                        'functions': len(functions(final.stdout)), 'breakpoint_source': location,
                        'metadata_only': metadata_only,
                        'debugedit_stderr': '', 'gdb_warning_removed': True})
        print('PASS:', label, 'functions', records[-1]['functions'], flush=True)
    (args.output / 'checks.json').write_text(json.dumps(records, indent=2) + '\n')
(args.output / 'checks.json').write_text(json.dumps(records, indent=2) + '\n')
print('PASS:', len(records), 'core module debugger controls', flush=True)
