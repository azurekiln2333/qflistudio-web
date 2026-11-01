"""C864 refreeze: build the readiness input manifest for the policy/broker repair scope.

What this manifest binds:

  - the seven frozen review artifacts (observer, test, wrapper, authorization,
    runner, worker, helper) with live hashes and pinned hashes
  - the five formatter paths the relay wrapper names, four of them repair files
  - the actual current product HEAD, read live, never hardcoded
  - the current core HEAD and its live work, by an exact, fully hashed inventory
  - the full 332-file app input snapshot from pinned snapshot()
  - the historical 164-file freeze, reported as 163 unchanged plus the one exact
    supervisor replacement. The old 164-hash match is never claimed.
  - the permitted-change check against the preserved parent capture

Two rules this script obeys on purpose:

  - Raw `git status --porcelain` output is never stripped as a whole. A whole-output
    strip erases the leading status space of the first line, so slicing the status
    codes then eats the first filename character. Lines are split and kept exactly.
  - Untracked directories are expanded with `--untracked-files=all`, so every listed
    entry is a file that can be hashed. A directory that stays unexpanded is reported
    as unhashed instead of being counted as a complete file.

This script only reads. It writes one file inside this directory.

Run: python -B -X utf8 build-readiness-input.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parent
ROOT = RESEARCH.parents[3]
CORE = ROOT.parent / "qfli_studio_core"
QFLI_C = ROOT.parent / "qfli_c"

PARENT = {
    "directory": "web-relay-input-20261026",
    "status": "historical, preserved, not rewritten",
    "manifestSha256": "226CB055D74439B6B7319D9796AEC62D70329144FDAB35FFEBBFD295AC7DA91A",
    "fullInputsSha256": "2DDB7E3846BAE9550DAEF5574CC21169407EDD8932373CAF088F1F115E9C572C",
    "coreHead": "64f0aa75a773c632a1101ce16e1900615b274960",
    "productHead": "26b5d14fa1ec8df46f4331625bf72fef6aea7f27",
}

PARENT_FREEZE = {
    "repo": "qfli_c",
    "commit": "0851e565920e746c4c093d85dfe612a4646f3b7c",
    "path": (".trellis/tasks/10-22-offline-standalone-ide/research/"
             "terminal-recovery-20261026/core-lib-config-freeze.json"),
    "sha256": "863F97CEB34FCB491780F1BA4AC38DADF472E1BA28C0CF0F7A522F89BA4E04D0",
    "kind": "current-workspace-source-binding-not-tested-acceptance",
    "captureHead": "2f9039a3ba95449679b17257b0313c1ee3644a2c",
    "boundFiles": 164,
    "unchangedExpected": 163,
    "replacement": {
        "path": "lib/services/process_supervisor.dart",
        "currentSha256": "095DE8C17C66DC206FE170B3F99B7447D8660F183085ECB338F97484FF0E5BFC",
    },
}

# Seven frozen review artifacts. The relay wrapper pins the runner, worker, helper
# and authorization module. The observer and its test were committed at 26b5d14.
FROZEN_PINS = (
    ("observer", ".trellis/tasks/10-22-standalone-offline-ide/research/run-web-observed-relay-window.py",
     "D1943BD1E622FC3CA5FE327E1473A141B3AF992CF48FC61F078F3140FC6552B3"),
    ("test", ".trellis/tasks/10-22-standalone-offline-ide/research/test_web_observed_relay_window.py",
     "81D61C8B0F639222725DF141AB9E63FD07280C9C053EBC065775BB777E60DEDC"),
    ("wrapper", ".trellis/tasks/10-22-standalone-offline-ide/research/run-web-relay-window.py",
     "401F61D44495DD0A8B681A25746263E589203A9555F30C49106ECA791DB0FDB3"),
    ("authorization", ".trellis/tasks/10-22-standalone-offline-ide/research/web_relay_authorization.py",
     "84445442FED9B9382555E02B8812C6321CBD7C7EC5026FF13904C5F5897A1DE4"),
    ("runner", ".trellis/tasks/10-22-standalone-offline-ide/research/run-web-app-window.py",
     "D80C46E1B1CF2ABE7E7A582E61016AC36266354242DE198A5623628659922A19"),
    ("worker", ".trellis/tasks/10-22-standalone-offline-ide/research/run-web-app-worker.ps1",
     "074AC02216BAB95E8DA23D87DCA7D1567BE5F2FCC4722D43E53D059227FB8B78"),
    ("helper", ".trellis/tasks/10-22-standalone-offline-ide/research/run-web-owned-window.py",
     "9DF7A94399AAE38951337D61693D65DE6E3CEF438D02D4E51C787242DFDA7FBE"),
)

FORMATTER_PATHS = (
    "lib/services/owned_preview_policy.dart",
    "lib/services/owned_preview_resource_broker.dart",
    "test/owned_preview_policy_test.dart",
    "test/owned_preview_resource_broker_test.dart",
    "test/web_offline_browser_test.dart",
)

REPAIR_FILES = FORMATTER_PATHS[:4]

APP_FULL_INPUTS = "app-full-inputs.json"

ALLOWED_DELTA = {
    "lib/services/process_supervisor.dart",
    "../qfli_studio_core/lib/services/process_supervisor.dart",
    "test/owned_preview_resource_broker_test.dart",
}


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def canonical_sha256(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest().upper()


def pk(path):
    return Path(path).as_posix()


def raw_stdout(arguments, cwd):
    return subprocess.run(["git", *arguments], cwd=str(cwd), check=True,
                          capture_output=True, text=True, timeout=30).stdout


def head_of(cwd):
    return raw_stdout(["rev-parse", "HEAD"], cwd).strip()


def branch_of(cwd):
    return raw_stdout(["rev-parse", "--abbrev-ref", "HEAD"], cwd).strip()


def status_lines(cwd, *extra):
    text = raw_stdout(["status", "--porcelain", *extra], cwd)
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def core_state():
    rows, malformed, directory_entries = [], [], []
    for line in status_lines(CORE, "--untracked-files=all"):
        if line == "":
            continue
        if len(line) < 4 or line[2] != " ":
            malformed.append(line)
            continue
        code, path = line[:2], line[3:]
        full = CORE.joinpath(*path.split("/"))
        row = {"code": code, "path": path}
        if full.is_dir():
            directory_entries.append(path)
            rows.append(row)
            continue
        if full.is_file():
            row.update(bytes=full.stat().st_size, sha256=sha256_file(full))
        rows.append(row)
    rows.sort(key=lambda item: item["path"])
    rollup = hashlib.sha256(json.dumps(
        [[r["code"], r["path"], r.get("bytes"), r.get("sha256")] for r in rows],
        separators=(",", ":")).encode("utf-8")).hexdigest().upper()
    hashed = sum(1 for r in rows if "sha256" in r)
    return {"head": head_of(CORE), "branch": branch_of(CORE),
            "statusEntries": len(rows), "wipFilesHashed": hashed,
            "wipDirectoryEntries": directory_entries,
            "malformedStatusLines": malformed,
            "completeWipFiles": not directory_entries and not malformed,
            "wipRollupSha256": rollup, "wip": rows,
            "untrackedExpansion": "git status --porcelain --untracked-files=all"}


def parent_freeze_state():
    candidate = QFLI_C / pk(PARENT_FREEZE["path"])
    if candidate.is_file():
        raw = candidate.read_bytes()
    else:
        raw = subprocess.run(["git", "-C", str(QFLI_C), "show",
                              f"{PARENT_FREEZE['commit']}:{PARENT_FREEZE['path']}"],
                             check=True, capture_output=True, timeout=30).stdout
    document = json.loads(raw.decode("utf-8"))
    bound = document.get("files")
    if not isinstance(bound, dict):
        raise ValueError("Parent freeze files entry is not an object")
    unchanged, changed, missing = [], [], []
    for path, digest in sorted(bound.items()):
        full = CORE.joinpath(*path.split("/"))
        if not full.is_file():
            missing.append(path)
        elif sha256_file(full) == digest.upper():
            unchanged.append(path)
        else:
            changed.append({"path": path, "parentSha256": digest.upper(),
                            "liveSha256": sha256_file(full)})
    return {"repo": PARENT_FREEZE["repo"], "commit": PARENT_FREEZE["commit"],
            "path": PARENT_FREEZE["path"],
            "sha256": hashlib.sha256(raw).hexdigest().upper(),
            "match": hashlib.sha256(raw).hexdigest().upper() == PARENT_FREEZE["sha256"],
            "kind": document.get("kind"), "captureHead": document.get("head"),
            "boundFiles": len(bound),
            "liveCheck": {"checked": len(bound), "unchanged": len(unchanged),
                          "changed": changed, "missing": missing,
                          "claimsOldHashMatch": False,
                          "note": ("The parent freeze stays a historical binding. "
                                   "Only the supervisor replacement is live.")},
            "supervisorReplacement": {
                "path": PARENT_FREEZE["replacement"]["path"],
                "parentSha256": bound.get(PARENT_FREEZE["replacement"]["path"], "").upper(),
                "currentSha256": PARENT_FREEZE["replacement"]["currentSha256"],
                "liveSha256": sha256_file(
                    CORE.joinpath(*PARENT_FREEZE["replacement"]["path"].split("/"))),
                "exact": (sha256_file(CORE.joinpath(
                    *PARENT_FREEZE["replacement"]["path"].split("/")))
                    == PARENT_FREEZE["replacement"]["currentSha256"]),
                "unchangedExpected": PARENT_FREEZE["unchangedExpected"],
                "observedUnchanged": len(unchanged)}}


def product_state():
    head = head_of(ROOT)
    subject = raw_stdout(["log", "-1", "--pretty=%s"], ROOT).strip()
    rows = []
    for line in raw_stdout(["show", "--name-status", "--pretty=format:", head], ROOT).split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t")
        path = parts[-1]
        full = ROOT.joinpath(*path.split("/"))
        row = {"status": parts[0], "path": path}
        if full.is_file():
            row.update(bytes=full.stat().st_size, sha256=sha256_file(full))
        rows.append(row)
    outside = [row["path"] for row in rows if not row["path"].startswith(".trellis/")]
    return {"root": str(ROOT), "head": head, "shortHead": head[:7],
            "branch": branch_of(ROOT), "subject": subject,
            "headCommitFiles": rows, "researchOnly": not outside,
            "nonResearchFiles": outside}


def app_full_state():
    target = HERE / APP_FULL_INPUTS
    if not target.is_file():
        return {"path": APP_FULL_INPUTS, "present": False}
    document = json.loads(target.read_text("utf-8"))
    files = document["files"]
    digest = canonical_sha256(files)
    return {"path": APP_FULL_INPUTS, "present": True, "sha256": sha256_file(target),
            "filesCount": document["filesCount"], "filesSha256": digest,
            "declaredFilesSha256": document["filesSha256"],
            "filesSha256MatchesCapture": digest == document["filesSha256"],
            "perFileHashCase": "lowercase hexdigest from the frozen snapshot",
            "coreHead": document["coreHead"],
            "processesStarted": document["capture"]["processesStarted"],
            "mainGuardHeld": document["capture"]["mainGuardHeld"],
            "files": files}


def parent_delta(current_files):
    parent = RESEARCH / PARENT["directory"] / APP_FULL_INPUTS
    if not parent.is_file():
        return {"available": False}
    old = {row["path"]: (row["bytes"], row["sha256"]) for row in
           json.loads(parent.read_text("utf-8"))["files"]}
    new = {row["path"]: (row["bytes"], row["sha256"]) for row in current_files}
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed = sorted(path for path in set(old) & set(new) if old[path][1] != new[path][1])
    unexpected = sorted(set(changed) - ALLOWED_DELTA)
    return {"available": True, "parentFiles": len(old), "currentFiles": len(new),
            "added": added, "removed": removed, "changed": changed,
            "allowed": sorted(ALLOWED_DELTA),
            "unexpectedChanges": unexpected,
            "permittedOnly": not unexpected and not added and not removed}


def main():
    pins = []
    for role, path, expected in FROZEN_PINS:
        full = ROOT / pk(path)
        live = sha256_file(full) if full.is_file() else None
        pins.append({"role": role, "path": path, "pinnedSha256": expected.upper(),
                     "liveSha256": live, "bytes": full.stat().st_size if full.is_file() else None,
                     "match": live == expected.upper()})
    formatter_paths = [
        {"path": path, "bytes": (ROOT / pk(path)).stat().st_size,
         "sha256": sha256_file(ROOT / pk(path)), "repairFile": path in REPAIR_FILES}
        for path in FORMATTER_PATHS]
    full_inputs = app_full_state()
    delta = parent_delta(full_inputs.get("files", []))
    freeze = parent_freeze_state()
    manifest = {
        "schemaVersion": 5,
        "kind": "web-relay-readiness-input",
        "window": "c864",
        "sourceOnly": True,
        "execution": False,
        "checkedUtc": utc(),
        "historicalParent": PARENT,
        "authoritative": {
            "fullInputs": {key: value for key, value in full_inputs.items() if key != "files"},
            "parentFreeze": freeze,
            "coreCheckpoint": {
                "head": head_of(CORE),
                "relation": ("Parent freeze capture HEAD 2f is historical metadata. Its "
                             "bound working bytes stay historical too, with exactly one "
                             "supervisor replacement. This checkpoint is the current core."),
            },
        },
        "frozenPins": pins,
        "frozenMatch": all(pin["match"] for pin in pins),
        "formatterPaths": formatter_paths,
        "repairFiles": [item for item in formatter_paths if item["repairFile"]],
        "repairStatus": {
            "owned_preview_resource_broker_test.dart":
                ("UNRUN for the combined candidate. The fixture cleanup is new and "
                 "has never run. The production broker bytes did run in C843 and the "
                 "gate failed there."),
            "combinedCandidate":
                ("UNRUN. Production bytes plus the fixture cleanup have not run "
                 "together, so no new pass is claimed."),
            "brokerProductionBytes":
                ("Exercised in C843 as 320 PASS and 1 FAIL, a failed gate. "
                 "Those bytes are not a pass."),
        },
        "product": product_state(),
        "core": core_state(),
        "permittedChanges": delta,
        "notProven": [
            "No formatter, test, analysis, content or gate phase ran for this input.",
            "No reviewed authorization record was created, read or consumed.",
            "No READY publication, channel message, grant or successor was made.",
            "The frozen supervisor was imported only to call snapshot(). Its main is guarded.",
            "load_helper, run and execute were never called; no Job and no channel.",
            "The combined candidate, production bytes plus the fixture cleanup, is UNRUN.",
            "The broker production bytes were exercised in C843 and the gate failed there: 320 PASS, 1 FAIL. No new pass is claimed.",
            "The historical 164 freeze is not a 164-hash match today.",
        ],
    }
    target = HERE / "readiness-input.json"
    target.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "path": str(target), "window": manifest["window"],
        "productHead": manifest["product"]["head"], "coreHead": manifest["core"]["head"],
        "frozenMatch": manifest["frozenMatch"],
        "fullInputsFiles": full_inputs.get("filesCount"),
        "fullInputsFilesSha256": full_inputs.get("filesSha256"),
        "freezeUnchanged": freeze["liveCheck"]["unchanged"],
        "freezeChanged": [row["path"] for row in freeze["liveCheck"]["changed"]],
        "freezeBound": freeze["liveCheck"]["checked"],
        "supervisorExact": freeze["supervisorReplacement"]["exact"],
        "deltaPermittedOnly": delta.get("permittedOnly"),
        "deltaChanged": delta.get("changed"), "deltaUnexpected": delta.get("unexpectedChanges"),
        "coreWipFilesHashed": manifest["core"]["wipFilesHashed"],
        "completeWipFiles": manifest["core"]["completeWipFiles"],
        "sha256": sha256_file(target)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())