"""Pure authorization validation for the Web relay window.

This module validates one authorization receipt against one coordinator event
record. It starts no process, creates no Job, imports no SDK and sends no channel
message. It never launches the wrapper, never edits it, never reads a channel and
never parses prose.

What this module does not do. It performs no cryptographic authentication and no
language parsing. It cannot prove that a coordinator wrote anything. A normalized
event is not the original authorization. Real authorization semantics live with
root: root reads the coordinator's message, checks it and pins the raw hash. This
module only binds that pin to a short-lived, single-use receipt.

Consumption is keyed on the coordinator and the grant only. A sequence number is
kept as evidence, but a new seq for the same grant never buys a second
consumption. Root may read a coordinator acknowledgement or a restatement of an
old grant, so seq alone must not open a path back in.

A receipt is not the coordinator's grant. Authority still lives with the
coordinator that wrote the event.

Default is refusal. An execution decision needs the explicit
``--execute-reviewed`` flag, a valid receipt and unconsumed grant identity. The
decision is a document, not a launch.

The window is fixed at 180 s. No argument widens it. A receipt and a command that
both claim a larger window are still refused.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re

RECEIPT_SCHEMA = 3
WINDOW_SECONDS = 180

# A receipt is a short-lived token over one recorded event, not a standing pass.
MAX_RECEIPT_LIFETIME_SECONDS = 600
MIN_REMAINING_SECONDS = WINDOW_SECONDS
CLOCK_SKEW_SECONDS = 60

EXECUTE_FLAG = "--execute-reviewed"
MARKER_SUFFIX = ".consumed"

# The one coordinator that may authorize this product's window runs.
EXPECTED_COORDINATOR = "c-coordinator"
EXPECTED_PRODUCT = "web"
EXPECTED_SCOPE = "global"
EXPECTED_PROTOCOL = "web-relay-format-app/v1"

GRANT_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{2,63}")
OWNER_RE = re.compile(r"[a-z][a-z0-9_-]+")
SHA256_RE = re.compile(r"[0-9a-f]{64}")

PLACEHOLDER_TOKENS = ("NEG", "VALID", "TEST", "DUMMY", "EXAMPLE", "PLACEHOLDER",
                      "FAKE", "SAMPLE", "TODO", "FIXTURE")

# Every field that binds a receipt to one exact coordinator event. seq is here as
# evidence only. It is deliberately absent from MARKER_FIELDS.
EVENT_FIELDS = ("seq", "author", "grant", "successor",
                "product", "scope", "protocol")
# One consumption per coordinator and grant. Nothing else decides replay.
MARKER_FIELDS = ("author", "grant")
# The raw channel record is preserved verbatim. Its prose is never parsed.
RAW_EVENT_FIELDS = ("by", "text", "seq", "ts", "kind")
FROZEN_KEYS = ("runner", "worker", "helper")
RECEIPT_FIELDS = ("schemaVersion", "grant", "successor", "windowSeconds",
                  "issuedAtUtc", "expiresAtUtc", "issuedBy", "wrapperSha256",
                  "frozen", "coordinatorEvent", "coordinatorEventSha256",
                  "rawEvent", "rawEventSha256")

FORBIDDEN_IMPORTS = ("subprocess", "ctypes", "socket", "urllib", "http",
                     "requests", "asyncio", "multiprocessing", "win32api")

# Frozen public surface. Root integrates against exactly this list.
__all__ = ("RECEIPT_SCHEMA", "WINDOW_SECONDS", "MAX_RECEIPT_LIFETIME_SECONDS",
           "MIN_REMAINING_SECONDS", "CLOCK_SKEW_SECONDS", "EXECUTE_FLAG",
           "MARKER_SUFFIX", "EXPECTED_COORDINATOR", "EXPECTED_PRODUCT",
           "EXPECTED_SCOPE", "EXPECTED_PROTOCOL", "PLACEHOLDER_TOKENS",
           "FORBIDDEN_IMPORTS", "GRANT_RE", "OWNER_RE", "SHA256_RE",
           "EVENT_FIELDS", "MARKER_FIELDS", "RAW_EVENT_FIELDS", "FROZEN_KEYS",
           "RECEIPT_FIELDS", "utc_now", "canonical", "digest_of",
           "file_sha256", "hashes_for", "parse_utc", "placeholder_tokens",
           "grant_problem", "event_problem", "raw_event_problem",
           "binding_fields", "receipt_id", "marker_binding", "marker_id",
           "marker_path", "consume_marker", "validate_receipt",
           "build_receipt", "decide_execution", "snapshot", "main",
           "self_test")


def utc_now():
    return datetime.now(timezone.utc)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def digest_of(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hashes_for(wrapper, runner, worker, helper):
    """Read the four files this receipt must be bound to."""
    return {"wrapper": file_sha256(wrapper),
            "frozen": {"runner": file_sha256(runner),
                       "worker": file_sha256(worker),
                       "helper": file_sha256(helper)}}


def parse_utc(text):
    if not isinstance(text, str) or not text.strip():
        return None
    try:
        moment = datetime.fromisoformat(text.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if moment.tzinfo is None:
        return None
    return moment


def placeholder_tokens(grant):
    tokens = re.split(r"[._-]", str(grant).upper())
    return [token for token in tokens if token in PLACEHOLDER_TOKENS]


def grant_problem(grant):
    """Shape is not authority. This only rejects unusable strings."""
    if not isinstance(grant, str) or not grant:
        return "An explicit grant is required; no default"
    if not GRANT_RE.fullmatch(grant):
        return "Grant must match the accepted character set"
    bad = placeholder_tokens(grant)
    if bad:
        return f"Placeholder grant tokens are not authorization: {bad}"
    return None


def event_problem(event, *, expected_author=EXPECTED_COORDINATOR,
                  expected_product=EXPECTED_PRODUCT,
                  expected_scope=EXPECTED_SCOPE,
                  expected_protocol=EXPECTED_PROTOCOL):
    """One exact coordinator, one exact protocol, all binding fields present."""
    if not isinstance(event, dict):
        return "A coordinator event record is required"
    for field in EVENT_FIELDS:
        if field not in event:
            return f"Coordinator event lacks {field}"
    seq = event["seq"]
    if isinstance(seq, bool) or not isinstance(seq, int) or seq <= 0:
        return "Coordinator event seq must be a positive integer"
    author = event["author"]
    if not isinstance(author, str):
        return "Coordinator event author must be a named owner"
    if author != expected_author:
        return f"Coordinator event author must be {expected_author}"
    for field, expected in (("product", expected_product),
                            ("scope", expected_scope),
                            ("protocol", expected_protocol)):
        if event[field] != expected:
            return f"Coordinator event {field} must be {expected}"
    problem = grant_problem(event["grant"])
    if problem:
        return f"Coordinator event grant unusable: {problem}"
    successor = event["successor"]
    if not isinstance(successor, str) or not OWNER_RE.fullmatch(successor):
        return "Coordinator event successor must be a named owner"
    return None


def raw_event_problem(raw):
    """The raw channel record must be intact. Its text is stored, never parsed."""
    if not isinstance(raw, dict):
        return "A raw channel event record is required"
    for field in RAW_EVENT_FIELDS:
        if field not in raw:
            return f"Raw event lacks {field}"
    if not isinstance(raw["by"], str) or not raw["by"]:
        return "Raw event by must name its sender"
    seq = raw["seq"]
    if isinstance(seq, bool) or not isinstance(seq, int) or seq <= 0:
        return "Raw event seq must be a positive integer"
    for field in ("text", "ts", "kind"):
        if not isinstance(raw[field], str) or not raw[field].strip():
            return f"Raw event {field} must be a non-empty string"
    return None


def binding_fields(receipt):
    """Everything a receipt claims. Used for reporting, not for consumption."""
    if not isinstance(receipt, dict):
        return {}
    return {"grant": receipt.get("grant"),
            "successor": receipt.get("successor"),
            "coordinatorEvent": receipt.get("coordinatorEvent"),
            "coordinatorEventSha256": receipt.get("coordinatorEventSha256"),
            "rawEvent": receipt.get("rawEvent"),
            "rawEventSha256": receipt.get("rawEventSha256"),
            "wrapperSha256": receipt.get("wrapperSha256"),
            "frozen": receipt.get("frozen")}


def receipt_id(receipt):
    """The receipt's own identity. Changes when any hash changes."""
    if not isinstance(receipt, dict):
        return None
    return digest_of(binding_fields(receipt))


def marker_binding(event):
    """One consumption per coordinator and grant. seq never enters."""
    if not isinstance(event, dict):
        return {}
    return {field: event.get(field) for field in MARKER_FIELDS}


def marker_id(event):
    """Marker name. Independent of run name, seq, hashes and expiry.

    A restated or acknowledged grant carries a new seq. The same coordinator and
    grant still lands on the same marker, so a new seq cannot replay.
    """
    binding = marker_binding(event)
    if not binding or any(binding.get(field) is None for field in MARKER_FIELDS):
        return None
    return digest_of(binding)


def marker_path(directory, rid):
    return Path(directory) / f"{rid}{MARKER_SUFFIX}"


def consume_marker(directory, rid):
    """Consume one marker id exactly once. Exclusive create decides the race."""
    if not isinstance(rid, str) or not SHA256_RE.fullmatch(rid):
        return False, "Marker id must be a lowercase sha256"
    directory = Path(directory)
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except BaseException as exc:
        return False, f"Marker directory unusable: {type(exc).__name__}"
    path = marker_path(directory, rid)
    try:
        handle = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        return False, "Grant already consumed; no replay"
    except BaseException as exc:
        return False, f"Marker create failed: {type(exc).__name__}"
    try:
        os.write(handle, (canonical({"markerId": rid}) + "\n").encode("utf-8"))
    finally:
        os.close(handle)
    return True, None


def _expiry_problems(receipt, now, window):
    """Lifetime cap, remaining runway and future-issue refusal."""
    problems = []
    issued = parse_utc(receipt["issuedAtUtc"])
    expires = parse_utc(receipt["expiresAtUtc"])
    if issued is None:
        problems.append("Receipt issuedAtUtc must be an ISO instant with a zone")
    if expires is None:
        problems.append("Receipt expiresAtUtc must be an ISO instant with a zone")
    if issued is None or expires is None:
        return problems
    if (issued - now).total_seconds() > CLOCK_SKEW_SECONDS:
        problems.append("Receipt issuedAtUtc is in the future")
    if expires <= issued:
        problems.append("Receipt expiry must follow its issue time")
        return problems
    lifetime = (expires - issued).total_seconds()
    if lifetime > MAX_RECEIPT_LIFETIME_SECONDS:
        problems.append("Receipt lifetime exceeds the accepted maximum")
    remaining = (expires - now).total_seconds()
    if remaining <= 0:
        problems.append("Receipt is expired")
    elif remaining < window:
        problems.append(f"Receipt leaves less than the {window} s window")
    return problems


def validate_receipt(receipt, *, command, event, hashes, now=None,
                     window=WINDOW_SECONDS, reviewed_event_sha256=None,
                     reviewed_raw_sha256=None):
    """Return every problem. An empty list means the receipt is acceptable.

    An empty list means the receipt binds one event and one binary set. It does
    not mean the event is authentic. This function writes nothing.
    """
    now = now or utc_now()
    problems = []
    if not isinstance(receipt, dict):
        return ["Receipt must be an object"]
    for field in RECEIPT_FIELDS:
        if field not in receipt:
            problems.append(f"Receipt lacks {field}")
    if problems:
        return problems

    if receipt["schemaVersion"] != RECEIPT_SCHEMA:
        problems.append(f"Receipt schemaVersion must be {RECEIPT_SCHEMA}")

    # The window is fixed. A caller cannot widen it by passing a larger value to
    # both the command and the receipt, and the receipt and command are compared
    # against the constant, never against the caller's value.
    if window != WINDOW_SECONDS:
        problems.append(f"Window must be fixed at {WINDOW_SECONDS}")

    grant = receipt["grant"]
    problem = grant_problem(grant)
    if problem:
        problems.append(problem)
    if not isinstance(command, dict) or command.get("grant") != grant:
        problems.append("Receipt grant does not match the command")
    if not isinstance(event, dict) or event.get("grant") != grant:
        problems.append("Receipt grant is not the coordinator event grant")

    successor = receipt["successor"]
    if not isinstance(successor, str) or not OWNER_RE.fullmatch(successor):
        problems.append("Receipt successor must be a named owner")
    if not isinstance(command, dict) or command.get("successor") != successor:
        problems.append("Receipt successor does not match the command")
    if not isinstance(event, dict) or event.get("successor") != successor:
        problems.append("Receipt successor is not the coordinator event successor")

    if receipt["windowSeconds"] != WINDOW_SECONDS:
        problems.append(f"Receipt window must be {WINDOW_SECONDS}")
    if not isinstance(command, dict) or command.get("windowSeconds") != WINDOW_SECONDS:
        problems.append(f"Command window must be {WINDOW_SECONDS}")

    problems.extend(_expiry_problems(receipt, now, WINDOW_SECONDS))

    issued_by = receipt["issuedBy"]
    if not isinstance(issued_by, str) or not issued_by.strip():
        problems.append("Receipt must name its issuer")

    wrapper_sha = receipt["wrapperSha256"]
    if not isinstance(wrapper_sha, str) or not SHA256_RE.fullmatch(wrapper_sha):
        problems.append("Receipt wrapperSha256 must be a lowercase sha256")
    elif wrapper_sha != (hashes or {}).get("wrapper"):
        problems.append("Receipt wrapper hash does not match the wrapper on disk")

    frozen = receipt["frozen"]
    expected = (hashes or {}).get("frozen") or {}
    if not isinstance(frozen, dict):
        problems.append("Receipt frozen must be an object")
    else:
        for key in FROZEN_KEYS:
            value = frozen.get(key)
            if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
                problems.append(f"Receipt frozen.{key} must be a lowercase sha256")
            elif value != expected.get(key):
                problems.append(f"Receipt frozen.{key} does not match the file on disk")

    bound = receipt["coordinatorEvent"]
    event_problems = event_problem(event)
    if event_problems:
        problems.append(event_problems)
    elif not isinstance(bound, dict):
        problems.append("Receipt coordinatorEvent must be an object")
    else:
        for field in EVENT_FIELDS:
            if bound.get(field) != event.get(field):
                problems.append(f"Receipt coordinatorEvent.{field} is not the event")

    if receipt["coordinatorEventSha256"] != digest_of(event):
        problems.append("Receipt is not bound to this exact coordinator event")

    raw = receipt["rawEvent"]
    raw_problems = raw_event_problem(raw)
    if raw_problems:
        problems.append(raw_problems)
    elif raw["by"] != event.get("author"):
        problems.append("Raw event sender is not the coordinator event author")
    elif raw["seq"] != event.get("seq"):
        problems.append("Raw event seq is not the coordinator event seq")
    if receipt["rawEventSha256"] != digest_of(raw):
        problems.append("Receipt does not preserve this exact raw event")

    if reviewed_event_sha256 is not None:
        if reviewed_event_sha256 != digest_of(event):
            problems.append("Coordinator event is not the root-reviewed event")
    if reviewed_raw_sha256 is not None:
        if reviewed_raw_sha256 != digest_of(raw):
            problems.append("Raw event is not the root-reviewed raw event")

    return problems


def build_receipt(*, event, raw_event, successor, wrapper_sha256, frozen,
                  issued_at, expires_at, issued_by="root",
                  window=WINDOW_SECONDS, now=None):
    """Root builds a receipt from one real coordinator event and its raw record.

    No human approval step exists and none is implied. Root already read the
    message and pinned it. This function only restates and binds.
    """
    now = now or utc_now()
    if window != WINDOW_SECONDS:
        return None, f"Window must be fixed at {WINDOW_SECONDS}"
    problem = event_problem(event)
    if problem:
        return None, problem
    problem = raw_event_problem(raw_event)
    if problem:
        return None, problem
    if raw_event["by"] != event["author"]:
        return None, "Raw event sender is not the coordinator event author"
    if raw_event["seq"] != event["seq"]:
        return None, "Raw event seq is not the coordinator event seq"
    if not isinstance(successor, str) or not OWNER_RE.fullmatch(successor):
        return None, "A named successor is required"
    if successor != event["successor"]:
        return None, "Successor does not match the coordinator event successor"
    if not isinstance(issued_by, str) or not issued_by.strip():
        return None, "A named issuer is required"
    if not isinstance(wrapper_sha256, str) or not SHA256_RE.fullmatch(wrapper_sha256):
        return None, "wrapperSha256 must be a lowercase sha256"
    if not isinstance(frozen, dict):
        return None, "frozen must be an object"
    for key in FROZEN_KEYS:
        value = frozen.get(key)
        if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
            return None, f"frozen.{key} must be a lowercase sha256"
    receipt = {"schemaVersion": RECEIPT_SCHEMA,
               "grant": event["grant"],
               "successor": successor,
               "windowSeconds": window,
               "issuedAtUtc": issued_at,
               "expiresAtUtc": expires_at,
               "issuedBy": issued_by,
               "wrapperSha256": wrapper_sha256,
               "frozen": {key: frozen[key] for key in FROZEN_KEYS},
               "coordinatorEvent": {field: event[field] for field in EVENT_FIELDS},
               "rawEvent": dict(raw_event)}
    receipt["coordinatorEventSha256"] = digest_of(event)
    receipt["rawEventSha256"] = digest_of(raw_event)
    # Any expiry problem refuses. A receipt with a malformed or inverted time
    # must never be produced and then handed on.
    expiry = _expiry_problems(receipt, now, WINDOW_SECONDS)
    if expiry:
        return None, expiry[0]
    return receipt, None


def decide_execution(*, flags, receipt, command, event, hashes, marker_dir,
                     now=None, window=WINDOW_SECONDS,
                     reviewed_event_sha256=None, reviewed_raw_sha256=None):
    """Decide whether an execution would be authorized. It launches nothing.

    Order matters. The flag is checked first, then the receipt, and only a
    receipt that passes may consume its marker. A bad receipt cannot burn a
    good marker.
    """
    flags = tuple(flags or ())
    if EXECUTE_FLAG not in flags:
        return {"execute": False, "processStarted": False,
                "reason": f"{EXECUTE_FLAG} is required; default is refusal"}
    problems = validate_receipt(receipt, command=command, event=event,
                                hashes=hashes, now=now, window=window,
                                reviewed_event_sha256=reviewed_event_sha256,
                                reviewed_raw_sha256=reviewed_raw_sha256)
    if problems:
        return {"execute": False, "processStarted": False,
                "reason": problems[0], "problems": problems}
    rid = marker_id(event)
    consumed, problem = consume_marker(marker_dir, rid)
    if not consumed:
        return {"execute": False, "processStarted": False,
                "receiptId": receipt_id(receipt), "markerId": rid,
                "reason": problem}
    return {"execute": True, "processStarted": False,
            "receiptId": receipt_id(receipt), "markerId": rid,
            "reason": "Receipt bound to the coordinator event and consumed"}


def snapshot():
    return {"module": "web_relay_authorization", "receiptSchema": RECEIPT_SCHEMA,
            "windowSeconds": WINDOW_SECONDS, "executeFlag": EXECUTE_FLAG,
            "defaultDecision": "refuse", "execution": False,
            "processStarted": False, "launchesNothing": True,
            "readsChannel": False, "writesChannel": False,
            "sendsChannel": False, "importsSdk": False,
            "parsesProse": False, "cryptographicAuthentication": False,
            "normalizedEventIsOriginalAuthorization": False,
            "receiptReplacesCoordinatorGrant": False,
            "rawEventPreserved": True,
            "expectedCoordinator": EXPECTED_COORDINATOR,
            "expectedProduct": EXPECTED_PRODUCT,
            "expectedScope": EXPECTED_SCOPE,
            "expectedProtocol": EXPECTED_PROTOCOL,
            "maxReceiptLifetimeSeconds": MAX_RECEIPT_LIFETIME_SECONDS,
            "minRemainingSeconds": MIN_REMAINING_SECONDS,
            "clockSkewSeconds": CLOCK_SKEW_SECONDS,
            "markerFields": list(MARKER_FIELDS),
            "markerDependsOnRunName": False,
            "markerDependsOnSeq": False,
            "markerDependsOnHashes": False,
            "markerDependsOnExpiry": False,
            "forbiddenImports": list(FORBIDDEN_IMPORTS)}


def _load_json(path, label):
    if not path:
        return None, f"{label} path is required"
    target = Path(path)
    if not target.is_file():
        return None, f"{label} file is missing"
    try:
        value = json.loads(target.read_text(encoding="utf-8-sig"))
    except BaseException as exc:
        return None, f"{label} unreadable: {type(exc).__name__}"
    if not isinstance(value, dict):
        return None, f"{label} must be an object"
    return value, None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt")
    parser.add_argument("--event", help="Normalized coordinator event as JSON")
    parser.add_argument("--raw-event", help="Raw channel record as JSON")
    parser.add_argument("--grant")
    parser.add_argument("--successor")
    parser.add_argument("--window-seconds", type=int, default=WINDOW_SECONDS)
    parser.add_argument("--wrapper")
    parser.add_argument("--frozen-runner")
    parser.add_argument("--frozen-worker")
    parser.add_argument("--frozen-helper")
    parser.add_argument("--marker-dir")
    parser.add_argument("--reviewed-event-sha256")
    parser.add_argument("--reviewed-raw-sha256",
                        help="Pin the exact raw record root read and checked")
    parser.add_argument("--execute-reviewed", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    if not any((args.receipt, args.grant, args.successor, args.event,
                args.raw_event, args.execute_reviewed)):
        print(json.dumps(snapshot(), indent=2), flush=True)
        return 0

    receipt, problem = _load_json(args.receipt, "Receipt")
    if problem:
        print(json.dumps({"execute": False, "processStarted": False,
                          "reason": problem}, indent=2), flush=True)
        return 3
    event, problem = _load_json(args.event, "Coordinator event")
    if problem:
        print(json.dumps({"execute": False, "processStarted": False,
                          "reason": problem}, indent=2), flush=True)
        return 3
    raw, problem = _load_json(args.raw_event, "Raw event")
    if problem:
        print(json.dumps({"execute": False, "processStarted": False,
                          "reason": problem}, indent=2), flush=True)
        return 3
    if receipt.get("rawEvent") != raw:
        print(json.dumps({"execute": False, "processStarted": False,
                          "reason": "Receipt does not carry this raw event"},
                         indent=2), flush=True)
        return 3
    try:
        hashes = hashes_for(args.wrapper, args.frozen_runner, args.frozen_worker,
                            args.frozen_helper)
    except BaseException as exc:
        print(json.dumps({"execute": False, "processStarted": False,
                          "reason": f"Hash source unreadable: {type(exc).__name__}"},
                         indent=2), flush=True)
        return 3
    command = {"grant": args.grant, "successor": args.successor,
               "windowSeconds": args.window_seconds}
    flags = (EXECUTE_FLAG,) if args.execute_reviewed else ()
    decision = decide_execution(flags=flags, receipt=receipt, command=command,
                                event=event, hashes=hashes,
                                marker_dir=args.marker_dir or ".",
                                window=args.window_seconds,
                                reviewed_event_sha256=args.reviewed_event_sha256,
                                reviewed_raw_sha256=args.reviewed_raw_sha256)
    decision["launchedNothing"] = True
    print(json.dumps(decision, indent=2), flush=True)
    return 0 if decision["execute"] else 3


def self_test():
    cases = []

    def case(name, actual, expected):
        cases.append((name, actual == expected, actual, expected))

    event = {"seq": 42, "author": EXPECTED_COORDINATOR, "grant": "C608-REALRUN",
             "successor": "c-coordinator", "product": EXPECTED_PRODUCT,
             "scope": EXPECTED_SCOPE, "protocol": EXPECTED_PROTOCOL}
    raw = {"by": EXPECTED_COORDINATOR, "seq": 42, "kind": "grant",
           "ts": "2026-10-26T03:58:40+00:00", "text": "Web ACCEPT"}
    case("snapshot refuses", snapshot()["execution"], False)
    case("snapshot starts nothing", snapshot()["processStarted"], False)
    case("no crypto claim", snapshot()["cryptographicAuthentication"], False)
    case("normalized is not original",
         snapshot()["normalizedEventIsOriginalAuthorization"], False)
    case("placeholder NEG rejected", bool(grant_problem("C607-NEG")), True)
    case("good event accepted", event_problem(event), None)
    case("foreign author rejected",
         bool(event_problem(dict(event, author="d-coordinator"))), True)
    case("wrong protocol rejected",
         bool(event_problem(dict(event, protocol="web-relay-window/v0"))), True)
    case("good raw accepted", raw_event_problem(raw), None)
    case("raw without text rejected",
         bool(raw_event_problem({k: v for k, v in raw.items() if k != "text"})), True)
    case("marker ignores seq", marker_id(event), marker_id(dict(event, seq=43)))
    case("marker changes with grant",
         marker_id(event) != marker_id(dict(event, grant="C609-REALRUN")), True)
    case("marker ignores hashes", marker_binding(event),
         {"author": EXPECTED_COORDINATOR, "grant": "C608-REALRUN"})
    case("no flag refuses",
         decide_execution(flags=(), receipt={}, command={}, event={},
                          hashes={}, marker_dir=".")["execute"], False)
    case("build refuses a non-180 window", build_receipt(
        event=event, raw_event=raw, successor="c-coordinator",
        wrapper_sha256="a" * 64,
        frozen={"runner": "b" * 64, "worker": "c" * 64, "helper": "d" * 64},
        issued_at="2026-10-26T03:59:00+00:00",
        expires_at="2026-10-26T04:05:00+00:00",
        window=360)[0], None)
    case("build refuses a malformed issue time", build_receipt(
        event=event, raw_event=raw, successor="c-coordinator",
        wrapper_sha256="a" * 64,
        frozen={"runner": "b" * 64, "worker": "c" * 64, "helper": "d" * 64},
        issued_at="not-a-time",
        expires_at="2026-10-26T04:05:00+00:00")[0], None)
    case("build refuses an inverted expiry", build_receipt(
        event=event, raw_event=raw, successor="c-coordinator",
        wrapper_sha256="a" * 64,
        frozen={"runner": "b" * 64, "worker": "c" * 64, "helper": "d" * 64},
        issued_at="2026-10-26T04:05:00+00:00",
        expires_at="2026-10-26T03:59:00+00:00")[0], None)

    failures = [entry for entry in cases if not entry[1]]
    for name, ok, actual, expected in cases:
        print(f"{'PASS' if ok else 'FAIL'} {name} actual={actual!r} expected={expected!r}")
    print(json.dumps({"selfTest": True, "cases": len(cases),
                      "passed": len(cases) - len(failures),
                      "failed": len(failures), "execution": False,
                      "processStarted": False}), flush=True)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
