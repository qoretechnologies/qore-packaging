#!/usr/bin/python3
# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Test the package's native Wasm metadata and version-matched deoptimization scripts."""
import argparse
import importlib.util
from pathlib import Path
import resource
import re
import shlex
import subprocess


def extract_prefix(source):
    signature = 'base::OwnedVector<uint8_t> CodeGenerator::GenerateWasmDeoptimizationData() {'
    ending = '  base::Vector<const uint8_t> frame_translations ='
    if source.count(signature) != 1:
        raise ValueError('Expected one Wasm metadata generator')
    start = source.index(signature)
    end = source.find(ending, start)
    if end < 0:
        raise ValueError('Missing metadata serialization boundary')
    body = source[start:end]
    for invariant in ('CHECK_EQ(result_, kSuccess);',
                      'CHECK_LE(deoptimization_exits_.size(),',
                      'CHECK_EQ(i, deoptimization_exit->deoptimization_id());'):
        if len(re.findall(r'(?m)^\s*' + re.escape(invariant), body)) != 1:
            raise ValueError('Missing metadata invariant: ' + invariant)
    return body.replace(signature,
        'base::OwnedVector<wasm::WasmDeoptEntry> GeneratorAdapter::Generate() {') + '  return deopt_entries;\n}\n'


def test_flags(source):
    flags = []
    for line in source.splitlines():
        if line.startswith('// Flags:'):
            flags.extend(shlex.split(line.split(':', 1)[1]))
    allowed = re.compile(r'--(?:(?:no-)?wasm-[a-z0-9-]+|liftoff|no-jit-fuzzing|'
                         r'allow-natives-syntax|expose-gc|no-predictable)(?:=[0-9]+)?')
    if not flags or any(not allowed.fullmatch(value) for value in flags):
        raise ValueError('Invalid upstream V8 test flags')
    return flags


def require_rejection(mode, result):
    expected = {
        'failed-generation': 'result_ == kSuccess',
        'excess-count': 'deoptimization_exits_.size() <=',
        'duplicate-id': 'i == deoptimization_exit->deoptimization_id()',
        'negative-count': 'eager_deopt_count >= 0',
        'mismatched-count': 'deopt_entries.size() == static_cast<size_t>(eager_deopt_count)',
        'out-of-range': 'deopt_index < base_data_.entry_count',
    }
    if result.returncode not in (-4, -5, -6) or 'Check failed: ' + expected[mode] not in result.stderr:
        raise AssertionError((mode, result.returncode, result.stdout, result.stderr))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--test-source', type=Path, required=True)
    parser.add_argument('--native-helper', type=Path, required=True)
    parser.add_argument('--tests', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root, tests, output = args.source.resolve(), args.tests.resolve(), args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    prefix = output.with_suffix('.inc')
    prefix.write_text(extract_prefix((root/'deps/v8/src/compiler/backend/code-generator.cc').read_text()))
    loader = importlib.util.spec_from_file_location('native_control', args.native_helper)
    native = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(native)
    receipts = list((root/'out/Release/.deps').rglob('raw-machine-assembler.o.d'))
    if len(receipts) != 1:
        raise ValueError('Expected exactly one native V8 compiler receipt')
    command = native.compile_command(receipts[0].read_text(), args.test_source.resolve(), output.with_suffix('.o'))
    command.append('-DPREFIX_FILE="' + str(prefix) + '"')
    subprocess.run(command, cwd=root/'out', check=True)
    base = root/'out/Release/obj.target/tools/v8_gypfiles'
    archives = [base/n for n in ('libv8_compiler.a', 'libv8_base_without_compiler.a',
        'libv8_snapshot.a', 'libv8_libbase.a', 'libabseil.a', 'libv8_zlib.a',
        'libhighway.a', 'libsimdutf.a')]
    subprocess.run([command[0], '-fno-lto', '-pthread', '-Wl,--gc-sections', str(output.with_suffix('.o')),
        '-Wl,--start-group', *map(str, archives), '-Wl,--end-group', '-lz', '-licui18n', '-licuuc',
        '-ldl', '-lrt', '-o', str(output)], cwd=root/'out', check=True)
    subprocess.run([str(output), 'positive'], check=True)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    for mode in ('failed-generation', 'excess-count', 'duplicate-id', 'negative-count',
                 'mismatched-count', 'out-of-range'):
        result = subprocess.run([str(output), mode], capture_output=True, text=True)
        output.with_name(output.name + '-' + mode + '.log').write_text(result.stdout + result.stderr)
        require_rejection(mode, result)
        print('Invalid Wasm metadata rejected:', mode, flush=True)
    scripts = sorted((tests/'test/mjsunit/wasm/deopt').glob('*.js'))
    if len(scripts) != 31:
        raise ValueError('Expected all 31 version-matched Wasm deoptimization tests')
    for script in scripts:
        subprocess.run([str(root/'out/Release/node'), *test_flags(script.read_text()),
            str(tests/'node-runner.js'), str(script.relative_to(tests))], cwd=tests, check=True, timeout=120)


if __name__ == '__main__':
    main()
