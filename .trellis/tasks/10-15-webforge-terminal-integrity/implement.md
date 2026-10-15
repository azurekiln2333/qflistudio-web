# Execution plan

## Steps

1. [x] Audit both terminal surfaces and the shared core (read-only).
2. [x] Write `research/core-terminal-findings.md`.
3. [x] Write `test/web_terminal_release_test.dart` covering:
   - built-in commands (`pwd`, `help`, `clear`, unsupported command)
   - execute + exit-code reporting (nonzero + silent success)
   - cancel/interrupt
   - exit/quit closing the session (`TerminalManager.onExitRequested`)
   - console error回传 via `appendDebug`
   - offline gating (online button absent, `showOnline` no-op)
   - standalone Terminax local-only session
4. [x] Run `flutter analyze --no-pub lib test` — clean.
5. [x] Release suite verified by the controller's serial run: 10/10
   (`.trellis/tasks/10-15-webforge-store-readiness/terminal-review-tests.log`,
   summarized in `research/verification-record.md`).
6. [x] No qfli_web-scope defect found; no `lib/` fix. Shared-core `git`
   shortcut gap routed to the core owner (findings §6.1).
7. [x] Spec update: `Quality Guidelines` and the `index.md` Quality Check gained
   the shared-terminal verification pattern.
8. [x] Controller committed the owned release suite and task records in c19bcfe.

## Validation

```bash
flutter analyze --no-pub lib test
flutter test --no-pub --concurrency=1 test/web_terminal_release_test.dart
flutter test --no-pub --concurrency=1 test/web_preview_current_file_test.dart
flutter test --no-pub --concurrency=1 test/web_tools_navigation_test.dart
```

## Review gate

- Test asserts user-visible text/tooltips and transcript contents, not private
  fields, except where the shared API is the only observable surface
  (`sessionCount`, `busy`), matching the core suite's precedent.
- No shared-core writes. No edits to `lib/main.dart`,
  `lib/pages/web_tools_page.dart`, `pubspec.yaml`, assets, platform config.
- `git add` limited to this task's own files.

## Rollback points

- After step 3: if the harness cannot drive the shared widgets cleanly, reduce
  to the directly-observable contracts and note the limitation.
- After step 6: if a defect requires a shared-core change, stop and report to
  the main controller instead of editing the core.
