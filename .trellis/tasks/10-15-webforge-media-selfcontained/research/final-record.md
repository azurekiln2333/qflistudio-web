# Final task record — WebForge curriculum offline media self-containment

Status: **source frozen, ready for p7 emit / p6 oracle**. No further source
edits from this owner.

## Outcome

All authored HTML/CSS curriculum code is offline self-contained. No fetchable
external URL and no missing local asset remains, with one intentional teaching
exception.

## Owned sources changed

- `scripts/curriculum/html_data.py`, `html_data2.py`, `html_data3.py`,
  `html_data4.py`
- `scripts/curriculum/css_data.py`..`css_data5.py`
- `scripts/curriculum/supplement.py` (only html-096 in round 2)
- `scripts/curriculum/make_demo_font.py` (new, reproducible font generator)

`js_data*.py`, `emit_content.py`, JSON assets, runner/oracle and any core/native
code were **not** touched.

## Key fixes (rounds)

1. External `placehold.co` and missing local images → inline `data:image/svg+xml`.
2. Styles/scripts → inline or `data:`; audio/video → runtime-generated;
   CSV → `data:text/csv`.
3. **CSS grammar bug** (p6 found): unquoted `url(data:…svg…)` containing spaces
   was dropped by CSS parsing. Fixed by quoting → `url("data:…")` in
   css-062/078/088 and peers.
4. **css-073 font**: first a `my.woff2` 404, then a broken 189-byte `AAAA…`
   placeholder. Replaced with a real, original 576-byte WOFF2 built by
   `make_demo_font.py` (`FontBuilder`+`TTGlyphPen`, glyphs covering `WebForge`),
   pinned timestamps → reproducible.
5. html-096 image map → inline 240x80 SVG; hotspots intact.

**Only permitted 404**: `missing.png` in `html-006`.

## Verification (all PASS)

```bash
python -X utf8 -m py_compile scripts/curriculum/*.py          # 18 files, exit 0
python -X utf8 .trellis/.../scan.py                            # OK: 10 files
python -X utf8 .trellis/.../check_css_grammar.py               # OK: 5 url() valid
python -X utf8 .trellis/.../check_html096.py                   # PASS
python -X utf8 .trellis/.../check_css_media.py                 # PASS
PYTHONPATH=.trellis/.runtime/font-tools python -X utf8 \
    .trellis/.../check_demo_font.py                            # PASS real WOFF2
PYTHONPATH=.trellis/.runtime/font-tools python -X utf8 \
    scripts/curriculum/make_demo_font.py                       # byte-identical twice
rg -n "my\.woff2|placehold\.co" scripts/curriculum              # empty
```

## Tooling (optional, project-local, not in emit path)

- `.trellis/.runtime/font-tools` (gitignored) holds `fonttools==4.67.0`,
  `brotli==1.2.0`, installed via
  `python -X utf8 -m pip install --target .trellis/.runtime/font-tools fonttools==4.67.0 brotli==1.2.0`.
- `emit_content.py` does not import fontTools.

## Handoff

- **p7**: ready — run unified `emit_content.py`, then the full content suite.
- **p6**: oracle aligned (font.load → `status==='loaded'`; CSS computed
  background non-none; html-096 natural size 240x80; only html-006 404s).

## Remaining

No remaining owned source defect. A new finding must reopen the source owner,
regenerate JSON and rerun the affected browser checks before rebuilding packages.
