# Implementation

- [x] Implement and test project-local serving, proxies, diagnostics and SSE.
- [x] Integrate server control, persisted settings, HTTP and codecs into Functions.
- [x] Replace duplicate editor preview startup through narrowly committed core hooks.
- [x] Integrate real Windows Nginx and exercise actual transport/lifecycle tests.
- [x] Build Android arm64-v8a, armeabi-v7a and x86_64 native executables; verify ELF
  dependencies, PIE, 16 KiB LOAD alignment and APK inclusion with licenses.
- [x] Cross-compile HarmonyOS arm64-v8a/x86_64; package a signed debug HAP and
  distinguish successful shell execution from the app's EACCES failure.
- [x] Verify Android x86_64 native runtime in the app on emulator-5556:
  API 37, actual 16 KiB pages, complete native smoke PASS.
- [ ] Verify Android arm64-v8a/armeabi-v7a application execution on devices.
- [ ] Resolve HarmonyOS application execution and verify the complete native
  smoke target. The original packaged file was mode 100644; both paths now use
  executableBinaryPaths, with signed HAP packaging verified. HDC connection was
  lost before the updated package could be checked in the app.
- [ ] Finish task after required device checks; preserve all unrelated work.

## Verification / Commit Gate

Run `flutter analyze --no-pub`, `flutter test --no-pub`, both relevant mobile
builds with the normal product target, `sha256sum --check vendor/nginx/HASHES.sha256`,
and inspect packaged native ABIs/licenses. Require `NGINX_SMOKE PASS` for mobile
execution claims. Use conventional commits with explicit task-owned paths;
stage only Nginx hunks in the already-modified HarmonyOS ability file.

## Rollback

Persist `engine: "webforge"` to select the existing in-process runtime. A native
startup failure cleans its session prefix and private middleware. Explicit Nginx
continues to report failure rather than changing the user's engine selection.
