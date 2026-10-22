#!/usr/bin/env python3
"""Preflight exact WebForge HAPs, then optionally run the real OHOS catalog.

The default is read-only device/archive preflight. --run explicitly opts into
installing both inspected HAPs, launching the test ability, forwarding CDP,
running the existing semantic oracles, and targeted test-ability cleanup.
Coordinate exclusive use of the specified live target before using --run.
No host-browser fallback or device/emulator/service startup is provided.
Signatures/profiles are required by default. --unsigned-emulator explicitly
allows ordinary unsigned installation only on a live x86_64 emulator; that
mode records no verified signing or physical-device proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile

from prepare_ohos_catalog import OUTPUT, ROOT, atomic_write, staged_files

BUNDLE = "com.azurekiln.qfli.webforge"
BOOTSTRAP = "http://127.0.0.1:19999/__qfli_catalog/bootstrap"
PARAMETERS = ("const.ohos.fullname", "const.ohos.apiversion", "const.product.devicetype")
EMULATOR_MODEL_PARAMETER = "const.product.model"
EMULATOR_LIBRARIES = ("libapp.so", "libflutter.so", "libqfli_web_syntax.so", "libqfli_nginx_napi.so")


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def execute(arguments: list[str], timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(arguments, cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout, check=False)


def output(result: subprocess.CompletedProcess) -> str:
    return (result.stdout + "\n" + result.stderr).strip()


class Device:
    def __init__(self, executable: str, target: str):
        self.executable, self.target = executable, target

    def require_live(self) -> None:
        result = execute([self.executable, "list", "targets"])
        targets = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if result.returncode or not self.target or self.target.startswith("[") or self.target not in targets:
            raise ValueError("The exact --device target is not live (hdc list targets); no device action performed")

    def call(self, *arguments: str) -> str:
        result = execute([self.executable, "-t", self.target, *arguments])
        text = output(result)
        if result.returncode or re.search(r"\[Fail\]|\berror:", text, re.IGNORECASE):
            raise ValueError(f"HDC {arguments[0]} failed: {text.replace(self.target, '<selected-target>')[:700]}")
        return text


def require_unsigned_emulator(device: Device) -> dict[str, str]:
    model = device.call("shell", "param", "get", EMULATOR_MODEL_PARAMETER).strip()
    architecture = device.call("shell", "uname", "-m").strip()
    if model != "emulator" or architecture != "x86_64":
        raise ValueError("--unsigned-emulator requires the selected live target's actual model emulator and uname -m x86_64")
    return {"model": model, "architecture": architecture}


def inspect_emulator_runtime(path: Path, artifact: dict) -> dict:
    """Require actual x86_64 ELF runtime members, not just an ABI directory."""
    recorded = {item["path"]: item["sha256"] for item in artifact["nativeLibraries"]}
    libraries = []
    with zipfile.ZipFile(path) as archive:
        for library in EMULATOR_LIBRARIES:
            member = f"libs/x86_64/{library}"
            if member not in recorded:
                raise ValueError(f"{path.name}: unsigned emulator requires packaged x86_64 {library}")
            payload = archive.read(member)
            if len(payload) < 20 or payload[:6] != b"\x7fELF\x02\x01" or \
                    int.from_bytes(payload[18:20], "little") != 62 or sha(payload) != recorded[member]:
                raise ValueError(f"{path.name}: {member} is not the inspected little-endian ELF64 x86_64 runtime")
            libraries.append({"path": member, "sha256": recorded[member], "elfMachine": 62})
    return {"abi": "x86_64", "libraries": libraries}


def find_sign_tool(explicit: Path | None, hdc: str) -> Path:
    candidates = [explicit] if explicit else [Path(hdc).parent / "lib/hap-sign-tool.jar"]
    for name in ("DEVECO_SDK_HOME", "OHOS_SDK_HOME"):
        if os.environ.get(name):
            base = Path(os.environ[name])
            candidates.extend(base / suffix for suffix in (
                "openharmony/toolchains/lib/hap-sign-tool.jar", "toolchains/lib/hap-sign-tool.jar",
                "default/openharmony/toolchains/lib/hap-sign-tool.jar"))
    for candidate in candidates:
        if candidate is not None and candidate.is_file():
            return candidate.resolve()
    raise ValueError("Official SDK hap-sign-tool.jar not found; supply --sign-tool")


def verify_signature(path: Path, sign_tool: Path, java: str) -> dict:
    # Exported profile content may include device IDs. Keep it only in this
    # temporary directory and persist only the explicitly selected public fields.
    with tempfile.TemporaryDirectory(prefix="qfli-hap-verify-") as directory:
        folder = Path(directory)
        certificate, profile, verified = (folder / name for name in ("chain.cer", "profile.p7b", "verified.json"))
        for operation, parameters in (
            ("verify-app", ["-inFile", str(path), "-outCertChain", str(certificate), "-outProfile", str(profile)]),
            ("verify-profile", ["-inFile", str(profile), "-outFile", str(verified)]),
        ):
            result = execute([java, "-jar", str(sign_tool), operation, *parameters], timeout=60)
            # The SDK CLI can exit zero after a verification failure. Require
            # its positive operation result and actual verification outputs.
            if result.returncode or not re.search(rf"\b{operation} success\b", output(result)):
                raise ValueError(f"{path.name}: official SDK {operation} did not verify successfully")
        result = json.loads(verified.read_text(encoding="utf-8"))
        if result.get("verifiedPassed") is not True:
            raise ValueError(f"{path.name}: provisioning profile signature was not verified")
        content = result.get("content", {})
        if content.get("bundle-info", {}).get("bundle-name") != BUNDLE:
            raise ValueError(f"{path.name}: provisioning profile is not bound to {BUNDLE}")
        validity = content.get("validity", {})
        if not validity.get("not-before", float("inf")) <= time.time() < validity.get("not-after", 0):
            raise ValueError(f"{path.name}: provisioning profile is not currently valid")
        return {"verified": True, "certificateChainSha256": sha(certificate.read_bytes()),
                "profileSha256": sha(profile.read_bytes()), "profileType": content.get("type"),
                "profileBundleName": BUNDLE, "validity": validity}


def inspect_archive(path: Path, kind: str, expected: dict[str, bytes]) -> dict:
    before = sha(path.read_bytes())
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError(f"{path.name}: duplicate archive paths")
        metadata = json.loads(archive.read("module.json"))
        app, module = metadata["app"], metadata["module"]
        expected_module, expected_type, expected_ability = (
            ("entry", "entry", "EntryAbility") if kind == "production" else ("entry_test", "feature", "TestAbility"))
        if app.get("bundleName") != BUNDLE or module.get("name") != expected_module or \
                module.get("type") != expected_type or module.get("mainElement") != expected_ability:
            raise ValueError(f"{path.name}: unexpected bundle/module/ability identity")
        abilities = [item for item in module.get("abilities", []) if item.get("name") == expected_ability]
        if len(abilities) != 1 or not abilities[0].get("exported"):
            raise ValueError(f"{path.name}: expected exported ability missing")
        if kind == "test" and abilities[0].get("launchType") != "singleton":
            raise ValueError(f"{path.name}: targeted test-ability cleanup requires singleton launchType")
        prefix = "resources/rawfile/"
        files = {}
        for name in ("examples.json", "tutorials.json"):
            member = prefix + (f"flutter_assets/assets/content/{name}" if kind == "production" else f"ohos_catalog/{name}")
            payload = archive.read(member)
            if payload != expected[name]:
                raise ValueError(f"{path.name}: {member} differs from current source/staging")
            files[name] = {"path": member, "bytes": len(payload), "sha256": sha(payload)}
        bytecode = archive.read("ets/modules.abc")
        if kind == "test":
            if archive.read(prefix + "ohos_catalog/manifest.json") != expected["manifest.json"] or \
                    b"CatalogHarness" not in bytecode or b"qfliCatalogStop" not in bytecode:
                raise ValueError(f"{path.name}: current compiled harness/manifest is missing")
        elif any(name.startswith(prefix + "ohos_catalog/") for name in names) or b"CatalogHarness" in bytecode:
            raise ValueError(f"{path.name}: test-only harness leaked into production HAP")
        native = [{"path": name, "sha256": sha(archive.read(name))} for name in names
                  if name.startswith("libs/") and name.endswith(".so")]
        if kind == "production" and not any(item["path"].endswith("/libqfli_nginx_napi.so") for item in native):
            raise ValueError(f"{path.name}: packaged WebForge native engine missing")
    if sha(path.read_bytes()) != before:
        raise ValueError(f"{path.name}: archive changed during preflight")
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": before,
            "bundleName": app["bundleName"], "moduleName": module["name"], "abilityName": expected_ability,
            "versionCode": app.get("versionCode"), "versionName": app.get("versionName"),
            "buildMode": app.get("buildMode"), "compileSdkVersion": app.get("compileSdkVersion"),
            "minAPIVersion": app.get("minAPIVersion"), "targetAPIVersion": app.get("targetAPIVersion"),
            "bytecodeSha256": sha(bytecode), "catalogs": files, "nativeLibraries": native}


def wait_for_bootstrap(endpoint: str) -> None:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(endpoint + "/json/list", timeout=1) as response:
                targets = json.load(response)
            if isinstance(targets, list) and any(item.get("url") == BOOTSTRAP for item in targets):
                return
        except (OSError, ValueError):
            pass
        time.sleep(0.25)
    raise ValueError("The forwarded native ArkWeb bootstrap target did not become ready")


def abstract_sockets(device: Device) -> set[str]:
    return {line.split()[-1][1:] for line in device.call("shell", "cat", "/proc/net/unix").splitlines()
            if line.split() and line.split()[-1].startswith("@")}


def debug_socket(device: Device, previous: set[str], requested: str | None) -> str:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        current = abstract_sockets(device)
        if requested:
            name = requested.lstrip("@")
            if name in current:
                return name
        else:
            candidates = {name for name in current - previous if "devtools" in name.lower()}
            if len(candidates) == 1:
                return candidates.pop()
            if len(candidates) > 1:
                raise ValueError("Several new debug sockets appeared; use an explicitly observed --unix-socket")
        time.sleep(0.25)
    raise ValueError("No unique observed native debug socket became ready; inspect selected target /proc/net/unix")


def validate_report(path: Path, expected: dict[str, bytes], parameters: dict[str, str]) -> dict:
    report = json.loads(path.read_text(encoding="utf-8"))
    manifest = json.loads(expected["manifest.json"])
    source_codes = {item["id"]: item["code"] for item in json.loads(expected["examples.json"])["entries"]}
    ids = set(source_codes)
    catalog = report.get("catalog", {})
    results = report.get("results", [])
    if report.get("runtime") != "ohos-arkweb" or report.get("device", {}).get("manifest") != manifest or \
            catalog.get("complete") is not True or catalog.get("executedExamples") != len(ids) or \
            catalog.get("totalExamples") != len(ids) or catalog.get("totalLessons") != manifest["counts"]["lessons"] or \
            report.get("passed") != len(ids) or \
            report.get("failed") != 0 or report.get("mappingIssues") != [] or \
            len(results) != len(ids) or {item.get("id") for item in results} != ids or \
            any(item.get("pass") is not True for item in results):
        raise ValueError("Native semantic report is incomplete, failed, or uses another catalog/runtime")
    for item in results:
        assertions = item.get("assertions", [])
        if item.get("codeSha256") != sha(source_codes[item["id"]].encode()) or not assertions or \
                item.get("checks") != len(assertions) or any(check.get("ok") is not True for check in assertions):
            raise ValueError("Native per-entry code hash/assertion evidence is incomplete or failed")
    if report.get("totalChecks") != sum(item["checks"] for item in results) or \
            not report.get("device", {}).get("runId") or not report.get("browserVersion"):
        raise ValueError("Native assertion/session/browser evidence is incomplete")
    for kind in ("examples", "tutorials"):
        if catalog.get(kind + "Sha256") != sha(expected[kind + ".json"]):
            raise ValueError(f"Native report {kind} source hash differs")
    environment = report.get("device", {}).get("environment", {})
    if environment.get("bundleName") != BUNDLE or environment.get("moduleName") != "entry_test" or \
            environment.get("abilityName") != "TestAbility" or not environment.get("deviceType") or \
            not environment.get("osFullName") or type(environment.get("sdkApiVersion")) is not int:
        raise ValueError("Native public ability/OS environment evidence is missing")
    for parameter, field in ((PARAMETERS[0], "osFullName"), (PARAMETERS[1], "sdkApiVersion"),
                             (PARAMETERS[2], "deviceType")):
        if parameters.get(parameter) and parameters[parameter] != str(environment[field]):
            raise ValueError(f"Native {field} differs from selected HDC target public parameter")
    return {"report": str(path), "reportSha256": sha(path.read_bytes()), "environment": environment,
            "runId": report["device"]["runId"], "browserVersion": report.get("browserVersion"),
            "passed": report["passed"], "totalChecks": report.get("totalChecks")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", required=True, help="exact currently live HDC target; never auto-selected")
    parser.add_argument("--production-hap", type=Path, required=True)
    parser.add_argument("--test-hap", type=Path, required=True)
    parser.add_argument("--run", action="store_true", help="install/launch/forward/run after exclusive device coordination")
    parser.add_argument("--unsigned-emulator", action="store_true",
                        help="explicit unsigned installation on actual model emulator + x86_64 only; never signed proof")
    parser.add_argument("--report", type=Path, default=ROOT / "build/content/ohos-catalog.md")
    parser.add_argument("--hdc", default=shutil.which("hdc"))
    parser.add_argument("--java", default=shutil.which("java"))
    parser.add_argument("--node", default=shutil.which("node"))
    parser.add_argument("--sign-tool", type=Path)
    parser.add_argument("--cdp-mode", choices=("tcp", "unix"), default="tcp")
    parser.add_argument("--port", type=int, default=9222, help="unused host/device CDP TCP port1025..65535")
    parser.add_argument("--unix-socket", help="exact observed abstract debug socket; otherwise require one newly created devtools socket")
    args = parser.parse_args()
    report = args.report.resolve()
    evidence_path = report.with_suffix(".device.json")
    evidence = {"schemaVersion": 1, "runtime": "ohos-arkweb", "status": "preflight-pending",
                "startedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "targetSelectionSha256": sha(args.device.encode()), "runRequested": args.run,
                "signingMode": "unsigned-emulator" if args.unsigned_emulator else "official-signature"}
    device = None
    forwarded = False
    launched = False
    exit_code = 1
    try:
        if not args.hdc or not args.node or (not args.unsigned_emulator and not args.java) or \
                not 1024 < args.port <= 65535:
            raise ValueError("HDC, Node, Java for signature verification, and a CDP port1025..65535 are required")
        device = Device(args.hdc, args.device)
        device.require_live()  # fail before any install/launch/forward or archive work
        if args.unsigned_emulator:
            evidence["emulatorIdentity"] = require_unsigned_emulator(device)
        print(f"Exact live HDC target verified; inspecting current catalogs and HAPs ({evidence['signingMode']}).", flush=True)
        expected = staged_files(ROOT)
        for name, payload in expected.items():
            if not (OUTPUT / name).is_file() or (OUTPUT / name).read_bytes() != payload:
                raise ValueError("Test staging is stale; run scripts/prepare_ohos_catalog.py before packaging")
        sign_tool = None
        if not args.unsigned_emulator:
            sign_tool = find_sign_tool(args.sign_tool, args.hdc)
            evidence["signatureVerifier"] = {"path": str(sign_tool), "sha256": sha(sign_tool.read_bytes())}
        evidence["artifacts"] = {}
        for kind, path in (("production", args.production_hap), ("test", args.test_hap)):
            path = path.resolve(strict=True)
            artifact = inspect_archive(path, kind, expected)
            if args.unsigned_emulator:
                artifact["signature"] = {"verified": False, "verification": "not-performed",
                                         "reason": "explicit unsigned-emulator mode; no signature/profile proof"}
                if kind == "production":
                    artifact["emulatorRuntime"] = inspect_emulator_runtime(path, artifact)
            else:
                artifact["signature"] = verify_signature(path, sign_tool, args.java)
            if sha(path.read_bytes()) != artifact["sha256"]:
                raise ValueError(f"{path.name}: archive changed during artifact verification")
            evidence["artifacts"][kind] = artifact
        production, test = evidence["artifacts"].values()
        if any(production[key] != test[key] for key in ("versionCode", "versionName")):
            raise ValueError("Production/test HAP versions differ")
        if not args.unsigned_emulator and \
                production["signature"]["certificateChainSha256"] != test["signature"]["certificateChainSha256"]:
            raise ValueError("Production/test verified signing certificates differ")
        parameters = {name: device.call("shell", "param", "get", name).strip() for name in PARAMETERS}
        if not parameters[PARAMETERS[0]] or not parameters[PARAMETERS[1]].isdigit():
            raise ValueError("Selected device did not return public OS name/SDK API parameter evidence")
        evidence["publicDeviceParameters"] = parameters
        evidence["manifest"] = json.loads(expected["manifest.json"])
        evidence["status"] = "preflight-passed"
        if args.run:
            if args.cdp_mode == "tcp" and int(parameters[PARAMETERS[1]]) < 20:
                raise ValueError("TCP CDP requires device API20+; use the observed Unix debug socket on API9..19")
            if args.unix_socket and not re.fullmatch(r"[A-Za-z0-9_.@-]+", args.unix_socket):
                raise ValueError("Invalid --unix-socket; use the exact observed abstract socket name")
            previous_sockets = abstract_sockets(device) if args.cdp_mode == "unix" else set()
            local = f"tcp:{args.port}"
            if local in device.call("fport", "ls"):
                raise ValueError("Chosen CDP port already belongs to an HDC forward; choose another --port")
            with socket.socket() as probe:
                probe.bind(("127.0.0.1", args.port))
            device.require_live()
            if args.unsigned_emulator and require_unsigned_emulator(device) != evidence["emulatorIdentity"]:
                raise ValueError("Selected emulator identity changed after preflight")
            for kind, artifact in evidence["artifacts"].items():
                if sha(Path(artifact["path"]).read_bytes()) != artifact["sha256"]:
                    raise ValueError(f"{kind} HAP changed after artifact preflight")
            if staged_files(ROOT) != expected:
                raise ValueError("Source catalogs changed after HAP preflight")
            print(f"Installing the two inspected HAPs on the coordinated target ({evidence['signingMode']}).", flush=True)
            installed = device.call("install", "-r", production["path"], test["path"])
            if not re.search(r"\bsuccess", installed, re.IGNORECASE):
                raise ValueError("HDC did not positively acknowledge HAP installation")
            evidence["installation"] = {"acknowledged": True}
            launch = device.call("shell", "aa", "start", "-b", BUNDLE, "-m", "entry_test", "-a", "TestAbility",
                                 "--ps", "qfliCatalogCdp", args.cdp_mode, "--pi", "qfliCatalogPort", str(args.port))
            launched = True
            if "start ability successfully" not in launch.lower():
                raise ValueError("Test ability launch was not positively acknowledged")
            remote = ("localabstract:" + debug_socket(device, previous_sockets, args.unix_socket)
                      if args.cdp_mode == "unix" else f"tcp:{args.port}")
            device.call("fport", local, remote)
            forwarded = True
            evidence["forward"] = {"local": local, "remote": remote}
            endpoint = f"http://127.0.0.1:{args.port}"
            wait_for_bootstrap(endpoint)
            report.parent.mkdir(parents=True, exist_ok=True)
            semantic_json = report.with_suffix(".json") if report.suffix.lower() == ".md" else Path(str(report) + ".json")
            prior_hash = sha(semantic_json.read_bytes()) if semantic_json.exists() else None
            print("Running every packaged example in native ArkWeb through the semantic runner.", flush=True)
            with report.with_suffix(".runner.log").open("w", encoding="utf-8") as log:
                result = subprocess.run([args.node, str(ROOT / "scripts/run_examples.mjs"), "--ohos-cdp", endpoint,
                                         "--report", str(report)], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                        timeout=3600, check=False)
            if result.returncode:
                raise ValueError("Native semantic runner failed; inspect its report and .runner.log")
            if prior_hash is not None and semantic_json.is_file() and sha(semantic_json.read_bytes()) == prior_hash:
                raise ValueError("Semantic runner did not produce a fresh report")
            evidence["semantic"] = validate_report(semantic_json, expected, parameters)
            if staged_files(ROOT) != expected:
                raise ValueError("Source catalogs changed during native semantic verification")
            evidence["status"] = "passed"
        exit_code = 0
    except (OSError, ValueError, KeyError, TypeError, AttributeError, zipfile.BadZipFile, subprocess.SubprocessError) as failure:
        evidence["status"] = "failed"
        evidence["error"] = str(failure).replace(args.device, "<selected-target>")
        print("OHOS catalog verification failed: " + evidence["error"], file=sys.stderr)
    finally:
        cleanup = []
        if device is not None and forwarded:
            try:
                device.call("fport", "rm", f"tcp:{args.port}", evidence["forward"]["remote"])
                if f"tcp:{args.port}" in device.call("fport", "ls"):
                    raise ValueError("Owned HDC forward remains after cleanup")
                cleanup.append("owned HDC forward removed")
            except (OSError, ValueError, subprocess.SubprocessError):
                cleanup.append("owned HDC forward removal failed")
                exit_code = 1
        if device is not None and launched:
            try:
                stopped = device.call("shell", "aa", "start", "-b", BUNDLE, "-m", "entry_test", "-a", "TestAbility",
                                      "--pb", "qfliCatalogStop", "true")
                if "start ability successfully" not in stopped.lower():
                    raise ValueError("Targeted test ability stop was not acknowledged")
                cleanup.append("targeted test ability stop requested")
            except (OSError, ValueError, subprocess.SubprocessError):
                cleanup.append("targeted test ability stop request failed")
                exit_code = 1
        evidence["cleanup"] = cleanup
        if exit_code and evidence["status"] == "passed":
            evidence["status"] = "cleanup-failed"
        evidence["completedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(evidence_path, (json.dumps(evidence, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(f"{evidence['status']}: {evidence_path}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
