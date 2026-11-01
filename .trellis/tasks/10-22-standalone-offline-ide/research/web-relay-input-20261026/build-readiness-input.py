"""Build the readiness input manifest for the current policy/broker repair scope.

What this manifest freezes:

  - the frozen supervisor interface (runner, worker, owned helper) and its pins
  - the reviewed authorization module hash the relay wrapper pins
  - the five formatter paths the relay wrapper names
  - the four policy/broker repair files by hash
  - the authoritative 164-file freeze manifest and the live 332-file app snapshot
  - the current core commit and its live work by an exact, fully hashed inventory

Two rules this script obeys on purpose:

  - Raw `git status --porcelain` output is never stripped as a whole. A whole-output
    strip erases the leading status space of the first line, so slicing the status
    codes then eats the first filename character. Lines are split and kept exactly.
  - Untracked directories are expanded with `--untracked-files=all`, so every listed
    entry is a file that can be hashed. A directory that stays unexpanded is reported
    as unhashed instead of being counted as a complete file.

This script only reads. It writes one file.

Run: python -B -X utf8 build-readiness-input.py
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parent
ROOT = RESEARCH.parents[3]
CORE = ROOT.parent / "qfli_studio_core"
QFLI_C = ROOT.parent / "qfli_c"

SUPERSEDES = {
    "path": "web-app-c782-20261026/source-before.json",
    "coreHead": "2f9039a3ba95449679b17257b0313c1ee3644a2c",
    "files": 332,
    "reusable": False,
    "reason": ("Old C782 input snapshot. It carries the same 332-file count as the live "
               "app snapshot but the stale capture HEAD 2f, so reusing it would look "
               "valid and carry wrong core metadata. Use this input instead."),
}

FREEZE = {
    "repo": "qfli_c",
    "commit": "0851e565920e746c4c093d85dfe612a4646f3b7c",
    "path": (".trellis/tasks/10-22-offline-standalone-ide/research/"
             "terminal-recovery-20261026/core-lib-config-freeze.json"),
    "sha256": "863F97CEB34FCB491780F1BA4AC38DADF472E1BA28C0CF0F7A522F89BA4E04D0",
    "boundFiles": 164,
    "captureHead": "2f9039a3ba95449679b17257b0313c1ee3644a2c",
}

FROZEN = {
    ".trellis/tasks/10-22-standalone-offline-ide/research/run-web-app-window.py":
        "d80c46e1b1cf2abe7e7a582e61016ac36266354242de198a5623628659922a19",
    ".trellis/tasks/10-22-standalone-offline-ide/research/run-web-app-worker.ps1":
        "074ac02216bab95e8da23d87dca7d1567be5f2fcc4722d43e53d059227fb8b78",
    ".trellis/tasks/10-22-standalone-offline-ide/research/run-web-owned-window.py":
        "9df7a94399aae38951337d61693d65de6e3cef438d02d4e51c787242dfda7fbe",
}

FORMATTER_PATHS = (
    "lib/services/owned_preview_policy.dart",
    "lib/services/owned_preview_resource_broker.dart",
    "test/owned_preview_policy_test.dart",
    "test/owned_preview_resource_broker_test.dart",
    "test/web_offline_browser_test.dart",
)

REPAIR_FILES = FORMATTER_PATHS[:4]

AUTHORIZATION = {
    "module": ".trellis/tasks/10-22-standalone-offline-ide/research/web_relay_authorization.py",
    "pinnedSha256": "84445442fed9b9382555e02b8812c6321cbd7c7ec5026ff13904c5f5897a1de4",
}

APP_FULL_INPUTS = "app-full-inputs.json"

OBSERVERS = {
    "finalObserver": {
        "path": ".trellis/tasks/10-22-standalone-offline-ide/research/run-web-observed-relay-window.py",
        "expectedSha256": "D1943BD1E622FC3CA5FE327E1473A141B3AF992CF48FC61F078F3140FC6552B3",
    },
    "test": {
        "path": ".trellis/tasks/10-22-standalone-offline-ide/research/test_web_observed_relay_window.py",
        "expectedSha256": "81D61C8B0F639222725DF141AB9E63FD07280C9C053EBC065775BB777E60DEDC",
    },
}

# The four repair files are unchanged against the current review. The older static
# review recorded smaller sizes, so only that note differs.
OLDER_REVIEW_SIZES = {
    "lib/services/owned_preview_resource_broker.dart": (11495, 11793),
    "test/owned_preview_resource_broker_test.dart": (18588, 19454),
}

CAPTURES = (
    "relay-window-default", "app-window-snapshot-only",
    "native-window-snapshot-only", "ohpm-window-snapshot-only",
)


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
    """Split porcelain exactly. Never strip the whole output or a single line."""
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


def freeze_state():
    """Read the 164-file freeze manifest and check it against the live core."""
    candidate = QFLI_C / pk(FREEZE["path"])
    if candidate.is_file():
        raw = candidate.read_bytes()
    else:
        raw = subprocess.run(["git", "-C", str(QFLI_C), "show",
                              f"{FREEZE['commit']}:{FREEZE['path']}"],
                             check=True, capture_output=True, timeout=30).stdout
    document = json.loads(raw.decode("utf-8"))
    bound = document.get("files")
    if not isinstance(bound, dict):
        raise ValueError("Freeze manifest files entry is not an object")
    matched, mismatched, missing = [], [], []
    for path, digest in sorted(bound.items()):
        full = CORE.joinpath(*path.split("/"))
        if not full.is_file():
            missing.append(path)
        elif sha256_file(full) == digest.upper():
            matched.append(path)
        else:
            mismatched.append(path)
    return {"repo": FREEZE["repo"], "commit": FREEZE["commit"], "path": FREEZE["path"],
            "sha256": hashlib.sha256(raw).hexdigest().upper(),
            "pinnedSha256": FREEZE["sha256"],
            "match": hashlib.sha256(raw).hexdigest().upper() == FREEZE["sha256"],
            "kind": document.get("kind"),
            "captureHead": document.get("head"),
            "productionTerminalSha256": document.get("productionTerminalSha256"),
            "boundFiles": len(bound),
            "coverageLimits": document.get("coverageLimits"),
            "liveCoreCheck": {"checked": len(bound), "matched": len(matched),
                              "mismatched": mismatched, "missing": missing,
                              "allBoundBytesMatchLiveCore": not mismatched and not missing}}


def product_state():
    """Record the current product commit and the files that commit touched."""
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
            "files": rows, "researchOnly": not outside, "nonResearchFiles": outside}


def observer_state():
    rows = []
    for role, spec in OBSERVERS.items():
        full = ROOT / pk(spec["path"])
        live = sha256_file(full) if full.is_file() else None
        rows.append({"role": role, "path": spec["path"],
                     "expectedSha256": spec["expectedSha256"], "liveSha256": live,
                     "bytes": full.stat().st_size if full.is_file() else None,
                     "match": live == spec["expectedSha256"]})
    return rows


def app_full_state(formatter_paths):
    target = HERE / APP_FULL_INPUTS
    if not target.is_file():
        return {"path": APP_FULL_INPUTS, "present": False}
    document = json.loads(target.read_text("utf-8"))
    files = document["files"]
    index = {row["path"]: row for row in files}
    cross = [{"path": item["path"],
              "inFullInputs": item["path"] in index,
              "bytesMatch": item["path"] in index and index[item["path"]]["bytes"] == item["bytes"],
              "sha256Match": item["path"] in index and
              index[item["path"]]["sha256"].upper() == item["sha256"]}
             for item in formatter_paths]
    digest = canonical_sha256(files)
    return {"path": APP_FULL_INPUTS, "present": True,
            "sha256": sha256_file(target),
            "filesCount": document["filesCount"], "filesSha256": digest,
            "declaredFilesSha256": document["filesSha256"],
            "filesSha256MatchesCapture": digest == document["filesSha256"],
            "perFileHashCase": "lowercase hexdigest from the frozen snapshot",
            "coreHead": document["coreHead"],
            "processesStarted": document["capture"]["processesStarted"],
            "mainGuardHeld": document["capture"]["mainGuardHeld"],
            "helperImported": document["capture"]["helperImported"],
            "crossCheck": cross,
            "allFormatterFilesMatch": all(
                row["inFullInputs"] and row["bytesMatch"] and row["sha256Match"]
                for row in cross)}


def main():
    frozen = []
    for path, digest in FROZEN.items():
        live = sha256_file(ROOT / pk(path))
        frozen.append({"path": path, "pinnedSha256": digest.upper(), "liveSha256": live,
                       "match": live == digest.upper()})
    formatter_paths = [
        {"path": path, "bytes": (ROOT / pk(path)).stat().st_size,
         "sha256": sha256_file(ROOT / pk(path)),
         "repairFile": path in REPAIR_FILES}
        for path in FORMATTER_PATHS]
    authorization_live = sha256_file(ROOT / AUTHORIZATION["module"])
    captures = []
    for name in CAPTURES:
        out = HERE / f"{name}.stdout.json"
        record = {"name": name, "stdoutFile": out.name}
        if out.is_file():
            record.update(stdoutBytes=out.stat().st_size,
                          stdoutSha256=sha256_file(out))
        captures.append(record)
    app_capture = next(item for item in captures
                       if item["name"] == "app-window-snapshot-only")
    actual_files = 0
    if (HERE / app_capture["stdoutFile"]).is_file():
        actual_files = json.loads((HERE / app_capture["stdoutFile"]).read_text("utf-8"))["files"]
    full_inputs = app_full_state(formatter_paths)
    observers = observer_state()
    older_review = [{"path": path, "olderReviewBytes": older, "currentBytes": current}
                    for path, (older, current) in OLDER_REVIEW_SIZES.items()]
    manifest = {
        "schemaVersion": 4,
        "kind": "web-relay-readiness-input",
        "sourceOnly": True,
        "execution": False,
        "checkedUtc": utc(),
        "supersedes": SUPERSEDES,
        "authoritative": {
            "actualSnapshot": {
                "files": actual_files,
                "capture": app_capture["stdoutFile"],
                "captureSha256": app_capture.get("stdoutSha256"),
                "command": "python -B -X utf8 run-web-app-window.py --snapshot-only",
                "note": ("--snapshot-only prints only the file count. The count and the "
                         "capture hash are a summary, not a hash set."),
            },
            "fullInputs": full_inputs,
            "freezeManifest": freeze_state(),
            "coreCheckpoint": {
                "head": head_of(CORE),
                "relation": ("Freeze capture HEAD 2f is historical metadata. The bound "
                             "working bytes stay authoritative. This checkpoint is the "
                             "current tested core commit."),
            },
        },
        "product": product_state(),
        "frozenInterface": {
            "runner": frozen[0], "worker": frozen[1], "helper": frozen[2],
            "runnerSha256": FROZEN[next(iter(FROZEN))].upper(),
            "protocol": "web-relay-format-app/v1",
            "wrapperPath": ".trellis/tasks/10-22-standalone-offline-ide/research/run-web-relay-window.py",
            "windowSeconds": 180, "executeFlagRequired": True,
            "reviewedExecutionRefused": True,
        },
        "authorization": {**AUTHORIZATION, "liveSha256": authorization_live,
                          "match": authorization_live == AUTHORIZATION["pinnedSha256"].upper()},
        "formatterPaths": formatter_paths,
        "repairFiles": [item for item in formatter_paths if item["repairFile"]],
        "reviewHashes": {
            "note": ("The four repair files keep the hashes the current review holds. "
                     "Their sizes differ only against the older static review record."),
            "olderReviewSizes": older_review,
        },
        "observers": observers,
        "observerMatch": all(item["match"] for item in observers),
        "core": core_state(),
        "captures": captures,
        "snapshotOnlyCommands": {
            "relay": "python -B -X utf8 run-web-relay-window.py",
            "app": "python -B -X utf8 run-web-app-window.py --snapshot-only",
            "native": "python -B -X utf8 run-web-native-window.py --snapshot-only",
            "ohpm": "python -B -X utf8 run-web-ohpm-window.py --snapshot-only",
        },
        "notProven": [
            "No formatter, test, analysis, content or gate phase ran for this input.",
            "No reviewed authorization record was created, read or consumed.",
            "No unnamed successor, channel message or READY publication was made.",
            "The frozen supervisor was imported only to call snapshot(). Its main is guarded.",
            "load_helper, run and execute were never called; no Job and no channel.",
            "A live core worktree is recorded, not validated: the WIP itself is unproven.",
            "The freeze manifest binds a working tree, not a clean core commit.",
            "READY stays closed until a later gate run produces real evidence.",
        ],
    }
    manifest["frozenMatch"] = all(item["match"] for item in frozen)
    target = HERE / "readiness-input.json"
    target.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "path": str(target), "frozenMatch": manifest["frozenMatch"],
        "productHead": manifest["product"]["head"],
        "productResearchOnly": manifest["product"]["researchOnly"],
        "authorizationMatch": manifest["authorization"]["match"],
        "coreHead": manifest["core"]["head"], "coreStatusEntries": manifest["core"]["statusEntries"],
        "wipFilesHashed": manifest["core"]["wipFilesHashed"],
        "completeWipFiles": manifest["core"]["completeWipFiles"],
        "freezeMatch": manifest["authoritative"]["freezeManifest"]["match"],
        "fullInputsPresent": full_inputs.get("present"),
        "fullInputsFiles": full_inputs.get("filesCount"),
        "fullInputsFilesSha256": full_inputs.get("filesSha256"),
        "fullInputsAllFormatterMatch": full_inputs.get("allFormatterFilesMatch"),
        "observerMatch": manifest["observerMatch"],
        "freezeBoundFilesMatchLive": manifest["authoritative"]["freezeManifest"]["liveCoreCheck"]["allBoundBytesMatchLiveCore"],
        "actualSnapshotFiles": manifest["authoritative"]["actualSnapshot"]["files"],
        "formatterPaths": len(formatter_paths), "sha256": sha256_file(target)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())