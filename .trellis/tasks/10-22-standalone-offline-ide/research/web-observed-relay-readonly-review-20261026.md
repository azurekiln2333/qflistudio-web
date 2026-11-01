# Read-only review: `run-web-observed-relay-window.py`

Date: 2026-10-26. Author: Pi. Mode: read-only. No SDK, test, Job, launcher,
browser or channel command was started. No file was modified.

Reviewed artifact, hash confirmed byte-for-byte against the supplied value:

| File | Size | SHA256 |
| --- | ---: | --- |
| `research/run-web-observed-relay-window.py` | 22728 | `532839ab788f5abaebe22733cdb89b63f955d28f2abd2270330b00cc5c24e8dc` |
| `research/test_web_observed_relay_window.py` | 18617 | 30 `def test_` declarations, counted statically |
| `research/run-web-relay-window.py` (frozen) | 60258 | `401f61d44495dd0a8b681a25746263e589203a9555f30c49106eca791db0fdb3` |
| `research/web_relay_authorization.py` | 30119 | `84445442fed9b9382555e02b8812c6321cbd7c7ec5026ff13904c5f5897a1de4` |

The three frozen wrappers are unchanged: `run-web-app-window.py`
`d80c46e1…` (17492), `run-web-app-worker.ps1` `074ac022…` (3814),
`run-web-owned-window.py` `9df7a943…` (12228).

## 1 Findings, classified

Classification rule: an **actual blocker** is a defect present in these bytes that
can produce a wrong durable claim or a wrong terminal state on a reachable path. A
**latent defect** is wrong in code but needs an abnormal path to fire. A
**hypothetical followup** is a robustness or consistency improvement with no current
wrong outcome.

| ID | Kind | Subject | Lines |
| --- | --- | --- | --- |
| B1 | **actual blocker** | control-plane boundary asserted, never verified | `:307`, `:443`, `:179-188` |
| B2 | **actual blocker** | observer approval is substring containment | `:186` |
| B3 | **latent defect** | publisher stop authority uses two different clocks | `:339-341`, `:380-381`, `:396-399` |
| R1 | hypothetical followup | a never-started Job is labelled `TERMINAL` | `:113-114`, `:131-140` |
| R2 | hypothetical followup | `finally` picks the phase by flag, not by Job identity | `:397` |
| R3 | hypothetical followup | `final-sender.json` written before the `finally` re-observation | `:385-388`, `:393-399` |
| R4 | hypothetical followup | `mkdir` and frozen imports sit outside `run()`'s `try` | `:292-295` |
| R5 | hypothetical followup | `inspect_reports` omits `c["runName"]` | `:264` |

The author (`web_terminal_observer`) is fixing B1 and B3. B2 is reported because
the requirement is explicit acceptance; it has the same shape as the frozen
wrapper's own approval path and may be a deliberate design choice.

### B1. The control-plane boundary is asserted, never verified

Requirement: the parent control Job may be created before the wrapper consumes
its marker, and that infrastructure boundary **must be explicitly granted**.

The report states it as fact:

- `:307` `"controlJobBeforeConsumptionExplicitlyGranted": True`
- `:443` `"controlInfrastructureBeforeWrapperConsumptionRequiresExplicitGrant": True`

Both are literals. Nothing in the file reads the grant to confirm the boundary was
granted. `observer_approval` (`:179-187`) checks exactly two things in the prose:
the protocol string and the observer hash. It does not look for any control-boundary
token, and no other function does either (the only occurrences of the concept are
the docstring at `:8-13`, the two constants above, and the printed snapshot).

The frozen validator cannot cover this gap either: `web_relay_authorization.py:187`
documents that the raw record's `text` is "stored, never parsed", and it only
requires `text`/`ts`/`kind` to be present (`:198`). So a grant that names
`web-observed-relay/v1` and the observer hash, but is silent about the parent
creating a control Job before the marker is consumed, is accepted, and the durable
report then claims the boundary was explicitly granted.

That is the "shape is not authority" failure the earlier protocol work was meant to
remove: a constant `True` standing in for evidence. It is the one place where this
file claims an authorization it does not check.

Concrete shape of a fix, for p3 to judge: require a third prose marker in
`observer_approval` (for example a fixed token such as
`control-job-before-consumption`), refuse when absent, and set the report field
from that check rather than from a literal.

### B2. Observer approval is substring containment, so mention is not acceptance

`:186`:

```python
if not isinstance(text, str) or PROTOCOL not in text or own_sha not in text:
    return "Fresh actual grant must explicitly name observer protocol and exact hash"
```

`in` is substring containment. A grant whose text reads
`do not accept web-observed-relay/v1 532839ab…` satisfies both tests and is
approved. The requirement is that C **explicitly accepts** the protocol and the
hash.

This matters more here than it would elsewhere, because this is the only gate on
observer authorization. The frozen validator deliberately does not parse prose
(`web_relay_authorization.py:187`), and the wrapper's own `reviewed_authorization`
(`run-web-relay-window.py:149-187`) checks the *structured* `protocol` field
(`web_relay_authorization.py:174`, `EXPECTED_PROTOCOL = "web-relay-format-app/v1"`),
not the text. So the observer's substring test is the sole prose gate in the chain.

Note this is not a regression introduced here: the frozen wrapper's own approval
path has the same shape. It is reported because the requirement for this run is
explicit acceptance, and mention is weaker than acceptance.

### B3. The publisher's stop authority uses two different clocks

Current behaviour, in three separate places:

- `:380-381` the final sender is admitted with **no budget check at all**:
  `owned_command(helper.channel_command(...), "final-sender", publisher, is_publisher=True)`
  runs whether or not `time.monotonic() >= deadline`.
- `:339-341` its own observation window is a fresh publisher clock:
  `time.monotonic() + PUBLISH_SECONDS if is_publisher else deadline`.
- `:396-399` any still-held Job re-observed in `finally` is passed the **parent**
  `deadline`, and `publisher=phase is publisher` decides whether `stop()` is
  allowed. `observe_owned` computes `late = clock() >= deadline` (`:114`) and stops
  the publisher on the first late pass (`:155`).

So the same publisher can be "within its own 8 s window" during its own observation
and "late" against the parent's 180 s clock during the `finally` re-observation. A
run admitted after the parent budget is exhausted therefore has no consistent rule
for whether the final RELEASE sender may be terminated.

Reachability, stated honestly: the `finally` branch needs a Job still in `held`
after `owned_command` returned, and today `observe_owned` returns only after a
successful `close()` that removes the Job. The reachable triggers are narrow (for
example an exception at the head of `observe_owned`, such as `str(job.job)` at
`:110`). So the inconsistency is real in code but latent in practice.

Why it still deserves a fix: the docstring says the final RELEASE is sent even when
the window is exhausted (`:14-17`, "final RELEASE is sent without waiting for
another model invocation"). Admission with no budget check implements that; the
`finally` stop on the parent clock contradicts it. One clock authority should be
chosen and enforced in both places.

## 1a. Exact-line handoff for the author

Quoted verbatim from `532839ab…` (22728 bytes, 461 lines). Nothing below is
paraphrased.

```python
179: def observer_approval(receipt, *, own_sha, reviewed_sha):
180:     if re.fullmatch(r"[0-9a-f]{64}", reviewed_sha or "") is None:
181:         return "Independent reviewed observer SHA256 is required"
182:     if own_sha != reviewed_sha:
183:         return "Observer differs from the independently reviewed source"
184:     raw = receipt.get("rawEvent") if isinstance(receipt, dict) else None
185:     text = raw.get("text") if isinstance(raw, dict) else None
186:     if not isinstance(text, str) or PROTOCOL not in text or own_sha not in text:
187:         return "Fresh actual grant must explicitly name observer protocol and exact hash"
188:     return None
```

```python
303:               "successorGrant": False, "controlPlaneOnly": True,
304:               "validation": validation, "finalSender": publisher,
305:               "evidenceErrors": [], "errors": [], "releasePublished": False,
306:               "atomicConsumptionOwner": "frozen wrapper, before SDK/publishers",
307:               "controlJobBeforeConsumptionExplicitlyGranted": True,
308:               "sourceSha256": sha256(__file__)}
```

```python
339:         observe_owned(job, phase, held,
340:                       time.monotonic() + PUBLISH_SECONDS if is_publisher else deadline,
341:                       publisher=is_publisher, notify=checkpoint)
```

```python
380:             owned_command(helper.channel_command(message, args.next_owner),
381:                           "final-sender", publisher, is_publisher=True)
```

```python
393:     finally:
394:         # Any unexpected exception must preserve ownership. Custodian Jobs are
395:         # never terminated here, even after the total deadline.
396:         for job in list(held):
397:             phase = validation if validation.get("handlesClosed") is not True else publisher
398:             observe_owned(job, phase, held, deadline,
399:                           publisher=phase is publisher, notify=checkpoint)
```

```python
443:             "controlInfrastructureBeforeWrapperConsumptionRequiresExplicitGrant": True,
444:             "liveCustodianNeverKilled": True, "runtimeValidation": "UNRUN"}))
```

The stop gate B3 depends on is `:155` `if late and publisher and not stop_sent:`,
and the definition it reads is `:114` `late = clock() >= deadline`.

A minimal fix shape, for the author to judge and not a prescription:

1. Require a third prose marker in `observer_approval` (a fixed token naming the
   control Job before marker consumption), refuse when absent, and derive `:307`
   from that check instead of the literal. `:443` states policy, so it can stay.
2. Choose one clock for the publisher: either its own `PUBLISH_SECONDS` window in
   both `:340` and `:398`, or refuse admission at `:380` when the parent budget is
   exhausted. Record the choice in the docstring.

Neither change touches Job semantics, and neither affects the five verified claims
in section 2.

## 2 Per-claim verification

| Claim | Verdict | Evidence |
| --- | --- | --- |
| Real wrapper child terminal + Job0, then same call auto-publishes final | **holds** | `observe_owned` returns only on `empty is True and root_gone(root)` (`:96-171`, gate at `:131-147`); `run()` then reads both reports, assesses, and calls `owned_command(..., "final-sender", publisher, is_publisher=True)` in the same invocation (`:355-378`) |
| Deadline must not kill a wrapper custodian that still holds nested Jobs | **holds** | stop is gated on `publisher` (`:155`); validation is called with `publisher=False` (`:341-345`), so `job.stop()` is unreachable for it. Close is gated on `active == 0` (see §3), and the helper's Job carries `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`, so closing early would kill descendants; it cannot happen |
| Query exception keeps the original handles | **holds** | `:126-137`: on exception `empty = False`, `queryConfirmed = False`, no close, no stop, object stays in `held`; test `test_uncertain_query_retains_exact_handles_until_recovery` |
| Publisher terminal state persisted independently | **holds, with R3** | `:382-389` writes `final-sender.json` with the publisher phase, `delivered`, `selfTerminalClaim: False`; `releasePublished` requires `phase_gone(publisher)` + exit 0 + no errors + no forced cleanup (`:378-381`) |
| No self-terminal claim | **holds** | `:305` `selfTerminalClaim: False`, `observerAliveAtWrite: True`; `:387` same in the sender file; the release text says `selfTerminalClaim=false` (`:372`). The sender's terminal is *observed* from its Job, not claimed |
| New C grant must name `web-observed-relay/v1` + this exact hash | **partly, see B1/B2** | `:179-187` requires both strings and exact source equality (`own_sha != reviewed_sha`); `preflight` requires `--reviewed-observer-sha256` and refuses on drift (`:206-208`). Containment is too weak, and the control boundary is not required at all |
| Parent control Job before wrapper marker boundary explicit | **fails, B1** | `:307`, `:443` are constants |

Additional confirmations:

- **Only the wrapper consumes the marker.** `preflight` does a read-only
  `marker.exists()` refusal (`:232-240`) and the comment states the wrapper's
  atomic create decides the race. The parent never consumes or delegates.
- **`--execute-reviewed` and both pins are required before any source read.**
  `:200-208`, and tests `test_missing_explicit_flag_refuses_before_source_or_receipt_reads`,
  `test_missing_independent_raw_pin_refuses_before_source_reads`,
  `test_observer_hash_drift_refuses_before_frozen_import`.
- **Refusal is separated from run.** `main()` returns exit 3 with
  `processStarted: False` for `PermissionError/OSError/ValueError` from preflight
  (`:453-459`), so a refusal never masquerades as a started run.
- **Snapshot mode is inert.** No arguments prints `execution: False`,
  `processStarted: False`, `runtimeValidation: "UNRUN"` (`:434-447`).
- **`empty()` refreshes `record`.** `run-web-owned-window.py:104-114` sets
  `jobActiveProcesses` and `terminal` on every call, so `root_gone` reads fresh
  facts from the same query. There is no stale-snapshot window.
- **Pure fake-Job regressions.** `test_web_observed_relay_window.py` docstring
  states "Never instantiate a real Job or launcher"; `FakeJob.close` raises
  `AssertionError("Closed a live exact Job")` if a live Job is ever closed. 30
  declarations, matching the reported count. I counted them; I did not run them.

## 3 Why the custodian is never killed early

`OwnedJob` (`run-web-owned-window.py:39-120`) creates the Job with
`JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` (`:68`), so `CloseHandle(job)` terminates any
surviving member. `close()` (`:122-125`) is therefore destructive, and the observer
only reaches it after `empty()` has returned true, which requires both
`WaitForSingleObject(process, 0) == 0` and `info.active == 0` (`:107-114`). With no
active process in the Job, closing cannot kill anything.

The one writer of a destructive stop is `job.stop()` → `TerminateJobObject`, and it
is reachable only under `if late and publisher and not stop_sent` (`:155`).

## 4 Hypothetical followups, ranked

None of these produces a wrong outcome in the current bytes. They are recorded so a
later change does not silently turn one into a blocker.

- **R1. A never-started Job is labelled `TERMINAL`.** When `job.start` raises,
  `process` stays `None`, and `empty()` returns `terminal and active == 0` with
  `terminal = self.process is None or …` → true. `observe_owned` then sets
  `terminalConfirmed = True` and status `TERMINAL` for a Job that never ran. No
  false RELEASE follows, because `phase_gone` (`:86-93`) additionally demands an
  exact `pid` and `creationFiletime100ns`, which an uncreated process lacks, and
  `inspect_reports` refuses on that. Covered by
  `test_uncreated_process_is_not_an_exact_terminal_identity`. Still a mislabel in
  the durable evidence, and it is the same "not created is not terminal" class of
  error flagged earlier.
- **R2. `finally` attributes every held Job to `validation` until validation is
  closed.** `:397` chooses the phase from `validation["handlesClosed"]`, not from
  the Job's identity. If validation were ever still held when a publisher exists,
  the publisher would be observed with `publisher=False` (never stopped) and
  `observe_owned` would overwrite `validation["root"]`, `jobHandle`,
  `processHandle` with the publisher's values, corrupting the retained-root
  identity that `inspect_reports` and the RELEASE text rely on. Today this is
  unreachable, because `owned_command(validation)` cannot return until its own
  `observe_owned` has closed and removed the Job. It is a latent trap, not a live
  defect.
- **R3. `final-sender.json` is written before the `finally` re-observation.** If
  the publisher is still held when `finally` runs, its durable file records the
  pre-`finally` phase while `observer.json` is rewritten afterwards, so the two
  files can disagree about the sender's terminal state.
- **R4. `directory.mkdir(exist_ok=False)` and the frozen imports sit outside
  `run()`'s `try`** (`:292-296`). A race that creates the directory after preflight,
  or a load failure, escapes as a traceback rather than the structured refusal JSON
  that `main()` produces. No Job exists at that point, so ownership is not at risk.
- **R5. `inspect_reports` checks `c.get("grant")` but not `c.get("runName")`**
  (`:264`), unlike the wrapper report, which is checked for both.
- **R6 is promoted to B3, not listed here.** It is wrong in code, so it is filed as
  a latent defect rather than a followup. See section 1.

## 5 Non-claims

I did not execute the 30 fake-Job regressions, the snapshot mode, or any real run,
so I do not assert that they pass; I counted the 30 declarations and read their
assertions. I did not verify runtime behaviour of the Win32 Job calls, which needs
a real execution I am not permitted to start. B1, B2 and B3 are judged from the
source alone and do not depend on runtime behaviour.

Scope boundary: I own only this report. I did not edit
`run-web-observed-relay-window.py` or `test_web_observed_relay_window.py`, did not
create a task, started no Job, used no grant, and sent nothing to any coordinator.

These findings are bound to `532839ab…` (22728 bytes, 461 lines, mtime 11:53:27).
The author is editing B1 and B3. When the refreshed bytes land, the review is re-run
against the new hash; nothing here carries forward to different file content.

## 6 Provisional status of the in-flight refresh (not a verdict)

While this report was being written the subject moved. These are two different
artifacts and they must not be confused:

| Artifact | Size | Lines | Tests | SHA256 |
| --- | ---: | ---: | ---: | --- |
| Reviewed baseline (all findings above) | 22728 | 461 | 30 | `532839ab788f5abaebe22733cdb89b63f955d28f2abd2270330b00cc5c24e8dc` |
| In-flight refresh, observer | 25455 | 505 | - | `399abc8638513761d44aff609e4dae6c75604d629b35bbc23466178b7a2ce1d1` |
| In-flight refresh, tests | 21372 | 441 | 36 | `4271d700278d7392d45f0784a1e3db60a8b44772fb9c7cbd26c51961be0ba3c3` |

The refresh is still moving: the test file is newer than the observer file
(12:14:35 vs 12:12:16) and the test count grew from 30 to 36. No verdict is issued
here. Reading the in-flight bytes suggests all three findings are being closed:

- **B1 appears addressed.** `CONTROL_BOUNDARY = "control-job-before-marker/v1"`
  (`:54`), the docstring requires the exact standalone line
  `ACCEPT web-observed-relay/v1 sha256=<exact hash> boundary=control-job-before-marker/v1`
  (`:10-12`), and `observer_approval` now demands
  `acceptance not in text.splitlines()` (`:192-194`). The literal at `:323` is then
  downstream of a mandatory check, not a free-standing claim.
- **B2 appears addressed.** `text.splitlines()` makes the match a whole-line
  equality, so both the embedded mention and the negated form fail. The author added
  `test_negative_mention_is_not_an_acceptance_line`, which is exactly the
  counterexample in B2.
- **B3 appears addressed.** `publisher_deadline(parent_deadline, now)` (`:295-296`)
  returns `None` at or after the parent deadline and otherwise clamps to
  `min(parent_deadline, now + PUBLISH_SECONDS)`, so admission is denied late and the
  sender's window can never exceed the parent budget. `admitted_deadline` is what
  `observe_owned` receives (`:372`). The `finally` loop still passes the parent
  `deadline` (`:441`), but that is now never stricter than the admitted window, so
  the two-clock contradiction is gone.

One item to check in the final bytes, not a blocker yet. When admission is denied
*after* `helper.OwnedJob()` has been constructed (`:355-362`), the never-started Job
is still handed to `observe_owned` (`:372`). For an uncreated process `empty()`
returns true (`run-web-owned-window.py:113-114`), so the phase ends up with
`admitted=False` / `admission="DENIED_PARENT_DEADLINE"` *and*
`terminalConfirmed=True` / `status="TERMINAL"`. `releasePublished` still cannot be
claimed, because `phase_gone` requires an exact pid and creation stamp, so no false
delivery follows. It is a self-contradictory phase record. `owned_command` also
returns `phase.get("admitted") is True` (`:375`) and the publisher call site ignores
that return value. The author's new assertion at test `:400` checks `admission`, and
it is worth confirming the same case does not also assert a terminal status.

## 7 Final narrow delta review on the frozen refresh

This section is the verdict for the bytes the author froze. The sections above are
left intact as history; they bind to the earlier `532839ab…` baseline and are
superseded by this one.

| Artifact | Size | Lines | Tests | SHA256 |
| --- | ---: | ---: | ---: | --- |
| Observer (frozen, reviewed here) | 25455 | 505 | - | `399abc8638513761d44aff609e4dae6c75604d629b35bbc23466178b7a2ce1d1` |
| Tests (frozen, reviewed here) | 21372 | 441 | 36 | `4271d700278d7392d45f0784a1e3db60a8b44772fb9c7cbd26c51961be0ba3c3` |

Both hashes were recomputed and match. Frozen neighbours are unchanged:
`run-web-relay-window.py` `401f61d4…`, `web_relay_authorization.py` `84445442…`,
`run-web-app-window.py` `d80c46e1…`, `run-web-app-worker.ps1` `074ac022…`,
`run-web-owned-window.py` `9df7a943…`.

### Verdict: PASS, no blockers

**Delta 1, whole-line ACCEPT with protocol, sha and boundary token: closed.**
`CONTROL_BOUNDARY = "control-job-before-marker/v1"` (`:54`); the docstring requires
the exact standalone line (`:9-12`); `observer_approval` builds
`f"ACCEPT {PROTOCOL} sha256={own_sha} boundary={CONTROL_BOUNDARY}"` and tests
`acceptance not in text.splitlines()` (`:193`). `splitlines()` makes that an
whole-line equality, so a mention inside a sentence and a negated form both fail.
The snapshot advertises the same token as `requiredControlBoundary` (`:487`).

This closes **B1** as well: the boundary token is now part of the single mandatory
acceptance line, so the boundary cannot be silent and still pass. `run()` reaches
the report literal only through `preflight()` (`:303`), which calls
`observer_approval` (`:230-232`). The field at `:323` is still written as a literal,
which is acceptable while the check remains mandatory on the same entry path.

**Delta 2, capped publisher allowance and two admission checks: closed.**
`publisher_deadline(parent_deadline, now)` is
`None if now >= parent_deadline else min(parent_deadline, now + PUBLISH_SECONDS)`
(`:294-296`). Check one runs before Job construction and returns without creating
one (`:348-353`). Check two runs after the synchronous `helper.OwnedJob()` call and
skips `job.start` (`:359-364`). `observe_owned` receives the clamped
`admitted_deadline` (`:366-367`), so the sender's `late` can never exceed the parent
budget. The `finally` loop still passes the parent `deadline` (`:441`), but since
`admitted_deadline <= deadline` that is never more permissive, so **B3**'s two-clock
contradiction is gone.

**Delta 3, late local release and denied-sender local evidence: closed.**
`local-release.json` is written before the sender is attempted (`:397-403`) with
`delivered: False`, `handoff: "LOCAL_RELEASE_REQUIRES_COORDINATOR_RELAY"` and
`requireParentActualExitBeforeRelay: True`. `final-sender.json` (`:426-431`) carries
`delivered`, `coordinatorRelayRequired: not report["releasePublished"]` (`:429`) and
`localReleasePath` (`:430`). A denied sender cannot be reported as delivered,
because `releasePublished` (`:423-425`) requires `phase_gone(publisher)`, which needs
the exact pid and creation stamp. No successor grant is emitted on any path.

**Delta 4, child runName and nextOwner: closed.** There is no child runName schema.
`inspect_reports` rejects only an *optional* present-but-different value
(`:265-266`) and binds nextOwner between child and wrapper (`:267-268`). Covered by
tests `:215` and `:220`.

### Residuals, non-blocking

- **N1. The second denial path still observes a never-started Job.** At `:359-364`
the denial sets `admitted=False` / `admission="DENIED_PARENT_DEADLINE"` /
`processStarted=False` but does not return, so the Job object created at `:356`
still reaches `observe_owned` (`:366`). For an uncreated process `empty()` returns
true (`run-web-owned-window.py:113-114`), and because `late` set `holdSeen` first
(`:130-133`) the phase ends as `terminalConfirmed=True` /
`status="TERMINAL_AFTER_HOLD"` / `handlesClosed=True` with an empty `root`.
Nothing false is claimed: `phase_gone` refuses the empty identity, so
`releasePublished` stays false, and the terminal branch returns before the stop gate
(`:144-159` precedes `:161`), so `forcedCleanup` is not set. The record does label a
sender that never had a process as terminal-after-hold. This branch is also
untested: `test_late_validation_records_local_release_without_publisher_launch`
(`:389`) drives the deadline past the parent *before* construction, so it returns at
`:353` and asserts `publisher.events` is empty vacuously.
- **N2. `finally` still selects the phase by flag and passes the parent deadline**
(`:439-441`). Harmless now because the clamped window is never wider, and because
`owned_command` cannot return while a Job is still held. It is the same latent
trap recorded earlier as R2.
- **N3. Cosmetic.** `owned_command` returns `phase.get("admitted") is True`
(`:375`) and the publisher call site ignores the return value; the decision is
taken from `releasePublished` instead, which is stricter.

None of N1, N2 or N3 can produce a false delivery, a false successor grant, or a
false claim about this parent's own terminal state.

### Test coverage note

36 `def test_` declarations were counted statically. The new ones map to this
delta: `:215` optional child runName, `:220` nextOwner binding, `:260` missing
boundary rejected, `:266` negative mention rejected, `:389` late local release,
`:404` capped allowance. I did not run them, so I do not assert they pass; the
reported 36 PASS is the author's and the coordinator's result, not mine.

## 8. Final narrow delta review on `d1943bd1` (validation-admission hole)

Reviewed at observer
`d1943bd1e622fc3ca5fe327e1473a141b3af992cf48fc61f078f3140fc6552b3` and tests
`81d61c8b0f639222725df141ab9e63fd07280c9c053ebc065775bb777e60dedc`. Both match
the supplied values. Frozen inputs unchanged (`run-web-relay-window.py`
`401f61d4…`, `web_relay_authorization.py` `84445442…`). 38 `def test_`
declarations counted.

### The reported hole, and what closed it

Root found that the **validation** branch could still launch after the parent
deadline. The precreate guard read
`publisher_deadline(...) if is_publisher else deadline`, so a validation command
received the raw parent deadline and `observe_owned` only *flagged* lateness
instead of refusing.

Both branches now refuse. `:347-348`:

```python
admitted_deadline = (publisher_deadline(deadline, now) if is_publisher
                     else (deadline if now < deadline else None))
```

Validation admission is now `None` at or past the parent deadline. The
`is_publisher and` prefix is gone from the prestart re-check at `:360`, so the
second guard covers both branches.

### Refusal writes no wrapper report and attempts no marker

`owned_command` returns `False` at `:353` (precreate) or falls through with
`admitted=False` (prestart) without calling `job.start`. The caller at `:384`
records the refusal and raises at `:394`:

```python
report["refusal"] = {"reason": "PARENT_DEADLINE_BEFORE_VALIDATION_START",
    "processStarted": False, "wrapperStarted": False,
    "grantConsumption": "NOT_ATTEMPTED_BY_THIS_INVOCATION", ...}
raise PermissionError("Validation admission refused at parent deadline; no wrapper/report read")
```

The raise precedes `wrapper_path`/`child_path` at `:395-398`, so the refusal
never reads `-relay/wrapper.json` or `job.json`. The wrapper never runs, so it
never creates them. `grantConsumption: NOT_ATTEMPTED_BY_THIS_INVOCATION` is
accurate: the only marker contact in the observer is the read-only
`marker.exists()` precheck at `:241-243`, and the sole consumer remains the
frozen wrapper at `run-web-relay-window.py:534`.

### Exact ACCEPT line required for this hash

`own_sha = sha256(__file__)` at `:216`, compared against
`--reviewed-observer-sha256` at `:217`, then `:192-193` requires a standalone
line via `acceptance not in text.splitlines()`. For this source the grant must
contain exactly:

```
ACCEPT web-observed-relay/v1 sha256=d1943bd1e622fc3ca5fe327e1473a141b3af992cf48fc61f078f3140fc6552b3 boundary=control-job-before-marker/v1
```

Any mention, negation, missing boundary, or stale hash fails that membership
test.

### Verdict: PASS, no blockers

### Residuals (unchanged, non-blocking)

- **N1.** `:323` `"controlJobBeforeConsumptionExplicitlyGranted": True` is still a
  constant. Every reachable `observer.json` has passed `preflight`, which
  enforces the ACCEPT line, so the value is never false. It is simply not
  derived from the check.
- **N2.** Precreate refusal still opens `validation.stdout.log`/`.stderr.log`
  with `"xb"` at `:344-345` before the admission decision, leaving two empty
  logs in the observer's own evidence directory. These are not wrapper reports.
- **N3.** `preflight` runs twice (`:303` in `run`, `:496` in `main`). Read-only and
  idempotent.

New tests `:398` and `:414` lock the two guards; `:424` asserts
`report["refusal"]["wrapperStarted"]` is false. I did not run them, so the 38
PASS remains the author's result, not mine.

## 9 Independent verification of `d1943bd1` (Pi)

Provenance first: section 8 above was **not** written by me. It appeared in this
file between my section 7 and this turn. I re-derived every claim in it from the
source rather than adopting it, and record two corrections: main's second
`preflight` call is at `:506`, not `:496`, and the marker-consumption citation
`:534` is correct but the atomic create it reaches is
`web_relay_authorization.py:259` (`os.open(..., O_CREAT|O_EXCL|O_WRONLY, 0o600)`)
via wrapper `:181`.

### Verdict: PASS, no blockers

The three reported fixes are present and behave as described.

**1. Both branches now refuse late admission.** `:347-348`:

```python
admitted_deadline = (publisher_deadline(deadline, now) if is_publisher
                     else (deadline if now < deadline else None))
```

Validation previously received the raw parent deadline and merely *flagged*
lateness inside `observe_owned`; it now receives `None` at or past the deadline
and refuses before constructing a Job (`:349-353`). The `is_publisher and` prefix
is gone from the prestart re-check (`:360`), so the second guard covers validation
too. The publisher keeps its clamped allowance
(`min(parent_deadline, now + PUBLISH_SECONDS)`, `:294-296`).

**2. A validation refusal writes no wrapper report and attempts no marker.**
`owned_command` returns `False` (`:353`), the caller records the refusal and raises
(`:385-394`):

```python
report["refusal"] = {"reason": "PARENT_DEADLINE_BEFORE_VALIDATION_START",
    "processStarted": False, "wrapperStarted": False,
    "grantConsumption": "NOT_ATTEMPTED_BY_THIS_INVOCATION", ...}
raise PermissionError("Validation admission refused at parent deadline; no wrapper/report read")
```

The raise precedes the `wrapper.json` / `job.json` reads, so neither is touched, and
the wrapper process never starts, so the only consumer
(wrapper `:534` → `decide_execution` → `web_relay_authorization.py:259`) is never
reached. `NOT_ATTEMPTED_BY_THIS_INVOCATION` is accurate; the observer's own marker
contact stays the read-only `marker.exists()` at `:243`.

**3. An empty Job is closed without stop.** The terminal branch
(`:145-174`) precedes the stop gate (`:161`), so a never-started Job satisfies
`empty()` and `root_gone`, takes `job.close()`, and never reaches `job.stop()`.
`forcedCleanup` therefore stays false. For a real `OwnedJob`, `empty()` returns
true when `process is None` and `active == 0`, and `close()` skips the null process
handle, so no `TerminateJobObject` and no kill-on-close victim exist. Asserted by
test `:414` (`assertNotIn("start", ...)`, `stop_count == 0`, `validation.closed`).

### Required grant line for this source

`own_sha = sha256(__file__)` (`:216`) must equal `--reviewed-observer-sha256`
(`:217`), and `:193` requires the standalone line. For these bytes:

```
ACCEPT web-observed-relay/v1 sha256=d1943bd1e622fc3ca5fe327e1473a141b3af992cf48fc61f078f3140fc6552b3 boundary=control-job-before-marker/v1
```

A mention, a negation, a missing boundary token or a stale hash all fail the
`text.splitlines()` membership test.

### Residuals, all non-blocking

- **N1.** `:323` `"controlJobBeforeConsumptionExplicitlyGranted": True` remains a
constant. It is never false on a reachable path, because `run()` reaches that
literal only through `preflight` (`:303`), which enforces the ACCEPT line. Not
derived, but not wrong.
- **N2.** The precreate refusal still opens `validation.stdout.log` /
`.stderr.log` with `"xb"` (`:344-345`) before the admission decision, leaving two
empty logs in the observer's own directory. They are not wrapper reports and no
consumer reads them as such.
- **N3.** `preflight` runs twice, `:303` in `run()` and `:506` in `main()`.
Read-only and idempotent.
- **N4, additional to section 8.** A validation refusal that happens *after* the
Job is constructed (`:360-362`) still falls through to `observe_owned` (`:372`).
The phase then ends with `admitted=False` / `processStarted=False` **and**
`terminalConfirmed=True`, `status="TERMINAL_AFTER_HOLD"`, `handlesClosed=True`,
`root={}`. Every field is individually true of an empty, never-started Job, so
this is not a false statement; it is only readable as "a process ran" by a
consumer that ignores `admitted`, `processStarted`, the empty `root` and the
present `report["refusal"]`. No release or successor can follow, because
`phase_gone` needs a real pid and creation stamp and `assessment` is absent.
Test `:414` does not assert this labelling, so it is unverified either way. A
one-line hardening would be to skip `observe_owned` when `admitted` is false.

### Coverage

38 `def test_` declarations counted. The two new ones target exactly this delta:
`:398` precreate exhaustion refuses before creating a Job, `:414` construction
exhaustion closes the unstarted Job without stop. I did not run them; the 38 PASS
is the author's and the coordinator's result, not mine.

