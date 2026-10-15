# Technical design

## Principle

Every lesson document must render identically offline. Classify each reference:

| Kind | Example | Action |
|---|---|---|
| **Fetch** (renders a resource) | `<img src>`, CSS `url()`, `og:image`, `onerror` fallback, `<script src>`, `<link rel=stylesheet>`, `<source src>` | Make self-contained |
| **Reference** (never fetched to render) | `canonical`, `itemtype`, `cite`, `rel=me/nofollow`, CSP, `preconnect`, `hreflang`, `og:url`, `mailto:`/`tel:` | Leave; it is the lesson |

## Inline SVG image technique

A deterministic, human-inspectable placeholder:

```
data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='60'%3E%3Crect width='120' height='60' fill='%23e8f0fe'/%3E%3Ctext x='60' y='35' font-size='14' text-anchor='middle' fill='%231a73e8'%3E示例图%3C/text%3E%3C/svg%3E
```

Rules:
- URL-encode `<`, `>`, `#`, `"` (use single quotes inside SVG so the HTML
  attribute can stay double-quoted).
- Match the original's declared `width`/`height` so layout lessons
  (object-fit, aspect-ratio, grid galleries, float wrap) still teach the point.
- For CSS sprites, the SVG width/height is the full sprite (e.g. `48x24`) and
  `background-position: -24px 0` still shows the second half.
- For `srcset`, produce two SVGs at the declared descriptor widths; `sizes` is
  unchanged.

## Stylesheets

Two cases:
- Plain `<link rel="stylesheet" href="style.css">` → inline `<style>` with the
  same rules.
- A lesson **about** `<link rel>` (e.g. "打印与文档元信息") → keep the
  `<link rel="stylesheet">` element but point `href` at a
  `data:text/css,...` URI so the teaching element survives and nothing 404s.
  `rel="icon"` → `data:image/svg+xml,...`; `rel="preload"` for a font → drop the
  fetch or point at a `data:` font is impractical, so convert the lesson to
  preload a `data:` image and explain, OR keep `as="font"` but note. Decide
  per-lesson to keep the lesson honest; do not leave a 404.

## Scripts

`<script src="app.js">` → `<script>` with the same minimal demonstration inline.
`analytics.js` example keeps the `<script>` element and inlines a no-op demo.

## Audio / video (no empty-src fakes)

- **Audio**: use a real, valid short PCM WAV as a
  `data:audio/wav;base64,...` URI **or** a runtime-generated Web Audio tone.
  A 1-byte or arbitrary placeholder is forbidden; the delivered document must
  actually play (assert `readyState >= 2` / `duration > 0`, or an audio-context
  oscillator whose gain node is live).
- **Video**: MP4 cannot be hand-authored reliably. Use a **runtime-generated**
  canvas animation that actually animates (frame count advances), with the same
  play/pause control teaching, and explain that a real deployment uses
  `<video><source>`.

Chosen implementation to avoid an unmaintainable 7 KB base64 literal inside a
Python source string: the `多媒体` lesson uses a **runtime-generated** demo for
both — a Web Audio tone played through an `<audio>`-adjacent button, and a
`<canvas>` animation for video. This is honest (the reader hears/sees real
playback), keeps the source readable, and needs no binary asset. `poster` uses
an inline SVG `data:` URI.

The base64-WAV option stays available if a later owner prefers a literal; it is
documented here but not used in-tree.

If a lesson's whole point is the `<source>` element, teach it with a `data:`
WAV source for audio and a canvas demo for video, explaining the substitution in
`explain`/`out`.

## CSV / JSON download

`<a download href="report.csv">` and `href="x.json"` → keep the `<a download>`
element, set `href` to a `data:text/csv;charset=utf-8,...` /
`data:application/json,...` URI, or generate via `Blob`+`URL.createObjectURL`
in an inline script. The latter is preferred where the lesson is about the
download mechanism.

## Preserved 404 example (the only one)

`html_data.py:91` keeps `src="missing.png"` and the adjacent `placehold.co`
image becomes an inline SVG. Update `explain`/`out`/`pit` to state that
`missing.png` is intentionally absent to demonstrate the `alt` fallback and the
browser's broken-image state.

This is the **only** permitted 404. `research/media-change-list.md` records its
IDs and every replaced image's new URI so p6 can assert:
- `missing.png` → `naturalWidth == 0` / broken (expected);
- every other `<img>` → `img.complete && img.naturalWidth > 0`.

## Image URI change list → p6

For each replaced image, the change list records: source file, lesson title,
original URI, new `data:` URI, intended width/height, and the DOM selector p6
should query. p6 uses this to assert natural size > 0 rather than text-only.

## Validation (p7-run after this lands)

```bash
python -X utf8 -m py_compile scripts/curriculum/*.py
python -X utf8 scripts/emit_content.py
# grep the emitted JSON for remaining fetchable refs
```

Local check this worker can run: `python -X utf8 -m py_compile` on the eight
files, plus a static scan (regex) asserting no `placehold.co`, no bare local
media refs remain in fetched positions.
