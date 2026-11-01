# JS real-OHOS repair: js-example-052 / js-example-053 / js-example-095

Sections 1–5 preserve the earlier worker's investigation and test revision.
Section 6 records the current integrated candidate; its real-click oracle
supersedes the earlier synthetic-click harness and its assertion counts.

Narrow scope of this worker:

- `scripts/js_example_assertions.mjs` (owned)
- `scripts/curriculum/js_data4.py` records `js-example-052` and `js-example-053` — **source
  fixes**, because those lessons themselves had the defect
- `scripts/curriculum/js_data5.py` record `js-example-095` — wording/generalisation only,
  the lesson behaviour was already correct
- this note

Not touched: runner, emitter, aggregates/assets, HTML/CSS content or oracles, Flutter,
build, `hdc`, device/CDP navigation. No assets regenerated.

## 1. Evidence from the real device run

Source: `.trellis/tasks/10-22-standalone-offline-ide/research/ohos-481-initial.json`
(runtime `ohos-arkweb`, ArkWeb 144.0.7559.59, OpenHarmony-7.0.0.105 API 26, 481 executed,
443 passed / 38 failed, 3985 checks, 0 mapping issues).

Only two failures are JavaScript:

| id | failing check | detail |
| --- | --- | --- |
| `js-example-052` | `js interaction #out` | `expect /定位失败\|不支持定位\|,/ got ""` |
| `js-example-095` | `js dom #out` | `expect 在线 got "离线"` |

Both records report `blockedRequests: []` and `resourceErrors: []`, and their console
contains **only** the two universal harness 404 lines (478 of 481 entries show the same
pair, so it is a harness artifact, not product traffic; 052 has no `log:` line at all).

## 2. Root causes — and why one is a product defect, the other an oracle defect

### `js-example-052` — the product really did hang (source fix required)

The lesson called `navigator.geolocation.getCurrentPosition(success, error)` and relied on
one of the two callbacks. On ArkWeb offline the API exists (`navigator.geolocation` is
truthy, so the capability check passes) but **neither callback ever fires**: there is no
permission decision to make and no device fix to deliver. The `<output>` therefore stayed
empty forever — exactly the `""` seen on device, with no `log:` line because the lesson
only logged nothing at all.

That is a genuine defect in the lesson, not a test problem: a page whose only feedback is
"wait forever" is broken product behaviour. The fix is in the lesson:

- a bounded watchdog (`TIMEOUT_MS = 800`) plus `clearTimeout` once anything settles;
- a single `finish()` guarded by a `settled` flag, so the first outcome wins and the UI can
  never be overwritten afterwards;
- an explicit in-progress render (`定位中`) so the transition is observable;
- `err.code === 1` mapped to the concrete cause `用户拒绝` instead of a raw message;
- `getCurrentPosition` also receives `{ timeout, maximumAge }`, and the call is wrapped in
  `try/catch` for synchronous throws.

Resulting contract: the UI always leaves `定位中` and lands on exactly one documented
terminal state — `纬度,经度`, `不支持定位`, `定位失败：<原因>`, or `定位超时`. No external
request is involved (geolocation is a device API), so the product stays offline.

### `js-example-095` — the oracle assumed the host was online

The lesson is correct: it renders `navigator.onLine ? '在线' : '离线'` and re-renders on
`online`/`offline`. On an offline emulator `navigator.onLine === false`, so `离线` is the
**right** answer; the oracle's hardcoded `out: '在线'` was a host-connectivity assumption
that only holds on a networked desktop browser.

The fix is in the oracle (expectation derived from live state), plus a small lesson
generalisation so the documented behaviour matches reality:

- `out`/`explain` now say the page shows the device's *current* real state and repaints on
  change, rather than promising `在线`;
- the render also logs `online=<bool>`, making the observed state explicit in transcripts.

The oracle no longer guesses: it reads `navigator.onLine` from the page and asserts the
label matches, then **forces** both transitions and asserts the repaint, then restores the
real device value and re-asserts. That proves the listeners are wired without depending on
host connectivity at all.

## 3. Oracle changes (`scripts/js_example_assertions.mjs`)

Removed the two stale host-assumption entries from the generic tables
(`INTERACTION_DOM['js-example-052']`, `DOM['js-example-095']`) and replaced them with
explicit per-id blocks.

### `js-example-052`

| check | what it proves |
| --- | --- |
| `action button present` | `#loc` exists and was clicked |
| `geolocation settles within budget` | `#out` leaves `""`/`定位中` inside a bounded wait |
| `terminal state is a documented outcome` | output matches **exactly one** of `^-?\d+\.\d{2},-?\d+\.\d{2}$`, `^不支持定位$`, `^定位超时$`, `^定位失败：.+$` |
| `not stuck in progress` | final output is neither empty nor `定位中` |

The coordinate branch is shape-checked (`纬度,经度` with two decimals) and the failure
branch must name a concrete cause — this is not a "non-empty" or prefix test, and no skip
or fallback exists. Bounded polling (≤4s in 100 ms steps) only waits for the lesson's own
800 ms budget on slower devices; it cannot make a hanging page pass.

### `js-example-095`

| check | what it proves |
| --- | --- |
| `initial label matches navigator.onLine` | rendering mirrors the *live* device state |
| `offline event repaints to 离线` | `offline` listener actually re-renders |
| `online event repaints to 在线` | `online` listener actually re-renders |
| `restores real device state` | the forced override is undone and the label returns to truth |

The override is a page-local `Object.defineProperty(navigator, 'onLine', …)` used only to
drive the listeners; it is always restored, so no later assertion can see a lie.

## 4. Verification (host Chromium, no device — per scope)

A throwaway harness outside the repository reproduced the runner's js path: single-document
loopback server, non-loopback request blocker, generic `driveInteraction` stimulus first,
then `assertJs(page, ctx)`. Scenarios:

| id | scenario | result |
| --- | --- | --- |
| 052 | normal (real permission prompt → deny) | `定位失败：用户拒绝`, 4/4 |
| 052 | **`geo-hang`** — API present, callbacks never fire (the ArkWeb offline case) | `定位超时`, 4/4 |
| 052 | `geo-denied` — immediate `code: 1` error | `定位失败：用户拒绝`, 4/4 |
| 095 | normal (`onLine = true`) | starts `在线`, flips `离线` → `在线`, restored, 4/4 |
| 095 | **offline (`onLine = false`)** — the emulator case | starts `离线`, flips `离线` → `在线`, restored `离线`, 4/4 |

All scenarios pass. Under the *old* oracle + old source the `geo-hang` scenario reproduces
the device failure (`#out === ""`), confirming the harness models the real defect.

Additional checks:

- `node --check scripts/js_example_assertions.mjs` clean; 0 occurrences of `ok: true`
  (no tautological assertions).
- All 101 baseline ids still referenced by the oracle; `052`/`053`/`095` removed from the
  generic tables only.
- Emitter invariants for the three edited records: exactly one `webforge-check` marker,
  marker before the structural body end, lesson body equal to the example body modulo the
  marker, no external references (`fetch`/`XHR`/`src=http`/`@import`/`import(`).
- `python -X utf8 scripts/test_emit_content.py` still passes: 481 topics
  (160/160/161), 481 distinct bodies, single tokenizer-aware marker, no asset writes.
- `assets/content/*.json` untouched — root regenerates.

## 4b. Second pass: `js-example-053` (clipboard), 2026-10-22

### Evidence

`research/ohos-481-final.json` (same ArkWeb 144.0.7559.59): 474 passed / 7 failed,
4012 checks. `js-example-053` is the only remaining JS failure:

```
js interaction #out js-example-053
  expect /内容：|读取失败/ got ""
```

`console` holds only the two universal harness 404 lines (no `log:` line),
`blockedRequests: []`, `resourceErrors: []`, and the other two assertions
(`check marker present`, `exactly one semantic oracle`) pass.

### Root cause — same class of platform defect as 052

An empty `#out` with no console output means the click handler ran but never reached a
write. The lesson did `out.textContent = '内容：' + (await navigator.clipboard.readText())`:
on ArkWeb the promise **never settles** (no permission prompt, no activation plumbing), so
the `await` suspends forever and nothing is ever written. The blanket `try/catch` cannot
help, because a promise that never rejects never reaches `catch`.

This is a genuine product defect: an `async` handler whose only feedback is `await` on a
promise that may never settle leaves the UI blank indefinitely. The fix belongs in the
lesson.

### Source fix (`js_data4.py`, record `js-example-053`)

Mirrors the 052 pattern — bounded settled state with immediate feedback:

- `out.textContent = '读取中'` before any await, so the click is always acknowledged;
- `watchdog = setTimeout(() => finish('读取超时'), 800)` bounds the wait;
- a single `finish()` guarded by `settled` plus `clearTimeout`, so the first outcome wins
  and a late platform callback cannot overwrite it;
- `finish('内容：' + await readText())` for success;
- the capability check now calls `finish('读取失败：不支持读取')` instead of `throw`;
- `catch` renders `读取失败：<message>` for rejection (with a non-`Error` fallback);
- every settled outcome is `console.log`-ed, so transcripts show the terminal state.

Terminal contract: `内容：<text>` | `读取失败：<reason>` | `读取失败：不支持读取` |
`读取超时`. `读取中` is transient only. No external request; clipboard is a device API.

`out`/`explain`/`pit` were rewritten to state the hang risk explicitly, matching 052.

### Oracle fix (`scripts/js_example_assertions.mjs`)

Removed `INTERACTION_DOM['js-example-053']` (the loose `/内容：|读取失败/` regex that
trivially matched any failure string) and added a four-scenario block:

| # | scenario | stub | asserted outcome |
| --- | --- | --- | --- |
| 1 | success | `readText` → `'WEBFORGE-CLIP'` | `读取中` on click, then exactly `内容：WEBFORGE-CLIP` |
| 2 | denial | rejects `NotAllowedError('Document is not focused')` | `读取中` first, then exactly `读取失败：Document is not focused` |
| 3 | API absent | `navigator.clipboard === undefined` | exactly `读取失败：不支持读取` |
| 4 | **hang** | `readText` returns a never-settling promise | stays `读取中`, then exactly `读取超时` |

Plus `action button present`, `stub installed`, `never stuck in progress`,
`settled outcome is logged and matches the DOM`, and `restores the platform clipboard`
— 12 checks in total.

**The oracle never reads the real user clipboard.** Each scenario installs a page-local
`Object.defineProperty(navigator, 'clipboard', …)` stub *before* clicking (falling back to
`Navigator.prototype` if the instance is not configurable). The original descriptor is
saved first and restored afterwards, so the page is not left mutated. A grep of the block
finds zero real `readText()` calls — the only textual occurrence is a comment.

Scenario 4 is the exact device condition: only the watchdog can leave `读取中` there, so
the assertion fails on any lesson that awaits the promise directly.

### Verification

Same throwaway host harness (loopback, non-loopback blocked, runner's generic stimulus
first, then `assertJs`). New source: **12/12, stable across 3 consecutive runs**.
Negative control — the old lesson text run against the new oracle — fails exactly the 6
fix-encoding checks and passes only the 6 that merely validate stub mechanics:

```
BAD  shows 读取中 synchronously on click
got "读取失败：Failed to execute 'readText' on 'Clipboard': Read permission denied."
BAD  denial path shows 读取中 first            got "内容：WEBFORGE-CLIP"
BAD  hanging read settles to 读取超时          got "读取失败：不支持读取"
BAD  hanging read stays in progress …          got "读取失败：不支持读取"
BAD  never stuck in progress                   #out="读取失败：不支持读取"
BAD  settled outcome is logged and matches …   logs=[]
```

Two details worth keeping:

- The synchronous `page.evaluate(... click() ...)` peek reliably observes `读取中` even
  when the stub resolves in a microtask, because `evaluate` returns before microtasks
  drain. Verified directly rather than assumed.
- An earlier draft asserted `读取中` on the *API-absent* path too. That was wrong and was
  removed: the absent branch has no `await` before the capability check, so it settles
  within the same task and the transient is genuinely unobservable. Asserting it would
  have encoded an implementation detail (that the check must be async-gapped).

## 5. For root

- Regenerate assets, then re-run the 481-entry ArkWeb passes. All three JS ids now assert
  real product behaviour with more coverage than before: 052 → 4 checks, 053 → 12,
  095 → 4 (was 1 generic check each in the baseline tables).
- The 6 non-JS failures in `ohos-481-final.json` (`html-example-160`, `css-example-044`,
  `css-example-050`, `css-example-114`, `css-example-116`, `css-example-120`) are outside
  this worker's scope — another owner holds HTML/CSS.
- Residual risk worth watching on device: if ArkWeb ever makes `navigator.geolocation` or
  `navigator.clipboard.readText()` throw synchronously instead of hanging, both lessons'
  `try/catch` cover it and the oracles accept the `失败：…` outcome — no new host
  assumption is introduced.

## 6. Integrated real-click and concurrent-read repair — 2026-10-23

### Current gesture ownership and JS052 checks

`scripts/js_example_assertions.mjs` now exports `SELF_DRIVEN_IDS` for JS052 and
JS053. `scripts/run_examples.mjs` skips its generic driver for those entries,
so each oracle owns its actual gesture. This prevents an earlier generic
clipboard read or an overlapping geolocation watchdog from contaminating the
scenario under test.

JS052 now requires an initially empty output, a present action button and a
real reachable `locator.click()` whose actionability errors propagate. After
the gesture, it waits for a bounded documented terminal state and requires the
matching console line (`unsupported` for the unsupported branch). The earlier
implementation swallowed click failures and could accept a prefilled timeout;
its old “button present” check did not prove a completed gesture. The current
block fixes that oracle gap. It does not introduce controlled geolocation
permission/callback scenarios in this batch.

### Current JS053 real-click oracle

Success, denial, API absence and never-settling reads all use real
`locator('#paste').click()` gestures. The oracle replaces only the page-local
platform API response and runs the authored handler unchanged. It records
`读取中` at the controlled `readText` boundary and combines the post-click
snapshot with the controlled reply in one renderer evaluation, reducing the
extra CDP requests competing with the lesson's 800 ms watchdog. Exact supplied
success text, actual denial reason, unsupported feedback, timeout and late
completion are asserted separately.

Two additional real clicks exercise overlapping reads: the latest result must
survive the older read's timeout and later completion. These browser assertions
are authored candidates, not a newly executed browser pass. The oracle's
`finally` restores and compares both original own/prototype clipboard
descriptors, including originally absent properties. It never reads the user's
actual clipboard; controlled scenarios prove handler feedback and lifecycle,
not platform clipboard permission or native clipboard access.

### Authored concurrent-read fix

The previous per-click `settled` flag handled late completion within one read,
but could not stop an older pending read from overwriting a newer successful
read. The authored JS053 source now assigns a monotonic generation to every
click. Each operation still settles once and clears its own watchdog; only
the latest generation may write the visible result or terminal console line.
This retains bounded feedback while preventing older timeout/success/error
callbacks from replacing current progress or results. Root regenerated the
paired example/tutorial assets from this source.

### Executed lightweight positive and negative controls

`scripts/test_clipboard_lifecycle.mjs` executes the actual generated JS053
inline script unchanged in a Node VM, with a minimal DOM/event boundary,
controlled platform Promises and deterministic timers. Assertions inspect
observable output/logging, not generation-counter names or implementation
text.

- Current generated catalog: `node --test scripts/test_clipboard_lifecycle.mjs`
  → **15 passed, 0 failed**, exit 0.
- Preserved pre-generation-guard catalog:
  `node scripts/test_clipboard_lifecycle.mjs --catalog <old examples.json>`
  → **9 passed, 6 failed**, expected exit 1. Failures are the older timeout,
  older success/error during latest progress, older success/error after latest
  success, and stale timeout while the newest read remains pending.

The suite also verifies immediate feedback, exact success/denial/unsupported
states, missing API/method, synchronous platform failure, bounded hang and
late success/error after timeout. Commands, the preserved snapshot location
and review details are in `clipboard-oracle-review.md`.

No fresh browser, Flutter or OHOS execution occurred for this candidate during
this update. The latest exhaustive native result remains **474/481 passed,
7 failed, 4012 assertions** in `ohos-481-final.json`; those seven failures
remain recorded. New desktop/mobile runs, fresh staging/HAP inspection and a
coordinated native rerun are still required. The earlier desktop481 pass and
synthetic harness cannot certify these later assets or real-click assertions.
