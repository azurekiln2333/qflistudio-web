# Web app relay window: single-command publication design

Date: 2026-10-26 (Asia/Shanghai). Parent task: `10-22-standalone-offline-ide`.

Current amendment, 2026-10-26: the guarded revision uses
`web-relay-format-app/v1` and requires a new reviewed coordinator event.
The current hashes, exact five formatter paths, pure verification results and
C terminal-observation requirement are recorded in
[the current handoff](web-relay-window-handoff-20261026.md).
Runtime validation remains UNRUN. The disabled revision below is historical.

**Historical state: SOURCE_ONLY_DISABLED.** The wrapper refuses every real run.
`RUN_ENABLED=False`, `main()` exits 3, and `run()` raises before it reads its
arguments. No grant unlocks it. Read
[`web-relay-window-incident-20261026.md`](web-relay-window-incident-20261026.md)
for the unauthorized `C607-NEG` run that must never count as acceptance, and
[`web-relay-window-handoff-20261026.md`](web-relay-window-handoff-20261026.md)
for the open blocker list.

The sections below record the original design review, kept as history. They are
not a description of what the code does now.

Historical method note. That review was read-only over the frozen app runner and
the C606 evidence. No SDK, Flutter, browser, WSL, native or device process was
started. No runner, worker, helper, core, platform or frozen file was changed.
The earlier claim that this file was "the only artifact of this review" is
superseded: the wrapper, the handoff and the incident report now exist.

## Frozen sources under review

```text
d80c46e1b1cf2abe7e7a582e61016ac36266354242de198a5623628659922a19  run-web-app-window.py
074ac02216bab95e8da23d87dca7d1567be5f2fcc4722d43e53d059227fb8b78  run-web-app-worker.ps1
9df7a94399aae38951337d61693d65de6e3cef438d02d4e51c787242dfda7fbe  run-web-owned-window.py (helper)
```

Hashes match `web-app-window-source-handoff-20261024.md`. These three stay frozen.

## 1 Where the C606 budget actually went

| Timestamp (UTC) | Event | Delta |
| --- | --- | --- |
| 18:11:21.370 | supervisor start (ACCEPT applied) | 0 |
| 18:11:21.746 | phase `format` | 0.376 |
| 18:11:22.920 | phase `tests` start | 1.174 |
| 18:13:04.682 | phase `tests` terminal, exit 1 | 101.761 |
| 18:13:13.471 | phases `analysis`, `content` terminal | 8.789 |
| 18:13:13.858 | publisher Job start | 0.387 |
| 18:13:14.442 | publisher terminal, exit 0, `delivered=true` | 0.584 |
| 18:17:54.726 | root relay text written | 280.284 |
| total | ACCEPT to root relay | **393.453** |

Facts from `job.json`. The supervisor finished in **113.072 s** inside its own
180 s budget. It recorded `status=RELEASE`, `allOwnedJobsEmpty=true`,
`terminalConfirmed=true`, `publication.delivered=true`, `rootRelayRequired=true`.
All five roots and the publisher are terminal with `jobActiveProcesses=0`.

So the in-run protocol passed. The window still failed. The 280.284 s gap is the
**root relay authored in a separate model tool round** after the supervisor
already exited. That round is the budget leak, not the runner.

## 2 Root cause and the one hard constraint

The runner cannot author the final handoff. It only publishes
`RELEASE_PENDING_PUBLISHER`, which states "NO SUCCESSOR GRANT". The final relay
text is written by the model after it reads `job.json`. That read-and-write step
costs whole tool rounds, and the window measures ACCEPT to relay, so the runner's
own 113 s is billed against a budget that also has to cover the model.

Constraint the wrapper cannot escape. The runner creates its publisher Job
inside its own process. That Job handle is private. No outside process can query
it. A wrapper in the same application can only observe it **indirectly**, because
the runner runs inside the wrapper's Job. So "publisher Job empty" must be proven
by two independent facts, never by one.

## 3 Proposed wrapper (new file, not written here)

`research/run-web-app-relay-window.py`. Windows-only host supervisor.
It runs the frozen runner as its owned child, then completes the relay itself,
inside one command. It never replaces the runner and never edits it.

Exact single runtime command, fixed placeholders:

```powershell
python -B -X utf8 .trellis/tasks/10-22-standalone-offline-ide/research/run-web-app-relay-window.py --grant ACTUAL_NEW_HANDOFF --run-name FRESH_NAME --next-owner NAMED_SUCCESSOR --window-seconds 180
```

The wrapper must already exist and be reviewed **before** the grant. Runtime has
exactly one model tool round: start it, then read its stdout. Preflight
`run-web-app-window.py --snapshot-only` runs during preparation, never at runtime,
so it cannot consume the window.

## 4 Sequence, all inside the one command

1. Load the pinned helper by SHA256. Refuse any change.
2. Take the frozen runner's own preflight snapshot once, for provenance only.
3. Create one outer `OwnedJob`. Start the frozen runner in it, suspended and
   assigned before resume. Write its stdout and stderr into the fresh evidence
   directory.
4. Poll every 50 ms until the runner root is signalled **and** outer active
   process count is 0, bounded by `window-seconds` minus the relay reserve.
5. Read and parse `job.json`. Require `schemaVersion=1` and the fields in §5.
6. Independently query the outer Job for `activeProcesses == 0`.
7. Compose the relay text deterministically from `job.json`. No model prose.
8. Publish it through the pinned helper `channel_command` inside a second owned
   Job, bounded by the reserve.
9. Confirm the relay Job root signalled, exit code 0 and outer active count 0.
10. Print one final JSON verdict and exit. Root needs no further round.

## 5 Terminal proof, and the live-versus-terminal rule

The wrapper must never call its own exit "outer terminal". Name the states.

- **Wrapper live**: the wrapper process exists or its Job is non-empty. This
  proves nothing about the supervisor. It is not terminal evidence.
- **Supervisor terminal**: the runner's exact root process handle is signalled,
  the outer Job `activeProcesses == 0`, and `job.json` shows
  `terminalConfirmed == true` and `allOwnedJobsEmpty == true`.
- **Publisher terminal**: `job.json` shows `publication.terminalConfirmed == true`,
  the outer Job `activeProcesses == 0` after the relay Job is gone, and the relay
  Job root exit code is 0.
- **Outer terminal**: the wrapper reports a verdict only after supervisor and
  publisher are both proven terminal. Otherwise it reports `HOLD/UNRELEASED`.

Relay rules. Send a `RELEASE` text only when every supervisor and publisher
condition holds. Send a `HOLD` text, or nothing, when cleanup is unconfirmed.
Runner exit 1 with confirmed cleanup is a real result: relay
`RELEASE_PENDING_ROOT_RELAY`, never `RELEASE`. A live wrapper, a started
publisher or a pending channel message is never a substitute for the supervisor's
own terminal record.

On window expiry with the runner still live, the wrapper terminates its own outer
Job (which stops the whole tree), records `forcedCleanup=true` and reports
`HOLD/UNRELEASED`. It must not relay a RELEASE. Preserve the exact creation
identities in the report.

## 6 Relay text, composed from evidence

One fixed template, filled only from `job.json` and the phase logs:

```text
Web <run-name> <status> to <next-owner>. Grant <grant>.
Runner <elapsed>s; phases <name=status,...>.
Terminal: roots <pid/exitCode,...> publisher <pid/exitCode>; outerActive=<n>.
allOwnedJobsEmpty=<bool> terminalConfirmed=<bool> publication.delivered=<bool>.
Source stable=<bool> coreHead=<sha> plus live WIP, not clean-core-only evidence.
Evidence <relative job.json path>.
No catalog/native/WSL/HAP/device extra. No further SDK/browser run until NEW grant.
```

The wrapper substitutes measured values. It must state "plus live WIP, not
clean-core-only evidence" exactly as C606 did, because the snapshot binds the
working tree. Omit no unrun item and invent no pass.

## 7 Budget

Reserve for relay and evidence read: `max(15 s, 10% of window)`.
The runner gets `window - reserve`. With the observed 113.072 s runner, a 180 s
window leaves about 52 s headroom and projects about 118 s total. The projected
gain is the removed 280.284 s model round. If `tests` grows and the runner crosses
`window - reserve`, the wrapper stops it and reports HOLD. That is the honest
failure, not a fabricated pass.

The window is now defined as **wrapper start to relay publish**. The relay
publish timestamp is authoritative for total budget, exactly as the C606 root
text already says.

## 8 What stays open

- The wrapper is designed, not written, not reviewed and not run.
- Actual Job nesting, outer accounting over the runner's inner publisher Job and
  the 50 ms poll cost are unproven on this host.
- The frozen runner's 113 s is one sample with 196 pass and 2 fail. The 2 test
  failures remain a source defect, separate from this window.
- A future fresh grant must accept this improved protocol explicitly. No earlier
  release or pending message authorizes it.

## 9 Status amendment, 2026-10-26

This design is not executable as written. The revision under review sets
`RUN_ENABLED=False` and `EXECUTION_STATE="SOURCE_ONLY_DISABLED"`. `main()` refuses
every real-run argument set and exits 3. `run()` raises before it reads its
arguments. No flag, environment variable or channel input unlocks it.

The authorization-evidence path in §3 is deferred. It must not be built as a
quick flag. It needs its own record format and a non-replay guarantee. Root
generates that record from a real grant that C issues. No user hand-approval is
needed.

An earlier unauthorized run under grant `C607-NEG` is recorded in
[`web-relay-window-incident-20261026.md`](web-relay-window-incident-20261026.md).
Its evidence must never be counted as acceptance.

### Open blockers

1. HOLD keep-alive is unverified on a real Job.
2. Report persistence as a success precondition is unverified.
3. The total-clock check before every launch is untested.
4. Relay and cleanup forced-cleanup aggregation is untested.
5. Authorization evidence is not implemented.
6. Total-budget success is judged before the final report write and stdout. It
   must be judged again after that I/O. Dead run.
7. `reportPersisted` is assigned after the report write, so the persisted file
   lacks the field. Set it before the write. Dead run.

Both items are closed in the current source. See §10.

## 10 Receipt design (Pi, independent)

This section is Pi's own proposal. Root integrates it later and reviews it
separately. It describes the artifact, not an executed protocol.

### Axes

Four independent axes, never collapsed into one verdict:

| Axis | Values |
| --- | --- |
| `gate` | `PASS` / `FAIL` / `INCOMPLETE` |
| `ownership` | `HOLD` / `RELEASE_READY` |
| `publication` | `DELIVERED` / `FAILED` |
| `budget` | `PROVISIONAL_WITHIN` / `PROVISIONAL_LATE` |

`INCOMPLETE` means no child record exists. It is not a failure. `ownership` is
read from the real Job state, so a missing `job.json` never implies live
resources, and a released Job never needs that file.

`RELEASE_READY` may coexist with `gate=FAIL` and `forcedCleanup=true`. A forced
cleanup that empties the real Job is a successful release of resources.

### Receipt file

`<run-name>-relay/wrapper.json`, written twice:

1. Pending: `assessmentPending=true`, `assessment=null`.
2. Final: `assessmentPending=false`, `assessment` holds the four axes,
   `labels` names each dirty axis, `reportPersisted` is true.

The clock is read after write 1 and after the stdout print. That gives a
provisional local budget only. The final write and the process exit sit outside
it, so a margin cannot settle the budget. `observerAuthority=c-coordinator`
judges WITHIN or LATE from the exact wrapper stop moment. `execute()` is
synchronous and has no hard timeout.

### Claim discipline

- The wrapper claims `RELEASE_READY` only, plus `wrapperAlive=true` and
  `formalReleaseClaimed=false`.
- The wrapper never claims an outer terminal, a formal release, or a successor
  grant.
- The wrapper never claims a settled budget. It reports a provisional local value
  and names `observerAuthority=c-coordinator`.
- C observes the exact pid and creation time, confirms both stop, then performs
the formal RELEASE. Only that step may claim `RELEASE`.
- `ownership=HOLD` keeps the process alive and retains the handles.

### What this receipt does not prove

No live run exists behind it. The axes, the keep-alive, the margin and the
formal-release handoff are source-only and covered by pure controls.