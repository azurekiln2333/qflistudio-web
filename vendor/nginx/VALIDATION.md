# Native Runtime Verification

Recorded on 2026-09-30; Android evidence updated on 2026-10-01 and Linux
native execution updated on 2026-10-02.
Packaging and application execution are separate checks.

| Platform | Native binary | Packaging | Application execution |
| --- | --- | --- | --- |
| Windows x64 | Official Nginx 1.31.6, SHA recorded | CMake install rule; full Flutter Windows build lacks Visual Studio C++ tools | Real-binary integration tests passed |
| Android x86_64 | NDK 27 / API 24 PIE, LOAD segments aligned to 0x4000 | Debug APK built and installed with native library extraction | Passed in the app on emulator-5556: API 37, actual page size 16384 |
| Android arm64-v8a, armeabi-v7a | NDK 27 / API 24 PIE, all LOAD segments aligned to 0x4000 | Debug APK built; all three native files and both licenses present | Pending physical device checks |
| HarmonyOS arm64-v8a | SDK Clang 15.0.4 PIE | Native file built for HAP inclusion | Pending physical device |
| HarmonyOS x86_64 | SDK Clang 15.0.4 PIE; simulator shell `-V` passed | Signed dual-ABI debug HAP built, including executableBinaryPaths declarations | Original app startup failed with EACCES and file mode 100644; execution after the manifest change remains unverified |
| Linux x86_64 | Retained upstream Nginx 1.31.6 source built with GCC 13 | CMake build/install integration; full Flutter packaging unverified | Standalone native static/proxy/404/stop checks passed; Flutter application unverified |
| macOS arm64/x86_64 | Retained upstream source build integrated with universal compiler flags | Xcode bundles and signs a sandbox-inheriting helper | Not run: no Apple build host or device |
| iOS | No native Nginx process integration | WebForge remains the in-process engine | Apple builds unavailable; explicit Nginx reports unavailable |

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
