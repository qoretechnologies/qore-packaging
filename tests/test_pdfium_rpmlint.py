# Copyright 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
import re
from pathlib import Path
import unittest


class PdfiumLicenseVocabularyTest(unittest.TestCase):
    def setUp(self):
        self.patterns = []
        source = Path(__file__).resolve().parents[1] / 'dependencies/pdfium-rpmlintrc'
        literals = re.findall(r"^addFilter\(r'(.*)'\)$", source.read_text(), re.M)
        exec(compile(source.read_text(), str(source), 'exec'),
             {'addFilter': lambda pattern: self.patterns.append(re.compile(pattern))})
        self.assertEqual(literals, [pattern.pattern for pattern in self.patterns])

    def matches(self, message):
        return any(pattern.search(message) for pattern in self.patterns)

    def test_documented_custom_notices_on_exact_packages(self):
        for name in ('libpdfium-qore148-0', 'libpdfium-qore148-0-debuginfo',
                     'libpdfium-qore-devel', 'qore-pdfium-debugsource'):
            for arch in ('x86_64', 'aarch64'):
                for license_ref in ('LicenseRef-AGG-2.3', 'LicenseRef-Public-Domain'):
                    self.assertTrue(self.matches(f'{name}.{arch}: W: invalid-license {license_ref}'))
        self.assertTrue(self.matches('qore-pdfium.src: W: invalid-license LicenseRef-AGG-2.3'))

    def test_other_licenses_packages_and_errors_remain_visible(self):
        prefix = 'libpdfium-qore148-0.x86_64: W: '
        diagnostic = 'invalid-license LicenseRef-AGG-2.3'
        for message in ('invalid-license LicenseRef-Unknown', 'invalid-license LicenseRef-AGG-2.4',
                        'invalid-license LicenseRef-Public-Domain-Unknown', diagnostic + ' extra',
                        'no-license-tag', 'no-documentation', 'shlib-policy-name-error incorrect',
                        'binary-or-shlib-defines-rpath /usr/lib64/libpdfium-qore148.so.0'):
            self.assertFalse(self.matches(prefix + message), message)
        for name in ('other', 'libpdfium-qore149-0', 'libpdfium-qore148-0-extra'):
            self.assertFalse(self.matches(f'{name}.x86_64: W: {diagnostic}'))
        self.assertFalse(self.matches(prefix.replace(': W:', ': E:') + diagnostic))
        self.assertFalse(self.matches(prefix.replace('x86_64', 'unexpected') + diagnostic))


if __name__ == '__main__':
    unittest.main()
