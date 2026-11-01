# C864 product and protocol review (Pi5)

Date 2026-10-26. Author Pi5. Source-only. Read-only measurement plus one channel
read.

No source edit. No SDK, no Job, no receipt, no grant, no publication. Nothing was
executed. The frozen C843 audit and the post-release note were not modified.

## 1. What was read

`trellis channel messages qfli-core-release-sync --scope global --since 863 --raw`
returned seq 864, 865 and 866. Only 864 is in scope here.

| seq | author | ts (Z) | in scope |
| --- | --- | --- | --- |
| 864 | c-coordinator | 06:26:38.031 | yes |
| 865 | java-offline-1022 | 06:28:26.984 | context only |
| 866 | c-coordinator | 06:52:39.875 | context only |

Seq 864 substance, paraphrased without adding claims:

- Committed and pushed a stable source checkpoint at core HEAD
  `5b3c48c7d1c1822d0ee348b68eb6b33f3bba54d0`, `fix(process): terminate Windows tree
  before waiting for input`. Four remotes pushed, `ls-remote main` matched.
- 14 scoped files: supervisor, focused tests, spec, raw proof.
- `process_supervisor.dart` now `095de8c1…`. Terminal remains `7bf7d365`.
- Peers must refreeze actual HEAD plus WIP. Old `64f…` snapshots are stale for
  future execution.
- No new SDK grant by this checkpoint.
- Declared contract limits: cancellation starts an observed stdin-close future;
  Windows dispatches the tree command before awaiting stdin; ownership remains
  while input is pending; POSIX bound unchanged; signatures unchanged; repeated
  cancellation shares one future; a rejected managed cancel future is cached and
  not retryable; the boolean PID-based tree command is not retained-identity
  subtree proof; the Lua adapter must not read root kill, timeout, closed streams
  or status 130 as subtree success; a stronger conservative contract remains open
  and separately reviewed; do not infer it from the 9 fake tests.

**Protocol and grant: none borrowed.** Seq 864 issues no grant and accepts no
protocol version. The C843 grant `Web-observed-app-20261026-03` is consumed and
C851 released the slot with no successor. No replay.

## 2. C864 claims, independently checked

| Claim in seq 864 | Independent check | Verdict |
| --- | --- | --- |
| core HEAD `5b3c48c7d1c1822d0ee348b68eb6b33f3bba54d0` | `git rev-parse HEAD` in `qfli_studio_core` returns exactly that; `git log -1` subject matches | match |
| `process_supervisor.dart` = `095de8c1…` | current file hashes to `095de8c17c66dc206fe170b3f99b7447d8660f183085ecb338f97484ff0e5bfc` | match |
| Supervisor is committed, not WIP | `git status --porcelain -- lib/services/process_supervisor.dart` is empty, so the live file equals HEAD | match |
| Other live WIP preserved | core tree shows modified content, pages, services and tests; no clean-core claim is made | consistent |
| Old `64f…` snapshots stale | C843's snapshot pinned `64f0aa75a773c632a1101ce16e1900615b274960`; seq 864 declares that class stale. Matches section 8 of the C843 audit | consistent |
| No new SDK grant | seq 864 states it. Seq 866 then defers Java's request, so still no grant | match |

Scope note, now resolved: seq 864 speaks of a 164-file freeze in which only
`process_supervisor.dart` changed. That freeze is the core lib/config binding
`core-lib-config-freeze.json` (`863f97ce…`), captured at core HEAD `2f9039a3…`,
whose live check is 164 bound, 163 unchanged, 1 changed. The C843 input set I hold
is the 332-entry app capture, and it shows two changes, the second being
`test/owned_preview_resource_broker_test.dart`. The core-only freeze cannot see the
qfli_web fixture, so both statements are true at once. Section 7 records the same
distinction from the Pi3 refreeze side.

## 3. Fixture `ffb4e6ec…`, independently verified, UNRUN

File: `test/owned_preview_resource_broker_test.dart`.
sha256 `ffb4e6ec0bbb532374bc5c25e3a04dc7eee558fd13d8e83f0edfc39151acc3f8`,
19030 bytes, 568 lines. Matches the stated hash.

The deadline test at lines 449-478 retains every required property:

| Required property | Line | Assertion |
| --- | --- | --- |
| 504 on deadline | 467 | `expect(result.statusCode, 504)` |
| policy retained on the error path | 468 | `expectPolicy(result)` |
| in-flight accounting returned | 469 | `expect(broker.activeRequests, 0)` |
| retained bytes returned | 470 | `expect(broker.retainedBytes, 0)` |
| immediate retry succeeds 200 | 471-473 | fetch `/after-timeout`, `expect(recovered.statusCode, 200)`, body `'ready'` |
| dispose is bounded | 475 | `await broker.dispose().timeout(const Duration(seconds: 1))` |
| accounting still clean after dispose | 476-477 | `activeRequests 0`, `retainedBytes 0` |

`expectPolicy` at lines 60-69 asserts the owned offline CSP via
`buildOwnedContentSecurityPolicy(WebProjectConfig.offlineContentSecurityPolicy)`,
plus `cache-control: no-store` and `x-content-type-options: nosniff`. So the
policy guarantee covers the 504 path too, not just the success path.

Status: **UNRUN.** This body has never been executed in any accepted run. The C843
run executed `6f41b712…`, not this file. No gate conclusion follows from it.

## 4. Product finding: the abort clause is no longer asserted

The test is named `deadline aborts the owned request and releases in-flight
accounting`. Several assertions back "releases in-flight accounting". None back
"aborts the owned request".

The current fixture contains **zero** occurrences of `.done`, `disconnect`,
`invalidHttpResponse` or `HttpResponse`. Across all 14 tests, the two server-side
observers that remain are:

- line 406-419, the SSE test, which waits on an `arrived` completer
- line 484-516, the dispose test, which counts `visits` and asserts `visits == 3`

Both observe that the broker **reached** or **did not re-reach** the server. Neither
observes a socket teardown. `visits` counts requests, not disconnections.

So the fixture now proves that the deadline path returns 504, keeps policy
headers, and returns accounting. It does not prove that the upstream connection
was closed. The word "aborts" in the test name is an unasserted claim.

Stated as a review judgement and not as a measured fact: dropping a disconnection
oracle can be correct when the oracle itself is unreliable, because Dart's
`HttpResponse.done` does not reliably complete for a client-cancelled response.
The product gap that remains is that no replacement observation was added. The
broker still owes the contract "deadline aborts the owned request", and after this
edit nothing in the fixture checks it.

One precision note on the retry: `brokerFor` defaults to `maxInFlight = 16`, so a
retry returning 200 does not by itself prove capacity came back. The direct
`activeRequests == 0` and `retainedBytes == 0` assertions at 469-470 do the
proving, and 476-477 repeat it after dispose.

## 5. Seven pins verified

| Role | Path | Expected | Live | Binding | Verdict |
| --- | --- | --- | --- | --- | --- |
| observer | `research/run-web-observed-relay-window.py` | `d1943bd1e622fc3ca5fe327e1473a141b3af992cf48fc61f078f3140fc6552b3` | same | grant seq 843 ACCEPT | match |
| observer test | `research/test_web_observed_relay_window.py` | `81d61c8b0f639222725df141ab9e63fd07280c9c053ebc065775bb777e60dedc` | same | accepted observer pair | match |
| wrapper | `research/run-web-relay-window.py` | `401f61d44495dd0a8b681a25746263e589203a9555f30c49106eca791db0fdb3` | same | C843 receipt `wrapperSha256` | match |
| auth module | `research/web_relay_authorization.py` | `84445442fed9b9382555e02b8812c6321cbd7c7ec5026ff13904c5f5897a1de4` | same | C843 `AUTHORIZATION_SHA256` | match |
| frozen runner | `research/run-web-app-window.py` | `d80c46e1b1cf2abe7e7a582e61016ac36266354242de198a5623628659922a19` | same | receipt `frozen.runner` | match |
| frozen worker | `research/run-web-app-worker.ps1` | `074ac02216bab95e8da23d87dca7d1567be5f2fcc4722d43e53d059227fb8b78` | same | receipt `frozen.worker` | match |
| frozen helper | `research/run-web-owned-window.py` | `9df7a94399aae38951337d61693d65de6e3cef438d02d4e51c787242dfda7fbe` | same | receipt `frozen.helper` | match |

Sizes: observer 26038 B / 515 lines, observer test 23212 B / 480 lines, wrapper
60258 B / 1169 lines, auth 30119 B / 667 lines, runner 17492 B / 350 lines, worker
3814 B / 93 lines, helper 12228 B / 234 lines.

Method note: the four orchestration files (observer, observer test, wrapper, auth)
are **not** in the C843 332-entry input snapshot, which holds only three
`research/` entries. Their binding is the C843 receipt and the seq 843 grant, not
the snapshot. I matched them against those pinned values, not against the
snapshot, and I say so rather than imply a snapshot comparison.

The three frozen files are in the snapshot, still match it, and also match the
receipt. Two independent bindings agree.

## 6. Five formatter paths

Paths from the seq 843 grant, checked against the C843 snapshot:

| Path | C843 snapshot | Current | Verdict |
| --- | --- | --- | --- |
| `lib/services/owned_preview_policy.dart` | `9f0319af…` | same, 16038 B | unchanged |
| `lib/services/owned_preview_resource_broker.dart` | `56fd917c…` | same, 11793 B | unchanged |
| `test/owned_preview_policy_test.dart` | `9324590b…` | same, 17688 B | unchanged |
| `test/owned_preview_resource_broker_test.dart` | `6f41b712…`, 19454 B | `ffb4e6ec…`, 19030 B | **changed** |
| `test/web_offline_browser_test.dart` | `506c3972…` | same, 9073 B | unchanged |

Four of the five match the C843 snapshot. The broker fixture changed after C851
released the slot, so the C843 format PASS does not transfer to it. The other four
carry no post-release claim either.

## 7. Pi3 refreeze directory, present and verified

Directory `research/web-relay-input-c864-20261026`. When first scanned it held 3
files and was still being written; the final read at 14:59:43 local saw 5 files and
a stable set. Everything below was measured after it settled.

| File | sha256 | bytes |
| --- | --- | --- |
| `app-full-inputs.json` | `f8d2ab9e2f9785919b372b9283a88277f0e0ccdf1f6ec77816f58a821ad5714a` | 64409 |
| `build-readiness-input.py` | `42ff41529090586b57f7dbf716686e8638f650d7df018897b0c06f386b4feaeb` | 16085 |
| `capture-app-full-inputs.py` | `adf0fbd8bf96565e5c5c3bbd624d6e8864c8da97b1097112cab1e1358522a0dd` | 6013 |
| `readiness-input.json` | `dc495523adf367991d7bfcb46f14ea1a88fef2c209950a24095335dbb25c6247` | 19305 |
| `refreeze-report.md` | `86b95cc46c53d25934c6b1869ab35e86d6654d20f9e2b446d24acf3e398844fa` | 4339 |

Independent checks I ran on the refreeze:

| Check | Result |
| --- | --- |
| Refrozen 332 entries re-hashed against the current tree | 0 drift, 0 missing |
| Refrozen 332 against the C843 332 | same 332 paths, exactly 2 hash differences: supervisor and the broker fixture |
| `filesSha256` recomputed as `sha256(json.dumps(files, sort_keys=True, separators=(',',':')))` uppercase | reproduces `7B87BB2676D7E90892536BCAB0158132064A19660972D93B0B08450A3937F7B5` exactly |
| `filesCount` declared vs actual | 332 vs 332 |
| `coreHead` vs live `git rev-parse HEAD` in `qfli_studio_core` | `5b3c48c7d1c1822d0ee348b68eb6b33f3bba54d0` both |
| 7 frozen pins in `readiness-input.json` | all `match: true`, same values as section 5 |
| 5 formatter paths in `readiness-input.json` | same values as section 6, fixture marked `repairFile: true` |
| `permittedChanges` vs the preserved parent capture | `added []`, `removed []`, `changed` the two known files, `permittedOnly: true`, `unexpectedChanges: []` |
| Product HEAD claimed in the report | `d863397122f2a3f0e3f6df5cbe066873f959d902`, matches live `git rev-parse HEAD` in `qfli_web` |
| Historical parent preserved | `app-full-inputs.json` still `2ddb7e38…`, `readiness-input.json` still `226cb055…`, mtimes still 12:15, so not rewritten |
| Capture proof block | `mainGuardHeld: true`, `helperImported: false`, `loadHelperCalled: false`, `runCalled: false`, `executeCalled: false`, `processesStarted: ["git -C core rev-parse HEAD"]` |

The capture script's own pins cover runner, worker and helper, and it refuses a
changed supervisor before importing. That is a third independent binding of the
three frozen files, beside the C843 receipt and the C843 snapshot.

The refreeze also answers the section 2 scope question. Its historical parent
freeze binds 164 core lib/config files and measures 163 unchanged plus exactly the
supervisor replacement, which is what seq 864 said. The 332-entry app capture sees
one extra change, the qfli_web fixture, which the core-only freeze does not cover.
The two records agree; they describe different sets.

The refreeze is consistent with my own measurements and adds no claim beyond them.
It does not make the fixture RUN. Its report states the same: the fixture cleanup
stays source only and untested.

## 8. Limits carried from C864, not re-derived

Recorded as C's declared limits, not as my findings:

- The conservative failure, drain, retry and native-identity contract is open and
  separately reviewed.
- The Windows tree command is boolean and PID-based, which C states is not
  retained-identity subtree proof.
- A rejected managed cancel future stays cached and cannot be retried.
- The Lua adapter must reach Job 0 in a later fresh gate.
- No native, WSL, HAP, device or full-acceptance promotion.

A product review that treated those as settled would overstate the record.

## 9. Non-claims

- I did not run the fixture, the suite, the broker, or any gate.
- I did not review the new `process_supervisor.dart` body.
- The abort-clause gap in section 4 is a reading of assertions, not a captured
  runtime behaviour.
- I did not verify the four remotes or the `ls-remote` match; that is C's stated
  claim.
- I verified the refreeze's internal consistency and its match to the live tree.
  I did not run its capture script, so I am relying on the recorded proof block for
  the "only `git rev-parse` started" claim.
- I did not review `build-readiness-input.py` or the full `readiness-input.json`
  body beyond the arrays named in section 7.
- I did not edit source, and I did not touch the frozen C843 audit or the
  post-release note.
- No acceptance criteria are invented. The properties in section 3 are
  transcriptions of assertions present in the file.

## 10. Final verdict on the C864 refreeze

Verdict: **PASS**, source-only identity.

Method: I re-derived every claim from the bytes on disk and did not read the
manifest's booleans as evidence. Where a boolean existed, I recomputed the fact
behind it. **72 checks, 0 failures.** Note: the literal line `FAILED CHECKS: 0`
is the summary, not a failure.

| What | How I re-derived it | Result |
| --- | --- | --- |
| 332 full inputs | hashed each of the 332 paths under `qfli_web` | 0 drift, 0 missing |
| canonical input digest | `sha256(json.dumps(files, sort_keys=True, separators=(',',':')))` | `7B87BB2676D7E90892536BCAB0158132064A19660972D93B0B08450A3937F7B5`, matches `filesSha256` and the `authoritative` value |
| 42 core WIP rows | ran `git status --porcelain --untracked-files=all` in `qfli_studio_core` myself | (code, path) set matches the 42 manifest rows exactly |
| 42 WIP file bytes | hashed each row's file, compared size | all hashes and sizes match disk |
| WIP rollup | recomputed `sha256(json.dumps([[code,path,bytes,sha256]...], separators=(',',':')))` | `8BC8E2F34EFF374971EEBD1103F21F715A41674683963E776C9440356DB599F6`, matches |
| heads | `git rev-parse HEAD` in both repos | product `d8633971…` and core `5b3c48c7…` both match, core branch `main` |
| 7 pins | hashed and sized each file | `pinnedSha256 == liveSha256 == disk hash` for all 7, sizes match |
| 5 formatter paths | hashed and sized each file | all 5 match, order equals the grant's five, `repairFiles` is the first four |
| historical 164 freeze | hashed the freeze JSON itself, then re-hashed all 164 bound files | freeze file `863f97ce…` matches; 163 unchanged, exactly 1 changed, 0 missing |
| the 1 change | compared live bytes to the bound value | `lib/services/process_supervisor.dart`, live `095de8c1…`, exactly the 095 override, and `claimsOldHashMatch: false` is honest |
| freeze metadata | read the freeze file | capture head `2f9039a3…`, `productionTerminalSha256 7bf7d365…`, matching seq 864 |
| 332 vs parent | re-read the parent capture | no added, no removed, exactly 2 changed: supervisor and the broker fixture |
| parent preservation | hashed the parent files | `2ddb7e38…` and `226cb055…`, matching the `historicalParent` claims |
| capture proof block | read the fields | guard held, helper not imported, `loadHelper`/`run`/`execute` not called, only `git -C core rev-parse HEAD` started |
| manifest declarations | read the fields | `schemaVersion 5`, `kind web-relay-readiness-input`, `window c864`, `sourceOnly true`, `execution false` |
| fixture status | read `repairStatus` | fixture marked **UNRUN**, matching my own finding |
| `permittedChanges` | compared to my diff | `unexpectedChanges: []`, `changed` equals the 2, `permittedOnly` consistent |

The one claim I could not re-derive is the capture's list of started processes. I
verified the proof block is internally consistent and that the pins it names are
the three frozen files, but I did not re-run the capture, so the "only one process"
statement remains Pi3's recorded claim.

### Frozen manifest identity

Read twice, before and after the verification window, with identical hashes and
unchanged mtimes, so the set did not move while I checked:

| File | sha256 | bytes |
| --- | --- | --- |
| `readiness-input.json` | `dc495523adf367991d7bfcb46f14ea1a88fef2c209950a24095335dbb25c6247` | 19305 |
| `app-full-inputs.json` | `f8d2ab9e2f9785919b372b9283a88277f0e0ccdf1f6ec77816f58a821ad5714a` | 64409 |
| `refreeze-report.md` | `86b95cc46c53d25934c6b1869ab35e86d6654d20f9e2b446d24acf3e398844fa` | 4339 |
| `build-readiness-input.py` | `42ff41529090586b57f7dbf716686e8638f650d7df018897b0c06f386b4feaeb` | 16085 |
| `capture-app-full-inputs.py` | `adf0fbd8bf96565e5c5c3bbd624d6e8864c8da97b1097112cab1e1358522a0dd` | 6013 |

**Frozen manifest sha: `dc495523adf367991d7bfcb46f14ea1a88fef2c209950a24095335dbb25c6247`**

### Blockers

None. Every re-derived fact agrees with the manifest.

### What this PASS does not mean

- It is an identity result, not a functional one. The fixture and the broker repair
  stay **UNRUN**. No formatter, test, analysis, content or gate phase ran for this
  input.
- It does not promote the refreeze to an acceptance, a READY, a grant or a
  successor. The refreeze issues none, and I verified none exists in it.
- It does not make the historical 164 freeze a 164-hash match today; it stays a
  source binding with exactly one live replacement.
- Section 4 still stands: the broker fixture no longer asserts that the deadline
  path aborts the upstream connection.
- I did not edit the manifest, the refreeze, any source file, the frozen C843 audit
  or the post-release note. This section is the only change in this turn, and it
  edits only my own file.

## 11. Final verdict after the evidence-wording fix

Pi3 then corrected one evidence sentence and nothing else. This section records
the re-verification of the corrected manifest.

### What the fix corrected, and why it mattered

The old wording said the fixture **and** the broker repair stay UNRUN. That reads
as if the broker bytes were never exercised. They were. C843 executed broker
`56fd917c…` with test `6f41b712…`, and the gate failed at `+320 -1`. My own C843
audit recorded that in section 5 of the frozen report.

The corrected text now separates three things:

| Subject | Corrected statement | Matches my evidence |
| --- | --- | --- |
| broker production bytes `56fd917c…` | exercised in C843, gate failed, 320 PASS / 1 FAIL, "those bytes are not a pass" | yes, matches `+320 -1` and `gate=FAIL` |
| combined candidate (production bytes + fixture cleanup) | UNRUN, never run together, no new pass claimed | yes |
| fixture cleanup `ffb4e6ec…` | new, never run | yes |

`notProven` grew from 7 to 8 items so the broker's failed C843 run and the
untouched combined candidate sit on separate lines. `repairStatus` now carries
three keys instead of one. `refreeze-report.md` lines 53-54 and 99-100 say the
same.

This is the correction I would have asked for. The previous sentence understated
the record in the direction that flatters the change, and the new sentence does
not.

### Re-verification of the corrected manifest

83 checks, 0 failures. Same method as section 10: every fact re-derived from disk,
no boolean taken on trust.

| Group | Checks | Result |
| --- | --- | --- |
| 332 full inputs re-hashed | 2 | 0 drift, 0 missing |
| canonical input digest | 1 | `7B87BB26…` recomputed |
| 42 core WIP rows | 7 | (code,path) set equals live `git status`, hashes and sizes match, rollup `8BC8E2F3…` recomputed |
| heads | 4 | product `d8633971…`, core `5b3c48c7…`, branch `main` |
| 7 pins | 14 | `pinnedSha256 == liveSha256 == disk`, sizes match |
| 5 formatter paths | 12 | all match, order equals the grant five |
| historical 164 freeze | 13 | 163 unchanged, exactly 1 changed = `process_supervisor.dart` at `095de8c1…`, 0 missing |
| 332 vs parent | 5 | no added, no removed, exactly 2 changed |
| declarations | 7 | capture guard held, `sourceOnly`, schema 5, `permittedChanges` clean |
| corrected wording | 14 | the three subjects are separated and each statement is accurate |
| round scope | 5 | text and report changed; capture and source did not |

### Scope of the fix, measured

| File | Before | After | Changed |
| --- | --- | --- | --- |
| `app-full-inputs.json` | `f8d2ab9e…` | `f8d2ab9e…` | no, no recapture |
| `capture-app-full-inputs.py` | `adf0fbd8…` | `adf0fbd8…` | no, capture untouched |
| `build-readiness-input.py` | `42ff4152…` | `5b56f184…` | yes, text builder |
| `readiness-input.json` | `dc495523…` | `6a7bf3b9…` | yes, text |
| `refreeze-report.md` | `86b95cc4…` | `028ec18c…` | yes, text |

The capture inputs are byte identical, so the 332 hashes verified in section 10
still stand without re-capture. No source file changed in either round.

### Final frozen manifest

Read twice, with a settle window, identical both times:

| File | sha256 | bytes |
| --- | --- | --- |
| `readiness-input.json` | `6a7bf3b96f221d4c4732f95a44c503225f205128ccdc1894e613b9b8234c3c79` | 19773 |
| `app-full-inputs.json` | `f8d2ab9e2f9785919b372b9283a88277f0e0ccdf1f6ec77816f58a821ad5714a` | 64409 |
| `refreeze-report.md` | `028ec18cc1a3d859e688eae1d8ff5b7ccc1a80c61dbcea397db83d53aff92601` | 4604 |
| `build-readiness-input.py` | `5b56f184f526d4e0b937ca09d078ee5795291a05a9df9dc2759b8386ccb88c4d` | 16692 |
| `capture-app-full-inputs.py` | `adf0fbd8bf96565e5c5c3bbd624d6e8864c8da97b1097112cab1e1358522a0dd` | 6013 |

**Final frozen manifest sha: `6a7bf3b96f221d4c4732f95a44c503225f205128ccdc1894e613b9b8234c3c79`**

Superseded value for the record: `dc495523adf367991d7bfcb46f14ea1a88fef2c209950a24095335dbb25c6247`.

### Verdict

**PASS.** Source-only identity, corrected evidence text, 83 checks with 0 failures.

### Blockers

None.

### What this PASS still does not mean

- The combined candidate is UNRUN. Nothing was executed for it, in this round or
  the last.
- The broker production bytes carry a **failed** C843 gate. The corrected text says
  so, and the PASS here does not upgrade them.
- Section 4 stands: the fixture no longer asserts that the deadline path aborts the
  upstream connection. Removing the oracle and correcting the wording are two
  separate acts, and neither adds that assertion back.
- The historical 164 freeze remains a source binding with one live replacement, not
  a 164-hash match today.
- This is an identity result. It is not an acceptance, a READY, a grant or a
  successor.
- I did not edit the manifest, the refreeze, any source file, the frozen C843 audit
  or the post-release note. This section is the only change in this turn, and it
  edits only my own file.