# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Exercise the actual generator, RPM classification and dependency solver."""
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.util.spec_from_file_location("qore_aot_identity", ROOT / "qore_aot_identity.py")
identity = importlib.util.module_from_spec(loader)
loader.loader.exec_module(identity)
DIGEST = "a01b1" + "c" * 59
MISMATCH = "a1b01" + "c" * 59


class IdentityRpmTest(unittest.TestCase):
    def test_rpm_refuses_old_or_malformed_aot_artifacts(self):
        for invalid in ("old", "digest"):
            with self.subTest(invalid=invalid), tempfile.TemporaryDirectory() as directory:
                self.build_packages(Path(directory), invalid)

    def test_runtime_source_retains_the_referenced_identity_after_stripping(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            include = root / "include/qore/intern"
            include.mkdir(parents=True)
            (include / "qore_aot_runtime_identity.h").write_text(f'#define QORE_AOT_RUNTIME_IDENTITY "{DIGEST}"\n')
            library = root / "libqore.so.20.0.0"
            result = subprocess.run(["c++", "-O2", "-g", "-fPIC", "-shared", "-Wall", "-Wextra", "-Werror",
                                     "-I" + str(root / "include"),
                                     str(ROOT.parent / "lib/qore_aot_runtime_identity.cpp"), "-o", str(library)],
                                    capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual("", result.stderr)
            isa = subprocess.check_output(["rpm", "--eval", "%{?_isa}"], text=True).strip()
            for stripped in (False, True):
                if stripped:
                    subprocess.run(["strip", "--strip-unneeded", str(library)], check=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.assertEqual([identity.capability(DIGEST, isa)], identity.dependencies(library, "provides", isa))

    def test_native_rpm_provides_requires_and_exact_solver(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packages = self.build_packages(root)
            isa = subprocess.check_output(["rpm", "--eval", "%{?_isa}"], text=True).strip()
            expected = identity.capability(DIGEST, isa)
            mismatch = identity.capability(MISMATCH, isa)
            for name, tag, value in [("qore-aot-probe", "--provides", expected),
                                     ("qore-aot-probe-module", "--requires", expected),
                                     ("qore-aot-probe-mismatch", "--requires", mismatch)]:
                output = subprocess.check_output(["rpm", "-qp", tag, str(packages[name])], text=True).splitlines()
                self.assertEqual([value], [line for line in output if line.startswith("qore-aot-runtime(")])
            output = subprocess.check_output(["rpm", "-qp", "--requires", str(packages["qore-aot-probe-native"])],
                                             text=True)
            self.assertNotIn("qore-aot-runtime(", output)
            database = root / "rpmdb"
            subprocess.run(["rpm", "--dbpath", str(database), "--initdb"], check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # Register the fixture provider only; never modify the host database.
            result = subprocess.run(["rpm", "--dbpath", str(database), "-i", "--justdb",
                                     str(packages["qore-aot-probe"])], capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            for name, succeeds in [("qore-aot-probe-module", True), ("qore-aot-probe-native", True),
                                   ("qore-aot-probe-mismatch", False)]:
                result = subprocess.run(["rpm", "--dbpath", str(database), "-i", "--test", str(packages[name])],
                                        capture_output=True, text=True)
                if succeeds:
                    self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                    self.assertNotIn("warning:", result.stderr.lower())
                else:
                    self.assertNotEqual(0, result.returncode)
                    self.assertIn(mismatch + " is needed by", result.stderr)

            # An installed AOT consumer must prevent an incompatible runtime
            # upgrade, while a paired module rebuild permits the transaction.
            subprocess.run(["rpm", "--dbpath", str(database), "-i", "--justdb",
                            str(packages["qore-aot-probe-module"])], check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stable_root, changed_root = root / "stable", root / "changed"
            stable_root.mkdir()
            changed_root.mkdir()
            stable = self.build_packages(stable_root, version="2.0")
            changed = self.build_packages(changed_root, version="3.0", runtime_digest=MISMATCH,
                                          module_digest=MISMATCH)
            cases = [([str(stable["qore-aot-probe"])], True),
                     ([str(changed["qore-aot-probe"])], False),
                     ([str(changed["qore-aot-probe"]), str(changed["qore-aot-probe-module"])], True)]
            for payloads, succeeds in cases:
                result = subprocess.run(["rpm", "--dbpath", str(database), "-U", "--test", *payloads],
                                        capture_output=True, text=True)
                if succeeds:
                    self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                    self.assertNotIn("warning:", result.stderr.lower())
                else:
                    self.assertNotEqual(0, result.returncode)
                    self.assertIn(expected + " is needed by", result.stderr)
            for names, succeeds in [(["qore-aot-probe"], False),
                                     (["qore-aot-probe", "qore-aot-probe-module"], True)]:
                result = subprocess.run(["rpm", "--dbpath", str(database), "-e", "--test", *names],
                                        capture_output=True, text=True)
                self.assertEqual(succeeds, result.returncode == 0, result.stdout + result.stderr)
                if not succeeds:
                    self.assertIn(expected + " is needed by", result.stderr)

    def build_packages(self, root, invalid=None, version="1.0", runtime_digest=DIGEST, module_digest=DIGEST):
        for directory in ("SOURCES", "SPECS", "attrs"):
            (root / directory).mkdir()
        system_attrs = Path(subprocess.check_output(["rpm", "--eval", "%{_fileattrsdir}"], text=True).strip())
        for path in system_attrs.glob("*.attr"):
            if path.name not in ("qore.attr", "qoreaot.attr"):
                (root / "attrs" / path.name).symlink_to(path)
        other_digest = MISMATCH if module_digest != MISMATCH else DIGEST
        for name, role, digest in [("runtime", "runtime", runtime_digest), ("module", "module", module_digest),
                                   ("mismatch", "module", other_digest), ("native", None, DIGEST)]:
            section = f'__attribute__((section(".qore.aot.{role}.v1"), aligned(1)))' if role else ""
            (root / "SOURCES" / (name + ".c")).write_text(
                f'static const char identity[] {section} = "{digest}";\n'
                'const char* package_identity(void) { return identity; }\n')
        if invalid == "old":
            (root / "SOURCES/module.c").write_text(
                'extern void qore_aot_fill_module_desc(void);\n'
                'void old_descriptor(void) { qore_aot_fill_module_desc(); }\n')
        elif invalid == "digest":
            path = root / "SOURCES/module.c"
            path.write_text(path.read_text().replace(DIGEST, "g" * 64))
        recipe = root / "SPECS/probe.spec"
        recipe.write_text(f'''%{{load:{ROOT}/qoreaot.attr}}
%{{load:{ROOT}/macros.qore}}
%global qore_rpm_helper {ROOT}/preserve-aot-metadata.py
%global qore_aot_identity_helper {ROOT}/qore_aot_identity.py
%qore_enable_aot_post
%global _local_file_attrs qoreaot
%define __qoreaot_provides /usr/bin/python3 {ROOT}/qore_aot_identity.py provides "%{{?_isa}}"
%define __qoreaot_requires /usr/bin/python3 {ROOT}/qore_aot_identity.py requires "%{{?_isa}}"
%global debug_package %{{nil}}
Name: qore-aot-probe
Version: {version}
Release: 1
Summary: AOT dependency resolution fixture
License: MIT
Source0: runtime.c
Source1: module.c
Source2: mismatch.c
Source3: native.c
%description
Runtime identity capability fixture.
%package module
Summary: Matching AOT identity fixture
%description module
Requires the runtime's exact compiled-code identity.
%package mismatch
Summary: Mismatched AOT identity fixture
%description mismatch
Requires an identity that compares equal as a version but differs as a name.
%package native
Summary: Native module fixture
%description native
A native-only module must not require an AOT runtime identity.
%prep
%setup -q -c -T
cp %{{SOURCE0}} %{{SOURCE1}} %{{SOURCE2}} %{{SOURCE3}} .
%build
# A freestanding fixture lets an empty RPM database exercise this one contract
# without importing the host's libc/loader package set. Real qcc artifacts and
# normal distribution link flags are qualified separately.
for part in runtime module mismatch native; do
    gcc -O2 -fPIC -shared -nostdlib -Wl,--build-id,--hash-style=sysv -o "$part.so" "$part.c"
done
%install
install -Dm755 runtime.so %{{buildroot}}%{{_libdir}}/libqore.so.20.0.0
install -Dm755 module.so %{{buildroot}}%{{_libdir}}/qore-modules/Probe.qmod
install -Dm755 mismatch.so %{{buildroot}}%{{_libdir}}/qore-modules/Mismatch.qmod
install -Dm755 native.so %{{buildroot}}%{{_libdir}}/qore-modules/Native.qmod
%files
%{{_libdir}}/libqore.so.20.0.0
%files module
%{{_libdir}}/qore-modules/Probe.qmod
%files mismatch
%{{_libdir}}/qore-modules/Mismatch.qmod
%files native
%{{_libdir}}/qore-modules/Native.qmod
%changelog
* Thu Oct 08 2026 Qore Technologies <info@qore.org> - 1.0-1
- Exercise exact AOT identity resolution.
''')
        result = subprocess.run(["rpmbuild", "-bb", "--define", f"_topdir {root}",
                                 "--define", f"_fileattrsdir {root / 'attrs'}", "--define", "_smp_build_ncpus 1",
                                 "--define", "_buildhost qore-rpm-builder", str(recipe)],
                                env=dict(os.environ, SOURCE_DATE_EPOCH="1791417600"),
                                capture_output=True, text=True)
        if invalid:
            self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
            expected = "rebuild with the current SDK" if invalid == "old" else "Invalid or inconsistent"
            self.assertIn(expected, result.stderr)
            self.assertFalse(list((root / "RPMS").rglob("*.rpm")), result.stdout)
            return {}
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertNotRegex(result.stdout + result.stderr, r"(?i)\bwarning:")
        packages = list((root / "RPMS").rglob("*.rpm"))
        self.assertEqual(4, len(packages), result.stdout)
        return {subprocess.check_output(["rpm", "-qp", "--qf", "%{NAME}", str(path)], text=True): path
                for path in packages}


if __name__ == "__main__":
    unittest.main()
