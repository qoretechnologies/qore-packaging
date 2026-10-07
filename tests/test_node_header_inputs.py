# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Check native RPM controls resolve V8's bundled private headers."""
from pathlib import Path
import os
import shlex
import subprocess
import tempfile
import unittest


SPEC = Path(__file__).resolve().parents[1] / 'dependencies/nodejs24-libnode.spec'
BUNDLED = '-Ideps/v8/third_party/abseil-cpp'


class NodeHeaderInputsTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='node header input ')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        check = SPEC.read_text().split('%check\n', 1)[1].split('\n%post ', 1)[0]
        commands = [shlex.split(line) for line in check.replace('\\\n', '').splitlines()
                    if line.startswith('g++ ')]
        self.controls = [(args[args.index('-o') + 1], [arg for arg in args if arg.startswith('-I')])
                         for args in commands if '-Ideps/v8' in args]
        self.assertEqual(7, len(self.controls), 'Cover every private V8 header consumer')
        self.environment = {key: value for key, value in os.environ.items()
                            if key not in ('CPATH', 'CPLUS_INCLUDE_PATH', 'C_INCLUDE_PATH',
                                           'OBJC_INCLUDE_PATH', 'GCC_EXEC_PREFIX', 'COMPILER_PATH')}
        header = self.root / 'deps/v8/src/base/platform/mutex.h'
        header.parent.mkdir(parents=True)
        header.write_text('#include "absl/synchronization/mutex.h"\n')
        self.bundled = self.root / BUNDLED[2:] / 'absl/synchronization/mutex.h'
        self.bundled.parent.mkdir(parents=True)
        self.bundled.write_text('constexpr int packaging_header_version = 137;\n')
        decoy = self.root / 'host headers/absl/synchronization/mutex.h'
        decoy.parent.mkdir(parents=True)
        decoy.write_text('constexpr int packaging_header_version = 999;\n')
        (self.root / 'control.cc').write_text(
            '#include "src/base/platform/mutex.h"\n'
            'static_assert(packaging_header_version == 137, "wrong Abseil headers");\n')

    def compile(self, flags, host=False):
        command = ['c++', '-std=c++20', '-Wall', '-Wextra', '-Werror', '-fsyntax-only',
                   '-nostdinc', '-nostdinc++', *flags]
        if host:
            command += ['-isystem', str(self.root / 'host headers')]
        return subprocess.run([*command, 'control.cc'], cwd=self.root, env=self.environment,
                              text=True, capture_output=True, timeout=30)

    def test_bundled_headers_work_without_installed_development_package(self):
        for name, flags in self.controls:
            with self.subTest(control=name):
                result = self.compile(flags)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual('', result.stderr)

    def test_bundled_headers_win_over_incompatible_system_headers(self):
        for name, flags in self.controls:
            with self.subTest(control=name):
                result = self.compile(flags, host=True)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual('', result.stderr)

    def test_original_missing_path_cannot_compile_without_installed_headers(self):
        for name, flags in self.controls:
            with self.subTest(control=name):
                result = self.compile([arg for arg in flags if arg != BUNDLED])
                self.assertNotEqual(0, result.returncode)
                self.assertIn('absl/synchronization/mutex.h', result.stderr)

    def test_original_missing_path_selects_incompatible_system_headers(self):
        for name, flags in self.controls:
            with self.subTest(control=name):
                result = self.compile([arg for arg in flags if arg != BUNDLED], host=True)
                self.assertNotEqual(0, result.returncode)
                self.assertIn('wrong Abseil headers', result.stderr)


if __name__ == '__main__':
    unittest.main()
