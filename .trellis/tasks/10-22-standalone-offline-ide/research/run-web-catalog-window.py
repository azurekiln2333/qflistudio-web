"""Run one explicitly granted, bounded Windows browser catalog window."""
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
import sys
import time


RESEARCH = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
HELPER = RESEARCH / "run-web-owned-window.py"
HELPER_SHA256 = "9df7a94399aae38951337d61693d65de6e3cef438d02d4e51c787242dfda7fbe"
VIEWPORTS = {"desktop": {"width": 1280, "height": 720},
             "mobile": {"width": 390, "height": 844}}
CONTROL_IDS = {"js-example-052", "js-example-053"}
WORK_SECONDS, CLEANUP_SECONDS, TOTAL_SECONDS = 300, 320, 330


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


def snapshot():
    files = {Path(__file__).resolve(), HELPER}
    for pattern in ("assets/content/**/*.json", "scripts/*.mjs",
                    "scripts/curriculum/**/*.py", "scripts/emit_content.py",
                    "scripts/audit_web_content.py", "scripts/test_emit_content.py",
                    "package.json", "package-lock.json", "pubspec.yaml", "pubspec.lock",
                    "node_modules/playwright/package.json",
                    "node_modules/playwright-core/package.json"):
        files.update(path.resolve() for path in ROOT.glob(pattern) if path.is_file())
    required = ("assets/content/examples.json", "assets/content/tutorials.json",
                "scripts/run_examples.mjs", "scripts/js_example_assertions.mjs",
                "package.json", "package-lock.json", "pubspec.yaml", "pubspec.lock")
    for relative in required:
        if not (ROOT / relative).is_file():
            raise FileNotFoundError(relative)
    return [{"path": path.relative_to(ROOT).as_posix(),
             "bytes": path.stat().st_size, "sha256": file_hash(path)}
            for path in sorted(files, key=lambda item: str(item).casefold())]


def runtime_provenance():
    resolved = {"python": sys.executable, "node": shutil.which("node.exe")}
    provenance = {}
    for name, executable in resolved.items():
        if not isinstance(executable, str) or not executable:
            raise FileNotFoundError(f"Actual scalar {name} executable missing; no install attempted")
        path = Path(executable).resolve()
        if (not path.is_file() or path.suffix.casefold() != ".exe"
                or any(part.casefold() == "windowsapps" for part in path.parts)):
            raise ValueError(f"Invalid/alias {name} executable: {path}")
        provenance[name] = {"path": str(path), "bytes": path.stat().st_size,
                            "sha256": file_hash(path)}
    return provenance


def load_helper():
    actual = file_hash(HELPER)
    if actual != HELPER_SHA256:
        raise RuntimeError(f"Reviewed owned-Job helper changed: {actual}")
    specification = importlib.util.spec_from_file_location("web_catalog_owned_job", HELPER)
    if specification is None or specification.loader is None:
        raise RuntimeError("Cannot load the reviewed local owned-Job helper")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)  # Its guarded main is not invoked.
    return module


def validate_report(path, expected, viewport, full):
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("Browser report is not an object")
    catalog = data.get("catalog")
    results = data.get("results")
    expected_ids = expected["ids"] if full else CONTROL_IDS
    if not isinstance(catalog, dict) or not isinstance(results, list):
        raise ValueError("Missing catalog/results in browser report")
    conditions = {
        "schema": data.get("schemaVersion") == 1,
        "host runtime": data.get("runtime") == "host-chromium" and data.get("device") is None,
        "viewport": data.get("viewport") == viewport,
        "browser identity": isinstance(data.get("browserVersion"), str) and bool(data["browserVersion"]),
        "timestamps": isinstance(data.get("startedAt"), str) and isinstance(data.get("completedAt"), str),
        "examples hash": catalog.get("examplesSha256") == expected["examplesSha256"],
        "tutorials hash": catalog.get("tutorialsSha256") == expected["tutorialsSha256"],
        "catalog count": catalog.get("totalExamples") == 481 and catalog.get("totalLessons") == 481,
        "executed count": catalog.get("executedExamples") == len(expected_ids),
        "complete flag": catalog.get("complete") is full,
        "pass count": data.get("passed") == len(expected_ids) and data.get("failed") == 0,
        "mapping": data.get("mappingIssues") == [],
        "assertion count": isinstance(data.get("totalChecks"), int) and data["totalChecks"] > 0,
        "row count": len(results) == len(expected_ids),
    }
    observed_ids = []
    for result in results:
        if not isinstance(result, dict):
            raise ValueError("Non-object browser result row")
        observed_ids.append(result.get("id"))
        if (result.get("pass") is not True or result.get("failed") != []
                or result.get("errors") != [] or result.get("blockedRequests") != []
                or not isinstance(result.get("checks"), int) or result["checks"] <= 0):
            raise ValueError(f"Failed/incomplete result row: {result.get('id')}")
        assertions = result.get("assertions")
        if (not isinstance(assertions, list) or len(assertions) != result["checks"]
                or any(not isinstance(item, dict) or item.get("ok") is not True
                       for item in assertions)):
            raise ValueError(f"Failed/incomplete assertions: {result.get('id')}")
    conditions["exact IDs"] = (len(observed_ids) == len(set(observed_ids))
                               and set(observed_ids) == expected_ids)
    failed = [name for name, passed in conditions.items() if not passed]
    if failed:
        raise ValueError("Browser report rejected: " + ", ".join(failed))
    return {"passed": data["passed"], "failed": data["failed"],
            "checks": data["totalChecks"], "complete": catalog["complete"],
            "browserVersion": data["browserVersion"], "viewport": data["viewport"],
            "reportSha256": file_hash(path), "validation": conditions}


def execute(helper, command, directory, name, deadline, cleanup_deadline, record, held):
    """Contain before resume; a terminal root with a live child still fails."""
    record.update(status="RUNNING", startedUtc=utc(), command=command, errors=[])
    job = None
    terminal = False
    try:
        job = helper.OwnedJob()
        held.append(job)
        with (directory / f"{name}.stdout.log").open("xb", buffering=0) as out, \
             (directory / f"{name}.stderr.log").open("xb", buffering=0) as err:
            job.start(command, ROOT, os.environ.copy(), out, err)
            while time.monotonic() < deadline:
                if job.empty():
                    break
                time.sleep(0.05)
            record["deadlineReached"] = not job.empty()
            record["orphanCleanup"] = (record["deadlineReached"]
                                       and job.record.get("terminal", False)
                                       and job.record.get("jobActiveProcesses", 0) > 0)
    except BaseException as exc:
        record["errors"].append(f"{type(exc).__name__}: {exc}")
    finally:
        try:
            if job is not None and not job.empty():
                job.stop()
                while time.monotonic() < cleanup_deadline and not job.empty():
                    time.sleep(0.05)
            terminal = job is None or job.empty()
        except BaseException as exc:
            record["errors"].append(f"Cleanup: {type(exc).__name__}: {exc}")
        record.update(root=dict(job.record) if job is not None else {},
                      terminalConfirmed=terminal, finishedUtc=utc())
        record["status"] = ("PASS" if terminal and record["root"].get("exitCode") == 0
                            and not record["errors"] and not record.get("deadlineReached")
                            and not record.get("orphanCleanup") else "FAIL_OR_INCOMPLETE")
        if job is not None and terminal:
            job.close()
            held.remove(job)
    return record["status"] == "PASS"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grant", required=True, help="Already accepted NEW named host handoff")
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--next-owner", required=True)
    parser.add_argument("--viewport", choices=sorted(VIEWPORTS), required=True)
    args = parser.parse_args()
    if (not args.grant.strip() or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", args.run_name)
            or not re.fullmatch(r"[a-z][a-z0-9_-]+", args.next_owner)):
        parser.error("Explicit grant, fresh simple run name and one named successor required")
    directory = RESEARCH / args.run_name
    directory.mkdir(exist_ok=False)  # Reject reuse before touching historical evidence.
    started = time.monotonic()
    report_path = directory / "job.json"
    report = {"schemaVersion": 1, "grant": args.grant, "nextOwner": args.next_owner,
              "startedUtc": utc(), "viewport": VIEWPORTS[args.viewport],
              "budgetSeconds": {"work": WORK_SECONDS, "cleanup": CLEANUP_SECONDS,
                                "total": TOTAL_SECONDS},
              "helperSha256": HELPER_SHA256, "errors": [], "firstError": None,
              "phases": [{"name": name, "status": "UNRUN"} for name in ("controls", "full")],
              "sourceSnapshotsIdentical": None, "delivered": False,
              "runtimeProvenanceIdentical": None,
              "successorGrantIssued": False, "rootRelayRequired": True}
    helper, before, expected = None, None, None
    held = []

    def failure(message):
        report["errors"].append(message)
        if report["firstError"] is None:
            report["firstError"] = message

    def persist():
        try:
            write_json(report_path, report)
            return True
        except BaseException as exc:
            failure(f"Report persistence: {type(exc).__name__}: {exc}")
            return False

    write_json(report_path, report)
    try:
        if os.name != "nt":
            raise RuntimeError("This supervisor is Windows-only")
        helper = load_helper()
        report["runtimeProvenanceBefore"] = runtime_provenance()
        node = report["runtimeProvenanceBefore"]["node"]["path"]
        before = snapshot()
        write_json(directory / "source-before.json", before)
        hashes = {item["path"]: item["sha256"] for item in before}
        catalog = json.loads((ROOT / "assets/content/examples.json").read_text(encoding="utf-8-sig"))
        ids = [item["id"] for item in catalog["entries"]]
        if len(ids) != 481 or len(set(ids)) != 481 or not CONTROL_IDS <= set(ids):
            raise ValueError("Expected exact unique481 catalog including both lifecycle controls")
        expected = {"ids": set(ids), "examplesSha256": hashes["assets/content/examples.json"],
                    "tutorialsSha256": hashes["assets/content/tutorials.json"]}
        report["catalogInputs"] = {key: value for key, value in expected.items() if key != "ids"}
        for phase in report["phases"]:
            full = phase["name"] == "full"
            remaining = started + WORK_SECONDS - time.monotonic()
            if full and remaining < 270:
                phase["reason"] = f"Full481 requires270s remaining; observed {remaining:.3f}s"
                failure(phase["reason"])
                break
            if not full and remaining < 30:
                phase["reason"] = "Less than30s remains for controls"
                failure(phase["reason"])
                break
            markdown = directory / f"{phase['name']}.md"
            command = [node, str(ROOT / "scripts/run_examples.mjs"), "--report", str(markdown),
                       "--viewport", f"{report['viewport']['width']}x{report['viewport']['height']}"]
            if not full:
                command += ["--filter", "^js-example-05[23]$"]
            deadline = started + WORK_SECONDS if full else min(started + 30, started + WORK_SECONDS)
            if not persist():
                raise OSError("Cannot persist phase checkpoint; no phase launched")
            passed = execute(helper, command, directory, phase["name"], deadline,
                             min(started + CLEANUP_SECONDS, deadline + 5), phase, held)
            try:
                phase["browserReport"] = validate_report(markdown.with_suffix(".json"), expected,
                                                         report["viewport"], full)
            except BaseException as exc:
                phase["errors"].append(f"Report: {type(exc).__name__}: {exc}")
                phase["status"] = "FAIL_OR_INCOMPLETE"
                passed = False
            if not passed:
                failure(f"{phase['name']} failed/incomplete: exit={phase['root'].get('exitCode')}; "
                        f"deadline={phase.get('deadlineReached')}; "
                        f"orphanCleanup={phase.get('orphanCleanup')}; {json.dumps(phase['errors'])}")
                if not full:
                    report["phases"][1]["reason"] = "Lifecycle controls failed/incomplete"
            if not persist():
                break
            if not passed:
                break
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
                    failure("Raw inputs changed during checks; no frozen-source pass")
            except BaseException as exc:
                failure(f"Final snapshot: {type(exc).__name__}: {exc}")
        if "runtimeProvenanceBefore" in report:
            try:
                report["runtimeProvenanceAfter"] = runtime_provenance()
                report["runtimeProvenanceIdentical"] = (
                    report["runtimeProvenanceBefore"] == report["runtimeProvenanceAfter"])
                if report["runtimeProvenanceIdentical"] is not True:
                    failure("Python/Node executable provenance changed during checks")
            except BaseException as exc:
                failure(f"Final executable provenance: {type(exc).__name__}: {exc}")
        report.update(validationTerminalConfirmed=not held,
                      status="RELEASE_PENDING_PUBLISHER" if not held else "HOLD/UNRELEASED",
                      elapsedSeconds=round(time.monotonic() - started, 3), finishedUtc=utc())
        persist()
        message = directory / "release.txt"
        publication = {"status": "UNRUN", "messageKind": report["status"]}
        report["publication"] = publication
        try:
            message.write_text(
                f"Web catalog {report['status']}; intended successor={args.next_owner}; "
                f"accepted grant={args.grant}. NO successor grant. "
                f"Viewport={args.viewport}; validation-terminal/empty Jobs={not held}; "
                f"phases={json.dumps(report['phases'])}; sourceStable={report['sourceSnapshotsIdentical']}; "
                f"errors={json.dumps(report['errors'])}; elapsed={report['elapsedSeconds']}s. "
                f"Root must verify final job.json/stdout RELEASE/delivered=true after publisher "
                f"terminal exit0/active0, then relay the actual named handoff. "
                f"Evidence {directory.relative_to(ROOT).as_posix()}. Host only; no core/native/HAP/device write.\n",
                encoding="utf-8")
            if helper is None:
                raise RuntimeError("Reviewed helper unavailable; explicit manual relay required")
            if time.monotonic() >= started + TOTAL_SECONDS - 2:
                raise TimeoutError("Publication budget exhausted; explicit manual relay required")
            command = helper.channel_command(message, args.next_owner)
            execute(helper, command, directory, "publisher",
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
        report["delivered"] = not held and publication.get("delivered") is True
        report["elapsedSeconds"] = round(time.monotonic() - started, 3)
        report["finishedUtc"] = utc()
        if held:
            report["status"] = "HOLD/UNRELEASED"
            failure("Unconfirmed cleanup: wrapper retains exact Job handles; no successor grant")
        elif report["delivered"]:
            report["status"] = "RELEASE"
        else:
            report["status"] = "WITHHELD"
        persist()
    try:
        print(json.dumps(report), flush=True)
    finally:
        if held:
            # Preserve exact ownership even when report persistence/stdout fails.
            while True:
                time.sleep(0.5)
    return 0 if (not report["errors"] and report["sourceSnapshotsIdentical"] is True
                 and report["runtimeProvenanceIdentical"] is True
                 and all(phase["status"] == "PASS" for phase in report["phases"])
                 and report["status"] == "RELEASE" and report["delivered"] is True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
