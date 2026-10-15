# Shared-core defects observed by `10-15-webforge-offline-ui`

Recorded for the controller's serialised verification. **Nothing here was
patched by this task** — `qfli_studio_core` is outside this task's writable
scope. Both items below have since been FIXED by the shared-core owner;
hashes are recorded for traceability.

---

## C1 — Core `ToolCard` overflows at 320 px / 2.0 text scale — FIXED (7b8b7f2)

- **Where**: `qfli_studio_core/lib/widgets/tool_widgets.dart:120` (`ToolCard`
  build → `Column`).
- **Cause**: fixed card height (`ToolsTheme.cardHeight`) with a `Spacer()` and
  multi-line title + description; at 2.0 text scale the text stack exceeds the
  fixed height.
- **Observed**: `RenderFlex overflowed by 12 pixels` on the short cards and
  `44 pixels` on taller ones, viewport 320×640, `TextScaler.linear(2.0)`.
- **Reproduced via**: a bare core `ToolsGrid` probe **and** the product's
  `WebToolsOverview` (which is just a core `ToolsGrid`). Product-owned views
  (`WebServerToolsView`, `WebCodecToolsView`) do **not** overflow.
- **Impact**: the tools surface (product-integrated, core-rendered) overflows
  under large text. This is the generic shared-core adaptive-layout defect; it
  is **not** a Web home-page merge and does not belong to this product.
- **Product stance**: not fixable without editing core; the shared-core channel
  owned the fix. Coverage was **not reduced** —
  `test/web_tools_navigation_test.dart` keeps a **real positive** no-overflow
  regression on the complete tools grid at 320×640 / 2.0. No reverse
  "defect-must-still-exist" sentinel is used.
- **Fix landed**: `7b8b7f2 fix(ui): adapt tools grid cards to large text` —
  text-scaling-aware grid extent with 320px/2x light+dark regressions. The
  product's positive regression now passes against that revision.

## C2 — Core editor `Git` menu item not gated by `offlineOnly` — FIXED (54a58ca)

- **Where**: `qfli_studio_core/lib/editor/editor_page.dart`, the
  `PopupMenuItem(value: 'git', ...)`.
- **Issue**: unlike the AI assistant and the online terminal (both correctly
  gated by `StudioProfile.current?.offlineOnly != true`), the Git entry is
  always shown. Local git is offline, but a remote `push`/`pull` would be a
  network entry, which an offline-only product must not expose.
- **Product stance**: core-owned; recorded only.
- **Fix landed**: `54a58ca` (editor Git/cloud/AI gates) and `b7b2d2e`
  (background refresh + terminal network/Git shortcuts). No further core request
  from this task.
