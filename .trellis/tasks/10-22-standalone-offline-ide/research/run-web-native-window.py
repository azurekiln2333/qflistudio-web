"""Prepare or run only the explicitly granted OHOS CDP native target window."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import struct
import sys
import time


RESEARCH = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
CPP = ROOT / "ohos/entry/src/main/cpp"
SDK = Path("D:/ProgramFiles/Huawei/DevEco Studio/sdk/default/openharmony/native")
HMS = SDK.parent.parent / "hms/native"
CONTROL = RESEARCH / "run-web-app-window.py"
HELPER = RESEARCH / "run-web-owned-window.py"
CONTROL_SHA256 = "d80c46e1b1cf2abe7e7a582e61016ac36266354242de198a5623628659922a19"
HELPER_SHA256 = "9df7a94399aae38951337d61693d65de6e3cef438d02d4e51c787242dfda7fbe"
TARGET = "qfli_web_cdp_transport"
ABIS = {"arm64-v8a": 183, "x86_64": 62}
WORK_SECONDS, CLEANUP_SECONDS, TOTAL_SECONDS, LAST_START = 150, 170, 180, 140
EXPORTS = {f"qfli_web_cdp_{name}" for name in ("open_self", "read", "write", "close")}


def load_control():
    for path, expected in ((CONTROL, CONTROL_SHA256), (HELPER, HELPER_SHA256)):
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"Pinned local lifecycle source changed: {path}")
    spec = importlib.util.spec_from_file_location("native_window_app_control", CONTROL)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot import pinned local lifecycle helpers")
    control = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(control)  # Guarded main: never starts app phases.
    return control


def same_path(value, expected):
    return str(Path(value).resolve()).casefold() == str(expected.resolve()).casefold()


def cache_binding(abi):
    directory = ROOT / f"ohos/entry/.cxx/default/default/release/{abi}"
    cache = directory / "CMakeCache.txt"
    values = dict(re.findall(r"^([^#/:\s]+):[^=\r\n]+=(.*)$",
                             cache.read_text(encoding="utf-8"), re.MULTILINE))
    for key, expected in {"CMAKE_BUILD_TYPE": "Release", "CMAKE_GENERATOR": "Ninja",
                          "CMAKE_SYSTEM_NAME": "OHOS", "OHOS_ARCH": abi,
                          "CMAKE_OHOS_ARCH_ABI": abi}.items():
        if values.get(key) != expected:
            raise ValueError(f"{abi} cache binding {key}: {values.get(key)!r}")
    output = ROOT / f"ohos/entry/build/default/intermediates/cmake/default/obj/{abi}"
    expected_paths = {
        "CMAKE_HOME_DIRECTORY": CPP, "qfli_nginx_napi_SOURCE_DIR": CPP,
        "CMAKE_CACHEFILE_DIR": directory, "CMAKE_LIBRARY_OUTPUT_DIRECTORY": output,
        "OHOS_SDK_NATIVE": SDK, "HMOS_SDK_NATIVE": HMS,
        "CMAKE_TOOLCHAIN_FILE": HMS / "build/cmake/hmos.toolchain.cmake",
        "CMAKE_COMMAND": SDK / "build-tools/cmake/bin/cmake.exe",
        "CMAKE_MAKE_PROGRAM": SDK / "build-tools/cmake/bin/ninja.exe",
        "CMAKE_READELF": SDK / "llvm/bin/llvm-readelf.exe",
    }
    for key, expected in expected_paths.items():
        if not values.get(key) or not same_path(values[key], expected):
            raise ValueError(f"{abi} cache path mismatch: {key}")
    compilers = {}
    for language, executable in (("C", "clang.exe"), ("CXX", "clang++.exe")):
        records = list(directory.glob(f"CMakeFiles/*/CMake{language}Compiler.cmake"))
        if len(records) != 1:
            raise ValueError(f"{abi} requires one generated {language} compiler record")
        matches = re.findall(rf'^set\(CMAKE_{language}_COMPILER "([^"\r\n]+)"\)$',
                             records[0].read_text(encoding="utf-8"), re.MULTILINE)
        expected = SDK / "llvm/bin" / executable
        if len(matches) != 1 or not same_path(matches[0], expected):
            raise ValueError(f"{abi} actual {language} compiler path mismatch")
        compilers[language] = str(expected.resolve())
    for path in (*compilers.values(), *(expected_paths[key] for key in
                  ("CMAKE_TOOLCHAIN_FILE", "CMAKE_COMMAND", "CMAKE_MAKE_PROGRAM", "CMAKE_READELF"))):
        if not Path(path).is_file():
            raise FileNotFoundError(path)
    return {"abi": abi, "directory": str(directory.resolve()),
            "output": str((output / f"lib{TARGET}.so").resolve()),
            "cmake": str(expected_paths["CMAKE_COMMAND"].resolve()),
            "readelf": str(expected_paths["CMAKE_READELF"].resolve()),
            "ninja": str(expected_paths["CMAKE_MAKE_PROGRAM"].resolve()),
            "toolchain": str(expected_paths["CMAKE_TOOLCHAIN_FILE"].resolve()),
            "compilers": compilers, "configuration": "Release/Ninja/OHOS",
            "cacheInputs": {key: value for key, value in sorted(values.items()) if not key.endswith("-ADVANCED") and re.match(
                r"^(?:CMAKE_(?:C|CXX)_FLAGS|CMAKE_(?:SHARED|MODULE|EXE)_LINKER_FLAGS|OHOS_|HMOS_|QFLI_)", key)}}


def snapshot(control):
    bindings = {abi: cache_binding(abi) for abi in ABIS}
    files = {Path(__file__).resolve(), CONTROL, HELPER,
             CPP / "CMakeLists.txt", CPP / "web_cdp_transport.h",
             CPP / "web_cdp_transport.cpp", CPP / "web_cdp_transport_napi.cpp",
             ROOT / "ohos/entry/build-profile.json5", ROOT / "ohos/entry/oh-package.json5",
             ROOT / "native/web_syntax/CMakeLists.txt",
             SDK / "oh-uni-package.json", HMS / "uni-package.json",
             SDK / "sysroot/usr/include/info/application_target_sdk_version.h"}
    for pattern in ("**/*.cpp", "**/*.c", "**/*.h", "**/*.hpp", "**/*.cmake", "**/CMakeLists.txt",
                    "types/libqfli_web_cdp_transport/*", "prebuilt/*/libqfli_nginx.a"):
        files.update(path.resolve() for path in CPP.glob(pattern) if path.is_file())
    for directory, pattern in ((SDK / "build/cmake", "*.cmake"),
                               (HMS / "build/cmake", "*.cmake"),
                               (SDK / "sysroot/usr/include/napi", "**/*.h")):
        files.update(path.resolve() for path in directory.glob(pattern) if path.is_file())
    quickjs = ROOT / "vendor/quickjs"
    hashes = quickjs / "HASHES.sha256"
    files.add(hashes)
    for line in hashes.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if match is None:
            raise ValueError("Invalid retained QuickJS hash input")
        path = (quickjs / match[2]).resolve()
        if control.file_hash(path) != match[1]:
            raise ValueError(f"Retained QuickJS input mismatch: {path}")
        files.add(path)
    for binding in bindings.values():
        files.update(Path(binding[key]) for key in ("cmake", "readelf", "ninja", "toolchain"))
        files.update(Path(path) for path in binding["compilers"].values())
    interpreter = Path(sys.executable).resolve(strict=True)
    if "windowsapps" in (part.casefold() for part in interpreter.parts):
        raise RuntimeError("Actual Python interpreter required; WindowsApps aliases refused")

    def records(paths):
        result = []
        for path in sorted(set(paths), key=lambda item: str(item).casefold()):
            if not path.is_file():
                raise FileNotFoundError(path)
            result.append({"path": str(path.resolve()), "bytes": path.stat().st_size,
                           "sha256": control.file_hash(path)})
        return result

    generated, artifacts = {}, {}
    for abi, binding in bindings.items():
        directory = Path(binding["directory"])
        generated_files = {directory / "CMakeCache.txt", directory / "build.ninja",
                           directory / "CMakeFiles/rules.ninja"}
        generated_files.update(path for path in (directory / "CMakeFiles").rglob("*.cmake")
                               if path.is_file())
        generated[abi] = records(generated_files)
        library = Path(binding["output"])
        artifacts[abi] = records([library]) if library.is_file() else []
    return {"immutable": {"files": records(files), "bindings": bindings,
                          "interpreter": str(interpreter)},
            "generated": generated, "artifacts": artifacts}


def validate_elf(path, abi):
    if path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError("Unexpected native artifact over 64 MiB")
    data = path.read_bytes()

    def bounded(offset, size):
        if offset < 0 or size < 0 or offset + size > len(data):
            raise ValueError("ELF file range outside artifact")
        return data[offset:offset + size]

    if len(data) < 64 or data[:7] != b"\x7fELF\x02\x01\x01":
        raise ValueError("ELF64 little-endian current-version header required")
    header = struct.unpack_from("<HHIQQQIHHHHHH", data, 16)
    kind, machine, version, entry, phoff, shoff, _, ehsize, phsize, phcount, shsize, shcount, _ = header
    if (kind, machine, version, entry, ehsize, phsize, shsize) != (3, ABIS[abi], 1, 0, 64, 56, 64):
        raise ValueError("ELF DYN/machine/entry/header dimensions mismatch")
    if phcount in (0, 0xffff) or shcount == 0:
        raise ValueError("Missing or unsupported extended ELF tables")
    bounded(phoff, phcount * phsize)
    bounded(shoff, shcount * shsize)
    loads = []
    for index in range(phcount):
        segment = struct.unpack_from("<IIQQQQQQ", data, phoff + index * phsize)
        if segment[0] == 1:
            _, flags, offset, vaddr, _, size, memory, alignment = segment
            bounded(offset, size)
            if (alignment < 0x4000 or alignment & (alignment - 1)
                    or offset % alignment != vaddr % alignment or size > memory):
                raise ValueError("LOAD segment lacks valid >=16KiB alignment/range")
            loads.append({"flags": flags, "offset": offset, "virtualAddress": vaddr,
                          "fileBytes": size, "memoryBytes": memory, "alignment": alignment})
    if not loads:
        raise ValueError("No LOAD segments")
    sections = [struct.unpack_from("<IIQQQQIIQQ", data, shoff + index * shsize)
                for index in range(shcount)]

    def strings(section):
        link = section[6]
        if link >= len(sections) or sections[link][1] != 3:
            raise ValueError("Invalid linked dynamic string table")
        table = bounded(sections[link][4], sections[link][5])

        def read(offset):
            if offset >= len(table):
                raise ValueError("Dynamic string outside table")
            end = table.find(b"\0", offset)
            if end < 0:
                raise ValueError("Unterminated dynamic string")
            return table[offset:end].decode("utf-8", errors="strict")
        return read

    symbol_sections = [section for section in sections if section[1] == 11]
    dynamic_sections = [section for section in sections if section[1] == 6]
    if len(symbol_sections) != 1 or len(dynamic_sections) != 1:
        raise ValueError("One dynamic symbol and dependency table required")
    symbols = symbol_sections[0]
    if symbols[9] != 24 or symbols[5] % 24:
        raise ValueError("Invalid ELF64 dynamic symbol dimensions")
    bounded(symbols[4], symbols[5])
    symbol_name = strings(symbols)
    candidates, imports = {}, set()
    for offset in range(symbols[4], symbols[4] + symbols[5], 24):
        name, info, visibility, section_index, _, _ = struct.unpack_from("<IBBHQQ", data, offset)
        name = symbol_name(name)
        if section_index == 0 and name:
            imports.add(name)
        if name.startswith("qfli_web_cdp_"):
            candidates.setdefault(name, []).append({"binding": info >> 4, "type": info & 15,
                                                    "visibility": visibility & 3, "section": section_index})
    if set(candidates) != EXPORTS or any(
            len(items) != 1 or items[0]["binding"] != 1 or items[0]["type"] != 2
            or items[0]["visibility"] != 0 or not 0 < items[0]["section"] < min(shcount, 0xff00)
            for items in candidates.values()):
        raise ValueError("Four defined GLOBAL DEFAULT FUNC transport exports required")
    dynamic = dynamic_sections[0]
    if dynamic[9] != 16 or dynamic[5] % 16:
        raise ValueError("Invalid ELF64 dynamic table dimensions")
    bounded(dynamic[4], dynamic[5])
    dependency_name = strings(dynamic)
    dependencies, terminated = [], False
    for offset in range(dynamic[4], dynamic[4] + dynamic[5], 16):
        tag, value = struct.unpack_from("<qQ", data, offset)
        if tag == 0:
            terminated = True
            break
        if tag == 1:
            dependencies.append(dependency_name(value))
    required_imports = {"napi_module_register", "napi_get_cb_info", "pthread_mutex_lock", "pthread_mutex_unlock"}
    if (not terminated or "libace_napi.z.so" not in dependencies
            or not any(name.startswith("libc++") for name in dependencies)
            or not required_imports <= imports):
        raise ValueError("Missing NAPI/C++ dependency or NAPI/pthread imports")
    return {"class": "ELF64", "endianness": "little", "type": "DYN", "machine": machine,
            "entry": entry, "loadSegments": loads, "transportExports": candidates,
            "needed": dependencies, "undefinedImports": sorted(imports), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grant")
    parser.add_argument("--run-name")
    parser.add_argument("--next-owner")
    parser.add_argument("--snapshot-only", action="store_true")
    args = parser.parse_args()
    if args.snapshot_only and any((args.grant, args.run_name, args.next_owner)):
        parser.error("Snapshot-only preflight takes no grant arguments")
    if not args.snapshot_only and (
            not args.grant or not args.grant.strip() or not args.run_name
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", args.run_name)
            or not args.next_owner or not re.fullmatch(r"[a-z][a-z0-9_-]+", args.next_owner)):
        parser.error("Runtime requires a new explicit grant, fresh run name and one next owner")
    control = load_control()
    if args.snapshot_only:
        source = snapshot(control)
        print(json.dumps({"snapshotOnly": True, "immutableFiles": len(source["immutable"]["files"]),
                          "bindings": source["immutable"]["bindings"],
                          "generatedFiles": {abi: len(items) for abi, items in source["generated"].items()},
                          "artifactsPresent": {abi: bool(items) for abi, items in source["artifacts"].items()},
                          "controlSha256": CONTROL_SHA256, "helperSha256": HELPER_SHA256}))
        return 0
    if os.name != "nt":
        raise RuntimeError("Windows-only native window supervisor")
    directory = RESEARCH / args.run_name
    directory.mkdir(exist_ok=False)
    started = time.monotonic()
    report_path = directory / "job.json"
    report = {"schemaVersion": 1, "grant": args.grant, "nextOwner": args.next_owner,
              "startedUtc": control.utc(), "budgetSeconds": {"work": WORK_SECONDS,
              "cleanup": CLEANUP_SECONDS, "total": TOTAL_SECONDS, "lastPhaseStart": LAST_START},
              "controlSha256": CONTROL_SHA256, "helperSha256": HELPER_SHA256,
              "errors": [], "firstError": None, "sourceSnapshotsIdentical": None,
              "phases": [{"name": f"{abi}-{kind}", "status": "UNRUN"}
                         for abi in ABIS for kind in ("build", "elf")]}
    helper, before, held = None, None, []

    def failure(message):
        report["errors"].append(message)
        if report["firstError"] is None:
            report["firstError"] = message

    def persist():
        try:
            control.write_json(report_path, report)
        except BaseException as exc:
            failure(f"Report persistence: {type(exc).__name__}: {exc}")

    control.write_json(report_path, report)
    try:
        helper = control.load_helper()
        before = snapshot(control)
        control.write_json(directory / "source-before.json", before)
        report["bindings"] = before["immutable"]["bindings"]
        for phase in report["phases"]:
            abi, kind = phase["name"].rsplit("-", 1)
            elapsed = time.monotonic() - started
            minimum, maximum = (10, 65) if kind == "build" else (1, 6)
            if elapsed >= LAST_START or WORK_SECONDS - elapsed < minimum or held:
                failure(f"{phase['name']} UNRUN: phase-start cutoff/budget or unconfirmed cleanup")
                break
            binding = cache_binding(abi)
            if binding != report["bindings"][abi]:
                raise ValueError(f"{abi} semantic cache/tool binding changed")
            if kind == "build":
                command = [binding["cmake"], "--build", binding["directory"],
                           "--target", TARGET, "--parallel", "1"]
            else:
                command = [binding["readelf"], "--wide", "--file-header", "--program-headers",
                           "--dyn-syms", "--dynamic", binding["output"]]
            persist()
            # Cache checks/report I/O above cannot silently consume the start cutoff.
            now = time.monotonic()
            if now >= started + LAST_START or started + WORK_SECONDS - now < minimum:
                failure(f"{phase['name']} UNRUN: phase-start cutoff/budget reached before launch")
                break
            deadline = min(started + WORK_SECONDS, now + maximum)
            passed = control.execute(helper, command, directory, phase["name"], deadline,
                                     min(started + CLEANUP_SECONDS, deadline + 5), phase, held)
            if passed:
                try:
                    if cache_binding(abi) != binding:
                        raise ValueError("Semantic cache/tool binding changed after regeneration")
                    if kind == "elf":
                        output = Path(binding["output"])
                        phase["elf"] = validate_elf(output, abi)
                        retained = directory / f"{abi}-lib{TARGET}.so"
                        retained.write_bytes(output.read_bytes())
                        phase["artifact"] = {"path": str(output), "retained": str(retained),
                                             "bytes": retained.stat().st_size,
                                             "sha256": control.file_hash(retained)}
                        if (control.file_hash(output) != phase["artifact"]["sha256"]
                                or phase["elf"]["sha256"] != phase["artifact"]["sha256"]):
                            raise ValueError("Artifact changed during validation/capture")
                        control.write_json(directory / f"{abi}-elf.json", phase["elf"])
                except BaseException as exc:
                    phase["errors"].append(f"Evidence: {type(exc).__name__}: {exc}")
                    phase["status"] = "FAIL_OR_INCOMPLETE"
                    passed = False
            if not passed:
                failure(f"{phase['name']} failed/incomplete: {json.dumps(phase)}")
                break
            persist()
    except BaseException as exc:
        failure(f"{type(exc).__name__}: {exc}")
    finally:
        for job in list(held):
            try:
                if not job.empty():
                    job.stop()
                    while time.monotonic() < started + CLEANUP_SECONDS and not job.empty():
                        time.sleep(0.05)
                if job.empty():
                    job.close()
                    held.remove(job)
            except BaseException as exc:
                failure(f"Final cleanup: {type(exc).__name__}: {exc}")
        if before is not None:
            try:
                after = snapshot(control)
                control.write_json(directory / "source-after.json", after)
                report["sourceSnapshotsIdentical"] = before["immutable"] == after["immutable"]
                report["generatedSnapshotsIdentical"] = before["generated"] == after["generated"]
                if not report["sourceSnapshotsIdentical"]:
                    failure("Immutable source/toolchain/semantic binding drift invalidates acceptance")
                for phase in report["phases"]:
                    if "artifact" in phase:
                        abi = phase["name"].rsplit("-", 1)[0]
                        if (len(after["artifacts"][abi]) != 1
                                or after["artifacts"][abi][0]["sha256"] != phase["artifact"]["sha256"]):
                            failure(f"{abi} output changed after retained ELF validation")
            except BaseException as exc:
                failure(f"Final snapshot: {type(exc).__name__}: {exc}")
        report.update(validationJobsTerminalConfirmed=not held,
                      status="RELEASE_PENDING_PUBLISHER" if not held else "HOLD/UNRELEASED")
        persist()
        publication = {"name": "publisher", "status": "UNRUN"}
        report["publication"] = publication
        try:
            message = directory / "release.txt"
            message.write_text(
                f"Web native-only {report['status']}; intended successor {args.next_owner}; "
                f"grant {args.grant}. NO SUCCESSOR GRANT: publisher is not yet terminal. "
                f"Validation Jobs terminal/empty={not held}; phases={json.dumps(report['phases'])}; "
                f"sourceStable={report['sourceSnapshotsIdentical']}; errors={json.dumps(report['errors'])}. "
                f"Evidence={directory.relative_to(ROOT).as_posix()}. Root must relay final job.json/stdout "
                f"after validation and publisher terminal/empty confirmation. "
                f"Native compile/ELF only; no Flutter/WSL/OHPM/Hvigor/HAP/device/debugger execution.\n",
                encoding="utf-8")
            if helper is None:
                raise RuntimeError("Pinned helper unavailable; explicit root relay required")
            if time.monotonic() >= started + TOTAL_SECONDS - 2:
                raise TimeoutError("Publisher budget exhausted; explicit root relay required")
            control.execute(helper, helper.channel_command(message, args.next_owner), directory,
                            "publisher", min(started + TOTAL_SECONDS - 1, time.monotonic() + 8),
                            started + TOTAL_SECONDS, publication, held)
            publication["delivered"] = publication["status"] == "PASS"
            if not publication["delivered"]:
                failure("Pending publication failed; explicit root relay required")
        except BaseException as exc:
            publication.update(delivered=False, error=f"{type(exc).__name__}: {exc}")
            failure(f"Publication: {type(exc).__name__}: {exc}")
        report.update(allOwnedJobsEmpty=not held, terminalConfirmed=not held, rootRelayRequired=True,
                      elapsedSeconds=round(time.monotonic() - started, 3), finishedUtc=control.utc())
        if held:
            report["status"] = "HOLD/UNRELEASED"
            failure("Unconfirmed cleanup; preserve exact Job handles and grant no successor")
        else:
            report["status"] = ("RELEASE" if publication.get("delivered") is True
                                else "RELEASE_PENDING_ROOT_RELAY")
        persist()
    try:
        print(json.dumps(report), flush=True)
    finally:
        if held:
            while True:
                time.sleep(0.5)  # Preserve exact handles even if final stdout failed.
    return 0 if (not report["errors"] and report["sourceSnapshotsIdentical"] is True
                 and all(phase["status"] == "PASS" for phase in report["phases"])
                 and report["publication"].get("delivered") is True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
