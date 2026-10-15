# Design

## Root cause (verified)

`module.executableBinaryPaths` makes `bm install` validate a standalone PIE
executable. On the HarmonyOS 7.0 phone that validation fails
(`ERR_INSTALL_CHECK_BIN_FILE_FAILED`). Removing the declaration installs and
launches; every other `qfli_*` app already runs native code as a **NAPI shared
library** and never uses that declaration.

## Chosen approach

Move HarmonyOS Nginx from "exec a standalone binary" to "run in-process through
the embedded lifecycle ABI", exactly like iOS. The embedded build already:

- omits `ngx_process.c`, `ngx_process_cycle.c`, `ngx_daemon.c`,
  `ngx_setproctitle.c` (no fork/exec/signals);
- exposes `qfli_nginx_version/start/poll/stop/release`;
- links as `libqfli_nginx.a` (Linux also builds `libqfli_nginx.so`).

Reuse that source. On HarmonyOS, wrap it in a thin NAPI module and load it as a
normal `.so`, following the `qfli_java`/`qfli_jdk_layout` template that is
already proven to install and run on this device.

## Components

1. **Build** — `scripts/build_nginx_embedded.sh ohos <ABI> <SDK_ROOT>`:
   - reuse the Linux/iOS code path (same `embedded.patch`, same addon `config`);
   - cross flags from the OHOS SDK: clang, sysroot, `--target=aarch64-linux-ohos`
     / `x86_64-linux-ohos`, `-fPIC`, `-Wl,-z,max-page-size=16384`;
   - produce `libqfli_nginx.so` per ABI (shared, `-Wl,-z,defs`);
   - keep the existing forbidden-symbol scan (`fork`, `exec*`, `posix_spawn`,
     `kill`, `setproctitle`, `exit`, ...) as a hard gate.
   - Output goes to `ohos/entry/libs/<abi>/libqfli_nginx.so` (a plain library
     directory, no `executableBinaryPaths`).

2. **NAPI bridge** — `ohos/entry/src/main/cpp/` (new):
   - `CMakeLists.txt` building `qfli_nginx_napi` as SHARED, linking
     `libace_napi.z.so` and the embedded objects (or `libqfli_nginx.so`);
   - `nginx_napi.cpp`: NAPI exports `version`, `start(prefix, test)`,
     `poll(token)`, `stop(token)`, `release(token)` that delegate to
     `qfli_nginx_*`. No lifecycle state beyond the ABI's own tokens; the Dart
     side already owns stop/release ordering.
   - `types/libqfli_nginx_napi/index.d.ts` + `oh-package.json5`.
   - `ExternalNativeOptions` in `ohos/entry/build-profile.json5` with
     `abiFilters: ["arm64-v8a", "x86_64"]`.

3. **ArkTS bindings** — `ohos/entry/src/main/ets/entryability/NginxBridge.ets`:
   - mirrors `EmbeddedNginxBridge.swift`: a `MethodChannel('qflistudio/nginx')`
     handler for `version/start/poll/stop/release`;
   - `import { ... } from 'libqfli_nginx_napi.so'`;
   - stops the active token on ability destroy.

4. **Dart** — `lib/services/web_runtime.dart`:
   - on `Platform.operatingSystem == 'ohos'`, use `EmbeddedNginxHost` (already
     exists) instead of `ProcessNginxHost`;
   - `nginxExecutable()` no longer resolves a `.so` executable path on OHOS;
     presence is decided by the embedded channel/version call.

5. **Manifest** — `ohos/entry/src/main/module.json5`:
   - remove `executableBinaryPaths`.

## Contracts kept

- `WebRuntimeSession` / `NginxSession` and the public `url` stay unchanged.
- WebForge middleware keeps the public port, proxies, SSE, diagnostics.
- `engine: "auto"` → embedded engine when available; explicit Nginx never
  substitutes; missing library → WebForge.
- The bridge is error-mapped like iOS: `INVALID_ARGUMENT`, `NGINX_START`,
  `NGINX_SESSION`.

## Compatibility / migration

- The standalone `libnginx_exec.so` build path (`build_nginx_ohos.sh`) becomes
  unused on OHOS; keep the script but stop shipping its output.
- Old `ProcessNginxHost` on OHOS is removed from selection; the class stays for
  desktop.

## Risks

- OHOS sysroot may lack an upstream header nginx needs; the `ohos_socket_compat.h`
  shim already exists for the standalone build and is reused.
- 16 KiB page alignment on device; keep `max-page-size=16384`.
- NAPI `start` blocks during configuration; `test=true` still runs config check
  in-process (same as iOS).

## Rollback

Keep the previous manifest, build script and Dart engine selection reachable via
task-local notes; never reset sibling trees or the shared core.
