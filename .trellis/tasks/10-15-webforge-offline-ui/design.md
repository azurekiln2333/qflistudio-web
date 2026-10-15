# Design — WebForge offline UI and networking-entry consolidation

Parent: `10-15-webforge-store-readiness`

## Scope boundary

- **Smallest behaviour gap**: with `offlineOnly` already true, the product still
  exposes two network-reaching surfaces it owns — the `HTTP` tool (arbitrary
  external requests) and the project settings dialog's API proxy editor (target
  forwards to any `http(s)` host). The tools tab is also split: the shell renders
  an entry card that pushes a second page instead of one integrated surface.
- **Where it lives**: `lib/pages/web_tools_page.dart` (HTTP tab, proxy editor)
  and `lib/main.dart` (`toolsTabBuilder` unset, `toolsPageBuilder` pushes a page).
- **Files to change (all owned)**:
  - `lib/pages/web_tools_page.dart` — split the reusable server and codec
    surfaces out; hide the HTTP tab and the proxy editor under `offlineOnly`.
  - `lib/pages/web_tools_overview.dart` (new) — the integrated tools body for
    `toolsTabBuilder`, built on `qfli_studio_core`'s `ToolsGrid` / `ToolSection`.
  - `lib/main.dart` — set `toolsTabBuilder` on `webProfile`; keep
    `toolsPageBuilder` for the editor content-tool path.
  - `test/web_app_test.dart`, `test/web_tools_navigation_test.dart`,
    `test/web_tools_page_test.dart`.
- **Explicitly not doing**: no edits to `qfli_studio_core`; no `pubspec.yaml`,
  assets, terminal delegation, or native config changes; no change to the five
  `PageView` pages; no cross-product merge.

## Reuse of core capability

Core already keys every offline decision off `StudioProfile.offlineOnly`
(defaults to `isOffline`, both `true` in `webProfile`). This task adds **no new
core flag**; it only makes product-owned UI honour the same flag.

| Entry | Owner | Core already handles? | This task |
| --- | --- | --- | --- |
| Login / register / account / ICP | core `ProfileTab` | yes (`offlineOnly`) | nothing |
| Cloud project scope + new cloud project | core `HomeTab` | yes | nothing |
| Community tutorial feed | core `HomePage` | yes (local variant) | nothing |
| Editor AI assistant / online terminal / online-run fallback | core `editor_page.dart` | yes | nothing |
| Git menu item | core `editor_page.dart` | **no** (local git, offline) | report only |
| HTTP tool | **product** | n/a | hide under `offlineOnly` |
| External API proxy editor | **product** | n/a | hide under `offlineOnly` |
| Loopback local web preview | **product** | n/a | keep |

`Git` is core-owned and runs local git; any *remote* git operation would need a
core guard. Per constraints this is **recorded and reported to the controller**,
not patched here.

## Integrated tools surface

`StudioProfile.toolsTabBuilder` renders *inside* `FunctionsTab`'s Scaffold, and
when it is set the shell stops rendering the separate "功能" entry card — so
switching from `toolsPageBuilder` to `toolsTabBuilder` removes the duplicate
entry with no core change.

```
FunctionsTab (core Scaffold, AppBar '工具')
└── WebToolsOverview            (lib/pages/web_tools_overview.dart, product)
    └── ToolsGrid               (core, reusable)
        sections = [            (product-owned cards)
          '本地服务' → push WebServerToolsView
          '编解码'   → push WebCodecToolsView
        ]
        onOpenTerminal          (core-provided 终端 card, unchanged)
        + core '通用' offline tools group (automatic)
```

`WebToolsOverview` must not nest another Scaffold/AppBar (core contract).
`toolsPageBuilder` stays wired to `WebToolsPage` because core's
`ContentToolsPage` and the editor's "内容工具" item resolve the product tools
page through it; removing it would regress other entry points.

## Offline gating inside the product

- `WebServerToolsView`: unchanged local preview (start/stop, copy URL, open in
  browser). Opening the loopback URL is local; keep it.
- `_WebProjectSettingsDialog`: under `offlineOnly`, omit the API-proxy section
  and do not emit `proxies` on save (merge-preserve any existing rules so a
  pre-existing config is not silently rewritten into a network entry).
- `WebToolsPage`: under `offlineOnly`, render only 服务器 / 编解码 tabs and drop
  the HTTP tool from both the tab list and the body. Non-offline products keep
  the three-tab behaviour (the widget stays usable by tests directly).
- Codec tool (JSON / URL / Base64) is pure in-process computation → offline-safe.

## Layout robustness

- Tools must not overflow at 320 px width or 2.0 text scale: use `ListView` /
  `Wrap` / `SingleChildScrollView` and `Expanded`-guarded rows, mirroring the
  core `ProjectStore` grid approach; the settings dialog already follows this.

## Rollback

Product-local, three files. Reverting `toolsTabBuilder` in `main.dart` restores
the previous two-page navigation; reverting the gating in `web_tools_page.dart`
restores the HTTP tab. No data migration, no persisted-format change.
