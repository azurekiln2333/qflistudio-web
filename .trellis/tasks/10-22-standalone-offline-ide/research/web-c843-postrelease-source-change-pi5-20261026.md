# Post-release source changes after C851 (Pi5)

Date 2026-10-26. Author Pi5. Read-only measurement. No source edit, no run.

Companion to `web-c843-evidence-pi5-20261026.md`. That file holds the frozen C843
evidence and was not modified. This file records source changes that happened
after C851 released the slot. They are kept apart on purpose: a post-release edit
is not C843 drift, and C843 drift is not a post-release edit.

## 1. Method

I re-hashed all 332 `{path, bytes, sha256}` entries from
`research/web-app-c843-20261026/source-after.json` against the current tree,
resolved relative to `D:/MyNewProjects/qfli_web`. Read-only. Nothing was executed.

Result:

| Bucket | Count |
| --- | --- |
| Unchanged vs the C843 snapshot | 330 |
| Changed vs the C843 snapshot | 2 |
| Missing | 0 |

So exactly two files differ from what C843 executed.

## 2. The two changed files

| Path | C843 snapshot sha256 | C843 bytes | Current sha256 | Current bytes | Delta |
| --- | --- | --- | --- | --- | --- |
| `../qfli_studio_core/lib/services/process_supervisor.dart` | `25ba430ce7c0a6e2740c506ce6b0319eeecd31c90a3dc20b53a005861d8f54a1` | 21248 | `095de8c17c66dc206fe170b3f99b7447d8660f183085ecb338f97484ff0e5bfc` | 21796 | +548 B |
| `test/owned_preview_resource_broker_test.dart` | `6f41b71218caf10d5dc4ceea5d112475d562a9827e944fd7600db4a091d8a913` | 19454 | `ffb4e6ec0bbb532374bc5c25e3a04dc7eee558fd13d8e83f0edfc39151acc3f8` | 19030 | −424 B |

Every other snapshot entry, including `lib/services/owned_preview_resource_broker.dart`
at `56fd917c…` and `lib/services/owned_preview_policy.dart` at `9f0319af…`, still
matches its C843 hash.

The broker under test was **not** touched. Only the test that exercises it was.

## 3. Change A: process_supervisor.dart

- Current mtime `2026-10-26T05:54:43.952Z`, which is 172.407 s after C851 and
  81.558 s after C852.
- This is the change C852 declared when it reopened `process_supervisor.dart`
  alone. The timing line up.
- Subject: the Windows cancel path that seq 846 described, where `stdin.close()`
  precedes `taskkill /T`.
- Status: current, and stale for any future binding, as C852 already stated.

I did not review the new body. Its content is outside this measurement.

## 4. Change B: owned_preview_resource_broker_test.dart

- Current mtime `2026-10-26T06:07:26.514Z`, which is 934.969 s after C851 and
  762.562 s after change A. This edit came long after the release.
- Not tracked by git (`git ls-files` reports no match; `git status` reports
  `?? test/owned_preview_resource_broker_test.dart`). There is no committed
  predecessor to diff against.
- The file is the only copy on disk. A recursive search of both
  `D:/MyNewProjects/qfli_web` and `D:/MyNewProjects/qfli_studio_core` for
  `owned_preview_resource_broker_test.dart` returns one hit: this file. The C843
  body is therefore **not recoverable** from the tree.

Recorded size change: 19454 B to 19030 B, so −424 B. Against the 580 lines I
recorded for `6f41b712…` in this session, the live file measures 568 lines, which
is −12 lines. The stated figure was 13 lines. I cannot re-measure the old file,
so I record the measured delta as −12 lines and −424 B and note the one-line
discrepancy rather than adopt either number as confirmed.

### The removed oracle

The live file contains **zero** occurrences of `.done`, `disconnect`,
`invalidHttpResponse` or `HttpResponse`. So the `HttpResponse.done` disconnection
oracle no longer exists in the current tree. That part of the statement checks out
by token absence.

The live `serve()` helper carries a comment that fits the change:

```dart
} catch (_) {
  // Negative fixtures deliberately observe cancellation by the broker.
```

The live deadline test at lines 449-476:

```dart
      final result = await broker
          .fetch('${broker.origin}/slow')
          .timeout(const Duration(seconds: 1));
      expect(result.statusCode, 504);
      expectPolicy(result);
      expect(broker.activeRequests, 0);
      expect(broker.retainedBytes, 0);
      final recovered = await broker.fetch('${broker.origin}/after-timeout');
```

It still wraps the fetch in a one-second timeout and still expects 504. Only the
server-side disconnection oracle was dropped.

### What the removal does to the assertion

The C843 failure text was:

```
TimeoutException after 0:00:01.000000: Future not completed
  dart:async  _startMicrotaskLoop
```

That message is produced by any `Future.timeout` that expires. The old body
plausibly held two such one-second timeouts: one on `broker.fetch(...)` and one on
the `done` oracle's completer. The stack shows only `dart:async` frames, so it does
not name the subject. With the old body gone, the subject cannot be recovered.

Two readings fit the same text, and they point in opposite directions:

- **Reading 1.** The expiry was the `done` oracle. Then the broker did deliver, the
  oracle was the bad part, and this edit addresses the C843 failure.
- **Reading 2.** The expiry was `broker.fetch(...)`. Then the broker never settled
  its future, and since `owned_preview_resource_broker.dart` is unchanged at
  `56fd917c…`, this edit changes nothing about the failure.

The available evidence does not choose between them.

## 5. Consequence for the frozen C843 audit

Section 5 of `web-c843-evidence-pi5-20261026.md` reads the timeout as the broker
failing to settle, and offers the mechanism that `_perform`'s `finally` never
resumes. That reading now sits under Reading 2 above and is no longer supported by
the record. I am recording the doubt against my own earlier text rather than
leaving it standing.

What survives unchanged in that audit: the gate was FAIL, the counter reached
`+320 -1`, the failing test name, the verbatim error, and the resource accounting
in section 4. What is now unqualified is the causal reading in its section 5.

Classification, stated plainly:

- The C843 failure is **not fixed and not refuted**.
- The edit is **UNRUN**. No gate conclusion may be drawn from it.
- The last executed evidence about the deadline path remains the C843 timeout.

## 6. What is stale, and for what

| Binding | Status |
| --- | --- |
| C843 `source-before.json` / `source-after.json` (`062cc4c4…`, byte identical) | Still valid as the record of what C843 executed. Not a current-tree claim |
| C843 executed test hash `6f41b712…` | Stale as a current-tree identity. Valid as C843's executed identity |
| C843 test line/byte counts | Stale. Superseded by the current `ffb4e6ec…` |
| Any future run input identity | Unbound. Needs its own pre-ACK snapshot |

The C843 pair is byte identical to itself, so no drift occurred inside the C843
window. The two changes in section 2 happened after that window closed. Nothing
here contradicts the earlier no-drift finding, and nothing here extends it.

## 7. Non-claims

- I did not run the edited test, the suite, or the broker.
- I did not review the new `process_supervisor.dart` body or the new test body.
- I did not establish which future the C843 timeout came from, because the old
  test body is not on disk and not in git.
- I did not confirm the 13-line figure. I measured −12 lines and −424 B and left
  the discrepancy open.
- I did not verify that the removal is correct engineering. I verified that the
  oracle's tokens are absent from the current file.
- I did not modify the frozen C843 audit, and I did not edit any product or source
  file.
- No acceptance criteria are invented.