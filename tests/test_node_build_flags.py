# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
import importlib.util
from pathlib import Path
import shlex
import subprocess
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "dependencies/nodejs24-build-flags.py"
loader = importlib.util.spec_from_file_location("node_build_flags", SOURCE)
flags = importlib.util.module_from_spec(loader)
loader.loader.exec_module(flags)


class NodeBuildFlagsTest(unittest.TestCase):
    def test_distribution_hardening_is_preserved(self):
        original = "-O2 -Wall -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=3 -fstack-protector-strong -funwind-tables -fasynchronous-unwind-tables -fstack-clash-protection -Werror=return-type -flto=auto -g"
        result = flags.build_environment(original, "-Wl,-z,relro -flto=auto -Wl,-z,now")
        self.assertEqual(shlex.split(result["CFLAGS"]), [x for x in original.split() if x != "-flto=auto"])
        self.assertEqual(shlex.split(result["CXXFLAGS"]), shlex.split(result["CFLAGS"]) + ["-Wno-error=return-type"])
        self.assertEqual(result["LDFLAGS"], "-Wl,-z,relro -Wl,-z,now")
        self.assertEqual(result["NODE_LTO_OPTION"], "--enable-lto")

    def test_supported_modes_and_adjacent_repeated_flags(self):
        for mode in ("-flto", "-flto=auto", "-flto=jobserver", "-flto=4"):
            result = flags.build_environment(mode + " " + mode + " -O2", mode)
            self.assertEqual(result["CFLAGS"], "-O2")
            self.assertEqual(result["LDFLAGS"], "")
            self.assertEqual(result["NODE_LTO_OPTION"], "--enable-lto")

    def test_absent_or_disabled_lto_stays_disabled(self):
        for options in ("", "-O2", "-flto -fno-lto"):
            result = flags.build_environment(options, "")
            self.assertEqual(result["NODE_LTO_OPTION"], "")
        enabled = flags.build_environment("-fno-lto -flto", "")
        self.assertEqual(enabled["NODE_LTO_OPTION"], "--enable-lto")
        self.assertEqual(enabled["CFLAGS"], "")

    def test_conflicts_and_unknown_modes_fail(self):
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            flags.build_environment("-flto", "-fno-lto")
        for mode in ("thin", "0", "-1", "", "auto,other"):
            with self.assertRaisesRegex(ValueError, "Unsupported"):
                flags.build_environment("-flto=" + mode, "")

    def test_generated_environment_round_trips_without_shell_execution(self):
        options = "-O2 '-DNAME=a b' '-DLITERAL=$(false)`false`' -flto=auto"
        generated = subprocess.check_output(["python3", str(SOURCE), "--cflags=" + options,
                                             "--ldflags=-Wl,-z,now"], text=True)
        script = generated + '\npython3 -c \'import json,os; print(json.dumps({k:os.environ[k] for k in ["CFLAGS","CXXFLAGS","LDFLAGS","NODE_LTO_OPTION"]}))\''
        import json
        restored = json.loads(subprocess.check_output(["sh", "-eu", "-c", script], text=True))
        self.assertEqual(restored, flags.build_environment(options, "-Wl,-z,now"))
        self.assertEqual(shlex.split(restored["CFLAGS"]), shlex.split(options)[:-1])


if __name__ == "__main__":
    unittest.main()
