# Technical design

## Boundary

`qfli_web` may only add/modify its own files. The terminal UI and shell live in
`qfli_studio_core` and are imported as a package
(`package:qfli_studio_core/...`). Verification is therefore done by *driving*
the shared widgets from this repo's test suite with the Web profile installed,
not by re-implementing them.

## What the release test must build

A single suite, `test/web_terminal_release_test.dart`, with these groups:

1. **Editor TerminalPane (real widget tree)**
   - Mount `TerminalPane` directly (as core's `terminal_pane_test.dart` does)
     with `onlineEnabled: false` to model the offline Web profile, into a temp
     working directory.
   - Built-ins over a real backend: `pwd` prints the sandbox path; `help`
     prints the sandbox help; `clear` empties the transcript; unknown command
     yields the honest unsupported message.
   - Execute + exit code: `attachOutput`/backend run a command; a nonzero status
     surfaces `exit code N` and success stays silent.
   - Cancel: `interruptActive()` reaches the backend while a command is running.
   - Exit: `TerminalSession`-level `exit`/`quit` closes the session via
     `onExitRequested` (verified through `TerminalManager`).
   - Console error回传: `appendDebug` appends a debug line visible in the
     transcript.
   - Offline gating: with `onlineEnabled: false`, the cloud terminal button is
     absent and `showOnline()` is a no-op.

2. **Standalone Terminax**
   - Mount `TerminaxTerminalPage` with a Web profile and a temp storage dir; it
     creates exactly one local session and runs a built-in (`pwd`) in it.
   - Confirm no online/cloud/login affordance appears.

3. **Current-file preview interaction**
   - Reuse the existing `web_preview_current_file_test.dart` semantics at the
     release level: tap uses the default URL, long-press resolves the current
     file, and a preview failure is surfaced (already covered; the release test
     asserts the terminal receives the console line via `appendDebug` to keep
     the "错误回传" contract in one place).

## Contracts relied on

- `TerminalPaneState`: `attachOutput`, `interruptActive`, `appendDebug`,
  `appendSystem`, `showOnline`, `focusInput`, `sessionCount`, `addSession`.
- `ShellBackend`: `execute`, `interrupt`, `lastExitCode`, `output`, `busy`.
- `TerminalSession`: `submit`, `interrupt`, `lines`, `onExitRequested`.
- `StudioProfile`: `offlineOnly`, `terminalCommandDelegate`.

These are public/shared API; no production widget is instrumented for the test.

## Compatibility / rollback

- Additive only: one new test file, plus (if a defect is found) a narrowly
  scoped fix inside `qfli_web/lib`. Rollback = delete the test file / revert the
  single commit.
- No shared-core edits, so no cross-repo compatibility risk.

## Validation commands

```bash
flutter analyze --no-pub lib test
flutter test --no-pub --concurrency=1 test/web_terminal_release_test.dart
flutter test --no-pub --concurrency=1 test/web_preview_current_file_test.dart
```
