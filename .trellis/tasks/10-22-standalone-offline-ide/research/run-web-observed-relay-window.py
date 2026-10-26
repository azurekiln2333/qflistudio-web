"""Observe the frozen Web wrapper and publish its actual terminal result automatically.

SOURCE ONLY until C explicitly approves ``web-observed-relay/v1`` plus this
file's exact SHA256 in a NEW actual grant. That grant must also approve the
underlying ``web-relay-format-app/v1`` operation and its five formatter paths.
Default invocation is a read-only snapshot. There is no inferred authorization.

The parent creates a control-plane private Job AFTER validating the receipt,
but BEFORE the child wrapper atomically consumes it. This deliberate boundary
must be explicitly granted by this exact standalone raw grant line:
ACCEPT web-observed-relay/v1 sha256=<exact hash> boundary=control-job-before-marker/v1
The parent never consumes or delegates the marker.
Only the unchanged wrapper consumes before its SDK or publisher Jobs. A racing
second wrapper can therefore start control infrastructure but cannot run SDK.

A deadline or uncertain query never terminates the live validation custodian.
The parent keeps its exact Job/process handles until root-terminal AND Job0.
Only the final coordination publisher can be stopped at its own deadline.
After the validation root and all payload/pending publisher reports are proven
terminal, final RELEASE is sent without waiting for another model invocation.
The final sender's own terminal/Job0/result is written separately before exit.
Neither this live parent nor that sender claims its own process terminal state.

180 seconds includes parent preflight, validation, publication and final I/O.
Synchronous Win32/file calls have no hard timeout. HOLD/late history is sticky;
eventual cleanup never promotes the run to a passing bounded gate. Local timing
is provisional. C independently judges actual completion and grants successors.
The pinned helper does not check CloseHandle results: handlesClosed records a
returned close routine, not OS confirmation. No SDK is started after validation.
Neither validation nor final sender is admitted at/after the parent deadline. Late validation writes
local-release.json for an explicit coordinator relay after observing this parent
exit; local release never claims successful delivery or a successor grant.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time

RESEARCH = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
WRAPPER = RESEARCH / "run-web-relay-window.py"
WRAPPER_SHA256 = "401f61d44495dd0a8b681a25746263e589203a9555f30c49106eca791db0fdb3"
AUTHORIZATION = RESEARCH / "web_relay_authorization.py"
AUTHORIZATION_SHA256 = "84445442fed9b9382555e02b8812c6321cbd7c7ec5026ff13904c5f5897a1de4"
PROTOCOL = "web-observed-relay/v1"
CONTROL_BOUNDARY = "control-job-before-marker/v1"
TOTAL_SECONDS = 180
PUBLISH_SECONDS = 8
POLL_SECONDS = 0.05
OBSERVER_SUFFIX = "-observed"


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def record_error(phase, message):
    errors = phase.setdefault("errors", [])
    if message not in errors:
        errors.append(message)


def root_gone(root):
    return (isinstance(root, dict) and root.get("terminal") is True
            and type(root.get("jobActiveProcesses")) is int
            and root["jobActiveProcesses"] == 0)


def phase_gone(phase):
    root = phase.get("root") if isinstance(phase, dict) else None
    identity = (isinstance(root, dict) and type(root.get("pid")) is int
                and root["pid"] > 0
                and isinstance(root.get("creationFiletime100ns"), str)
                and root["creationFiletime100ns"].isascii()
                and root["creationFiletime100ns"].isdigit())
    return (identity and phase.get("terminalConfirmed") is True and root_gone(root))


def observe_owned(job, phase, held, deadline, *, publisher=False,
                  clock=time.monotonic, sleep=time.sleep, notify=lambda: None):
    """Pure-injectable custody loop; never stop a validation custodian.

    The caller registers ``job`` in held before calling start(). Unknown query,
    close failure or deadline retains the SAME object. A publisher alone may be
    stopped. No close call occurs before actual root-terminal plus Job0 proof.
    """
    phase.setdefault("errors", [])
    phase.setdefault("deadlineReached", False)
    phase.setdefault("holdSeen", False)
    phase.setdefault("forcedCleanup", False)
    phase["custodianPreserved"] = not publisher
    phase["handlesClosed"] = False
    phase["terminalConfirmed"] = False
    phase["jobHandle"] = str(job.job)
    phase["processHandle"] = str(job.process)
    stop_sent = False
    last_hold = None

    def checkpoint():
        try:
            notify()
        except BaseException as exc:
            phase["holdSeen"] = True
            record_error(phase, f"Evidence: {type(exc).__name__}: {exc}")

    while True:
        late = clock() >= deadline
        if late:
            phase["deadlineReached"] = True
            phase["holdSeen"] = True
        try:
            empty = job.empty()
            phase["root"] = dict(job.record)
            phase["processHandle"] = str(job.process)
            phase["queryConfirmed"] = True
        except BaseException as exc:
            empty = False
            phase["queryConfirmed"] = False
            phase["holdSeen"] = True
            record_error(phase, f"Query: {type(exc).__name__}: {exc}")
        # Do not trust a boolean that contradicts the actual recorded root.
        if empty is True and root_gone(phase.get("root")):
            phase["terminalConfirmed"] = True
            phase["terminalObservedUtc"] = utc()
            try:
                job.close()
            except BaseException as exc:
                phase["holdSeen"] = True
                record_error(phase, f"Close: {type(exc).__name__}: {exc}")
            else:
                phase["handlesClosed"] = True
                phase["handlesRetained"] = False
                held.remove(job)
                phase["status"] = ("TERMINAL_AFTER_HOLD" if phase["holdSeen"]
                                   else "TERMINAL")
                checkpoint()
                return
        if late and publisher and not stop_sent:
            try:
                job.stop()
            except BaseException as exc:
                phase["holdSeen"] = True
                record_error(phase, f"Publisher stop: {type(exc).__name__}: {exc}")
            else:
                stop_sent = True
                phase["forcedCleanup"] = True
        phase["status"] = "HOLD"
        phase["handlesRetained"] = True
        current_hold = (late, phase.get("queryConfirmed"), len(phase["errors"]),
                        phase.get("forcedCleanup"))
        if current_hold != last_hold:
            checkpoint()
            last_hold = current_hold
        try:
            sleep(POLL_SECONDS)
        except BaseException as exc:
            phase["holdSeen"] = True
            record_error(phase, f"Wait: {type(exc).__name__}: {exc}")
            checkpoint()


def observer_approval(receipt, *, own_sha, reviewed_sha):
    if re.fullmatch(r"[0-9a-f]{64}", reviewed_sha or "") is None:
        return "Independent reviewed observer SHA256 is required"
    if own_sha != reviewed_sha:
        return "Observer differs from the independently reviewed source"
    raw = receipt.get("rawEvent") if isinstance(receipt, dict) else None
    text = raw.get("text") if isinstance(raw, dict) else None
    acceptance = f"ACCEPT {PROTOCOL} sha256={own_sha} boundary={CONTROL_BOUNDARY}"
    if not isinstance(text, str) or acceptance not in text.splitlines():
        return "Fresh actual grant requires exact standalone observer ACCEPT/hash/boundary line"
    return None


def load_wrapper():
    if sha256(WRAPPER) != WRAPPER_SHA256:
        raise PermissionError("Frozen reviewed wrapper changed")
    if sha256(AUTHORIZATION) != AUTHORIZATION_SHA256:
        raise PermissionError("Frozen authorization module changed")
    spec = importlib.util.spec_from_file_location("web_observed_frozen_wrapper", WRAPPER)
    if spec is None or spec.loader is None:
        raise PermissionError("Cannot load frozen wrapper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # Guarded main; no Job is created on import.
    return module


def preflight(args):
    if not getattr(args, "execute_reviewed", False):
        raise PermissionError("--execute-reviewed is required")
    if not getattr(args, "reviewed_raw_sha256", None):
        raise PermissionError("Independent root-reviewed raw-event pin is required")
    own_sha = sha256(__file__)
    if own_sha != getattr(args, "reviewed_observer_sha256", None):
        raise PermissionError("Independent reviewed observer source pin is required")
    wrapper = load_wrapper()
    if wrapper.frozen_mismatches():
        raise PermissionError("Frozen app runner/worker/helper changed")
    problem = wrapper.validate_args(args.grant, args.run_name, args.next_owner)
    problem = problem or wrapper.path_refusal(args.run_name)
    target = RESEARCH / (args.run_name + OBSERVER_SUFFIX)
    if target.exists():
        problem = problem or "Observer evidence directory exists; no replay"
    if problem:
        raise PermissionError(problem)
    receipt, _, problem = wrapper.reviewed_authorization(args, consume=False)
    if problem:
        raise PermissionError(problem)
    problem = observer_approval(receipt, own_sha=own_sha,
                                reviewed_sha=args.reviewed_observer_sha256)
    if problem:
        raise PermissionError(problem)
    # Read-only replay precheck. The wrapper remains the only marker consumer;
    # its atomic create decides a race after control infrastructure starts.
    spec = importlib.util.spec_from_file_location("web_observed_marker_check", AUTHORIZATION)
    authorization = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(authorization)
    marker = authorization.marker_path(RESEARCH / ".web-relay-consumed",
                                        authorization.marker_id(receipt["coordinatorEvent"]))
    if marker.exists():
        raise PermissionError("Grant already consumed; no control Job replay")
    return wrapper, receipt, target


def inspect_reports(wrapper_report, child_report, validation_phase, *, grant,
                    run_name, raw_pin):
    """Independent ownership gate. A failed test gate may still release resources."""
    errors = []
    w, c = wrapper_report, child_report
    if not isinstance(w, dict) or not isinstance(c, dict):
        return {"releaseEligible": False, "gate": "INCOMPLETE",
                "errors": ["Both durable reports are required"]}
    if not phase_gone(validation_phase):
        errors.append("Actual validation root and containing Job are not terminal")
    actual = validation_phase.get("root") or {}
    identity = w.get("wrapper") or {}
    if (identity.get("pid") != actual.get("pid")
            or identity.get("creationFiletime100ns") != actual.get("creationFiletime100ns")):
        errors.append("Wrapper report does not identify the retained validation root")
    if w.get("grant") != grant or w.get("runName") != run_name or c.get("grant") != grant:
        errors.append("Reports do not match this exact grant/run")
    if "runName" in c and c["runName"] != run_name:
        errors.append("Child report runName does not match the expected run directory")
    if c.get("nextOwner") != w.get("nextOwner"):
        errors.append("Child and wrapper nextOwner differ")
    if (w.get("authorization") or {}).get("rawEventSha256") != raw_pin:
        errors.append("Wrapper receipt does not match the independently pinned event")
    if (w.get("resourcesReleased") is not True or w.get("cleanupConfirmed") is not True
            or w.get("handlesRetained") is not False):
        errors.append("Wrapper resources or cleanup remain unproven")
    for name in ("accept", "sourceFormat", "supervisor", "relay"):
        if not phase_gone(w.get(name)):
            errors.append(f"Wrapper {name} phase is not terminal+Job0")
    if c.get("allOwnedJobsEmpty") is not True or c.get("terminalConfirmed") is not True:
        errors.append("Child aggregate terminal+Job0 is unproven")
    phases = c.get("phases")
    if not isinstance(phases, list) or not phases:
        errors.append("Child phase records are missing")
    else:
        for phase in phases:
            if not phase_gone(phase):
                errors.append("A child payload phase is not terminal+Job0")
    if not phase_gone(c.get("publication")):
        errors.append("Child pending publisher is not terminal+Job0")
    gate = (w.get("assessment") or {}).get("gate", "INCOMPLETE")
    if gate not in ("PASS", "FAIL", "INCOMPLETE"):
        gate = "INCOMPLETE"
    return {"releaseEligible": not errors, "gate": gate, "errors": errors}


def publisher_deadline(parent_deadline, now):
    """Refuse late admission; a sender gets at most the remaining parent budget."""
    return None if now >= parent_deadline else min(parent_deadline, now + PUBLISH_SECONDS)


def run(args, *, started=None):
    if started is None:
        started = time.monotonic()
    deadline = started + TOTAL_SECONDS
    wrapper, receipt, directory = preflight(args)
    if os.name != "nt":
        raise PermissionError("Real execution is Windows only")
    # Loading imports does not instantiate a Job. The receipt was checked first.
    frozen_spec = importlib.util.spec_from_file_location("web_observed_frozen_app", wrapper.RUNNER)
    frozen = importlib.util.module_from_spec(frozen_spec)
    frozen_spec.loader.exec_module(frozen)
    helper = frozen.load_helper()
    directory.mkdir(exist_ok=False)
    report_path = directory / "observer.json"
    validation = {"name": "validation", "errors": []}
    publisher = {"name": "final-sender", "errors": []}
    report = {"schemaVersion": 1, "protocol": PROTOCOL, "grant": args.grant,
              "runName": args.run_name, "nextOwner": args.next_owner,
              "startedUtc": utc(), "windowSeconds": TOTAL_SECONDS,
              "observerAliveAtWrite": True, "selfTerminalClaim": False,
              "successorGrant": False, "controlPlaneOnly": True,
              "validation": validation, "finalSender": publisher,
              "evidenceErrors": [], "errors": [], "releasePublished": False,
              "atomicConsumptionOwner": "frozen wrapper, before SDK/publishers",
              "controlJobBeforeConsumptionExplicitlyGranted": True,
              "sourceSha256": sha256(__file__)}
    held = []

    def checkpoint():
        report["heldJobs"] = len(held)
        report["elapsedSeconds"] = round(time.monotonic() - started, 3)
        try:
            atomic_json(report_path, report)
        except BaseException as exc:
            message = f"{type(exc).__name__}: {exc}"
            if message not in report["evidenceErrors"]:
                report["evidenceErrors"].append(message)
            try:
                print(json.dumps({"ownership": "HOLD", "evidenceError": message,
                                  "heldJobs": len(held)}), flush=True)
            except BaseException:
                pass

    def owned_command(command, name, phase, *, is_publisher=False):
        phase.update(command=command)
        with (directory / (name + ".stdout.log")).open("xb", buffering=0) as out, \
             (directory / (name + ".stderr.log")).open("xb", buffering=0) as err:
            now = time.monotonic()
            admitted_deadline = (publisher_deadline(deadline, now) if is_publisher
                                 else (deadline if now < deadline else None))
            if admitted_deadline is None:
                phase.update(admitted=False, admission="DENIED_PARENT_DEADLINE",
                             processStarted=False)
                checkpoint()
                return False
            phase["observationDeadlineMonotonic"] = admitted_deadline
            job = helper.OwnedJob()
            held.append(job)  # Keep the original custodian even when start raises.
            try:
                # Check again after synchronous Job construction. No process is
                # launched if construction consumed the remaining allowance.
                if time.monotonic() >= admitted_deadline:
                    phase.update(admitted=False, admission="DENIED_PARENT_DEADLINE",
                                 processStarted=False)
                else:
                    phase.update(admitted=True, admission="ADMITTED", startedUtc=utc(),
                                 processStarted=True)
                    job.start(command, ROOT, os.environ.copy(), out, err)
            except BaseException as exc:
                record_error(phase, f"Start: {type(exc).__name__}: {exc}")
                phase["holdSeen"] = True
        phase["root"] = dict(job.record)
        checkpoint()
        observe_owned(job, phase, held, admitted_deadline,
                      publisher=is_publisher, notify=checkpoint)
        phase["finishedUtc"] = utc()
        checkpoint()
        return phase.get("admitted") is True

    checkpoint()
    command = [sys.executable, "-B", "-X", "utf8", str(WRAPPER),
               "--execute-reviewed", "--authorization", str(Path(args.authorization).resolve()),
               "--reviewed-raw-sha256", args.reviewed_raw_sha256,
               "--grant", args.grant, "--run-name", args.run_name,
               "--next-owner", args.next_owner]
    try:
        if not owned_command(command, "validation", validation):
            report["refusal"] = {
                "reason": "PARENT_DEADLINE_BEFORE_VALIDATION_START",
                "processStarted": False, "wrapperStarted": False,
                "grantConsumption": "NOT_ATTEMPTED_BY_THIS_INVOCATION",
                "coordinatorRelayRequired": True,
                "successorGrant": False}
            report["coordinatorRelayRequired"] = True
            checkpoint()
            raise PermissionError("Validation admission refused at parent deadline; no wrapper/report read")
        wrapper_path = RESEARCH / (args.run_name + "-relay") / "wrapper.json"
        child_path = RESEARCH / args.run_name / "job.json"
        wrapper_report = json.loads(wrapper_path.read_text(encoding="utf-8-sig"))
        child_report = json.loads(child_path.read_text(encoding="utf-8-sig"))
        assessment = inspect_reports(wrapper_report, child_report, validation,
                                     grant=args.grant, run_name=args.run_name,
                                     raw_pin=args.reviewed_raw_sha256)
        report["assessment"] = assessment
        report["wrapperAssessment"] = wrapper_report.get("assessment")
        report["validationExitCode"] = validation["root"].get("exitCode")
        if assessment["releaseEligible"]:
            local_release = {"validationRoot": validation["root"],
                "validationTerminalAndJob0": True, "assessment": assessment,
                "grant": args.grant, "runName": args.run_name,
                "nextOwner": args.next_owner, "recordedUtc": utc(),
                "delivered": False, "successorGrant": False,
                "handoff": "LOCAL_RELEASE_REQUIRES_COORDINATOR_RELAY",
                "requireParentActualExitBeforeRelay": True}
            atomic_json(directory / "local-release.json", local_release)
            report["localRelease"] = local_release
            text = (
                f"Web {args.grant} FINAL validation TERMINAL RELEASE to {args.next_owner}. "
                f"Exact retained validation root {json.dumps(validation['root'])}; "
                f"JobHandle={validation['jobHandle']} ProcessHandle={validation['processHandle']}. "
                f"All wrapper/payload/pending publishers terminal+Job0 independently checked. "
                f"gate={assessment['gate']} priorHold={validation['holdSeen']} "
                f"deadlineReached={validation['deadlineReached']}. "
                f"Core includes live WIP; no clean/tested-core-only claim. "
                f"Observer control-plane only, still alive, selfTerminalClaim=false. "
                f"This final sender remains pending while sending; C must read its separate "
                f"terminal/result before any next SDK. Evidence {directory.relative_to(ROOT)}/"
                f"final-sender.json and observer.json. No successor grant. "
                f"Grant consumed; no replay. Budget provisional; C judges actual total."
            )
            message = directory / "final-release.txt"
            message.write_text(text, encoding="utf-8")
            owned_command(helper.channel_command(message, args.next_owner),
                          "final-sender", publisher, is_publisher=True)
            report["releasePublished"] = (phase_gone(publisher)
                and publisher["root"].get("exitCode") == 0
                and not publisher.get("errors") and not publisher.get("forcedCleanup"))
            atomic_json(directory / "final-sender.json", {
                "phase": publisher, "delivered": report["releasePublished"],
                "controlPlaneOnly": True, "selfTerminalClaim": False,
                "coordinatorRelayRequired": not report["releasePublished"],
                "localReleasePath": str(directory / "local-release.json"),
                "finishedUtc": utc(), "heldJobs": len(held)})
        else:
            report["errors"].extend(assessment["errors"])
    except BaseException as exc:
        report["errors"].append(f"Observation/publication: {type(exc).__name__}: {exc}")
    finally:
        # Any unexpected exception must preserve ownership. Custodian Jobs are
        # never terminated here, even after the total deadline.
        for job in list(held):
            phase = validation if validation.get("handlesClosed") is not True else publisher
            observe_owned(job, phase, held, deadline,
                          publisher=phase is publisher, notify=checkpoint)
        report["resourcesReleased"] = not held
        report["holdSeen"] = bool(validation.get("holdSeen") or publisher.get("holdSeen"))
        report["budgetLate"] = (time.monotonic() >= deadline
                                or validation.get("deadlineReached") is True)
        report["localBudget"] = "PROVISIONAL_LATE" if report["budgetLate"] else "PROVISIONAL_WITHIN"
        report["budgetAuthority"] = "c-coordinator after actual final sender/result observation"
        report["finishedUtc"] = utc()
        checkpoint()
        # Sample after final write; still provisional because this next durable
        # write and process exit cannot be sampled from within this process.
        report["budgetLate"] = bool(report["budgetLate"] or time.monotonic() >= deadline)
        report["localBudget"] = "PROVISIONAL_LATE" if report["budgetLate"] else "PROVISIONAL_WITHIN"
        report["sampledAfterFinalIo"] = True
        checkpoint()
    success = (validation.get("root", {}).get("exitCode") == 0
               and report.get("assessment", {}).get("gate") == "PASS"
               and report.get("assessment", {}).get("releaseEligible") is True
               and report["releasePublished"] and not report["holdSeen"]
               and not report["budgetLate"] and not report["errors"]
               and not report["evidenceErrors"])
    print(json.dumps({"observerReport": str(report_path), "passed": success,
                      "resourcesReleased": report["resourcesReleased"],
                      "localBudget": report["localBudget"]}), flush=True)
    return 0 if success else 1


def main():
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-reviewed", action="store_true")
    parser.add_argument("--authorization")
    parser.add_argument("--reviewed-raw-sha256")
    parser.add_argument("--reviewed-observer-sha256")
    parser.add_argument("--grant")
    parser.add_argument("--run-name")
    parser.add_argument("--next-owner")
    args = parser.parse_args()
    if not any(vars(args).values()):
        print(json.dumps({"snapshotOnly": True, "execution": False,
            "processStarted": False, "protocol": PROTOCOL,
            "observerSha256": sha256(__file__), "wrapperSha256": WRAPPER_SHA256,
            "authorizationSha256": AUTHORIZATION_SHA256,
            "windowSeconds": TOTAL_SECONDS, "grantRequired": True,
            "controlInfrastructureBeforeWrapperConsumptionRequiresExplicitGrant": True,
            "requiredControlBoundary": CONTROL_BOUNDARY,
            "liveCustodianNeverKilled": True, "runtimeValidation": "UNRUN"}))
        return 0
    if not all((args.execute_reviewed, args.authorization, args.reviewed_raw_sha256,
                args.reviewed_observer_sha256, args.grant, args.run_name, args.next_owner)):
        parser.error("Explicit reviewed receipt, raw pin, observer pin, grant, run name and successor required")
    # Refusal is separated from actual run exceptions: never call a process that
    # already started a false no-process authorization refusal.
    try:
        preflight(args)
    except (PermissionError, OSError, ValueError) as exc:
        print(json.dumps({"refused": True, "execution": False, "processStarted": False,
                          "reason": f"{type(exc).__name__}: {exc}"}), flush=True)
        return 3
    return run(args, started=started)


if __name__ == "__main__":
    raise SystemExit(main())
