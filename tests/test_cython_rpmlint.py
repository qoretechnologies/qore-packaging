# Copyright 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
import re
from pathlib import Path
import unittest


class CythonLintScopeTest(unittest.TestCase):
    def setUp(self):
        self.patterns = []
        source = Path(__file__).resolve().parents[1] / "dependencies/python-Cython-rpmlintrc"
        # rpmlint 2 extracts literal pattern text; it does not evaluate Python
        # string escapes. Require raw strings to agree with both interpretations.
        literals = re.findall(r"^addFilter\(r'(.*)'\)$", source.read_text(), re.M)
        exec(compile(source.read_text(), str(source), "exec"),
             {"addFilter": lambda pattern: self.patterns.append(re.compile(pattern))})
        self.assertEqual(literals, [pattern.pattern for pattern in self.patterns])

    def matches(self, message):
        return any(pattern.search(message) for pattern in self.patterns)

    def test_only_exact_reviewed_package_and_template_paths_match(self):
        self.assertEqual(len(self.patterns), 32)
        for arch in ("x86_64", "aarch64"):
            prefix = "python313-Cython." + arch + ": E: "
            template = ("devel-file-in-non-devel-package "
                        "/usr/lib64/python3.13/site-packages/Cython/Utility/Buffer.c")
            self.assertTrue(self.matches(prefix + template))
            self.assertTrue(self.matches(prefix + "devel-dependency python313-devel"))
            for changed in (
                    template.replace("Buffer.c", "NewUnreviewed.c"),
                    template.replace("Cython/Utility", "another/Utility"),
                    template.replace("python3.13", "python3.14"),
                    template + ".unexpected", "devel-dependency unrelated-devel"):
                self.assertFalse(self.matches(prefix + changed), changed)
            self.assertFalse(self.matches(prefix.replace("Cython", "another") + template))

    def test_actual_packaging_errors_are_never_hidden(self):
        for message in (
                "script-without-shebang /usr/lib64/python3.13/site-packages/Cython/Build/Cythonize.py",
                "no-dependency-on python-base 3.13", "non-standard-executable-perm /usr/bin/cython 0777",
                "dangling-symlink /usr/bin/cython /usr/bin/alts", "binary-or-shlib-defines-rpath /usr/bin/cython"):
            self.assertFalse(self.matches("python313-Cython.x86_64: E: " + message), message)


if __name__ == "__main__":
    unittest.main()
