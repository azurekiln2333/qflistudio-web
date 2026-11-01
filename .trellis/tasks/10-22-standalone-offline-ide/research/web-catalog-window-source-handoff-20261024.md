# Bounded single-viewport catalog runner — source handoff

Status: **SOURCE ONLY / UNRUN**, 2026-10-24. No browser, Node, Flutter, native,
WSL or device process was started for this preparation. This does not establish
new catalog, platform or eleven-product acceptance.

An independent [read-only validator control](web-catalog-validator-controls-20261024.json)
later accepted the historical report's schema using its own historical hashes,
then rejected a wrong viewport, a stale catalog hash and a full report presented
as the partial controls phase. This executes only Python report validation;
the new supervisor and current browser catalog remain unrun.

## Boundary and command

The missing behavior is a bounded, explicit-handoff supervisor for the existing
production semantic runner. Only [run-web-catalog-window.py](run-web-catalog-window.py)
and this handoff were added. Catalogs, oracles, shared core and the existing Job
helper are unchanged. The new entry imports that same-repository reviewed helper
through `importlib`; its `main` is guarded and its exact SHA256 is pinned in the
new entry. Helper drift rejects execution rather than silently trusting a new
process primitive.

After an actual **new named330s host handoff** is accepted, one viewport runs as:

```powershell
python -X utf8 .trellis/tasks/10-22-standalone-offline-ide/research/run-web-catalog-window.py --grant ACTUAL_HANDOFF --run-name FRESH_NAME --next-owner NAMED_SUCCESSOR --viewport desktop
```

Use `--viewport mobile` in a separate named window. Desktop is1280x720, mobile
390x844. This script neither acquires a slot nor installs/downloads dependencies.
An existing run directory is rejected before old evidence is touched. Run names
permit only letters, digits, underscore and hyphen.

## Phases and result contract

The window allows300s work, cleanup through320s and bounded publication through
330s. First it invokes `scripts/run_examples.mjs` with the production oracles
filtered to exact JS052/JS053. That control is explicitly partial. It starts the
full481 pass only after the controls pass and at least270s work budget remains;
historical full runs took about241s. A control failure or insufficient time
leaves full **UNRUN**, rather than knowingly starting a doomed deadline run.

Each Node root is created suspended, assigned to an owned Windows Job before
resume, and observed through the exact handle/creation record. A terminal root
with descendants cannot release: the supervisor waits for the Job to drain
within the phase deadline. Remaining descendants at that deadline require
own-Job cleanup and make the phase fail even when the root itself exited0.
No foreign process, device, daemon or forward is touched. The contained
publisher sends only **RELEASE_PENDING_PUBLISHER** when validation Jobs are
empty, or **HOLD/UNRELEASED** when cleanup is unconfirmed, plus the validation-
terminal/empty state and an explicit **NO successor grant**. Its notification directs
root to verify the completed checkpoint; the recipient must not accept that
pending message as a host handoff.

Only after every owned Job, including the publisher, is terminal/active0 and the
publisher exits0 does final `job.json`/stdout record `status=RELEASE` and
`delivered=true`. `rootRelayRequired=true` and `successorGrantIssued=false`
remain explicit: root relays that completed checkpoint as the actual named
handoff. There is no recursive publication acknowledgement. A terminal failed
publisher leaves **WITHHELD**; unconfirmed cleanup leaves **HOLD/UNRELEASED** and
retains exact Job handles in a live supervisor, including when report persistence
or stdout raises. Pending-message I/O is guarded by the publisher failure path.
Neither state grants a successor.
This closes the race where an early RELEASE message could be followed by a
residual publisher Job. Test success and safe host release remain separate.

The report validator requires current host-Chromium runtime, the requested
viewport, both raw catalog SHA256 values,481 unique current source IDs and
481 lessons, exact selected result IDs, zero mapping issues/failures/external
requests, nonempty passing semantic assertions, and `complete=true` only for
the full phase. A terminal process exit0 alone is insufficient. Malformed or
missing browser JSON is a recorded failure, and still enters cleanup/publication.

Every fresh run directory owns its per-phase stdout/stderr, Markdown/JSON
browser reports, `job.json`, source manifests and release/publisher evidence.
The first error and independent phase statuses are preserved. Raw before/after
hashes bind all content JSON, all root `scripts/*.mjs`, curriculum Python,
emitter/audit/test-emitter Python, root package manifests/locks, available local
Playwright package manifests, this runner and the reviewed helper. Input drift
invalidates the checkpoint. Interpreter provenance uses actual `sys.executable`;
Node uses one scalar `shutil.which('node.exe')` result, not PowerShell command
aliases/arrays. Both must resolve to existing executable files outside WindowsApps.
Their exact paths, sizes and raw SHA256 are compared before/after; the fixed
resolved Node path launches both browser phases. Provenance drift fails the
checkpoint. Browser executable bytes are not pinned; actual browser version
comes from each executed report.

## Verification still required

Python AST parsing, source/whitespace checks and the helper-pin comparison
passed; manual cleanup/report-flow review was source-only. No new executable
Job control or browser pass is claimed here. The reused primitive's historical own-child Job control
remains separate evidence in [web-owned-job-self-control-20261024.json](web-owned-job-self-control-20261024.json).
Before adopting this entry, root should independently review deadline/exception/
publisher paths; then its actual named run must prove terminal cleanup, exact
current reports and source stability. Each full481 viewport, current OHOS
catalog, native module/HAP and owned-preview/debugger proof remains separate.
