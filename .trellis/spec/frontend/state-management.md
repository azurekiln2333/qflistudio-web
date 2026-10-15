# State Management

> How `qfli_web` manages state. This is a Flutter app built on
> `qfli_studio_core` stores and `flutter` primitives — there is no Redux/Provider
> graph in this repository.

---

## State Layers

| Layer | Mechanism | Owner |
|-------|-----------|-------|
| Product profile | `const StudioProfile webProfile` + `StudioProfile.current` | `lib/main.dart` |
| App stores | `ProjectStore`, `AuthStore`, `SettingsStore` (core `ChangeNotifier`) | created in `lib/main.dart`, passed to `QfliApp` |
| Screen state | `StatefulWidget` local fields + `setState` | `lib/pages/*` |
| Runtime session | `WebRuntimeSession?` field + stream subscriptions | screen state |

## Local Pattern

- Stores are constructed once in `main()` and injected into the shared
  `QfliApp`; screens receive the store they need (`WebToolsPage({store})`).
- Watch a store with `ListenableBuilder` / `ListenableBuilder(listenable:
  store)` instead of manual listeners:

```dart
Widget build(BuildContext context) => ListenableBuilder(
  listenable: widget.store,
  builder: (context, _) { /* read widget.store.projects */ },
);
```

Reference: `_WebServerToolsViewState.build`.

- Derived selection is resolved during build (pick the selected project or fall
  back to the first), not cached in a field that can go stale:

```dart
final path = projects.any((p) => p.path == _selectedPath)
    ? _selectedPath
    : projects.isEmpty ? null : projects.first.path;
```

- Runtime streams are subscribed after a successful start and cancelled on stop
  /dispose (`_requests`, `_debug` in `_WebServerToolsViewState`).
- `setState` marks only the screen dirty; never mutate `StudioProfile.current`
  after startup in product code.

## Persistence

- Project configuration is written to the project's `.qfli/web.json` through the
  settings dialog, which builds a fresh map and validates it with
  `WebProjectConfig.parse` before writing (`_WebProjectSettingsDialogState._save`).
- Never persist an unvalidated config, and never write the config from the
  server start path.

## Common Mistakes

- Recreating `ProjectStore`/`AuthStore`/`SettingsStore` inside a screen.
- Holding `WebRuntimeSession` in a global instead of the screen that started it.
- Reading `StudioProfile.current` and mutating it from UI code.
- Caching the selected project path without re-validating it against the current
  store list.
