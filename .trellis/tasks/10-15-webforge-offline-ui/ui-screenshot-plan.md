# UI verification record (five pages, narrow, large text, light/dark)

Status: **verified via real-device visual review + existing widget/core suites.**
Not a 12-image screenshot deliverable — no `web_ui_screenshots_test.dart` exists
and none is planned. The earlier "planned, 12 shots" draft was never executed
and is superseded by this record.

---

## What was actually verified

### 1. Five pages — real-device visual check (controller)

- The controller visually reviewed all **five pages** (首页 / 工具 / 教程 /
  示例 / 我的) on a real device.
- Artefact: the parent task produced
  `.trellis/tasks/10-15-webforge-store-readiness/` → `ui-five-pages-redacted.jpg`
  (redacted). The **unredacted original** contains another app's PIP and is kept
  **local only** — it is not committed and must not be reproduced.
- This confirms the real, rendered shell: navigation bar/rail, the integrated
  tools tab (本地服务 + 编解码 + core 终端 + 通用, **no HTTP tab / no proxy
  editor**), the local tutorial/example variants, and the offline-only profile
  page (no login/账号 sections).

### 2. Narrow (320×640) and 2.0 text scale — existing automated suites

- Covered by the product widget suite, not screenshots:
  - `test/web_tools_navigation_test.dart` →
    `integrated tools grid survives narrow large-text viewport` (positive
    no-overflow on the complete tools grid at 320×640 / 2.0);
    `all five pages survive narrow large-text viewport`.
  - The shared core `ToolsGrid` regression added with `7b8b7f2`;
    `ToolCard` text-scaling-aware extent.
- These are the authoritative narrow/large-text checks. They pass; no new
  screenshot harness is claimed.

### 3. Light and dark — existing core/product suites

- Theme is driven by `SettingsStore` through `QfliApp._appearance`; light/dark
  coverage comes from the existing widget/core suites (core light+dark
  regressions in `7b8b7f2`, product widget tests). No product-specific dark
  screenshot set is claimed.

---

## Status vs. the old draft (explicitly not done)

- ❌ `test/web_ui_screenshots_test.dart` — **does not exist and will not be
  added.** The old draft named it as a planned file.
- ❌ 12-shot matrix (normal/narrow/large-text/dark × screens) — **not
  produced.** The matrix above is historical draft, not a deliverable.
- ❌ `research/screenshots/` output — not produced.

## Core overflow note (historical, now fixed)

The old draft warned that scenario 3 would show the shared-core `ToolCard`
overflow "until the core fix lands". That fix **landed** (`7b8b7f2`), owned by
the shared-core channel; no overflow remains, and the product keeps only the
positive 320×640 / 2.0 regression (no reverse sentinel).

## If a screenshot set is later wanted

It would be a separate, explicitly-scoped task (harness + matrix +
`research/screenshots/`), run by the controller — deliberately not this task's
deliverable.
