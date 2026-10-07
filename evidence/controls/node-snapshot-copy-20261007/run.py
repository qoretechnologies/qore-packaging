# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json, shlex, subprocess

root = Path('/work/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1')
out = Path('/control')
receipt = next((root / 'out/Release/.deps').rglob('raw-machine-assembler.o.d'))
base_args = shlex.split(receipt.read_text().splitlines()[0].split(' := ', 1)[1])
base_args = [x for x in base_args if not x.startswith('-flto') and x != '-ffat-lto-objects']
records = []
def run(name, args, expected=0):
    with (out / (name + '.log')).open('w') as log:
        result = subprocess.run(args, cwd=root/'out', stdout=log, stderr=subprocess.STDOUT)
    records.append(dict(name=name, command=args, exit_code=result.returncode, expected=expected))
    (out / 'status.json').write_text(json.dumps(records, indent=2) + '\n')
    if expected == 'fatal':
        assert result.returncode in (-4, -5, -6), (name, result.returncode)
        assert 'Check failed:' in (out/(name+'.log')).read_text()
    else:
        assert result.returncode == expected, (name, result.returncode)

def compile(variant, name, source):
    args = list(base_args)
    args[2:4] = [f'/control/{variant}-{name}.o', str(source)]
    args[args.index('-MF') + 1] = f'/control/{variant}-{name}.d'
    args += ['-fno-lto', '-DPREFIX_FILE="' + variant + '-prefix.inc"']
    if variant == 'fixed':
        args[1:1] = ['-I/control/proposed']
    run(variant + '-' + name + '-compile', args)

archive_root = root / 'out/Release/obj.target/tools/v8_gypfiles'
archives = [str(archive_root / n) for n in ('libv8_compiler.a', 'libv8_base_without_compiler.a',
    'libv8_snapshot.a', 'libv8_libbase.a', 'libabseil.a', 'libv8_zlib.a', 'libhighway.a', 'libsimdutf.a')]
compile('original','control',out/'control.cc')
run('link',['g++','-fno-lto','-pthread','-Wl,--gc-sections','/control/original-control.o','-Wl,--start-group',*archives,'-Wl,--end-group','-lz','-licui18n','-licuuc','-ldl','-lrt','-o','/control/control'])
run('normal',['/control/control'])
run('memory',['valgrind','--error-exitcode=99','--leak-check=full','--show-leak-kinds=all','--errors-for-leak-kinds=all','--log-file=/control/valgrind.log','/control/control'])
print('SnapshotTable native checks passed normally and under Valgrind.')
