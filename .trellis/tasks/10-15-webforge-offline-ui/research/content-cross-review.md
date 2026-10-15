# Cross-review: WebForge curriculum assets (2nd round, read-only)

Reviewer task: `10-15-webforge-offline-ui` (content cross-check only).
Author of assets/scripts: `10-15-webforge-content-curriculum` (p7).
Scope reviewed: `assets/content/tutorials.json` (301 entries) and
`assets/content/examples.json` (301 entries).
Not changed here: p7 scripts, assets, `pubspec.yaml`.
Not run: no Flutter/Dart command; all checks were read-only text/JSON analysis.

---

## Summary

| Area | Result |
| --- | --- |
| Structure / fields | Clean — no empty required field, no duplicate title/explain/output, every entry 1 lesson. |
| Referential integrity | Clean — 0 unresolved `sourceLessonId`, all `prerequisites` resolve by title. |
| CSS selector reachability | Clean — 4 flagged classes are JS-toggled at runtime, not broken. |
| Example/tutorial linkage | Clean by design — every example body equals its source lesson body. |
| **`type` field (F2 — RETRACTED, no runtime defect)** | `type` is intentionally `html` for every entry; see F2 below. The real issue is p7's **test statistic**, not the data. |
| **`output` promise vs code (F3)** | Minor — a few lessons promise runtime behaviour the offline preview cannot show. |

---

## F2 — RETRACTED: `type: "html"` is correct; only p7's test statistic is wrong

**My earlier conclusion was a logic error. Corrected here.**

`ContentProductTypes.byProduct['webforge'] = {'html','css','javascript'}`, and
`ContentFilter.matches` does **set containment**:
`types.contains(entry.type)`. With every entry `type == 'html'`, **all 602
entries match** — nothing is filtered out at runtime. The earlier claim that
only 100 html entries survive was wrong, and the "change `type` to
`language`" advice was wrong and is withdrawn.

**Why `type: "html"` must stay** (controller-confirmed):
`CodeImportService.suggestedFileName(type)` resolves through
`_templateForType(type)` → `ProjectTemplate.fromType(type)`; the Web template's
`mainFile` is `index.html`. A `css`/`js` `type` would make an imported example
land as a `.css`/`.js` main file instead of a runnable `index.html`. So `type`
is the **executable artifact kind** (always a self-contained HTML document
here), and `language` carries the subject (html/css/javascript). This matches
the assets: every entry is a full HTML document with inline `<style>`/`<script>`.

**The actual defect is in p7's guard tests**
(`test/content/webforge_content_test.dart`):

- `cover html, css and javascript` filters `catalog.tutorials.where((t) =>
  t.type == 'css')` — that bucket is legitimately empty, so the `isNotEmpty`
  assertion is testing the wrong field. It should count by **`language`** and
  assert ~301 across the three subjects (html 100 / css 100 / javascript 101).
- `pass the core release validator for web types` passes
  `requiredTypes: {'html','css','javascript'}` with
  `minimumEntriesPerType = 100`. The validator counts per `entry.type`, so
  css/js buckets are 0. For a product whose only executable kind is HTML, the
  correct call is to validate against the **actual runnable type** —
  `requiredTypes: {'html'}` (301 entries, ≥100) — and separately assert the
  per-language subject spread (F2-test), not the validator's per-type minimum.

**Do not change the data.** Fix the test's statistic/validator arguments only.

See also: `trellis channel thread webforge-content-review content-type-field`.

---

## F3 — a few `output` promises exceed what the offline preview can show (minor)

Example: `js-tutorial-095` "离线检测与在线状态". The code prints
`navigator.onLine` and shows 在线/离线, but the `output` text promises
"断开网络后显示离线，恢复后回到在线" — a live network transition the in-app
preview cannot reproduce. The explanation itself already notes `onLine` only
reflects a network interface, so the lesson is not wrong, but the `output`
wording over-promises. Recommend softening the `output` line (consistent with
the file's own caveat). Not blocking.

---

## Checked and found acceptable (explicitly cleared)

- **`prerequisites` use titles, not ids.** Core treats `prerequisites` as a
  display-only string list (`local_content_pages.dart` renders each item as a
  bullet; `ContentRepository` never resolves them to ids). 329 raw "unresolved"
  matches are therefore a non-issue, and 298/301 lessons carry prerequisites.
- **4 CSS "selector not found" hits** — `css-example-032` `.move`,
  `-043` `.scrolled`, `-052` `.open`, `-086` `.dark`. Each class is added at
  runtime by the example's own `<script>` toggle, so the selectors do match. Not
  a defect.
- **`templateType: "html"` on CSS/JS examples** — `templateType` is only
  parsed/validated in core, not used to dispatch execution; every example is a
  self-contained HTML document with inline `<style>`/`<script>`, so `html` is
  the correct wrapper type. (Distinct from F2, which is about `type`.)
- **Examples equal their source lesson code (301/301)** — intentional: the
  example `summary` reads "可运行的 HTML 示例，验证：…" and links via
  `sourceLessonId`. They are runnable copies, not independent variants. Worth a
  note only if richer example variants are later desired.
- **No placeholders / no reuse**: 0 duplicate titles, 0 duplicate `explain`,
  0 duplicate `output`; all required fields non-empty; every entry has ≥1
  lesson, concepts, pitfalls and exercises.

---

## Method

Read-only PowerShell/JSON inspection of both assets:

- field-emptiness sweep over title/summary/objective/explain/code/output and
  concepts/pitfalls/exercises;
- duplicate detection over titles / explain / output;
- `sourceLessonId` resolution against tutorial lesson ids;
- CSS `<style>` selector-vs-markup reachability scan over all 100 CSS examples;
- `type` / `language` group counts over both files;
- spot reads of beginner, intermediate and advanced lessons for
  explain↔code↔output coherence.

No Flutter/Dart command was run (per controller instruction). No file outside
this task's docs was written.
