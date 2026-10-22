"""Inspect actual current HAP catalogs, native ABI and test-source separation."""
from pathlib import Path
import argparse
import hashlib
import io
import json
import struct
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
from prepare_ohos_catalog import staged_files
from run_ohos_catalog import inspect_archive


ABIS = (("arm64-v8a", 183), ("x86_64", 62))
FLUTTER_LIBRARIES = ("libapp.so", "libflutter.so")


def flutter_libraries(archive):
    """Reject missing, placeholder or wrong-architecture Flutter runtime pairs."""
    names = set(archive.namelist())
    required = [(f"libs/{abi}/{library}", machine)
                for abi, machine in ABIS for library in FLUTTER_LIBRARIES]
    missing = [name for name, _ in required if name not in names]
    if missing:
        raise ValueError("missing required Flutter runtime libraries: " + ", ".join(missing))
    libraries = []
    for name, machine in required:
        payload = archive.read(name)
        if len(payload) < 64 or payload[:6] != b"\x7fELF\x02\x01" or \
                struct.unpack_from("<HH", payload, 16) != (3, machine):
            raise ValueError(f"{name}: expected ELF64 little-endian ET_DYN machine {machine}")
        libraries.append({"path": name, "bytes": len(payload),
                          "sha256": hashlib.sha256(payload).hexdigest(), "machine": machine})
    return libraries


def verify_flutter_fixtures():
    """Exercise only the runtime-pair gate using isolated header-only ZIP fixtures."""
    payloads = {}
    for abi, machine in ABIS:
        header = bytearray(64)
        header[:6] = b"\x7fELF\x02\x01"
        struct.pack_into("<HH", header, 16, 3, machine)
        for library in FLUTTER_LIBRARIES:
            payloads[f"libs/{abi}/{library}"] = bytes(header)

    def check(entries, expected_error=None):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            for name, payload in entries.items():
                archive.writestr(name, payload)
        with zipfile.ZipFile(buffer) as archive:
            try:
                result = flutter_libraries(archive)
            except ValueError as error:
                if expected_error is None or expected_error not in str(error):
                    raise AssertionError(f"unexpected fixture rejection: {error}") from error
            else:
                if expected_error is not None or len(result) != 4:
                    raise AssertionError("runtime-pair fixture was incorrectly accepted")

    check(payloads)
    rejected = []
    for name, payload in payloads.items():
        check({key: value for key, value in payloads.items() if key != name}, name)
        rejected.append(f"missing {name}")
        wrong_machine = bytearray(payload)
        struct.pack_into("<H", wrong_machine, 18,
                         62 if "/arm64-v8a/" in name else 183)
        check({**payloads, name: bytes(wrong_machine)}, name)
        rejected.append(f"wrong machine {name}")
    name = next(iter(payloads))
    for label, payload in (("truncated header", b"\x7fELF"),
                           ("non-ELF placeholder", b"x" * 64)):
        check({**payloads, name: payload}, name)
        rejected.append(label)
    executable = bytearray(payloads[name])
    struct.pack_into("<H", executable, 16, 2)
    check({**payloads, name: bytes(executable)}, name)
    rejected.append("ET_EXEC instead of ET_DYN")
    return {"status": "passed", "acceptedFixtures": 1,
            "rejectedFixtures": len(rejected), "rejections": rejected,
            "scope": "isolated header-only fixtures; no platform-runtime execution"}


def audit(path, kind, expected, readelf):
    result = inspect_archive(path, kind, expected)
    result["status"] = "passed"
    if kind != "production":
        return result
    libraries = []
    with zipfile.ZipFile(path) as archive, tempfile.TemporaryDirectory() as temp:
        for abi, machine in ABIS:
            name = f"libs/{abi}/libqfli_web_syntax.so"
            payload = archive.read(name)
            assert payload[:6] == b"\x7fELF\x02\x01", name
            assert struct.unpack_from("<HH", payload, 16) == (3, machine), name
            assert struct.unpack_from("<Q", payload, 24)[0] == 0, name
            offset = struct.unpack_from("<Q", payload, 32)[0]
            size, count = struct.unpack_from("<HH", payload, 54)
            loads = []
            for index in range(count):
                start = offset + size * index
                if struct.unpack_from("<I", payload, start)[0] != 1:
                    continue
                alignment = struct.unpack_from("<Q", payload, start + 48)[0]
                assert alignment >= 16384, name
                loads.append(alignment)
            assert loads, name
            local = Path(temp) / f"{abi}.so"
            local.write_bytes(payload)
            symbols = subprocess.check_output([str(readelf), "--dyn-syms", "--wide", str(local)], text=True)
            exports = [line.split()[-1] for line in symbols.splitlines()
                       if " GLOBAL " in line and " DEFAULT " in line and " UND " not in line]
            # CMake's CRT may also expose the standard ELF init/fini hooks.
            assert set(exports) - {"_init", "_fini"} == {
                "qfli_web_syntax_check", "qfli_web_syntax_version"}, exports
            libraries.append({"path": name, "bytes": len(payload),
                              "sha256": hashlib.sha256(payload).hexdigest(),
                              "machine": machine, "entry": 0, "loadAlignment": loads,
                              "exports": exports})
        assert "resources/rawfile/flutter_assets/vendor/quickjs/LICENSE" in archive.namelist()
        try:
            result["flutterLibraries"] = flutter_libraries(archive)
            result["flutterRuntime"] = {"status": "passed"}
        except ValueError as error:
            result["status"] = "failed"
            result["flutterRuntime"] = {"status": "failed", "error": str(error)}
    result["syntaxLibraries"] = libraries
    result["signedInstallation"] = "not verified by archive inspection"
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--production", type=Path)
    parser.add_argument("--test", type=Path)
    parser.add_argument("--readelf", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--self-test", action="store_true",
                        help="verify the runtime-pair gate using isolated ZIP fixtures")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(verify_flutter_fixtures(), indent=2))
        sys.exit(0)
    for name in ("production", "test", "readelf", "report"):
        if getattr(args, name) is None:
            parser.error(f"--{name} is required unless --self-test is used")
    expected = staged_files(ROOT)
    results = {}
    for kind, path in (("production", args.production), ("test", args.test)):
        try:
            results[kind] = audit(path, kind, expected, args.readelf)
        except (AssertionError, KeyError, OSError, ValueError, struct.error,
                subprocess.CalledProcessError, zipfile.BadZipFile) as error:
            results[kind] = {"path": str(path), "status": "failed", "error": str(error)}
    args.report.write_text(json.dumps(results, indent=2) + "\n", encoding="utf8")
    print(json.dumps(results, indent=2))
    sys.exit(1 if any(result["status"] != "passed" for result in results.values()) else 0)
