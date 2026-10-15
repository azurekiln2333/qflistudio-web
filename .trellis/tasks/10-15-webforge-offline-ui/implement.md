# Implement — WebForge offline UI and networking-entry consolidation

Parent: `10-15-webforge-store-readiness`

## Change boundary

- Files: `lib/pages/web_tools_page.dart`, `lib/pages/web_tools_overview.dart`
  (new), `lib/main.dart`, the three named test files,
  `scripts/web_markup_assertions.mjs` (new, see Batch 4),
  `research/content-cross-review.md` (new), these task docs.
- Not touching: `qfli_studio_core`, `pubspec.yaml`, assets, terminal delegation,
  platform native config, the five `PageView` pages' count, p7's runner
  (`scripts/run_examples.mjs`) and JS assertion module.

## Ordered checklist

### Batch 4 — content cross-review + markup assertions (added mid-session)

- [x] Read-only cross-review of `assets/content/*.json` →
      `research/content-cross-review.md`.
      - Confirmed F2 is **not a data defect**: `type: "html"` is required
        (`CodeImportService.suggestedFileName`); the fault is p7's test statistic
        (count by `language`) and the validator `requiredTypes`. Retracted the
        original high-severity claim and posted a correction.
      - F3 (minor): a few `output` promises exceed the offline preview.
      - Cleared items recorded so nobody "fixes" non-bugs.
- [x] Wrote `scripts/web_markup_assertions.mjs` (owner: this task) exporting
      `assertMarkupExample(page, example, addCheck)` and `COVERED_IDS`:
      100 HTML + 100 CSS, each with concrete semantic/attribute or computed /
      interactive values. `node --check` clean; dynamic import returns 200 ids.
- [x] Sync interface + progress to p7 via the `webforge-content-review`
      channel (thread `markup-assertions-interface`).
- [x] p7 wires the export into the runner; full Chromium run is p7's.
- [x] Independent real run by this task's own temporary probe
      (`build/web_markup_probe.mjs`, git-ignored, Playwright Chromium):
      **200/200 pass, 772 checks, 0 fail**; p7's full run **301/301, 1820
      checks, mapping 0**. First run was 171/29; all 29 were wrong
      expectations / timing in this module (fixed), **no content defect**.
      See `research/markup-assertions-run.md` for the per-case table.
- [x] Notified p7 that the runner must tolerate subresource 404s
      (`html-example-061` app.css/app.js, `css-example-073` my.woff2).

### Batch 1 — offline gating in the product tools

- [x] In `lib/pages/web_tools_page.dart`:
  - [x] Read `StudioProfile.current?.offlineOnly == true` once and gate on it.
  - [x] Hide the `HTTP` tab (`_HttpTool`) and its `Tab` entry when offline.
  - [x] Extract `WebServerToolsView` (server domain) and `WebCodecToolsView`
        (JSON/URL/Base64) so both `WebToolsPage` and the integrated overview
        reuse them without duplicating widget code.
  - [x] In `_WebProjectSettingsDialog`: hide the API-proxy section when offline
        and preserve any pre-existing `proxies` on save instead of writing an
        empty list.
- [x] Verify: `test/web_tools_page_test.dart` green.

### Batch 2 — integrated tools tab

- [x] New `lib/pages/web_tools_overview.dart`: `WebToolsOverview` returning a
      core `ToolsGrid` with product `ToolSection`s (本地服务 / 编解码) and the
      shell `onOpenTerminal`; no nested Scaffold/AppBar.
- [x] `lib/main.dart`: set `toolsTabBuilder: _buildWebToolsTab`; keep
      `toolsPageBuilder` pointing at `WebToolsPage`; wire
      `contentRepositoryFactory: WebForgeContentRepository.new` (p7's file).
- [x] Verify: `test/web_tools_navigation_test.dart` green.

### Batch 3 — layout and five-page coverage

- [x] Narrow (320×640) / large-text (2.0) widget tests: the full shell walks all
      five pages with no exception, and the **complete integrated tools grid**
      (`WebToolsOverview`) asserts a real no-overflow pass.
- [x] Five pages visually reviewed on a real device by the controller
      (`ui-five-pages-redacted.jpg` in the parent task; original local-only).
      Light/dark via existing widget/core suites. No 12-shot screenshot
      deliverable — the old `web_ui_screenshots_test.dart` draft is superseded
      (`ui-screenshot-plan.md`).
- [x] Extend `test/web_app_test.dart` with profile assertions for the offline
      gating (offlineOnly true, toolsTabBuilder set).

## Validation commands

```bash
flutter analyze --no-pub lib test
flutter test --no-pub --concurrency=1 test/web_app_test.dart test/web_tools_navigation_test.dart test/web_tools_page_test.dart
```

## Review gates

- No `qfli_studio_core` file appears in `git status`.
- `grep` for `HttpClient` / `_HttpTool` / `proxies` still shows them used only
  behind the offline gate; no unconditional path remains.
- Each batch: `flutter analyze` clean, targeted tests green.

## Commit / rollback points

- One commit per batch; stage only the files that batch touched
  (`git add <explicit paths>`, never `git add .`).
- Rollback: revert the batch commit; `main.dart` revert restores prior
  navigation, `web_tools_page.dart` revert restores the HTTP tab.

## Verification status (this session)

- Product Flutter tests: **82/82 pass** (controller-run).
- Shared core targeted tests: **116/116 pass** (controller-run).
- Shared-core fixes that closed this task's earlier findings, all landed:
  - `54a58ca` — editor Git / cloud / AI entry gates under `offlineOnly`.
  - `b7b2d2e` — background refresh + terminal network/Git shortcuts gated.
  - `7b8b7f2` — core `ToolsGrid`/`ToolCard` text-scaling-aware extent (320px /
    2.0 light+dark no overflow). Owned-by-core; this task keeps the **positive**
    320×640 / 2.0 no-overflow regression (no reverse sentinel).
- `flutter analyze --no-pub lib test` → 0 issues (last run before the shared
  device window; no further dart/flutter launched from this task — the
  controller serialises verification).
- Markup oracle (`scripts/web_markup_assertions.mjs`):
  - `node --check` clean; dynamic import exposes `assertMarkupExample` +
    `COVERED_IDS` (200).
  - Runtime probe (`build/web_markup_probe.mjs`, git-ignored) over all 100 HTML
    + 100 CSS in Chromium. **Final: 200/200 (772 checks).** An intermediate
    revision once showed 196/200, then 197/200 — all remaining failures were p5
    source defects (see `research/markup-assertions-run.md` and the
    `p5-source-defects` channel thread), now fixed and re-emitted.
  - Every replaced image asserts real decode (`img.complete && naturalWidth>0`;
    CSS backgrounds probed with `new Image()`), so a corrupt data URI cannot
    pass. `html-006 missing.png` asserts `naturalWidth===0` (the single
    permitted 404). `html-010` asserts canvas repaint + a live Web Audio
    oscillator at 440 Hz.

### Pending after p5's fix

- [x] html-096 re-emitted and passing (inline SVG 240×80, `usemap`/`#m`,
      hotspots 0,0,120,80 / 120,0,240,80; oracle asserts
      `naturalWidth===240 && naturalHeight===80`).
- [x] html-097 now uses a runtime Blob stylesheet (no `rest.css`, no network);
      oracle passes.
- [x] html-061 inlines style/script (no `app.css`/`app.js` fetch).
- [x] css-062 / 078 / 088 — fixed and passing: quoted `url("data:image/svg+xml,
      ...")`, computed background is non-`none`, inline `data:image/`, and
      decodes. Sources: `css_data4.py:155`, `css_data5.py:71`,
      `css_data5.py:191`.
- [x] css-073 — real font load verified: visible ASCII "WebForge", inline
      `data:font/woff2` (no `my.woff2` request), `document.fonts.load('16px
      MyFont', 'WebForge')` non-empty, every `FontFace.status === 'loaded'`, and
      `document.fonts.check(...) === true`.
- [x] **Final 200 run on the current assets: `200/200 pass, 772 checks, 0
      fail`.** The oracle is now **frozen** (no further probe churn; re-run only
      if the assets change again). p7 then runs the full 301.
- [x] **p7 full run: `301/301 pass, 1820 checks, mapping issues 0`** (HTML + CSS
      via this module; JS via p7's own module). This is the final markup result.
      Code/JSON/oracle are frozen; the controller owns stage/commit and task
      status.

### Oracle strictness (no weakening)

- every replaced image: `complete && naturalWidth>0` **and** `src` starts with
  `data:image/`;
- every CSS background: present, `data:image/` URI, and decodes through
  `new Image()`;
- the only tolerated failure: `html-006 missing.png` (`naturalWidth===0`).

## Report to controller

Two shared-core observations (recorded, NOT patched here — see
`shared-core-defects.md` for the full record):

1. **Core editor `Git` menu item is not gated by `offlineOnly`**
   (`qfli_studio_core/lib/editor/editor_page.dart`, the `value: 'git'`
   PopupMenuItem). Local git is offline, but a remote push/pull would be a
   network entry. A core guard is the controller's call.
2. **Core `ToolCard` overflows at 2.0 text scale under a 320 px viewport**
   (`qfli_studio_core/lib/widgets/tool_widgets.dart:120` — fixed-height Column
   with a `Spacer` and multi-line text; observed `RenderFlex overflowed by 12
   pixels` and larger at 44 px). The product cannot fix this without editing
   core. Acceptance coverage is **not reduced**: the full integrated tools grid
   keeps a real positive no-overflow regression at 320×640 / 2.0, which fails
   honestly until the shared-core fix lands. This is a generic core adaptive-
   layout defect (shared-core channel owns it); it is **not** a Web home-merge
   change.

Transient, not attributable to this task: core `editor_page.dart` was mid-edit
by another worker (compile error `Expected 'else' or comma`) and the
not-yet-committed `test/web_terminal_release_test.dart` showed 4 failures. Both
were confirmed pre-existing by temporarily stashing **only this task's own two
`lib/` files** (never another worker's paths) and re-running; the failures
persisted unchanged.
