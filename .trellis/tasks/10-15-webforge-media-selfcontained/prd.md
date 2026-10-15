# WebForge curriculum offline media self-containment

Child task of `10-15-webforge-store-readiness`. Owns offline self-containment of
the authored HTML/CSS curriculum lesson code.

## Problem

Imported lesson/example documents reference media and assets that do not exist
on device, and some request the network:

1. **External network images** — `https://placehold.co/...` in `<img src>`,
   CSS `background: url(...)`, `og:image`, and an `onerror` fallback. On an
   offline WebForge build these 404 or hit the network and fail.
2. **Missing local assets** — `clip.mp4`, `tone.mp3`, `cover.png`, `small.jpg`,
   `large.jpg`, `hero.jpg`, `below.jpg`, `chart.png`, `photo.jpg/webp/avif`,
   `favicon.ico`, `font.woff2`, `style.css`, `app.css`, `rest.css`, `app.js`,
   `analytics.js`, `report.csv`, `x.json`. A real import shows broken media.
3. **Fake media** — a `<video>`/`<audio>` whose `src` points at a non-existent
   file is not a working demo.

## Requirements

- Replace every **fetched** external image with an inline
  `data:image/svg+xml,...` URI (offline, deterministic, keeps intended size).
- Replace **fetched** local assets so the document is self-contained:
  - stylesheets → inline `<style>` (or `data:text/css`) while preserving the
    lesson's teaching point (including `<link rel="stylesheet">` lessons);
  - scripts → inline `<script>`;
  - images → inline SVG `data:` URIs (including CSS `url()`, sprites, multiple
    backgrounds, `srcset`/`sizes`, `og:image`, `onerror` fallback).
- **Audio/video**: no empty/`missing` `src` masquerading as playable. Either a
  genuinely valid, extremely short embedded clip (`data:` URI) or a
  **runtime-generated** demo (Web Audio tone / canvas animation). The proof must
  actually play in a browser.
- **CSV / JSON download** lessons: generate the payload with `data:`/`Blob` at
  runtime, not a fake fixture file.
- **Keep** the intentional `missing.png` 404 teaching example
  (`html_data.py:91`) and make the lesson explain its effect.
- **Name the intentional exceptions explicitly** (added constraint): the only
  allowed 404 is the `missing.png` lesson in the HTML list. Record its exact
  emitted IDs (`html-tutorial-00N` / `html-example-00N`; computed after emit) in
  `research/media-change-list.md` so p6 can exclude it from "no 404" assertions.
  **Every other automatically requested local asset must resolve.** No second
  exception.
- **Audio/video must be genuinely playable** (added constraint): a 1-byte or
  otherwise unrelated `data:` payload is forbidden. The output must be a valid
  playable resource (e.g. a real short PCM WAV) or an explicitly
  runtime-generated demo whose playback the reader can observe. "Looks like a
  media element" is not enough.
- **Send the image URI change list to p6** (added constraint) so the oracle can
  assert `img.complete && naturalWidth > 0` for each replaced image (and the
  `missing.png` case asserts the opposite), instead of only a text check.
- Leave **non-fetched reference URLs** (canonical, schema.org `itemtype`,
  `blockquote cite`, `rel=nofollow/me`, CSP, `preconnect`/`dns-prefetch`,
  `hreflang`, `og:url`, `mailto:`/`tel:`, the `a[href^="https"]` selector) as
  they are: they are never requested to render, and they are the teaching point.

## Scope / ownership

- May edit: `scripts/curriculum/html_data.py`, `html_data2.py`, `html_data3.py`,
  `html_data4.py`, `css_data.py`, `css_data2.py`..`css_data5.py`.
- **Claim these files exclusively** (declare to p7 before editing).
- **Must NOT edit**: `scripts/curriculum/js_data*.py` (p7), `emit_content.py`,
  `assets/content/*.json`, any Flutter `lib/`, native files.
- No `emit`, no flutter/dart, no stage/commit.

## Coordination

- **p7 (JS source + emit owner)**: after this task lands, p7 runs the unified
  `emit_content.py` and the content tests. Declare HTML/CSS source exclusivity.
- **p6 (oracle)**: any expected-output/oracle adjustment needed because a lesson
  now generates media at runtime instead of loading a file.
- Flag (do not fix): `emit_content.py::_element_for` hardcodes
  `https://placehold.co/40` in its fixture generator.

## Acceptance Criteria

- [x] No lesson code in the eight source files fetches an external network
      resource for rendering.
- [x] No lesson code references a local media/asset path that does not exist
      (except the named `missing.png` exception).
- [x] `missing.png` 404 example retained and explained (`html-006`) and recorded
      as the single intentional exception.
- [x] Audio/video demos genuinely produce playable output (runtime-generated),
      never an empty `src`.
- [x] CSV/JSON download uses `data:`.
- [x] Non-fetched reference URLs intentionally preserved.
- [x] `python -X utf8 -m py_compile` passes; `scan.py` reports clean.
- [x] Unified emit, product tests and final browser oracles pass: 301/301, 1820 assertions, mapping0.
