# Execution plan

## Steps

1. [x] Add `rethrow;` after the FAIL `debugPrint` in `tool/nginx_smoke.dart`
       (comment + `rethrow;` only; no other change to that file).
   [x] Device follow-up: `_supportsRecursiveWatch` watches the independent probe
       directory instead of the project root, fixing the Android inotify
       double-watch assertion. SSE detection in `main` unchanged.
2. [x] Create `integration_test/nginx_runtime_test.dart`:
   - `IntegrationTestWidgetsFlutterBinding.ensureInitialized()`
   - `WebRuntime.nginxExecutable()` availability probe → `markTestSkipped` when
     absent
   - `tester.runAsync(() => smoke.main())`
   - `expect(tester.takeException(), isNull)`
3. [x] Record the change and the pending device result in
       `research/device-verification.md`.
4. [ ] Hand off to the controller for serial: `dart format` check,
       `flutter analyze --no-pub tool integration_test`, then a real device
       `flutter test integration_test/nginx_runtime_test.dart -d <device>`.

## Validation

```bash
dart format --output=none --set-exit-if-changed tool/nginx_smoke.dart integration_test/nginx_runtime_test.dart
flutter analyze --no-pub tool integration_test
flutter test integration_test/nginx_runtime_test.dart -d <device>
```

## Review gate

- `tool/nginx_smoke.dart` propagates errors with `rethrow` and probes a separate
  directory to avoid Android duplicate-root watcher assertions.
- New test asserts a real fail on a broken engine **and** on a missing runtime
  for Android/iOS/HarmonyOS (no skip path there); only a desktop host without a
  packaged runtime may skip.
- No edits to `lib/main.dart`, shared core, native/build files, other tests or
  `pubspec.yaml`.
- `git add` limited to this task's own two source files.

## Rollback points

- After step 1: if `rethrow` changes the standalone tool's expected behaviour
  (it should only change the failure exit), stop and report.
- After step 2: if the probe cannot distinguish "unavailable" from "broken",
  prefer running the smoke and letting it fail over skipping. Non-desktop
  platforms must never skip.
