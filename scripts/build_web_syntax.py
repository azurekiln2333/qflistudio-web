#!/usr/bin/env python3
"""Offline, source-pinned QuickJS syntax-only bridge builds; never runs user JS."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent


def executable(path):
    candidate = Path(path)
    if os.name == "nt" and candidate.suffix != ".exe":
        candidate = candidate.with_suffix(".exe")
    if not candidate.is_file():
        raise RuntimeError(f"Compiler not found: {candidate}")
    return str(candidate)


def compiler_preflight(cc, platform, flags, sdk=None):
    """Fail on an unusable compiler before compiling the retained engine."""
    try:
        version = subprocess.check_output([cc, "--version"], text=True).splitlines()[0]
        target = subprocess.check_output([cc, *flags, "-dumpmachine"], text=True).strip().lower()
    except (OSError, subprocess.CalledProcessError, IndexError) as error:
        raise RuntimeError(f"Cannot identify the required GCC/Clang compiler: {cc}") from error
    if platform == "windows" and not ("mingw" in target or ("windows" in target and "gnu" in target)):
        raise RuntimeError(
            f"Windows QuickJS requires a GNU/MinGW target; {cc} targets {target}. "
            "For standalone Clang with a default MSVC target, pass --sdk <MinGW-root> "
            "and, when needed, --link-cc <MinGW-gcc>, or select a GNU-target Clang. "
            "The shipping JavaScript backend cannot be omitted."
        )
    probe = """#include <stdint.h>
#include <sys/time.h>
#if !defined(__clang__) && (!defined(__GNUC__) || __GNUC__ < 9)
#error QuickJS requires GCC 9 or newer, or Clang; older GCC miscompiles module atoms
#endif
int main(void) { return 0; }
"""
    result = subprocess.run(
        [cc, *flags, "-std=gnu11", "-x", "c", "-fsyntax-only", "-"],
        input=probe, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    if result.returncode:
        raise RuntimeError(
            f"QuickJS compiler preflight failed for {cc} ({target}). "
            "Use GCC 9+ or Clang with complete platform headers; Windows standalone "
            f"Clang needs --sdk <MinGW-root>.\n{result.stdout}"
        )
    return version


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", required=True, choices=["windows", "linux", "macos", "ohos", "android", "ios"])
    parser.add_argument("--abi", choices=["arm64-v8a", "x86_64"], default="arm64-v8a")
    parser.add_argument("--arch", choices=["arm64", "x86_64"], default="arm64", help="Apple architecture")
    parser.add_argument("--apple-sdk", choices=["iphoneos", "iphonesimulator", "macosx"], help="Apple SDK/platform")
    parser.add_argument("--sdk", type=Path, help="OHOS native SDK, Android NDK, or Windows MinGW sysroot")
    parser.add_argument("--cc", help="Explicit host compiler (GCC/Clang; not MSVC)")
    parser.add_argument("--link-cc", help="Optional linker driver (e.g. MinGW GCC when compiling with Clang)")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    source = ROOT / "vendor" / "quickjs"
    retained = json.loads((source / "SOURCE.json").read_text(encoding="utf8"))
    archive = source / "quickjs-2026-06-04.tar.xz"
    if hashlib.sha256(archive.read_bytes()).hexdigest() != retained["archiveSha256"]:
        raise RuntimeError("Retained official QuickJS archive hash mismatch")
    hashes = retained["buildInputSha256"]
    for relative, expected in hashes.items():
        actual = hashlib.sha256((source / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f"Retained QuickJS source hash mismatch: {relative}")

    output = (args.output or ROOT / "build" / "native" / "web_syntax" / args.platform / (args.abi if args.platform in ["ohos", "android"] else "")).resolve()
    output.mkdir(parents=True, exist_ok=True)
    flags = []
    link_flags = []
    if args.platform == "ohos":
        if not args.sdk:
            parser.error("--sdk must name the installed OHOS native SDK")
        cc = executable(args.sdk / "llvm" / "bin" / "clang")
        triple = "aarch64-linux-ohos" if args.abi == "arm64-v8a" else "x86_64-linux-ohos"
        flags += [f"--target={triple}", f"--sysroot={args.sdk / 'sysroot'}"]
        link_flags += ["-Wl,-z,max-page-size=16384"]
    elif args.platform == "android":
        if not args.sdk:
            parser.error("--sdk must name the installed Android NDK")
        host = "windows-x86_64" if os.name == "nt" else "darwin-x86_64" if sys.platform == "darwin" else "linux-x86_64"
        toolchain = args.sdk / "toolchains" / "llvm" / "prebuilt" / host
        cc = executable(toolchain / "bin" / "clang")
        triple = "aarch64-linux-android24" if args.abi == "arm64-v8a" else "x86_64-linux-android24"
        flags += [f"--target={triple}", f"--sysroot={toolchain / 'sysroot'}"]
        link_flags += ["-Wl,-z,max-page-size=16384"]
    elif args.platform in ["ios", "macos"]:
        apple_sdk = args.apple_sdk or ("iphoneos" if args.platform == "ios" else "macosx")
        if args.platform == "ios" and apple_sdk == "macosx":
            parser.error("iOS requires iphoneos or iphonesimulator")
        if args.platform == "macos" and apple_sdk != "macosx":
            parser.error("macOS requires macosx")
        if apple_sdk == "iphoneos" and args.arch != "arm64":
            parser.error("iPhone device builds require arm64")
        sdk = subprocess.check_output(["xcrun", "--sdk", apple_sdk, "--show-sdk-path"], text=True).strip()
        cc = args.cc or subprocess.check_output(["xcrun", "--find", "clang"], text=True).strip()
        triple = f"{args.arch}-apple-macos11.0" if apple_sdk == "macosx" else f"{args.arch}-apple-ios13.0" + ("-simulator" if apple_sdk == "iphonesimulator" else "")
        flags += ["-target", triple, "-isysroot", sdk]
    else:
        cc = args.cc or shutil.which("clang") or shutil.which("gcc")
        if not cc:
            raise RuntimeError("Pass --cc with an installed GCC or Clang compiler")
        if args.platform == "windows" and args.sdk:
            # The installed OHOS clang can also compile its native Windows target
            # against local MinGW headers; GCC 4.9 is only a linker driver here.
            flags += ["--target=x86_64-w64-windows-gnu", f"--sysroot={args.sdk}"]
    compiler_version = compiler_preflight(cc, args.platform, flags, args.sdk)
    common = flags + ["-std=gnu11", "-O2", "-fno-strict-aliasing", "-fwrapv", "-fvisibility=hidden", "-D_GNU_SOURCE", '-DCONFIG_VERSION="2026-06-04"', f"-I{source}", f"-I{ROOT / 'native' / 'web_syntax'}"]
    if args.platform != "windows":
        common += ["-fPIC"]
    sources = [ROOT / "native" / "web_syntax" / "qfli_web_syntax.c"] + [source / name for name in ["quickjs.c", "cutils.c", "libregexp.c", "libunicode.c", "dtoa.c"]]
    objects = []
    for item in sources:
        obj = output / (item.stem + ".o")
        subprocess.run([cc, *common, "-c", str(item), "-o", str(obj)], check=True)
        objects.append(str(obj))
    if args.platform == "ios":
        library = output / "libqfli_web_syntax.a"
        subprocess.run(["xcrun", "ar", "rcs", str(library), *objects], check=True)
    else:
        name = "qfli_web_syntax.dll" if args.platform == "windows" else "libqfli_web_syntax.dylib" if args.platform == "macos" else "libqfli_web_syntax.so"
        library = output / name
        link = ["-dynamiclib"] if args.platform == "macos" else ["-shared"]
        if args.platform == "windows":
            link_flags += ["-static-libgcc", "-static", "-lwinpthread"]
        else:
            link_flags += ["-lm"]
            if args.platform != "android":
                link_flags += ["-lpthread"]
        link_cc = args.link_cc or cc
        target_flags = [] if args.link_cc else flags
        subprocess.run([link_cc, *target_flags, *link, *objects, *link_flags, "-o", str(library)], check=True)
    metadata = {"platform": args.platform, "abi": args.arch if args.platform in ["ios", "macos"] else args.abi if args.platform in ["ohos", "android"] else "host", "compiler": cc, "quickjs": "2026-06-04", "library": str(library), "sha256": hashlib.sha256(library.read_bytes()).hexdigest()}
    metadata["compilerVersion"] = compiler_version
    if args.sdk:
        metadata["sdk"] = str(args.sdk.resolve())
    if args.link_cc:
        metadata["linkCompiler"] = args.link_cc
    if args.platform in ["ios", "macos"]:
        metadata["appleSdk"] = apple_sdk
    (output / "build.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf8")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
