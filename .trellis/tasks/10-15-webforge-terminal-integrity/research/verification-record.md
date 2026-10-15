# Verification record — WebForge terminal integrity

This file records verification **as reported by the main controller's serial
run**, not a self-run claim. During the build-mutex window this worker stopped
all `flutter`/`dart` commands at the controller's request; the controller then
ran the suite serially once the shared build cache was quiet.

## Suite

`test/web_terminal_release_test.dart` — 10 tests.

## Evidence

Controller-run command:

```
flutter test --no-pub --concurrency=1 --reporter expanded test/web_terminal_release_test.dart
```

Real log: `.trellis/tasks/10-15-webforge-store-readiness/terminal-review-tests.log`

Result (from that log):

```
00:00 +0: WebForge profile terminal contract the Web profile is offline-only with no host toolchain
00:01 +1: Editor TerminalPane (offline Web profile) built-in commands run against the real sandbox
00:01 +2: Editor TerminalPane (offline Web profile) an unknown command reports honestly instead of silently
00:01 +3: Editor TerminalPane (offline Web profile) a nonzero exit keeps its integer; success stays silent
00:01 +4: Editor TerminalPane (offline Web profile) the Stop control cancels a running command
00:01 +5: Editor TerminalPane (offline Web profile) interruptActive is a safe no-op with nothing running
00:01 +6: Editor TerminalPane (offline Web profile) console error output is returned to the transcript
00:01 +7: Editor TerminalPane (offline Web profile) offline gating hides the online terminal and blocks showOnline
00:01 +8: Standalone Terminax (offline Web profile) opens a local session and runs a built-in
00:02 +9: TerminalSession exit contract exit and quit request a session close without executing
00:02 +10: All tests passed!
```

**10/10 passed.**

## Earlier failures (closed)

During authoring, this worker's own intermittent run showed 4 failures. They are
**resolved and closed**; the controller's clean run above is authoritative.

| # | Failing test | Root cause | Resolution |
|---|--------------|------------|------------|
| 1 | built-in commands (`pwd`) | Assertion used a `Text.data` predicate; the editor pane renders rows as `SelectableText`, which it does not match | Use `find.textContaining` |
| 2 | unknown command | Same finder defect | Use `find.textContaining` |
| 3 | console error output | Same finder defect | Use `find.textContaining` |
| 4 | Terminax `help` | Asserted the *first* help line; the transcript is a lazy `ListView.builder` and that row scrolled out of the built range | Assert on the last help line ("其它系统命令在当前平台不可用") |

One earlier run also hit a shared-build-cache race
(`PathExistsException: ...cache.dill.track.dill`), caused by concurrent
`flutter test` invocations against the same build cache. That is the build-mutex
issue the controller coordinated; it is **not** a product or test defect.

## Environment note

A separate, unrelated failure mode was reported by the controller: an Android
release build saw `GeneratedPluginRegistrant` include `integration_test`, which
release excludes — suspected to be caused by concurrent `flutter test` runs
rewriting generated files. This worker started no build; all `flutter`/`dart`
usage stopped once the mutex request arrived.

## Scope reminders

- No `lib/` product code was changed (no Web-scope defect found).
- No file under `../qfli_studio_core` was changed.
- The offline `git status` shortcut gap is a shared-core concern, routed by the
  controller/Go coordinator; see `research/core-terminal-findings.md` §6.1.
