# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Exercise the recipe's native link inputs against versioned-only ELF files."""
from pathlib import Path
import os
import re
import shlex
import subprocess
import tempfile
import unittest


SPEC = Path(__file__).resolve().parents[1] / 'dependencies/nodejs24-libnode.spec'


class NodeLinkInputsTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='node link input ')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.built = self.root / 'out/Release'
        self.built.mkdir(parents=True)
        self.decoy = self.root / 'host-library'
        self.decoy.mkdir()
        recipe = SPEC.read_text()
        self.soname = 'libnode.so.' + re.search(r'^%global soname (\d+)$', recipe, re.M)[1]
        check = recipe.split('%check\n', 1)[1].split('\n%post ', 1)[0].replace('\\\n', '')
        self.inputs = []
        for line in check.splitlines():
            if not line.startswith('g++ '):
                continue
            command = shlex.split(line.replace('%{soname}', self.soname.removeprefix('libnode.so.')))
            inputs = [arg for arg in command if arg == '-lnode' or 'libnode.so.' in arg]
            if inputs:
                self.assertEqual(1, len(inputs))
                self.inputs.append((command[command.index('-o') + 1], inputs[0]))
        self.assertEqual(9, len(self.inputs), 'Every native shared-library control is covered')
        self.environment = {key: value for key, value in os.environ.items()
                            if key not in ('LIBRARY_PATH', 'LD_LIBRARY_PATH', 'LD_PRELOAD')}
        self.library(self.built / self.soname, 137)
        self.library(self.decoy / self.soname, 999)
        (self.decoy / 'libnode.so').symlink_to(self.soname)
        (self.root / 'consumer.c').write_text(
            'extern int node_packaging_probe(void);\n'
            'int main(void) { return node_packaging_probe() == 137 ? 0 : 1; }\n')

    def run_command(self, command):
        return subprocess.run(command, cwd=self.root, env=self.environment, text=True,
                              capture_output=True, timeout=30)

    def library(self, path, value):
        source = path.with_suffix('.c')
        source.write_text('int node_packaging_probe(void) { return ' + str(value) + '; }\n')
        result = self.run_command(['cc', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
                                   '-Wl,-soname,' + self.soname, str(source), '-o', str(path)])
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual('', result.stderr)

    def link(self, operand):
        return self.run_command(['cc', '-Wall', '-Wextra', '-Werror', 'consumer.c',
                                 '-L' + str(self.decoy), '-Lout/Release', '-Wl,-t',
                                 operand, '-Wl,-rpath,' + str(self.built), '-o', 'consumer'])

    def test_versioned_only_build_wins_over_installed_development_library(self):
        self.assertFalse((self.built / 'libnode.so').exists())
        for name, operand in self.inputs:
            with self.subTest(control=name):
                result = self.link(operand)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual('', result.stderr)
                self.assertIn('out/Release/' + self.soname, result.stdout.splitlines())
                self.assertNotIn(str(self.decoy / 'libnode.so'), result.stdout.splitlines())
                executed = self.run_command(['./consumer'])
                self.assertEqual(0, executed.returncode, executed.stderr)

    def test_missing_built_library_cannot_fall_back_to_an_installed_copy(self):
        (self.built / self.soname).rename(self.built / 'unavailable')
        for name, operand in self.inputs:
            with self.subTest(control=name):
                result = self.link(operand)
                self.assertNotEqual(0, result.returncode)
                self.assertIn('out/Release/' + self.soname, result.stderr)

    def test_original_generic_link_silently_selects_the_installed_library(self):
        result = self.link('-lnode')
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(str(self.decoy / 'libnode.so'), result.stdout.splitlines())
        self.assertNotIn('out/Release/' + self.soname, result.stdout.splitlines())


if __name__ == '__main__':
    unittest.main()
