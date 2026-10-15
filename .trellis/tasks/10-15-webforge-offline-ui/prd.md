# WebForge offline UI and networking-entry consolidation

Parent: `10-15-webforge-store-readiness`

## Goal

Make WebForge a genuinely offline product: no reachable network entry anywhere in
the product, a coherent (not split) home + tools UI, and a layout that survives
narrow screens and large text — all without touching shared core behaviour.

## Background

- `qfli_web` is a Flutter app that reuses `qfli_studio_core` (shared editor,
  shell, stores, terminal, offline tools). Core is read-only for this task.
- `webProfile` in `lib/main.dart` already declares `isOffline: true` (so
  `offlineOnly` defaults to true). Core already hides, under `offlineOnly`:
  the profile login/account sections, the cloud project scope + "new cloud
  project", the community tutorial feed (local variant instead), and the editor
  AI assistant / online terminal / online-run fallback.
- What remains is **product-owned** networking surface plus UI coherence.

## Requirements

1. **Audit every reachable network entry in this product**, reusing the existing
   `offlineOnly` / `isOffline` capability of `qfli_studio_core`; hide product
   entries that this repo owns:
   - Git (including any remote push/pull entry),
   - login / register / account,
   - cloud terminal (online terminal),
   - cloud project,
   - HTTP tool (arbitrary external requests),
   - external proxy (API proxy target forwarding).
2. **Keep the loopback local web preview** (`127.0.0.1`), including opening it in
   the system browser. It must not be disabled by the offline hide.
3. **Home UI coherence / tool consolidation**: the Web tools surface must be one
   integrated surface reached through the existing shell tools tab, not a
   separate pushed page that duplicates navigation.
4. **Exactly five PageView pages** preserved: 首页 / 工具 / 教程 / 示例 / 我的.
   No page may be added, removed, or made unreachable.
5. **The whole UI must survive narrow screens (e.g. 320 px width) and large
   text (e.g. 2.0 text scale)** across the five pages **and** the tools
   surface; no overflow exceptions. Verified by a **real positive** no-overflow
   regression on the complete tools grid at 320×640 / 2.0. (The shared-core
   `ToolCard` adaptive-layout defect this used to expose was fixed by the
   shared-core channel in `7b8b7f2`; `shared-core-defects.md` records it.)
6. No product merge in this repo: any cross-product merge happens in the
   sub-product, never in core.
7. **Concrete per-example markup assertions**: this task owns
   `scripts/web_markup_assertions.mjs`, giving each of the 100 HTML and 100 CSS
   examples at least one concrete semantic-content / attribute or computed /
   interactive value assertion (no generic marker, no stylesheet-exists, no
   DOM-reads-itself). p7's runner consumes the export.

## Constraints

- Writable repo: `D:/MyNewProjects/qfli_web` only. Do **not** edit
  `qfli_studio_core` (shared core). Shared-core defects are reported, not fixed.
- Do **not** modify: `pubspec.yaml`, content assets, terminal delegation,
  platform native config, shared core.
- Owned files: `lib/main.dart`, `lib/pages/web_tools_page.dart`, new product
  tool-integration UI file(s) (`lib/pages/web_tools_overview.dart`),
  `scripts/web_markup_assertions.mjs`, `test/web_app_test.dart`,
  `test/web_tools_navigation_test.dart`, `test/web_tools_page_test.dart`,
  and this task's Trellis docs.
- The content owner (`wD:p7`, task `10-15-webforge-content-curriculum`) may wire
  a content repository in `lib/main.dart` (done: `WebForgeContentRepository`)
  and owns the runner (`scripts/run_examples.mjs`) + JS assertion module.
- `dart`/`flutter` and platform builds are paused during the shared device
  window; this task's verification is controller-serialised.
- Commit explicitly staged own files only, never `git add .`.
- No platform builds.

## Acceptance Criteria

- [x] No product-owned UI path reaches the network with `offlineOnly` set:
      the HTTP tool and external proxy entry are absent from the shipped tools
      surface; no git remote / cloud / login entry is reachable from this repo.
- [x] Loopback local web preview still starts and its URL is still openable.
- [x] Tools surface is reachable through the shell tools tab as one integrated
      body (no duplicated second entry page).
- [x] `PageView` item count remains exactly 5 and all five destinations are
      reachable.
- [x] Widget tests cover the five-page navigation, the removed network entries
      and the narrow/large-text layouts, including a **real positive**
      no-overflow assertion on the complete tools grid at 320×640 / 2.0 (no
      reverse "defect must still exist" sentinel). The shared-core `ToolCard`
      fix (`7b8b7f2`) has landed; runs green.
- [x] Five pages visually reviewed on a real device by the controller; redacted
      artefact `ui-five-pages-redacted.jpg` lives in the parent task (unredacted
      original is local-only). Narrow 2.0 and light/dark are covered by the
      existing widget/core suites — see `ui-screenshot-plan.md` (no 12-shot
      screenshot deliverable is claimed).
- [x] `flutter analyze --no-pub lib test` is clean.
- [x] Controller commits verified batches using explicit product-owned paths;
      all worker writing is stopped before staging.
- [x] `scripts/web_markup_assertions.mjs` provides 100 HTML + 100 CSS concrete
      per-example assertions (real decode / media playback / CSS computed), plus
      a 320×640/2.0-capable runtime probe; syntax/export verified; handed to
      p7's runner and run independently by this task.
- [x] Read-only content cross-review recorded in
      `research/content-cross-review.md`, with the F2 retraction synced.
- [x] Markup oracle re-run after the media fixes: **200/200 (772 checks)** for
      HTML+CSS by this module; p7's full run **301/301, 1820 checks, mapping
      issues 0**. Oracle frozen; code/JSON frozen.
- [x] Core findings closed by shared revisions `54a58ca` / `b7b2d2e` / `7b8b7f2`;
      product Flutter **82/82** and shared targeted **116/116** green.

## Notes

- Core capability references: `StudioProfile.offlineOnly` / `isOffline`,
  `HomePage._createPageView` (5 pages), `FunctionsTab` / `ToolsGrid` /
  `StudioProfile.toolsTabBuilder`.
