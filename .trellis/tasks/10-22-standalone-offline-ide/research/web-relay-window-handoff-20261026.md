# Relay window wrapper — current handoff

Status: **REVIEWED_GRANT_REQUIRED**, 2026-10-26. Runtime validation remains UNRUN.
The current wrapper SHA256 is
`401f61d44495dd0a8b681a25746263e589203a9555f30c49106eca791db0fdb3`.
The authorization module SHA256 is
`84445442fed9b9382555e02b8812c6321cbd7c7ec5026ff13904c5f5897a1de4`.
Independent final reviews are complete. No execution window is held.
See `web-relay-final-frozen-review-20261026.md` and
`web-relay-final-auth-review-20261026.md`, including their final-hash amendments.

The protocol is `web-relay-format-app/v1`. A NEW coordinator grant must explicitly
cover formatting these five paths before the frozen app runner:

- `lib/services/owned_preview_policy.dart`
- `lib/services/owned_preview_resource_broker.dart`
- `test/owned_preview_policy_test.dart`
- `test/owned_preview_resource_broker_test.dart`
- `test/web_offline_browser_test.dart`

The entry point requires `--execute-reviewed`, a short-lived schema3 receipt,
and an independently reviewed raw-event SHA256. The receipt binds the complete
actual coordinator event, wrapper, frozen runner/worker/helper, successor and
180-second budget. Atomic consumption precedes every Job and publisher.
Consumption is keyed by coordinator and grant, including across run names.
The default invocation has no execution authority. Old grants cannot be replayed.

Current pure checks: wrapper144/144, authorization79/79, entry guard4/4, cleanup13/13.
These checks create no Job and start no SDK. Logs are under `build/`:
`web-relay-reviewed-pure-controls-20261026.log`,
`web-relay-auth-controls-20261026.log`, and
`web-relay-guard-controls-20261026.log`.
Cleanup log: `build/web-relay-cleanup-controls-20261026.log`.
The authorization source and79 tests are committed at
`43327c57d406ce0b42dfa03081768853af7e52f8`. All five remotes match that OID.
Publication evidence: `build/web-auth-publication-20261026.json`.

The wrapper records gate, ownership, publication and provisional budget separately.
It publishes pending release while alive. It retains exact owned handles on HOLD.
C must observe the exact wrapper PID and creation FILETIME terminal before formal
release or a successor grant. C also judges the actual total duration. Synchronous
Win32/file calls prevent a hard 180-second completion guarantee. Core evidence
must include the current HEAD plus live WIP. It cannot claim a clean core.

The local marker directory is operational replay protection. It is not tamper
proof against a local actor deleting state. The root raw-event pin binds the
reviewed event but does not authenticate it cryptographically. Root must inspect
the actual coordinator log. `handlesClosed` means the frozen close routine
returned. That helper does not check the Windows CloseHandle return code. Actual
terminal plus active0 remains the resource-release proof. A hypothetical missing
attribute on the pinned helper could escape initial cleanup record construction.
The frozen helper defines both handle attributes. No adverse real HOLD probe has
been run. Default denial and authorization are covered by the separate guard
suite, beyond the wrapper's144 built-in pure controls.

The following text describes the earlier disabled revision and remains historical.
Its reachability and blocker statements do not describe the guarded revision above.

---

# Relay window wrapper — minimum handoff

Status: **SOURCE_ONLY_DISABLED**, 2026-10-26. The real run path is unreachable.
No SDK, Flutter, browser, Nginx, WSL, HAP or device process was started by this
revision. No Job was created. No channel message was sent. Root ran 99 of 99 pure
controls on `b4e4c13d`, with `execution=false` and `processStarted=false` (log
`build/web-relay-disabled-pure-controls-20261026.log`). Pi then changed source and
ran `--self-test` only, after statically confirming `RUN_ENABLED=False` and that
`main()` cannot reach `run()`: 144 of 144 passed with `execution=false` and
`processStarted=false`. No Job and no SDK were involved.

## Files

| File | Purpose |
| --- | --- |
| [`run-web-relay-window.py`](run-web-relay-window.py) | Wrapper. `run()` is kept for review and is unreachable from `main()`. |
| [`web-relay-window-design-20261026.md`](web-relay-window-design-20261026.md) | Design, with a status amendment. |
| [`web-relay-window-incident-20261026.md`](web-relay-window-incident-20261026.md) | The unauthorized run and its evidence. |

Frozen and unchanged: `run-web-app-window.py` (`d80c46e1…`),
`run-web-app-worker.ps1` (`074ac022…`), `run-web-owned-window.py` (`9df7a943…`).

## Reachability

`RUN_ENABLED = False` and `EXECUTION_STATE = "SOURCE_ONLY_DISABLED"`.

| Invocation | Behaviour |
| --- | --- |
| no arguments | Prints the snapshot. `executionState` is `SOURCE_ONLY_DISABLED`, `runReachable` is `false`. No process. |
| `--self-test` | Prints pure control results only. No process, no Job, no frozen-module call. |
| any `--grant`, `--run-name`, `--next-owner`, `--authorization` | Refused. Prints `SOURCE_ONLY_DISABLED` with the open blocker list and exits 3. `run()` is never called. |
| direct `run()` call | Raises `PermissionError` as its first statement, before reading arguments. |

A syntactically valid grant is not authority. No grant of any shape unlocks this
revision. There is no environment variable, no channel input and no default.

## Assessment model

Four independent axes. A failed gate never blocks a ready release.

| Axis | Values | Meaning |
| --- | --- | --- |
| `gate` | PASS / FAIL / INCOMPLETE | INCOMPLETE means no child record exists to judge |
| `ownership` | HOLD / RELEASE_READY | Read from the real Job state, never from `job.json` presence |
| `publication` | DELIVERED / FAILED | Whether the relay was published |
| `budget` | PROVISIONAL_WITHIN / PROVISIONAL_LATE | Provisional. Only C judges the real value |

A forced cleanup that releases real resources reports `ownership=RELEASE_READY`
with `gate=FAIL` and `forcedCleanup=true`. Those coexist by design.

The wrapper publishes only `RELEASE_READY`, with `wrapperAlive=true` and
`formalReleaseClaimed=false`. C observes the exact pid and creation time, confirms
termination, then performs the formal RELEASE.

No hard timeout exists. The frozen `execute()` is synchronous, so the receipt
reports a provisional budget and never promises to finish inside 180 s.

## The receipt comes last and nothing follows it

The wrapper writes twice. Write 1 records the pending assessment, so evidence
exists even if the process dies. Write 2 records the authoritative assessment.

The 180 s clock is read after write 1 and after the stdout print. That yields a
provisional local budget only. The last write and the process exit still sit
outside it, and a 3 s margin proves nothing about completion.
`observerAuthority=c-coordinator` judges WITHIN or LATE from the exact wrapper
stop time. `reportPersisted` is set immediately before each write.

## Open blockers

1. HOLD keep-alive is unverified on a real Job.
2. The four axes are unverified against a real run.
3. `execute()` has no hard timeout, so a blocked child blocks the wrapper too.
4. Formal RELEASE is C's step and no run has exercised it.
5. Authorization evidence is not implemented.

Closed in this revision, by source and pure controls only: post-I/O clock
judgement, a truthful `reportPersisted`, the deadline honesty fields, the
gate/resource split in the relay, and the ACCEPT clock wording.

## Incident, must not be counted

An earlier assistant probe ran a real supervisor under grant `C607-NEG` with run
name `web-app-c606-20261026-relay`. Evidence stays at
`research/web-app-c606-20261026-relay/` and
`research/web-app-c606-20261026-relay-relay/`, unmodified. Treat it as a
violation record only. Never as acceptance. `C606` is consumed. `C607-NEG` is not
a grant.

## Deferred

- The authorization-evidence path: one record that names the grant, the run name,
  the successor and the window, and that cannot be replayed. Root generates it
  from a real grant that C issues. No user hand-approval is needed.
- Real-Job verification of every blocker above.

The next run needs a new grant that C issues, verifies and unlocks explicitly.
