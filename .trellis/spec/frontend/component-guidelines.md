# Component Guidelines

> How `qfli_web` builds Flutter widgets. The product owns screens in
> `lib/pages/`; shared editor/shell widgets come from `qfli_studio_core`.

---

## Component Structure

- Public screen widget: `StatelessWidget` or `StatefulWidget` with a `const`
  constructor and `Key? key`, e.g. `WebToolsPage({required this.store})` in
  `lib/pages/web_tools_page.dart`.
- Private helper widgets in the same file when only that screen uses them
  (`_HttpTool`, `_TextTool`, `_ProxyDraft`, `_WebProjectSettingsDialog`).
- State objects own their controllers and cancel subscriptions in `dispose()`:

```dart
@override
void dispose() {
  unawaited(_requests?.cancel());
  unawaited(_debug?.cancel());
  final server = _server;
  if (server != null) unawaited(server.stop());
  super.dispose();
}
```

Reference: `_WebServerToolsViewState.dispose`, `_HttpToolState.dispose`.

## Props Conventions

- Pass collaborators and stores explicitly (`required this.store`); do not read
  globals from widgets.
- Product-wide configuration is read from `StudioProfile.current` /
  the `webProfile` constant, not hardcoded in widgets.
- Use Material 3 widgets and `Theme.of(context).colorScheme` for colour; the app
  shell supplies the theme.

## Async & Mounted Guards

- After every `await` in a `State`, check `mounted` before `setState` or
  navigation. The runtime start path does this twice, including stopping a
  server that arrived after the widget was disposed:

```dart
final server = await WebRuntime.start(path);
if (!mounted) { await server.stop(); return; }
```

Reference: `_WebServerToolsViewState._start` (`lib/pages/web_tools_page.dart`).

## Styling Patterns

- Spacing with `SizedBox` and standard `EdgeInsets`.
- Long diagnostic output uses `SelectableText` with
  `TextStyle(fontFamily: 'monospace')` and is capped/truncated by the owner.
- Lists that can grow unbounded are bounded in code (the log list is trimmed to
  200 entries in `_append`).

## Accessibility

- Icon-only buttons carry `tooltip:` (e.g. `'项目服务设置'`, `'复制地址'`).
- Disabled actions are expressed by `null` callbacks, not by hiding the control,
  so the affordance stays visible (`onPressed: busy ? null : _stop`).

## Common Mistakes

- Keeping a `Timer`/`StreamSubscription`/server alive after `dispose`.
- Calling `setState` after an `await` without a `mounted` guard.
- Hardcoding product strings instead of using the profile/localization, or
  duplicating a shared widget instead of using `qfli_studio_core`.
