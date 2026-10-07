# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


loader = importlib.util.spec_from_file_location('install_layout', Path(__file__).with_name('install-layout.py'))
layout = importlib.util.module_from_spec(loader)
loader.loader.exec_module(layout)


class InstallLayoutTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.parent = Path(temporary.name)
        self.root = self.parent / 'staging'
        self.root.mkdir()
        for relative, interpreter in layout.INTERPRETERS.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'#!/usr/bin/env ' + interpreter + b'\n# body is unchanged\n')
            path.chmod(0o755)
        self.docdir = Path('/usr/share/doc/packages')
        self.notices = self.root / self.docdir.relative_to('/') / 'qore-jni-module/third-party-notices'
        self.notices.mkdir(parents=True)
        self.notice = self.notices / 'example.jar.txt'
        self.notice.write_bytes(b'coordinate\nCopyright 2026\r\nLicense\rAttribution\n')
        self.jar = self.root / 'usr/share/qore-modules/Example/jar/example.jar'
        self.jar.parent.mkdir(parents=True)
        self.jar.write_bytes(b'PK\x03\x04signed bytes\r\n\r')
        self.provenance = self.notices / 'provenance.json'
        self.provenance.write_bytes(b'{"source": "unchanged"}\r\n')

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes()
                for p in self.root.rglob('*') if p.is_file()}

    def test_interpreters_modes_notices_and_pinned_bytes(self):
        jars = self.jar.read_bytes(), self.provenance.read_bytes()
        layout.normalize(self.root, self.docdir)
        for relative, interpreter in layout.INTERPRETERS.items():
            path = self.root / relative
            self.assertEqual(b'#!/usr/bin/' + interpreter + b'\n# body is unchanged\n', path.read_bytes())
            self.assertEqual(0o755, path.stat().st_mode & 0o777)
        self.assertEqual(b'coordinate\nCopyright 2026\nLicense\nAttribution\n', self.notice.read_bytes())
        self.assertEqual(jars, (self.jar.read_bytes(), self.provenance.read_bytes()))
        before = self.snapshot()
        layout.normalize(self.root, self.docdir)
        self.assertEqual(before, self.snapshot())

    def test_other_distribution_documentation_prefix(self):
        destination = self.root / 'usr/share/doc/qore-jni-module'
        shutil.move(str(self.notices.parent), destination)
        layout.normalize(self.root, '/usr/share/doc')
        self.assertNotIn(b'\r', (destination / 'third-party-notices/example.jar.txt').read_bytes())

    def test_missing_script_is_rejected_before_any_write(self):
        (self.root / list(layout.INTERPRETERS)[-1]).unlink()
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'regular staged file'):
            layout.normalize(self.root, self.docdir)
        self.assertEqual(before, self.snapshot())

    def test_unexpected_or_truncated_interpreter_is_rejected_before_any_write(self):
        script = self.root / list(layout.INTERPRETERS)[-1]
        for data in (b'#!/usr/bin/env python3\nbody', b'#!/usr/bin/env bash'):
            with self.subTest(data=data):
                script.write_bytes(data)
                before = self.snapshot()
                with self.assertRaisesRegex(ValueError, 'Unexpected installed script interpreter'):
                    layout.normalize(self.root, self.docdir)
                self.assertEqual(before, self.snapshot())

    def test_missing_generated_notices_is_rejected_before_any_write(self):
        self.notice.unlink()
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'Missing generated JAR notices'):
            layout.normalize(self.root, self.docdir)
        self.assertEqual(before, self.snapshot())

    def test_invalid_documentation_prefix(self):
        before = self.snapshot()
        for prefix in ('relative', '/', '/usr/../doc'):
            with self.subTest(prefix=prefix), self.assertRaisesRegex(ValueError, 'Documentation prefix'):
                layout.normalize(self.root, prefix)
        self.assertEqual(before, self.snapshot())

    def test_symlinked_script_does_not_write_outside_staging(self):
        script = self.root / 'usr/bin/qjavac'
        external = self.parent / 'outside'
        script.rename(external)
        script.symlink_to(external)
        before = external.read_bytes(), self.snapshot()
        with self.assertRaisesRegex(ValueError, 'regular staged file'):
            layout.normalize(self.root, self.docdir)
        self.assertEqual(before, (external.read_bytes(), self.snapshot()))

    def test_symlinked_staging_directory_rejected(self):
        alias = self.parent / 'alias'
        alias.symlink_to(self.root, target_is_directory=True)
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'regular staged file'):
            layout.normalize(alias, self.docdir)
        self.assertEqual(before, self.snapshot())

    def test_symlinked_notice_rejected_before_any_write(self):
        external = self.parent / 'outside'
        self.notice.rename(external)
        self.notice.symlink_to(external)
        before = external.read_bytes(), self.snapshot()
        with self.assertRaisesRegex(ValueError, 'regular staged file'):
            layout.normalize(self.root, self.docdir)
        self.assertEqual(before, (external.read_bytes(), self.snapshot()))

    def test_duplicate_jars_hardlink_without_rewriting_or_crossing_packages(self):
        runtime = self.jar.parents[2]
        duplicate = runtime / 'Another/jar/example.jar'
        duplicate.parent.mkdir(parents=True)
        duplicate.write_bytes(self.jar.read_bytes())
        duplicate.chmod(self.jar.stat().st_mode & 0o777)
        different = duplicate.with_name('different.jar')
        different.write_bytes(b'different version of dependency')
        optional = self.root / 'usr/share/qore/java/kotlin/lib/example.jar'
        optional.parent.mkdir(parents=True)
        optional.write_bytes(self.jar.read_bytes())
        before = self.jar.read_bytes(), different.read_bytes(), optional.read_bytes()
        subprocess.run(['hardlink', '-t', '-O', str(runtime)], check=True, capture_output=True)
        self.assertEqual(self.jar.stat().st_ino, duplicate.stat().st_ino)
        self.assertNotEqual(self.jar.stat().st_ino, different.stat().st_ino)
        self.assertNotEqual(self.jar.stat().st_ino, optional.stat().st_ino)
        self.assertEqual(before, (self.jar.read_bytes(), different.read_bytes(), optional.read_bytes()))


if __name__ == '__main__':
    unittest.main()
