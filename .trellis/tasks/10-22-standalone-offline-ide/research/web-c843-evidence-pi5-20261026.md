# C843 resource release and gate evidence (Pi5)

Date 2026-10-26. Author Pi5. Source-only audit of recorded evidence.

No SDK, grant, Job, publisher or source change. Nothing was executed except one
read-only channel read (`trellis channel messages ... --since 844 --raw`). This
audit is frozen to the C843 before/after snapshot pair and makes no future-run
identity claim.

## 1. Scope

Audited artifacts, all read only:

| Path | sha256 | bytes |
| --- | --- | --- |
| `research/web-app-c843-20261026-observed/observer.json` | `07a5a83081c13de5…` (prefix) | 5175 |
| `research/web-app-c843-20261026-observed/final-sender.json` | `2e0ea340d8e6e36d…` | 1836 |
| `research/web-app-c843-20261026-observed/local-release.json` | `0edd799729f3e0c8…` | 725 |
| `research/web-app-c843-20261026-observed/root-terminal-observation.json` | `985484f6317af960…` | 5807 |
| `research/web-app-c843-20261026-relay/wrapper.json` | `c641d807f93cd7bb…` | 12161 |
| `research/web-app-c843-20261026/job.json` | `0d19c24c3327323f…` | 9876 |
| `research/web-app-c843-20261026/source-before.json` | `062cc4c44dad632903291091f8ea5ff1f526195f486795467df8ec2b6e26e9ec` | 63329 |
| `research/web-app-c843-20261026/source-after.json` | `062cc4c44dad632903291091f8ea5ff1f526195f486795467df8ec2b6e26e9ec` | 63329 |
| `build/web-c843-reviewed-receipt-20261026.json` | — | 3928 |
| `build/web-c843-root-reviewed-raw-pin-20261026.txt` | — | 64 |

Prefixes above are the first 16 hex characters of each file hash, recorded so a
later reader can re-derive the full value.

## 2. Identities, all confirmed

| Claim | Evidence | Verdict |
| --- | --- | --- |
| Grant `Web-observed-app-20261026-03`, successor `c-coordinator` | receipt `grant`, `successor`; observer `grant`, `nextOwner`; job/wrapper `grant`, `nextOwner` | match |
| Receipt schema 3, coordinator event seq 843, protocol `web-relay-format-app/v1` | receipt `schemaVersion: 3`, `coordinatorEvent.seq: 843`, `protocol` | match |
| Window 180 s | receipt `windowSeconds: 180`; observer `windowSeconds: 180`; job `budgetSeconds {work 150, cleanup 170, total 180}`; wrapper `budgetSeconds: 180` | match |
| Raw pin `d7c2c7cf007dab7bab4dcfff64ab3e81682dbd5ee902f8d4db77e330e7f3b8f9` | `build/web-c843-root-reviewed-raw-pin-20261026.txt`; receipt `rawEventSha256`; observer `--reviewed-raw-sha256`; root-terminal-observation command | all four identical |
| Observer source `d1943bd1…` | observer `sourceSha256` | match to the reviewed observer |
| Wrapper `401f61d4…`, auth `84445442…` | receipt `wrapperSha256`, observer `AUTHORIZATION_SHA256` pin, wrapper `authorizationSha256` | match |
| Frozen runner/worker/helper | receipt `frozen {runner d80c46e1…, worker 074ac022…, helper 9df7a943…}`; job `helperSha256 9df7a943…` | match |
| Validation root 71720 | observer `validation.root.pid`, job `phases` wrapper root, root-terminal-observation `validation.root` | match |
| Validation creation filetime `134374672342866742` | same three places | match |
| Validation terminal true, exit 1, Job0 | observer `validation.root {terminal true, exitCode 1, jobActiveProcesses 0}`, `terminalConfirmed true`, `status TERMINAL` | match |
| Final sender 88116, filetime `134374673390379035` | observer `finalSender.root`, final-sender.json `phase.root` | match |
| Sender terminal true, exit 0, Job0 | same, `terminalConfirmed true`, `custodianPreserved false`, `forcedCleanup false` | match |
| `heldJobs = 0` | observer `heldJobs: 0`; final-sender.json `heldJobs: 0`; root-terminal-observation `heldJobs: 0` | match |
| Observer elapsed 105.387 s | observer `elapsedSeconds: 105.387` | match |
| Original exec session 7698 actual terminal exit 1 | root-terminal-observation `{originalExecSession 7698, actualOriginalTerminal true, originalExitCode 1}`; channel seq 850 | match |
| Root terminal observation recorded 05:49:57.997 | root-terminal-observation `observedUtc 2026-10-26T05:49:57.997135+00:00` | match |
| seq 850 appended 05:49:58.556 | channel seq 850 `ts` | match |

The five formatter paths from the grant are present in the 332-entry snapshot and
unchanged across the pair:

| Path | sha256 in snapshot |
| --- | --- |
| `lib/services/owned_preview_policy.dart` | `9f0319afd64e20322bdefd7085a1927e3fda28f4e6f33a70ae317b0c39715802` |
| `lib/services/owned_preview_resource_broker.dart` | `56fd917c3b4706e9dcf7b6328ec55f0e1de5c76a6825190f98c90606e6af13d5` |
| `test/owned_preview_policy_test.dart` | `9324590b14b57bea5483c3aaa6fee2df9f0f89aad0baf1c47b17cd667062b639` |
| `test/owned_preview_resource_broker_test.dart` | `6f41b71218caf10d5dc4ceea5d112475d562a9827e944fd7600db4a091d8a913` |
| `test/web_offline_browser_test.dart` | `506c39720b1ea9badd7bf716c2b790cbb7e2b773ee1d896e34612a7f4c29d098` |

## 3. Source drift: none, within C843 scope

`source-before.json` and `source-after.json` are **byte identical**:
`062cc4c44dad632903291091f8ea5ff1f526195f486795467df8ec2b6e26e9ec`, 63329 bytes
each. Both hold 332 `{path, bytes, sha256}` entries. `coreHead` is
`64f0aa75a773c632a1101ce16e1900615b274960` in both, and the same value appears in
`job.json` and channel seq 848.

Independent corroboration of the same fact:

- `job.json` `sourceSnapshotsIdentical: true`
- wrapper `assessment` reports no change; `sourceFormatBefore`/`sourceFormatAfter`
  are recorded and `sourceFormatChanged: []`
- seq 848 `sourceStable=True`

So: **no source drift occurred during the C843 window.** This is a statement about
the C843 window only. See section 7 for why it must not be carried forward.

## 4. Resources: released and corroborated

Kept deliberately separate from the gate.

| Resource fact | Evidence |
| --- | --- |
| All owned Jobs empty | job `allOwnedJobsEmpty: true`; wrapper `outerActiveProcesses: 0`; observer `heldJobs: 0` |
| All phase Jobs terminal with Job0 | format 89764/0, tests 11388/0, analysis 91100/0, content 80740/0, publisher 89372/0, validation 71720/0, sender 88116/0 |
| Handles closed | observer `handlesClosed: true`, `handlesRetained: false`; wrapper `handlesRetained: false`, `cleanupConfirmed: true`, `resourcesReleased: true` |
| No forced cleanup | observer `forcedCleanup: false`; wrapper `forcedCleanup: false`; sender `forcedCleanup: false` |
| No HOLD, no deadline | observer `holdSeen: false`, `budgetLate: false`, `localBudget: PROVISIONAL_WITHIN`; wrapper `phaseDeadlineReached: false`, `budgetLate: false` |
| Custodian preserved for validation | observer `validation.custodianPreserved: true` |
| Final release published | observer `releasePublished: true`; final-sender `delivered: true`; wrapper `publication: DELIVERED`, `relayDelivered: true` |
| No successor grant | observer `successorGrant: false`; wrapper `successorGrant: false`; local-release `successorGrant: false` |
| Local release exists separately | `local-release.json` records `delivered: false`, `handoff: LOCAL_RELEASE_REQUIRES_COORDINATOR_RELAY`, `requireParentActualExitBeforeRelay: true` |

The wrapper itself refuses to treat process exit as cleanup proof:
`processExitIsNotCleanupProof: true`. The audit agrees with that stance and does
not infer cleanup from exit codes alone.

## 5. Gate: FAIL, one failing test

Kept deliberately separate from section 4.

| Gate fact | Evidence |
| --- | --- |
| Gate FAIL | wrapper `assessment {gate FAIL, ownership RELEASE_READY, publication DELIVERED, budget PROVISIONAL_WITHIN}`; observer `assessment.gate FAIL`; seq 848 `gate=FAIL gateErrors=1 gateSource=runner` |
| Failure count | `tests.stdout.log` final counter `+320 -1`, closing line `Some tests failed.` → 320 pass, 1 fail |
| Phase results | format PASS, tests FAIL_OR_INCOMPLETE, analysis PASS, content PASS |
| Validation root exit 1 | observer `validation.root.exitCode: 1`; job tests phase `exitCode: 1` |
| Release eligibility still true | observer `assessment.releaseEligible: true`, `errors: []` |

The single failure, verbatim from `tests.stdout.log:157-160`:

```
00:15 +148: test/owned_preview_resource_broker_test.dart: deadline aborts the owned request and releases in-flight accounting
00:16 +148 -1: test/owned_preview_resource_broker_test.dart: deadline aborts the owned request and releases in-flight accounting [E]
  TimeoutException after 0:00:01.000000: Future not completed
  dart:async  _startMicrotaskLoop
```

That is the only `-1` transition in the log. Everything before it passed
(`+148`), and the counter reaches `+320 -1` without any second failure.

Reading of the failure, stated as a mechanism and not as proof:

- The test gives the broker a 200 ms `requestDeadline` and wraps the fetch in a
  1 s `.timeout(...)`. The `TimeoutException` proves the broker's own future never
  completed inside 1 s, so the caller received no 504, no 502 and no error at all.
- In the broker version recorded in this snapshot (`56fd917c…`), `_cancel` only
  claims `operation.response` and calls `abort()` plus `client.close(force: true)`.
  Delivery happens solely in `_perform`'s `finally`. If the abort and forced close
  do not resume the suspended `await for` over the open response stream, the
  `finally` never runs and the future never settles.
- That matches the observed symptom exactly: not a wrong status, but no status.

So the earlier move of delivery out of `_cancel` closed the mis-attributed status
problem and opened a non-delivery problem on the deadline path. This audit records
the symptom; it does not assert the mechanism as proven, because no runtime trace
was captured.

This is the same test family that carried the original C782 deadline complaint, so
the C843 run is evidence that the deadline path was **not** closed by that fix.

## 6. Channel evidence, seq 845 to 853

Read with `trellis channel messages qfli-core-release-sync --scope global --since 844 --raw`.

| seq | author | ts (Z) | substance |
| --- | --- | --- | --- |
| 845 | web-offline-1022 | 05:47:49.534 | Pre-ACK. Raw 843 pinned `d7c2c7cf…`, receipt path, observer evidence path, session 7698 retained, no release claim |
| 846 | Lua | 05:48:13.780 | Lua832 residual diagnosis: `process_supervisor.dart:264-267` awaits `stdin.close()` before `taskkill /T`, root-only fallback, no subtree survival assertion. Explicitly probable, not attributed |
| 847 | web-offline-1022 | 05:48:58.256 | RELEASE_PENDING_PUBLISHER, all four phase records, `sourceStable=True`, publisher not yet terminal |
| 848 | web-offline-1022 | 05:48:58.916 | GRANT CONSUMED, `gate=FAIL gateErrors=1`, `resourcesReleasedAtRelay=true`, `wrapperCleanupPending=true`, `forcedRelease=false` |
| 849 | web-offline-1022 | 05:48:59.562 | FINAL validation TERMINAL RELEASE, exact validation root, JobHandle 316 / ProcessHandle 412 |
| 850 | web-offline-1022 | 05:49:58.556 | Original exec session 7698 ACTUAL TERMINAL exit 1, observer PID 87884, resource corroboration only, gate remains failed |
| 851 | c-coordinator | 05:51:51.545 | C independently accepts 849/850. Proof 164.471426 s within 180. Gate FAIL 320/1. Resource release is not validation success |
| 852 | c-coordinator | 05:53:22.394 | Reopens only `lib/services/process_supervisor.dart` plus focused tests/spec for the 846 defect |
| 853 | Lua | 05:54:07.396 | Lua acknowledges C851 ownership, awaits the cancel contract, no source write yet |

Two properties worth recording explicitly:

1. seq 849 and seq 850 both say no successor grant, and seq 851 returns the slot to
   `c-coordinator` without granting a successor. Three independent statements agree.
2. seq 850 says the observer wrote a durable root observation. The user-side note
   that the root write is an actual tool proof and not a report self-claim is
   consistent with the artifact: `root-terminal-observation.json` carries
   `observedUtc 05:49:57.997135` and session 7698 identity, while the observer's own
   report stops at `finishedUtc 05:48:59.623751`. The two are separate artifacts
   written at different times by different processes.

## 7. Timeline, all offsets from receipt `issuedAtUtc` 05:47:14.145574Z

| Offset | Event |
| --- | --- |
| 0.000000 s | Receipt issued (pre-ACK reference point) |
| 0.137474 s | Observer started |
| 0.140310 s | Validation command admitted and started |
| 0.272362 s | Wrapper clock start |
| 104.849638 s | Validation root terminal, Job0, exit 1 |
| 104.891000 s | Final sender started |
| 105.474742 s | Final sender terminal, Job0, exit 0 |
| 105.478177 s | Observer finished writing |
| 163.851561 s | Root terminal observation recorded (`root-terminal-observation.json`) |
| 164.410426 s | Channel seq 850 appended |
| 164.471426 s | Root publisher tool actual terminal (C851's figure) |
| 277.399426 s | C851 appended |

Observer `elapsedSeconds` is 105.387 while its `finishedUtc` sits 105.478177 s
after the reference. The 0.091 s difference is the final durable write that
happens after the elapsed sample, which the observer itself discloses through
`sampledAfterFinalIo`.

Everything up to and including the actual tool proof at 164.471426 s is inside
180 s. C851 was appended at 277.399426 s, outside 180, and C851 states that
plainly: the independent inspection happened later and is not claimed to be inside
the window.

Gate pass and resource release are different claims:

- **Resources**: all Jobs 0, handles closed, no forced cleanup, release delivered.
  Corroborated across observer, wrapper, job and root observation.
- **Gate**: FAIL with 320 pass and 1 fail. Validation is not a success.
- A released resource set does not promote a failed gate, and a failed gate does
  not invalidate the resource accounting. The two are recorded separately here on
  purpose.

## 8. Frozen scope and what must not be carried forward

This audit covers the C843 window only.

Channel seq 852 reopened `lib/services/process_supervisor.dart`. That means the
332-entry snapshot audited here no longer binds the tree for any future run. It
remains valid as the record of what C843 actually executed, and it must not be
used as the input identity for a later run.

Therefore:

- The no-drift finding in section 3 is true for C843 and false as a statement
  about any later tree.
- The broker and test hashes in section 2 identify what ran in C843. They are not
  a claim about the current or future build.
- Any later run needs its own fresh pre-ACK snapshot and its own identity
  comparison.
- The `process_supervisor.dart` defect from seq 846 is a separate, still-open item
  with its own repair checkpoint. It is recorded here because C843 evidence names
  it, not because this audit resolved it.

## 9. Non-claims

- I did not run the failing test, the suite, or the broker. The failure text is
  quoted from the recorded log.
- The deadline-path mechanism in section 5 is a reading of the code plus the
  symptom. It is not a captured trace and not a proof.
- I did not verify that 320 is the complete pass count of the intended suite; I
  verified the counter reached `+320 -1` and the log closed with `Some tests
  failed.`
- I did not confirm that the single failure is the only way the gate could fail;
  I confirmed it is the only `-1` transition in this log.
- I did not reconcile the observer's `elapsedSeconds` against wall clock beyond
  the offsets in section 7.
- I make no claim about the current on-disk tree, because seq 852 invalidated the
  snapshot for that purpose.
- No acceptance criteria are invented. The acceptance statements in sections 4 and
  5 are transcriptions of recorded fields, not new thresholds.
