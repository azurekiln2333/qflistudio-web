# Execution plan

## Steps

1. [x] Declare HTML/CSS source exclusivity to p7 (recorded in the task docs).
2. [x] `html_data.py` — inline the `placehold.co` image; keep + explain the
       `missing.png` 404; fix `srcset`, audio/video (runtime-generated),
       `cover.png`.
3. [x] `html_data2.py` — `chart.png`, `favicon.ico`/`style.css`/`font.woff2`,
       `hero.jpg`/`below.jpg`, `cover.png`/`og:image`.
4. [x] `html_data3.py` — `report.csv`, `photo.*`, `app.css`/`app.js`,
       `favicon.ico`/`touch-icon.png`, `placehold.co` figure.
5. [x] `html_data4.py` — `placehold.co` responsive images, `og:image`,
       `onerror` fallback (invalid data URI), template `app.js`/`style.css`.
6. [x] `css_data.py`..`css_data5.py` — CSS `url(placehold.co)` sprites/
       backgrounds, `src` images.
7. [x] Static scan: `scan.py` reports no fetchable external URL or bare missing
       local asset.
8. [x] `python -X utf8 -m py_compile scripts/curriculum/*.py` passes.
9. [ ] p7 runs emit + content tests; p6 applies the oracle change list.
10. [x] Record evidence (`research/verification-record.md`,
        `research/media-change-list.md`); hand to controller.

## Validation

```bash
python -X utf8 -m py_compile scripts/curriculum/html_data*.py scripts/curriculum/css_data*.py
# static scan (this worker):
#   no "placehold.co" in fetch positions
#   no src/href/url() pointing at a bare local media path
```

## Review gate

- Each edit is local to a lesson's `code`/`explain`/`out`/`pit`; no structural
  change to the data model, keys, or the number of lessons.
- No `js_data*.py`, no `emit_content.py`, no JSON assets.
- Non-fetched reference URLs preserved.
- Audio/video output is genuinely playable/generated, never empty `src`.

## Rollback points

- After the HTML files: if an inline SVG changes a lesson's teaching result,
  re-check its `out` text matches.
- If a video lesson cannot be made honestly playable without a binary asset,
  convert it to the canvas runtime demo and state the substitution.
