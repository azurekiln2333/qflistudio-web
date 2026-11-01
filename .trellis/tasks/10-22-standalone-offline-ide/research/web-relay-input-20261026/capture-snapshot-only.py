"""Capture the frozen runners' read-only snapshot commands for one readiness input.

This script is evidence tooling for the readiness input snapshot. It runs only the
commands each runner documents as starting nothing:

  run-web-relay-window.py            no arguments -> snapshot() and return
  run-web-app-window.py              --snapshot-only
  run-web-native-window.py           --snapshot-only
  run-web-ohpm-window.py             --snapshot-only

Every argument list is a fixed literal. Any list containing an execution flag, a
grant, a run name or a successor name is refused before a child starts. The script
never imports a runner, never opens a channel and never touches product or core.

Run: python -B -X utf8 capture-snapshot-only.py
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parent
ROOT = RESEARCH.parents[3]

FORBIDDEN = ("--execute-reviewed", "--grant", "--run-name", "--next-owner",
             "--authorization", "--reviewed-raw-sha256", "--run")

COMMANDS = (
    ("relay-window-default", "run-web-relay-window.py", []),
    ("app-window-snapshot-only", "run-web-app-window.py", ["--snapshot-only"]),
    ("native-window-snapshot-only", "run-web-native-window.py", ["--snapshot-only"]),
    ("ohpm-window-snapshot-only", "run-web-ohpm-window.py", ["--snapshot-only"]),
)


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest().upper()


def guard(extra):
    hits = [flag for flag in FORBIDDEN if flag in extra]
    if hits:
        raise SystemExit(f"Refused execution argument(s): {hits}")


def main():
    captures = {"capturedUtc": utc(), "python": sys.executable,
                "root": str(ROOT), "commands": []}
    for name, script, extra in COMMANDS:
        guard(extra)
        script_path = RESEARCH / script
        command = [sys.executable, "-B", "-X", "utf8", str(script_path), *extra]
        record = {"name": name, "script": script, "arguments": extra,
                  "scriptSha256": sha256_bytes(script_path.read_bytes()),
                  "command": ["python", "-B", "-X", "utf8", script, *extra]}
        try:
            done = subprocess.run(command, cwd=str(ROOT), capture_output=True, timeout=900)
        except BaseException as exc:  # Record the refusal instead of raising.
            record.update(exitCode=None, error=f"{type(exc).__name__}: {exc}")
            captures["commands"].append(record)
            continue
        out, err = done.stdout, done.stderr
        (HERE / f"{name}.stdout.json").write_bytes(out)
        (HERE / f"{name}.stderr.txt").write_bytes(err)
        record.update(exitCode=done.returncode, stdoutBytes=len(out),
                      stdoutSha256=sha256_bytes(out), stderrBytes=len(err),
                      stderrSha256=sha256_bytes(err))
        captures["commands"].append(record)
    (HERE / "captures.json").write_text(
        json.dumps(captures, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({c["name"]: c.get("exitCode") for c in captures["commands"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
