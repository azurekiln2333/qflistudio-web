# Release verification contracts

## 1. Scope / Trigger

Apply to Android/OHOS release builds, native integration tests and offline
store-readiness work. Product source stays in `qfli_web`; generic core defects
require a declared shared owner and a separate core commit.

## 2. Commands and interfaces

```text
flutter analyze --no-pub lib test integration_test tool
flutter test --no-pub --concurrency=1
flutter test -d <direct-adb-endpoint> integration_test/nginx_runtime_test.dart
flutter test -d <direct-adb-endpoint> integration_test/content_import_test.dart
flutter build apk --release
flutter build hap --release
```

## 3. Contracts

- Serialize platform builds and plugin-registry regeneration. In the installed
  Flutter OHOS toolchain, switching debug/integration to release with `--no-pub`
  leaves `GeneratedPluginRegistrant` referencing the dev-only integration-test
  plugin. Use pub-enabled builds on mode transitions; do not patch generated
  registrants or ship test-plugin dependencies as a workaround.
- The native test must propagate smoke exceptions into a failed test.
  `tester.runAsync` reports exceptions through the binding: assert
  `tester.takeException()` after awaiting it. Logging `FAIL` and returning is
  forbidden. Require the packaged native engine on every shipping mobile target.
- The recursive-watch capability probe owns an independent directory. Never
  register a duplicate watch on the live server root: Android's Dart inotify
  path can assert on that duplicate. Test SSE delivery when watching works;
  record a capability skip only when watching genuinely is unavailable.
- The new OHOS artifact is `ohos/entry/build/default/outputs/default/`.
  A historical `build/ohos/hap/*signed.hap` is not proof of the current build.
  Signing profiles must bind `com.azurekiln.qfli.webforge`. Do not substitute a
  sibling product's profile/bundle identity. Never commit private signing data.
- Resolve HDC local paths to real absolute Windows paths before file transfer.
  Use the direct ADB endpoint when an mDNS serial contains spaces. Never restart
  shared device services or install over a sibling app to fix connectivity.

## 4. Validation and error matrix

| Condition | Required outcome |
| --- | --- |
| Mobile runtime missing | Integration test fails; no desktop-style skip |
| Smoke logs a failure | Exception propagates; test fails |
| OHOS Hvigor succeeds but no signature | Report unsigned build separately; Flutter wrapper may exit 1 |
| `bm install` reports 9568320 / no signature file | Record signing blocker; no device pass claim |
| Android release uses debug key | Validation APK only; store signing remains required |
| Phone installation requires manual confirmation | Report actual waiting/rejection; build success is separate |

## 5. Good / Base / Bad cases

- Good: tests pass, fresh archives contain product assets and correct native
  ABIs, then real device evidence is recorded with its exact limitations.
- Base: unsigned OHOS HAP builds, installation rejects missing signature, and
  that blocker is preserved in task results.
- Bad: copying an older signed HAP into the output location, calling a debug-key
  APK store-ready, or weakening native/content assertions to obtain a green run.

## 6. Required evidence

Record analyze/test totals, browser per-entry results, exact build paths and
hashes, bundle/application identities, native library entries, shared-core
revision and separate installation/runtime outcomes. Keep historical platform
evidence dated; it does not replace current-artifact testing.

## 7. Wrong vs correct

Wrong: `flutter build apk --release --no-pub` immediately after an integration
test, then editing the generated registry to silence the missing plugin error.

Correct: `flutter build apk --release` regenerates the mode-specific registry,
and a clean APK build verifies the resulting dependency selection.
