#!/usr/bin/env python3
"""Package explicit native build outputs without source trees or object caches."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile


ROOT = Path(__file__).resolve().parent.parent


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def build_files(platform, source, abi):
    """Required source/destination pairs; a missing binary fails packaging."""
    if platform == "linux":
        return [
            (source / "desktop/nginx", "bin/nginx"),
            (source / "embedded/libqfli_nginx.a", "lib/libqfli_nginx.a"),
            (source / "embedded/libqfli_nginx.so", "lib/libqfli_nginx.so"),
            (source / "embedded/undefined-symbols.txt", "evidence/nginx-undefined-symbols.txt"),
            (source / "web_syntax/libqfli_web_syntax.so", "lib/libqfli_web_syntax.so"),
            (source / "web_syntax/build.json", "evidence/web-syntax-build.json"),
        ]
    if platform == "android":
        return [
            (source / "nginx/libnginx_exec.so", f"jniLibs/{abi}/libnginx_exec.so"),
            (source / "web_syntax/libqfli_web_syntax.so", f"jniLibs/{abi}/libqfli_web_syntax.so"),
        ]
    if platform == "ohos":
        return [
            (source / "nginx/libqfli_nginx.a", f"prebuilt/{abi}/libqfli_nginx.a"),
            (source / "nginx/libqfli_nginx.so", f"embedded/{abi}/libqfli_nginx.so"),
            (source / "nginx/undefined-symbols.txt", "evidence/nginx-undefined-symbols.txt"),
            (source / "cmake/libqfli_nginx_napi.so", f"libs/{abi}/libqfli_nginx_napi.so"),
            (source / "cmake/libqfli_web_cdp_transport.so", f"libs/{abi}/libqfli_web_cdp_transport.so"),
            (source / "cmake/web_syntax/libqfli_web_syntax.so", f"libs/{abi}/libqfli_web_syntax.so"),
            (ROOT / "ohos/entry/src/main/cpp/web_cdp_transport.h", "include/web_cdp_transport.h"),
        ]
    raise ValueError(f"Unsupported platform: {platform}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", choices=["linux", "android", "ohos"], required=True)
    parser.add_argument("--abi", default="x86_64", choices=["arm64-v8a", "armeabi-v7a", "x86_64"])
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "build/ci/artifacts")
    args = parser.parse_args()
    source = args.input.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    name = f"qfli-native-{args.platform}-{args.abi}-{commit[:12]}"
    required = build_files(args.platform, source, args.abi)
    required += [
        (ROOT / "native/nginx/embedded/qfli_nginx.h", "include/qfli_nginx.h"),
        (ROOT / "native/web_syntax/qfli_web_syntax.h", "include/qfli_web_syntax.h"),
        (ROOT / "LICENSE", "licenses/project-LICENSE"),
        (ROOT / "vendor/nginx/LICENSE", "licenses/nginx-LICENSE"),
        (ROOT / "vendor/nginx/android-glob/LICENSE", "licenses/android-glob-LICENSE"),
        (ROOT / "vendor/quickjs/LICENSE", "licenses/quickjs-LICENSE"),
    ]
    for path, _ in required:
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"Required build output is missing or empty: {path}")

    with tempfile.TemporaryDirectory(prefix="package-", dir=output) as temporary:
        package = Path(temporary) / name
        package.mkdir()
        for path, destination in required:
            target = package / destination
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        for log in sorted((source / "logs").glob("*.log")):
            target = package / "evidence" / log.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(log, target)
        run_url = None
        if os.environ.get("GITHUB_RUN_ID"):
            run_url = (f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/"
                       f"{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}")
        metadata = {
            "commit": commit,
            "platform": args.platform,
            "abi": args.abi,
            "runUrl": run_url,
            "runAttempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
            "runnerOS": os.environ.get("RUNNER_OS"),
            "androidNdk": os.environ.get("ANDROID_NDK_VERSION") if args.platform == "android" else None,
            "ohosSdk": os.environ.get("OHOS_SDK_VERSION") if args.platform == "ohos" else None,
            "nginx": "1.31.6",
            "quickjs": "2026-06-04",
            "files": [{"path": p.relative_to(package).as_posix(), "bytes": p.stat().st_size,
                       "sha256": sha256(p)} for p in sorted(package.rglob("*")) if p.is_file()],
        }
        (package / "build-manifest.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf8")
        (package / "README.txt").write_text(
            "QFLIWebForge native build outputs\n"
            f"Target: {args.platform}/{args.abi}\nCommit: {commit}\n"
            "These are native components, not APK/HAP/IPA installers.\n"
            "Android libnginx_exec.so is a PIE executable, not a dlopen library.\n"
            "OHOS libs/ contains packaged NAPI/parser libraries.\n"
            "OHOS prebuilt/ is the archive consumed by the app CMake build.\n"
            "OHOS embedded/ is the standalone C ABI library, not the NAPI bridge.\n"
            "Cross-compilation does not prove device execution or signing.\n"
            "Checksums: run sha256sum -c SHA256SUMS from this directory.\n"
            "See docs/native-builds.md in the source repository for download/use.\n",
            encoding="utf8",
        )
        files = sorted(p for p in package.rglob("*") if p.is_file())
        (package / "SHA256SUMS").write_text("".join(
            f"{sha256(p)}  {p.relative_to(package).as_posix()}\n" for p in files), encoding="utf8")
        archive = output / f"{name}.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(package, arcname=name)
    digest = sha256(archive)
    archive.with_suffix(archive.suffix + ".sha256").write_text(f"{digest}  {archive.name}\n", encoding="utf8")
    summary = f"- `{archive.name}` ({archive.stat().st_size:,} bytes), SHA-256 `{digest}`\n"
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf8") as stream:
            stream.write(summary)
    print(summary, end="")


if __name__ == "__main__":
    main()
