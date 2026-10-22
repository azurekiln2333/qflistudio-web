# HTML 101–160 production-runner check

Captured 2026-10-22. Scope: the 60 authored HTML expansion examples and their matching tutorial lessons, IDs `html-example-101` through `html-example-160`. This is host-browser evidence from the production `scripts/run_examples.mjs` runner. It does not establish OHOS/ArkWeb device execution.

## Final results

| Runtime | Viewport | Passed | Failed | Assertions | Mapping issues |
| --- | --- | --- | --- | --- | --- |
| Playwright Chromium 156.0.8078.4 | 1280 × 720 | 60 | 0 | 725 | 0 |
| Playwright Chromium 156.0.8078.4 | 390 × 844 | 60 | 0 | 725 | 0 |

Both runs used Windows x64 and Node v24.15.0. The desktop run started at `2026-10-22T05:50:39.334Z` and completed at `2026-10-22T05:51:09.447Z`; the narrow run started at `2026-10-22T05:50:39.336Z` and completed at `2026-10-22T05:51:09.384Z`. Each run selected all 60 IDs, with one semantic oracle per example, and checked external requests and internal resource errors. All selected examples passed those checks.

The loaded catalog contained 481 examples, 481 lessons and 481 distinct lesson bodies. These commands deliberately select only the 60 expansion HTML examples; the runner correctly reports `complete: false`. This report is not a complete 481-example catalog pass.

```powershell
node scripts/run_examples.mjs --filter '^html-example-(10[1-9]|1[1-5][0-9]|160)$' --report build/content/html-check-desktop.md *> build/content/html-check-desktop.log
node scripts/run_examples.mjs --filter '^html-example-(10[1-9]|1[1-5][0-9]|160)$' --viewport 390x844 --report build/content/html-check-mobile.md *> build/content/html-check-mobile.log
```

Machine-readable reports are `build/content/html-check-desktop.json` and `build/content/html-check-mobile.json`. Their Markdown siblings summarize the same runs. These are generated local artifacts.

## Source identity

The final reports bind execution to these aggregate source bytes; the current aggregate files matched both hashes when this record was written.

| File | SHA-256 |
| --- | --- |
| `assets/content/examples.json` | `2d8f8c0aa321f3e861af5f46cd0a9b2b1430010b513d3c3eea106c0eca2eeb1c` |
| `assets/content/tutorials.json` | `10e750b7bd8fa8f1cb9d252831bce224248c0075589f5367c4312e37104acb36` |
| `scripts/curriculum/html_expansion.py` | `6e9d05e38b3af1f4a6f46c9483c7157f11ab56b503263a5c6569237492bdc555` |
| `scripts/html_expansion_assertions.mjs` | `6f8406af3365274bdee0b243fa07a9bdd93314c8833c1b9417f780f865f0236c` |
| `scripts/run_examples.mjs` | `74f017f448c6e750d74f0ca61bc636d37f0fd630e185789f10ae774d25404074` |

The HTML module also passed a Python syntax parse and schema inventory: 60 records, 60 distinct titles, 60 distinct complete code bodies, and all required `t/level/obj/pre/con/explain/code/out/pit/ex` fields. `node --check scripts/html_expansion_assertions.mjs` and the owned-path `git diff --check` completed successfully.

## Failures found and repaired

The first production-runner execution at both viewports passed 48/60, failed 12 and executed 721 assertions. Initial evidence remains in `build/content/html-check-initial-{desktop,mobile}.{md,json}`. The failing IDs were 109, 119, 122, 125, 126, 134, 135, 136, 137, 140, 141 and 144. Actual shipped sources served over loopback and Chromium DOM/geometry probes were used to distinguish authored defects from incorrect oracle assumptions.

Authored HTML repairs:

- **109, table footer:** use `foot.rows[0].rowIndex` (3); a `tfoot` element itself has no `rowIndex`.
- **119, image submit coordinates:** decode the input's real image source with `Image`, and build `new FormData(form, event.submitter)` in the submit handler. Read actual `spot.x` and `spot.y` values. A click at `(30,20)` produces coordinate values `30` and `20`; `HTMLInputElement` does not expose image `naturalWidth` or `complete`.
- **122, formdata:** explicitly build `new FormData(form)` after cancelling submission, allowing the existing `formdata` event listener to run. Correct the lesson's claim about constructor-triggered `formdata` events.
- **134, MathML:** describe the observed `block math` computed display and numerator/denominator placement. An inline fraction need not exceed normal text-line height.
- **135, picture:** encode the literal spaces in two SVG `srcset` data URIs as `%20`, so the browser can parse and select the intended candidates. Explain source-order selection accurately.
- **136, sup/sub:** correct the three-subscript/four-superscript count and the direction of the document-position comparison.

Oracle repairs and stronger checks:

- Replace exactly 22 invalid `(await text(...)).then(...)` expressions with bounded, count-checked `await text(...).then(...)` edits.
- Initialize search/form inputs before the corresponding actions (102/122), check actual table-footer identity/index (109), and verify decoded image dimensions plus real submitted coordinates (119).
- Replace the unconditional navigation check in 123 with comparison against the original page URL. Use a sentinel to prove the submit event fires when a submitter is omitted, and assert its exact output.
- Check ruby annotation placement above base glyphs (125), observed bidi computed styles (126), MathML text via `textContent` plus real fraction geometry (134), and selected picture source/intrinsic dimensions derived from the actual viewport (135).
- Align 137 with the existing authored same-origin Blob HTML object: check `text/html`, Blob origin, document root and exact inner text without inserting a test fixture.
- Read canvas fallback and SVG metadata via `textContent` (140/141). Check canvas CSS content dimensions 150 × 75 separately from its bordered outer width 152, preserving bitmap pixel assertions.
- Use native `element.querySelectorAll` for light-DOM checks (144), because Playwright CSS locators pierce shadow roots; retain the actual shadow heading and slot assertions.

The final result adds four meaningful assertions overall and has no skipped failing examples. Aggregate generation/staging was performed by the parent after the authored repairs; this worker changed only the two HTML-owned source/oracle files and this report during the HTML check assignment.

## Remaining evidence boundary

The parent can run the complete 481-example catalog against the same aggregates. Current OHOS validation requires rebuilding the production/test HAPs for these 481-example assets and running the catalog driver against a connected, identified device. The previous 301-example test HAP is stale for this expansion. Host Chromium results must remain separate from that device evidence.
