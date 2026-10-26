# C782 authorized Web validation — 2026-10-26

Grant: `Web-relay-format-app-20261026-01`, actual global event782.
Protocol: `web-relay-format-app/v1`. The grant is consumed and cannot be replayed.
Root independently read the complete raw grant. Its canonical SHA256 is
`9f1c05f7c1bf598e2d5ef3e589b71b8bdaef45b5c10ca87c8a3d1dc49f8c2413`.

## Result

| Gate | Actual result |
| --- | --- |
| Exact five-file source format | PASS, four files changed by Dart formatter |
| Frozen11-file format check | PASS, zero changes |
| Full application suite |316 PASS,4 FAIL |
| Production CSP browser regressions | Both WebForge and Nginx PASS |
| Production early console bridge | Both engines PASS |
| Scoped full application analysis | No issues found |
| Product content audit |481 tutorial/example pairs, issues0 |
| Captured input stability |332 inputs identical after granted formatting |
| Resource ownership | All exact Jobs terminal+active0, no forced cleanup |
| Final coordination budget | FAILED, final sender completed559.172s after wrapper start |

The four failed tests belong only to the newly added owned-preview policy and
resource broker. Failures: raw Chinese URL rejected, an incorrect negative case
for the ordinary `a..` path segment, capacity returned after result delivery, and
reentrant cancellation completing a result twice. Their subsequent source
repairs remain UNRUN and are excluded from the validated preview-security commit.

The CSP regression copies unchanged shipped HTML027, HTML097, HTML137, HTML138
and JS017 sources. It checks actual loaded object and SVG content. Both engines
produce the required cross-port object/embed CSP violations with zero escaped
requests and zero sentinel hits. This is desktop production-policy evidence.
It does not establish the separate481-example desktop/mobile or ArkWeb gate.

Core HEAD: `2f9039a3ba95449679b17257b0313c1ee3644a2c` plus44 live WIP entries.
The captured terminal source was the C-owned7bf7d365 candidate. No clean-core or
tested-terminal claim follows from this run.

## Exact ownership

Root polled original exec session39231 to terminal exit1. Wrapper PID75072,
creation FILETIME134374558013668585, returned after107.828s.

| Phase | PID | Exit | Terminal / Job active |
| --- | --- | --- | --- |
| ACCEPT |22424 |0 | true /0 |
| Source format |61980 |0 | true /0 |
| Supervisor |64460 |1 | true /0 |
| Format |80468 |0 | true /0 |
| Tests |36236 |1 | true /0 |
| Analysis |79344 |0 | true /0 |
| Content |76252 |0 | true /0 |
| Child publisher |70472 |0 | true /0 |
| Wrapper pending relay |22092 |0 | true /0 |
| Root final sender |82644 |0 | true /0 |

The root final sender creation FILETIME is134374563601042473. Its retained Job
ended with remainingHeldJobs0. No successor SDK grant is inferred here.
C independently decides handoff after observing the exact wrapper and sender.

The wrapper started at02:36:41.514311Z and finished at02:38:29.324272Z.
Root final sender finished at02:46:00.686184Z. Thus the provisional wrapper budget
is within180, but actual final publication is late. Global786/787 pending reports
are not the formal terminal handoff. Global789 is the actual root release.
A later source-only control-plane observer is being prepared to publish directly
when its retained validation child exits, avoiding a model turn between those
steps. It requires separate review and a fresh explicit grant before use.

## Evidence

- `web-app-c782-20261026/job.json` and phase stdout/stderr logs.
- `web-app-c782-20261026/source-before.json` and `source-after.json`.
- `web-app-c782-20261026-relay/wrapper.json`.
- `web-app-c782-20261026-relay/root-terminal-observation.json`.
- `web-app-c782-20261026-relay/final-sender.json`.

The close routine returning is not proof of checked Windows CloseHandle status.
The terminal+active0 records provide the resource-release evidence. No catalog,
native, WSL, OHPM, HAP or device execution was added to this window.
The eleven-product parent remains in progress.
