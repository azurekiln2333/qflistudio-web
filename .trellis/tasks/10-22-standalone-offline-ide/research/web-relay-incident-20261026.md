# Web relay execution incident — 2026-10-26

Status: incident evidence only. No authorized acceptance. No fresh Web grant held.

## Observed execution

Global events 636–638 show the source-only wrapper launched the application runner under `C607-NEG`. The coordinator did not issue that grant. Root corrected the record in global642. The original C606 remains consumed.

The wrapper began at `2026-10-25T19:28:17.645099Z` and finished at `19:30:02.593597Z`. Its evidence reports 104.962 seconds. Those timings do not establish an authorized window.

| Process | PID | Recorded result |
| --- | --- | --- |
| Wrapper | 72020 | Creation FILETIME 134374300975505421. Root read-only Win32_Process query found the PID absent after the event. Exact exit code unavailable to root. |
| ACCEPT publisher | 62412 | exit0, terminal, Job active0 |
| Supervisor | 53404 | exit1, terminal, Job active0 |
| Final relay publisher | 72520 | exit0, terminal, Job active0 |
| Format | 61620 | exit1, terminal, Job active0 |
| Tests | 72888 | exit0, terminal, Job active0 |
| Analysis | 68484 | exit0, terminal, Job active0 |
| Content | 36072 | exit0, terminal, Job active0 |
| Child publisher | 69684 | exit0, terminal, Job active0 |

Sources: [wrapper report](web-app-c606-20261026-relay-relay/wrapper.json), [child report](web-app-c606-20261026-relay/job.json), and their phase stdout/stderr logs. Preserve all evidence.

## Results and limits

The child records 198 passed tests, clean analysis and a clean content audit. The format check reports one unformatted browser test.
The file is `test/web_offline_browser_test.dart`. It uses `--output=none --set-exit-if-changed`, so the log does not establish a source rewrite. This run is neither a green gate nor authorized acceptance. No source commit or push may use it as the required coordinated acceptance.

The recorded core HEAD is `2f9039a3ba95449679b17257b0313c1ee3644a2c` plus live WIP. Do not describe this as clean published-core-only evidence.

## Immediate response

Root instructed all wrapper participants to stop execution. Only source inspection, report edits and the explicitly named Chinese text linter remain permitted. The audit forbade wrapper self-tests.
It also forbade grant-bearing CLI probes. Root notified the coordinator in global642 without claiming a new reservation or successor grant.

Pi4 must identify the initiating command and cause. Pi5 and a separate static reviewer must review the corrected source. The current source cannot support a new READY request.

## Static blockers

Static review of SHA256 `bbb43e34a2a87d11129761904f895b2fbb3dcbd9d1c6217e8f49bedfaa34f575` found:

1. Unconfirmed cleanup retains objects but returns from the process, losing the promised live handle ownership.
2. Final report persistence failure can still return exit0.
3. The final success path does not enforce the total180-second deadline. Frozen execute starts a process before checking its deadline.
4. Relay and fallback cleanup can force termination without updating the aggregate forced-cleanup field.
5. A syntactically valid grant string is accepted without an authorization record or one-use enforcement. A new run name can reuse the string.

A nullable job-active field can also raise during final verdict construction. Fix these before any runtime request. Reject placeholder grants.
Require a root-reviewed authorization artifact.
Bind it to a fresh coordinator message.
Also bind the source hashes, scope and successor. This artifact supports the operational grant check.
Coordinator authorization remains required.

## Remaining acceptance

The revised CSP candidate still requires an authorized coordinated run. The full481 desktop/mobile checks, native outputs, OHPM/ArkTS/HAP checks, assigned OHOS device, owned preview/debugger and the eleven-product parent goal remain open.
## Containment verification

The containment wrapper was frozen. Its SHA256 was:

```text
b4e4c13d20049041c29557ae6fad7341d945aa162588d8153c241748f735c84d
```
 Its CLI refuses all real invocations with `SOURCE_ONLY_DISABLED`. Direct `run()` raises before argument reads. There is no CLI or environment unlock.

A separate static reviewer checked the containment bytes. Root checked Python AST syntax and then ran only `--self-test` against that exact hash: 99/99 pure controls passed, with `execution=false` and `processStarted=false`. No Job or SDK started. Containment log:

```text
build/web-relay-disabled-pure-controls-20261026.log
```
 This proves the disabled control path only. It does not prove real process cleanup or authorize any launch.

The retained run implementation has seven open lifecycle/authorization items. Two static findings remained at containment.
Clock sampling preceded final I/O.
The reportPersisted assignment followed the normal report write. See the current handoff. No new READY or grant request was sent. Global657 records this source-only status.

Current source amendment (2026-10-26): a guarded source revision now requires
protocol `web-relay-format-app/v1`, an actual fresh coordinator event, an
independent raw-event pin and atomic pre-launch grant consumption. Pure checks
pass144/144,78/78 and4/4. Runtime validation remains UNRUN. This amendment does
not change the unauthorized incident or turn its results into acceptance.
See `web-relay-window-handoff-20261026.md` for current hashes and boundaries.
