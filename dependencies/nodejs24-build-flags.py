#!/usr/bin/python3
# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Pass distribution LTO requests through Node's supported configure option."""
import argparse
import re
import shlex


def build_environment(cflags, ldflags):
    groups = [shlex.split(cflags), shlex.split(ldflags)]
    requests = []
    for flags in groups:
        enabled = None
        for flag in flags:
            if flag == "-fno-lto":
                enabled = False
            elif flag == "-flto" or re.fullmatch(r"-flto=(auto|jobserver|[1-9][0-9]*)", flag):
                enabled = True
            elif flag.startswith("-flto="):
                raise ValueError("Unsupported GCC LTO mode: " + flag)
        if enabled is not None:
            requests.append(enabled)
    if len(set(requests)) > 1:
        raise ValueError("Conflicting compiler and linker LTO requests")
    enabled = bool(requests and requests[0])
    # External positive flags occur after GYP's per-target -fno-lto and would
    # override its handling of the assembly stack scanner. Configure owns LTO.
    filtered = [[flag for flag in flags if flag not in ("-flto", "-fno-lto") and not flag.startswith("-flto=")]
                for flags in groups]
    return {
        "CFLAGS": shlex.join(filtered[0]),
        "CXXFLAGS": shlex.join([*filtered[0], "-Wno-error=return-type"]),
        "LDFLAGS": shlex.join(filtered[1]),
        "NODE_LTO_OPTION": "--enable-lto" if enabled else "",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cflags", required=True)
    parser.add_argument("--ldflags", required=True)
    args = parser.parse_args()
    for name, value in build_environment(args.cflags, args.ldflags).items():
        print("export " + name + "=" + shlex.quote(value))


if __name__ == "__main__":
    main()
