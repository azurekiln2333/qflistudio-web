# Quality Guidelines

> Quality standards for `qfli_web` UI and widget tests. Behavior is verified
> through the real widget tree and real HTTP where possible.

---

## Required Checks

```bash
flutter analyze --no-pub lib test
flutter test --no-pub --concurrency=1 test/web_app_test.dart test/web_tools_navigation_test.dart test/web_tools_page_test.dart
```

## Widget Testing Pattern

- Set the profile before pumping and restore it in teardown; construct real
  stores with a temp storage file:

```dart
final previous = StudioProfile.current;
StudioProfile.current = webProfile;
final store = ProjectStore(storageFile: File('${temp.path}/projects.json'));
addTearDown(() {
  StudioProfile.current = previous;
  store.dispose(); auth.dispose(); settings.dispose();
  temp.deleteSync(recursive: true);
});
```

Reference: `test/web_tools_navigation_test.dart`.

- Pump real route transitions (`pumpAndSettle`) before interacting with tabs and
  dialogs; assert with real Material text/tooltips (`find.byTooltip`,
  `find.text`).
- Assert persisted effects, not just that a button was tapped — e.g. read
  `.qfli/web.json` back and compare the decoded map
  (`test/web_tools_navigation_test.dart`).
- Enter the shared Tools tab and interact directly with the inline `本地服务`,
  `Web 编解码` and inspection controls; assert five destinations and no extra
  `Web 工具` feature-hub route. Advance the PageView transition (300 ms), then
  allow real resource-discovery/isolate work through `tester.runAsync`, observing
  the public busy indicator before `pumpAndSettle`. Assert actual tool results
  and cover narrow layouts and 2x text scaling in both themes. See
  [Offline Web Tools](./offline-web-tools.md) for limits and semantic regressions.

## Verifying shared-core terminal surfaces

The WebForge terminal (editor `TerminalPane` and standalone
`TerminaxTerminalPage`) is implemented in `qfli_studio_core`. Verify it by
driving the shared widgets from this repo's suite with the real Web profile
installed — never by re-implementing or instrumenting production widgets.
Reference: `test/web_terminal_release_test.dart`.

Key pitfalls proven while writing that suite:

- **Transcript lines are not plain `Text`.** The editor pane renders each row as
  `SelectableText`; the standalone terminal renders `Text.rich`. Match with
  `find.textContaining` / `find.text` (both cover these), never a
  `widget is Text && widget.data == ...` predicate, which misses them.
- **The transcript is a lazy `ListView.builder`.** A row that has scrolled out
  of the built range is not in the tree at all, so assert on a line near the
  bottom of long output (e.g. the last `help` line), not the first.
- **Model the offline gate, don't guess it.** `EditorPage` passes
  `onlineEnabled: StudioProfile.current?.offlineOnly != true`; mount the pane
  with `onlineEnabled: false` and assert `Icons.cloud_outlined` is absent and
  `showOnline()` opens no session.
- **Replace, don't add, a delegate.** The Web profile has no
  `terminalCommandDelegate`; a cancellation test installs a profile-local
  delegate and restores it in `addTearDown`, so the shared wiring is exercised
  without changing the shipped profile.

## Forbidden Patterns

- Asserting on internal fields instead of user-visible text, tooltips or
  persisted files.
- Widget tests that start a real browser or a real native engine; keep those in
  the runtime/native suites.
- Adding debug-only hooks to production widgets to make a test pass.
- Hardcoded widget geometry that breaks under large text / small viewports
  without a layout test.

## Code Review Checklist

- Does the screen dispose every controller, subscription and owned session?
- Are all `await` continuations guarded by `mounted`?
- Is product configuration read from `StudioProfile`/`webProfile` rather than
  duplicated string constants?
- Do UI actions that write files validate through `WebProjectConfig.parse`
  first?
- Are tests asserting the persisted/observable result, and do they clean up temp
  state?
