# CSS capability-branch review — css_expansion_assertions.mjs

Read-only critique for **root to relay to CSSPi**. I did not write code, oracles, or assertions,
and ran no CDP/browser/device command.

Final reviewed revision: `scripts/css_expansion_assertions.mjs`, 91,033 bytes, mtime
2026-10-22 21:02:20 (css-156 fix, frozen). Earlier revisions reviewed: 20:15:30 → 20:22:12 →
20:23:56. Line numbers below are from the **21:02:20** revision.

Scope: runtime capability branches, judged against the class of defect root rejected in css-157
(an outcome-derived branch that cannot fail).

---

## 1. Verdict summary (final)

| Case | Branch pattern | Verdict |
| --- | --- | --- |
| css-156 scrollbar-gutter | measured reservation + independent scrollbar-model control | **Fixed — my reported bug is resolved** |
| css-144 hyphenation | unconditional containment + independent control | **Correct** |
| css-157 overscroll | unconditional containment + bounded fallback probe | **Correct** |
| css-148 text-box-trim | no branch; bounded font-metric band | **Correct** |

---

## 2. css-156 — reported bug RESOLVED (was: helper measured the wrong property)

### 2.1 What I originally reported

`hasOverlayScrollbars()` computed `100 - parseFloat(getComputedStyle(probe).width)` and returned
`reserved < 1`, and the branch keyed off that boolean.

I reported two things. **One was correct, one was wrong**, and I am correcting the record here
because the evidence contradicts my stated mechanism:

- **CORRECT — the branch conflated two different engine states.** An engine that *ignores*
  `scrollbar-gutter` entirely and an engine that paints *overlay* scrollbars both produced
  `reserved < 1`, so both took the "overlay" path. On an engine that ignores the property, the
  case passed vacuously — the lesson's actual claim was never verified.
- **WRONG — I claimed `getComputedStyle().width` can never change, so the helper "always returned
  true".** That is false, and the recorded runs disprove it. `scrollbar-gutter: stable` *does*
  reduce the used `width` on Chromium: `browser-481-desktop.json` and `browser-481-mobile.json`
  both record css-156's `stable reserves 15px even without overflow :: 185px` as **PASS**. If
  computed `width` were immovable, that assertion could never have passed on any engine. The
  helper therefore worked correctly on classic-scrollbar Chromium and only mis-classified the
  ArkWeb-class engine (which reported `200px`). My mechanism claim was overstated; the
  *mis-classification* claim was the real defect. Both are recorded so the finding is not
  misremembered as broader than it was.

### 2.2 What the final revision does — and why it resolves the bug

`hasOverlayScrollbars` is **gone**. It is replaced by two helpers that measure different things
separately:

```js
// :139-149  how much this engine reserves for `scrollbar-gutter: stable`
const stableGutterReservation = (page) => page.evaluate(() => {
  const probe = document.createElement('div');
  probe.style.cssText =
    'position:absolute;left:-9999px;width:137px;height:20px;overflow-y:auto;scrollbar-gutter:stable';
  probe.textContent = 'x';
  document.body.appendChild(probe);
  const reserved = 137 - probe.clientWidth;      // clientWidth, not computed width
  probe.remove();
  return reserved;
});

// :156-165  the engine's scrollbar model, with no scrollbar-gutter involved
const plainScrollbarWidth = (page) => page.evaluate(() => {
  const probe = document.createElement('div');
  probe.style.cssText = 'position:absolute;left:-9999px;width:100px;height:40px;overflow-y:scroll';
  probe.innerHTML = '<div style="height:200px"></div>';
  document.body.appendChild(probe);
  const reserved = probe.offsetWidth - probe.clientWidth;   // box vs client area
  probe.remove();
  return reserved;
});
```

Three things are now right, and each maps to a defect I raised:

1. **Measurement uses the client area** (`137 - clientWidth`, `offsetWidth - clientWidth`), which
   is where a scrollbar or gutter is actually taken from. This is robust even on a hypothetical
   engine that reserves a gutter without shrinking the `width` property.
2. **The capability is measured independently of the feature it gates.** `plainScrollbarWidth`
   uses a plain `overflow-y: scroll` element with no `scrollbar-gutter`, so the scrollbar model is
   no longer inferred from the property under test. This is the specific correction to the
   backwards justification in the old comment (which had claimed a plain probe "reports 0 on
   engines that still reserve a classic gutter for `stable`"). The new comment at `:129-137`
   states the correct relationship instead: the two quantities are measured separately and *may
   legitimately disagree*, with the observed build cited.
3. **The branch no longer keys off a boolean derived from one probe.** It keys off the measured
   reservation itself:

```js
// :1104-1118
const reserved = await stableGutterReservation(page);
const scrollbar = await plainScrollbarWidth(page);
const shortReserved = 200 - shift.before.short;

if (reserved === 0) {
  addCheck('this engine reserves nothing for the stable gutter',
    shortReserved === 0 && (await computed(page, '#short', 'width')) === '200px', ...);
} else {
  addCheck('the stable box reserves exactly what this engine reserves',
    shortReserved === reserved, ...);
  addCheck('the reserved gutter comes out of the declared 200px width',
    near(parseFloat(await computed(page, '#short', 'width')), 200 - reserved), ...);
}
```

`shortReserved` is derived from the **subject's own `clientWidth`** (`shift.before.short`),
measured before overflow is introduced, and is then compared against the **independent 137px
probe**. Two separate measurements that can disagree — so the check is falsifiable, not
self-confirming. The hard-coded `15px` is gone; the expected value is derived from the engine.

### 2.3 Branch liveness — three scenarios, all live

| Scenario | `reserved` | Behaviour | Live? |
| --- | --- | --- | --- |
| Classic scrollbars, gutter supported | 15 (desktop Chromium) | `else` arm: `shortReserved === 15 === reserved`, width ≈ 185 | **Yes** — this is what desktop/mobile runs report (`185px` PASS) |
| Overlay scrollbars | 0 | `if` arm: `shortReserved === 0`, width 200 | **Yes** — overlay engines take this arm |
| Engine ignores `scrollbar-gutter` | 0 | `if` arm passes the width part, **but** the unconditional no-shift check fails if that engine paints classic scrollbars | **Yes, fail-closed** |

Both arms are therefore reachable in practice, proven by the two recorded runs disagreeing
(`185px` on desktop/mobile vs `200px` on ArkWeb). The dead-branch defect I reported is gone.

### 2.4 Unconditional no-shift invariant — the strongest check, kept

```js
// :1086-1095
const shift = await page.evaluate(() => { /* clientWidth before, force 400px overflow, after */ });
addCheck('the stable box does not move when a scrollbar appears',
  shift.after.short === shift.before.short, `${shift.before.short} -> ${shift.after.short}`);
```

This is asserted **unconditionally**, on `clientWidth`, and it is the real guarantee of
`scrollbar-gutter: stable`. It is also what closes my "vacuous pass" concern: on an engine that
ignores the property *and* paints classic scrollbars, adding overflow changes `clientWidth`, so
this check fails. Such an engine can no longer reach a green result. Only an engine where nothing
takes space at all (genuine overlay) passes the `reserved === 0` arm, and on that engine the
lesson genuinely has no observable difference — which is honest rather than vacuous.

### 2.5 One portability caveat (not a defect, no action needed)

`:1117` compares `computed('#short','width')` against `200 - reserved`. That equality holds on
both engines measured (Chromium shrinks `width` for a reserved gutter). A hypothetical engine that
reserves the gutter in the client area but keeps the reported `width` at 200px would fail this one
check while the `clientWidth`-based checks at `:1095`/`:1116` still pass. I mention it only so a
future failure there is recognised as an engine quirk rather than a regression. There is no
evidence either measured engine behaves that way, so no change is warranted.

---

## 3. Branches that are correct — no action

### css-144 hyphenation (`:882-905`) — correct

Containment is asserted **unconditionally**:

```js
const hyphen = await box(page, '.hyphen');
addCheck('hyphenated word also stays inside the box', hyphen.width <= 120, ...);
```

The capability probe only decides *how* the word broke, and it runs on a **different element with
a different word** (`hyphenatesWords()`: own 40px host, own `lang="en"`, own word
`extraordinarily`). The branch cannot be decided by the assertion it guards. This matches root's
instruction: unconditional containment, with the source supplying the fallback
(`.hyphen { hyphens: auto; overflow-wrap: break-word; }`, `css_expansion.py:1718`).

### css-157 overscroll (`:1121-1147` region) — correct

Asserts containment unconditionally, adds a **stimulus control** independent of the feature, and
probes the bounded fallback directly:

- page is long enough to scroll (precondition, unconditional)
- scroller fully inside viewport (pointer-reachability precondition)
- "the wheel really scrolls the inner scroller" — proves the gesture is delivered *before*
  asserting anything about chaining
- page holds still while the inner scroller still has room
- bounded-fallback probe via synthetic `WheelEvent`: cancels at end, cancels at start, **does not**
  cancel inside
- real gesture after the fallback still scrolls

This is the shape root asked for, with the fallback verified bounded in both directions.

### css-148 text-box-trim (`:942-957`) — correct

No capability branch. The former hardcoded `30.25px` is now a band:

```js
// :954
trimHeight >= 0.55 * fontSize && trimHeight <= 0.85 * fontSize   // 22–34px at 40px
```

A font metric legitimately varies by font, so a band is correct rather than a weakening, and it
stays falsifiable: a no-op trim remains at the full 1.2em (48px), well outside the band. The
differential check at `:955` (`plainHeight - trimHeight > 0.3 * fontSize`) is independent. The
observed ArkWeb value (28px) lands inside the band, which is the right outcome for a varying
metric.

---

## 4. Corrections to my own earlier review (audit trail)

Two concerns were raised against the 20:15:30 revision and do not apply to the final one:

- I had noted that css-144's `else` branch asserted the word *overflows*, contradicting the
  regenerated source's `overflow-wrap: break-word` fallback. The final revision asserts containment
  unconditionally and has no such `else`. **Withdrawn.**
- I had noted that css-156's overlay arm asserted a bare `computed('#short','width') === '200px'`,
  indistinguishable from a no-op. The final revision adds the unconditional no-shift invariant
  (`:1095`), derives `shortReserved` from `clientWidth`, and compares against an independent probe.
  **Superseded.**

And one correction to the *substance* of my css-156 report, stated plainly because it matters for
how the finding is remembered: **my claim that `getComputedStyle().width` can never change was
wrong** — the recorded desktop and mobile runs show `185px`, which is only possible if the
reserved gutter does reduce the used `width`. The defect was the *mis-classification* of
"ignores the property" as "overlay scrollbars", not an always-true boolean. The fix addresses the
mis-classification, which was the substantive issue.

---

## 5. Boundary note for root

This review covers **assertion quality only**. It does not report whether cases pass on device:
the packaged catalogs were still the stale pre-fix content at the time of my earlier passes
(`examples.json` sha256 `2d8f8c0a…eeb1c`, identical in all four copies and inside the inspected
HAP). css-156 needs no content change (its source was never touched), so its assertions are
self-contained; css-144's conclusions assume the regenerated catalog ships. Full-481 integration
is root's run to report, not mine.
