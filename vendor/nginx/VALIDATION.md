# Native Runtime Verification

Recorded on 2026-09-30; Android evidence updated on 2026-10-01, Linux
native execution updated on 2026-10-02, and HarmonyOS embedded execution
updated on 2026-10-12.
Packaging and application execution are separate checks.

| Platform | Native binary | Packaging | Application execution |
| --- | --- | --- | --- |
| Windows x64 | Official Nginx 1.31.6, SHA recorded | CMake install rule; full Flutter Windows build lacks Visual Studio C++ tools | Real-binary integration tests passed |
| Android x86_64 | NDK 27 / API 24 PIE, LOAD segments aligned to 0x4000 | Debug APK built and installed with native library extraction | Passed in the app on emulator-5556: API 37, actual page size 16384 |
| Android arm64-v8a, armeabi-v7a | NDK 27 / API 24 PIE, all LOAD segments aligned to 0x4000 | Debug APK built; all three native files and both licenses present | Pending physical device checks |
| HarmonyOS arm64-v8a / x86_64 | Embedded engine (`libqfli_nginx.a`) linked into a NAPI module | Signed dual-ABI HAP with `libs/<abi>/libqfli_nginx_napi.so`; no `executableBinaryPaths` | Passed on a HarmonyOS 7.0 phone (API 26): `[NGINX_SMOKE] PASS ... log port-conflict stop restart auto`; only live reload skipped (no recursive watch in the sandbox) |
| Linux x86_64 | Retained upstream Nginx 1.31.6 source built with GCC 13 | CMake build/install integration; full Flutter packaging unverified | Standalone native static/proxy/404/stop checks passed; Flutter application unverified |
| macOS arm64/x86_64 | Retained upstream source build integrated with universal compiler flags | Xcode bundles and signs a sandbox-inheriting helper | Not run: no Apple build host or device |
| iOS | Embedded upstream engine via `libqfli_nginx.a` | Runner static archive + Swift channel source integrated | Not run: no Apple build host or device |

## HarmonyOS Embedded Engine (2026-10-12)

The HarmonyOS build no longer ships a standalone PIE executable.
`module.executableBinaryPaths` made `bm install` fail with
`9568449 ERR_INSTALL_CHECK_BIN_FILE_FAILED`; the shipped HAP instead links the
embedded archive into `libqfli_nginx_napi.so` through
`ohos/entry/src/main/cpp/CMakeLists.txt`. Both ABI archives pass the
forbidden-process-symbol gate. The signed HAP installs and the in-app smoke
passes HTML/CSS/404, native HTTP and WebSocket proxying, diagnostics, the native
access log, port-conflict rejection, stop, restart and `engine: auto`.

One general embedded defect surfaced and is fixed: running `nginx -t` before
the server left the process-global cached time at 0 (`ngx_time_init()` pointed
`ngx_cached_time` at slot 0 without resetting the static slot cursor, and
`ngx_time_update()`'s same-second early return did not repoint it), which made
the access-log handler drop every line. The fix is
`vendor/nginx/patches/embedded-time-cache.patch` (repoint `ngx_cached_time` in
the early return); a `qfli_nginx_reset_time()` reset attempt did not fix it and
was removed from `embedded.patch`. Guards:
`test_embedded.py::test_access_log_after_configuration_check` and
`native/nginx/embedded/run_access_log_regression.sh` (`server-only`,
`test-then-server`, `server-then-server`, `test-then-restart`).

## Linux Native Check (2026-10-02)

WSL access became available. `scripts/build_nginx_desktop.sh linux` built the
retained source in the qfli-java-build Linux environment. The actual executable
reported `nginx/1.31.6`, passed `nginx -t`, served a native static fixture,
forwarded an HTTP proxy request with the upstream response header, returned
404 for a missing file, and stopped with no listener accepting connections.
The reproducible harness and configuration are in the active native platform
audit task's research directory. Its missing-file error log is expected.

This verifies the standalone native Linux binary. It does not establish a
Linux Flutter application build, middleware/SSE/WebSocket integration pass,
or any Apple execution result. Those remain separate gates.

## Earlier Desktop Completion (2026-10-01)

Linux/macOS now have complete source-build, packaging and executable discovery
paths. At that point these paths had not been native-built or executed. Linux
environment inspection first returned WSL access denied in the restricted
session. Both requests to access WSL with the required permission were not
executed because automatic approval review returned HTTP 503 (review service
unavailable). This is an environment limitation, not a compiler result.
Apple targets have no local Xcode or Apple device and were not run.

The Windows host passed static analysis and all 33 product tests,
including automatic native selection and the real upstream Nginx integration
suite. Desktop shell inputs passed
Bash syntax checks, and the retained source archive's SHA-256 matched its
manifest. No Linux/macOS runtime pass is inferred from these host checks.

## Desktop Integration Assertions

`test/nginx_session_test.dart` exercises the official Windows executable:

- Actual `Server: nginx/1.31.6` and native engine headers.
- HTML/CSS serving, private-file rejection, console bridge and native access log.
- HTTP method/body/status/headers, unchanged redirects and binary WebSocket echo.
- Longer HTTPS routes retain priority over overlapping native HTTP routes.
- Real SSE reload after file change, occupied-port rejection and listener shutdown.

`flutter analyze --no-pub` and the full Dart suite are required alongside these
tests. They do not prove Android/HarmonyOS application execution.

## Device Check

```bash
flutter run --debug --no-pub -d DEVICE -t tool/nginx_smoke.dart --no-resident
```

The dedicated target selects Nginx explicitly and writes `[NGINX_SMOKE] PASS` or
`FAIL` to device logs. It checks HTML/CSS, proxy bodies, WebSocket, SSE, browser
diagnostics, access logs, shutdown and a second start/stop. Build or installation
success is not a test pass. Use the product's normal `lib/main.dart` target when
building deliverable APK/HAP files.

### Android

The API 37 x86_64 emulator reports `getconf PAGESIZE` as `16384`. The application
package reports `pageSizeCompat=0`. The packaged x86_64 Flutter library's LOAD
alignment is `0x10000`; all three packaged Nginx ABIs use `0x4000`.
The application
resolved Nginx inside `applicationInfo.nativeLibraryDir`, executed it through
the product runtime, and emitted:

```text
[NGINX_SMOKE] PASS HTML CSS 404 proxy WebSocket SSE diagnostics log port-conflict stop restart auto
```

The automatic engine selection also uses Nginx. An occupied public port is
rejected, a missing asset returns 404, and both native listeners close on stop.
This proves application execution on this emulator; arm64/32-bit and older API
device execution remain separate checks. On a memory-constrained Windows build,
the Gradle wrapper/daemon initially failed with errno=1455; temporary lower JVM
memory options allowed the build to pass without changing project defaults.

### HarmonyOS

On the phone simulator, the application reported:

```text
executable=/data/storage/el1/bundle/libs/x86_64/libnginx_exec.so
mode=100644
probe=/system/bin/echo code=0 out=probe
ProcessException: Permission denied
Command: /data/storage/el1/bundle/libs/x86_64/libnginx_exec.so -v
```

The successful system-command probe shows that app process execution is
available; the packaged Nginx file lacked executable bits. The local SDK module
schema and Hvigor pre-build validator support `module.executableBinaryPaths`,
using paths relative to the module root and restricted to its `libs/<abi>/`
directories. Both Nginx paths are now declared, and the signed HAP's
`module.json` retains them. The simulator lost its HDC connection before this
change could be tested in the app. Do not claim this packaging change fixes
device execution until the full smoke target passes.

## Embedded Engine Follow-up (2026-10-02)

The retained upstream 1.31.6 engine now has an embedded C ABI, an iOS static
archive recipe, Runner link integration and a Swift lifecycle channel. The
shared session uses a process or embedded host while preserving the existing
health-token, middleware, proxy and diagnostics behavior.

Available environment results for this source change:

- Linux embedded engine: all nine real-library service/lifecycle cases passed.
  They cover upstream version/header, static/404, configuration checks, unsafe
  core settings, bind conflicts/recovery, HTTP body/path/status fidelity, busy
  and stale tokens, early/repeated stop, active proxy stop and partial requests.
- The same nine cases passed AddressSanitizer/UndefinedBehaviorSanitizer.
  Python leak detection is disabled for its allocator; the separate native C
  harness retains LeakSanitizer and passed 100 config/start/HTTP/active-stop
  cycles with no sanitizer error. Native sigaction handlers/masks/flags, stdio
  identities and descriptor counts remain unchanged. Python also verifies the
  environment pointer/sentinel and current directory.
- Windows: all 38 Flutter tests pass, including the actual upstream process
  integration and five new native-channel contract cases. Product source
  analysis is clean. The unscoped analyzer also scanned unrelated retained
  build snapshots/SDK copies and failed; use `flutter analyze --no-pub lib test
  tool/nginx_smoke.dart` for the product source gate in this audit checkout.
- Android emulator-5560 (x86_64/API 37/16 KiB): the current application smoke
  again emitted its complete PASS marker. The ordinary lib/main.dart APK was
  rebuilt/restored as build 4002, retaining installed app data. Build 1 was
  rejected as older than installed build 4001; no uninstall/downgrade was used.
- iOS/macOS: Xcode, Apple SDKs and devices are unavailable. No Apple compile,
  archive validation, link, signing or device pass is claimed. Android ARM and
  32-bit execution were not run without matching devices.

Reproduce the available native gate on Linux:

```bash
QFLI_NGINX_SANITIZE=1 bash scripts/build_nginx_embedded.sh linux /absolute/output
QFLI_NGINX_SANITIZE=1 bash scripts/test_nginx_embedded.sh /absolute/output
```

Exact artifacts, failures and limits are recorded in the active task's
`research/nginx-embedded-verification-2026-10-02.md`.

### Portability Follow-up (2026-10-03)

The embedded addon now removes ngx_process.c, ngx_process_cycle.c, ngx_daemon.c
and ngx_setproctitle.c from CORE_SRCS. Their fork calls were still compiled even
with daemon/master disabled and would fail against the iOS SDK. Event-engine
globals and rejecting process-operation stubs are supplied by the addon. The
build rejects these objects and forbidden process imports in the static archive.
Archives are recreated before replacing existing outputs. A reuse regression
seeded the output with all four old process objects; the rebuild removed every
one and passed the import gate. Archive member lists are retained as evidence.
Linux normal and ASan/UBSan builds both pass nine actual-library cases and the
100-cycle C lifecycle harness; the latter also runs LeakSanitizer. These results
supersede the older embedded archive. Apple compilation remains unavailable.

The reconnected Android emulator-5560 (API 37/x86_64/16 KiB) ran build 4003 and
emitted the full smoke PASS marker. The ordinary lib/main.dart build 4004 was
then installed and launched. Emulator startup used a read-only overlay; no app
uninstall or data clearing was performed. Device log timestamps remain October 2.
