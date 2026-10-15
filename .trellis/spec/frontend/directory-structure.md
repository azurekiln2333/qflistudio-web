# Directory Structure

> How `qfli_web` UI code is organized. This is a Flutter app; the shared editor,
> stores and shell live in the sibling `qfli_studio_core` package.

---

## Layout

```
lib/
├── main.dart          # webProfile (StudioProfile) + app bootstrap
├── content/webforge_content_repository.dart # Product-owned offline curriculum
└── pages/
    ├── web_tools_overview.dart # Tools tab body using the shared ToolsGrid
    └── web_tools_page.dart     # Reusable server, HTTP and codec views
```

- `main.dart` defines `webProfile` and supplies `webPreviewFactory`,
  `toolsPageBuilder`, `toolsTabBuilder` and `contentRepositoryFactory` to the shell.
  It is intentionally a `const` so tests can assert the profile without running
  `main()` (see `test/web_app_test.dart`).
- `lib/pages/` holds product-owned screens and embedded tool bodies. Private sub-widgets
  live in the same file (e.g. `_HttpTool`, `_TextTool`,
  `_WebProjectSettingsDialog`) until a second screen needs them.
- Everything reusable (editor, home tabs, project cards, stores, templates,
  settings, splash, localization) comes from `package:qfli_studio_core/...`.
  Do not copy shared widgets into this repository.

## Where New UI Goes

- A new Web tool → a reusable view in `lib/pages/`, registered in
  `WebToolsOverview` through `toolsTabBuilder`. Keep five shell pages; consolidate
  Web-only cards within this product rather than altering core navigation.
- Offline WebForge shows local server and codec tools; HTTP and proxy controls
  are excluded by the profile's `offlineOnly` policy.
- A product-wide behaviour (title, templates, entry names, supported
  extensions) → the `webProfile` constant in `lib/main.dart`.
- Navigation between top-level screens is owned by `qfli_studio_core`; WebForge
  narrows it through `webProfile` (`showHomeTabs: false`) rather than adding
  routes here.

## Naming Conventions

- Files: `lower_snake_case.dart`; one public widget per file named after it
  (`WebToolsPage` in `web_tools_page.dart`).
- Private widgets: leading underscore in the same file.
- Widget tests mirror the screen name: `web_tools_page.dart` →
  `test/web_tools_page_test.dart`.

## Examples

- Product screen with tabs, dialogs and async tooling:
  `lib/pages/web_tools_page.dart`.
- Profile-driven packaging asserted in tests: `test/web_app_test.dart`,
  `test/web_tools_navigation_test.dart`.
