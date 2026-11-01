"""Own the frozen Web app supervisor and publish its exact root relay in one command.

Default (no arguments) prints a snapshot and executes nothing. A real run needs a
reviewed authorization record, a fresh run name and one explicit successor. Shape is
not authority: the record must match the command and must not be reused. The wrapper
reuses the frozen supervisor module's verified Job manager, publishes the ACCEPT, owns
the frozen supervisor, proves its real terminal state, then publishes the root relay.
The wrapper is still live while it publishes, so it never claims outer terminal.
"""
from __future__ import annotations

import argparse
import ctypes as C
from ctypes import wintypes as W
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time

RESEARCH = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
RUNNER = RESEARCH / "run-web-app-window.py"
WORKER = RESEARCH / "run-web-app-worker.ps1"
HELPER = RESEARCH / "run-web-owned-window.py"

RUNNER_SHA256 = "d80c46e1b1cf2abe7e7a582e61016ac36266354242de198a5623628659922a19"
WORKER_SHA256 = "074ac02216bab95e8da23d87dca7d1567be5f2fcc4722d43e53d059227fb8b78"
HELPER_SHA256 = "9df7a94399aae38951337d61693d65de6e3cef438d02d4e51c787242dfda7fbe"

# One fixed window for this task. The frozen supervisor budgets 180 s from its own
# start, so the wrapper must stop it earlier to keep report and relay budget.
TOTAL_SECONDS = 180
MIN_RESERVE, POLL_SECONDS = 15, 0.05
FINAL_WRITE_MARGIN = 3.0  # Admission guard only. It proves nothing about completion.
WRAPPER_SUFFIX = "-relay"
RUN_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}")
NEXT_OWNER_RE = re.compile(r"[a-z][a-z0-9_-]+")
GRANT_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{2,63}")
PLACEHOLDER_TOKENS = ("NEG", "VALID", "TEST", "DUMMY", "EXAMPLE", "PLACEHOLDER",
                      "FAKE", "SAMPLE", "TODO", "FIXTURE")

# Real execution requires the explicit flag and a root-pinned, fresh receipt.
# A grant string, an environment variable or a directory name never authorizes it.
RUN_ENABLED = True
EXECUTION_STATE = "REVIEWED_GRANT_REQUIRED"
AUTHORIZATION_MODULE = RESEARCH / "web_relay_authorization.py"
FORMAT_FILES = (
    "lib/services/owned_preview_policy.dart",
    "lib/services/owned_preview_resource_broker.dart",
    "test/owned_preview_policy_test.dart",
    "test/owned_preview_resource_broker_test.dart",
    "test/web_offline_browser_test.dart",
)
AUTHORIZATION_SHA256 = "84445442fed9b9382555e02b8812c6321cbd7c7ec5026ff13904c5f5897a1de4"


def utc():
    return datetime.now(timezone.utc).isoformat()


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def relay_reserve(total=TOTAL_SECONDS):
    """Budget kept back for report read and relay publish."""
    return max(MIN_RESERVE, int(total * 0.1))


def supervisor_deadline_offset(total=TOTAL_SECONDS):
    """The frozen supervisor's own budget is 180 s; the wrapper stops it earlier."""
    return total - relay_reserve(total)


def clock_exhausted(now, deadline, minimum=2.0):
    """frozen.execute starts its Job before it looks at the deadline."""
    return now + minimum >= deadline


def active_count(value):
    """A missing or None count must fail closed. Never raise, never skip a report."""
    if isinstance(value, bool) or not isinstance(value, int):
        return -1
    return value


def placeholder_grant(grant):
    tokens = re.split(r"[._-]", str(grant).upper())
    return [token for token in tokens if token in PLACEHOLDER_TOKENS]


def paths_for(run_name):
    """Two distinct directories.

    The wrapper owns `<run-name>-relay`. The frozen supervisor creates
    `<run-name>` itself with mkdir(exist_ok=False), so the wrapper must never
    create that child path.
    """
    return RESEARCH / f"{run_name}{WRAPPER_SUFFIX}", RESEARCH / run_name


def refusal_for_dirs(wrapper_dir, child_dir):
    """Both directories are independent replay guards."""
    wrapper_dir, child_dir = Path(wrapper_dir), Path(child_dir)
    if wrapper_dir.exists():
        return f"Wrapper directory exists; no replay: {wrapper_dir.name}"
    if child_dir.exists():
        return f"Child evidence directory exists; no replay: {child_dir.name}"
    return None


def path_refusal(run_name):
    return refusal_for_dirs(*paths_for(run_name))


def validate_args(grant, run_name, next_owner):
    if not grant or not GRANT_RE.fullmatch(grant):
        return "An explicit grant is required; no default and no replay"
    if placeholder_grant(grant):
        return "Placeholder grants are not authorization"
    if not run_name or not RUN_NAME_RE.fullmatch(run_name):
        return "A fresh simple run name is required"
    if not next_owner or not NEXT_OWNER_RE.fullmatch(next_owner):
        return "Exactly one explicit successor is required"
    return None






def reviewed_authorization(args, *, consume=False):
    """Bind a real grant receipt; this function never starts a process."""
    if not getattr(args, "execute_reviewed", False):
        return None, None, "--execute-reviewed is required"
    raw_pin = getattr(args, "reviewed_raw_sha256", None)
    if not isinstance(raw_pin, str) or re.fullmatch(r"[0-9a-f]{64}", raw_pin) is None:
        return None, None, "The root-reviewed raw event SHA256 is required"
    if file_hash(AUTHORIZATION_MODULE) != AUTHORIZATION_SHA256:
        return None, None, "Reviewed authorization module changed"
    spec = importlib.util.spec_from_file_location("web_relay_receipt", AUTHORIZATION_MODULE)
    if spec is None or spec.loader is None:
        return None, None, "Cannot load the reviewed receipt validator"
    authorization = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(authorization)
    try:
        receipt = json.loads(Path(args.authorization).read_text(encoding="utf-8-sig"))
    except (OSError, TypeError, ValueError) as exc:
        return None, None, f"Receipt unreadable: {type(exc).__name__}"
    if not isinstance(receipt, dict):
        return None, None, "Receipt must be an object"
    event = receipt.get("coordinatorEvent")
    command = {"grant": args.grant, "successor": args.next_owner,
               "windowSeconds": TOTAL_SECONDS}
    hashes = {"wrapper": file_hash(Path(__file__)),
              "frozen": {"runner": file_hash(RUNNER),
                         "worker": file_hash(WORKER), "helper": file_hash(HELPER)}}
    problems = authorization.validate_receipt(
        receipt, command=command, event=event, hashes=hashes,
        reviewed_raw_sha256=raw_pin)
    if problems:
        return None, None, problems[0]
    if consume:
        decision = authorization.decide_execution(
            flags=(authorization.EXECUTE_FLAG,), receipt=receipt,
            command=command, event=event, hashes=hashes,
            marker_dir=RESEARCH / ".web-relay-consumed",
            reviewed_raw_sha256=raw_pin)
        if not decision["execute"]:
            return None, None, decision.get("reason", "Receipt refused")
    return receipt, authorization.receipt_id(receipt), None


def frozen_mismatches():
    expected = {RUNNER: RUNNER_SHA256, WORKER: WORKER_SHA256, HELPER: HELPER_SHA256}
    return [{"path": str(path.relative_to(ROOT)), "expected": digest,
             "actual": file_hash(path) if path.is_file() else None}
            for path, digest in expected.items()
            if not path.is_file() or file_hash(path) != digest]


def load_frozen():
    """Import the frozen supervisor. Its main is guarded, so no Job starts here."""
    mismatches = frozen_mismatches()
    if mismatches:
        raise RuntimeError(f"Frozen source changed: {json.dumps(mismatches)}")
    specification = importlib.util.spec_from_file_location("frozen_app_supervisor", RUNNER)
    if specification is None or specification.loader is None:
        raise RuntimeError("Cannot load the frozen app supervisor")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def process_identity():
    """Own PID and creation time, so C can observe this exact process later."""
    kernel = C.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = W.HANDLE
    kernel.GetCurrentProcess.argtypes = []
    kernel.GetProcessId.argtypes = [W.HANDLE]
    kernel.GetProcessId.restype = W.DWORD
    kernel.GetProcessTimes.argtypes = [W.HANDLE] + [C.POINTER(W.FILETIME)] * 4
    kernel.GetProcessTimes.restype = W.BOOL
    handle = kernel.GetCurrentProcess()
    stamps = [W.FILETIME() for _ in range(4)]
    if not kernel.GetProcessTimes(handle, *(C.byref(stamp) for stamp in stamps)):
        raise C.WinError(C.get_last_error())
    created = (stamps[0].dwHighDateTime << 32) | stamps[0].dwLowDateTime
    return {"pid": int(kernel.GetProcessId(handle)),
            "creationFiletime100ns": str(created)}


def gate_pass(report):
    phases = report.get("phases") or []
    return (report.get("status") == "RELEASE"
            and report.get("sourceSnapshotsIdentical") is True
            and not report.get("errors")
            and bool(phases)
            and all(phase.get("status") == "PASS" for phase in phases))


def publisher_confirmed(report):
    """The runner's own publisher needs its own terminal record, not a summary."""
    publication = report.get("publication") or {}
    root = publication.get("root") or {}
    return (report.get("allOwnedJobsEmpty") is True
            and report.get("terminalConfirmed") is True
            and publication.get("terminalConfirmed") is True
            and root.get("terminal") is True
            and root.get("jobActiveProcesses") == 0)


def phase_root_terminated(phase):
    """Read the Job record the frozen execute() already wrote, not a summary."""
    root = phase.get("root") or {}
    return (phase.get("terminalConfirmed") is True
            and root.get("terminal") is True
            and root.get("jobActiveProcesses") == 0)


def phase_forced(phase):
    return bool(phase.get("forcedCleanup") or phase.get("deadlineReached"))


def deadline_block(accept_phase, supervisor_phase, relay_phase, source_format_phase=None):
    """Name every deadline, and state that the frozen execute has no hard timeout."""
    source_format_phase = source_format_phase or {}
    return {
        "totalSeconds": TOTAL_SECONDS,
        "supervisorSeconds": supervisor_deadline_offset(),
        "relayReserveSeconds": relay_reserve(),
        "finalWriteMarginSeconds": FINAL_WRITE_MARGIN,
        "synchronousExecute": True,
        "hardTimeout": False,
        "completionPromise": "none",
        "localBudgetProvisional": True,
        "budgetObserverAuthority": "c-coordinator",
        "marginProvesCompletion": False,
        "acceptDeadlineReached": bool(accept_phase.get("deadlineReached")),
        "sourceFormatDeadlineReached": bool(source_format_phase.get("deadlineReached")),
        "supervisorDeadlineReached": bool(supervisor_phase.get("deadlineReached")),
        "relayDeadlineReached": bool(relay_phase.get("deadlineReached")),
        "anyPhaseDeadlineReached": bool(
            source_format_phase.get("deadlineReached")
            or accept_phase.get("deadlineReached")
            or supervisor_phase.get("deadlineReached")
            or relay_phase.get("deadlineReached")),
        "totalDeadlineReached": False,
        "judgedAfterFinalIo": False,
    }


def wrapper_claim(ownership):
    """The wrapper publishes a readiness claim. It never claims a formal release."""
    return {"ownership": ownership,
            "releaseReady": ownership == "RELEASE_READY",
            "formalReleaseClaimed": False,
            "wrapperAlive": True,
            "releaseAuthority": "C, after observing this pid and creation time stop"}


def created_job_gone(phase):
    """A phase contributes a Job only once it has a pid. No pid means no Job.

    Not-created is not live. An empty phase record, or one without a pid, means the
    frozen execute() never created a Job there, so it holds no resource.
    """
    root = phase.get("root")
    if not isinstance(root, dict) or root.get("pid") is None:
        return True
    return (root.get("terminal") is True
            and active_count(root.get("jobActiveProcesses")) == 0)


def released_resources(*, cleanup_confirmed, held, phases):
    """Judge resources from real Jobs, never from a missing supervisor record.

    The frozen execute() drops a handle from `held` only after it confirms empty(),
    so an empty `held` with confirmed cleanup means every created Job is terminal
    and nothing is live. A phase that never created a Job is not live either, which
    is why a failed ACCEPT does not force HOLD.
    """
    return (cleanup_confirmed is True
            and not held
            and all(created_job_gone(phase) for phase in phases))


def ownership_state(*, resources_released):
    """Read the real Job state. A missing job.json never means resources are live."""
    return "RELEASE_READY" if resources_released is True else "HOLD"


def gate_state(supervisor_report, accept_delivered):
    """PASS, FAIL or INCOMPLETE. INCOMPLETE means no record exists to judge."""
    if not accept_delivered or not supervisor_report:
        return "INCOMPLETE"
    return "PASS" if gate_pass(supervisor_report) else "FAIL"


def publication_state(*, relay_delivered):
    return "DELIVERED" if relay_delivered is True else "FAILED"


def budget_state(*, late):
    """Provisional only. C judges WITHIN/LATE from the real wrapper stop time.

    The local read happens before the final write and before process exit, so it
    cannot settle the budget. FINAL_WRITE_MARGIN is an admission guard, not proof.
    """
    return "PROVISIONAL_LATE" if late else "PROVISIONAL_WITHIN"


def assess(*, gate, ownership, publication, budget):
    """Four independent axes. A failed gate does not block a ready release."""
    return {"gate": gate, "ownership": ownership,
            "publication": publication, "budget": budget}


def failure_labels(*, gate, ownership, publication, budget):
    """Label each axis that is not clean. Gate and resources stay separate."""
    labels = []
    if gate == "FAIL":
        labels.append("gate")
    elif gate == "INCOMPLETE":
        labels.append("gate_incomplete")
    if ownership == "HOLD":
        labels.append("ownership_hold")
    if publication == "FAILED":
        labels.append("publication_failed")
    if budget == "PROVISIONAL_LATE":
        labels.append("budget_late_provisional")
    return labels


def persist(report_path, report):
    """Set the persisted flag immediately before the write.

    write_json renames the temporary file into place as its last step, so a raised
    write leaves the previous file untouched. The flag therefore never contradicts
    the bytes on disk. Returns the exception, or None on success.
    """
    report["reportPersisted"] = True
    try:
        write_json(report_path, report)
        return None
    except BaseException as exc:
        report["reportPersisted"] = False
        return exc


def wrapper_cleanup(held, deadline, failure, state, phases=()):
    """Preserve exact final identities and keep unconfirmed Job handles alive."""
    confirmed = True
    records = state.setdefault("jobs", [])
    for job in list(held):
        item = {"jobHandle": str(job.job), "processHandle": str(job.process),
                "phase": "unassigned-before-root", "handlesClosed": False}
        try:
            if not job.empty():
                state["stopped"] = True
                job.stop()
                while time.monotonic() < deadline and not job.empty():
                    time.sleep(POLL_SECONDS)
            empty = job.empty()
            item.update(root=dict(job.record), terminalAndEmpty=empty)
            pid = job.record.get("pid")
            for phase in phases:
                if pid is not None and (phase.get("root") or {}).get("pid") == pid:
                    phase["root"] = dict(job.record)
                    phase["terminalConfirmed"] = empty
                    item["phase"] = phase.get("name")
            if empty:
                job.close()
                item["handlesClosed"] = True
                held.remove(job)
            else:
                confirmed = False
                failure(f"{item['phase']}: Job still active; handles retained")
        except BaseException as exc:
            confirmed = False
            item.update(root=dict(job.record), error=f"{type(exc).__name__}: {exc}")
            failure(f"{item['phase']} cleanup: {type(exc).__name__}: {exc}")
        records.append(item)
    return confirmed


def compose_accept(*, run_name, grant, next_owner, wrapper):
    return (
        f"Web {run_name} ACCEPT {grant} to {next_owner}. Window {TOTAL_SECONDS}s, "
        f"one wrapper command, including the five granted formatter paths.\n"
        f"Wrapper pid={wrapper['pid']} created={wrapper['creationFiletime100ns']} "
        f"wrapperAlive=true outerTerminalClaimed=false.\n"
        f"The budget clock started at wrapper entry, before this ACCEPT was "
        f"written. The window covers ACCEPT through relay publish. The wrapper "
        f"formats only the five granted paths, then launches the frozen supervisor.\n"
        f"No SDK/browser/native/device run beyond this window. No successor grant.\n")


def compose_relay(*, run_name, grant, next_owner, report, wrapper, outer_active,
                  forced_cleanup, supervisor_terminal):
    """No self-referential delivery field: this text is written before it is sent.

    The gate verdict and the resource-release state sit on separate labelled lines,
    so a gate failure is never read as a resource leak, and a forced release is
    never read as a gate failure.
    """
    passed = gate_pass(report)
    phases = ",".join(f"{phase.get('name')}={phase.get('status')}"
                      for phase in report.get("phases") or [])
    roots = ",".join(
        f"{phase.get('name')}:{(phase.get('root') or {}).get('pid')}/"
        f"{(phase.get('root') or {}).get('exitCode')}"
        for phase in report.get("phases") or [])
    publication = report.get("publication") or {}
    published_root = publication.get("root") or {}
    errors = len(report.get("errors") or [])
    released = (report.get("allOwnedJobsEmpty") is True
                and active_count(published_root.get("jobActiveProcesses")) == 0)
    return (
        f"Web {run_name} -> {next_owner}. Grant {grant}. "
        f"GRANT CONSUMED; NO SUCCESSOR GRANT.\n"
        f"gate={'PASS' if passed else 'FAIL'} gateErrors={errors} "
        f"gateSource=runner.\n"
        f"resources resourcesReleasedAtRelay={str(released).lower()} "
        f"wrapperCleanupPending=true forcedRelease={str(bool(forced_cleanup)).lower()}.\n"
        f"ownership=pre_cleanup releaseReadyPending=true formalReleaseClaimed=false "
        f"releaseAuthority=C-after-observation wrapperAlive=true.\n"
        f"supervisorTerminal={supervisor_terminal} outerActive={outer_active}.\n"
        f"Runner elapsed={report.get('elapsedSeconds')}s phases {phases}.\n"
        f"Roots {roots} publisher {published_root.get('pid')}/"
        f"{published_root.get('exitCode')} delivered={publication.get('delivered')}.\n"
        f"allOwnedJobsEmpty={report.get('allOwnedJobsEmpty')} "
        f"terminalConfirmed={report.get('terminalConfirmed')} "
        f"sourceStable={report.get('sourceSnapshotsIdentical')} "
        f"coreHead={report.get('coreHead')} plus live WIP, not clean-core-only evidence.\n"
        f"Wrapper pid={wrapper['pid']} created={wrapper['creationFiletime100ns']} "
        f"wrapperAliveAtRelay=true outerTerminalClaimed=false wrapperExitPending=true.\n"
        f"Evidence research/{run_name}/job.json. No catalog/native/WSL/HAP/device extra. "
        f"No SDK/browser run until a NEW explicit grant.\n")


def snapshot():
    mismatches = frozen_mismatches()
    return {
        "snapshotOnly": True,
        "execution": False,
        "processStarted": False,
        "executionState": EXECUTION_STATE,
        "runReachableWithReviewedAuthorization": RUN_ENABLED,
        "reviewedExecutionAvailable": RUN_ENABLED,
        "authorizationModuleSha256": AUTHORIZATION_SHA256,
        "explicitExecuteFlagRequired": True,
        "rootReviewedRawPinRequired": True,
        "protocol": "web-relay-format-app/v1",
        "sourceFormattingRequiresExplicitGrant": list(FORMAT_FILES),
        "wrapper": {"path": str(Path(__file__).resolve().relative_to(ROOT)),
                    "sha256": file_hash(Path(__file__).resolve())},
        "frozen": {"runner": RUNNER_SHA256, "worker": WORKER_SHA256,
                   "helper": HELPER_SHA256},
        "frozenMatch": not mismatches,
        "mismatches": mismatches,
        "windowSeconds": TOTAL_SECONDS,
        "relayReserveSeconds": relay_reserve(),
        "supervisorDeadlineSeconds": supervisor_deadline_offset(),
        "directories": {"wrapper": f"<FRESH_NAME>{WRAPPER_SUFFIX}",
                        "childEvidence": "<FRESH_NAME>"},
        "reuses": "frozen run-web-app-window.py execute() and load_helper()",
        "authorizationRequired": True,
        "placeholderGrantsRefused": list(PLACEHOLDER_TOKENS),
        "plannedCommand": [
            "python", "-B", "-X", "utf8",
            str(Path(__file__).resolve().relative_to(ROOT)),
            "--authorization", "<REVIEWED_RECORD.json>",
            "--execute-reviewed", "--reviewed-raw-sha256", "<ROOT_REVIEWED_RAW_SHA256>",
            "--grant", "<EXPLICIT_NEW_GRANT>", "--run-name", "<FRESH_NAME>",
            "--next-owner", "<NAMED_SUCCESSOR>"],
        "requires": "C must accept this protocol in a NEW explicit grant before any run",
    }


def run(args):
    if not getattr(args, "execute_reviewed", False):
        raise PermissionError("--execute-reviewed and a fresh receipt are required")
    if not RUN_ENABLED:
        raise PermissionError(f"{EXECUTION_STATE}: the real run path is disabled")
    started = time.monotonic()                    # One clock, from before ACCEPT.
    total_deadline = started + TOTAL_SECONDS
    supervisor_deadline = started + supervisor_deadline_offset()
    refusal = path_refusal(args.run_name)
    if refusal:
        raise FileExistsError(refusal)
    problem = validate_args(args.grant, args.run_name, args.next_owner)
    if problem:
        raise PermissionError(problem)
    if frozen_mismatches():
        raise PermissionError("Reviewed frozen inputs changed")
    record, digest, problem = reviewed_authorization(args, consume=True)
    if problem:
        raise PermissionError(problem)
    wrapper_dir, child_dir = paths_for(args.run_name)
    frozen = load_frozen()
    helper = frozen.load_helper()
    wrapper = process_identity()
    wrapper_dir.mkdir(exist_ok=False)              # The child directory stays for the runner.
    report_path = wrapper_dir / "wrapper.json"
    report = {"schemaVersion": 1, "grant": args.grant, "nextOwner": args.next_owner,
              "runName": args.run_name, "windowSeconds": TOTAL_SECONDS,
              "relayReserveSeconds": relay_reserve(),
              "supervisorDeadlineSeconds": round(supervisor_deadline_offset(), 3),
              "wrapperDirectory": wrapper_dir.name,
              "childEvidenceDirectory": child_dir.name,
              "authorization": record, "authorizationSha256": digest,
              "frozen": {"runner": RUNNER_SHA256, "worker": WORKER_SHA256,
                         "helper": HELPER_SHA256},
              "wrapper": wrapper, "wrapperState": "STARTED",
              "wrapperAliveAtRelay": None, "outerTerminalClaimed": False,
              "startedUtc": utc(), "errors": [], "firstError": None,
              "reportPersisted": False, "finalized": False}
    persist(report_path, report)
    print(json.dumps({"wrapper": wrapper, "state": "STARTED",
                      "evidence": str(wrapper_dir.relative_to(ROOT))}), flush=True)

    def failure(message):
        report["errors"].append(message)
        if report["firstError"] is None:
            report["firstError"] = message

    held = []
    accept_phase = {"name": "accept"}
    source_format_phase = {"name": "source-format"}
    supervisor_phase = {"name": "supervisor"}
    relay_phase = {"name": "relay"}
    cleanup_state = {"stopped": False, "jobs": []}
    report.update(accept=accept_phase, sourceFormat=source_format_phase,
                  supervisor=supervisor_phase, relay=relay_phase)
    accept_delivered = False
    supervisor_terminal = False
    publisher_terminal = False
    relay_delivered = False
    supervisor_report = {}
    try:
        accept_path = wrapper_dir / "accept.txt"
        accept_path.write_text(compose_accept(run_name=args.run_name, grant=args.grant,
                                              next_owner=args.next_owner,
                                              wrapper=wrapper), encoding="utf-8")
        accept_deadline = min(started + relay_reserve() / 2, time.monotonic() + 8)
        if clock_exhausted(time.monotonic(), accept_deadline):
            failure("ACCEPT not started: clock exhausted before launch")
        else:
            accept_delivered = frozen.execute(
                helper, helper.channel_command(accept_path, args.next_owner),
                wrapper_dir, "accept", accept_deadline, total_deadline,
                accept_phase, held)
            report["accept"] = accept_phase
            if not accept_delivered:
                failure("ACCEPT publication failed; supervisor not launched")
            elif clock_exhausted(time.monotonic(), supervisor_deadline, 5.0):
                failure("Supervisor not started: clock exhausted before launch")
            else:
                # This phase must be explicitly included in the NEW grant.
                # Only the five named source files may be formatted.
                report["sourceFormatBefore"] = {
                    name: file_hash(ROOT / name) for name in FORMAT_FILES}
                dart = frozen.resolve_runtime_paths()["dart"]
                source_format_deadline = min(time.monotonic() + 15, supervisor_deadline - 5)
                format_ok = False
                if clock_exhausted(time.monotonic(), source_format_deadline):
                    failure("Source format not started: insufficient time")
                else:
                    format_ok = frozen.execute(
                        helper, [dart, "format", *FORMAT_FILES], wrapper_dir,
                        "source-format", source_format_deadline,
                        min(source_format_deadline + 5, total_deadline), source_format_phase, held)
                report["sourceFormat"] = source_format_phase
                report["sourceFormatAfter"] = {
                    name: file_hash(ROOT / name) for name in FORMAT_FILES}
                report["sourceFormatChanged"] = [
                    name for name in FORMAT_FILES
                    if report["sourceFormatBefore"][name] != report["sourceFormatAfter"][name]]
                if not format_ok:
                    failure("Owned source format failed; application not launched")
                elif clock_exhausted(time.monotonic(), supervisor_deadline, 5.0):
                    failure("Application not started: insufficient time after source format")
                else:
                    command = [str(Path(args.python_executable)), "-B", "-X", "utf8",
                               str(RUNNER), "--grant", args.grant,
                               "--run-name", args.run_name, "--next-owner", args.next_owner]
                    frozen.execute(helper, command, wrapper_dir, "supervisor",
                                   supervisor_deadline, total_deadline,
                                   supervisor_phase, held)
                    report["supervisor"] = supervisor_phase
                    supervisor_terminal = phase_root_terminated(supervisor_phase)
    except BaseException as exc:
        failure(f"Launch: {type(exc).__name__}: {exc}")
    finally:
        try:
            job_path = child_dir / "job.json"
            if job_path.is_file():
                supervisor_report = json.loads(job_path.read_text(encoding="utf-8-sig"))
            else:
                failure("Supervisor report missing; relay refused")
            publisher_terminal = publisher_confirmed(supervisor_report)
            outer_active = active_count(
                (supervisor_phase.get("root") or {}).get("jobActiveProcesses"))
            forced_now = (phase_forced(supervisor_phase) or phase_forced(accept_phase)
                          or phase_forced(source_format_phase)
                          or cleanup_state["stopped"])
            if (accept_delivered and not forced_now and supervisor_terminal
                    and publisher_terminal and outer_active == 0 and supervisor_report):
                if clock_exhausted(time.monotonic(), total_deadline):
                    failure("Relay not started: total clock exhausted")
                else:
                    try:
                        message_path = wrapper_dir / "relay.txt"
                        message_path.write_text(compose_relay(
                            run_name=args.run_name, grant=args.grant,
                            next_owner=args.next_owner, report=supervisor_report,
                            wrapper=wrapper, outer_active=outer_active,
                            forced_cleanup=forced_now,
                            supervisor_terminal=supervisor_terminal), encoding="utf-8")
                        report["wrapperAliveAtRelay"] = True
                        relay_deadline = min(total_deadline,
                                             time.monotonic() + relay_reserve())
                        relay_delivered = frozen.execute(
                            helper, helper.channel_command(message_path, args.next_owner),
                            wrapper_dir, "relay", relay_deadline, total_deadline,
                            relay_phase, held)
                        report["relay"] = relay_phase
                        if not relay_delivered:
                            failure("Relay publication failed; explicit manual relay required")
                    except BaseException as exc:
                        failure(f"Relay: {type(exc).__name__}: {exc}")
            else:
                failure("Relay skipped: ACCEPT, supervisor terminal or cleanup is unproven")
        except BaseException as exc:
            failure(f"Supervisor report: {type(exc).__name__}: {exc}")
        finally:
            cleanup_confirmed = wrapper_cleanup(
                held, total_deadline, failure, cleanup_state,
                (accept_phase, source_format_phase, supervisor_phase, relay_phase))

    forced_cleanup = (phase_forced(supervisor_phase) or phase_forced(accept_phase)
                          or phase_forced(source_format_phase)
                      or phase_forced(relay_phase) or cleanup_state["stopped"])
    any_deadline = bool(source_format_phase.get("deadlineReached")
                        or accept_phase.get("deadlineReached")
                        or supervisor_phase.get("deadlineReached")
                        or relay_phase.get("deadlineReached"))
    outer_active = active_count(
        (supervisor_phase.get("root") or {}).get("jobActiveProcesses"))
    # Ownership reads the real Job state. Not-created is not live: a phase with no
    # pid contributes no Job, so a failed ACCEPT or a supervisor that never launched
    # must not read as a live resource. A missing job.json is never read as
    # "resources still live" either. `outer_active` stays recorded as a fact, but it
    # is -1 when nothing was created, so it must not decide ownership.
    resources_released = released_resources(cleanup_confirmed=cleanup_confirmed,
                                            held=held,
                                            phases=(accept_phase, source_format_phase,
                                                    supervisor_phase, relay_phase))
    report.update(
        assessmentPending=True, assessment=None,
        acceptDelivered=accept_delivered,
        supervisorTerminal=supervisor_terminal,
        publisherTerminal=publisher_terminal,
        outerActiveProcesses=outer_active,
        forcedCleanup=forced_cleanup,
        phaseDeadlineReached=any_deadline,
        relayDelivered=relay_delivered,
        successorGrant=False,
        cleanupConfirmed=cleanup_confirmed,
        cleanupJobs=cleanup_state["jobs"],
        resourcesReleased=resources_released,
        handlesRetained=not cleanup_confirmed,
        processExitIsNotCleanupProof=True,
        clockStartedUtc=report.get("startedUtc"),
        deadline=deadline_block(accept_phase, supervisor_phase, relay_phase,
                                source_format_phase))
    if not cleanup_confirmed:
        report["holdReason"] = ("Retained Job handles; this process stays alive so "
                               "ownership is not dropped")

    # Write 1: evidence exists even if this process dies here. The persisted flag is
    # set immediately before this write, so the bytes on disk never contradict it.
    problem = persist(report_path, report)
    if problem is not None:
        failure(f"Report persistence 1: {type(problem).__name__}: {problem}")
    try:
        print(json.dumps(report), flush=True)
    except BaseException as exc:
        failure(f"Stdout 1: {type(exc).__name__}: {exc}")

    # Read the clock after the write and after the print, never before them. The
    # frozen execute() is synchronous and has no hard timeout. What follows is a
    # PROVISIONAL local budget only: the final write and the process exit still sit
    # outside it, so this code cannot prove completion inside 180 s.
    # FINAL_WRITE_MARGIN is an admission guard, never completion proof.
    # observerAuthority=c-coordinator judges WITHIN/LATE from the exact stop time.
    late = clock_exhausted(time.monotonic(), total_deadline, FINAL_WRITE_MARGIN)
    report["deadline"]["totalDeadlineReached"] = late
    report["deadline"]["judgedAfterFinalIo"] = True
    assessment = assess(gate=gate_state(supervisor_report, accept_delivered),
                        ownership=ownership_state(
                            resources_released=resources_released),
                        publication=publication_state(
                            relay_delivered=relay_delivered),
                        budget=budget_state(late=late))
    report.update(assessment=assessment, assessmentPending=False,
                  labels=failure_labels(**assessment),
                  wrapperClaim=wrapper_claim(assessment["ownership"]),
                  budgetSeconds=TOTAL_SECONDS, budgetLate=late,
                  budgetAuthority="provisional",
                  budgetObserverAuthority="c-coordinator",
                  clockJudgedAfterFinalIo=True,
                  finalWriteMarginSeconds=FINAL_WRITE_MARGIN,
                  elapsedSeconds=round(time.monotonic() - started, 3),
                  finishedUtc=utc())

    # Write 2: the authoritative receipt. Nothing is reported after this write, so
    # the file and the exit code cannot disagree.
    problem = persist(report_path, report)
    if problem is not None:
        failure(f"Report persistence 2: {type(problem).__name__}: {problem}")
        report["reportPersisted"] = False
    final_ok = (assessment["gate"] == "PASS"
                and assessment["publication"] == "DELIVERED"
                and assessment["ownership"] == "RELEASE_READY"
                and assessment["budget"] == "PROVISIONAL_WITHIN"
                and report["reportPersisted"] is True
                and not report["errors"])
    if not cleanup_confirmed:
        while True:  # Frozen ownership rule: never exit while holding a Job.
            time.sleep(0.5)
    return 0 if final_ok else 1


def self_test():
    """Pure negative controls. No subprocess, no Job, no real entry point."""
    cases = []

    def case(name, actual, expected):
        cases.append((name, actual == expected, actual, expected))

    granted = "C608-WEB180"
    case("reject empty grant", validate_args("", "r1", "owner") is not None, True)
    case("reject grant with space",
         validate_args("C608 WEB180", "r1", "owner") is not None, True)
    case("reject short grant", validate_args("ab", "r1", "owner") is not None, True)
    case("reject placeholder NEG",
         validate_args("C607-NEG", "r1", "owner") is not None, True)
    case("reject placeholder VALID",
         validate_args("C607-VALID", "r1", "owner") is not None, True)
    case("reject placeholder TEST",
         validate_args("C608-TEST", "r1", "owner") is not None, True)
    case("placeholder tokens detected", placeholder_grant("C607-NEG"), ["NEG"])
    case("real grant has no placeholder", placeholder_grant(granted), [])
    case("real grant alone accepts", validate_args(granted, "r1", "owner"), None)
    case("reject bad run name with real grant",
         validate_args(granted, "a/b", "owner") is not None, True)
    case("bad run name is the only fault", validate_args(granted, "r1", "owner"), None)
    case("reject missing owner with real grant",
         validate_args(granted, "r1", "") is not None, True)
    case("reject upper owner with real grant",
         validate_args(granted, "r1", "Owner") is not None, True)
    case("accept valid trio", validate_args(granted, "fresh-1", "c-coordinator"), None)

    case("window is exactly 180", TOTAL_SECONDS, 180)
    case("reserve 180", relay_reserve(), 18)
    case("supervisor deadline 162", supervisor_deadline_offset(), 162)
    case("deadline is earlier than runner budget",
         supervisor_deadline_offset() < TOTAL_SECONDS, True)
    case("deadline leaves relay budget",
         TOTAL_SECONDS - supervisor_deadline_offset() >= MIN_RESERVE, True)
    case("clock exhausted before launch", clock_exhausted(100.0, 101.0, 5.0), True)
    case("clock available", clock_exhausted(100.0, 200.0, 5.0), False)
    case("clock blocks a late start", clock_exhausted(178.0, 180.0, 2.0), True)

    case("None count fails closed", active_count(None), -1)
    case("missing count fails closed", active_count(-1), -1)
    case("bool is not a count", active_count(True), -1)
    case("string is not a count", active_count("0"), -1)
    case("zero count is zero", active_count(0), 0)
    case("two active is two", active_count(2), 2)

    wrapper_dir, child_dir = paths_for("fresh-1")
    case("wrapper dir has suffix", wrapper_dir.name, "fresh-1-relay")
    case("child dir has no suffix", child_dir.name, "fresh-1")
    case("wrapper and child differ", wrapper_dir != child_dir, True)

    fake = {"pid": 4242, "creationFiletime100ns": "134000000000000000"}
    good = {"status": "RELEASE", "sourceSnapshotsIdentical": True, "errors": [],
            "elapsedSeconds": 113.072, "allOwnedJobsEmpty": True,
            "terminalConfirmed": True, "coreHead": "2f9039a3",
            "phases": [{"name": "format", "status": "PASS",
                        "root": {"pid": 1, "exitCode": 0}}],
            "publication": {"terminalConfirmed": True, "delivered": True,
                            "root": {"pid": 2, "exitCode": 0, "terminal": True,
                                     "jobActiveProcesses": 0}}}
    text = compose_relay(run_name="fresh-1", grant="C608-WEB180",
                         next_owner="c-coordinator", report=good, wrapper=fake,
                         outer_active=0, forced_cleanup=False,
                         supervisor_terminal=True)
    case("relay says no successor", "NO SUCCESSOR GRANT" in text, True)
    case("relay says grant consumed", "GRANT CONSUMED" in text, True)
    case("relay carries wrapper pid", "pid=4242" in text, True)
    case("relay carries creation time", "134000000000000000" in text, True)
    case("relay admits wrapper live", "wrapperAliveAtRelay=true" in text, True)
    case("relay denies outer terminal", "outerTerminalClaimed=false" in text, True)
    case("relay never claims outer terminal", "outer terminal" not in text, True)
    case("relay marks live WIP", "not clean-core-only evidence" in text, True)
    case("relay records publisher root", "publisher 2/0" in text, True)
    case("relay has no self delivery claim", "relayDelivered" not in text, True)

    accept = compose_accept(run_name="fresh-1", grant="C608-WEB180",
                            next_owner="c-coordinator", wrapper=fake)
    case("accept names the grant", "ACCEPT C608-WEB180" in accept, True)
    case("accept says the clock predates it",
         "clock started at wrapper entry" in accept, True)
    case("accept no longer claims to start the clock",
         "ACCEPT starts the budget clock" not in accept, True)
    case("accept carries wrapper pid", "pid=4242" in accept, True)
    case("accept denies outer terminal", "outerTerminalClaimed=false" in accept, True)
    case("accept grants nothing", "No successor grant" in accept, True)

    case("publisher confirmed needs root terminal", publisher_confirmed(good), True)
    case("publisher rejects summary-only",
         publisher_confirmed({**good,
                              "publication": {"terminalConfirmed": True,
                                              "delivered": True,
                                              "root": {"pid": 2, "exitCode": 0}}}),
         False)
    case("publisher rejects active root",
         publisher_confirmed({**good,
                              "publication": {"terminalConfirmed": True,
                                              "root": {"pid": 2, "exitCode": 0,
                                                       "terminal": True,
                                                       "jobActiveProcesses": 1}}}),
         False)
    case("publisher rejects unconfirmed",
         publisher_confirmed({**good, "terminalConfirmed": False}), False)
    case("phase root terminated needs record",
         phase_root_terminated({"terminalConfirmed": True,
                                "root": {"terminal": True, "jobActiveProcesses": 0}}),
         True)
    case("phase root rejects live job",
         phase_root_terminated({"terminalConfirmed": True,
                                "root": {"terminal": False, "jobActiveProcesses": 3}}),
         False)
    case("phase root rejects missing record",
         phase_root_terminated({"terminalConfirmed": True}), False)
    case("phase root rejects None count",
         phase_root_terminated({"terminalConfirmed": True,
                                "root": {"terminal": True,
                                         "jobActiveProcesses": None}}), False)
    case("relay phase forced counts", phase_forced({"forcedCleanup": True}), True)
    case("relay deadline counts as forced", phase_forced({"deadlineReached": True}), True)
    case("clean relay phase is not forced", phase_forced({"name": "relay"}), False)
    case("release needs cleanup", wrapper_claim("HOLD")["releaseReady"], False)
    case("release ready when clean", wrapper_claim("RELEASE_READY")["releaseReady"],
         True)
    case("wrapper never claims a formal release",
         wrapper_claim("RELEASE_READY")["formalReleaseClaimed"], False)
    case("wrapper states it is alive", wrapper_claim("HOLD")["wrapperAlive"], True)
    case("release authority is C",
         wrapper_claim("HOLD")["releaseAuthority"],
         "C, after observing this pid and creation time stop")

    case("gate PASS on a clean record", gate_state(good, True), "PASS")
    case("gate FAIL on a dirty record",
         gate_state({**good, "errors": ["tests failed"]}, True), "FAIL")
    case("gate INCOMPLETE without a record", gate_state({}, True), "INCOMPLETE")
    case("gate INCOMPLETE without ACCEPT", gate_state(good, False), "INCOMPLETE")
    case("ownership ready when released",
         ownership_state(resources_released=True), "RELEASE_READY")
    case("ownership holds when live",
         ownership_state(resources_released=False), "HOLD")
    case("ownership holds when unknown",
         ownership_state(resources_released=None), "HOLD")
    case("publication delivered", publication_state(relay_delivered=True),
         "DELIVERED")
    case("publication failed", publication_state(relay_delivered=False), "FAILED")
    case("budget within", budget_state(late=False), "PROVISIONAL_WITHIN")
    case("budget late", budget_state(late=True), "PROVISIONAL_LATE")
    case("local budget is never final",
         budget_state(late=False).startswith("PROVISIONAL"), True)
    case("a failed gate still releases",
         assess(gate="FAIL", ownership="RELEASE_READY", publication="FAILED",
                budget="PROVISIONAL_LATE")["ownership"], "RELEASE_READY")
    case("the four axes stay independent",
         assess(gate="FAIL", ownership="RELEASE_READY", publication="FAILED",
                budget="PROVISIONAL_LATE"),
         {"gate": "FAIL", "ownership": "RELEASE_READY",
          "publication": "FAILED", "budget": "PROVISIONAL_LATE"})
    case("labels name only the dirty axes",
         failure_labels(gate="FAIL", ownership="RELEASE_READY",
                        publication="FAILED", budget="PROVISIONAL_LATE"),
         ["gate", "publication_failed", "budget_late_provisional"])
    case("labels stay empty when clean",
         failure_labels(gate="PASS", ownership="RELEASE_READY",
                        publication="DELIVERED",
                        budget="PROVISIONAL_WITHIN"), [])
    case("labels call out an incomplete gate",
         failure_labels(gate="INCOMPLETE", ownership="HOLD",
                        publication="FAILED", budget="PROVISIONAL_WITHIN"),
         ["gate_incomplete", "ownership_hold", "publication_failed"])
    case("a forced release with a failed gate is ready",
         assess(gate="FAIL", ownership=ownership_state(resources_released=True),
                publication="FAILED", budget="PROVISIONAL_LATE")["ownership"],
         "RELEASE_READY")

    bad = {**good, "errors": ["tests failed"], "status": "RELEASE_PENDING_ROOT_RELAY"}
    case("gate fails with errors", gate_pass(bad), False)
    case("gate passes clean", gate_pass(good), True)
    case("gate fails on drift", gate_pass({**good, "sourceSnapshotsIdentical": False}), False)

    with tempfile.TemporaryDirectory() as temporary:
        base_dir = Path(temporary)
        case("fresh dirs accepted",
             refusal_for_dirs(base_dir / "a-relay", base_dir / "a"), None)
        (base_dir / "taken-relay").mkdir()
        taken = base_dir / "taken-relay"
        case("wrapper dir replay refused",
             refusal_for_dirs(taken, base_dir / "taken") is not None, True)
        case("wrapper refusal names the dir",
             "taken-relay" in (refusal_for_dirs(taken, base_dir / "taken") or ""), True)
        (base_dir / "childonly").mkdir()
        child = base_dir / "childonly"
        case("child dir replay refused",
             refusal_for_dirs(base_dir / "childonly-relay", child) is not None, True)
        case("child refusal names the dir",
             "childonly" in (refusal_for_dirs(base_dir / "childonly-relay", child) or ""),
             True)
        case("either dir blocks the run", refusal_for_dirs(taken, child) is not None, True)

    snap = snapshot()
    case("snapshot runs nothing", snap["execution"], False)
    case("snapshot starts nothing", snap["processStarted"], False)
    case("snapshot matches frozen", snap["frozenMatch"], True)
    case("snapshot requires authorization", snap["authorizationRequired"], True)
    case("snapshot keeps relay budget",
         snap["windowSeconds"] - snap["supervisorDeadlineSeconds"] >= MIN_RESERVE, True)
    case("snapshot shows two directories",
         snap["directories"]["wrapper"] != snap["directories"]["childEvidence"], True)
    case("snapshot plans an authorization flag",
         "--authorization" in snap["plannedCommand"], True)

    case("reviewed execution gate exists", RUN_ENABLED, True)
    case("state requires a reviewed grant", EXECUTION_STATE, "REVIEWED_GRANT_REQUIRED")
    try:
        run(None)
        run_blocked = False
    except PermissionError:
        run_blocked = True
    except BaseException:
        run_blocked = False
    case("run refuses before touching arguments", run_blocked, True)

    fail_report = {**good, "status": "RELEASE_PENDING_ROOT_RELAY",
                   "errors": ["format phase failed"]}
    fail_text = compose_relay(run_name="fresh-1", grant="C608-WEB180",
                              next_owner="c-coordinator", report=fail_report,
                              wrapper=fake, outer_active=0, forced_cleanup=True,
                              supervisor_terminal=True)
    gate_lines = [line for line in fail_text.splitlines() if line.startswith("gate=")]
    resource_lines = [line for line in fail_text.splitlines()
                      if line.startswith("resources ")]
    case("relay has one gate line", len(gate_lines), 1)
    case("relay has one resource line", len(resource_lines), 1)
    case("relay gate line names FAIL", "gate=FAIL" in gate_lines[0], True)
    case("relay gate line counts errors", "gateErrors=1" in gate_lines[0], True)
    case("relay gate line omits resources", "resources" not in gate_lines[0], True)
    case("relay resource line omits gate", "gate=" not in resource_lines[0], True)
    case("relay resource line names the forced release",
         "forcedRelease=true" in resource_lines[0], True)
    case("relay resource line names the released state",
         "resourcesReleasedAtRelay=true" in resource_lines[0], True)
    case("relay defers wrapper cleanup",
         "wrapperCleanupPending=true" in resource_lines[0], True)
    case("relay pass line on a clean report", "gate=PASS" in text, True)
    case("relay clean resources are not forced",
         "forcedRelease=false" in
         [line for line in text.splitlines() if line.startswith("resources ")][0], True)

    block = deadline_block({"name": "accept"}, {"name": "supervisor"},
                           {"name": "relay"})
    case("deadline names the total", block["totalSeconds"], 180)
    case("deadline names the margin", block["finalWriteMarginSeconds"],
         FINAL_WRITE_MARGIN)
    case("deadline admits no hard timeout", block["hardTimeout"], False)
    case("deadline runs synchronously", block["synchronousExecute"], True)
    case("deadline promises no completion", block["completionPromise"], "none")
    case("deadline marks the local budget provisional",
         block["localBudgetProvisional"], True)
    case("deadline names the budget observer", block["budgetObserverAuthority"],
         "c-coordinator")
    case("deadline margin proves nothing", block["marginProvesCompletion"], False)
    case("deadline starts unreached", block["totalDeadlineReached"], False)
    case("deadline starts unjudged", block["judgedAfterFinalIo"], False)
    case("deadline starts without a phase hit", block["anyPhaseDeadlineReached"], False)
    fired = deadline_block({"name": "accept", "deadlineReached": True},
                           {"name": "supervisor"}, {"name": "relay"})
    case("deadline records a phase hit", fired["anyPhaseDeadlineReached"], True)
    case("deadline names the firing phase", fired["acceptDeadlineReached"], True)
    case("deadline leaves the total alone", fired["totalDeadlineReached"], False)

    with tempfile.TemporaryDirectory() as temporary:
        persist_path = Path(temporary) / "receipt.json"
        holder = {"status": "PENDING_FINAL_IO_CLOCK", "errors": []}
        case("persist succeeds", persist(persist_path, holder) is None, True)
        on_disk = json.loads(persist_path.read_text(encoding="utf-8"))
        case("persisted flag reaches disk", on_disk["reportPersisted"], True)
        case("persisted flag matches memory", holder["reportPersisted"], True)
        case("persisted file holds the status", on_disk["status"],
             "PENDING_FINAL_IO_CLOCK")
        before = json.loads(persist_path.read_text(encoding="utf-8"))
        holder["status"] = "RELAYED"
        blocked = persist(Path(temporary) / "missing" / "receipt.json", holder)
        case("persist reports a failure", blocked is not None, True)
        case("failed persist flips the flag", holder["reportPersisted"], False)
        case("failed persist keeps the old file",
             json.loads(persist_path.read_text(encoding="utf-8")), before)
        case("failed persist leaves the old status",
             json.loads(persist_path.read_text(encoding="utf-8"))["status"],
             "PENDING_FINAL_IO_CLOCK")

    no_launch = ({"name": "accept"}, {"name": "supervisor"}, {"name": "relay"})
    case("no launch leaves nothing live",
         released_resources(cleanup_confirmed=True, held=[], phases=no_launch), True)
    case("no launch is not HOLD",
         ownership_state(resources_released=released_resources(
             cleanup_confirmed=True, held=[], phases=no_launch)), "RELEASE_READY")
    case("a failed ACCEPT is not live",
         released_resources(cleanup_confirmed=True, held=[],
                            phases=({"name": "accept"}, {"name": "supervisor"},
                                    {"name": "relay"})), True)
    case("no supervisor record is still a release",
         released_resources(cleanup_confirmed=True, held=[],
                            phases=({"name": "accept", "root": {"pid": 9,
                                                                   "terminal": True,
                                                                   "jobActiveProcesses": 0}},
                                    {"name": "supervisor"}, {"name": "relay"})),
         True)
    case("a live created Job blocks release",
         released_resources(cleanup_confirmed=True, held=[],
                            phases=({"name": "accept",
                                     "root": {"pid": 9, "terminal": False,
                                              "jobActiveProcesses": 0}},)), False)
    case("a terminal created Job releases",
         released_resources(cleanup_confirmed=True, held=[],
                            phases=({"name": "accept",
                                     "root": {"pid": 9, "terminal": True,
                                              "jobActiveProcesses": 0}},)), True)
    case("an unknown active count blocks release",
         released_resources(cleanup_confirmed=True, held=[],
                            phases=({"name": "accept",
                                     "root": {"pid": 9, "terminal": True,
                                              "jobActiveProcesses": None}},)), False)
    case("a retained handle blocks release",
         released_resources(cleanup_confirmed=True, held=[object()],
                            phases=no_launch), False)
    case("unconfirmed cleanup blocks release",
         released_resources(cleanup_confirmed=False, held=[],
                            phases=no_launch), False)
    case("a root without a pid is no Job",
         created_job_gone({"name": "accept", "root": {"exitCode": 1}}), True)
    case("a phase without a record is no Job",
         created_job_gone({"name": "accept"}), True)

    failures = [entry for entry in cases if not entry[1]]
    for name, ok, actual, expected in cases:
        print(f"{'PASS' if ok else 'FAIL'} {name} actual={actual!r} expected={expected!r}")
    print(json.dumps({"selfTest": True, "cases": len(cases),
                      "passed": len(cases) - len(failures),
                      "failed": len(failures), "execution": False,
                      "processStarted": False}), flush=True)
    return 0 if not failures else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorization",
                        help="Path to a reviewed authorization record; "
                             "required for a real run")
    parser.add_argument("--execute-reviewed", action="store_true")
    parser.add_argument("--reviewed-raw-sha256")
    parser.add_argument("--grant")
    parser.add_argument("--run-name")
    parser.add_argument("--next-owner")
    parser.add_argument("--python-executable", default=os.sys.executable)
    parser.add_argument("--self-test", action="store_true",
                        help="Run pure negative controls only")
    args = parser.parse_args()
    if args.self_test:
        if any((args.grant, args.run_name, args.next_owner, args.authorization,
                args.execute_reviewed, args.reviewed_raw_sha256)):
            parser.error("Self-test takes no grant arguments")
        return self_test()
    if not any((args.grant, args.run_name, args.next_owner, args.authorization,
                args.execute_reviewed, args.reviewed_raw_sha256)):
        print(json.dumps(snapshot()), flush=True)
        return 0 if not frozen_mismatches() else 1
    if not args.execute_reviewed:
        print(json.dumps({"executionState": EXECUTION_STATE, "execution": False,
                          "processStarted": False, "refused": True,
                          "reason": "--execute-reviewed and a fresh root-pinned receipt are required"}),
              flush=True)
        return 3
    if not all((args.authorization, args.grant, args.run_name,
                args.next_owner, args.reviewed_raw_sha256)):
        parser.error("Explicit reviewed execution requires receipt, raw pin, grant, run name and successor")
    if os.name != "nt":
        parser.error("Real execution is Windows-only")
    try:
        problem = validate_args(args.grant, args.run_name, args.next_owner)
        problem = problem or path_refusal(args.run_name)
        if problem:
            raise PermissionError(problem)
        _, _, problem = reviewed_authorization(args, consume=False)
        if problem:
            raise PermissionError(problem)
    except (PermissionError, FileExistsError, ValueError, OSError) as exc:
        print(json.dumps({"executionState": EXECUTION_STATE, "execution": False,
                          "processStarted": False, "refused": True,
                          "reason": f"{type(exc).__name__}: {exc}"}), flush=True)
        return 3
    # Once execution begins, errors must retain their actual evidence. Never
    # relabel a post-launch exception as a no-process authorization refusal.
    return run(args)



if __name__ == "__main__":
    raise SystemExit(main())
