# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Verify the fixed V8 runtime/SDK commands and fixture boundary."""
import copy
from pathlib import Path
import unittest

import test_installed_qualification as fixtures

module = fixtures.module


class InstalledV8Test(unittest.TestCase):
    def setUp(self):
        fixture = fixtures.InstalledQualificationTest('test_valid_native_manifest')
        fixture.setUp()
        fixture.add_modules()
        self.manifest = fixture.manifest
        self.manifest['modules'] = [entry for entry in self.manifest['modules'] if entry['name'] == 'v8']
        self.directory = Path('/tmp/V8 fixtures ; data')
        self.binary = Path('/usr/lib64/qore-modules/v8-api-2.0.qmod')
        self.files = '\n'.join(str(self.binary.parent) + suffix for suffix in module.MODULE_PRELOADS['v8'])

    def commands(self, phase):
        return dict(module.module_commands('v8', phase, self.directory, self.binary,
                                           installed_files=self.files))

    def test_pinned_complete_manifest_and_required_runtime_dependencies(self):
        self.assertIs(module.validate(self.manifest), self.manifest)
        for name in ('qore-process-module', 'qore-uuid-module'):
            for mutation in ('missing', 'phase'):
                changed = copy.deepcopy(self.manifest)
                entry = next(row for row in changed['packages'] if row['name'] == name)
                if mutation == 'missing':
                    changed['packages'].remove(entry)
                else:
                    entry['phase'] = 'sdk'
                with self.subTest(name=name, mutation=mutation), self.assertRaisesRegex(ValueError, 'V8 qualification'):
                    module.validate(changed)

    def test_complete_runtime_suites_preload_only_installed_modules(self):
        commands = self.commands('runtime')
        expected = {Path(path).stem for path in module.MODULE_FIXTURES['v8'] if path.endswith('.qtest')}
        self.assertEqual(14, len(expected))
        self.assertEqual(expected | {'cli'}, set(commands))
        for name in expected:
            command = commands[name]
            with self.subTest(suite=name):
                self.assertIn('--enable-debug', command)
                self.assertIn('-b', command)
                self.assertEqual(['timeout', '600', 'qore'], command[command.index('timeout'):command.index('timeout')+3])
                self.assertEqual([str(self.directory / 'test' / (name + '.qtest')), '-v'], command[-2:])
                self.assertIn('QORE_V8_TEST_MODULE_DIR=' + str(self.binary.parent), command)
                self.assertIn('QORE_V8_TEST_QMOD_DIR=' + str(self.binary.parent), command)
                preloads = [command[i + 1] for i, arg in enumerate(command) if arg == '-l']
                self.assertEqual([str(self.binary), *self.files.splitlines()], preloads)
                for variable in ('NODE_OPTIONS', 'NODE_PATH', 'QORE_TYPESCRIPT_ACTION_SCRIPTS',
                                 'QORE_TYPESCRIPT_MASTER_ACTION_SCRIPT', 'QORE_PROVIDER_INDEX_DIR'):
                    self.assertEqual('-u', command[command.index(variable) - 1])
                self.assertNotIn('c++', command)
        self.assertEqual(['sh', str(self.directory / 'debian/tests/cli')], commands['cli'][-2:])

    def test_sdk_preserves_runtime_coverage_and_adds_real_consumers(self):
        runtime = self.commands('runtime')
        sdk = self.commands('sdk')
        self.assertEqual(set(runtime) | {'compiler', 'reference-build', 'reference-lifetime', 'reference-valgrind'},
                         set(sdk))
        for name, command in runtime.items():
            self.assertEqual(command, sdk[name])
        self.assertEqual(str(self.directory / 'debian/tests/compiler'), sdk['compiler'][-1])
        build = sdk['reference-build']
        self.assertIn('-flto', build)
        self.assertIn('-lqore', build)
        self.assertEqual(['-o', str(self.directory / 'reference-control')], build[-2:])
        source = next(arg for arg in build if arg.endswith('/v8-reference-control.cpp'))
        self.assertTrue(Path(source).is_file())
        valgrind = sdk['reference-valgrind']
        self.assertEqual('valgrind', valgrind[0])
        self.assertIn('--error-exitcode=99', valgrind)
        self.assertIn('--errors-for-leak-kinds=definite,indirect,possible', valgrind)
        self.assertFalse(any('suppress' in arg for arg in valgrind))

    def test_unsafe_ambiguous_or_separate_module_paths_are_rejected(self):
        for invalid in (None, Path('v8-api-2.0.qmod'), Path('/usr/lib64/../v8-api-2.0.qmod'),
                        Path('/usr/lib64/v8-api-2.0.so'), Path('/usr/lib64/other.qmod')):
            with self.subTest(binary=invalid), self.assertRaises(ValueError):
                module.module_commands('v8', 'runtime', self.directory, invalid, installed_files=self.files)
        for invalid in ('', self.files + '\n' + self.files.splitlines()[0],
                        self.files.replace('/usr/lib64/qore-modules/TypeScriptProxy/', '/elsewhere/TypeScriptProxy/')):
            with self.subTest(files=invalid), self.assertRaises(ValueError):
                module.module_commands('v8', 'runtime', self.directory, self.binary, installed_files=invalid)

    def test_runtime_dependencies_do_not_install_a_compiler_or_memory_profiler(self):
        for family in ('fedora', 'suse', 'el'):
            self.assertEqual(['openssl', 'which'], module.module_dependencies('v8', 'runtime', family))
            self.assertEqual(['valgrind'], module.module_dependencies('v8', 'sdk', family))


if __name__ == '__main__':
    unittest.main()
