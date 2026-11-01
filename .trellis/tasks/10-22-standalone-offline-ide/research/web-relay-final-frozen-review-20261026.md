# Final frozen review: `run-web-relay-window.py`

Date: 2026-10-26. Reviewer: Pi. Mode: read-only.

Reviewed artifact:

```text
aafaa64435d551c65b05858d46bb06449a03d6d3a9293033575c3b6a47f2d5d9  run-web-relay-window.py
59058 bytes, 1169 lines
```

The SHA256 was re-computed from disk before reading and matched the requested
value. No runner, worker, helper, SDK, Flutter, browser, nginx, WSL or device
process was started. No `--self-test` run was performed in this review. No code
was changed. Every statement below comes from reading source and from
`Get-FileHash` / `Select-String` against the frozen file and its frozen inputs.

## Verdict

| # | Check | Result |
| --- | --- | --- |
| 1 | Cleanup `HOLD` / `RELEASE_READY` | Pass, with one residual fragility (F3) |
| 2 | Phase registered early | Pass |
| 3 | Formatter deadline relative to phase start | Pass |
| 4 | Exactly five formatter files | Pass, with a stated limit (F8) |
| 5 | Report refresh | Pass, with one residual (F4) |
| 6 | Handle retention | Pass |

No check failed. Six residual findings are listed at the end. None of them
requires a live run to describe; all six are source-visible.

## 1 Cleanup `HOLD` versus `RELEASE_READY`

`wrapper_cleanup` (388) returns `confirmed`, and `run()` maps that to the
ownership axis through `released_resources` (312) and `ownership_state` (325):

- `released_resources` = `cleanup_confirmed is True and not held and all(created_job_gone(p) for p in phases)`.
- `ownership_state` = `RELEASE_READY` only when that is exactly `True`, else `HOLD`.

The pairing with process lifetime is consistent:

- `cleanup_confirmed` false means at least one Job was not confirmed empty, which
  in turn means `held` is non-empty, because `wrapper_cleanup` removes a Job from
  `held` only inside the `if empty:` branch (409).
- `run()` then enters `while True: time.sleep(0.5)` (769). So `HOLD` never exits
  and never silently drops a handle.
- `HOLD` cannot be reached with `cleanup_confirmed` true in practice: a phase
  counts as having created a Job only when its `root` carries a `pid`, and the
  frozen `OwnedJob.empty()` (frozen helper, 105-115) is the only writer of
  `terminal` / `jobActiveProcesses`.

`gate` failure and `RELEASE_READY` remain independent: `final_ok` (766) requires
`gate == "PASS"`, but `ownership` is computed from `released_resources` alone, so
`gate=FAIL` with `ownership=RELEASE_READY` is representable and is asserted by the
pure controls.

## 2 Phase registered early

The four phase dicts are created at 566-569 and registered into the report at
570-571, before the `try` at 578:

```python
report.update(accept=accept_phase, sourceFormat=source_format_phase,
              supervisor=supervisor_phase, relay=relay_phase)
```

This closes the earlier defect where a raised `frozen.execute` left
`report["sourceFormat"]` absent. Because the report holds the same dict objects,
`wrapper_cleanup`'s back-fill (401-406: `phase["root"] = dict(job.record)`,
`phase["terminalConfirmed"] = empty`) is always serialized, including on the
exception path.

The later re-bindings (`report["accept"] = accept_phase` at 595, and the
equivalents for the other three phases) are redundant. Harmless, see F5.

## 3 Formatter deadline relative to phase start

At 602:

```python
source_format_deadline = min(time.monotonic() + 15, supervisor_deadline - 5)
```

and the hard window at 612:

```python
min(source_format_deadline + 5, total_deadline)
```

Both are now anchored to the moment the phase may start, not to wrapper entry.
The earlier form used `started + 20` / `started + 25`, which silently shortened
the phase by however long ACCEPT took, up to its 8 s allowance. That defect is
closed. The phase is also clamped to five seconds before the supervisor
deadline, so it cannot consume the launch margin.

Note: 15 s is a chosen constant with no measurement behind it. It is recorded as
a choice, not as a measured budget.

## 4 Exactly five formatter files

`FORMAT_FILES` (53-59) holds exactly five paths. The same tuple is used in four
places and nowhere else:

- `dart format` arguments (610-611),
- `sourceFormatBefore` (597-598),
- `sourceFormatAfter` (615-616),
- `sourceFormatChanged` (617-619).

All five files exist on disk; none can raise `FileNotFoundError` during the
before/after hashing. `dart format` receives explicit file arguments, never a
directory, so it cannot rewrite an unlisted file. See F8 for the limit of this
guarantee.

## 5 Report refresh

Two writes, both through `persist` (372), which sets `reportPersisted` immediately
before each write so the flag never contradicts the bytes on disk:

1. Write 1 (733) after `report.update(...)` at 690-700, which carries
   `cleanupConfirmed`, `cleanupJobs`, `resourcesReleased`, `handlesRetained`,
   `deadline` and the back-filled phase records.
2. Write 2 (756) after the assessment and the post-I/O clock read at 743.

The assessment is computed from the clock read after write 1 and after the stdout
print, and it stays provisional (`budgetAuthority="provisional"`,
`budgetObserverAuthority="c-coordinator"`, 748-750). Nothing is reported after
write 2, so file and exit code cannot disagree. See F4 for the one exception.

## 6 Handle retention

`wrapper_cleanup` (388-421) records, per Job, the Job handle, the process handle,
the resolved phase name, the final `root` record, `terminalAndEmpty` and
`handlesClosed`. `job.close()` is called only inside `if empty:`. A non-empty Job
is left open, `confirmed` becomes false, and the failure text names the phase
(`f"{item['phase']}: Job still active; handles retained"`, 415). The retained
handle is therefore still valid and still named at the moment C observes it.

The pre-`try` construction of `item` uses `str(job.job)` and `str(job.process)`.
Those attributes exist on the frozen `OwnedJob` (frozen helper 59, 86, 87), so
this does not fail. See F3 for why the placement still matters.

## Residual findings

Severity is about evidence honesty, not about live risk.

### F1 (medium) `snapshot()` still claims `runReachable: false`

At 486 the snapshot emits `"runReachable": False`, while 487 emits
`"reviewedExecutionAvailable": RUN_ENABLED`, and `RUN_ENABLED` is now `True` (50).
The real run path is reachable behind the reviewed gate, so `runReachable: false`
is no longer true. Fix: drop the field, or make it
`runReachable=RUN_ENABLED and explicit flag and receipt gate`.

### F2 (medium) No pure control covers the live authorization path

`reviewed_authorization` (149) is the only authorization path: `run()` calls it
with `consume=True` (534), `main()` with `consume=False` (1154). The 144
`case(...)` controls contain no case that exercises `validate_receipt`,
`decide_execution` or `EXECUTE_FLAG`. The previously dead `load_authorization`
and `authorization_replayed` are gone, which is correct, but their controls were
removed with them and nothing replaced the coverage. The gate that now decides
every real run is untested, even purely.

### F3 (low-medium) Cleanup record construction sits outside its own guard

`wrapper_cleanup` builds `item` before the `try` (396-397). If that construction
raised, the exception would leave `wrapper_cleanup`, escape the `finally`, and
skip both the `HOLD` refresh and the `while True` keepalive. The attributes do
exist today, so this is latent rather than active. Fix: move the `item` build
inside the `try`.

### F4 (low) One error can miss the last write

At 758-760, a failed write 2 appends to `report["errors"]` after the last
persist. The persisted file therefore lacks that single error, while the exit code
is still non-zero. This is an accepted tradeoff, recorded so it is not mistaken
for a bug later.

### F5 (info) Redundant phase re-binding

The four `report["<phase>"] = <phase>` assignments after the early registration
are no-ops. They are harmless, but they invite a future edit that reorders them
and silently reintroduces the defect closed in §2.

### F6 (info) `RUN_ENABLED` is now `True`

The hard `SOURCE_ONLY_DISABLED` kill switch is gone by design. Default denial now
rests entirely on `--execute-reviewed` plus the receipt plus the root raw pin.
There is no longer a single boolean that disables execution outright. This matches
the agreed protocol and is recorded as a deliberate change of posture.

### F7 (info) Receipt is validated twice

`main()` validates with `consume=False` (1154) and `run()` validates again with
`consume=True` (534). The pre-flight result is discarded, so it guarantees
nothing about the second call, and the receipt file is read twice with a window
between the reads.

### F8 (info) `sourceFormatChanged` is scoped, not exhaustive

`sourceFormatChanged` (617) compares only the five listed files, so it is
`⊆ FORMAT_FILES` by construction. It proves that no listed file changed outside
the grant, and it cannot prove anything about unlisted files. The guarantee rests
on `dart format` being given explicit file arguments, not on the comparison.

## What this review does not claim

- No live run happened, so no axis value, no `HOLD` behaviour and no
  `RELEASE_READY` handoff is verified against a real Job.
- The 144 pure controls were not executed in this review and their pass count is
  not re-asserted here.
- The five formatter files were not formatted and their current contents were not
  judged.
- `web_relay_authorization.py` was pinned to
  `ee4d251a494772ec607c990a35abca538c07a3b7801863c23ad7dd3e320915e9` (60) and that
  constant was compared against the module on disk here: the module hashes to
  `ee4d251a494772ec607c990a35abca538c07a3b7801863c23ad7dd3e320915e9` (29293 bytes),
  so the pin holds. The three frozen inputs also re-hashed to `d80c46e1…` (runner),
  `074ac022…` (worker) and `9df7a943…` (helper).

## Conclusion

`aafaa644` closes the two high findings from the previous review: phase records
now survive a raised `execute`, and the formatter deadline is relative to phase
start. Cleanup, ownership, report refresh and handle retention are coherent with
the agreed protocol: the wrapper publishes `RELEASE_READY` only, names the
handles it still holds, keeps the process alive while it holds any, and leaves the
formal release to C after external observation.

The remaining gaps are evidential. F1 is a false field in the snapshot. F2 means
the authorization gate itself has no pure control. F3 is a latent ordering
fragility in the cleanup record. None of the three blocks a reviewed decision to
run, but all three should be named in that decision rather than assumed closed.

## Post-freeze amendment

A later revision changed the wrapper again. This section records the difference
against the reviewed artifact, without re-reviewing the whole file.

### New artifact

```text
401f61d44495dd0a8b681a25746263e589203a9555f30c49106eca791db0fdb3  run-web-relay-window.py
60258 bytes, 1169 lines
```

The SHA256 and byte count were measured from disk. The reviewed artifact was
`aafaa644…`, 59058 bytes, 1169 lines.

The intermediate value `338d31ce…`, named as the pin-only revision, was never
observed on disk. By the time the wrapper was hashed it had already advanced to
`401f61d4…`. So this amendment compares `aafaa644…` directly against `401f61d4…`,
and the difference it proves contains both the pin update and the F1 rewrite at
once.

### The three differences

1. Validator pin. `AUTHORIZATION_SHA256` moved from `ee4d251a…` to
   `84445442fed9b9382555e02b8812c6321cbd7c7ec5026ff13904c5f5897a1de4` (line 60).
   The module on disk now hashes to exactly that value (30119 bytes), so the pin
   and the module agree. A 64-character hex value replaced a 64-character hex
   value, so this change is length-neutral.
2. F1 closed. The snapshot field at 486 is now
   `"runReachableWithReviewedAuthorization": RUN_ENABLED`. The old
   `"runReachable": False` is gone, so the snapshot no longer denies that a
   reviewed run is possible.
3. Line endings normalised. The file is now entirely CRLF: 1169 CRLF and 0 bare
   LF. The reviewed artifact was LF.

### Why no fourth difference can be hiding

The byte delta is fully accounted for:

```text
       59058  reviewed artifact
     +  1169  one carriage return per line terminator
     +    31  the snapshot field rewrite (30 chars -> 61 chars on that line)
     = 60258  current artifact, exactly
```

The identity is exact, not approximate, and the line count is unchanged at 1169
with every `def` still on its reviewed line number. Any further edit, however
small, would break the total. So the difference is confined to the pin value, the
snapshot field and the encoding. No logic moved.

One cosmetic consequence: `snapshot()` now reports the same fact twice, at 486
(`runReachableWithReviewedAuthorization`) and 487 (`reviewedExecutionAvailable`).
Harmless, but one of the two could be dropped later.

### Finding status after the amendment

| Finding | Status |
| --- | --- |
| F1 snapshot denied a reviewed run | Closed by the field rewrite above |
| F2 authorization gate had no test coverage | Closed by the three test files below |
| F3 cleanup record built outside its guard | Residual only. The frozen `OwnedJob` exposes `.job`, `.process`, `.record`, `.empty()`, `.stop()` and `.close()`, so the construction cannot fail today. The ordering is still worth tightening. |

### F2 coverage, counted statically

| File | `def test_` | Size | SHA256 |
| --- | ---: | ---: | --- |
| `test_web_relay_guard.py` | 4 | 3423 | `470f29517d83eef24309438774a986c4bc9282ee87100e93ade1732e464a771c` |
| `test_web_relay_authorization.py` | 79 | 31765 | `95ee470e83c355953a56f2f6fa5f847f15723d05816402bbaaa9d59c8a569a0f` |
| `test_web_relay_cleanup.py` | 13 | 9286 | `c81e0e86ab56b63f5344306660344df266bd3597f551b58894dd7cff279e17f1` |

The counts match the claim: four guard tests, seventy-nine authorization tests,
thirteen cleanup tests. The wrapper's own `--self-test` surface is unchanged at
144 `case(...)` entries.

Note on where the count lives: the authorization module's embedded `self_test`
contains 17 literal `case(...)` calls, not 79. The 79 comes from the dedicated
`test_web_relay_authorization.py`. Both numbers are correct for their own file.

### What this amendment does not claim

The three test files were counted by reading their `def test_` lines. They were
not executed, so their pass state is not asserted here. The wrapper's own
`--self-test` was not executed either. No SDK, runner, helper or Job was started,
and no formatter was run. This amendment confirms identity and difference; it does
not add a verdict on behaviour.

With F1, F2 and F3 resolved to the extent above, the six checks in the main body
stand unchanged, and nothing in the reviewed logic moved between `aafaa644` and
`401f61d4`.
