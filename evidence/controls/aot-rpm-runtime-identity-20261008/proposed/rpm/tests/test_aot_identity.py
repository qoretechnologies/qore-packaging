# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Binary-format, failure and real ELF controls for AOT RPM dependencies."""
import importlib.util
import io
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("qore_aot_identity", ROOT / "qore_aot_identity.py")
identity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(identity)
DIGEST = "0123456789abcdef" * 4


def elf(entries=(), bits=64, endian="<", extended=False):
    """Construct ELF shared objects with independently controlled section data."""
    header = struct.Struct(endian + ("HHIIIIIHHHHHH" if bits == 32 else "HHIQQQIHHHHHH"))
    section = struct.Struct(endian + ("IIIIIIIIII" if bits == 32 else "IIQQQQIIQQ"))
    names = b"\x00.shstrtab\x00" + b"".join(name + b"\x00" for name, _, _, _ in entries)
    body = bytearray(16 + header.size)
    body[:16] = b"\x7fELF" + bytes((1 if bits == 32 else 2, 1 if endian == "<" else 2, 1)) + bytes(9)
    names_offset = len(body)
    body.extend(names)
    sections = [(0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                (1, 3, 0, 0, names_offset, len(names), 0, 0, 1, 0)]
    name_offset = len(b"\x00.shstrtab\x00")
    for name, kind, flags, payload in entries:
        sections.append((name_offset, kind, flags, 0, len(body), len(payload), 0, 0, 1, 0))
        body.extend(payload)
        name_offset += len(name) + 1
    table_offset = len(body)
    if extended:
        sections[0] = (0, 0, 0, 0, 0, len(sections), 1, 0, 0, 0)
    body[16:16 + header.size] = header.pack(3, 62, 1, 0, 0, table_offset, 0, 16 + header.size,
                                            0, 0, section.size, 0 if extended else len(sections),
                                            0xffff if extended else 1)
    for item in sections:
        body.extend(section.pack(*item))
    return bytes(body)


def record(role="module", digest=DIGEST):
    return f".qore.aot.{role}.v1".encode(), 1, 2, digest.encode() + b"\x00"


class IdentityTest(unittest.TestCase):
    def test_roles_classes_byte_orders_and_extended_tables(self):
        for role in ("runtime", "module"):
            for bits in (32, 64):
                for endian in ("<", ">"):
                    for extended in (False, True):
                        with self.subTest(role=role, bits=bits, endian=endian, extended=extended):
                            self.assertEqual((role, DIGEST), identity.read_identity(io.BytesIO(
                                elf([record(role)], bits, endian, extended))))

    def test_every_truncated_prefix_fails(self):
        for bits in (32, 64):
            for endian in ("<", ">"):
                data = elf([record()], bits, endian)
                for end in range(len(data)):
                    with self.subTest(bits=bits, endian=endian, end=end), self.assertRaises(ValueError):
                        identity.read_identity(io.BytesIO(data[:end]))

    def test_native_only_module_and_missing_aot_identity(self):
        self.assertIsNone(identity.read_identity(io.BytesIO(elf())))
        for name in (b"qore_aot_fill_module_desc", b"qore_aot_fill_module_runtime_identity"):
            table = (b".dynstr", 3, 2, b"\x00" + name + b"\x00")
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "rebuild"):
                identity.read_identity(io.BytesIO(elf([table])))
            self.assertEqual(("runtime", DIGEST), identity.read_identity(io.BytesIO(elf([table, record("runtime")]))))
        for value in (b"\x00prefix_qore_aot_fill_module_desc\x00", b"\x00qore_aot_fill_module_desc_suffix\x00"):
            self.assertIsNone(identity.read_identity(io.BytesIO(elf([(b".dynstr", 3, 2, value)]))))

    def test_duplicate_unknown_or_invalid_records_fail(self):
        variants = [[record(), record()], [record(), record("runtime")],
                    [(b".qore.aot.module.v2", 1, 2, DIGEST.encode() + b"\x00")]]
        for kind in (0, 3, 8):
            variants.append([(record()[0], kind, 2, record()[3])])
        for flags in (0, 1, 3, 6, 0x802):
            variants.append([(record()[0], 1, flags, record()[3])])
        for data in (b"", b"a" * 64, b"a" * 65, b"A" * 64 + b"\x00", b"g" * 64 + b"\x00",
                     b"a\x00" + b"a" * 62 + b"\x00", b"a" * 65 + b"\x00"):
            variants.append([(record()[0], 1, 2, data)])
        for entries in variants:
            with self.subTest(entries=entries), self.assertRaises(ValueError):
                identity.read_identity(io.BytesIO(elf(entries)))

    def test_linked_modules_require_a_single_consistent_identity(self):
        name, kind, flags, value = record()
        self.assertEqual(("module", DIGEST), identity.read_identity(io.BytesIO(
            elf([(name, kind, flags, value * 3)]))))
        with self.assertRaisesRegex(ValueError, "inconsistent"):
            identity.read_identity(io.BytesIO(elf([(name, kind, flags, value + b"a" * 64 + b"\x00")])))

    def test_invalid_headers_and_section_offsets_fail(self):
        data = elf([record()])
        variants = []
        for offset, value in ((0, 0), (4, 0), (5, 0), (6, 2), (16, 2), (20, 2), (52, 0),
                              (58, 0), (60, 1), (62, 0)):
            changed = bytearray(data)
            changed[offset] = value
            variants.append(changed)
        table = struct.unpack_from("<Q", data, 40)[0]
        for offset, fmt, value in [(40, "Q", 2**64 - 1), (table + 64, "I", 2**32 - 1),
                                   (table + 64 + 4, "I", 1), (table + 128 + 24, "Q", len(data)),
                                   (table + 128 + 32, "Q", 2**64 - 1)]:
            changed = bytearray(data)
            struct.pack_into("<" + fmt, changed, offset, value)
            variants.append(changed)
        for changed in variants:
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                identity.read_identity(io.BytesIO(changed))

    def test_dynamic_string_bounds_and_false_marker(self):
        with self.assertRaisesRegex(ValueError, "dynamic string table"):
            identity.read_identity(io.BytesIO(elf([(b".dynstr", 3, 2, b"\x00")]*2)))
        for kind, data in [(1, b"\x00ok\x00"), (3, b""), (3, b"unterminated"), (3, b"x\x00")]:
            with self.subTest(kind=kind, data=data), self.assertRaises(ValueError):
                identity.read_identity(io.BytesIO(elf([(b".dynstr", kind, 2, data)])))
        # An incidental string in ordinary data is not an AOT descriptor import.
        self.assertIsNone(identity.read_identity(io.BytesIO(elf([
            (b".rodata", 1, 2, b"\x00qore_aot_fill_module_desc\x00")]))))

    def test_capability_uses_exact_name_and_validates_inputs(self):
        for isa in ("(x86-64)", "(aarch-64)"):
            self.assertEqual(f"qore-aot-runtime({DIGEST}){isa}", identity.capability(DIGEST, isa))
        for digest, isa in [(DIGEST.upper(), "(x86-64)"), (DIGEST[:-1], "(x86-64)"),
                            (DIGEST, ""), (DIGEST, "x86-64"), (DIGEST, "(a b)")]:
            with self.subTest(digest=digest, isa=isa), self.assertRaises(ValueError):
                identity.capability(digest, isa)
        # Distinct equal-length hashes whose numeric RPM version segments normalize equally.
        left = "a01b1" + "c" * 59
        right = "a1b01" + "c" * 59
        equal = subprocess.check_output(["rpm", "--eval", f'%{{expr:v"{left}" == v"{right}"}}'], text=True)
        self.assertEqual("1", equal.strip())
        self.assertNotEqual(identity.capability(left, "(x86-64)"), identity.capability(right, "(x86-64)"))

    def test_dependency_roles_symlinks_and_io_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime, module, native = root / "libqore.so.20.0.0", root / "Probe.qmod", root / "Native.qmod"
            runtime.write_bytes(elf([record("runtime")]))
            module.write_bytes(elf([record()]))
            native.write_bytes(elf())
            value = identity.capability(DIGEST, "(x86-64)")
            for path, operation, expected in [(runtime, "provides", [value]), (runtime, "requires", []),
                                              (module, "requires", [value]), (module, "provides", []),
                                              (native, "requires", []), (native, "provides", [])]:
                self.assertEqual(expected, identity.dependencies(path, operation, "(x86-64)"))
            link = root / "libqore.so.20"
            link.symlink_to(runtime)
            self.assertEqual([], identity.dependencies(link, "provides", "(x86-64)"))
            with self.assertRaises(FileNotFoundError):
                identity.dependencies(root / "missing.qmod", "requires", "(x86-64)")
            with self.assertRaises(ValueError):
                identity.dependencies(module, "wrong", "(x86-64)")
            for payload in (elf(), elf([record()])):
                runtime.write_bytes(payload)
                with self.assertRaises(ValueError):
                    identity.dependencies(runtime, "provides", "(x86-64)")
            module.write_bytes(elf([record("runtime")]))
            with self.assertRaises(ValueError):
                identity.dependencies(module, "requires", "(x86-64)")

    def test_cli_deduplicates_and_fails_without_partial_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "Probe.qmod"
            path.write_bytes(elf([record()]))
            command = ["python3", "-B", "-W", "error", str(ROOT / "qore_aot_identity.py"), "requires", "(x86-64)"]
            result = subprocess.run(command, input=f"{path}\n{path}\n\n", text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(identity.capability(DIGEST, "(x86-64)") + "\n", result.stdout)
            result = subprocess.run(command, input=f"{path}\n{path}.missing\n", text=True, capture_output=True)
            self.assertNotEqual(0, result.returncode)
            self.assertEqual("", result.stdout)
            self.assertIn("FileNotFoundError", result.stderr)

    def test_buildroot_validation_scope_and_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            modules = root / "usr/lib64/qore-modules/nested"
            modules.mkdir(parents=True)
            (root / "usr/lib64/libqore.so.20.0.0").write_bytes(elf([record("runtime")]))
            module = modules / "Probe.qmod"
            module.write_bytes(elf([record()]))
            (modules / "Native.qmod").write_bytes(elf())
            (modules / "Probe.qmod.backup").write_text("not an ELF payload")
            (root / "usr/lib64/unrelated.so").write_text("not a Qore library")
            identity.validate_root(root, "/usr/lib64")
            # A source-only payload with no native module directory is valid.
            identity.validate_root(root, "/usr/lib")
            for bad_root, libdir in [(Path("."), "/usr/lib64"), (root / "missing", "/usr/lib64"),
                                     (root, "usr/lib64"), (root, "/"), (root, "/../usr/lib64")]:
                with self.subTest(root=bad_root, libdir=libdir), self.assertRaises(ValueError):
                    identity.validate_root(bad_root, libdir)
            module.write_bytes(elf([(b".dynstr", 3, 2, b"\x00qore_aot_fill_module_desc\x00")]))
            with self.assertRaisesRegex(ValueError, "rebuild"):
                identity.validate_root(root, "/usr/lib64")
            result = subprocess.run(["python3", "-B", "-W", "error", str(ROOT / "qore_aot_identity.py"),
                                     "validate-root", str(root), "/usr/lib64"], capture_output=True, text=True)
            self.assertNotEqual(0, result.returncode)
            self.assertEqual("", result.stdout)
            self.assertIn("rebuild with the current SDK", result.stderr)


if __name__ == "__main__":
    unittest.main()
