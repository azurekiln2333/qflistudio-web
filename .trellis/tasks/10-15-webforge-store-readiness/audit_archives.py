"""Inspect fresh release packages against the product source and native ABI."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
MACHINES = {"arm64-v8a": 183, "armeabi-v7a": 40, "x86_64": 62}


def elf(data, abi, android):
    assert data[:4] == b"\x7fELF", f"{abi}: not ELF"
    assert data[5] == 1, f"{abi}: unexpected endian"
    kind, machine = struct.unpack_from("<HH", data, 16)
    assert kind == 3 and machine == MACHINES[abi], (abi, kind, machine)
    if data[4] == 2:
        offset = struct.unpack_from("<Q", data, 32)[0]
        entry_size, count = struct.unpack_from("<HH", data, 54)
        fmt = "<IIQQQQQQ"
        file_index, virtual_index = 2, 3
    else:
        offset = struct.unpack_from("<I", data, 28)[0]
        entry_size, count = struct.unpack_from("<HH", data, 42)
        fmt = "<IIIIIIII"
        file_index, virtual_index = 1, 2
    alignments = []
    for i in range(count):
        header = struct.unpack_from(fmt, data, offset + i * entry_size)
        if header[0] != 1:
            continue
        alignments.append(header[7])
        if android:
            assert header[7] >= 16384, (abi, "LOAD alignment", header[7])
            assert header[file_index] % 16384 == header[virtual_index] % 16384
    assert alignments, f"{abi}: no LOAD segments"
    return {"machine": machine, "loadAlignments": alignments}


def inspect(path, android):
    path = Path(path).resolve()
    result = {"path": str(path), "bytes": path.stat().st_size,
              "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        assets = {}
        for relative in ["assets/content/tutorials.json", "assets/content/examples.json",
                         "vendor/nginx/LICENSE", "vendor/nginx/android-glob/LICENSE"]:
            matches = [n for n in names if n.endswith("flutter_assets/" + relative)]
            assert len(matches) == 1, (relative, matches)
            data = archive.read(matches[0])
            assert data == (ROOT / relative).read_bytes(), f"stale packaged asset: {relative}"
            assets[relative] = hashlib.sha256(data).hexdigest()
        result["sourceAssetHashes"] = assets
        libraries = {}
        for abi in (MACHINES if android else {"arm64-v8a": 183, "x86_64": 62}):
            suffix = f"/{abi}/" + ("libnginx_exec.so" if android else "libqfli_nginx_napi.so")
            matches = [n for n in names if n.endswith(suffix)]
            assert len(matches) == 1, (abi, matches)
            libraries[matches[0]] = elf(archive.read(matches[0]), abi, android)
        result["nativeLibraries"] = libraries
        if not android:
            assert not any(n.endswith("libnginx_exec.so") for n in names)
            module = json.loads(archive.read("module.json"))
            encoded = json.dumps(module)
            assert "executableBinaryPaths" not in encoded
            assert "com.azurekiln.qfli.webforge" in encoded
            assert module["app"]["vendor"] == "QFLI", module["app"]
            assert module["app"]["buildMode"] == "release", module["app"]
            assert module["app"]["debug"] is False, module["app"]
            result["bundleName"] = "com.azurekiln.qfli.webforge"
            result["vendor"] = module["app"]["vendor"]
            result["buildMode"] = module["app"]["buildMode"]
            result["versionName"] = module["app"]["versionName"]
            result["versionCode"] = module["app"]["versionCode"]
    return result


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: python audit_archives.py <apk> <hap> <report.json>")
    report = {"android": inspect(sys.argv[1], True), "ohos": inspect(sys.argv[2], False)}
    Path(sys.argv[3]).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
