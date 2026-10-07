# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
import importlib.util
from pathlib import Path
import shlex
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'dependencies/nodejs24-reschedule-test.py'
loader = importlib.util.spec_from_file_location('node_reschedule', SOURCE)
control = importlib.util.module_from_spec(loader)
loader.loader.exec_module(control)


class RescheduleCommandTest(unittest.TestCase):
    prefix = 'cmd_/build/raw-machine-assembler.o := g++ -o /build/raw-machine-assembler.o ../src/raw-machine-assembler.cc '
    suffix = '-DV8_TARGET_ARCH_ARM64 -O2 -Wall -Werror=return-type -fstack-protector-strong -g -MMD -MF /build/raw.d -c'

    def test_native_abi_hardening_and_warnings_survive(self):
        command = control.compile_command(self.prefix + self.suffix, Path('/test/source.cc'), Path('/test/test.o'))
        self.assertEqual(command[:4], ['g++', '-o', '/test/test.o', '/test/source.cc'])
        for flag in ('-DV8_TARGET_ARCH_ARM64', '-O2', '-Wall', '-Werror=return-type', '-fstack-protector-strong', '-g'):
            self.assertIn(flag, command)
        self.assertEqual(command[command.index('-MF') + 1], '/test/test.d')
        self.assertEqual(command[-1], '-fno-lto')

    def test_lto_modes_use_native_archive_sections(self):
        for lto in ('-flto', '-flto=auto', '-flto=4', '-flto=jobserver'):
            with self.subTest(lto=lto):
                command = control.compile_command(self.prefix + lto + ' -ffat-lto-objects ' + self.suffix,
                                                  Path('/test/source.cc'), Path('/test/test.o'))
                self.assertNotIn(lto, command)
                self.assertNotIn('-ffat-lto-objects', command)
                self.assertIn('-fno-lto', command)

    def test_quotes_spaces_and_literal_shell_characters(self):
        flags = ['-I/path with spaces', '-DLITERAL=$(false)`false`', '-DNAME="a b"']
        command = control.compile_command(self.prefix + shlex.join(flags) + ' ' + self.suffix,
                                          Path('/test/source with spaces.cc'), Path('/test/test.o'))
        for flag in flags:
            self.assertIn(flag, command)
        self.assertEqual(command[3], '/test/source with spaces.cc')

    def test_dependency_contents_are_not_executed(self):
        command = control.compile_command(self.prefix + self.suffix + '\nmalicious: ignored\n',
                                          Path('/test/source.cc'), Path('/test/test.o'))
        self.assertNotIn('malicious:', command)

    def test_malformed_or_unexpected_receipts_are_rejected(self):
        valid = self.prefix + self.suffix
        bad = ['', 'not a command', valid.replace('cmd_', 'other_', 1),
               valid.replace('g++', 'sh -c', 1), valid.replace(' -o ', ' -E ', 1),
               valid.replace('raw-machine-assembler.cc', 'different.cc'),
               valid.replace(' -c', ''), valid + ' -c', valid.replace('-MF', '-MD'),
               valid.replace('/build/raw.d', '-c'), valid.replace(' -MF /build/raw.d', '') + ' -MF']
        for receipt in bad:
            with self.subTest(receipt=receipt):
                with self.assertRaises(ValueError):
                    control.compile_command(receipt, Path('/test/source.cc'), Path('/test/test.o'))


if __name__ == '__main__':
    unittest.main()
