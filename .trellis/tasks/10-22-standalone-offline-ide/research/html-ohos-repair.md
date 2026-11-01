# HTML 135 / 144 / 160 — OHOS ArkWeb repair

Owner scope: `scripts/curriculum/html_expansion.py` (lessons `html-example-135`,
`html-example-144`, `html-example-160` only) and the matching cases in
`scripts/html_expansion_assertions.mjs`, plus this research note. No aggregate
assets, `emit_content.py`, runner, Flutter, build, device or `hdc` work; no CDP
navigation (root grants that slot separately, after the CSS owner).

> Sections 1–6 record the first repair round (135, 144) from
> `research/ohos-481-initial.json`. Section 7 records the 160 repair from the
> fresh full-catalog run `research/ohos-481-final.json` (474 pass / 7 fail).

## 1. Input evidence

`research/ohos-481-initial.json` (root run):

* runtime `ohos-arkweb`, `browserVersion 144.0.7559.59`,
  OS `OpenHarmony-7.0.0.105` / API 26, device type `phone`,
  bundle `com.azurekiln.qfli.webforge`, module `entry_test`.
* catalog manifest sha256: examples `2d8f8c0a…`, tutorials `10e750b7…` (481/481).
* result: **443 pass / 38 fail**, 3985 checks. Of the 38 failures: **CSS 34**,
  **JavaScript 2**, **HTML 2** — the two HTML failures are exactly
  `html-example-135` and `html-example-144`.

### 1.1 `html-example-135` (picture / `<source media>`)

```
crop matches actual viewport media query  ok=false
  {"expectedWidth":300,"width":200,"wide":true,"sourceMatches":false}
currentSrc is the matching candidate       ok=false
probe selected crop                        ok=false
```

`wide` is `matchMedia('(min-width: 600px)').matches` = **true**, yet the engine
selected the `(min-width: 300px)` candidate (200 px wide) and
`currentSrc` was not the candidate the oracle derived from `matchMedia`.

### 1.2 `html-example-144` (declarative shadow DOM)

```
host border applied   ok=false
probe: host 边框=0.857143px
```

The `:host { border: 1px solid }` declaration **did** apply (the probe reads a
non-zero border), but the assertion demanded the literal string `1px`.

## 2. Diagnosis

### 2.1 Shared root cause: the documents declared no viewport meta

Both lessons shipped `<head><meta charset="utf-8"><title>…</title></head>` and no
`<meta name="viewport" content="width=device-width, initial-scale=1">`.

On a phone that means the **default mobile layout viewport**: 980 px wide, fitted
to the device by page scale. Two consequences:

1. `window.innerWidth` / `matchMedia(...)` report the **980 px layout viewport**,
   not the ~412 px device width.
2. ArkWeb 144 resolved `<picture><source media>` against the **device width**
   (≈412 px) — `(min-width: 600px)` false, `(min-width: 300px)` true → the 200 px
   candidate. That is why the report shows `wide: true` and `width: 200`
   simultaneously: two different viewports were consulted by the same document.

So this is **primarily a source (authoring) defect** — a responsive
art-direction lesson must declare its viewport — and only secondarily an
assertion problem, because the oracle derived its expectation from `matchMedia`
(the 980 px layout viewport) while the engine used another one.

### 2.2 `html-example-144`: a strict-value assertion, not a style failure

`:host { border: 1px solid #c8cdd4; padding: 8px }` definitely applied. The
computed value read back as `0.857143px` because the no-meta page is scaled to
fit the 980 px layout viewport into the device width (1 / 1.1666… = 0.857143),
and the length is reported through that scale. `=== '1px'` therefore encoded a
desktop-only assumption. On desktop Chromium the same document reports `1px`.

### 2.3 Host-Chromium reproduction boundary

Host Chromium (Playwright 1.64) at 412×915 with `isMobile: true` and **no**
viewport meta keeps the layout viewport at **980 px and selects the 300 px
candidate** (`innerWidth=981, wide=true, naturalWidth=300`). It is internally
spec-consistent, so ArkWeb's `matchMedia`-vs-`<source media>` divergence cannot
be reproduced on the host. What *is* reproducible — and what the fix targets — is
removing the precondition: with a viewport meta the layout viewport equals the
device width on every engine, so `matchMedia` and `<source media>` can no longer
disagree.

## 3. Changes made

### 3.1 `scripts/curriculum/html_expansion.py` (content, 2 lessons)

| id | change |
| --- | --- |
| 135 | added `<meta name="viewport" content="width=device-width, initial-scale=1">`; `explain` now teaches that `media` queries resolve against the layout viewport and that a missing viewport meta makes the layout viewport 980 px; `out` no longer claims a fixed `实际宽=300 / 命中宽屏=true`; pitfall 3 replaced (`source 的 srcset 也需要 data:` → the missing-viewport-meta trap) |
| 144 | added the same viewport meta; `explain`/`out`/pitfall 3 now state that `:host` lengths are page-scaled and must not be read as literal px |

Document bodies remain complete, self-contained and offline; no external URL was
introduced; `HTML_EXTRA` still has 60 entries and 60 unique bodies.

### 3.2 `scripts/html_expansion_assertions.mjs` (oracle, 2 cases)

**135** — engine assertions kept spec-correct (`naturalWidth` must equal the
candidate selected by the same media query the document declares, and
`currentSrc` must be that candidate); the third check was rewritten so the
lesson script is verified **independently of engine selection**:

```js
const probe = await text(page, '#state');
addCheck('probe reports the same crop as the DOM',
  probe.includes(`实际宽=${crop.width}`) && probe.includes(`命中宽屏=${crop.wide}`) &&
  probe.includes('source 数=2') && probe.includes('已加载=true'), probe);
```

Before, this check compared the probe against `crop.expectedWidth`, i.e. it
re-asserted the engine expectation; now it cross-checks two independent
computations (lesson JS vs. DOM read), so an engine-selection failure is reported
once (by the engine checks) and a script regression is reported separately.

**144** — the hardcoded `'1px'` was replaced with four concrete checks. The key
one measures an identical page-level `1px solid` border in the *same*
environment and requires exact equality (no tolerance, no skip):

```js
const parity = await page.evaluate(() => { /* div { border: 1px solid } → computed */ });
addCheck(':host border style is solid', host.borderStyle === 'solid', host.borderStyle);
addCheck(':host border width equals a page-level 1px border',
  host.width === parity.width && parity.style === 'solid', `${host.width} vs ${parity.width}`);
addCheck(':host padding applied', parseFloat(host.padding) > 0, host.padding);
addCheck(':host display is block', host.display === 'block', host.display);
addCheck('probe shadow state',
  probe.includes('shadowRoot=true') && probe.includes('分配节点=1') &&
  probe.includes('外部 h3 数=0') && probe.includes(`host 边框=${host.width}`), probe);
```

Why this is not tautological tolerance: `border-style: solid` cannot come from a
UA default (UA default is `none`, width `0px`), and the width must equal a
page-level `1px` border measured in the same document — under a scaled viewport
that is `0.857143px === 0.857143px`, under a 1:1 viewport `1px === 1px`. It still
fails if `:host` stops applying (width would be `0px`, style `none`) or if the
declaration changes to a different width.

## 4. Verification performed (host only, no device/CDP)

Static:

* `python -X utf8 -W error::SyntaxWarning` compile of `html_expansion.py`: clean.
* `HTML_EXTRA`: 60 entries, 60 unique bodies, both repaired documents complete,
  both carry the viewport meta.
* `node --check scripts/html_expansion_assertions.mjs`: exit 0.

Browser (`research/verify_html_135_144.mjs`, host Chromium, two contexts):

| context | id | result | checks | observed |
| --- | --- | --- | --- | --- |
| desktop 1280×720 | 135 | PASS | 8 | `innerWidth=1280, wide=true, naturalWidth=300` |
| desktop 1280×720 | 144 | PASS | 11 | host border `1px`, parity `1px` |
| phone 412×915, `isMobile`, dsf 2 | 135 | PASS | 8 | `innerWidth=412, wide=false, naturalWidth=200` (engine and `matchMedia` agree) |
| phone 412×915, `isMobile`, dsf 2 | 144 | PASS | 11 | host border `1px`, parity `1px` |

The phone context is the meaningful one: it is the first time these documents
report the device width as the layout viewport, i.e. the condition under which
ArkWeb's two viewports can no longer disagree.

### 4.1 Document hashes (for root's regeneration)

The pre-fix shipped catalog matched the OHOS report's `codeSha256` exactly, which
confirms the dump used for verification is faithful to the emitter:

| id | shipped (old, = report `codeSha256`) | after repair |
| --- | --- | --- |
| 135 | `7664269f00c6abf1e430a97d6ab12dbd5363cc76b644548203af0c3d7dcfe02c` | `1edb2be62891502d45a0067e7ea2b855bf9bfe7ca263ff9687d052db6c754e54` |
| 144 | `53bf8835bb7c3cbb5295d7893eb4048f71d7bd5aece647318ab8cb57a1913a8d` | `a8dfe62ca3dea43c50d82343c37d90dc96ec0aa0e47ab642f63ff3277440c9b5` |
| 160 | `9e5467cfdc97320890b53241fbc235fb6fae6af478efd291cdd3400230254b35` | `5a1d50bd45a45f6ceb9134cc976417b7a5e7bb7f0a36ced53c3051b87d52aae5` |

## 5. What root must do next

1. Regenerate `assets/content/examples.json` and `assets/content/tutorials.json`
   (emit is root-owned) — only ids 135 and 144 change; both are `language: html`,
   `type: html`, and their `sourceLessonId` lesson bodies change identically, so
   the lesson/example mapping stays intact. The tutorial entries
   (`html-tutorial-135/144` → `lessons[0].code`) embed the same body and change
   with them.
2. Re-run the OHOS catalog in the exclusive slot. Expected: both ids pass; the
   remaining 36 failures are CSS (34) and JavaScript (2), not HTML.
3. No change is needed in the runner, the OHOS harness or the device adapter.

## 6. Notes and residual risks

* **404 console noise is harness-wide, not content-specific.** 479 of 481
  examples log two `Failed to load resource … 404` console lines while
  `resourceErrors` is empty for every entry — an auxiliary fetch (favicon-style),
  not a shipped document asset. It should not be read as a content defect.
* **58 of the 60 expansion HTML documents still have no viewport meta.** This
  repair deliberately touched only the failing ids (135, 144, then 160). Any
  lesson whose assertions depend on viewport width (media queries, `matchMedia`,
  responsive `srcset`/`picture`, `vw` units) **or on `position: fixed` / popover /
  dialog geometry** carries the same ArkWeb divergence risk. If a later failure of
  that shape appears, the fix is the same: declare the viewport meta in the lesson,
  anchor top-layer UI explicitly, then keep the assertion spec-correct.
* CSS (34) and JavaScript (2) failures in the same run belong to the CSS owner
  and the JS owner respectively; nothing here overlaps them.
* No device, CDP, Flutter, build or `hdc` command was run for this repair; the
  OHOS confirmation still depends on root's exclusive slot.
* Task-local artifacts added: `verify_html_135_144.mjs` (two-context verifier,
takes ids as arguments), `diag_html_160_popover.mjs`, `negative_html_160.mjs`,
`show_html_case.mjs` (read-only case printer), `tmp_check_html.py`,
`tmp_check_attr.py`, `tmp_hash.py`. `fix_then_probes.mjs` remains unsafe and
unused (do not run).

## 7. Second round — `html-example-160` (fresh run `ohos-481-final.json`)

### 7.1 Evidence

`research/ohos-481-final.json`: `ohos-arkweb 144.0.7559.59`, **474 pass / 7 fail**,
4012 checks, `runId 1792685836647`. `html-example-160` is the only remaining HTML
failure; its record:

```
checks: 21, errors: []
failed: { "name": "page load/setup",
          "detail": "TimeoutError: locator.click: Timeout 3000ms exceeded." }
last passing check: help popover opens
```

The 18 checks before it all pass (table, status role, details group, empty-title
rejection with focus/aria-invalid, one row added, tfoot total, status
announcement, error cleared, popover opens). The `codeSha256`
`9e5467cf…` equals the pre-fix document, so the run used exactly the source
repaired here.

The thrown error is swallowed by the runner
(`run_examples.mjs:401`, `String(e).split('\n')[0]`), so only Playwright's first
line survived; the actionability sub-reason was discarded.

### 7.2 Root cause: the top-layer popover was outside the visual viewport

Same family as 135/144 — lesson 160 also shipped **no viewport meta**. Consequences
on the device:

1. layout viewport = 980 px while the device is ~412 px, page scale ≠ 1;
2. `[popover]`'s UA style is `position: fixed; inset: 0; margin: auto`, so the
   popover is centred on the **initial containing block** of the 980 px layout
   viewport — for a 302×98 box that is roughly `x≈340, y≈1040`;
3. the close button therefore sits near `y≈1104` in layout coordinates.

Host measurement of the same document at 412×915 (mobile emulation, no meta):
popover `{x:340, y:1040, w:302, h:98}`, close button `{x:355, y:1104}`, layout
width `981`, `visualViewport.scale 0.42` — i.e. Chromium shrink-to-fits the whole
980 px layout, so the visual viewport is also 980 CSS px wide and the button is
still *visible* (the click works on host).

ArkWeb does not shrink that far: lesson 144's `:host` border measured
`0.857143px` for `1px`, i.e. page scale `6/7 ≈ 0.857`. That makes the visual
viewport only `412/(6/7) ≈ 480 × 1068` CSS px, so the close button at `y≈1104`
falls **below the visual viewport**. Playwright cannot scroll a `position: fixed`
element into view, so `locator.click` retries until the 3000 ms timeout — the
exact first line in the report. It also explains the asymmetry: `#open-help` lives
in normal flow near the top of the document and clicked fine, while only the
in-popover button was unreachable.

Caveat: because the runner keeps only the first error line, this is the leading
and quantitatively consistent explanation, not a captured sub-reason. The fix
below removes the mechanism either way (layout viewport = visual viewport, and the
popover is explicitly anchored instead of relying on UA centring).

### 7.3 Changes (only my two files)

`scripts/curriculum/html_expansion.py` — lesson 160:

* added `<meta name="viewport" content="width=device-width, initial-scale=1">`;
* popover placement no longer depends on UA centring:
  `#help { inset: auto 12px 12px; margin: 0; max-width: calc(100vw - 24px); }`
  plus `#help:popover-open { display: block; }`;
* `explain` now teaches that popovers enter the top layer, that UA centring can
  push them off-screen when the viewport is scaled, and that `:popover-open`
  styles the open state; `out` documents both dismiss paths.

`scripts/html_expansion_assertions.mjs` — case 160, restructured so evidence is
never lost to a throw and the cause is named instead of a bare timeout:

```
open → 'help popover opens'
     → 'close button is reachable'   (visible box, inside visualViewport, elementFromPoint == close-help)
     → Escape → 'escape light-dismisses popover'      (real user path 1)
     → reopen → 'popover reopens'
     → click  → 'help popover closes'                 (real user path 2, popovertargetaction=hide)
```

No `force: true`, no synthetic `element.click()`, no skip, no widened tolerance:
the popover must genuinely be openable, reachable, light-dismissible and
button-closable. The reachability check records the geometry (box, visual
viewport, scale, hit-test target) so a future platform failure reports *why*.

### 7.4 Verification

Negative control first (`research/negative_html_160.mjs`) — current document with
the popover pushed to `inset: auto 12px -400px`, at 412×915 mobile emulation:

```
ok   help popover opens
FAIL close button is reachable | {"box":{"x":27,"y":1281,"w":43,"h":23},
     "view":{"left":0,"top":0,"w":412,"h":915},"scale":1,"insideViewport":false,"hit":null}
ok   escape light-dismisses popover
ok   popover reopens
threw: TimeoutError: locator.click: Timeout 3000ms exceeded.
```

That reproduces the ArkWeb signature (bare click timeout) while the new check
names the cause and the Escape path keeps working — the check discriminates and
is not tautological.

After the fix (`research/verify_html_135_144.mjs html-example-160`, host):

| context | 160 | checks | popover box | close button |
| --- | --- | --- | --- | --- |
| desktop 1280×720 | PASS | 20 | `{x:12,y:610,w:302,h:98}` | `{x:27,y:674,w:43,h:23}`, hit `BUTTON#close-help` |
| phone 412×915 `isMobile` dsf 2 | PASS | 20 | `{x:12,y:805,w:302,h:98}` | `{x:27,y:869}`, `scale=1`, inside viewport |

Full regression of the three repaired ids, both contexts: 135 `8/8`, 144 `11/11`,
160 `20/20` — all PASS. `node --check` clean; `HTML_EXTRA` still 60 entries with
60 unique bodies and 3 pitfalls each.

### 7.5 What root must do next

1. Regenerate **both** aggregates — `assets/content/examples.json`
   (`html-example-160`) **and** `assets/content/tutorials.json`
   (`html-tutorial-160` → `lessons[0].code`, which embeds the same body).
   Only 160 is stale: the shipped aggregates already carry the 135/144 repairs
   (`examples.json` `1edb2be6…`/`a8dfe62c…`, `tutorials.json` tutorial bodies
   identical), while `html-example-160` and `html-tutorial-160` still hold
   `9e5467cf…`. New hash for both: `5a1d50bd45a45f6ceb9134cc976417b7a5e7bb7f0a36ced53c3051b87d52aae5`.
2. Re-run the full 481 catalog in the exclusive slot. Expected: `html-example-160`
   passes; the residual failures (CSS / JavaScript) are not HTML.
3. Optional runner improvement (root-owned, not done here): keep more than the
   first line of a thrown error — `String(e).split('\n').slice(0, 3).join(' / ')`
   — so future interaction failures report the actionability sub-reason
   ("element is outside of the viewport", "intercepts pointer events", …)
   instead of only `Timeout 3000ms exceeded.`
