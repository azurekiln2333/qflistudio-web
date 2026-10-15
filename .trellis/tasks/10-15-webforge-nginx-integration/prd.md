# WebForge native Nginx device integration test

Child task of `10-15-webforge-store-readiness`. Owns the executable device
gate for the embedded native Nginx runtime.

## Problem

`tool/nginx_smoke.dart` is the only end-to-end native Nginx check, but its
`main` swallows failures:

```dart
} catch (error, stack) {
  debugPrint('[NGINX_SMOKE] FAIL $error\n$stack');
} finally { ... }
```

It never rethrows, so the process exits 0 even when every check failed. An
automated device run therefore reports success on a broken engine — a false
pass. There is also no `integration_test/` entry that drives the smoke through
the test framework, so the smoke cannot be wired into a normal device test
command with a real pass/fail exit.

## Requirements

- `tool/nginx_smoke.dart`: after logging `[NGINX_SMOKE] FAIL ...`, rethrow so a
  failure produces a non-zero exit. Keep the existing `finally` cleanup and the
  standalone tool entry (`flutter run -t tool/nginx_smoke.dart`) unchanged.
- New `integration_test/nginx_runtime_test.dart`:
  - Initialize `IntegrationTestWidgetsFlutterBinding`.
  - Run `smoke.main` inside `runAsync`.
  - Assert `tester.takeException()` is null so a `runAsync`-captured error
    cannot pass silently.
  - Skip with a clear message **only on a desktop host without a packaged
    runtime**. Android, iOS and HarmonyOS ship the engine with the app: a
    missing runtime there must FAIL the test, never skip (a skip would let a
    broken, runtime-less package pass).
- Do not change `lib/main.dart` or the product run entry.

## Constraints

- Files this task may write: `tool/nginx_smoke.dart` (minimal add: rethrow +
  `dart format` only), `integration_test/nginx_runtime_test.dart`, and this
  task's own `.trellis/tasks/10-15-webforge-nginx-integration/**` docs.
- Touch nothing else: no shared core, no native/build files, no other tests,
  no `pubspec.yaml`.
- No `flutter`/`dart` execution by this worker; the main controller runs the
  device test serially and commits after review.

## Acceptance Criteria

- [ ] `tool/nginx_smoke.dart` rethrows after logging FAIL; `finally` intact.
- [ ] `main` still runs standalone with an unchanged product entry.
- [ ] `integration_test/nginx_runtime_test.dart` runs the smoke via
      `runAsync` and fails on any smoke error (`takeException` null check).
- [ ] Non-desktop platforms never skip: a missing runtime on Android/iOS/
      HarmonyOS is a test **failure**; only a desktop host without a packaged
      runtime may skip.
- [ ] Android explicitly asserts the executable path is non-null (missing
      `libnginx_exec.so` fails with a clear reason).
- [ ] `dart format` clean (verified by the controller).
- [ ] Controller-run device result recorded in this task's `research/`.
