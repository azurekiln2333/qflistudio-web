# Freeze preconditions (single-pass final run)

Status: **FROZEN — 301/301, mapping 0.**

The CSS-073 real-font fix and the quoted data-URI fixes landed in p5's CSS
sources; the unified emit produced a self-contained JSON with no fetchable
external/missing resources. The single full run passed.

## Final result

- `python -X utf8 scripts/emit_content.py` → 301 tutorials / 301 examples
  (html 100 / css 100 / javascript 101), byte-idempotent.
- `scripts/audit_web_content.py --product` → 0 issue.
- `node scripts/run_examples.mjs` → **301 passed / 0 failed**, mapping issues 0;
  full per-id table in `research/example-execution-report.md`.
- css-073 `@font-face` uses an inline, reproducible 576-byte WOFF2 (no
  `my.woff2`); the font generator lives in ignored `.trellis/.runtime/font-tools`
  and regular emit does not depend on it.

## Ready checklist (executed)

1. `python -X utf8 scripts/emit_content.py` ✔
2. Confirmed no fetchable external/missing resources ✔
3. `node scripts/run_examples.mjs` once, full table written ✔
4. 301/301, mapping issues 0 ✔ → frozen

## Already-complete cleanup (this task, no runner needed)

- Removed unused emit helpers: `_CSS_IN_HTML`, `_SCRIPT_IN_HTML`, `_CSS_RULE`,
  `_element_for`, `_fixture_markup`, `_css_plain_selectors` (no dead future
  stubs remain).
- Removed unused `curriculum/common.py::lesson` helper.
- `emit_content.py` docstring corrected: the `webforge-check` marker is a
  cross-cutting sanity check only; semantic verification is the job of the
  per-example oracles (`js_example_assertions.mjs`, `web_markup_assertions.mjs`).
- Verified: `py_compile` (emit + curriculum modules) OK; Node syntax OK for
  runner + both oracle modules; emit byte-identical on repeat.

## Constraints observed

No Flutter/Dart, no device, no core edits, no stage/commit; p5/p6 modules and
`package*.json` untouched; HTML/CSS sources not edited (html-097 fix was within
this task's granted scope).
