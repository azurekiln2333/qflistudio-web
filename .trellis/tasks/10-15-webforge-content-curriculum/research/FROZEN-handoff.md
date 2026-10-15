# FROZEN — WebForge content curriculum

Status: **FROZEN**. No further code/JSON changes.

## Frozen artifacts

- Content JSON (byte-idempotent under `scripts/emit_content.py`):
  - `assets/content/tutorials.json`  SHA256 `9841D2093C69B471…`
  - `assets/content/examples.json`   SHA256 `784332D5217F9F64…`
  - 301 tutorials / 301 examples (html 100 / css 100 / javascript 101).
- Sources: `scripts/curriculum/*.py` (`js_data*` this task; `html_data*` /
  `css_data*` / `supplement.py` p5).
- Runner + JS oracle (this task): `scripts/run_examples.mjs`,
  `scripts/js_example_assertions.mjs`, `scripts/audit_web_content.py`.
- Markup oracle (p6): `scripts/web_markup_assertions.mjs`.

## Verification (final)

- `scripts/audit_web_content.py --product` → 0 issue.
- `node scripts/run_examples.mjs` → **301 passed / 0 failed**, 1820 assertions,
  mapping issues 0. Full per-id table: `example-execution-report.md`.
- `python -X utf8 scripts/emit_content.py` re-run: JSON byte-identical
  (idempotent) — no drift.
- CSS-073 uses an inline, reproducible 576-byte WOFF2; no `my.woff2`; no
  `placehold.co`; only intentional 404 is `html-example-006` `/missing.png`
  (runner exact id+path allowlist).
- Product suite: **82 tests passed** (owned by main control); `flutter analyze`
  clean; `test/content/webforge_content_test.dart` maintained by main control.
- Final APK built by main control on this frozen JSON.

## Ownership

- This task owns: `scripts/curriculum/js_data*.py`, `scripts/emit_content.py`,
  `scripts/run_examples.mjs`, `scripts/js_example_assertions.mjs`,
  `scripts/audit_web_content.py`; `assets/content/*.json` (regenerated only by
  emit).
- p5 owns HTML/CSS sources; p6 owns the markup oracle.
- Main control owns `test/content/webforge_content_test.dart`, `main.dart`
  wiring, `package*.json`, and standard commit/staging.
- Shared core (`qfli_studio_core`) contains none of this task's changes.

**Handoff complete. Ended.**
