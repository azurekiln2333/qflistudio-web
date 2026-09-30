# Native Nginx Integration

## Requirement

The original request explicitly asks to port a real server such as Nginx, rather
than implementing a substitute. The Dart development service and Web tools are
completed work toward that goal; they do not satisfy the native port requirement.

## Evidence Collected on 2026-09-30

- Official Windows docs provide a native console executable and `-s stop`,
  `-s quit`, and `-s reload` lifecycle commands. Windows paths in configuration
  must use forward slashes. Windows Nginx uses select/poll and has limited
  worker scaling: https://nginx.org/en/docs/windows.html
- The official download page lists upstream source and Windows distributions:
  https://nginx.org/en/download.html
- Termux has a real Android Nginx build, including cross-compilation patches,
  precomputed Android feature values, and dependencies on android-glob, crypt,
  PCRE2, OpenSSL, and zlib. Its prefix is Termux-specific; its executable cannot
  simply be copied into this app. Reference implementation:
  https://github.com/termux/termux-packages/tree/master/packages/nginx
- Android 10 target apps cannot exec files from their writable app home
  directory. Native binaries must ship in the APK, with packaging and execution
  validated on a current target-SDK device. Do not extract an executable asset
  into app data and assume `chmod` makes it runnable:
  https://developer.android.com/about/versions/10/behavior-changes-10#execute-permission
- An OpenHarmony native LLVM toolchain exists at the local DevEco SDK path.
  No Nginx source, build integration, packaged Nginx binary, or device execution
  proof exists yet. Android/Termux success is not proof of HarmonyOS support.
- iOS requires a different embedding approach from desktop child-process
  execution. A real port is not currently established; do not advertise it.

## Local Build Environment

The following was the initial environment snapshot; later device findings are
recorded under Implementation Evidence Update.

- WSL `qfli-java-build` starts successfully and provides cc, make, and patch.
- The `Ubuntu` instance fails because its registered ext4.vhdx is missing.
- Android NDK 27.0.12077973 is installed, with clang and make for Windows.
- OpenHarmony clang is installed in DevEco Studio's default SDK.
- `where.exe nginx` found no installed Nginx.
- Android `adb devices` and HarmonyOS `hdc list targets` are empty.
- `flutter build apk --debug --no-pub` passed.
- `flutter build hap --debug --no-pub` passed and produced a signed HAP.
- Windows Flutter build is blocked by a missing Visual Studio C++ toolchain.
- iOS/macOS source integration cannot be compiled on this Windows host.

## Next Implementation

1. Pin and retain actual upstream Nginx source, license, and reproducible build
   inputs; start with Android/HarmonyOS cross-compilation and the official
   Windows executable.
2. Package the native binary using each platform's executable-code rules.
3. Add a product-owned process/session adapter with an isolated runtime prefix,
   config validation before startup, loopback binding, log forwarding, and full
   shutdown on editor/tool disposal.
4. Keep the existing diagnostics and reload features available when Nginx is
   selected. Never silently report Nginx if native startup failed.
5. Verify startup, actual HTTP serving, proxies/WebSocket upgrades, reload,
   occupied ports, invalid configuration, and shutdown using the real binary.
6. Keep this task in progress until the native port and required device checks
   are proven. Build success alone does not prove mobile execution.

## Implementation Evidence Update

Official Nginx 1.31.6 source and the Windows executable are retained with hashes
and licenses. Windows real-binary tests now pass for serving, diagnostics/logs,
native HTTP/WebSocket proxies, HTTPS prefix priority, reload and shutdown.
Android NDK 27 produced all three ABI executables with 16 KiB PIE alignment; the
debug APK includes all binaries and both licenses.

OpenHarmony SDK Clang 15.0.4 built arm64-v8a and x86_64. The API 24 x86_64 phone
simulator appeared during this continuation. Its shell ran the real binary's
`-V`, and a signed test HAP installed. App `nginxPath` resolved
`/data/storage/el1/bundle/libs/x86_64/libnginx_exec.so`; app `Process.run(..., ['-v'])`
failed with `Permission denied`. Follow-up app probes confirmed mode `100644`
and successful `/system/bin/echo` execution. This narrows the failure to packaged
executable permissions, without proving there are no further execution limits.
The local module schema and Hvigor pre-build validator expose
`module.executableBinaryPaths`; both module-relative `libs/<abi>/libnginx_exec.so`
paths are declared, and signed dual-ABI HAP packaging preserves them. The
simulator disconnected before the updated HAP could be verified in the app.

The local `@ohos.app.ability.childProcessManager.d.ts` describes
`startNativeChildProcess` as supported on PCs/2-in-1 devices and tablets; on other
device types it returns 801. App EACCES and shell success must be treated as
different evidence. Native application execution remains unresolved. Auto uses
WebForge for this specific permission failure; explicit Nginx fails truthfully.

On 2026-10-01 the user switched debugging to Android. The connected
`emulator-5556` reports API 37, x86_64, and `getconf PAGESIZE` of `16384`. Running
`tool/nginx_smoke.dart` produced a real application PASS for HTML/CSS, HTTP
proxying, WebSocket, SSE reload, diagnostics, native access logs, 404, occupied
port rejection, shutdown, restart and default automatic Nginx selection. The app
resolved the executable inside its extracted native library directory.
Arm64/32-bit and older API execution still need device evidence.

WSL Windows NDK/SDK tools work via `/init executable argv[0] args`; normal exec
became unavailable when WSLInterop's binfmt registration disappeared. Clang CRLF
normalization remains necessary for generated configuration strings. Android
32-bit Bionic needs signed stat-block and socket-length comparison patches;
OpenHarmony's socket header needs a local CMSG_NXTHDR comparison adaptation.
