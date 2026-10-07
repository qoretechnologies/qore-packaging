# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
import importlib.util
from pathlib import Path
import subprocess
import unittest

SOURCE = Path(__file__).resolve().parents[1]/'dependencies/nodejs24-wasm-deopt-test.py'
loader = importlib.util.spec_from_file_location('node_wasm_deopt', SOURCE)
control = importlib.util.module_from_spec(loader)
loader.loader.exec_module(control)


class WasmDeoptimizationTest(unittest.TestCase):
    prefix = '''base::OwnedVector<uint8_t> CodeGenerator::GenerateWasmDeoptimizationData() {
  CHECK_EQ(result_, kSuccess);
  CHECK_LE(deoptimization_exits_.size(), static_cast<size_t>(Deoptimizer::kMaxNumberOfEntries) + 1);
  int deopt_count = static_cast<int>(deoptimization_exits_.size());
  auto deopt_entries = base::OwnedVector<wasm::WasmDeoptEntry>::New(deopt_count);
  for (int i = 0; i < deopt_count; i++) {
    auto* deoptimization_exit = deoptimization_exits_[i];
    CHECK_EQ(i, deoptimization_exit->deoptimization_id());
  }
'''
    suffix = '  base::Vector<const uint8_t> frame_translations = translations_.ToFrameTranslationWasm();\n}'

    def test_preserve_allocation_and_fill_body(self):
        actual = control.extract_prefix('// before\n' + self.prefix + self.suffix)
        self.assertEqual(actual, self.prefix.replace(
            'base::OwnedVector<uint8_t> CodeGenerator::GenerateWasmDeoptimizationData()',
            'base::OwnedVector<wasm::WasmDeoptEntry> GeneratorAdapter::Generate()') +
            '  return deopt_entries;\n}\n')

    def test_missing_or_ambiguous_source_rejected(self):
        for source in ('', self.prefix, self.prefix + self.suffix + self.prefix,
                       (self.prefix+self.suffix).replace('CHECK_EQ(result_, kSuccess);', ''),
                       (self.prefix+self.suffix).replace('CHECK_LE(deoptimization_exits_.size(),', 'DCHECK_LE(deoptimization_exits_.size(),'),
                       (self.prefix+self.suffix).replace('CHECK_EQ(i, deoptimization_exit->deoptimization_id());', '')):
            with self.subTest(source=source), self.assertRaises(ValueError):
                control.extract_prefix(source)

    def test_preserve_upstream_flags_in_order(self):
        self.assertEqual(control.test_flags('// Flags: --wasm-deopt --allow-natives-syntax\n'
            '// text\n// Flags: --wasm-tiering-budget=1000 --no-predictable\n'),
            ['--wasm-deopt', '--allow-natives-syntax', '--wasm-tiering-budget=1000', '--no-predictable'])

    def test_invalid_flag_shapes_rejected(self):
        for flags in ('', '// Flags: test.js', '// Flags: --eval=process.exit(0)',
                      '// Flags: --require=anything', '// Flags: --wasm-deopt;touch'):
            with self.subTest(flags=flags), self.assertRaises(ValueError):
                control.test_flags(flags)

    def test_exact_expected_failure_required(self):
        expected = 'Check failed: result_ == kSuccess.'
        control.require_rejection('failed-generation', subprocess.CompletedProcess([], -6, '', expected))
        for code, message in ((0, expected), (1, expected), (-11, expected), (-6, 'unrelated failure')):
            with self.subTest(code=code, message=message), self.assertRaises(AssertionError):
                control.require_rejection('failed-generation', subprocess.CompletedProcess([], code, '', message))


if __name__ == '__main__':
    unittest.main()
