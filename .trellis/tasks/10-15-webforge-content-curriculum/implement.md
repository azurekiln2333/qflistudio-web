# Implementation Record — WebForge 专属内容

Delivered. This file records what was actually built and verified.

## Content

- Authored three language tiers (`scripts/curriculum/*.py`): html, css,
  javascript, plus `supplement.py`. Each lesson has objective, prerequisites,
  concepts, explain, runnable code, expected output, exercises and pitfalls.
- `scripts/emit_content.py` produces `assets/content/tutorials.json` and
  `assets/content/examples.json`: **301 tutorials and 301 examples**
  (html 100 / css 100 / javascript 101). Emit is byte-idempotent on repeat.
- Delivered `type` is always `html` (each document is a complete, standalone,
  previewable page and imports as `index.html`); the subject is preserved in
  `language` (html/css/javascript).
- `pubspec.yaml` registers `assets/content/`.

## Repository (Dart)

- `lib/content/webforge_content_repository.dart` implements the core
  `ContentRepository` contract against the product assets.
- `main.dart` wiring (`contentRepositoryFactory: WebForgeContentRepository.new`)
  is owned by main control / p6; recorded as a diff, not applied here.
- Product test `test/content/webforge_content_test.dart` is maintained by main
  control (language coverage + html import contract).

## Verification

- `scripts/audit_web_content.py --product` → **0 issue**; all titles, explains,
  codes and outputs unique; 301/301 distinct example bodies; every example links
  to an existing lesson.
- `scripts/run_examples.mjs` (Playwright Chromium, one isolated browser context
  per example) runs the delivered JSON. Semantic assertions come from per-example
  oracles, never the marker alone:
  - `scripts/js_example_assertions.mjs` — all 101 JS examples with concrete
    console / DOM / interaction / canvas expectations (owner: this task).
  - `scripts/web_markup_assertions.mjs` — 200 HTML/CSS examples (owner: p6),
    `assertMarkupExample(page, example, addCheck)` + `COVERED_IDS`.
  - Runner cross-cutting checks: no page errors, no external requests of any kind
    (including images), no broken same-origin resources (exact `URL.pathname`
    allowlist, currently only `html-example-006 -> /missing.png`), origin-based
    same-origin decision, per-example context.
- Full per-id table: `research/example-execution-report.md`.
- Attribution of the remaining failures (corrected per p6's probe):
  `research/final-verification-handoff.md` — unquoted `url(data:image/svg+xml,…)`
  with spaces is an invalid CSS token dropped by the parser; plus the `my.woff2`
  fake font in css-073. These are source defects in p5's CSS sources.
- `research/freeze-preconditions.md` — the one-pass final run and freeze gate.

## Cleanup

- Removed unused helpers/stubs: emit `_CSS_IN_HTML`, `_SCRIPT_IN_HTML`,
  `_CSS_RULE`, `_element_for`, `_fixture_markup`, `_css_plain_selectors`,
  `curriculum/common.py::lesson`. No future-empty methods remain.
- `emit_content.py` docstring states the marker is a sanity check only.

## Ownership freeze

- Sources: `scripts/curriculum/js_data*.py` and `scripts/emit_content.py`
  (this task). HTML/CSS sources (`html_data*.py`, `css_data*.py`,
  `supplement.py`) — p5; `supplement.py` html-097 fixed within this task's
  granted scope.
- Runner + JS oracle (this task): `scripts/run_examples.mjs`,
  `scripts/js_example_assertions.mjs`, `scripts/audit_web_content.py`.
- Markup oracle: `scripts/web_markup_assertions.mjs` (p6).
- JSON: `assets/content/*.json` — regenerated only by `emit_content.py`.
- Submission: staged/committed by main control; this task does not commit.
  Shared core must remain clean (other owners' metadata may remain).
