# JS052/053 oracle review — 2026-10-23

Scope: current `scripts/js_example_assertions.mjs` JS052/053 blocks and
`SELF_DRIVEN_IDS`, `scripts/run_examples.mjs` dispatch, and the authored JS053
document in `scripts/curriculum/js_data4.py`. Read-only review of product/oracle
sources; this note is the only file written by the reviewer. No browser,
Flutter, build, device or network process was started during C's exclusive
resource window.

## Findings

### 1. JS052 can claim a successful action after its real click failed

At review time, `clicked` is set from selector count, the subsequent
`click(...).catch(() => {})` discards actionability rejection, and every other
check reads only the terminal text. The check named “not stuck in progress”
therefore does not prove the transition its comment claims.

A lightweight Node invocation of the actual `assertJs` function supplied a
page stub with one button, a rejected click, and an already-present
`定位超时`. All four JS052 checks returned `ok: true`, including detail
`#loc clicked`. This is an oracle control-flow counterexample, not browser or
OHOS evidence. The authored current page starts empty, so the counterexample
does not claim the current unchanged document already fails; it identifies an
accepted mutation that removes the intended interaction.

Root acknowledged this finding and owns the fix: require the initial empty
state, propagate a failed real click, and require a documented terminal
outcome logged after that gesture. A controlled four-branch geolocation
rewrite is not required for this batch.

### 2. JS053 settle-once is local to one click; overlapping reads can overwrite a newer result

The authored handler creates `settled` and `watchdog` inside each click. A
second click starts an independent read while the first is pending. If the
second read completes and then the first watchdog fires, the older operation
replaces the newer result with `读取超时`. The current oracle exercises its four
scenarios sequentially, after each previous operation has settled, so it does
not cover this interaction.

The current emitted authored `<script>` was executed unchanged in a small
Node VM with a DOM/event boundary stub and deterministic timer callbacks:

1. Invoke the registered handler twice, leaving the first read pending.
2. Resolve the second read with `SECOND`; observed `内容：SECOND`.
3. Invoke the first registered watchdog; observed `读取超时`, with both terminal
   messages logged.

This proves the handler's cross-click race, not native click/permission
behavior. A narrow remedy is to disable repeat activation while a read is
pending and re-enable on settlement, or use an operation generation so stale
callbacks cannot update the current output. If adopted, add one overlap case
to the real-click oracle. This is a distinct small product behavior gap;
root decides whether it belongs in this candidate batch.

### 3. JS053's 800 ms watchdog can race multiple post-click CDP round trips

Success and denial use a real click, then `calls()` and `readOut()` as separate
CDP requests, and only then another request resolves/rejects the deferred
platform response. On a heavily loaded native target the authored 800 ms
watchdog can legitimately expire between these requests, producing a false
failure of the success/denial scenario. The timeout branch also samples
progress only after a click and two remote calls. This is a static timing
hazard; no current browser failure is asserted.

Keep the real locator gesture and authored clock. Consider recording the
authored progress value at the controlled `readText` boundary (or a page-local
observer installed before the real click), and combine the post-click
snapshot/controlled reply in one renderer evaluation. This reduces the
oracle's contribution to the 800 ms race while still proving that the handler
rendered progress before reading. Persist timestamps and the observed phase
when a failure occurs. Avoid increasing the product watchdog solely to hide
test transport latency, or replacing the real click with DOM `.click()`.

## Reviewed behavior with no concrete defect found

- `SELF_DRIVEN_IDS` contains exactly JS052/053; runner dispatch skips generic
  driving for those IDs before calling their baseline oracle. This prevents
  an uncontrolled clipboard pre-read and a competing second watchdog.
- All four JS053 scenarios call real `locator('#paste').click()`. Success,
  denial and hang use deferred API replies; absence uses `undefined`. Exact
  output and one/zero-call checks are independently meaningful.
- The late-success check exercises the authored same-operation `settled`
  guard. Removing that guard would replace the timeout text with the late
  supplied text and fail the oracle.
- Clipboard own and immediate-prototype descriptors are captured before
  mutation. `finally` restores the originals, including deletion when the
  property originally did not exist, then compares all descriptor fields.
  The prototype fallback fails visibly if a non-configurable own property
  prevents control; it does not silently use the real clipboard. No concrete
  descriptor-restoration leak was found in the reviewed paths.
- Optional chaining, Promises, accessor descriptors and the locator API are
  consistent with the already-used Chromium/ArkWeb runner features. Only an
  actual current ArkWeb run can establish these scenarios on the native
  target; this review provides no new native acceptance claim.
- The runner's setup failure now preserves several nonempty error lines,
  which should retain actionability details.

## Lightweight checks

`node --check scripts/js_example_assertions.mjs` and
`node --check scripts/run_examples.mjs` completed successfully. The Node
counterexamples above ran without browser processes or source modification.
The next authorized browser window should run JS052/053 first, then the full
desktop/mobile catalogs, followed by a fresh archive and coordinated native
run. Prior native 474/481 evidence does not certify this candidate.

## Follow-up deterministic lifecycle regression

Added `scripts/test_clipboard_lifecycle.mjs`, which loads the actual generated
JS053 document from the catalog, extracts its authored inline script, and
executes it unchanged with a minimal DOM/event boundary, controlled platform
Promises and a deterministic clock. It asserts observable output/logging and
does not inspect a generation counter or implementation text. These tests
provide script lifecycle evidence; real button actionability, browser
permissions and ArkWeb execution remain separate gates.

Coverage includes immediate progress, exact success/error/unsupported output,
synchronous platform failure, bounded hang, late success/error after timeout,
and older success/error/timeout while the newest read is pending or already
successful. All six overlap regressions assert that stale operations cannot
replace current feedback or append misleading terminal logs.

After root's authored latest-request fix and asset regeneration:

```powershell
node --test scripts/test_clipboard_lifecycle.mjs
```

Result: **15 passed, 0 failed** (exit 0).

The preserved pre-fix catalog was also executed directly:

```powershell
$clipboardOldCatalog = Join-Path $env:TEMP 'qfli-web-examples-before-clipboard-generation.json'
node scripts/test_clipboard_lifecycle.mjs --catalog $clipboardOldCatalog
```

Result: **9 passed, 6 failed** (expected exit 1). Failures are exactly the
older timeout, older success/error during latest progress, older success/error
after the newest success, and stale timeout while the newest request is still
pending. This negative control establishes that the tests catch the original
cross-click defect. The old snapshot was preserved.
