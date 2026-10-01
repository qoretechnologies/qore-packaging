#!/usr/bin/python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Check atomic fixture status publication without unrelated filesystem I/O."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


loader = importlib.util.spec_from_file_location("proc_ctl", sys.argv.pop(1))
proc_ctl = importlib.util.module_from_spec(loader)
loader.loader.exec_module(proc_ctl)


class PublicationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.path = self.root / "exit.json"

    def test_creation_and_update_publish_complete_files_without_global_sync(self):
        with patch.object(proc_ctl.os, "sync", side_effect=AssertionError("global filesystem flush")):
            proc_ctl.write_text(self.path, '{"exit": 0}')
            self.assertEqual(self.path.read_text(), '{"exit": 0}')
            real_replace = Path.replace

            def replace(temporary, destination):
                self.assertEqual(destination.read_text(), '{"exit": 0}')
                self.assertEqual(temporary.read_text(), '{"exit": 1}')
                return real_replace(temporary, destination)

            with patch.object(Path, "replace", replace):
                proc_ctl.write_text(self.path, '{"exit": 1}')
            self.assertEqual(self.path.read_text(), '{"exit": 1}')
        self.assertEqual(list(self.root.iterdir()), [self.path])

    def test_replace_failure_preserves_previous_result_and_cleans_temporary(self):
        self.path.write_text("previous")
        with patch.object(Path, "replace", side_effect=OSError("replace failed")):
            with self.assertRaisesRegex(OSError, "replace failed"):
                proc_ctl.write_text(self.path, "new")
        self.assertEqual(self.path.read_text(), "previous")
        self.assertEqual(list(self.root.iterdir()), [self.path])

    def test_partial_write_failure_preserves_previous_result_and_cleans_temporary(self):
        self.path.write_text("previous")

        def partial_write(path, content):
            path.write_bytes(b"partial")
            raise OSError("write failed")

        with patch.object(Path, "write_text", partial_write):
            with self.assertRaisesRegex(OSError, "write failed"):
                proc_ctl.write_text(self.path, "new")
        self.assertEqual(self.path.read_text(), "previous")
        self.assertEqual(list(self.root.iterdir()), [self.path])


if __name__ == "__main__":
    unittest.main()
