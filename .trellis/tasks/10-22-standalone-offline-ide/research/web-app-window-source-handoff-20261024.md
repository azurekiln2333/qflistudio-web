# Full Web application window — source handoff

Status: **SOURCE ONLY / HEAVY EXECUTION UNRUN**, 2026-10-24. This preparation
started no Dart, Flutter, flutter_tester, browser, Nginx, WSL, native build or
device command. It claimed no host slot, accepted no grant, sent no channel
message and made no core/product-source edit, commit or push.

## Boundary and future command

The missing behavior is a complete application check with independent phase
results, frozen input evidence and exact descendant cleanup. This preparation
adds only [run-web-app-window.py](run-web-app-window.py),
[run-web-app-worker.ps1](run-web-app-worker.ps1) and this handoff. Existing
focused/catalog runners and [run-web-owned-window.py](run-web-owned-window.py)
remain unchanged. The supervisor imports the reviewed local Job helper with
its guarded main and verifies this exact helper SHA256 before use:

```text
9df7a94399aae38951337d61693d65de6e3cef438d02d4e51c787242dfda7fbe
```

After root reviews these sources and accepts a **new explicit named 180-second
host handoff**, the command is:

```powershell
python -B -X utf8 .trellis/tasks/10-22-standalone-offline-ide/research/run-web-app-window.py --grant ACTUAL_NEW_HANDOFF --run-name FRESH_NAME --next-owner NAMED_SUCCESSOR
```

Replace all placeholders with that actual handoff, a never-used run directory
name and its one intended successor. Existing evidence directories are refused.
The entry does not acquire a slot or infer a grant from an old channel release.
The worker rejects a standalone invocation without the owned-worker switch.
Commands are fixed; there are no download/install commands or arbitrary command
string arguments. Installed local SDK/Node/Playwright/native inputs are assumed.

The supervisor selects one existing `flutter.bat` application specifically;
generic `flutter` can also match an extensionless shell script on this host.
Python is the actual running `sys.executable`, validated as one existing `.exe`
and rejected if any path segment is `WindowsApps`. The exact absolute paths are
passed as scalar worker arguments, copied into `job.json`/snapshot provenance,
and logged as `ResolvedApplicationPaths` in every phase before `LASTEXITCODE`
is cleared. The worker never repeats a `Get-Command` lookup. This avoids the
observed real-Python-plus-WindowsApps-alias array from `Get-Command python`.

## Phases and evidence

Work is scheduled through 150 seconds, validation cleanup through 170 seconds,
and publisher cleanup through 180 seconds from supervisor start. These are
process scheduling deadlines; synchronous Python hashing and report I/O do not
have a separate hard wall-clock watchdog. Runtime duration and cleanup therefore
still need proof in the first actual granted run.

| Phase | Maximum seconds | Minimum remaining seconds | Fixed check |
| --- | ---: | ---: | --- |
| format | 12 | 12 | `dart format --output=none --set-exit-if-changed` for eleven listed task-owned Dart files |
| tests | 110 | 100 | `flutter test --no-pub --concurrency=1 --timeout 35s --reporter expanded` |
| analysis | 25 | 20 | `flutter analyze --no-pub lib test integration_test tool` |
| content | 6 | 5 | `python -X utf8 scripts/audit_web_content.py --product --report RUN/content-audit.md` |

Each phase starts **UNRUN**. A failed phase does not prevent a later independent
phase when its minimum remaining budget is available and prior Jobs are empty.
Insufficient time leaves that phase UNRUN and makes the overall gate fail. The
phase maxima can exceed the aggregate budget; an overall pass requires all four
actually finish within the shared work window.

Format is a check and requires the complete `11 files (0 changed)` footer.
PowerShell verifies the formatter exists and clears `LASTEXITCODE` immediately
before invocation, so a failed invocation cannot inherit `chcp` success. Tests
require a nonzero executed-test count and the full `All tests passed!` footer;
the passed and skipped counts are recorded. Analysis requires `No issues found`.
Content requires exactly one zero-issue result. Exit 0 alone cannot establish
these results. Skips remain visible limitations in the preserved test log.

This full test suite includes real Nginx and Node/Chromium descendants through
the existing runtime/offline-browser tests. A runtime grant must cover those
host processes. This is separate from the exhaustive 481-item catalog runner,
native module/HAP builds, OHOS/device execution and preview/debugger acceptance.

Every phase and the publisher start suspended in separate private Windows Jobs,
are assigned before resume, and retain exact root handles/creation identities.
A root exit with live descendants is incomplete. Deadline cleanup targets only
the owned Job. Forced cleanup, missing evidence, source drift, publication
failure or any unrun phase cannot produce an overall pass. Unconfirmed cleanup
retains the exact handles in a live supervisor with **HOLD/UNRELEASED**, including
when final report persistence or stdout fails.

## Two-step publication and actual handoff

The contained publisher sends a validation outcome headed
**RELEASE_PENDING_PUBLISHER**, or HOLD when validation cleanup is unconfirmed.
It explicitly says **NO SUCCESSOR GRANT** because that publisher has not yet
terminated. Its intended successor field does not authorize another host run.

After publisher exit 0, terminal root and active-process count zero are
confirmed, final `job.json` and stdout may record **RELEASE**,
`allOwnedJobsEmpty=true`, `terminalConfirmed=true`, `publication.delivered=true`
and `rootRelayRequired=true`. Root must read and relay that completed exact
report as the actual named handoff. A failed publisher with confirmed cleanup
records **RELEASE_PENDING_ROOT_RELAY**, exits unsuccessfully and needs explicit
root relay; an unconfirmed publisher remains HOLD with handles retained. The
on-channel pending message must never be treated as the final handoff.

Each fresh run directory preserves phase stdout/stderr, `job.json`,
`source-before.json`, `source-after.json`, `content-audit.md`, `release.txt` and
publisher stdout/stderr. The first error and all independent phase statuses are
retained. RELEASE describes process cleanup; acceptance additionally requires
all four PASS, stable source inputs, no errors and successful publication.

## Input binding and source validation

The snapshot occurs before format and every other validation. It binds all Web
`lib`, `test`, `integration_test` and `tool` Dart; core `lib`/`vendor` Dart and
core HEAD; effective manifests/config/package configuration; catalog JSON;
script/oracle/curriculum sources; both runner files and the pinned helper;
available Playwright package/browser metadata; the default syntax DLL and any
explicit syntax-library override; and available local/SDK-adjacent Nginx
executables. Resolved Flutter/Node/Python/PowerShell paths and the syntax override
are included as provenance. Before/after differences invalidate frozen-source
acceptance. This does not hash every installed SDK/Node/Chromium executable or
every third-party dependency byte.

The lightweight command reads hashes/core HEAD, checks the helper pin and writes
no reports or Jobs:

```powershell
python -B -X utf8 .trellis/tasks/10-22-standalone-offline-ide/research/run-web-app-window.py --snapshot-only
```

Actual preparation results:

- Python AST and Windows PowerShell parser: PASS.
- Snapshot-only: **327 files**, core HEAD
  `2f9039a3ba95449679b17257b0313c1ee3644a2c`; pinned helper matched.
- Exact preflight selections: Python
  `D:\ProgramFiles\Python\Python313\python.exe`, Flutter
  `D:\ProgramFiles\flutter_ohos\bin\flutter.bat`, Dart
  `D:\ProgramFiles\flutter_ohos\bin\cache\dart-sdk\bin\dart.exe`, PowerShell
  `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`, Node
  `D:\ProgramFiles\nodejs\node.exe`. A fresh after-snapshot re-resolves paths
  so a changed selection invalidates the checkpoint.
- Three path-only executable controls: **3/3**, proving single actual paths,
  WindowsApps Python rejection and no extensionless Flutter fallback. No
  selected SDK/native/browser executable was launched.
- Twelve synthetic success/failure validator controls: **12/12**, covering
  changed/missing format footer, valid/skipped/zero/missing test footer,
  clean/failing analysis and zero/nonzero/duplicate content result. They ran
  only Python in a temporary directory and launched no subprocess or Job.
- Independent read-only source review corrected premature release publication,
  omitted native inputs and stale formatter exit status; re-review found those
  addressed. Actual Job/runtime cleanup remains UNRUN. The reused primitive's
  historical [own-child control](web-owned-job-self-control-20261024.json) is
  separate evidence.

Reviewed source SHA256 values:

```text
d80c46e1b1cf2abe7e7a582e61016ac36266354242de198a5623628659922a19  run-web-app-window.py
074ac02216bab95e8da23d87dca7d1567be5f2fcc4722d43e53d059227fb8b78  run-web-app-worker.ps1
```

A future live-tree result binds whatever shared core WIP exists in that exact
snapshot; it cannot be described as published-core-only acceptance without
separate evidence. This source handoff establishes no new application,
platform, catalog or eleven-product acceptance.
