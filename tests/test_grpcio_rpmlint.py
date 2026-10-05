# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
import json
import re
from pathlib import Path
import unittest


class GrpcioLintScopeTest(unittest.TestCase):
    def setUp(self):
        source = Path(__file__).resolve().parents[1] / 'dependencies/python-grpcio-rpmlintrc'
        self.patterns = []
        literals = re.findall(r"^addFilter\(r'(.*)'\)$", source.read_text(), re.M)
        exec(compile(source.read_text(), str(source), 'exec'),
             {'addFilter': lambda pattern: self.patterns.append(re.compile(pattern))})
        self.assertEqual(literals, [pattern.pattern for pattern in self.patterns])

    def matches(self, message):
        return any(pattern.search(message) for pattern in self.patterns)

    @staticmethod
    def message(arch):
        return (f'python313-grpcio.{arch}: W: binary-or-shlib-calls-gethostbyname '
                f'/usr/lib64/python3.13/site-packages/grpc/_cython/'
                f'cygrpc.cpython-313-{arch}-linux-gnu.so')

    def test_exact_reviewed_elf_files(self):
        self.assertEqual(len(self.patterns), 2)
        for arch in ('x86_64', 'aarch64'):
            self.assertTrue(self.matches(self.message(arch)))

    def test_filter_is_registered_in_recipe_and_source_bundle(self):
        root = Path(__file__).resolve().parents[1] / 'dependencies'
        sources = json.loads((root / 'sources.json').read_text())['python-grpcio']['extra_sources']
        self.assertEqual(sources.count('python-grpcio-rpmlintrc'), 1)
        recipe = (root / 'python-grpcio.spec').read_text()
        self.assertEqual(re.findall(r'^Source14:\s+(\S+)$', recipe, re.M),
                         ['python-grpcio-rpmlintrc'])

    def test_unreviewed_packages_paths_and_architectures_remain_visible(self):
        for arch in ('x86_64', 'aarch64'):
            message = self.message(arch)
            for changed in (
                    message.replace('python313-grpcio', 'python313-other'),
                    message.replace('python313', 'python314'),
                    message.replace('python3.13', 'python3.14'),
                    message.replace('cpython-313', 'cpython-314'),
                    message.replace('/grpc/', '/other/'),
                    message.replace('cygrpc.', 'other.'),
                    message.replace('/lib64/', '/lib/'),
                    message.replace('W:', 'E:'),
                    message.replace('gethostbyname', 'mktemp'),
                    message + '.unexpected', 'other: ' + message,
                    message.replace('-' + arch + '-', '-other-')):
                self.assertFalse(self.matches(changed), changed)
        self.assertFalse(self.matches(self.message('ppc64le')))

    def test_unrelated_diagnostics_remain_visible(self):
        for diagnostic in ('binary-or-shlib-defines-rpath', 'undefined-non-weak-symbol',
                           'missing-dependency', 'non-standard-executable-perm',
                           'dangling-symlink'):
            message = self.message('x86_64').replace('binary-or-shlib-calls-gethostbyname', diagnostic)
            self.assertFalse(self.matches(message), message)


if __name__ == '__main__':
    unittest.main()
