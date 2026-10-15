# Technical design

## Failure propagation in `tool/nginx_smoke.dart`

The only edit is inside the existing `catch`:

```dart
} catch (error, stack) {
  debugPrint('[NGINX_SMOKE] FAIL $error\n$stack');
  rethrow;
} finally {
  // unchanged cleanup
}
```

- `main`'s return type stays `Future<void>`; a rethrown error propagates out of
  `main`, so `flutter run -t tool/nginx_smoke.dart` on a device surfaces it in
  the console. For the automated gate, `runAsync(() => smoke.main())` receives
  the same error as a rejected future.
- `finally` still stops the session, closes the upstream, closes the client and
  deletes the temp project before the error escapes.
- The PASS path is unchanged; only failing runs change exit behaviour.

## Driving the smoke from `integration_test`

`integration_test/nginx_runtime_test.dart`:

```dart
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('native Nginx runtime smoke', (tester) async {
    if (!await _nativeEngineAvailable()) {
      markTestSkipped('native Nginx runtime not available on this host');
      return;
    }
    await tester.runAsync(() => smoke.main());
    expect(
      tester.takeException(),
      isNull,
      reason: 'the native Nginx smoke reported a failure',
    );
  });
}
```

Why each part:

- **`runAsync`** — the smoke does real socket/file IO and awaits
  `WebRuntime.start`; the fake async zone of `testWidgets` would stall it.
- **`takeException()`** — `runAsync` captures an error thrown inside its
  callback and reports it through the binding rather than failing the enclosing
  test directly. Without this assertion a thrown smoke error could leave the
  test green. This is the "avoid runAsync swallowing" guard the task requires.
- **Availability gate** — Android, iOS and HarmonyOS ship the native engine
  with the app, so they are **never skipped**: a missing runtime is a broken
  package and must fail. Android additionally asserts
  `WebRuntime.nginxExecutable()` is non-null (clear failure for a missing
  `libnginx_exec.so`). Only a desktop dev host with no packaged runtime may
  `markTestSkipped`. The probe must not mask a real failure on a shipping
  platform.

### Availability gate

`_desktopHostWithoutRuntime(executable)` returns true **only** for
Windows/Linux/macOS with a null executable path. Every other platform proceeds
and fails for real when the runtime is missing.

## Compatibility / boundaries

- `tool/nginx_smoke.dart` keeps its `main()` and top-level helpers; the
  standalone `flutter run -t tool/nginx_smoke.dart` invocation documented in
  `vendor/nginx/VALIDATION.md` keeps working.
- The new test is additive; the only shared file touched is the smoke tool.
- Rollback = revert the one-line `rethrow` and delete the new test.

## Validation (controller-run)

```bash
dart format --output=none --set-exit-if-changed tool/nginx_smoke.dart integration_test/nginx_runtime_test.dart
flutter analyze --no-pub tool integration_test
flutter test integration_test/nginx_runtime_test.dart -d <device>
```
