"""Bound a new, explicitly granted full Web app host gate; never claim a slot."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


RESEARCH = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
CORE = ROOT.parent / "qfli_studio_core"
HELPER = RESEARCH / "run-web-owned-window.py"
WORKER = RESEARCH / "run-web-app-worker.ps1"
HELPER_SHA256 = "9df7a94399aae38951337d61693d65de6e3cef438d02d4e51c787242dfda7fbe"
WORK_SECONDS, CLEANUP_SECONDS, TOTAL_SECONDS = 150, 170, 180
PHASES = (("format", 12, 12), ("tests", 110, 100),
          ("analysis", 25, 20), ("content", 6, 5))


def utc():
    return datetime.now(timezone.utc).isoformat()


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def load_helper():
    if file_hash(HELPER) != HELPER_SHA256:
        raise RuntimeError("Reviewed local owned-Job helper changed")
    specification = importlib.util.spec_from_file_location("web_app_owned_job", HELPER)
    if specification is None or specification.loader is None:
        raise RuntimeError("Cannot load reviewed local owned-Job helper")
    helper = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(helper)  # main is guarded; no Job starts here.
    return helper


def resolve_runtime_paths():
    # Use the running interpreter, never a second ambiguous PATH python lookup.
    python = Path(sys.executable).resolve(strict=True)
    if (not python.is_file() or python.suffix.casefold() != ".exe"
            or "windowsapps" in (part.casefold() for part in python.parts)):
        raise RuntimeError("Actual Python executable required; WindowsApps aliases are refused")
    flutter_command = shutil.which("flutter.bat")
    if not flutter_command:
        raise FileNotFoundError("Installed Windows flutter.bat missing")
    flutter = Path(flutter_command).resolve(strict=True)
    if not flutter.is_file() or flutter.name.casefold() != "flutter.bat":
        raise RuntimeError("One installed Flutter batch executable required")
    dart = flutter.parent / "cache/dart-sdk/bin/dart.exe"
    if not dart.is_file():
        raise FileNotFoundError(dart)
    powershell_command = shutil.which("powershell.exe")
    if not powershell_command:
        raise FileNotFoundError("Installed Windows PowerShell missing")
    powershell = Path(powershell_command).resolve(strict=True)
    if not powershell.is_file():
        raise FileNotFoundError(powershell)
    node_command = shutil.which("node.exe")
    return {"flutter": str(flutter), "dart": str(dart.resolve()), "python": str(python),
            "powershell.exe": str(powershell),
            "node": str(Path(node_command).resolve()) if node_command else None,
            "syntaxOverride": os.environ.get("QFLI_WEB_SYNTAX_LIBRARY")}


def snapshot():
    files = {Path(__file__).resolve(), HELPER, WORKER}
    for directory in (ROOT / "lib", ROOT / "test", ROOT / "integration_test",
                      ROOT / "tool", CORE / "lib", CORE / "vendor"):
        files.update(path.resolve() for path in directory.rglob("*.dart") if path.is_file())
    for base, patterns in (
        (ROOT, ("assets/content/**/*.json", "scripts/*.mjs", "scripts/*.py",
                "scripts/curriculum/**/*.py", "analysis_options.yaml", "pubspec.yaml",
                "pubspec.lock", ".dart_tool/package_config.json", "package.json",
                "package-lock.json", "node_modules/playwright/package.json",
                "node_modules/playwright-core/package.json",
                "node_modules/playwright-core/browsers.json")),
        (CORE, ("assets/content/**/*.json", "pubspec.yaml", "analysis_options.yaml",
                "vendor/**/pubspec.yaml")),
    ):
        for pattern in patterns:
            files.update(path.resolve() for path in base.glob(pattern) if path.is_file())
    required = (ROOT / "pubspec.yaml", ROOT / "pubspec.lock",
                ROOT / "analysis_options.yaml", ROOT / ".dart_tool/package_config.json",
                ROOT / "assets/content/examples.json", ROOT / "assets/content/tutorials.json",
                CORE / "pubspec.yaml", HELPER, WORKER)
    for path in required:
        if not path.is_file():
            raise FileNotFoundError(path)
    runtime_paths = resolve_runtime_paths()
    library = runtime_paths["syntaxOverride"]
    if library:
        native = Path(library).resolve()
        if not native.is_file():
            raise FileNotFoundError(native)
        files.add(native)
    native_inputs = [ROOT / "build/native/web_syntax/windows/qfli_web_syntax.dll",
                     ROOT / "assets/runtime/nginx/windows/nginx.exe"]
    if runtime_paths["flutter"]:
        flutter_bin = Path(runtime_paths["flutter"]).resolve().parent
        # Flutter tests resolve Nginx relative to flutter_tester before assets.
        native_inputs.append(flutter_bin / "cache/artifacts/engine/windows-x64/data/nginx/nginx.exe")
    for native in native_inputs:
        if native.is_file():
            files.add(native.resolve())
    core_head = subprocess.run(["git", "-C", str(CORE), "rev-parse", "HEAD"],
                               check=True, capture_output=True, text=True, timeout=5).stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", core_head):
        raise ValueError("Core HEAD identity was not a full commit hash")
    return {"coreHead": core_head, "runtimePaths": runtime_paths, "files": [
        {"path": os.path.relpath(path, ROOT).replace("\\", "/"),
         "bytes": path.stat().st_size, "sha256": file_hash(path)}
        for path in sorted(files, key=lambda item: str(item).casefold())]}


def execute(helper, command, directory, name, deadline, cleanup_deadline, phase, held):
    phase.update(status="RUNNING", command=command, startedUtc=utc(), errors=[])
    job = None
    terminal = False
    try:
        job = helper.OwnedJob()
        held.append(job)
        with (directory / f"{name}.stdout.log").open("xb", buffering=0) as out, \
             (directory / f"{name}.stderr.log").open("xb", buffering=0) as err:
            job.start(command, ROOT, os.environ.copy(), out, err)
            while time.monotonic() < deadline and not job.empty():
                time.sleep(0.05)
            phase["deadlineReached"] = not job.empty()
    except BaseException as exc:
        phase["errors"].append(f"{type(exc).__name__}: {exc}")
    finally:
        try:
            phase["forcedCleanup"] = job is not None and not job.empty()
            if phase["forcedCleanup"]:
                job.stop()
                while time.monotonic() < cleanup_deadline and not job.empty():
                    time.sleep(0.05)
            terminal = job is None or job.empty()
        except BaseException as exc:
            phase["errors"].append(f"Cleanup: {type(exc).__name__}: {exc}")
        phase.update(root=dict(job.record) if job is not None else {},
                     terminalConfirmed=terminal, finishedUtc=utc())
        phase["status"] = ("PASS" if terminal and phase["root"].get("exitCode") == 0
                           and not phase["errors"] and not phase.get("deadlineReached")
                           and not phase.get("forcedCleanup") else "FAIL_OR_INCOMPLETE")
        if job is not None and terminal:
            job.close()
            held.remove(job)
    return phase["status"] == "PASS"


def validate_phase(directory, phase):
    name = phase["name"]
    output = (directory / f"{name}.stdout.log").read_text(encoding="utf-8-sig", errors="replace")
    if name == "format":
        if re.search(r"Formatted 11 files \(0 changed\)", output) is None:
            raise ValueError("No complete unchanged formatter footer")
    elif name == "tests":
        footer = re.search(r"\+(\d+)(?:\s+~(\d+))?: All tests passed!", output)
        if footer is None:
            raise ValueError("No full test success footer; exit0 alone is insufficient")
        phase["testFooter"] = {"passed": int(footer[1]), "skipped": int(footer[2] or 0)}
        if phase["testFooter"]["passed"] == 0:
            raise ValueError("Full application gate requires executed tests")
    elif name == "analysis" and "No issues found" not in output:
        raise ValueError("No clean full-analysis footer")
    elif name == "content":
        content = (directory / "content-audit.md").read_text(encoding="utf-8")
        if re.findall(r"^Issues: (\d+)$", content, re.MULTILINE) != ["0"]:
            raise ValueError("Product content audit lacks an exact zero-issue result")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grant")
    parser.add_argument("--run-name")
    parser.add_argument("--next-owner")
    parser.add_argument("--snapshot-only", action="store_true",
                        help="Read hashes/core HEAD only; no grant, Job, SDK or report mutation")
    args = parser.parse_args()
    if args.snapshot_only:
        if any((args.grant, args.run_name, args.next_owner)):
            parser.error("Snapshot-only preflight takes no host-grant arguments")
        load_helper()
        source = snapshot()
        print(json.dumps({"snapshotOnly": True, "files": len(source["files"]),
                          "coreHead": source["coreHead"], "helperSha256": HELPER_SHA256,
                          "runtimePaths": source["runtimePaths"]}))
        return 0
    if (not args.grant or not args.grant.strip() or not args.run_name
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", args.run_name)
            or not args.next_owner or not re.fullmatch(r"[a-z][a-z0-9_-]+", args.next_owner)):
        parser.error("Runtime requires --grant, a fresh simple --run-name and one --next-owner")
    directory = RESEARCH / args.run_name
    directory.mkdir(exist_ok=False)
    started = time.monotonic()
    report_path = directory / "job.json"
    report = {"schemaVersion": 1, "grant": args.grant, "nextOwner": args.next_owner,
              "startedUtc": utc(), "budgetSeconds": {"work": WORK_SECONDS,
              "cleanup": CLEANUP_SECONDS, "total": TOTAL_SECONDS},
              "helperSha256": HELPER_SHA256, "errors": [], "firstError": None,
              "phases": [{"name": name, "status": "UNRUN"} for name, _, _ in PHASES],
              "sourceSnapshotsIdentical": None}
    helper, before, held = None, None, []

    def failure(message):
        report["errors"].append(message)
        if report["firstError"] is None:
            report["firstError"] = message

    def persist():
        try:
            write_json(report_path, report)
        except BaseException as exc:
            failure(f"Report persistence: {type(exc).__name__}: {exc}")

    write_json(report_path, report)
    try:
        if os.name != "nt":
            raise RuntimeError("This host supervisor is Windows-only")
        helper = load_helper()
        before = snapshot()  # Before format CHECK and every executable validation.
        write_json(directory / "source-before.json", before)
        report["coreHead"] = before["coreHead"]
        report["runtimePaths"] = before["runtimePaths"]
        for phase, (_, maximum, minimum) in zip(report["phases"], PHASES):
            remaining = started + WORK_SECONDS - time.monotonic()
            if remaining < minimum or held:
                phase["reason"] = (f"Minimum{minimum}s exceeds remaining{remaining:.3f}s"
                                   if not held else "Prior Job cleanup unconfirmed")
                failure(f"{phase['name']} UNRUN: {phase['reason']}")
                continue
            command = [report["runtimePaths"]["powershell.exe"],
                       "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass",
                       "-File", str(WORKER), "-Phase", phase["name"],
                       "-EvidenceDirectory", str(directory),
                       "-FlutterExecutable", report["runtimePaths"]["flutter"],
                       "-PythonExecutable", report["runtimePaths"]["python"], "-OwnedWorker"]
            deadline = min(started + WORK_SECONDS, time.monotonic() + maximum)
            write_json(report_path, report)
            passed = execute(helper, command, directory, phase["name"], deadline,
                             min(started + CLEANUP_SECONDS, deadline + 5), phase, held)
            if passed:
                try:
                    validate_phase(directory, phase)
                except BaseException as exc:
                    phase["errors"].append(f"Evidence: {type(exc).__name__}: {exc}")
                    phase["status"] = "FAIL_OR_INCOMPLETE"
                    passed = False
            if not passed:
                failure(f"{phase['name']} failed/incomplete: {json.dumps(phase)}")
            write_json(report_path, report)
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
                after = snapshot()
                write_json(directory / "source-after.json", after)
                report["sourceSnapshotsIdentical"] = before == after
                if before != after:
                    failure("Raw input/core HEAD drift invalidates frozen-source acceptance")
            except BaseException as exc:
                failure(f"Final snapshot: {type(exc).__name__}: {exc}")
        report.update(validationJobsTerminalConfirmed=not held,
                      status="RELEASE_PENDING_PUBLISHER" if not held else "HOLD/UNRELEASED",
                      elapsedSeconds=round(time.monotonic() - started, 3), finishedUtc=utc())
        persist()
        message = directory / "release.txt"
        publication = {"name": "publisher", "status": "UNRUN"}
        report["publication"] = publication
        try:
            message.write_text(
                f"Web full-app {report['status']}; intended successor {args.next_owner}; "
                f"grant {args.grant}. NO SUCCESSOR GRANT: publisher is not yet terminal. "
                f"Validation Jobs terminal/empty={not held}; phases={json.dumps(report['phases'])}; "
                f"sourceStable={report['sourceSnapshotsIdentical']}; errors={json.dumps(report['errors'])}; "
                f"elapsed={report['elapsedSeconds']}s; evidence={directory.relative_to(ROOT).as_posix()}. "
                f"Root must relay final job.json/stdout after validation and publisher Jobs are terminal/empty. "
                f"Host only; no core/native/HAP/device mutation.\n", encoding="utf-8")
            if helper is None:
                raise RuntimeError("Reviewed helper unavailable; explicit manual relay required")
            if time.monotonic() >= started + TOTAL_SECONDS - 2:
                raise TimeoutError("Publication budget exhausted; explicit manual relay required")
            execute(helper, helper.channel_command(message, args.next_owner), directory, "publisher",
                    min(started + TOTAL_SECONDS - 1, time.monotonic() + 8),
                    started + TOTAL_SECONDS, publication, held)
            publication["delivered"] = publication["status"] == "PASS"
            if not publication["delivered"]:
                failure("Channel publication failed; explicit manual relay required")
        except BaseException as exc:
            publication.update(delivered=False, error=f"{type(exc).__name__}: {exc}")
            failure(f"Publication: {type(exc).__name__}: {exc}")
        report["allOwnedJobsEmpty"] = not held
        report["terminalConfirmed"] = not held
        report["rootRelayRequired"] = True
        report["elapsedSeconds"] = round(time.monotonic() - started, 3)
        report["finishedUtc"] = utc()
        if held:
            report["status"] = "HOLD/UNRELEASED"
            failure("Unconfirmed cleanup; retain exact handles and do not grant a successor")
        elif publication.get("delivered") is True:
            report["status"] = "RELEASE"
        else:
            report["status"] = "RELEASE_PENDING_ROOT_RELAY"
        persist()
    try:
        print(json.dumps(report), flush=True)
    finally:
        if held:
            while True:  # Preserve ownership even if stdout/report persistence fails.
                time.sleep(0.5)
    return 0 if (not report["errors"] and report["sourceSnapshotsIdentical"] is True
                 and all(phase["status"] == "PASS" for phase in report["phases"])
                 and report["publication"].get("delivered") is True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
