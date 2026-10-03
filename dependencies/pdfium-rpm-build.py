#!/usr/bin/env python3
# Copyright 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Configure PDFium with the distribution compiler, runtime and RPM flags."""
import argparse
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import tempfile


def output(*args):
    return subprocess.check_output(args, text=True).strip()


def configure(jobs, bundled_freetype=False):
    if bundled_freetype and not Path("third_party/freetype/src/include/freetype/freetype.h").is_file():
        raise RuntimeError("The pinned bundled FreeType source is missing")
    compiler = shutil.which("clang-21") or shutil.which("clang")
    if compiler is None:
        raise RuntimeError("Clang 21 or newer is required")
    compiler = str(Path(compiler).resolve())
    version = int(output(compiler, "-dumpversion").split(".")[0])
    if version < 21:
        raise RuntimeError("Clang is too old for the pinned PDFium source")
    resource_dir = Path(output(compiler, "--print-resource-dir"))
    if not (resource_dir / "include" / "stddef.h").is_file():
        raise RuntimeError("The selected Clang resource headers are missing")
    cpu = {"x86_64": "x64", "aarch64": "arm64"}[platform.machine()]
    runtime = None
    for name in ("libclang_rt.builtins.a", "libclang_rt.builtins-" + platform.machine() + ".a"):
        candidate = Path(output(compiler, "--print-file-name=" + name))
        if candidate.is_absolute() and candidate.is_file():
            runtime = candidate.resolve()
            break
    if runtime is None:
        raise RuntimeError("The matching compiler-rt builtins archive is missing")
    suffix = runtime.name.removeprefix("libclang_rt.builtins").removesuffix(".a")
    # GN expects an unversioned bin/ layout. Leap installs versioned executables
    # directly in /usr/bin; point each GN tool at the selected distribution tool.
    toolchain = Path("rpm/toolchain").resolve()
    (toolchain / "bin").mkdir(parents=True, exist_ok=True)
    for tool in ("clang", "clang++", "ld.lld", "llvm-ar", "llvm-nm", "llvm-readelf",
                 "llvm-objcopy", "llvm-strip"):
        executable = compiler if tool == "clang" else (
            shutil.which(tool+"-"+str(version)) or shutil.which(tool))
        if executable is None:
            raise RuntimeError("Missing distribution tool: " + tool)
        link = toolchain / "bin" / tool
        target = Path(executable).resolve()
        if link.is_symlink() and link.resolve() == target:
            continue
        link.symlink_to(target)
    flags = {key.lower(): shlex.split(os.environ.get(key, ""))
             for key in ("CPPFLAGS", "CFLAGS", "CXXFLAGS", "LDFLAGS")}
    # GN appends language-specific flags after target warning policies. Put
    # shared RPM flags in the common group so a late -Wall cannot override a
    # third-party target's existing warning choices.
    common = []
    while flags["cflags"] and flags["cxxflags"] and flags["cflags"][0] == flags["cxxflags"][0]:
        common.append(flags["cflags"].pop(0))
        flags["cxxflags"].pop(0)
    # The RPM policy selects fortification; avoid the Chromium default redefining it.
    flags["cppflags"].insert(0, "-U_FORTIFY_SOURCE")
    # Chromium uses -no-canonical-prefixes, so a compiler reached through our
    # private tool layout cannot discover its distribution resource headers.
    flags["cppflags"].append("-resource-dir=" + str(resource_dir))
    extra = []
    for flag in ("-fno-lifetime-dse", "-Wa,--crel,--allow-experimental-crel",
                 "-fsanitize-ignore-for-ubsan-feature=array-bounds",
                 "-Wno-unsafe-buffer-usage-in-static-sized-array",
                 "-fsanitize-ignore-for-ubsan-feature=return"):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([compiler, "-Werror", "-Werror=unknown-warning-option", flag,
                                     "-x", "c++", "-c", "/dev/null", "-o", directory+"/probe.o"],
                                    capture_output=True, text=True, check=False)
        if result.returncode == 0:
            extra.append(flag)
        else:
            print("Distribution compiler does not support", flag)
    variables = {"qore_"+key: value for key, value in flags.items()}
    variables.update(qore_common_cflags=common, qore_extra_cflags=extra, qore_compiler_rt_dir=str(runtime.parent),
                     qore_compiler_rt_suffix=suffix)
    Path("rpm/buildflags.gni").write_text("".join(
        key + " = " + json.dumps(value) + "\n" for key, value in variables.items()))
    Path("build/config/gclient_args.gni").write_text(
        "build_with_chromium = false\ncheckout_android = false\ncheckout_skia = false\n")
    for library in ("icu", "brotli"):
        shutil.copy2(Path("build/linux/unbundle")/(library+".gn"),
                     Path("third_party")/library/"BUILD.gn")
    env = dict(os.environ, CC=str(toolchain/"bin/clang"), CXX=str(toolchain/"bin/clang++"))
    subprocess.run(["python3", "build/gen.py", "--no-last-commit-position", "--no-static-libstdc++"],
                   cwd="gn-src", env=env, check=True)
    Path("gn-src/out/last_commit_position.h").write_text(
        '#define LAST_COMMIT_POSITION_NUM 2342\n'
        '#define LAST_COMMIT_POSITION "2342 (129ce6b9af1a)"\n')
    subprocess.run(["ninja", "-C", "gn-src/out", "-j"+str(jobs), "gn"], check=True)
    args = dict(is_debug=False, is_component_build=False, pdf_is_standalone=True,
                pdf_enable_v8=False, pdf_enable_xfa=False, pdf_use_skia=False,
                pdf_use_partition_alloc=False,
                use_sysroot=False, clang_use_chrome_plugins=False, treat_warnings_as_errors=True,
                target_os="linux", target_cpu=cpu, use_custom_libcxx=False, is_clang=True,
                clang_base_path=str(toolchain), clang_version=str(version),
                use_siso=False, use_remoteexec=False, pdf_bundle_freetype=bundled_freetype,
                use_system_freetype=not bundled_freetype, use_system_lcms2=True, use_system_libopenjpeg2=True,
                use_system_libpng=True, use_system_libtiff=True, use_system_zlib=True,
                use_system_libjpeg=True, symbol_level=2, use_dwarf5=True, use_debug_fission=False,
                forbid_non_component_debug_builds=False, use_thin_lto=False,
                use_allocator_shim=False, use_partition_alloc_as_malloc=False, enable_rust=False)
    subprocess.run(["gn-src/out/gn", "gen", "out/Release", "--args="+" ".join(
        key+"="+json.dumps(value) for key, value in args.items())], check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--bundled-freetype", action="store_true",
                        help="Use PDFium's pinned private FreeType source and configuration")
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    configure(args.jobs, args.bundled_freetype)
