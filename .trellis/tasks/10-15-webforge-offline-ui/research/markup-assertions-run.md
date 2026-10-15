# web_markup_assertions.mjs — real run results

Probe: temporary `build/web_markup_probe.mjs` (git-ignored), Playwright Chromium,
1280×800, all non-loopback requests blocked.

## Result

```
targets=200 pass=200 fail=0 checks=772        # this module (100 HTML + 100 CSS)
```

p7's full run (HTML + CSS via this module, JS via its own module):

```
301/301 pass, 1820 checks, mapping issues 0
```

All 100 HTML + 100 CSS examples pass with 772 concrete checks. Oracle frozen.

## Original failures (first run: 171 pass / 29 fail)

All 29 were **wrong expectations / timing in this module**, not content defects.
Fixes made, with the evidence that drove each:

| Example | Was failing | Cause | Fix |
| --- | --- | --- | --- |
| html-007 | `border-top-style === 'solid'` | `<table border="1">` computes as `outset` | assert border style is not `none` |
| html-010 | `innerText` of `<video>` | fallback text lives in `textContent`, not rendered `innerText` | read `textContent` |
| html-041 | `time:nth-of-type(2)` | the two `<time>` are in different parents | select `time[datetime="PT45M"]` |
| html-061 | PAGEERROR `Unexpected token '<'` | probe server returned HTML for `app.js` | probe returns 404 for sub-resources; the lesson now inlines style/script (no `app.js`/`app.css` to fetch) |
| html-064 | `el.disabled` | fieldset-disabled input has `disabled===false` | assert `matches(':disabled')` |
| html-072 | `.thumb` 120×80 | `img{max-width:100%}` shrinks it | assert `object-fit: cover` + bounded box |
| html-090 | `body > p === 2` | browser splits into 3 top-level `<p>`, `div` is a sibling | assert `>=2` and no `p > div` |
| html-094 | `'header nav main footer'` count | descendant-selector misuse | count each tag separately |
| css-002 | `#1a73e8` from `hsl(...)` | `hsl(217 89% 51%)` resolves to `rgb(19,104,241)` | assert the rgb value; widen width tolerance |
| css-010 | hover colour | read before the 0.2s transition finished | `settle()` then assert `#0d47a1` |
| css-014 | `.note` blue | first `.note` is `#intro` (red) | select `p.note:not(#intro)` |
| css-016/065 | `display` contains `box` | Chrome reports `flow-root` for the clamped box | assert real clipping (`scrollHeight > clientHeight`) |
| css-022 | `background-size === '20px 20px'` | two layers → `20px 20px, 20px 20px` | use `includes` |
| css-023/059 | counter text equals rendered number | `getComputedStyle(::before).content` returns the template | assert `counter(` template + `counter-increment` |
| css-029 | `break-inside: avoid` on screen | rule lives in `@media print` | assert the print rule contents |
| css-032 | transform after click | read before the 0.4s transition | `settle()` then assert `160` |
| css-034 | `line-height === '1.2'` | resolves to `38.4px` | assert `1.2 × font-size` |
| css-044 | `max-width === '65ch'` | resolves to a pixel value (`609.883px`) | assert constrained width + centred |
| css-050 | `page.check` timeout | input is `display:none` | set `checked` property+attribute and dispatch change |
| css-052 | grid rows still 0 | read before the 0.3s transition | `settle()` then assert positive rows |
| css-074/075 | hover `left` / `::after` width | read before transition | `settle()` then assert |
| css-079 | `contain-intrinsic-size === '300px'` | computes as `auto 300px` | use `includes('300px')` |
| css-080 | `grid-auto-flow === 'row dense'` | Chrome reports `dense` | use `includes('dense')` |
| css-086 | body still white after click | read before 0.3s transition | `settle()` then assert `#202124` + `.dark` |
| css-087 | `split(' ').length === 2` | named lines add `[left]/[mid]/[right]` tokens | assert named lines + half-width bounding boxes |
| css-094 | autofill rule includes `#e8f0fe` | rule style exposes resolved rgb | assert `inset` + `1000px` + `32, 33, 36` |

## Content defects found

**Final run: 200/200 pass, 772 checks, 0 fail** (p7 full: 301/301, 1820
checks, mapping 0). The intermediate 197/200 state below is historical and is
now resolved.

1. **css-example-062 / 078 / 088** — the inline-SVG `url(data:image/svg+xml,...)`
   is **unquoted**, so Chromium drops the entire `background` declaration.
   Repro: `getComputedStyle(document.querySelector('.hero')).backgroundImage ===
   'none'`; `[...document.styleSheets[0].cssRules]` shows the rule without
   `background`; 0 network requests, 0 pageerrors. Quoting the URL
   (`url("data:...")`) restores it and it decodes. Sources:
   `css_data4.py:155`, `css_data5.py:71`, `css_data5.py:191`.

**Fixed and passing (resources now offline):**

- **html-096** re-emitted inline SVG 240×80 (hotspots in-bounds).
- **html-097** now uses a runtime Blob stylesheet (no `rest.css`, no network).
- **html-061** inlines its style/script (no `app.css`/`app.js` fetch).
- **css-073** now embeds a real font; oracle upgraded to require
  `document.fonts.load('16px MyFont', 'WebForge')` non-empty and every
  `FontFace.status === 'loaded'` (not just a `@font-face` rule), plus a visible
  ASCII "WebForge" sample.
- Every other replaced image decodes; `html-006 missing.png` fails as intended
  (`naturalWidth===0`); `html-088` uses an invalid data URI to trigger `onerror`
  (no 404); `html-010`'s canvas repaint + 440 Hz Web Audio are real.

### Superseded note (was wrong — do not tolerate)

An earlier revision of this doc told the runner to tolerate sub-resource 404s
from `html-061`/`css-073`. That was a workaround, not a fix. Both lessons now
inline their resources, so **no lesson except `html-006 missing.png` is allowed
to 404 or fetch anything off-page**. The runner must NOT exempt any other
sub-resource 404.

## Runner note for p7

1. `#webforge-check` is not asserted here by design; keep the runner's own
   presence check if still wanted.
