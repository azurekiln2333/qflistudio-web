# Nginx Runtime

The product uses actual upstream Nginx 1.31.6. `SOURCE.json` records the official
source/Windows archives and SHA-256 values. The compressed upstream source is
retained here; generated build trees live under `build/native/nginx/`.

## Windows

`assets/runtime/nginx/windows/nginx.exe` is the official Windows binary. CMake
installs it and the upstream license into the application bundle's
`data/nginx/` directory. It can also be exercised from the checkout by Dart tests.

## Linux and macOS

The desktop ports build the retained upstream C source without a download.
They need Bash, tar, make, a native C compiler and checksum tools (`sha256sum`
on Linux, `shasum` on macOS). The build omits gzip, rewrite and auth-basic so
PCRE, zlib and crypt do not become extra package dependencies. Native HTTP and
WebSocket proxies use the same product integration as Windows and Android.

Linux CMake builds Nginx automatically and installs it, with executable
permissions and its license, into `data/nginx/` next to the application.
Build on the target Linux machine; cross-compiling the runner is rejected
because Nginx's configure probes must run for the target operating system.

The macOS Xcode target builds with all requested `ARCHS` (arm64 and/or x86_64),
copies the executable into `Contents/Helpers/nginx`, and signs it before the
outer app with the app's signing identity. `Nginx.entitlements` enables sandbox
inheritance; the parent app grants both network client and server access. The
source build uses universal compiler flags for both probes and final objects.
The bundled upstream license lives in `Contents/Resources/nginx/`.

For desktop integration tests from a checkout, build the host executable first:

```bash
bash scripts/build_nginx_desktop.sh linux
# On an Apple build host:
ARCHS="arm64 x86_64" bash scripts/build_nginx_desktop.sh macos
flutter test --no-pub test/nginx_session_test.dart
```

The default output is `assets/runtime/nginx/<platform>/nginx`. Generated Unix
executables and source build trees are ignored. Application builds select their
own output directories. The integration suite discovers the host runtime and
marks itself skipped when no native build exists; a skip is not runtime proof.

## iOS

The iOS app uses the existing in-process WebForge server for local preview,
proxying and live reload. It does not claim native Nginx. The upstream process
lifecycle uses executable launch and signals, which are not available to an iOS
application. An in-process Nginx port would need separate event-loop and global
state integration. Explicit Nginx selection therefore reports an unavailable
runtime rather than selecting a different engine.

## Android


From Linux or WSL, build each supported ABI using an installed NDK:

```bash
bash scripts/build_nginx_android.sh arm64-v8a /path/to/android-ndk
bash scripts/build_nginx_android.sh armeabi-v7a /path/to/android-ndk
bash scripts/build_nginx_android.sh x86_64 /path/to/android-ndk
```

WSL can use the Windows NDK through its clang/llvm-ar executables. Built PIE
executables are packaged as `jniLibs/<abi>/libnginx_exec.so`; legacy native-library
extraction supplies an executable path inside the APK's native library directory.
Do not copy them into writable app data to execute them. The build targets API 24
and uses 16 KiB ELF segment alignment.

`patches/` and `android-glob/` are from the Termux package implementations:
https://github.com/termux/termux-packages/tree/master/packages/nginx
https://github.com/termux/termux-packages/tree/master/packages/libandroid-glob
Their bytes are retained in the repo. The glob library retains its BSD license.
The native Android build disables rewrite/auth-basic modules to avoid adding
PCRE/crypt dependencies. HTTPS upstream transport runs through the Dart bridge;
plain HTTP proxies and WebSocket upgrades run directly in Nginx.

The local `android-stat-*.patch` and `android-socklen.patch` adapt signed file
sizes and socket lengths to Bionic's 32-bit ABI. They keep compiler warnings
enabled. `scripts/nginx_cc.sh` normalizes Clang CRLF output and supplies argv[0]
when invoking Windows tools through WSL's `/init` interpreter. Shell scripts,
patches and C inputs retain LF on Windows checkouts through scoped attributes.

## HarmonyOS

```bash
bash scripts/build_nginx_ohos.sh arm64-v8a /path/to/openharmony/native
bash scripts/build_nginx_ohos.sh x86_64 /path/to/openharmony/native
```

The real upstream source cross-compiles with the OpenHarmony SDK. Outputs go to
`ohos/entry/libs/<abi>/libnginx_exec.so`. `ohos_socket_compat.h` adapts the SDK's
`CMSG_NXTHDR` signed comparison without disabling warnings. The SDK's definition
is in `native/sysroot/usr/include/sys/socket.h`.

The API 24 x86_64 phone simulator executed this binary with `-V` from the shell.
The original application package resolved the library with mode `100644`, and
`Process.run(..., ['-v'])` returned `Permission denied`. System `echo` execution
inside the app succeeded. `module.executableBinaryPaths` now declares both
`libs/<abi>/libnginx_exec.so` paths; the signed dual-ABI HAP retains these entries.
Application execution after this manifest change is still unverified.
Automatic selection uses WebForge when this exec permission error occurs;
explicit Nginx selection reports the error. Further phone/device execution
integration is required. `childProcessManager.startNativeChildProcess` is
documented by the local SDK as available on PCs/2-in-1 devices and tablets.

## Product Integration

`.qfli/web.json` selects `engine: "auto" | "nginx" | "webforge"`. Auto uses the
packaged native binary when available. Explicit Nginx selection fails if the
binary is missing or fails startup; it never silently substitutes another engine.

Nginx owns the public loopback listener. A private Dart middleware listener
provides safe project files, SPA fallback, browser diagnostics and live reload.
Each session validates native configuration with `nginx -t`, forwards native
access/error logs, and stops the native process and middleware together.

`HASHES.sha256` covers the retained source, patches, libraries and native binaries:

```bash
sha256sum --check vendor/nginx/HASHES.sha256
```

Mobile runtime claims require device verification in addition to successful
cross-compilation and packaging. See `VALIDATION.md` for evidence and remaining
checks. Android x86_64 application execution passed on an API 37 emulator with
16 KiB memory pages; arm64/32-bit devices remain unverified. iOS native Nginx
integration is not established.
