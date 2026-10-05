# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
import importlib.util
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.util.spec_from_file_location('node_symbols', ROOT / 'dependencies/nodejs24-rpm-symbols.py')
symbols = importlib.util.module_from_spec(loader)
loader.loader.exec_module(symbols)


class NodeMetadataTest(unittest.TestCase):
    def test_all_obsolete_names_and_versions_are_rejected(self):
        for name in symbols.OBSOLETE:
            for version in ('', '@GLIBC_2.2.5', '@@GLIBC_2.17'):
                self.assertEqual(symbols.obsolete_imports('                 U ' + name + version), [name])

    def test_cares_and_unrelated_names_are_permitted(self):
        for name in symbols.OBSOLETE:
            self.assertEqual(symbols.obsolete_imports(' U ares_' + name + '@CARES_1.0'), [])
        self.assertEqual(symbols.obsolete_imports('\n U getaddrinfo@GLIBC_2.17\n U free\n'), [])

    def test_mixed_symbols_cannot_hide_obsolete_imports(self):
        self.assertEqual(symbols.obsolete_imports(' U ares_gethostbyaddr\n U gethostbyaddr\n'
                                               ' U gethostbyname_r@GLIBC_2.17\n U gethostbyaddr'),
                         ['gethostbyaddr', 'gethostbyname_r'])

    def test_sqlite_license_is_named_and_installed_in_both_packages(self):
        recipe = (ROOT / 'dependencies/nodejs24-libnode.spec').read_text()
        self.assertIn(' AND blessing\n', recipe)
        self.assertNotIn('LicenseRef-Public-Domain', recipe)
        self.assertEqual(recipe.count('%license LICENSE SQLITE-LICENSE'), 2)
        notice = (ROOT / 'dependencies/nodejs24-SQLITE-LICENSE').read_text()
        self.assertIn('The author disclaims copyright', notice)
        self.assertIn('May you share freely, never taking more than you give.', notice)

    def test_proposed_filter_accepts_only_the_exact_library_warning(self):
        patterns = []
        source = ROOT / 'dependencies/nodejs24-libnode-rpmlintrc'
        exec(compile(source.read_text(), str(source), 'exec'),
             {'addFilter': lambda expression: patterns.append(re.compile(expression))})
        self.assertEqual(len(patterns), 1)
        for arch in ('x86_64', 'aarch64'):
            message = (f'libnode137.{arch}: W: binary-or-shlib-calls-gethostbyname '
                       '/usr/lib64/libnode.so.137')
            self.assertTrue(patterns[0].search(message))
            for changed in (message.replace('libnode137.', 'libnode138.'),
                            message.replace('.so.137', '.so.138'),
                            message.replace(arch, 'ppc64le'),
                            message.replace('W:', 'E:'),
                            message.replace('gethostbyname', 'mktemp'),
                            message.replace('/lib64/', '/lib/'),
                            'prefix ' + message, message + '.unexpected'):
                self.assertFalse(patterns[0].search(changed), changed)

    def test_guard_and_filter_are_registered_together(self):
        sources = json.loads((ROOT / 'dependencies/sources.json').read_text())['nodejs24-libnode']
        recipe = (ROOT / 'dependencies/nodejs24-libnode.spec').read_text()
        for number, name in ((8, 'nodejs24-SQLITE-LICENSE'), (9, 'nodejs24-rpm-symbols.py'),
                             (10, 'nodejs24-libnode-rpmlintrc')):
            self.assertEqual(sources['extra_sources'].count(name), 1)
            self.assertEqual(re.findall(r'^Source' + str(number) + r':\s+(\S+)$', recipe, re.M), [name])
        self.assertIn('python3 %{SOURCE9} out/Release/libnode.so.%{soname}', recipe)


if __name__ == '__main__':
    unittest.main()
