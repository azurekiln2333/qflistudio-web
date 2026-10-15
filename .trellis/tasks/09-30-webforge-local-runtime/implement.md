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
- [x] Add Linux source build, bundle installation and runtime discovery.
- [x] Add macOS architecture builds, signed sandbox-inheriting helper and discovery.
- [x] Verify desktop completion on the available Windows environment and record
  skipped native platforms separately from successful source-level checks.
  Linux WSL access could not pass permission review (service HTTP 503); no Apple
  build environment exists. Neither platform has a native runtime pass.
- [x] Verify Android arm64-v8a application execution on a physical device
  (2026-10-15, OPD2413): full native HTTP/proxy/WebSocket/SSE/log/lifecycle smoke
  passes. Evidence: `../10-15-webforge-store-readiness/android-native-device-final.log`.
- [ ] Verify armeabi-v7a application execution on a 32-bit device; no such device
  is available in this workspace. Packaged ABI/ELF checks are build evidence only.
- [x] Resolve HarmonyOS application execution. The standalone
  `libnginx_exec.so` + `executableBinaryPaths` form was rejected at install by
  `bm install` (`ERR_INSTALL_CHECK_BIN_FILE_FAILED`), so OHOS moved to the
  in-process embedded engine delivered as a NAPI shared library. The signed HAP
  installs on the real phone and the in-app smoke printed `[NGINX_SMOKE] PASS`
  (see task `10-11-ohos-nginx-embedded`). The access-log regression found during
  that smoke was fixed in
  `vendor/nginx/patches/embedded-time-cache.patch`.
- [ ] Finish task after the remaining Android 32-bit device check; preserve all
  unrelated work.

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
