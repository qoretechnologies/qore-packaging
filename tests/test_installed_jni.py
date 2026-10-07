# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import installed_jni as jni


class JniFixtureTransferTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        for number, name in enumerate(jni.ARTIFACTS):
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(bytes([number]) * (number + 1))
        self.manifest = {'arch': 'aarch64', 'packages': [{'sha256': 'a' * 64}],
                         'modules': [{'name': 'jni', 'commit': 'b' * 40}]}
        self.bundle = self.root / 'bundle'

    def export(self):
        return jni.export_bundle(self.source, self.bundle, self.manifest)

    def test_complete_bundle_roundtrip_preserves_bytes_and_executable_mode(self):
        record = self.export()
        self.assertEqual(record, jni.verify_bundle(self.bundle, self.manifest))
        target = self.root / 'runtime'
        jni.import_bundle(self.bundle, target, self.manifest)
        for name in jni.ARTIFACTS:
            self.assertEqual((self.source / name).read_bytes(), (target / name).read_bytes())
            self.assertEqual((target / name).stat().st_mode & 0o777,
                             0o755 if name == 'jni-smoke' else 0o644)

    def test_manifest_fingerprint_covers_architecture_sources_and_package_hashes(self):
        self.export()
        for mutation in ('arch', 'package', 'source'):
            manifest = copy.deepcopy(self.manifest)
            if mutation == 'arch':
                manifest['arch'] = 'x86_64'
            elif mutation == 'package':
                manifest['packages'][0]['sha256'] = 'c' * 64
            else:
                manifest['modules'][0]['commit'] = 'd' * 40
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                jni.verify_bundle(self.bundle, manifest)

    def test_manifest_key_order_does_not_change_fingerprint(self):
        self.assertEqual(jni.manifest_digest({'a': 1, 'b': 2}),
                         jni.manifest_digest({'b': 2, 'a': 1}))

    def test_tampering_is_rejected_before_any_runtime_copy(self):
        self.export()
        (self.bundle / 'test/opcua-test-server.jar').write_bytes(b'changed')
        target = self.root / 'runtime'
        with self.assertRaisesRegex(ValueError, 'digest mismatch'):
            jni.import_bundle(self.bundle, target, self.manifest)
        self.assertFalse(target.exists())

    def test_incomplete_or_unexpected_artifact_inventory_is_rejected(self):
        record = self.export()
        for mutation in ('missing', 'extra', 'traversal', 'list', 'null'):
            changed = copy.deepcopy(record)
            if mutation == 'missing':
                changed['files'].pop('jni-smoke')
            elif mutation == 'extra':
                changed['files']['unreviewed-script'] = 'a' * 64
            elif mutation == 'traversal':
                changed['files']['../escape'] = changed['files'].pop('jni-smoke')
            elif mutation == 'list':
                changed = []
            else:
                changed['files'] = None
            (self.bundle / 'bundle.json').write_text(json.dumps(changed))
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                jni.verify_bundle(self.bundle, self.manifest)

    def test_symlinked_artifact_is_rejected_even_with_matching_bytes(self):
        self.export()
        path = self.bundle / 'jni-smoke'
        path.unlink()
        path.symlink_to(self.source / 'jni-smoke')
        with self.assertRaisesRegex(ValueError, 'regular file'):
            jni.verify_bundle(self.bundle, self.manifest)

    def test_symlinked_bundle_parent_directory_is_rejected(self):
        self.export()
        (self.bundle / 'test').rename(self.bundle / 'real-test')
        (self.bundle / 'test').symlink_to(self.bundle / 'real-test', target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'regular file'):
            jni.verify_bundle(self.bundle, self.manifest)

    def test_existing_runtime_artifact_is_preserved(self):
        self.export()
        target = self.root / 'runtime'
        target.mkdir()
        (target / 'jni-smoke').write_text('existing')
        with self.assertRaisesRegex(ValueError, 'replace'):
            jni.import_bundle(self.bundle, target, self.manifest)
        self.assertEqual((target / 'jni-smoke').read_text(), 'existing')
        self.assertFalse((target / 'test').exists())

    def test_runtime_parent_symlink_cannot_redirect_fixture_writes(self):
        self.export()
        target = self.root / 'runtime'
        outside = self.root / 'outside'
        target.mkdir()
        outside.mkdir()
        (target / 'test').symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'replace'):
            jni.import_bundle(self.bundle, target, self.manifest)
        self.assertEqual(list(outside.iterdir()), [])

    def test_missing_source_rejected_before_bundle_creation(self):
        (self.source / 'jni-smoke').unlink()
        with self.assertRaisesRegex(ValueError, 'regular file'):
            self.export()
        self.assertFalse(self.bundle.exists())

    def test_copy_failure_does_not_publish_bundle_metadata(self):
        with patch.object(jni.shutil, 'copyfile', side_effect=OSError('disk full')):
            with self.assertRaisesRegex(OSError, 'disk full'):
                self.export()
        self.assertFalse((self.bundle / 'bundle.json').exists())

    def test_runtime_commands_cover_provider_and_native_safety_suites_without_compiling(self):
        commands = jni.commands('runtime', Path('/tmp/fixture space'), None)
        names = {name for name, _ in commands}
        for name in ('jni-reference-safety', 'jni-exception-location', 'OpcUaDataProvider',
                     'ExcelDataProvider', 'JdbcDataProvider', 'compiled-consumer', 'headless'):
            self.assertIn(name, names)
        self.assertNotIn('compiler', names)
        self.assertFalse({'javac', 'qkotlinc', 'qcc'} & {token for _, command in commands for token in command})
        for name, command in commands:
            if name in ('jni-reference-safety', 'jni-exception-location'):
                self.assertIn('--enable-debug', command)
                self.assertIn('-b', command)

    def test_sdk_commands_build_fixtures_and_cover_all_reviewed_suites(self):
        commands = jni.commands('sdk', Path('/tmp/SDK fixtures'), Path('/usr/lib64/qore-modules/jni-api-2.0.qmod'))
        names = [name for name, _ in commands]
        self.assertEqual(names[:2], ['build-java-fixtures', 'build-kotlin-fixture'])
        for path in jni.FIXTURES:
            if path.endswith('.qtest'):
                self.assertIn(Path(path).stem, names)
        self.assertEqual(names[-1], 'compiler')
        self.assertIn('jni', names)
        self.assertIn('kotlin', names)
        self.assertNotIn('jms', names)

    def test_sdk_requires_absolute_installed_module_and_valid_phase(self):
        for binary in (None, Path('relative.qmod')):
            with self.subTest(binary=binary), self.assertRaises(ValueError):
                jni.commands('sdk', Path('/tmp/test'), binary)
        with self.assertRaises(ValueError):
            jni.commands('unreviewed', Path('/tmp/test'), None)

    def test_both_phases_use_private_writable_home_and_font_cache(self):
        for phase in ('sdk', 'runtime'):
            directory = Path('/tmp/private JNI fixture')
            commands = jni.commands(phase, directory, Path('/usr/lib64/qore-modules/jni-api-2.0.qmod'))
            for name, command in commands:
                with self.subTest(phase=phase, name=name):
                    self.assertIn('HOME=' + str(directory), command)
                    self.assertIn('XDG_CACHE_HOME=' + str(directory / '.cache'), command)
                    self.assertIn('QORE_JNI_JVM_ARGS=-Xcheck:jni', command)


if __name__ == '__main__':
    unittest.main()
