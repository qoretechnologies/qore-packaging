#!/usr/bin/python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Check complete-suite validation, diagnostic policy and fixture cleanup."""
import importlib.util
import io
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

loader = importlib.util.spec_from_file_location('fixture', Path(__file__).with_name('litmus-httpd-test.py'))
fixture = importlib.util.module_from_spec(loader)
loader.loader.exec_module(fixture)


class FixtureTests(unittest.TestCase):
    def setUp(self):
        self.output = '\n'.join(f"summary for `{name}': of {count} tests run: {count} passed, 0 failed"
                                for name, count in [('basic',16),('copymove',13),('props',33),('locks',40),('http',4)])

    def test_all_suites_and_only_approved_diagnostics(self):
        self.assertEqual([], fixture.validate_output(self.output))
        for warning in fixture.EXPECTED_WARNINGS:
            self.assertEqual([warning], fixture.validate_output(self.output + '\nWARNING: ' + warning))

    def test_missing_duplicate_failed_or_unknown_warning_is_rejected(self):
        for output in (self.output.split('\n', 1)[1], self.output + '\n' + self.output,
                       self.output.replace('16 passed, 0 failed', '15 passed, 1 failed'),
                       self.output + '\nWARNING: unexpected server behavior'):
            with self.subTest(output=output), self.assertRaises(RuntimeError):
                fixture.validate_output(output)

    def test_readiness_and_early_exit(self):
        for payload, succeeds in ((b'notice: resuming normal operations\n', True), (b'startup failed\n', False)):
            read, write = os.pipe()
            with os.fdopen(read, 'rb') as stream:
                os.write(write, payload)
                os.close(write)
                if succeeds:
                    self.assertIn('resuming normal operations', fixture.await_startup(stream))
                else:
                    with self.assertRaisesRegex(RuntimeError, 'exited before startup'):
                        fixture.await_startup(stream)

    def test_startup_deadline(self):
        read, write = os.pipe()
        try:
            with os.fdopen(read, 'rb') as stream, self.assertRaisesRegex(RuntimeError, 'deadline exceeded'):
                fixture.await_startup(stream, timeout=0)
        finally:
            os.close(write)

    def test_static_dynamic_and_missing_apache_modules(self):
        with tempfile.TemporaryDirectory() as directory:
            modules = Path(directory)
            for name in ('authz_core', 'dav', 'dav_fs'):
                (modules / ('mod_' + name + '.so')).touch()
            directives = fixture.module_directives(modules, 'prefork.c\nmod_unixd.c\n')
            self.assertEqual(3, len(directives))
            self.assertTrue(all('mpm_' not in line and 'unixd' not in line for line in directives))
            with self.assertRaisesRegex(RuntimeError, 'mod_mpm_event.so'):
                fixture.module_directives(modules, '')
            for name in ('mpm_event', 'unixd'):
                (modules / ('mod_' + name + '.so')).touch()
            self.assertEqual(5, len(fixture.module_directives(modules, '')))

    def test_cleanup_on_success_startup_failure_and_test_failure(self):
        for phase in ('success', 'startup', 'test'):
            server = Mock(pid=1234)
            server.communicate.return_value = (b'', None)
            with self.subTest(phase=phase), patch.object(fixture.subprocess, 'Popen', return_value=server), \
                    patch.object(fixture, 'await_startup', side_effect=RuntimeError('startup') if phase == 'startup' else None, return_value=''), \
                    patch.object(fixture.os, 'killpg') as kill, patch('sys.stdout', new_callable=io.StringIO):
                def exercise():
                    with fixture.running_server(['httpd']):
                        if phase == 'test':
                            raise ValueError('test failure')
                if phase == 'success':
                    exercise()
                else:
                    with self.assertRaises(RuntimeError if phase == 'startup' else ValueError):
                        exercise()
                kill.assert_called_once_with(server.pid, signal.SIGTERM)
                server.communicate.assert_called_once_with(timeout=20)

    def test_shutdown_timeout_kills_and_reaps(self):
        server = Mock(pid=1234)
        server.communicate.side_effect = [subprocess.TimeoutExpired('httpd', 20), (b'', None)]
        with patch.object(fixture.subprocess, 'Popen', return_value=server), \
                patch.object(fixture, 'await_startup', return_value=''), \
                patch.object(fixture.os, 'killpg') as kill, patch('sys.stdout', new_callable=io.StringIO):
            with self.assertRaises(subprocess.TimeoutExpired):
                with fixture.running_server(['httpd']):
                    pass
            self.assertEqual([signal.SIGTERM, signal.SIGKILL], [call.args[1] for call in kill.call_args_list])
            self.assertEqual(2, server.communicate.call_count)


if __name__ == '__main__':
    unittest.main()
