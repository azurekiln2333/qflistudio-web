# Quality Guidelines

> Quality standards for `qfli_web` runtime and native work. Verification must be
> based on a real engine, not a mock channel or a filename.

---

## Required Checks

Run these before reporting a task complete (the `--no-pub` flag avoids a network
resolve and is the test convention; release mode transitions require pub-enabled
builds as described in [Release Verification](./release-verification.md)):

```bash
flutter analyze --no-pub lib test
flutter test --no-pub --concurrency=1 test/<affected>_test.dart
```

Native/device claims need their own evidence — see
[Web Runtime](./web-runtime.md) and
`.trellis/spec/backend/native-runtime.md`.

## Quality Expectations

- **Behavior tests over unit assertions.** Serve over a real loopback
  `HttpClient`, assert status and body, and check post-stop connection refusal.
  See `test/web_dev_server_test.dart` and `test/nginx_session_test.dart`.
- **One shared HTTP helper.** Reuse `request(...)` from
  `test/web_dev_server_test.dart` (`import 'web_dev_server_test.dart' show
  request;`) instead of copying a client into each file.
- **Every started session is stopped in teardown.** Use
  `addTearDown(server.stop)` even when the test stops it explicitly, so an
  assertion failure cannot leak a listener.
- **Unavailable platforms are recorded, never faked.** The application smoke
  fails on Android/OHOS/iOS when the required packaged engine is unavailable.
  An unsupported desktop host may record a visible skip (`markTestSkipped`).
  Missing device/signing/build environments remain explicit limits, never passes.

## Forbidden Patterns

- Labelling the Dart middleware as "Nginx". Advertise Nginx only when a real
  upstream `nginx` binary or embedded library is packaged, started and stopped.
- A second preview listener: the editor already owns one via
  `webProfile.webPreviewFactory`; do not also start one through
  `RunnerService.runProject`.
- Manual URL percent-encoding by string concatenation for the preview resolver;
  build the URL through `Uri`/`Uri.parse` (see the current-file preview contract
  in `test/web_preview_current_file_test.dart`).
- Loosening `WebProjectConfig.parse` to accept an invalid config at save time.
- Test-only hooks added to production code paths.

## Code Review Checklist

- Does the change keep exactly one public preview endpoint per run, and does it
  stop on editor exit?
- Are traversal, hidden-file and symlink-escape requests still rejected?
- Does an explicit engine selection still fail loudly instead of substituting?
- For native changes: is the ELF for the right ABI, and are build/bundle hashes
  updated (`vendor/nginx/HASHES.sha256`, `SOURCE.json`)?
- Do new tests assert real HTTP/engine behavior, not just that a URL string was
  produced?

## Bounded Windows host verification

### Scope / Trigger

Use for coordinated Flutter/Chromium checks that must release the shared host
even when a test or its teardown hangs.

### Signatures

Use a fresh coordinated grant with the task's `research/run-web-app-window.py
--grant ACTUAL_HANDOFF --run-name FRESH_NAME --next-owner NAMED_SUCCESSOR` for
the full app gate. Its `--snapshot-only` reads inputs without starting a Job or
SDK. The catalog entry is `research/run-web-catalog-window.py` with the same
grant/name/successor arguments and `--viewport desktop|mobile`; each viewport
requires a separate grant. The PowerShell app file is an owned worker only.
Native-only compilation uses `research/run-web-native-window.py` with the same
grant/name/successor arguments, or `--snapshot-only` for lightweight preparation.
It runs only the CDP target/readelf for two sequential ABIs,150/170/180seconds,
with no new phase at/after140seconds. Linux/WSL, OHPM/Hvigor/HAP and device work
each require their own separately coordinated gate.

The earlier `run-web-owned-window.py` remains the pinned local Job primitive
and historical focused-run evidence. Do not replay its consumed grants or use
its older publication sequence for a new app/catalog window.

### Contracts

Create the worker suspended, assign it to a private Windows Job without
breakaway, then resume. Retain the exact process handle and creation time.
Use the entry's agreed schedule: app150/170/180seconds for work/cleanup/total;
catalog300/320/330seconds for one viewport. Synchronous snapshot/report I/O is
not a hard wall-clock watchdog; record actual elapsed time. Kill only the owned
Job. Preserve each run's logs and raw input hashes.

Resolve one actual executable before launch: Python uses `sys.executable`,
Flutter uses one existing absolute `flutter.bat`, and the worker receives those
literal paths. Refuse WindowsApps Python aliases. Do not pass
`(Get-Command python).Source` as one executable: this host returns both the real
interpreter and an alias. Log the chosen paths, clear `LASTEXITCODE` immediately
before the native invocation and require a nonnull exit afterward. A stale
success from encoding/path preparation cannot establish a phase pass.

The contained publisher sends `RELEASE_PENDING_PUBLISHER` and explicit
`NO SUCCESSOR GRANT`; validation Jobs being empty does not prove publisher
cleanup. Only after all validation and publisher roots are terminal/active0
can final evidence record `RELEASE`, `terminalConfirmed=true`,
`allOwnedJobsEmpty=true` and delivered publication. Root reads that final
checkpoint and relays the named successor handoff. A failed publisher requires
explicit root relay after confirmed cleanup; unconfirmed cleanup stays
`HOLD/UNRELEASED` with exact handles retained, even if report/stdout I/O fails.
Release describes cleanup; acceptance also requires every phase PASS and
unchanged frozen inputs. The new app/catalog/native entries remain source-only until
their own actual named executions prove these paths.

### Validation / Error Matrix

| Condition | Required result |
| --- | --- |
| Root exits while a child remains | Job remains nonempty; no RELEASE yet |
| Execution deadline | Terminate owned Job; exit124 is incomplete evidence |
| Worker result missing/malformed | Record error/incomplete result; still clean up and publish |
| Channel send fails | Report failed delivery for explicit relay; no successful wrapper result |
| Input hash changes | Checkpoint is unstable; no frozen-source pass |
| Publisher notification arrives before publisher exit | Pending only; successor must not start |
| Multiple executable candidates or WindowsApps Python alias | Reject/select one actual file before launch; never stringify the array |
| Native invocation has no exit code | Phase fails; do not inherit an earlier command's success |
| Report/stdout fails while a Job remains unconfirmed | Retain owned handles in the live supervisor; no successor grant |

### Good / Base / Bad Cases

Good: normal completion and an empty Job followed by a terminal successful
publication followed by a root relay. Base: formatter/test/analyzer codes remain
separate. Bad: a killed worker's unfinished analyzer is reported as green, only
its PID is checked, or a pending publisher message is treated as a grant.

### Tests Required

The lightweight self-control starts a Python root that leaves a live child.
Assert root termination alone leaves the Job nonempty, then owned cleanup makes
it empty. `web-owned-job-self-control-20261024.json` records that actual check.
Run the PowerShell snapshot preflight under the same `-NoProfile` launch.
Compute SHA256 through .NET streams so missing `Get-FileHash` cannot prevent
the test from starting. Keep explicit UTF8 console encoding.
Verify single-path resolution with the installed aliases present and reject
alias-only Python, absent Flutter batch files and stale/null native exits.
Source/synthetic checks establish no runtime Job, full-suite or browser pass.

### Wrong vs Correct

Wrong: kill Node, observe its exit, and assume Chromium is gone. Correct:
contain the complete descendant tree before the root runs and verify the
private Job's active-process count before announcing RELEASE.

Wrong: publish RELEASE from inside the publisher that is still running.
Correct: publish pending/no-grant, then let root relay the completed evidence
after that publisher itself exits and its owned Job is empty.
