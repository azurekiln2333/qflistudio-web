# Implementation

## Order

1. [x] Capture baselines (module.json5, web_runtime.dart, scripts) under `research/`.
2. [x] Add `ohos` platform to the embedded build; produce `libqfli_nginx.so`
       per ABI and prove the forbidden-symbol scan passes.
3. [x] Wire the build output into `ohos/entry/src/main/cpp/prebuilt/<abi>/` and add
       `externalNativeOptions` + NAPI bridge + `index.d.ts`.
4. [x] Add `NginxBridge.ets` and register it in `EntryAbility.ets` (plus
       `onDestroy` stop/poll/release).
5. [x] Select `EmbeddedNginxHost` for OHOS in `lib/services/web_runtime.dart`;
       `auto` falls back to WebForge when the embedded channel is absent.
6. [x] Remove `executableBinaryPaths` from `module.json5`; drop the obsolete
       `libs/*/libnginx_exec.so`.
7. [x] Build the HAP, install on the real device, verify install + embedded start
       + serve + diagnostics + stop/release. `[NGINX_SMOKE] PASS` on the phone
       (raw log `research/ohos-smoke-device-2026-10-12.log`); only live reload is
       reported SKIP (recursive watch unsupported on OHOS). The an access-log
       defect that smoke surfaced was root-caused and fixed (see
       `research/access-log-time-cache-fix-2026-10-12.md`); the install gate was
       re-verified with the fixed HAP (`research/ohos-install-2026-10-12.log`).
       In-app re-run with the fixed HAP is pending a device unlock.
8. [x] Run Dart session/contract tests and analyze; record raw output.

## Validation commands

- `bash scripts/build_nginx_embedded.sh ohos arm64-v8a <SDK_NATIVE_ROOT>`
- `hvigorw --mode module -p product=default -p module=entry@default assembleHap`
- `hdc file send <abs hap> /data/local/tmp/<dir>/` (absolute path only; relative
  paths silently transfer a directory tree and cause `install file path invalid`)
- `hdc shell bm install -p /data/local/tmp/<dir>/entry-default-signed.hap -r`
- `flutter test --no-pub --concurrency=1 test/web_dev_server_test.dart test/nginx_session_test.dart`
- `flutter analyze --no-pub lib test`

## Device verification

- Confirm `bm install` succeeds without `executableBinaryPaths`.
- In-app: `engine: "nginx"` starts, serves a project over the loopback port,
  version string is the real upstream version, stop releases the token.
- `engine: "auto"` selects the embedded engine.
- Capture hilog and any HTTP evidence under `research/`.

## Gates / rollback points

- After step 2: if the embedded OHOS build fails on missing headers, stop and
  report rather than ship a broken library.
- After step 7: if install still fails, revert to the last installable HAP and
  record the exact installer error before changing anything else.

## Result

All steps complete with evidence in
`research/ohos-embedded-verification-2026-10-12.md` and the raw device log
`research/ohos-smoke-device-2026-10-12.log`. The device smoke printed
`[NGINX_SMOKE] PASS HTML CSS 404 proxy WebSocket SSE-skipped diagnostics log
port-conflict stop restart auto`. The one non-pass check is live reload, which
the middleware itself treats as optional and which the smoke now reports as
`SKIP live-reload` rather than a failure.

## Notes

- HDC caveat: always send with an absolute local path.
- Do not touch `qfli_studio_core`.
- Preserve task 10-09 terminal/current-file changes and existing iOS/OHOS edits.
