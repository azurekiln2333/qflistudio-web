# OHOS embedded Nginx verification, 2026-10-12

## Summary

HarmonyOS native Nginx moved from a standalone PIE executable
(`libnginx_exec.so` + `module.executableBinaryPaths`, rejected by `bm install`
with `ERR_INSTALL_CHECK_BIN_FILE_FAILED`) to an in-process embedded engine
delivered as a NAPI shared library. The HAP installs on the real device without
`executableBinaryPaths` and packages `libqfli_nginx_napi.so` for both ABIs.

## Source changes (this repository only)

| Path | Role |
| --- | --- |
| `ohos/entry/src/main/cpp/CMakeLists.txt` | Builds `qfli_nginx_napi` (SHARED) per ABI from the prebuilt archive |
| `ohos/entry/src/main/cpp/nginx_napi.cpp` | NAPI exports `version/start/poll/stop/release` over `qfli_nginx_*` |
| `ohos/entry/src/main/cpp/include/qfli_nginx.h` | Byte-identical copy of `native/nginx/embedded/qfli_nginx.h` |
| `ohos/entry/src/main/cpp/prebuilt/<abi>/libqfli_nginx.a` | Embedded engine archive per ABI |
| `ohos/entry/src/main/cpp/types/libqfli_nginx_napi/*` | ArkTS type declaration + `oh-package.json5` |
| `ohos/entry/src/main/ets/entryability/NginxBridge.ets` | `qflistudio/nginx` MethodChannel over the NAPI module |
| `ohos/entry/src/main/ets/entryability/EntryAbility.ets` | Registers the channel; `onDestroy` stops+releases; `nginxPath` removed |
| `ohos/entry/build-profile.json5` | `externalNativeOptions` with `abiFilters` arm64-v8a + x86_64 |
| `ohos/entry/src/main/module.json5` | `executableBinaryPaths` removed |
| `ohos/entry/oh-package.json5` | Declares `libqfli_nginx_napi.so` |
| `lib/services/web_runtime.dart` | OHOS routes to `EmbeddedNginxHost`; `auto` falls back to WebForge |
| `scripts/build_nginx_embedded.sh` | OHOS branch requires a Windows-visible build root |
| deleted `ohos/entry/libs/*/libnginx_exec.so` | Obsolete standalone executables |

## Native build evidence

Command (per ABI, WSL):

```bash
QFLI_NGINX_BUILD_ROOT=/mnt/d/MyNewProjects/qfli_web/build/native/nginx/buildroot \
  bash scripts/build_nginx_embedded.sh ohos <out> \
  /mnt/d/ProgramFiles/Huawei/OpenHarmony/Sdk/23/native <arm64-v8a|x86_64>
```

Result: `Built upstream Nginx 1.31.6 embedded library` for both `embedded-ohos-arm64`
and `embedded-ohos-x86_64`. Each output contains `libqfli_nginx.a`,
`libqfli_nginx.so`, `undefined-symbols.txt`, `HASHES.sha256`.

Forbidden-process-symbol gate on the packaged archives
(`nm -u ohos/entry/src/main/cpp/prebuilt/<abi>/libqfli_nginx.a`): no `fork`,
`vfork`, `exec*`, `posix_spawn`, `kill`, `raise`, `system`, `popen`, `exit`,
`abort` or `setproctitle` import.

Note: the final `.so` links `abort` from `libc.so` (nginx `ngx_abort`); it is a
libc function, not a process-management primitive, and is present on OHOS.

## NAPI shared object evidence

`libqfli_nginx_napi.so` (arm64-v8a) built by the OHOS toolchain:
ELF64 AArch64 `DYN`; NEEDED `libace_napi.z.so`, `libc++_shared.so`, `libc.so`;
exports `RegisterQfliNginxModule` and `qfli_nginx_version/start/poll/stop/release`;
no forbidden dynamic imports.

The DevEco `hmos.toolchain.cmake` injects `OHOS_ARCH` per ABI
(`arm64-v8a` / `x86_64`), confirmed in `ohos/entry/.cxx/**/CMakeCache.txt`, so the
`CMakeLists.txt` ABI gate resolves without extra `arguments`.

## HAP packaging evidence

`flutter build hap --debug` (hvigor `assembleHap`) →
`ohos/entry/build/default/outputs/default/entry-default-signed.hap`
(162,046,138 bytes at the 2026-10-12 05:17 rebuild, after the prebuilt archives
were refreshed). ZIP contents include
`libs/arm64-v8a/libqfli_nginx_napi.so` (660,464) and
`libs/x86_64/libqfli_nginx_napi.so` (701,880); no `libnginx_exec.so` entry and
no `executableBinaryPaths` field in the packaged `module.json`.

Device install on the HarmonyOS 7.0 phone (MRT-AL10, API 26,
`192.168.68.207:46551`):

```text
hdc file send build/ohos/hap/entry-default-signed.hap /data/local/tmp/qfli11/entry-default-signed.hap
hdc shell bm install -p /data/local/tmp/qfli11/entry-default-signed.hap -r
install bundle successfully.
```

This is the primary install-gate result: the HAP installs with no
`executableBinaryPaths` requirement.

## On-device verification (real phone)

Device: HarmonyOS 7.0 `MRT-AL10` (nova 14 Ultra), API 26, arm64-v8a, hdc TCP
`192.168.68.207:46551`.

Build + install + end-to-end smoke:

```text
flutter build hap --debug                 -> Built build/ohos/hap/entry-default-signed.hap
hdc shell bm install -p /data/local/tmp/qfli11/entry-default-signed.hap -r
                                          -> install bundle successfully.
flutter run -d 192.168.68.207:46551 -t tool/nginx_smoke.dart --debug
  [NGINX_SMOKE] SKIP live-reload (recursive watch unsupported)
  [NGINX_SMOKE] PASS HTML CSS 404 proxy WebSocket SSE-skipped diagnostics log port-conflict stop restart auto
```

Raw log: `research/ohos-smoke-device-2026-10-12.log`.

Note: a second, minimal patch `vendor/nginx/patches/embedded-time-cache.patch`
(added concurrently) also fixes the same early-return path by republishing
`ngx_cached_time`. Both patches are applied by `build_nginx_embedded.sh` and the
combined Linux suite (`Ran 10 tests ... OK`) and the device smoke both pass with
them together, so they are redundant but compatible.

This PASS covers the full embedded lifecycle in-app: install without
`executableBinaryPaths`, embedded engine start, real upstream version, static
HTML/CSS, 404, native HTTP proxy, WebSocket proxy, editor diagnostics, the
native access log, occupied-port rejection, stop, restart, and `engine: "auto"`
selecting the embedded engine.

`tool/nginx_smoke.dart` now probes recursive `Directory.watch` first and reports
`SKIP live-reload` when the sandbox does not deliver filesystem events. That is
the middleware's own documented optional capability, so it skips one check
instead of masking the stop/auto results; it is not treated as a pass.

## Dart verification (host)

```text
flutter analyze --no-pub lib test          -> No issues found
flutter test --no-pub --concurrency=1 \
  test/nginx_host_test.dart test/nginx_session_test.dart \
  test/web_app_test.dart test/web_dev_server_test.dart
                                           -> All tests passed
```

New channel-contract cases: an absent embedded channel surfaces
`MissingPluginException` (the signal `WebRuntime.auto` uses to fall back), and a
malformed version throws `StateError`.

## Root cause found and fixed: access log empty after a `-t` run

The device smoke failed at the native access-log check while every earlier
assertion (engine name, HTML/CSS/404, SSE diagnostics, HTTP proxy 201) passed.
This reproduced on Linux with the real embedded library, so it was **not**
OHOS-specific.

Reproduction (`native/nginx/embedded/access_log_probe.py`, real `.so`):

| Sequence | access.log before fix | after fix |
| --- | --- | --- |
| server only | 63 B | 63 B |
| `-t` then server | **0 B** | 63 B |
| server, stop, server | 63 B (truncated) | 126 B |
| `-t`, server, stop, server | 0 B | 63 B |

Mechanism: the embedded engine calls Nginx `main()` more than once in one
process (the editor runs `nginx -t` during validate, then the server). The
cached-time slot index and lock are process-global statics that survive the
`-t` run, so after it `ngx_time()` returned 0. That value equals the freshly
zeroed access-log `disk_full_time`, and `ngx_http_log_handler` treats an equal
`ngx_time()`/`disk_full_time` as a disk-full duplicate and skips the line.
Instrumentation confirmed `QFLIDBG diskfull now=0 stored=0` in the broken run
versus `now=1791751438 stored=0` in the working run.

Fix (`vendor/nginx/patches/embedded-time-cache.patch`): in the early-return
branch of `ngx_time_update()` (`cached_time[slot].sec == sec`), set
`ngx_cached_time = tp;` so the cached-time pointer always matches the live slot.
`ngx_time_init()` repoints `ngx_cached_time` at slot 0 without resetting the
static slot cursor, so a second cycle in the same second left the pointer on the
zeroed slot and `ngx_time()` read 0.

An earlier attempt (a `qfli_nginx_reset_time()` that zeroed the slot, lock and
cache and re-ran `ngx_time_init()` at `qfli_nginx_main` entry) was tested and
did **not** fix it: it re-ran `ngx_time_init()` twice in the same second and hit
the very early-return path that left the pointer stale, so every scenario stayed
at 0 bytes. That patch (and its `qfli_nginx_reset_time` prototype in
`qfli_nginx_internal.h`, and the `ngx_times.c` section of `embedded.patch`) were
removed. The `embedded.patch` file was regenerated cleanly (a stale/truncated
`ngx_times.c` hunk had left it malformed); it now applies without warning.

Evidence: the 4-scenario probe prints `ACCESS_LOG_PROBE PASS`; the embedded
suite's `test_access_log_after_configuration_check` passes and the suite now
reports `Ran 10 tests ... OK` plus `PASS: 100 config/start/HTTP/active-stop
cycles` after a clean Linux rebuild.

## Remaining / not verified

- Live reload (SSE `data: reload`) is skipped on the OHOS sandbox because
  recursive `Directory.watch` delivers no events there. The middleware already
  treats watching as optional; the smoke now reports `SKIP live-reload` instead
  of failing. This is independent of the embedded engine change.
- Apple (macOS/iOS) build, sign and device runs are unavailable on this host.
- Android ARM runtime is unavailable (no physical ARM device).
- Linux Flutter GUI packaging is not exercised; only the native engine build is.

## Review fixes applied

- D1: `ReadString` now copies through a `std::vector<char>(length + 1)` scratch
  buffer instead of writing `length + 1` bytes into a `length`-byte `std::string`.
- D2: `WebRuntime.start` probes the embedded channel for `auto`; when it is absent
  the session degrades to WebForge. Explicit `nginx` never substitutes.
- D3: `stopActiveNginx` stops, then polls (bounded 100×50 ms) and releases the
  token, mirroring `EmbeddedNginxBridge.swift` deinit, so a later `start()` in the
  same process cannot hit `-EBUSY`.
- D4: verified `OHOS_ARCH` is injected by the DevEco toolchain per ABI.
