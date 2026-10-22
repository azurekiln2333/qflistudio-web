# Independent Web tools review — 2026-10-22

Reviewer: native Codex `core_research`, reassigned by root as `trellis-check` for the new Web tools slice. Read source request, AGENTS/workflow, task PRD/design/implement/check.jsonl, applicable frontend/backend/guides specs, and the current dirty worktree. Root assigned exclusive ownership of tools services/widgets/tests and serialized Flutter commands. No core/main/platform/catalog/runner files were edited. No commit was made.

## Verdict

Substantial correctness fixes landed in the assigned worktree, including the two later HTML boundary findings F12/F13. **Final integration approval remains pending:** root owns the current full analysis/widget rerun after concurrent shared-core API mismatches stabilize. The Flutter slot was released with no live Flutter process; root then authorized only the F12/F13 service/tests/browser-fixture follow-up, which is complete. No subsequent Flutter command was run by this reviewer.

The earlier implementation report `web-tools-results.md` is historical. Its claims that capped synchronous recursive I/O is safe on the UI isolate, that duplicate declarations always use the last value, and that its formatter preserves content are superseded by this review.

## Findings fixed locally

| ID | Severity | Original repro / failure | Fix and evidence |
| --- | --- | --- | --- |
| F1 | High | `directory.listSync(recursive: true)` built a complete recursive listing before filtering; `node_modules` was traversed despite the apparent skip, and a cap on HTML matches did not cap other entries. Opening Tools or clicking refresh blocked the UI. | `WebMarkupInspector.scanDocuments` uses asynchronous per-directory discovery, never enters excluded directories or follows links, caps visited entries at 10,000 and HTML files at 200, and reports truncation. Regression creates an excluded nested HTML and another test creates 201 HTML files. |
| F2 | High | The widget performed document and up to 32 stylesheet reads/parsing in synchronous `setState` callbacks; state did not track same-store project loading/removal. | `inspectFileAsync` uses `Isolate.run`; widget awaits discovery/analysis and guards every continuation with `mounted` and a generation counter. Store listeners are attached/detached on lifecycle changes. Widget regressions observe real missing-resource results after load/removal and dispose during pending discovery without a later exception. |
| F3 | High | CSS formatter reconstructed a flat inspection model: `@media`, `@supports`, `@layer`, `@import`, comments and custom-property case could disappear. It mishandled strings containing multiple spaces or escapes. | Formatter now scans original tokens and preserves nesting/at-rules/comments/string bytes/custom case. Malformed input or custom-property block values retain source verbatim. Unit checks assert scope/bytes/idempotence; actual Chromium results before/after are equal, including imported height, media-rule width/color, supports display, layer margin and pseudo-element string. |
| F4 | High | HTML formatter trimmed raw script/pre/textarea content and inserted whitespace into mixed inline children, changing programs or rendered text. | Raw/mixed/text-bearing elements are emitted as source-preserved ranges; malformed tag structure retains original source. DOM/script/browser tests cover nested mixed content, JavaScript template text, preformatted text and textarea value. Root-level inline fragment protection was added in F12 below. |
| F5 | High | `isOfflineClean` ignored missing resources and skipped/error inspections, so `<img src="missing.png">` could show “可直接离线预览”. | Missing files, invalid/escaping paths, error findings and incomplete reference/stylesheet checks prevent clean status. Over-limit checks emit explicit findings. UI limits its claim to recognized static resources and points dynamic requests to preview logs. |
| F6 | High | Lexical path checks allowed a project symlink to point outside the root; document entry itself was not confined. Icon links could be read as UTF-8 CSS and throw. | Existing ancestors are canonicalized before document/resource reads, including missing descendants of symlink directories; only stylesheet links/imports are followed. UTF-8 and filesystem failures produce findings. Real Windows symlink escape test passed; outside document and binary icon/invalid-document tests passed. |
| F7 | Medium | `srcset="data:image/png;base64,AAAA 1x, local.png 2x"` split the data URI at its comma. CSS comments/quoted strings looked like URL references; HTML entities were not decoded. | Candidate scanning retains data commas; resource attributes decode HTML entities; CSS comment/string URL lookalikes are ignored. Regressions assert one inline and two existing local resources with zero external references. |
| F8 | Medium | Local CSS imports were reported but their contents were never inspected, permitting a false clean verdict when an imported stylesheet referenced the network. CSS source locations were all reported as HTML 1:1. | Local import chains are followed within the same 32-file limit with cycle suppression. Each CSS reference uses its own stylesheet index and exposes its origin in reference rows. An import-chain test finds an external URL on stylesheet line 3. |
| F9 | Medium | Color scanner reported `#fff` selectors, `<red>` type selectors or URL fragments as colors; comment stripping destroyed `content:"/* literal */"`. Malformed/nonfinite numeric functions could be accepted or throw. | Colors are scanned only within declaration values, skipping URLs/strings/comments. Comment masking preserves quoted text and original newlines/offsets. RGB/HSL arguments reject malformed/nonfinite forms; 148 named colors, transparent, RGB/HSL/hex and contrast cases pass. |
| F10 | Medium | Specificity counted namespace prefixes as types, legacy pseudo-elements as classes and missed `:nth-child(... of ...)`; decimal weighting let 101 classes outrank an ID. | Lexicographic comparison is used for sorting and functional maxima. Namespace, legacy/modern pseudo-element, `:where`/`:is`/`:not`/`:has`, nth-child list, host/slotted and 101-class cases pass. Nesting `&` is visibly marked “依赖嵌套父规则，未计算” rather than assigned a claimed final triple. |
| F11 | Medium | Box-model sums ignored shorthand/longhand order, important values, unitless zero, absent/none border style and border-box minimum sizes. Duplicate-property UI claimed the last declaration always wins. | Edge resolution respects declaration order/important, supports shorthand/physical longhands/border shorthand, zero/px, and effective border style. Non-px conversion remains unavailable. Border-box sizes include the minimum padding/border footprint. Duplicate UI explicitly notes valid values and important affect the winner. Regressions cover each supported behavior. |

## Later findings and final verification handoff

### F12 — High, fixed: root-level HTML inline fragment formatting could change text

Input to `WebMarkupInspector.formatHtml`:

```html
<span>A</span><span>B</span>
```

The original parent-range protection missed this fragment because there was no parent in the scanner stack. Each span became its own output line and the inserted newline changed browser text from `AB` to `A B`.

Fix: `formatHtml` now returns the complete original fragment whenever root-level inline/non-block elements or non-whitespace text are present. It continues formatting safe block documents and protecting mixed/raw ranges. New unit regression covers adjacent inline siblings without a separator, an intentional separator and surrounding root text; root will execute that extra case in its final Flutter run.

Executed evidence: production Dart fixture output was loaded in actual Chromium. All three fragment before/after `innerText` values match, with independently asserted `AB`, `A B` and `first bold tail`. See `web-tools-browser-results.json`.

### F13 — Medium, fixed: raw-text closing search accepted a tag-name prefix

Input to `structureFindings`:

```html
<script>const label = "</scripture>";</script>
```

The original `_tokenize` search accepted a matching name prefix, so it could treat `</scripture>` as an end tag and report a spurious unmatched close. The same prefix issue applied to style/title/textarea.

Fix: the scanner continues searching until the matching name is followed by HTML whitespace, `/` or `>`. Added unit regression covers all four raw-text element names, prefix decoys, mixed-case closing names, whitespace and slash boundaries. Root will execute that extra case in its final Flutter run. Executed Dart/browser fixture embeds `</scripture>` inside a real script template string, asserts zero structure findings, and confirms the script source and executed value are identical after formatting.

### F14 — Final widget/integration rerun unavailable during concurrent core edits

The latest navigation attempt failed at compilation in `../qfli_studio_core/lib/editor/editor_problems_bar.dart`:

- line 24 uses nonexistent `CodeDiagnostic.line` and `.column`;
- line 34 uses nonexistent `EditorFileDiagnostics.pending`.

The report was sent to root, which relayed it to the single core integrator. These files are outside this slice and were not edited here.

Before that shared-core mismatch, the combined tools run passed the service and overview cases but two navigation cases timed out because their old helper only advanced the fake clock while the new panel performed real asynchronous filesystem/isolate work. The navigation helper now first advances the real PageView animation by 300 ms, then observes the public busy indicator while allowing real async work via `tester.runAsync`. The **final helper change has not yet passed** because of the compilation failure; root must rerun it after core stabilizes.

## Commands and current authoritative results

1. Latest completed focused service command:

   ```text
   flutter test --no-pub --concurrency=1 test/web_css_tools_test.dart test/web_markup_inspector_test.dart
   ```

   **47/47 pass** before the two final F12/F13 unit cases were added, including actual on-disk Windows symlink confinement, async/isolate disk analysis and the 201-document cap test. There are now 49 service cases for root's final run. No skip was needed for symbolic links on this host.

2. Last affected analysis before the final extra regression assertions:

   ```text
   flutter analyze --no-pub lib/services/web_source_scan.dart lib/services/web_css_tools.dart lib/services/web_markup_inspector.dart lib/widgets/web_tools lib/pages/web_tools_overview.dart test/web_css_tools_test.dart test/web_markup_inspector_test.dart test/web_tools_overview_test.dart test/web_tools_navigation_test.dart test/web_tools_page_test.dart
   ```

   **No issues found (10 items).** Final full analysis remains root-owned after shared-core stabilization.

3. `web_tools_overview_test.dart`: all **11 widget cases passed** in the last combined run, including inline controls, codec result, CSS/markup result interactions, real project reference counts, 320×640 at 2× text, store load/removal and disposal in-flight. `web_tools_page_test.dart`: **4/4 passed** in that run. Combined navigation/full rerun remains F14, so these are narrow recorded results rather than a full-suite approval.

4. Actual browser semantic comparison:

   ```text
   dart --packages=.dart_tool/package_config.json .trellis/tasks/10-22-standalone-offline-ide/research/web-tools-format-fixture.dart .trellis/tasks/10-22-standalone-offline-ide/research/web-tools-format-fixture.json
   node .trellis/tasks/10-22-standalone-offline-ide/research/web-tools-browser-check.mjs .trellis/tasks/10-22-standalone-offline-ide/research/web-tools-format-fixture.json .trellis/tasks/10-22-standalone-offline-ide/research/web-tools-browser-results.json
   ```

   **Pass, 16 actual assertion calls, zero requests**, after F12/F13 fixes. The fixture JSON is generated by the production Dart formatter, not by a copied implementation. Chromium executes source/formatted HTML and CSS separately, compares the entire observation record, and asserts imported height=45px, media width=123px/red, grid display, layer margin=7px, text=`AB C`, pseudo-content=`"a  b"`, script result and pre/textarea bytes. It also compares all three root-level inline/text fragments, verifies their exact rendered text, and checks no false structure findings for the script end-tag prefix decoy. The route aborter records every attempted request; the result contains `requests: []`. This fixture does not claim OHOS behavior.

5. `git diff --check -- lib/pages/web_tools_overview.dart test/web_tools_navigation_test.dart`: pass (only Git line-ending notices). Source scan confirmed no HttpClient/socket/network-fetch calls in the new services/widgets. Sync disk methods remain only behind the service's background-isolate entry from the UI; they are not invoked in build or setState callbacks.

## Capability limits and scope

- Tools are actual inline controls on Tools, with terminal still routed through the existing shell callback. The remaining common-tools cards are the existing shared offline utility entries; no new Web feature hub was introduced.
- HTML/CSS inspection remains a bounded literal-source scanner, explicitly labeled as an inspection rather than a full conformance validator/compiler. `base href` is detected and makes the result incomplete rather than claiming a reliable clean resolution. Dynamic JS requests/imports are outside static resource inspection and must be confirmed in preview logs.
- Unsupported color functions (`color-mix`, relative/system colors), translucent-color contrast, non-px box conversion and nested-parent specificity are not fabricated. The box view is a declaration-based single-rule model; computed cascade, stylesheet origins, writing-mode logical properties and variable evaluation require a browser and are outside its displayed calculation.
- Directory discovery is bounded, not exhaustive over an arbitrarily large project. Its UI shows the cap; per-document reference/stylesheet caps also show an incomplete finding and suppress clean status.
- No project files are written by these tools; formatting produces a separate copyable result. Copyable output must preserve meaning; F12/F13 are corrected and covered by actual Dart/Chromium evidence, with final unit execution delegated to root.
- This review proves selected host Dart/Flutter/Chromium behavior only. No OHOS device/package claim, cross-product completion claim, commit or push is implied.

## Handoff

Root owns shared-core compilation stabilization, final 70-case affected tools rerun (49 services + 11 overview + 6 navigation + 4 page), full affected app analysis/tests, spec capture and explicit-path commits. `frontend/quality-guidelines.md` still describes old gateway-card navigation; update that contract to the inline page and real async inspection waits.

Reviewer is now read-only again. No further product edits or Flutter commands are planned. Final integration approval awaits root's complete verification evidence.
