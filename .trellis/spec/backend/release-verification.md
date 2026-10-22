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
- The installed official `hap-sign-tool.jar` can print `verify-app failed` and
  return exit code zero. Require an explicit `verify-app success` marker,
  exported certificate/profile, and successful `verify-profile`; also validate
  current profile validity and the exact product bundle. A cryptographically
  valid old HAP still fails current-source catalog byte/hash checks.
- The test-only ArkWeb harness and its source/catalog staging use the separate
  [Catalog Verification](./catalog-verification.md) contract. Full Hvigor ArkTS
  and ArkUI compilation is required; a standalone SDK type check with weaker
  nullability options does not prove the application's compilation contract.
- The installed Flutter OHOS builder defaults to arm64. Build release with
  `--target-platform ohos-arm64,ohos-x64` when verifying the x86_64 emulator;
  native CMake ABI filters alone do not add x86_64 `libapp.so`/`libflutter.so`.
  Inspect actual ELF runtime members for both ABIs before installation.
- This local x86_64 emulator accepts an ordinary unsigned `hdc install -r`.
  Use only the explicit, identity-checked catalog-driver emulator mode above.
  Report unsigned emulator acceptance separately from physical-device signing.

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

## 8. Storage cleanup while preserving incremental builds

- Keep `build/app`, `.dart_tool`, `android/.gradle`, OHOS build/dependency
  directories and `build/native/nginx` when the user still needs fast Android
  and OHOS builds. A blanket `flutter clean` discards useful incremental work.
- Historical `build/native/platform-audit` exports and `build/native/validation`
  emulator data are independent of normal WebForge builds. Before removing
  such exports, archive their patches, source deltas, scripts and small test
  evidence; keep the original `.trellis/tasks` records and unrelated dirty work.
- Validate exact absolute targets inside this workspace, require no tracked
  files in them, and inspect links. Remove reparse points themselves without
  following SDK, global Pub Cache or sibling-workspace targets. Windows long
  paths and WSL symlinks require the same boundary check.
- After cleanup, run `flutter build apk --release` and then
  `flutter build hap --release`. Verify fresh output archives and preserve the
  signing distinction in section 4; unsigned OHOS packaging is not a signed
  release or a device pass. Record archive hashes and measured bytes freed.
