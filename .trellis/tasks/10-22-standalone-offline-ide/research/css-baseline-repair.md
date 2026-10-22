# Baseline CSS oracle repair — record

Owner: this session (exclusive ownership of `scripts/web_markup_assertions.mjs`
`CSS_CASES` + this task's CSS research reports).
Scope: repair genuine defects in the shipped 100 CSS oracles, strengthen weak /
tautological checks, and remove every host-viewport assumption. No aggregate
generator, asset, runner, main, core or platform file was modified.

---

## 0. Reviewer follow-up: `page.viewportSize().width` at line 1358

Status: **already repaired before this follow-up, and re-verified now.**

`css-example-002` used to read the width directly:

```js
const viewport = page.viewportSize().width;   // throws when the context is host-owned
```

A host-owned context (the OHOS / ArkWeb persistent context the native runner
reuses, created with `viewport: null`) makes `viewportSize()` return `null`, so
that line threw `TypeError: Cannot read properties of null (reading 'width')`
and the whole example failed.

It now goes through the shared helper:

```js
const viewport = await viewportWidth(page);
```

The grep below is the current state of the whole oracle module. The only
remaining `viewportSize()` calls are inside the helpers themselves, and each one
is null-guarded:

```
$ Select-String scripts/web_markup_assertions.mjs -Pattern 'viewportSize'
66,68,71,74 : comments explaining the constraint
80          : const size = page.viewportSize();          // inside viewportWidth()
91          : const original = page.viewportSize();      // inside atViewport()
```

There are **zero** unconditional `page.viewportSize().width` reads left in the
file. The same audit was applied to the authored module: its `pinViewport` helper
used to call `setViewportSize()` unconditionally, which also throws in a
host-owned context; it is now tolerant and reports whether the pin applied.

### The helpers (single source of truth)

| Helper | Behaviour |
| --- | --- |
| `viewportWidth(page)` | returns `page.viewportSize().width` when Playwright owns the viewport, otherwise `window.innerWidth`. Media queries evaluate against exactly this width. |
| `atViewport(page, w, h, fn)` | tries `setViewportSize()`, runs `fn` and restores. Returns **null** when the window is host-owned, so callers fall back to asserting the branch the real width implies instead of pretending to be desktop. |
| `gridColumns(page, sel)` | counts only the grid tracks that carry content, so `repeat(auto-fit, …)`'s collapsed `0px` tracks are not miscounted as columns. |
| `pinViewport(page, w, h)` (authored module) | best-effort pin; never throws, and every case that uses it now derives its expected values from the width it actually has. |

---

## 1. Genuine defects repaired (wrong at real viewports)

| id | lesson | was | now |
| --- | --- | --- | --- |
| 011 | media queries | asserted "three columns at 1280px" only | walks the real ladder: **599→1, 600→2, 899→2, 900→3** columns, plus equal `1fr` tracks and the row count implied by the column count |
| 044 | 65ch measure | asserted `maxWidth < viewport`, which is **false at phone widths** (609.9 > 412) | measures `65ch` independently in the same engine, asserts `max-width == 65ch`, `width == min(65ch, available)`, `line-height == 27.2px`, and asserts centring only when there is slack |
| 051 | holy grail | asserted three columns unconditionally, but the page collapses to one column at ≤640px | asserts the wide state (1fr/3fr/1fr proportions, sidebars flanking main, header spanning) **and** the narrow state (1 column, `head/left/main/right/foot` stacked, all at the same x, increasing y) |
| 064 | responsive nav | asserted only the desktop state, never the hamburger | asserts wide (burger hidden, menu flex, items on one row) **and** drives the real toggle at 412px: click the ☰ label → menu revealed and items stacked → click again → hidden, checking the checkbox state each way |

## 2. Weak / tautological checks strengthened

| id | was | now |
| --- | --- | --- |
| 041 | `position !== null` (always true) and `content` "is empty" | reads the real `::after` style: empty content, `position: absolute`, `top/right: 0`, four `8px` borders, top+right red `#ea4335`, bottom+left transparent |
| 029 | only checked that a `@media print` rule was parsed | switches the page to print with `emulateMedia({media:'print'})` and asserts nav + button are `display: none`, body paints white, `.card` is `break-inside: avoid`; then restores screen media and asserts the nav comes back |
| 090 | `padding === '8px' \|\| '16px'` and `h2 === 18 \|\| 24` (either branch passes anywhere) | asserts **both** sides of the 600px breakpoint: `--space`/`--title` values, the declarations that consume them, and that the breakpoint really changes the padding and heading size |
| 015 | `grid-template-columns !== 'none'` | counts real auto-fit tracks at 1280 (3) and 412 (2), asserts the cards wrap to a second row when narrow, every card ≥160px, all cards share one width, and the page never overflows |
| 036 | `box-shadow !== 'none'` | asserts the authored two-layer shadow (both layers, both offsets, both blurs, 8% black) and the exact `text-shadow` with a real downward offset |
| 035 | `opacity < 1` (accepts 0.99) | asserts `opacity === '0.5'`, `cursor: not-allowed`, hover shade `#1557b0`, and **real** `:active` (mouse held) sinking `matrix(1,0,0,1,0,1)`, plus the keyboard `:focus-visible` 3px `#8ab4f8` ring |
| 021 | `filter.includes('grayscale')` (accepts `grayscale(0.2)`) | asserts `grayscale(1) contrast(1.2)`, `blur(6px)`, the 40% white glass, and that the image really decodes |
| 050 | set `.checked` in JS and dispatched events | clicks the `<label>` like a user: box checks, slider turns `#1a73e8`, knob slides `matrix(1,0,0,1,22,0)`; a second click restores grey and `none` |

Two further cases were corrected because the new viewport sweep proved their
assertions were only true at one width:

- **130**: `60ch` was asserted as the literal `480px` at a pinned 960px viewport.
  It now measures `60ch` in the same engine and asserts `min(60ch, available)`.
- **157**: the wheel-chaining test assumed the fixed 260px scroller was on
  screen. It now delivers the wheel only when the scroller is inside the
  viewport, and otherwise asserts the two-axis `contain` contract.

---

## 3. Validation

Environment: Chromium **156.0.8078.4** (bundled Playwright 1.64.1). No Flutter,
no device execution — browser-side verification only. Nothing here claims OHOS
runtime execution.

### 3.1 Real runner (unmodified `scripts/run_examples.mjs`, real assets)

Root has since integrated both expansion modules, so the assets now hold 481
examples (160 CSS). All of the runs below use the **real runner against the
real generated assets**, not a harness.

| run | result |
| --- | --- |
| shipped 100 CSS baseline, 1280×720 | **100 / 100 pass, 836 assertions, 0 failures, 0 mapping issues** |
| full 160 CSS, 1280×720 desktop | **160 / 160 pass, 1503 assertions, 0 failures, 0 mapping issues** |
| full 160 CSS, 800×1180 tablet | **160 / 160 pass, 1503 assertions, 0 failures** |
| full 160 CSS, 412×915 phone | **160 / 160 pass, 1502 assertions, 0 failures** |
| full 160 CSS, 360×640 small phone | **160 / 160 pass, 1502 assertions, 0 failures** |

Reports: `runner-css-desktop.md`, `runner-css-160-desktop.md`,
`runner-css-160-800.md`, `runner-css-160-412.md`, `runner-css-160-360.md`.

Before this repair the 100-example desktop run reported 776 assertions; the
current 836 is added coverage, not removed checks.

### 3.1a Whole-catalog observation (not CSS)

`runner-full-481.md`: 481 examples, 469 pass, **12 fail — all
`html-example-*`**. No CSS example fails. The twelve are
109, 119, 122, 125, 126, 134, 135, 136, 137, 140, 141, 144 and belong to the
sibling HTML oracle module, which this session does not own.

### 3.2 Full CSS suite (100 baseline + 60 authored), desktop and mobile

Harness mirrors the runner: fresh context per example, the same injected
`#webforge-check` marker, external-request / page-error / broken-resource
policing.

| viewport | baseline 100 | full 160 |
| --- | --- | --- |
| 1280×720 desktop | 100/100, 436 assertions | 160/160, 803 assertions |
| 800×1180 tablet | 100/100, 436 | 160/160, 803 |
| 412×915 phone | 100/100, 435 | 160/160, 802 |
| 360×640 small phone | 100/100, 435 | 160/160, 802 |

### 3.3 Host-owned context (the OHOS condition)

Report: `css-host-viewport.md` / `css-host-viewport-all.md`.

- `--native` (`viewport: null`, real `viewportSize() === null`): **100/100**
  baseline and **160/160** full suite.
- Forced-throw proxy (`viewportSize()` → null **and** `setViewportSize()`
  throws, which is what a host-owned ArkWeb window does): **480/480 rows**
  (160 examples × {412, 800, 1280}) with **0 failures**, and every
  width-branching case provably took the `window.innerWidth` fallback instead of
  asserting desktop.

### 3.4 Mutation tests (assertions are not vacuous)

| report | mutations | detected |
| --- | --- | --- |
| `css-repair-mutation.md` (the 12 repaired baseline cases) | 36 | **36 / 36** |
| `css-expansion-mutation.md` (the 60 authored lessons) | 60 | **60 / 60** |

Each mutation is a single semantic edit: removed media query, moved breakpoint,
wrong colour/shadow/filter/offset, flipped toggle wiring, dropped `break-inside`,
variables that never switch, and so on. Every one turns at least one check red.

---

## 4. Changed surface

```
scripts/web_markup_assertions.mjs      viewport helpers + 12 CSS_CASES (+ case 002 width read)
scripts/css_expansion_assertions.mjs   pinViewport made host-safe; 119/124/128/130/157 derive from the real viewport
```

Untouched by design: `scripts/emit_content.py`, `scripts/run_examples.mjs`,
`assets/**`, `lib/**`, `ohos/**`, existing tests, and the sibling
`html_*` / `js_*` expansion modules owned by other workers.

## 5. Known open item (not mine to change)

The four baseline lessons still teach behaviour that only exists at some widths
and are now asserted correctly at all of them. `css-example-011`, `044`, `051`
and `064` remain unchanged as lesson content — only their oracles became
viewport-correct.
