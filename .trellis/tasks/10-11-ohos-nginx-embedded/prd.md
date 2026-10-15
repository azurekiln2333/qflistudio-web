# OHOS native Nginx via embedded shared library

## Goal

Make the HarmonyOS build of QFLIWebForge install on a real device **and** run
native Nginx in-app, then let `engine: "auto"` select it. Today the HAP ships
`libnginx_exec.so` as a standalone PIE executable declared through
`module.executableBinaryPaths`; on a HarmonyOS 7.0 phone that declaration makes
`bm install` fail with `9568449 ERR_INSTALL_CHECK_BIN_FILE_FAILED`.

## Background (verified on device)

- Device: HarmonyOS 7.0 phone (API 26), ABI `arm64-v8a`, ten same-signed
  `com.azurekiln.qfli.*` apps already installed.
- HAP with `executableBinaryPaths` → install fails (`check bin file failed`).
- Same HAP with the declaration removed → **installs and launches**.
- Every other language app (qfli_python, qfli_java, qfli_c, qfli_go, qfli_rust,
  qfli_lua, qfli_dart) ships its runtime as a real shared library
  (`libqfli_py.so`) and never uses `executableBinaryPaths`.
- iOS already runs Nginx through the embedded lifecycle ABI
  (`qfli_nginx_version/start/poll/stop/release`) linked into the app.

The embedded path is the only one proven to work on both a real device and on
Apple platforms; it removes the exec-at-install requirement entirely.

## Requirements

- The HarmonyOS HAP installs on the real phone with no `executableBinaryPaths`.
- Native Nginx runs **in-process** through the existing embedded lifecycle ABI,
  delivered as a shared library under `libs/<abi>/`.
- The Dart side uses `EmbeddedNginxHost` on HarmonyOS, so configuration checks,
  health-token, diagnostics, stop and release follow the iOS contract.
- `engine: "auto"` selects the embedded engine when the library is present;
  explicit Nginx never silently substitutes WebForge; missing library falls back
  to WebForge.
- WebForge (Dart middleware) behavior, public loopback port, proxies, SSE and
  diagnostics are unchanged.
- No regression to Nginx/iOS/OHOS edits already present in the working tree.

## Acceptance criteria

- [ ] `build_nginx_embedded.sh ohos` produces `libqfli_nginx.so` for arm64-v8a
      (and x86_64) with no fork/exec/process-management objects, verified by the
      existing symbol scan.
- [ ] HarmonyOS HAP with the shared library and **without** `executableBinaryPaths`
      installs on the real device.
- [ ] On device, `engine: "nginx"` starts the embedded engine, serves a project,
      reports the real version, streams diagnostics, and stops/releases cleanly.
- [ ] `engine: "auto"` picks the embedded engine on HarmonyOS.
- [ ] The Dart session/HTTP contract tests still pass; WebForge is unaffected.
- [ ] Results and limits recorded with raw command output under `research/`.

## Scope and ownership

Deliverable is inside `qfli_web` only. The shared core stays read-only. No
commits or pushes. The terminal/current-file work (task 10-09) must be preserved.
