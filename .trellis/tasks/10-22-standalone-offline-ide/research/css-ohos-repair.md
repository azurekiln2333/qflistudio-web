# CSS OHOS (ArkWeb 144) repair — classification and fixes

Task: `.trellis/tasks/10-22-standalone-offline-ide`
Ownership at time of work: `scripts/web_markup_assertions.mjs` (CSS cases only),
`scripts/css_expansion_assertions.mjs`, `scripts/curriculum/css_expansion.py`, research reports.

Status: **frozen**. Oracle and lesson-source fixes are complete and verified on the host;
the packaged catalog is stale until root regenerates it, and root's full desktop/mobile
481 run against the regenerated catalog is the final gate.

## 1. Baseline

First real ArkWeb run (`research/ohos-481-initial.json`):

| metric | value |
| --- | --- |
| examples | 481 |
| pass / fail | 443 / 38 |
| failures by language | css 34, html 2, javascript 2 |
| checks | 3985 |
| browser | Chromium/ArkWeb 144.0.7559.59 |
| runtime | ohos-arkweb, `viewportSize()` null (host-owned) |

This report covers the **34 CSS** failures only (HTML/JS belong to other workers).

Of those 34: **31 were oracle defects** and **3 were product defects in the lesson
source** (129, 144, 157).

## 2. Root cause 1 — sticky `:hover` on the reused native page (oracle bug, 5 cases)

The native runner reuses **one page** for the whole catalog. ArkWeb keeps a sticky
`:hover` on whatever element the pointer last landed on, so after the previous
example a "base state" read returned the `:hover` value:

* `035`: `.btn` read `rgb(21, 87, 176)` (the hover shade) instead of `rgb(26, 115, 232)`.
* `031`: the hovered `.box` had a 40px hover margin, breaking `margin-inline: 24px`.

Fix (both dispatchers, `assertMarkupExample` / `assertExpansionExample`):

```js
async function parkPointer(page) {
  try { await page.mouse.move(-1, -1); } catch {}
}
```

`move(-1, -1)` is outside the viewport and clears `:hover` completely (verified:
no element matches `:hover` afterwards; `move(0, 0)` leaves `<html>` hovered).
Cases that assert hover drive the pointer themselves, so parking first is safe.

**Resolved by this fix: 031, 044, 114, 116, 120.**

## 3. Root cause 2 — integer literals vs device fractional geometry (oracle bug, 21 cases)

Two legitimate sources of fractional geometry on a real device:

1. **Sub-pixel layout noise.** The native page lays out at a 980px layout viewport
   with `devicePixelRatio` 3.5 and `visualViewport.scale` ≈ 0.37347, so a 200px box
   measures `200.00001525878906`.
2. **Device-pixel border snapping.** ArkWeb snaps borders to whole device pixels at
   dpr 3.5: an authored `1px` border measures **0.857143px** and an authored `3px`
   border measures **2.857143px** (verified on 147 and 035).

Largest observed deviation is **0.286px**, so a single tight tolerance absorbs both
while still failing on a real 1px error, a missing border, or a wrong size:

```js
const GEOMETRY_TOLERANCE = 0.5;
const near = (actual, expected, tol = GEOMETRY_TOLERANCE) =>
  Number.isFinite(actual) && Math.abs(actual - expected) <= tol;
```

Applied to: 122, 123, 124, 126, 127, 131, 132, 133, 135, 136, 137, 138, 139, 144
(box width), 145 (equal-width check), 147 (border width + container width), 150,
154, 155, 158 — plus `035` (outline width) and `041` in the baseline module.

## 4. Root cause 3 — OS-font-dependent literals (oracle bug, 4 cases)

Hard-coded pixel widths measured on desktop Chromium cannot hold on a device font.
Each was replaced with a **font-independent** assertion, not a skip.

### 4.1 Measurement primitive

Neither `canvas.measureText` nor a detached probe span is usable: both resolve the
font family through their own fallback chain and measured **133px** where the
element itself occupied **145.86px**. `Range` geometry uses the same text stack that
laid the element out, so it matches exactly:

```js
const rangeTextWidths = (page, sel) => /* full width + per-word widths via Range */
```

### 4.2 Per case

| case | old expectation | new assertion |
| --- | --- | --- |
| 125 `max-content` | `≈145.859px` | equals the Range width of the whole line (±1px) |
| 125 `min-content` | `≈59.109px` | equals the widest single word's Range width (±1px) |
| 145 digit run | `≈56.3px` | equals the Range width of the same four digits (±1px) |
| 148 trimmed box | `= 30.25px` | height lands in the cap band (0.55em–0.85em) **and** trimming removes > 0.3em |
| 041 badge | `width = 128` | `width = text Range width + 16px + 16px` (±1px) + `display: inline-block` |

`125` `fit-content` (→ 120px) and `145` "1111 vs 8888 equal" keep their exact
meaning; they only needed the tolerance (1e-6 float difference).

### 4.3 141 `text-emphasis`

The mark is painted outside the em box. Under the lesson's roomy 36px line-height it
fits inside the leading on desktop (36 → 36) but pushes the box out on ArkWeb
(36 → 41.43), so neither "grows" nor "same" is portable. The oracle now proves the
semantics font-independently:

* the plain (no-emphasis) line box is exactly the authored 36px line-height;
* with emphasis the line box never shrinks and never costs a whole extra line;
* **re-measured under `line-height: 1`** (where the mark cannot fit) the line box
  must grow — measured 20 → 28. That is the real proof the mark sits outside the
  text box, and it holds on both engines.

## 5. Root cause 4 — engine-dependent behaviour: fixed in the lesson source

Each of these was originally an oracle-side capability branch. The branch shape root
rejected (deriving the branch from the outcome of the assertion it guards) was
removed from 144 and 157 by **fixing the lesson source** so the teaching contract
holds on every engine and can be asserted unconditionally. 156 is the one remaining
capability branch, and it is driven by an independent control.

| case | observation | resolution |
| --- | --- | --- |
| 144 `hyphens: auto` | declared (`hyphens: auto`, `lang="en"`) but **no dictionary** on ArkWeb, so the word never broke: span 234px in a 121.7px box (1 line box). The lesson's own `out` claimed both boxes contained the word — false on that engine | **product fix**: lesson now pairs `hyphens: auto` with `overflow-wrap: break-word` (`hyphens: auto; overflow-wrap: break-word`), so containment holds everywhere and `out` was rewritten to describe the fallback. Oracle asserts containment **unconditionally**; the hyphenation probe only decides whether an *extra* multi-line-box assertion applies |
| 157 wheel chaining | `.tall` was a fixed 1600px and the scroller sat at `left: 300px`: on a tall host viewport (1990px) the page had **no scroll range**, and on a narrow one the scroller was off-screen, so the contract was untestable. ArkWeb also did not honour wheel overscroll containment | **product fix**: `.tall { height: 300vh }` and the scroller moved to `inset: 40px 8px` so both preconditions hold on any viewport; a **bounded wheel-boundary fallback** was added (`preventDefault()` only at the top/bottom boundary, `{ passive: false }`, inner scrolling untouched). Oracle asserts the page-not-scroll contract **unconditionally**, ahead of which it proves the wheel is really delivered (stimulus control) |
| 156 `scrollbar-gutter: stable` | **overlay scrollbars** on ArkWeb, so `stable` reserved 0 and the box stayed 200px; this host Chromium reserves 15px (and, notably, reserves a gutter for `stable` even while painting overlay scrollbars) | capability branch retained — see §5.1 |
| 153 spinner | bounding box 56.5px, not 40px, because the element is **rotating** (40 × √2 = 56.57) | asserts computed `width`/`height` 32px + 4px border ⇒ 40px across, instead of a bounding box of a rotated box |
| 129 container units | authored `2.5cqw` of a 200px container = 5px, but the engine enforces a **minimum font size of 8px** (all of 4px–8px render at 9.43px) | **product fix**: lesson changed to `10cqi` / `5cqw` so every size is ≥ 10px (400px → 40/20px, 200px → 20/10px). Teaching unchanged, clamp no longer in play |

### 5.1 The one capability branch (156) and why it is not self-justifying

The branch is decided by two measurements, neither taken from the element under test:

* `stableGutterReservation()` — how much this engine reserves for
  `scrollbar-gutter: stable`, read with `clientWidth` on a **fresh 137px element**;
* `plainScrollbarWidth()` — `offsetWidth - clientWidth` on a plain
  `overflow-y: scroll` element (no gutter property), i.e. the scrollbar model
  itself, where 0 means overlay.

The two are deliberately **not** equated: this host was measured painting overlay
scrollbars (plain probe 0) while still reserving 15px for `stable`. The case then
compares `#short`'s own reservation (`200 - clientWidth`) against the independently
measured reservation — no hard-coded 15px — so the branch cannot be satisfied by
whatever happened.

An earlier revision measured the probe with `getComputedStyle(probe).width`; that was
replaced (see `research/css-assertion-branch-review.md`) because it used the feature
under test as its own probe and left the no-reservation branch as dead code.

**Branch liveness is proven**, not assumed (`research/css-156-branch-liveness.mjs`):

| scenario | expected | observed |
| --- | --- | --- |
| unmodified lesson on this engine | reservation branch runs, case passes | pass, 8 checks |
| `scrollbar-width: none` (emulates ArkWeb: declaration kept, nothing reserved) | no-reservation branch runs, case **passes** | pass, 7 checks |
| same neutralisation **+ lesson rule removed** | case **fails** | fail on `stable gutter is declared` |

The unconditional no-layout-shift invariant (`#short` `clientWidth` unchanged when a
scrollbar appears) is kept and holds on every engine.

## 6. Results

### 6.1 Host suite (`css-suite-verify.mjs`, from the curriculum source)

| viewport | result |
| --- | --- |
| 1280×720 | **160/160**, 824 assertions |
| 800×600 | **160/160**, 824 assertions |
| 412×800 | **160/160**, 823 assertions |
| 360×640 | **160/160**, 823 assertions |
| native, host-owned viewport (`viewportSize()` null, 412×915 window) | **160/160**, 823 assertions |

Host-viewport proxy (`css-host-viewport.mjs --all --expansion`): **480 rows, 0
failures**, 15 width-branching rows all taking the width fallback.

### 6.2 Mutation strength

| harness | result |
| --- | --- |
| `css-expansion-mutation.mjs` (60 cases, 63 mutations) | **63 / 63 detected, 0 undetected** |
| `css-repair-mutation.mjs` (repaired baseline cases) | **36 / 36 detected, 0 undetected** |

The 129, 144 and 157 mutations were extended so each *half* of a repaired contract is
required independently:

* 144 — `overflow-wrap: anywhere` removal **and** `overflow-wrap: break-word` removal;
* 157 — `overscroll-behavior: contain` removal, the `preventDefault()` call removal,
  and `{ passive: false }` removal;
* 156 — `scrollbar-gutter: stable` removal, plus the branch-liveness harness above.

### 6.3 Native ArkWeb 144 (real packaged bundle, filtered, partial report)

`research/runner-native-34-final.md` — the 34 original failures:

| run | result |
| --- | --- |
| initial full 481 | 443 pass / 38 fail (34 css) |
| after `parkPointer` | 5 of 34 fixed |
| after all oracle fixes | **33 / 34 pass** |

Residual at that point: **129** only, because the packaged asset still contained the
old lesson CSS (`5cqi` / `2.5cqw`). The lesson source is now corrected, so 129 clears
with the regenerated catalog. **144 and 157 also need the regenerated catalog** — their
source fixes (`overflow-wrap: break-word`, `300vh` + `inset` + wheel fallback) are not
in the packaged bundle yet.

No further device run was made: the native grant was revoked, and root's full
desktop/mobile 481 run against the regenerated catalog is the final gate.

## 7. Classification summary

**Actual product defects: 3**

| case | defect |
| --- | --- |
| 129 | lesson used `2.5cqw` → 5px, clamped by the engine's 8px minimum font size; the rendered sizes contradicted the documented `out` |
| 144 | lesson claimed both boxes contained the long word, but `hyphens: auto` without a dictionary overflows; no `overflow-wrap` fallback was declared |
| 157 | the lesson was untestable on a tall or narrow viewport (`.tall` fixed at 1600px, scroller at `left: 300px`) and had no fallback where the engine ignores wheel containment |

**Oracle defects: 31**

| class | count | cases |
| --- | --- | --- |
| sticky `:hover` on the reused page | 5 | 031, 044, 114, 116, 120 |
| integer literals vs fractional/snapped geometry | 21 | 122, 123, 124, 126, 127, 131, 132, 133, 135, 136, 137, 138, 139, 144, 145, 147, 150, 154, 155, 158, 035 |
| OS-font-dependent literals | 4 | 125, 145, 148, 041 |
| wrong measurement model for the widget | 1 | 153 |
| capability branch without an independent control | 1 | 156 |

(Some cases appear in more than one class; the totals above count the primary cause.
144 and 156 were originally mis-classified here as "platform behaviour, no product
fault". That was wrong: 144 was a product defect (fixed in source) and 156 was an
oracle defect (the probe measured the feature under test and left a branch dead).)

## 8. Files changed

* `scripts/web_markup_assertions.mjs` — `parkPointer`, `near`/`GEOMETRY_TOLERANCE`,
  `rangeTextWidths`; case fixes 035, 041.
* `scripts/css_expansion_assertions.mjs` — `parkPointer`, `near`,
  `rangeTextWidths`, `hyphenatesWords`, `stableGutterReservation`,
  `plainScrollbarWidth`; case fixes 122–158, plus the module header rules rewritten
  to describe the final semantics (see §8.1).
* `scripts/curriculum/css_expansion.py` — product fixes for 129 (`10cqi` / `5cqw` +
  `out`/`explain`), 144 (`overflow-wrap: break-word` + `out`), 157 (`300vh`,
  `inset: 40px 8px`, bounded wheel fallback + `explain`/`out`/`pit`).

## 8.1 Header rules corrected

The module header previously claimed "literal expectations only — no `||` fallbacks"
and "the oracle never injects styles or markup into the page". Both contradicted what
the final code legitimately does. The header now states the actual contract:

* expectations are literal, **or** derived from an independent control the case cannot
  influence;
* a capability branch is allowed **only** with an independent probe (different
  element, different size, different content), never inferred from the assertion it
  guards;
* a probe may append and remove a temporary element, and a case may toggle a class or
  inline style to re-measure, but **no assertion is reported against a mutated lesson
  state**: probe elements are removed, overrides are restored, and the lesson's own
  rules are never overwritten for the measurement the case reports.


## 9. Follow-up round — fresh native full 481 (`ohos-481-final.json`)

After the catalog was regenerated, the full native 481 run reported **474 pass / 7
fail**. Five were CSS (mine); `html-example-160` and `js-example-053` belong to other
workers.

### 9.1 Strict-branch leftovers (4 cases)

044, 114, 116 and 120 still carried `===` comparisons on integer geometry — the same
class already fixed elsewhere, missed because an earlier multi-edit batch failed part
way through. Converted to the existing bounded `near()`:

| case | failing assertion | observed |
| --- | --- | --- |
| 044 | `at a narrow width the article fills the available width` | 551.143 vs 551 |
| 114 | `first/second/third equal item is 200px wide`, `equal items sit at 200px steps` | 200.00001525878906, 199.99996948242188, 400.0000305175781 |
| 116 | `container height stays 200px`, `second row starts at 50px (40 + 10 gap)` | 200 float, 50.000003814697266 |
| 120 | `first row item is 40px tall`, `second/third implicit row starts at 48px/96px` | 40 float, 48.000003814697266, 96.00000762939453 |

`044`'s `max-width really is 65ch` was also switched from an inline `Math.abs(...) < 0.5`
to `near()` for consistency. `116`'s `i1.y !== i4.y` became
`Math.abs(i1.y - i4.y) > 1`, so the "different row" intent survives the tolerance.

### 9.2 050 — first click swallowed (oracle stimulus defect)

Symptom from the native run: after the first click the box was still unchecked and
grey; the *second* click produced checked + blue. The lesson CSS is correct
(`.switch input:checked + .slider`), and the second click proves the label wiring
works — so the first click was lost, not mis-wired.

Cause: the dispatcher parks the pointer off-document (`mouse.move(-1, -1)`) before
every case, and an engine that hit-tests before processing the pointer move can drop
the click issued immediately afterwards.

Fix (no force, no writing `.checked`):

1. **stimulus control** — move the pointer to the switch centre, let it settle, and
   assert `document.elementFromPoint` really resolves inside `.switch`, so a dropped
   click can never be confused with a bad pointer target;
2. **wait for the real outcome** — poll `input.checked` (bounded 2 s) instead of
   assuming a fixed delay, then let the 0.2 s transition settle before reading the
   colours;
3. the same for the click back, polling until it is really unchecked.

If a click never toggles, `waitFor` times out and the case fails — the assertion is
not softened. The three 050 mutations (`checked state never turns blue`, `knob does
not slide`, `knob slides too far`) are still detected.

Host Chromium does not reproduce the dropped click, so
`research/css-050-click-stability.mjs` cannot demonstrate the ArkWeb behaviour; it
verifies the case is stable both with the pointer parked (dispatcher behaviour) and
untouched (control). The native re-run is the proof.

### 9.3 Follow-up results

| gate | result |
| --- | --- |
| host suite 1280x720 | **160/160**, 825 assertions |
| host suite 412x800 | **160/160**, 824 assertions |
| native host-owned viewport | **160/160**, 824 assertions |
| `css-expansion-mutation.mjs` | **63/63 detected** |
| `css-repair-mutation.mjs` | **36/36 detected** |
| targeted 044/050/114/116/120 at 412x800 | **5/5**, 39 assertions |

Frozen again after this round. No device, CDP or Flutter command was issued; root's
aggregate run remains the gate.

### 9.4 050 — literal self-assertion removed

The case ended with a check whose inputs were constants:

```js
const geometry = await page.evaluate(() => ({ w: 48, knob: 20, left: 3, travel: 22 }));
addCheck('knob travel keeps the knob inside the track',
  geometry.left + geometry.knob + geometry.travel + geometry.left === geometry.w, ...);
```

Every number was supplied by the oracle, so the comparison was true on any page —
a self-assertion, not a measurement. Replaced with geometry read from the engine
**while the switch is still checked** (captured before the toggle back):

* `track` — `.slider` bounding width;
* `trackBorder` — its computed left/right border widths;
* `knob` — `::before` computed width;
* `left` — `::before` computed left inset;
* `travel` — parsed out of the **observed** checked `transform` matrix.

Two bounded assertions replace the one vacuous check:

| assertion | meaning |
| --- | --- |
| `the checked knob travels exactly the free space in the track` | `left + knob + travel + left == track - borders` (±1px) |
| `the knob travel is a real movement, not zero` | `travel > knob / 2` |

Falsifiability verified on a host harness (`research/css-050-geometry-mutation.mjs`):

| mutation | failing checks |
| --- | --- |
| unmodified | 0 (measured `{track:48, trackBorder:[0,0], knob:20, left:3, travel:22}`) |
| travel → 10px | 3, including both new geometry checks |
| travel → 30px | 2, including the free-space check (knob overflows) |
| track → 60px | 2, including the free-space check (gap left) |

`css-repair-mutation.mjs` still detects all three original 050 mutations, and the new
free-space check now fails alongside them.

### 9.5 Final state after this round

| gate | result |
| --- | --- |
| host suite 1280x720 | **160/160**, 826 assertions |
| host suite 412x800 | **160/160**, 825 assertions |
| native host-owned viewport | **160/160**, 825 assertions |
| `css-repair-mutation.mjs` | **36/36 detected** |
| `css-expansion-mutation.mjs` | **63/63 detected** |
| 050 geometry mutations | **3/3 detected**, unmodified passes |

Frozen. Only 050 changed in this round; no other CSS case was touched, and no device,
CDP or Flutter command was issued.
