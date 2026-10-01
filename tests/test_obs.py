# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
import importlib.util
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.util.spec_from_file_location("obs_tools", ROOT / "tools/obs.py")
obs = importlib.util.module_from_spec(loader)
loader.loader.exec_module(obs)


class ObsTest(unittest.TestCase):
    def test_osc_permits_one_source_download_attempt_and_propagates_errors(self):
        with patch.object(obs.subprocess, "run", return_value="result") as run:
            self.assertEqual("result", obs.osc("checkout", "project", "package"))
            command = run.call_args.args[0]
            self.assertEqual("http_retries=1", command[command.index("--setopt") + 1])
            self.assertTrue(run.call_args.kwargs["check"])
        with patch.object(obs.subprocess, "run", side_effect=subprocess.CalledProcessError(1, command)):
            with self.assertRaises(subprocess.CalledProcessError):
                obs.osc("checkout", "project", "package")

    def test_project_templates_are_disabled_and_owned(self):
        for channel in ("testing", "stable"):
            self.assertEqual(obs.validate_project(ROOT / f"obs/project-{channel}.xml"), obs.PREFIX + channel)

    def test_projects_outside_namespace_and_enabled_publication_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "project.xml"
            for text in [
                '<project name="home:another-user"/>',
                '<project name="home:davidnichols:qore:testing"><person userid="davidnichols" role="maintainer"/>'
                '<build><disable/></build><publish><enable/></publish></project>',
            ]:
                path.write_text(text)
                with self.assertRaises(ValueError):
                    obs.validate_project(path)

    def test_candidates_and_unpinned_sources_cannot_be_uploaded(self):
        for manifest in [{"candidate": True}, {"packaging_overlay": {"file": "hash"}},
                         {"name": "qore", "commit": "HEAD"}]:
            with self.subTest(manifest=manifest), patch.object(obs.builder, "verify_bundle", return_value=manifest):
                with self.assertRaises(ValueError):
                    obs.validate_upload(obs.PREFIX + "testing", Path("unused"))

    def test_direct_stable_upload_is_rejected_before_reading_source(self):
        with patch.object(obs.builder, "verify_bundle", side_effect=AssertionError("source read")):
            with self.assertRaisesRegex(ValueError, "promotion"):
                obs.validate_upload(obs.PREFIX + "stable", Path("unused"))

    def test_authentication_failure_never_creates_project(self):
        with patch.object(obs, "osc", side_effect=RuntimeError("401")) as call:
            with self.assertRaisesRegex(RuntimeError, "401"):
                obs.create_project(ROOT / "obs/project-testing.xml", True)
            self.assertEqual(call.call_count, 1)
            self.assertNotIn("PUT", call.call_args.args)

    def make_bundle(self, directory, version):
        directory.mkdir()
        files = {"qore.spec": f"Name: qore\nVersion: {version}\n".encode(),
                 f"qore-{version}.tar.xz": f"source fixture {version}".encode()}
        for name, content in files.items():
            (directory / name).write_bytes(content)
        manifest = {"schema": 1, "name": "qore", "spec": "qore.spec",
                    "commit": "1" * 40, "source_date_epoch": 1,
                    "sources": {name: hashlib.sha256(content).hexdigest()
                                for name, content in files.items()}}
        (directory / "source-manifest.json").write_text(json.dumps(manifest))

    def simulate_upload(self, existing, source):
        operations = []
        committed = {}

        def fake_osc(*args, **kwargs):
            operations.append(args)
            if args[0] == "checkout":
                shutil.copytree(existing, Path(args[2]))
                (Path(args[2]) / ".osc").mkdir()
            elif args[0] == "remove":
                (kwargs["cwd"] / args[1]).unlink()
            elif args[0] == "commit":
                committed.update({p.name: p.read_bytes() for p in kwargs["cwd"].iterdir() if p.is_file()})

        with patch.object(obs, "osc", side_effect=fake_osc), patch("sys.stdout", new_callable=io.StringIO):
            obs.upload(obs.PREFIX + "testing", source, True)
        return operations, committed

    def test_upload_replaces_only_verified_previous_version_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            old, new = Path(tmp) / "old", Path(tmp) / "new"
            self.make_bundle(old, "1")
            self.make_bundle(new, "2")
            calls, committed = self.simulate_upload(old, new)
            self.assertIn(("remove", "qore-1.tar.xz"), calls)
            self.assertEqual(committed, {p.name: p.read_bytes() for p in new.iterdir()})
            self.assertEqual(calls[-1], ("commit", "-m", "Pinned source " + "1" * 40))

    def test_upload_preserves_unmanaged_obs_services(self):
        with tempfile.TemporaryDirectory() as tmp:
            old, new = Path(tmp) / "old", Path(tmp) / "new"
            self.make_bundle(old, "1")
            self.make_bundle(new, "2")
            (old / "_service").write_text("<services/>")
            with self.assertRaisesRegex(ValueError, "Unexpected existing OBS sources: _service"):
                self.simulate_upload(old, new)

    def test_upload_rejects_tampered_previous_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            old, new = Path(tmp) / "old", Path(tmp) / "new"
            self.make_bundle(old, "1")
            self.make_bundle(new, "2")
            (old / "qore-1.tar.xz").write_bytes(b"changed outside the pinned bundle")
            with self.assertRaises(ValueError):
                self.simulate_upload(old, new)

    def test_dry_run_never_contacts_obs(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "new"
            self.make_bundle(source, "2")
            with patch.object(obs, "osc", side_effect=AssertionError("remote call")), \
                    patch("sys.stdout", new_callable=io.StringIO) as output:
                obs.upload(obs.PREFIX + "testing", source, False)
            self.assertIn('"qore-2.tar.xz"', output.getvalue())
