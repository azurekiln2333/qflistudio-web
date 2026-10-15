# Native Nginx Runtime

> Contract for building, packaging and running the retained upstream Nginx
> engine across platforms. Apply when changing `scripts/`, `vendor/nginx/`,
> `native/nginx/`, the Nginx host classes or platform runners.

---

## Scope

`qfli_web` ships upstream Nginx 1.31.6 in two shapes:

- **Process engine** — a standalone `nginx` binary executed by
  `ProcessNginxHost` (desktop; historically Android/OHOS).
- **Embedded engine** — the same sources compiled in-process behind the
  `qfli_nginx_version/start/poll/stop/release` C ABI, delivered as a shared
  library or static archive and driven by `EmbeddedNginxHost`
  (`qfli_studio_core` channel `qflistudio/nginx`). The embedded build omits
  `ngx_process.c`, `ngx_process_cycle.c`, `ngx_daemon.c` and
  `ngx_setproctitle.c`, so it never forks/execs.

Both run under `NginxSession` (`lib/services/nginx_session.dart`), which owns the
public loopback listener while a private `WebDevServer` middleware keeps static
protection, SPA, proxies, SSE and diagnostics.

## Build Contracts

All builders resolve paths from the repo root and share the retained source at
`vendor/nginx/nginx-1.31.6.tar.gz`, verified against
`vendor/nginx/HASHES.sha256` (SHA-256
`974ed5298a5e398e008704ed5db284e655fc270c596493dbccada452448fc9f1`).

| Target | Script | Output |
|--------|--------|--------|
| Windows (prebuilt) | recorded in `vendor/nginx/SOURCE.json` | `assets/runtime/nginx/windows/nginx.exe` |
| Linux / macOS | `scripts/build_nginx_desktop.sh <platform>` | `assets/runtime/nginx/<platform>/nginx` |
| Android | `scripts/build_nginx_android.sh <abi> <NDK>` | `android/.../jniLibs/<abi>/libnginx_exec.so` |
| OHOS (embedded, shipped) | `scripts/build_nginx_embedded.sh ohos <out> <sdk-native-root> <abi>` → linked by `ohos/entry/src/main/cpp/CMakeLists.txt` | `libs/<abi>/libqfli_nginx_napi.so` |
| OHOS (process, obsolete) | `scripts/build_nginx_ohos.sh <abi> <SDK>` | `libnginx_exec.so` — no longer shipped |
| Linux / iOS / OHOS (embedded) | `scripts/build_nginx_embedded.sh <platform> <output> ...` | `libqfli_nginx.a` + `libqfli_nginx.so` |
| iOS bundle | `scripts/bundle_nginx_ios.sh` | Runner static archive |
| macOS bundle | `scripts/bundle_nginx_macos.sh` | `Contents/Helpers/nginx` |

Rules:

- Android and OHOS process builds require `-Wl,-z,max-page-size=16384` and the
  `ohos_socket_compat.h` / Android socket compat patches.
- The embedded build's forbidden-symbol gate (`fork`, `exec*`, `posix_spawn`,
  `kill`, `setproctitle`, `exit`, ...) is a hard fail. Do not weaken it.
- The HarmonyOS native SDK ships a Windows `clang.exe`. Under WSL the build tree
  must sit on a Windows-visible mount, so set `QFLI_NGINX_BUILD_ROOT=/mnt/<drive>/...`;
  a WSL-only path such as `/tmp` makes configure fail with a bare
  "C compiler ... is not found". The OHOS branch of the script now rejects it early.
- Retained upstream source, patches and packaged binaries are covered by
  `HASHES.sha256`; update `SOURCE.json` and the hash file together when inputs
  change.

## Platform Rules

- **HarmonyOS ships the embedded NAPI engine, never a process executable.**
  `module.executableBinaryPaths` makes `bm install` fail
  (`9568449 ERR_INSTALL_CHECK_BIN_FILE_FAILED`) on a HarmonyOS 7.0 phone even
  though the ELF is valid. The shipped HAP instead carries
  `libs/<abi>/libqfli_nginx_napi.so`, built from the per-ABI `libqfli_nginx.a`
  embedded archive via `externalNativeOptions`; the NAPI exports
  `version/start/poll/stop/release` over `qfli_nginx_*` and backs the
  `qflistudio/nginx` channel. Do not reintroduce `executableBinaryPaths`.
- **Do not package host executables.** A cross-built runner must not ship a
  host-architecture binary. Missing native delivery on a shipping mobile target
  fails its integration gate; only unsupported desktop development hosts may skip.
- **Android** packages PIE executables under `jniLibs/<abi>/` with legacy
  library extraction; `nginxPath` returns `applicationInfo.nativeLibraryDir`.
- **iOS** links a static archive (no `fork`); every object must match the
  device/simulator platform before linking. Apple build/sign/runtime gates stay
  separate from Linux compilation.
- Keep engine evidence distinct per platform; a Linux embedded pass does not
  prove an Apple or Android pass.

## Verification Commands

```bash
sha256sum --check vendor/nginx/HASHES.sha256
bash scripts/build_nginx_embedded.sh linux /abs/output   # builds .so + lifecycle test
bash scripts/test_nginx_embedded.sh /abs/output          # real-library lifecycle cases
bash native/nginx/embedded/run_access_log_regression.sh /abs/output/libqfli_nginx.so   # -t/serve/stop/serve access log
# device gate (propagates smoke exceptions into real test failures):
flutter test -d <device> integration_test/nginx_runtime_test.dart
```

`tool/nginx_smoke.dart` must be run on real hardware/emulator and print its PASS
marker; shell `nginx -V` and an APK/HAP build alone are not execution evidence.

## Status Notes (do not overstate)

- Linux embedded: real-library lifecycle cases verified.
- Windows: native transport/lifecycle tests pass; the full GUI build lacks VS C++
  tools.
- Android x86_64: application smoke PASS on an API 37 / 16 KiB emulator.
- Apple (iOS/macOS): source/build integration exists; no build/sign/device pass
  is claimed without Xcode and Apple hardware.
- HarmonyOS: the embedded NAPI engine is built for arm64-v8a and x86_64, both
  archives pass the forbidden-symbol gate, and the signed dual-ABI HAP installs
  on a HarmonyOS 7.0 phone with no `executableBinaryPaths`. The on-device
  `tool/nginx_smoke.dart` run passes HTML/CSS/404, native HTTP and WebSocket
  proxying, diagnostics, the native access log, port-conflict, stop, restart and
  `engine: auto`; only live reload is skipped because the OHOS sandbox delivers
  no recursive filesystem watch events. A general embedded defect it exposed is
  fixed: a configuration check (`-t`) before the server left `ngx_time()` at 0,
  so the access-log handler treated the line as a disk-full duplicate and skipped
  it. `ngx_time_init()` repoints `ngx_cached_time` at slot 0 without resetting
  the static slot cursor, and `ngx_time_update()`'s same-second early return did
  not repoint the pointer; the fix repoints `ngx_cached_time` in that early
  return (`vendor/nginx/patches/embedded-time-cache.patch`). Regression:
  `native/nginx/embedded/access_log_probe.py` and
  `native/nginx/embedded/run_access_log_regression.sh` cover server-only,
  `-t`-then-server, server-then-server and `-t`/serve/stop/serve.

See [Web Runtime](./web-runtime.md) for the full engine/session contract and
`vendor/nginx/VALIDATION.md` for the evidence log.

The HarmonyOS device evidence above is historical (2026-10-12). The fresh
2026-10-15 release HAP is unsigned because no WebForge-bound signing profile is
available; installation rejects it with 9568320 (no signature file). Do not use
the old signed artifact as evidence for the new release. Follow
[Release Verification](./release-verification.md) for current-artifact gates.
