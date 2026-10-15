# Frontend Development Guidelines

> Guidelines for the Flutter UI owned by `qfli_web`. Shared editor, shell and
> stores come from `qfli_studio_core`.

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | `lib/pages` layout, profile wiring, naming | Implemented |
| [Component Guidelines](./component-guidelines.md) | Widget structure, props, async guards, a11y | Implemented |
| [State Management](./state-management.md) | Store injection, local state, config persistence | Implemented |
| [Quality Guidelines](./quality-guidelines.md) | Widget-test pattern, forbidden patterns, review checklist | Implemented |
| [Content Imports](./content-import.md) | MD3 catalogs, custom filenames, editor and project imports | Implemented |

## Pre-Development Checklist

- New or changed screen → read
  [Directory Structure](./directory-structure.md) and
  [Component Guidelines](./component-guidelines.md).
- Touching stores, selection or persisted project settings → read
  [State Management](./state-management.md).
- Offline catalogs and code imports → read
  [Content Imports](./content-import.md).

## Quality Check

- Run `flutter analyze --no-pub lib test` and the affected widget suites.
- Verify the persisted result (e.g. `.qfli/web.json`) and the visible editor
  file, not just that an action was triggered.
- Terminal/editor-surface changes → read the shared-surface section of
  [Quality Guidelines](./quality-guidelines.md) and run
  `flutter test --no-pub --concurrency=1 test/web_terminal_release_test.dart`.
