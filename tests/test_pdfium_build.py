# Copyright 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Exercise distribution tool/resource discovery without bootstrapping GN."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

loader = importlib.util.spec_from_file_location(
    "pdfium_build", Path(__file__).resolve().parents[1] / "dependencies/pdfium-rpm-build.py")
pdfium = importlib.util.module_from_spec(loader)
loader.loader.exec_module(pdfium)


class PdfiumBuildTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.enterContext(contextlib.chdir(self.root))
        for name in ("build/config", "build/linux/unbundle", "third_party/icu", "third_party/brotli",
                     "gn-src/out", "distro/bin", "distro/lib/clang/21/include", "distro/lib/runtime"):
            Path(name).mkdir(parents=True, exist_ok=True)
        for tool in ("clang", "clang++", "ld.lld", "llvm-ar", "llvm-nm", "llvm-readelf",
                     "llvm-objcopy", "llvm-strip"):
            Path("distro/bin", tool).touch()
        self.resource = self.root / "distro/lib/clang/21"
        (self.resource / "include/stddef.h").touch()
        self.runtime = self.root / "distro/lib/runtime/libclang_rt.builtins.a"
        self.runtime.touch()
        for library in ("icu", "brotli"):
            Path("build/linux/unbundle", library + ".gn").write_text(library)
        self.compiler_version = "21.1.8"
        self.enterContext(patch.dict(os.environ, {"CFLAGS": "-O2 -g", "CXXFLAGS": "-O2 -g",
                                                 "LDFLAGS": "-Wl,-z,relro"}, clear=True))
        self.which = self.enterContext(patch.object(pdfium.shutil, "which", side_effect=self.find))
        self.enterContext(patch.object(pdfium, "output", side_effect=self.output))
        self.run = self.enterContext(patch.object(pdfium.subprocess, "run",
                                                 return_value=subprocess.CompletedProcess([], 0)))
        self.enterContext(patch.object(pdfium.platform, "machine", return_value="x86_64"))

    def find(self, name):
        path = self.root / "distro/bin" / name.removesuffix("-21")
        return str(path) if path.is_file() else None

    def output(self, compiler, option):
        if option == "-dumpversion":
            return self.compiler_version
        if option == "--print-resource-dir":
            return str(self.resource)
        name = option.removeprefix("--print-file-name=")
        return str(self.runtime) if name == self.runtime.name else name

    def configure(self):
        with contextlib.redirect_stdout(io.StringIO()):
            pdfium.configure(2)

    def variables(self):
        return {key: json.loads(value) for key, value in (
            line.split(" = ", 1) for line in Path("rpm/buildflags.gni").read_text().splitlines())}

    def test_distribution_resource_path_flags_and_gn_bootstrap(self):
        self.configure()
        variables = self.variables()
        self.assertIn("-resource-dir=" + str(self.resource), variables["qore_cppflags"])
        self.assertEqual(variables["qore_common_cflags"], ["-O2", "-g"])
        self.assertEqual(variables["qore_cflags"], [])
        self.assertEqual(variables["qore_ldflags"], ["-Wl,-z,relro"])
        self.assertEqual(variables["qore_compiler_rt_dir"], str(self.runtime.parent))
        self.assertEqual(variables["qore_compiler_rt_suffix"], "")
        self.assertEqual(Path("third_party/icu/BUILD.gn").read_text(), "icu")
        commands = [call.args[0] for call in self.run.call_args_list]
        self.assertIn("--no-static-libstdc++", commands[-3])
        self.assertIn('target_cpu="x64"', commands[-1][-1])
        self.assertIn('treat_warnings_as_errors=true', commands[-1][-1])
        self.assertIn('use_dwarf5=true', commands[-1][-1])
        self.assertIn('pdf_use_partition_alloc=false', commands[-1][-1])
        self.assertIn('pdf_bundle_freetype=false', commands[-1][-1])
        self.assertIn('use_system_freetype=true', commands[-1][-1])

    def test_bundled_freetype_requires_the_pinned_source(self):
        with self.assertRaisesRegex(RuntimeError, "pinned bundled FreeType"):
            pdfium.configure(2, bundled_freetype=True)
        self.run.assert_not_called()

    def test_bootstrap_preserves_lto_and_uses_the_selected_llvm_linker(self):
        with patch.dict(os.environ, {"CFLAGS": "-O2 -g -flto=auto",
                                     "CXXFLAGS": "-O2 -g -flto=auto",
                                     "LDFLAGS": "-flto=auto -Wl,-z,relro"}):
            self.configure()
        bootstrap = next(call for call in self.run.call_args_list
                         if call.args[0][:2] == ["python3", "build/gen.py"])
        env = bootstrap.kwargs["env"]
        self.assertEqual(env["AR"], str(self.root / "rpm/toolchain/bin/llvm-ar"))
        self.assertEqual(env["CXXFLAGS"], "-O2 -g -flto=auto")
        self.assertEqual(env["LDFLAGS"].split(), ["-flto=auto", "-Wl,-z,relro",
                         "--ld-path=" + str(self.root / "rpm/toolchain/bin/ld.lld")])
        self.assertIn("-flto=auto", self.variables()["qore_common_cflags"])
        self.assertEqual(self.variables()["qore_ldflags"], ["-flto=auto", "-Wl,-z,relro"])

    def test_bundled_freetype_disables_the_system_library(self):
        header = Path("third_party/freetype/src/include/freetype/freetype.h")
        header.parent.mkdir(parents=True)
        header.touch()
        with contextlib.redirect_stdout(io.StringIO()):
            pdfium.configure(2, bundled_freetype=True)
        arguments = self.run.call_args_list[-1].args[0][-1]
        self.assertIn('pdf_bundle_freetype=true', arguments)
        self.assertIn('use_system_freetype=false', arguments)

    def test_arm64_versioned_tool_layout_and_suffixed_runtime(self):
        self.runtime = self.runtime.with_name("libclang_rt.builtins-aarch64.a")
        self.runtime.touch()
        with patch.object(pdfium.platform, "machine", return_value="aarch64"):
            self.configure()
        self.assertEqual(self.variables()["qore_compiler_rt_suffix"], "-aarch64")
        self.assertIn('target_cpu="arm64"', self.run.call_args_list[-1].args[0][-1])
        self.assertEqual(Path("rpm/toolchain/bin/clang++").resolve(), self.root / "distro/bin/clang++")

    def test_language_specific_flags_remain_separate(self):
        with patch.dict(os.environ, {"CFLAGS": "-O2 -Wstrict-prototypes", "CXXFLAGS": "-O2 -std=c++20"}):
            self.configure()
        variables = self.variables()
        self.assertEqual(variables["qore_common_cflags"], ["-O2"])
        self.assertEqual(variables["qore_cflags"], ["-Wstrict-prototypes"])
        self.assertEqual(variables["qore_cxxflags"], ["-std=c++20"])

    def test_reconfigure_preserves_matching_tools(self):
        self.configure()
        before = Path("rpm/buildflags.gni").read_bytes()
        self.configure()
        self.assertEqual(Path("rpm/buildflags.gni").read_bytes(), before)

    def test_missing_and_old_compiler_are_rejected(self):
        with patch.object(pdfium.shutil, "which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "Clang 21"):
                self.configure()
        self.compiler_version = "20.0.0"
        with self.assertRaisesRegex(RuntimeError, "too old"):
            self.configure()
        self.run.assert_not_called()

    def test_missing_resource_headers_are_rejected(self):
        (self.resource / "include/stddef.h").unlink()
        with self.assertRaisesRegex(RuntimeError, "resource headers"):
            self.configure()
        self.run.assert_not_called()

    def test_missing_runtime_or_tools_are_rejected(self):
        self.runtime.unlink()
        with self.assertRaisesRegex(RuntimeError, "builtins archive"):
            self.configure()
        self.runtime.touch()
        Path("distro/bin/llvm-ar").unlink()
        with self.assertRaisesRegex(RuntimeError, "Missing distribution tool: llvm-ar"):
            self.configure()
        self.run.assert_not_called()

    def test_existing_foreign_tool_is_not_overwritten(self):
        Path("rpm/toolchain/bin").mkdir(parents=True)
        path = Path("rpm/toolchain/bin/clang")
        path.write_text("unrelated file")
        with self.assertRaises(FileExistsError):
            self.configure()
        self.assertEqual(path.read_text(), "unrelated file")
        self.run.assert_not_called()

    def test_unsupported_compiler_flags_are_not_passed_to_gn(self):
        def run(command, **kwargs):
            return subprocess.CompletedProcess(command, 1 if "-x" in command else 0)
        self.run.side_effect = run
        self.configure()
        self.assertEqual(self.variables()["qore_extra_cflags"], [])
        self.assertIn('treat_warnings_as_errors=true', self.run.call_args_list[-1].args[0][-1])

    def test_build_tool_failure_propagates(self):
        def run(command, **kwargs):
            if command[0] == "ninja":
                raise subprocess.CalledProcessError(7, command)
            return subprocess.CompletedProcess(command, 0)
        self.run.side_effect = run
        with self.assertRaises(subprocess.CalledProcessError):
            self.configure()

    def test_allocator_policy_uses_the_declared_pdfium_argument(self):
        self.configure()
        command = self.run.call_args_list[-1].args[0]
        self.assertIn("--fail-on-unused-args", command)
        arguments = command[-1].removeprefix("--args=").split()
        self.assertIn("pdf_use_partition_alloc=false", arguments)
        names = {argument.split("=", 1)[0] for argument in arguments}
        self.assertNotIn("use_allocator_shim", names)
        self.assertNotIn("use_partition_alloc_as_malloc", names)

    def test_gn_argument_error_aborts_configuration(self):
        def run(command, **kwargs):
            if command[:2] == ["gn-src/out/gn", "gen"]:
                self.assertTrue(kwargs["check"])
                raise subprocess.CalledProcessError(1, command, stderr="Build argument has no effect")
            return subprocess.CompletedProcess(command, 0)
        self.run.side_effect = run
        with self.assertRaises(subprocess.CalledProcessError) as error:
            self.configure()
        self.assertEqual(error.exception.returncode, 1)
        self.assertEqual(error.exception.stderr, "Build argument has no effect")


if __name__ == "__main__":
    unittest.main()
