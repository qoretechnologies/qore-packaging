#!/usr/bin/python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Read Qore's referenced AOT identity from ELF without executing target code.

The runtime and module sections contain the same NUL-terminated SHA-256 string
used by the loader. The digest is part of the RPM capability *name*: RPM's
version comparison is unsuitable for byte-for-byte digest equality.
"""

import argparse
from pathlib import Path, PurePosixPath
import re
import struct
import sys
from typing import BinaryIO


SECTIONS = {b".qore.aot.runtime.v1": "runtime", b".qore.aot.module.v1": "module"}
IDENTITY = re.compile(rb"[0-9a-f]{64}\x00")


def read_identity(stream: BinaryIO) -> tuple[str, str] | None:
    """Return (role, digest), or None for a native-only ELF module.

    Reject invalid ELF tables and ambiguous/malformed identity metadata. An
    AOT module identified by its descriptor helper import must have metadata;
    this also rejects old AOT modules that need rebuilding with the new SDK.
    Reads are bounded by the actual file size before allocating their data.
    """
    size = stream.seek(0, 2)

    def read(offset: int, count: int) -> bytes:
        if offset < 0 or count < 0 or offset > size or count > size - offset:
            raise ValueError("ELF data extends beyond the file")
        stream.seek(offset)
        data = stream.read(count)
        if len(data) != count:
            raise ValueError("ELF file changed while reading")
        return data

    ident = read(0, 16)
    if ident[:4] != b"\x7fELF" or ident[4] not in (1, 2) or ident[5] not in (1, 2) or ident[6] != 1:
        raise ValueError("Unsupported ELF identification")
    endian = "<" if ident[5] == 1 else ">"
    header = struct.Struct(endian + ("HHIIIIIHHHHHH" if ident[4] == 1 else "HHIQQQIHHHHHH"))
    section = struct.Struct(endian + ("IIIIIIIIII" if ident[4] == 1 else "IIQQQQIIQQ"))
    fields = header.unpack(read(16, header.size))
    if fields[0] != 3 or fields[2] != 1 or fields[7] != 16 + header.size:
        raise ValueError("Expected an ELF shared object")
    table_offset, entry_size, count, names_index = fields[5], fields[10], fields[11], fields[12]
    if not table_offset or entry_size != section.size:
        raise ValueError("Missing or invalid ELF section table")
    first = section.unpack(read(table_offset, entry_size))
    if first[1] != 0:
        raise ValueError("ELF section zero must have type NULL")
    if count == 0:
        count = first[5]
    if names_index == 0xffff:
        names_index = first[6]
    if count < 2 or table_offset > size or count > (size - table_offset) // entry_size:
        raise ValueError("Invalid ELF section count")
    if not 0 < names_index < count:
        raise ValueError("Invalid ELF section-name table index")

    def get_section(index: int) -> tuple[int, ...]:
        return section.unpack(read(table_offset + index * entry_size, entry_size))

    names_header = get_section(names_index)
    if names_header[1] != 3:
        raise ValueError("ELF section names must be a string table")
    names = read(names_header[4], names_header[5])
    if not names or names[0] != 0 or names[-1] != 0:
        raise ValueError("Unterminated ELF section-name table")
    result = None
    aot = False
    have_dynamic_strings = False
    for index in range(1, count):
        item = get_section(index)
        name_offset, kind, flags, _, offset, length = item[:6]
        if name_offset >= len(names):
            raise ValueError("Invalid ELF section-name offset")
        # The name table ends in NUL, so every in-bounds offset terminates.
        # Compare only the small names of interest: scanning/copying arbitrary
        # overlapping suffixes could otherwise make malformed input quadratic.
        name = next((key for key in SECTIONS if names.startswith(key + b"\x00", name_offset)), None)
        if kind != 8 and (offset > size or length > size - offset):  # NOBITS has no file payload.
            raise ValueError("ELF section extends beyond the file")
        if names.startswith(b".qore.aot.", name_offset):
            if name is None or result is not None:
                raise ValueError("Unsupported or duplicate Qore AOT identity section")
            # PROGBITS, allocated, read-only, uncompressed, not executable.
            if kind != 1 or flags != 2 or not length or length % 65:
                raise ValueError("Invalid Qore AOT identity section attributes")
            value = read(offset, 65)
            # Linking several .qo modules may concatenate identical records.
            # Mixed runtime contracts must never be accepted in one artifact.
            if not IDENTITY.fullmatch(value):
                raise ValueError("Invalid or inconsistent Qore AOT identity digest")
            for start in range(65, length, 65):
                if read(offset + start, 65) != value:
                    raise ValueError("Invalid or inconsistent Qore AOT identity digest")
            result = SECTIONS[name], value[:64].decode("ascii")
        elif names.startswith(b".dynstr\x00", name_offset):
            if kind != 3 or have_dynamic_strings:
                raise ValueError("Invalid ELF dynamic string table")
            have_dynamic_strings = True
            strings = read(offset, length)
            if not strings or strings[0] != 0 or strings[-1] != 0:
                raise ValueError("Unterminated ELF dynamic string table")
            aot |= b"\x00qore_aot_fill_module_desc\x00" in strings
            aot |= b"\x00qore_aot_fill_module_runtime_identity\x00" in strings
    # libqore defines the helpers too. Its explicit runtime role distinguishes
    # those definitions from a module without adding a target-code execution.
    if aot and result is None:
        raise ValueError("AOT artifact lacks runtime identity metadata; rebuild with the current SDK")
    return result


def capability(digest: str, isa: str) -> str:
    """Return an exact, architecture-qualified capability, never a hash EVR."""
    if not re.fullmatch(r"[0-9a-f]{64}", digest) or not re.fullmatch(r"\([A-Za-z0-9_-]+\)", isa):
        raise ValueError("Invalid AOT digest or RPM ISA")
    return f"qore-aot-runtime({digest}){isa}"


def dependencies(path: Path, operation: str, isa: str) -> list[str]:
    """Generate a runtime provide or module requirement for one RPM payload."""
    if operation not in ("provides", "requires"):
        raise ValueError("Invalid dependency operation")
    if path.is_symlink():
        return []  # Only the real library/module supplies dependencies.
    with path.open("rb") as stream:
        identity = read_identity(stream)
    is_module = path.name.endswith(".qmod")
    if identity is None:
        if not is_module:
            raise ValueError(f"{path}: libqore lacks runtime identity metadata")
        return []
    role, digest = identity
    if (role == "module") != is_module:
        raise ValueError(f"{path}: identity role disagrees with artifact path")
    value = capability(digest, isa)
    return [value] if (role == "runtime") == (operation == "provides") else []


def validate_root(root: Path, libdir: str) -> None:
    """Validate installed ELF payloads in the mandatory RPM build phase.

    RPM intentionally ignores dependency-generator exit codes. Validation
    therefore also runs after stripping, as an ordinary checked build command.
    The generator remains responsible for producing the exact capabilities.
    """
    directory = PurePosixPath(libdir)
    if not root.is_absolute() or not root.is_dir():
        raise ValueError("RPM buildroot must be an existing absolute directory")
    if not directory.is_absolute() or ".." in directory.parts or directory == PurePosixPath("/"):
        raise ValueError("RPM libdir must be a non-root absolute path without parent components")
    library_root = root.joinpath(*directory.parts[1:])
    modules = library_root / "qore-modules"
    paths = list(modules.rglob("*.qmod"))
    paths.extend(path for path in library_root.glob("libqore.so.*")
                 if re.fullmatch(r"libqore\.so\.[0-9.]+", path.name))
    for path in sorted(paths):
        dependencies(path, "requires", "(validation)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    for operation in ("provides", "requires"):
        commands.add_parser(operation).add_argument("isa")
    validate = commands.add_parser("validate-root")
    validate.add_argument("root", type=Path)
    validate.add_argument("libdir")
    args = parser.parse_args()
    if args.operation == "validate-root":
        validate_root(args.root, args.libdir)
        return
    # Collect everything first: failure must not emit a partial dependency set.
    result = set()
    for line in sys.stdin:
        path = line.rstrip("\n")
        if path:
            result.update(dependencies(Path(path), args.operation, args.isa))
    print("\n".join(sorted(result)), end="\n" if result else "")


if __name__ == "__main__":
    main()
