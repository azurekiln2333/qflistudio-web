# Device verification record

## Device evidence so far

The main controller ran the smoke on a real Android device. It surfaced the
inotify double-watch assertion described above, which is now fixed by watching
an independent probe directory. Re-run pending.

## Change summary

### `tool/nginx_smoke.dart` (minimal)

1. Added `rethrow;` after the existing FAIL `debugPrint`, plus a short
   explanatory comment. The `finally` cleanup (client close, session stop,
   upstream close, temp-project delete) is unchanged, and the standalone
   `main()` entry is unchanged.

   Effect: a run that logs `[NGINX_SMOKE] FAIL` now exits non-zero instead of 0.
   This is the false-pass fix.

2. `_supportsRecursiveWatch` now watches an **independent probe directory**
   (`<root>/.watch-probe`) instead of the project root:

   ```dart
   subscription = probe.watch(recursive: true).listen(...);
   ```

   **Real-device finding (Android):** the live middleware already holds a
   recursive watch on the project root, and the Dart VM backs each recursive
   watch with an inotify instance. Adding a second recursive watch over the same
   tree tripped a Dart VM `AssertionError`. The probe only needs to answer
   "does recursive watching work here", so it owns a directory nobody else
   watches. The SSE live-reload check in `main` is unchanged and still performs
   the real reload assertion against the running server. No `AssertionError` is
   caught or suppressed, and Android is never skipped.

Every other line in the tool is the user's existing native work and was left
untouched.

### `integration_test/nginx_runtime_test.dart` (new)

- `IntegrationTestWidgetsFlutterBinding.ensureInitialized()`.
- Availability gate:
  - **Android — never skipped.** `WebRuntime.nginxExecutable()` is asserted
    `isNotNull` (a null path means the package is missing
    `libnginx_exec.so`), then the smoke runs. A runtime-less Android build
    therefore fails this test instead of passing.
  - **iOS / HarmonyOS — never skipped.** The engine ships as an embedded shared
    library with no executable path to probe; the smoke runs directly and fails
    for real if the library is absent.
  - **Desktop (Windows / Linux / macOS) — skip only when no packaged runtime
    exists**, which is a legitimate developer-machine case. If an executable is
    present, the smoke runs.
- `await tester.runAsync(smoke.main)`.
- `expect(tester.takeException(), isNull)` — this is what converts a
  `runAsync`-captured smoke error into a real test failure. Without it the
  smoke could throw and the test still report green.

## Commands for the controller (serial)

```bash
dart format --output=none --set-exit-if-changed \
  tool/nginx_smoke.dart integration_test/nginx_runtime_test.dart
flutter analyze --no-pub tool integration_test
flutter test integration_test/nginx_runtime_test.dart -d <device-with-native-nginx>
```

## What to look for in the device log

- Success path: `[NGINX_SMOKE] PASS HTML CSS 404 proxy WebSocket ...` and a
  green test.
- Failure path: `[NGINX_SMOKE] FAIL ...` **and** a red test with reason
  "the native Nginx smoke reported a failure" — this is the behaviour the
  rethrow enables; if the FAIL log appears but the test is green, the
  `takeException` guard has regressed.
- Non-native host: on desktop without a packaged runtime, `markTestSkipped`
  fires (not a failure). On Android/iOS/HarmonyOS there is **no skip path** — a
  missing runtime is a red test.
- Android specifically: a missing `libnginx_exec.so` fails at the
  `expect(..., isNotNull)` guard with a clear reason before the smoke even runs.

## Limitations

- iOS / HarmonyOS cannot be reached by this worker; their embedded-engine
  execution is exercised by the same test but was not run here.
- The smoke's live-reload leg self-skips when recursive `Directory.watch` is
  unsupported (the tool already handles this). The probe was changed to watch an
  independent directory after a real Android inotify assertion; see the change
  summary above.
