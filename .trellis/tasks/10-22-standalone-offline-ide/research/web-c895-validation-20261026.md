# C895 observed Web gate, validation record

Source-only report. No SDK run, no source change and no commit was made for this
note. It records what the C895 evidence directories already contain, plus the
C904 acceptance of that release.

Authoritative total: **158.019 s** from pre-ACK `09:55:41.343308Z` to the latest
publisher-tool transcript `09:58:19.362Z`. That is within the 180 s bound. The
earlier approximate 156.3 s figure is retired.

## Evidence directories

| Directory | Content |
| --- | --- |
| `web-app-c895-20261026` | gate: job, four phase logs, source before and after |
| `web-app-c895-20261026-relay` | relay wrapper, accept, source format, supervisor, relay |
| `web-app-c895-20261026-observed` | observer, final sender, root terminal observation |

| File | Bytes | SHA256 |
| --- | --- | --- |
| `job.json` | 7588 | `766504143F713604E6A8544DB584EE5E62AC25055DE441E2BC6EBAC1B528C683` |
| `tests.stdout.log` | 75664 | `2EAE40CEED6051E93A198C14608C07EF527444281E7FB90FA07673261F6BF0A3` |
| `release.txt` | 4545 | `DB9E6DA2EFCFDBE70ECDCB05DC09C756DB6465D6FC6F6C26C176915DD6E1D2CF` |
| `source-before.json` | 63329 | `A54030D711FF192552FDCB11D00B9203B6DE8781356DEF006747A831E41C1E00` |
| `source-after.json` | 63329 | `A54030D711FF192552FDCB11D00B9203B6DE8781356DEF006747A831E41C1E00` |
| `wrapper.json` | 12150 | `8C5EBFFF5B98822213201DCD5FD2037F7DCA49029327F3AB2A571C655E44A4DE` |
| `observer.json` | 5175 | `A0BA56504D4EA6251FA8EDAC4113DC4385F10DCFC9EB5E775B89DC4CFFB26A7E` |
| `root-terminal-observation.json` | 1105 | `9661E62FFD074C6DA993F6BABFD6809CFD549F96545D77D75F39C0190D312020` |
| `final-sender.json` | 1836 | `A2840316D13A3E677CB5D3B6C0217E99BAC7828D6DA3ECF96FC63384D298DF72` |

Grant `Web-observed-app-20261026-04`, run `web-app-c895-20261026`, successor
`c-coordinator`, window 180 s.

## Gate

`job.json` records `status: RELEASE`, `errors: []`, `firstError: null`,
`sourceSnapshotsIdentical: true`, `allOwnedJobsEmpty: true`,
`terminalConfirmed: true`, `validationJobsTerminalConfirmed: true`.

All four phases PASS, each with exit 0, Job 0 and no deadline or forced cleanup.

| Phase | Root pid | Creation FILETIME | Exit | Job | Deadline | Forced |
| --- | --- | --- | --- | --- | --- | --- |
| format | 14288 | `134374821434461863` | 0 | 0 | no | no |
| tests | 89516 | `134374821444699175` | 0 | 0 | no | no |
| analysis | 88336 | `134374822358677819` | 0 | 0 | no | no |
| content | 9472 | `134374822416971422` | 0 | 0 | no | no |

## Counts

- Format: `Formatted 11 files (0 changed) in 0.08 seconds.`
- Tests: `01:28 +321: All tests passed!` That is 321 passed and 0 skipped. The
  log holds no skip marker and no failure marker.
- Analysis: `No issues found! (ran in 3.7s)` over 4 items.
- Content: 481 of 481 for tutorial titles, example titles, example bodies,
  explain and lesson output. `Issues: 0`. Type split html 160/160, css 160/160,
  javascript 161/161, 1582 distinct concepts.

The broker deadline fixture `ffb4e6ec` was exercised by this run. The earlier
UNRUN note is superseded for that fixture.

At validation capture the four candidate files were uncommitted: untracked in
the working tree at the moment the gate ran. That is the capture-time state, not
a lasting one. Root commits the four candidate files after reviews. The hashes
below bind the exact bytes this gate validated, so the commit can be checked
against them.

## Bound candidate bytes

Full SHA256 of the four candidate files, from the frozen formatter manifest
`sourceFormatBefore` in `wrapper.json`. The after map is identical and
`sourceFormatChanged` is empty, so these bytes are unchanged across the run.

| File | SHA256 | Bytes |
| --- | --- | --- |
| `lib/services/owned_preview_policy.dart` | `9F0319AFD64E20322BDEFD7085A1927E3FDA28F4E6F33A70AE317B0C39715802` | 16038 |
| `lib/services/owned_preview_resource_broker.dart` | `56FD917C3B4706E9DCF7B6328EC55F0E1DE5C76A6825190F98C90606E6AF13D5` | 11793 |
| `test/owned_preview_policy_test.dart` | `9324590B14B57BEA5483C3AAA6FEE2DF9F0F89AAD0BAF1C47B17CD667062B639` | 17688 |
| `test/owned_preview_resource_broker_test.dart` | `FFB4E6EC0BBB532374BC5C25E3A04DC7EEE558FD13D8E83F0EDFC39151ACC3F8` | 19030 |

The fifth formatter path, `test/web_offline_browser_test.dart`, is not a
candidate file. It pins `506C39720B1EA9BADD7BF716C2B790CBB7E2B773EE1D896E34612A7F4C29D098`.

These four hashes match the working tree at report time.

## Source invariance

- `source-before.json` and `source-after.json` are byte identical, both
  `A54030D711FF…C1E00`, 63329 bytes, 332 files each.
- The relay `sourceFormatBefore` and `sourceFormatAfter` maps are equal and
  `sourceFormatChanged` is empty.
- `job.json` `sourceSnapshotsIdentical` is true.

No input file changed during the run.

## Core

Core HEAD `5b3c48c7d1c1822d0ee348b68eb6b33f3bba54d0` plus live work. This is host
and work-in-progress evidence. It is not clean-core evidence and not device
evidence.

## Terminal evidence

Each of these is confirmed terminal with Job 0:

| Layer | Identity | Terminal |
| --- | --- | --- |
| Outer execution | session 71189, chunk `8484c4`, write_stdin `229ce0` | exit 0 at `09:57:32.369Z` |
| Validation root | pid 82672, FILETIME `134374821414952833` | exit 0, Job 0 |
| Relay accept | pid 91020 | exit 0, Job 0 |
| Relay source format | pid 6884 | exit 0, Job 0 |
| Relay supervisor | pid 71208 | exit 0, Job 0 |
| Relay publish | pid 88568 | exit 0, Job 0 |
| Final sender | pid 23080, FILETIME `134374822437902519` | exit 0, Job 0, delivered true |
| Root 903 publisher | chunk `06b0da` | exit 0 at `09:58:19.362Z` |

`final-sender.json` records `delivered: true`, `heldJobs: 0`,
`controlPlaneOnly: true`, `selfTerminalClaim: false`,
`coordinatorRelayRequired: false`.

`observer.json` records `gate: PASS`, `releaseEligible: true`, `budgetLate:
false`, `holdSeen: false`, `heldJobs: 0`, `resourcesReleased: true`,
`validationExitCode: 0`, `selfTerminalClaim: false`, `successorGrant: false`.

`wrapper.json` assessment: gate PASS, ownership `RELEASE_READY`, publication
`DELIVERED`, budget `PROVISIONAL_WITHIN`. `formalReleaseClaimed` is false because
the wrapper is still alive while it publishes. Release authority is C, after
observing pid and creation time stop.

Elapsed: runner `99.981 s`, observer `102.876 s`, relay wrapper `102.119 s`. Each
is inside its own window. The authoritative end-to-end figure is the 158.019 s
above, not these.

## C904 acceptance

`coordinatorAcceptance` in `root-terminal-observation.json`: global sequence
904, `fullProofSeconds: 158.019`, `actualPublisherToolTranscriptUtc:
2026-10-26T09:58:19.362Z`, `actualOriginalTerminalTranscriptUtc:
2026-10-26T09:57:32.369Z`, `within180: true`.

C904 accepted the resource release with 321 PASS and 0 skip across all phases.
The grant is consumed and not replayable. No further Web SDK owner exists.

## Remaining open

All 11 products and OHOS acceptance remain open. This report is host and WIP
evidence for Web only.

## Not proven

- No device, native or OHOS runtime evidence is in these directories.
- No clean-core claim follows from a core head plus live work.
- At validation capture the four candidate files were uncommitted. This note
does not commit them. Root commits them after reviews, and the bound hashes
above let that commit be checked byte for byte.
- This note ran nothing. It records evidence, and it does not certify a later
  candidate.