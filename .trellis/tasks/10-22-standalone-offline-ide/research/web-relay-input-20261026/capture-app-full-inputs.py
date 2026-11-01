"""Capture the full read-only input list from the pinned app supervisor.

`run-web-app-window.py --snapshot-only` prints only a summary: the file count,
the core HEAD and the runtime paths. It never prints the per-file hashes. This
script calls the same frozen `snapshot()` function directly and saves the whole
result, so the readiness input can bind real file hashes.

Why this is safe, checked before the import and again after it:

  - `snapshot()` is inspected first. It reads and hashes files, resolves tool
    paths with `shutil.which`, and runs exactly one subprocess:
    `git -C <core> rev-parse HEAD`. It starts no Job and opens no channel.
  - `execute()`, which does start a Job through `helper.OwnedJob()`, is reached
    only from `main()`. `main()` is behind `if __name__ == "__main__":`.
  - The module is imported under a private name, so that guard cannot fire. The
    script asserts the guard did not run.
  - `load_helper()` is not called, `run()` is not called, `execute()` is not
    called, and no grant argument exists in this file.
  - The three frozen pins are verified before the import. A changed supervisor
    is refused instead of being executed.

Run: python -B -X utf8 capture-app-full-inputs.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parent
ROOT = RESEARCH.parents[3]
CORE = ROOT.parent / "qfli_studio_core"

RUNNER = RESEARCH / "run-web-app-window.py"
WORKER = RESEARCH / "run-web-app-worker.ps1"
HELPER = RESEARCH / "run-web-owned-window.py"

PINS = {
    RUNNER: "D80C46E1B1CF2ABE7E7A582E61016AC36266354242DE198A5623628659922A19",
    WORKER: "074AC02216BAB95E8DA23D87DCA7D1567BE5F2FCC4722D43E53D059227FB8B78",
    HELPER: "9DF7A94399AAE38951337D61693D65DE6E3CEF438D02D4E51C787242DFDA7FBE",
}

HEX64 = re.compile(r"[0-9a-f]{64}")


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


def check_pins():
    mismatches = []
    for path, expected in PINS.items():
        live = sha256_file(path) if path.is_file() else None
        if live != expected:
            mismatches.append({"path": path.name, "expected": expected, "live": live})
    if mismatches:
        raise SystemExit(f"Frozen source changed; refusing to import: {json.dumps(mismatches)}")
    return {path.name: expected for path, expected in PINS.items()}


def main():
    pins = check_pins()
    spec = importlib.util.spec_from_file_location("pinned_app_supervisor", RUNNER)
    if spec is None or spec.loader is None:
        raise SystemExit("Cannot load the pinned app supervisor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if module.__name__ == "__main__":
        raise SystemExit("Guard failed: the supervisor main would have run")
    for required in ("snapshot", "execute", "load_helper"):
        if not callable(getattr(module, required, None)):
            raise SystemExit(f"Expected frozen function missing: {required}")
    if getattr(module, "run", None) is not None:
        raise SystemExit("Unexpected run() entry point; refusal is safer than guessing")

    source = module.snapshot()
    files = source.get("files")
    if not isinstance(files, list) or not files:
        raise SystemExit("Snapshot returned no file list")
    bad = [item for item in files
           if not isinstance(item, dict) or not HEX64.fullmatch(str(item.get("sha256", "")))
           or not isinstance(item.get("bytes"), int) or not item.get("path")]
    if bad:
        raise SystemExit(f"Snapshot file rows are malformed: {bad[:3]}")

    independent = subprocess.run(["git", "-C", str(CORE), "rev-parse", "HEAD"],
                                 check=True, capture_output=True, text=True,
                                 timeout=10).stdout.strip()
    if independent != source.get("coreHead"):
        raise SystemExit("Snapshot core HEAD disagrees with an independent rev-parse")

    document = {
        "capture": {
            "capturedUtc": utc(),
            "mode": "import pinned run-web-app-window.py and call snapshot() directly",
            "why": ("--snapshot-only prints only the file count. This calls the same "
                    "frozen snapshot() so the per-file hashes are real."),
            "pins": pins,
            "moduleName": module.__name__,
            "mainGuardHeld": module.__name__ != "__main__",
            "helperImported": False,
            "loadHelperCalled": False,
            "runCalled": False,
            "executeCalled": False,
            "processesStarted": ["git -C core rev-parse HEAD"],
            "coreHeadIndependent": independent,
        },
        "coreHead": source["coreHead"],
        "runtimePaths": source.get("runtimePaths"),
        "filesCount": len(files),
        "filesSha256": canonical_sha256(files),
        "files": files,
    }
    target = HERE / "app-full-inputs.json"
    target.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(target), "filesCount": len(files),
                      "filesSha256": document["filesSha256"],
                      "coreHead": document["coreHead"],
                      "sha256": sha256_file(target)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())