# Copyright (C) 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Protect installed PDF fixture completeness, renderer enforcement and SDK separation."""
import copy
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

import test_installed_qualification as fixtures
import installed_pdf

module = fixtures.module


class InstalledPdfTest(unittest.TestCase):
    def setUp(self):
        fixture = fixtures.InstalledQualificationTest('test_valid_native_manifest')
        fixture.setUp()
        fixture.add_modules()
        self.manifest = fixture.manifest
        self.manifest['modules'] = [e for e in self.manifest['modules'] if e['name'] == 'pdf']
        self.directory = Path('/tmp/PDF fixtures ; data')
        self.binary = Path('/usr/lib64/qore-modules/pdf-api-2.0.qmod')
        self.provider = self.binary.parent / 'PdfDataProvider/PdfDataProvider.qmod'

    def commands(self, phase):
        return dict(module.module_commands('pdf', phase, self.directory, self.binary,
                                           installed_files=str(self.provider)))

    def test_pinned_renderer_packages_are_required_in_correct_phases(self):
        self.assertIs(module.validate(self.manifest), self.manifest)
        for name in ('libpdfium-qore148-0', 'libpdfium-qore-devel'):
            for mutation in ('missing', 'phase'):
                changed = copy.deepcopy(self.manifest)
                entry = next(e for e in changed['packages'] if e['name'] == name)
                if mutation == 'missing':
                    changed['packages'].remove(entry)
                else:
                    entry['phase'] = 'sdk' if entry['phase'] == 'runtime' else 'runtime'
                with self.subTest(name=name, mutation=mutation), self.assertRaisesRegex(ValueError, 'PDF qualification'):
                    module.validate(changed)

    def test_complete_fixture_inventory_and_source_pin_are_enforced(self):
        for mutation in ('missing', 'duplicate', 'repository', 'revision', 'hash'):
            changed = copy.deepcopy(self.manifest)
            row = changed['modules'][0]
            if mutation == 'missing':
                row['fixtures'].pop()
            elif mutation == 'duplicate':
                row['fixtures'].append(copy.deepcopy(row['fixtures'][0]))
            elif mutation == 'repository':
                row['fixtures'][0]['url'] = row['fixtures'][0]['url'].replace('module-pdf', 'module-xml')
            elif mutation == 'revision':
                row['commit'] = 'e' * 40
            else:
                row['fixtures'][0]['sha256'] = 'invalid'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                module.validate(changed)

    def test_runtime_executes_all_suites_against_both_installed_modules(self):
        commands = self.commands('runtime')
        self.assertEqual({'pdf', 'pdf-editor', 'pdf-encryption', 'pdf-forms', 'pdf-renderer',
                          'pdf-signatures', 'PdfDataProvider'}, set(commands))
        for name, command in commands.items():
            with self.subTest(suite=name):
                self.assertIn('QORE_PDF_REQUIRE_PDFIUM=1', command)
                self.assertEqual('-u', command[command.index('PDF_FONT_MODE') - 1])
                self.assertIn('-b', command)
                self.assertIn('--enable-debug', command)
                self.assertEqual(['timeout', '300', 'qore'], command[4:7])
                self.assertEqual([str(self.binary), str(self.provider)],
                                 [command[i+1] for i, arg in enumerate(command) if arg == '-l'])
                self.assertEqual([str(self.directory / 'test' / (name + '.qtest')), '-v'], command[-2:])

    def test_sdk_keeps_runtime_coverage_and_checks_qore_and_pdfium_consumers(self):
        runtime = self.commands('runtime')
        sdk = self.commands('sdk')
        self.assertEqual(set(runtime) | {'compiler', 'pdfium-api-build', 'pdfium-api', 'pdfium-api-valgrind'},
                         set(sdk))
        for name in runtime:
            self.assertEqual(runtime[name], sdk[name])
        self.assertEqual(str(self.directory / 'debian/tests/compiler'), sdk['compiler'][-1])
        self.assertTrue(Path(sdk['pdfium-api-build'][-2]).is_file())
        self.assertEqual([str(self.directory / 'pdfium-api')], sdk['pdfium-api'])
        self.assertEqual('valgrind', sdk['pdfium-api-valgrind'][0])
        self.assertIn('--error-exitcode=99', sdk['pdfium-api-valgrind'])
        self.assertIn('--errors-for-leak-kinds=definite,indirect,possible', sdk['pdfium-api-valgrind'])
        self.assertFalse(any('suppress' in value for value in sdk['pdfium-api-valgrind']))

    def test_invalid_or_ambiguous_installed_module_paths_are_rejected(self):
        for binary in (None, Path('pdf-api-2.0.qmod'), Path('/usr/lib64/../pdf-api-2.0.qmod'),
                       Path('/usr/lib64/other.qmod'), Path('/usr/lib64/pdf-api-2.0.so')):
            with self.subTest(binary=binary), self.assertRaises(ValueError):
                module.module_commands('pdf', 'runtime', self.directory, binary,
                                       installed_files=str(self.provider))
        for files in ('', str(self.provider) + '\n' + str(self.provider),
                      '/elsewhere/PdfDataProvider/PdfDataProvider.qmod'):
            with self.subTest(files=files), self.assertRaises(ValueError):
                module.module_commands('pdf', 'runtime', self.directory, self.binary, installed_files=files)

    def test_runtime_dependencies_exercise_images_and_fonts_without_development_packages(self):
        for family, font in [('fedora', 'dejavu-sans-fonts'), ('el', 'dejavu-sans-fonts'), ('suse', 'dejavu-fonts')]:
            self.assertEqual(['qpdf', 'openssl', 'ImageMagick', font],
                             module.module_dependencies('pdf', 'runtime', family))
            self.assertEqual(['valgrind'], module.module_dependencies('pdf', 'sdk', family))

    def test_pdfium_consumer_uses_installed_pkgconfig_and_keeps_assertions(self):
        with (patch.object(installed_pdf.subprocess, 'check_output', side_effect=[
                '-I"/installed headers" -DFPDF_SHARED', '-L"/installed libs" -lpdfium-qore148']),
              patch.object(installed_pdf.subprocess, 'run') as run):
            installed_pdf.build_api(self.directory / 'pdfium-api')
        command = run.call_args.args[0]
        self.assertIn('-UNDEBUG', command)
        self.assertIn('-Werror', command)
        self.assertIn('-I/installed headers', command)
        self.assertIn('-L/installed libs', command)
        self.assertEqual(['-o', str(self.directory / 'pdfium-api')], command[-2:])
        self.assertTrue(installed_pdf.SOURCE.is_file())
        self.assertTrue(run.call_args.kwargs['check'])

    def test_pdfium_contract_and_compiler_failures_abort_the_build(self):
        with (patch.object(installed_pdf.subprocess, 'check_output',
                           side_effect=subprocess.CalledProcessError(1, ['pkg-config'])),
              patch.object(installed_pdf.subprocess, 'run') as run):
            with self.assertRaises(subprocess.CalledProcessError):
                installed_pdf.build_api(self.directory / 'pdfium-api')
            run.assert_not_called()
        with (patch.object(installed_pdf.subprocess, 'check_output', return_value='-DFPDF_SHARED'),
              patch.object(installed_pdf.subprocess, 'run',
                           side_effect=subprocess.CalledProcessError(7, ['cc']))):
            with self.assertRaises(subprocess.CalledProcessError) as error:
                installed_pdf.build_api(self.directory / 'pdfium-api')
            self.assertEqual(7, error.exception.returncode)


if __name__ == '__main__':
    unittest.main()
