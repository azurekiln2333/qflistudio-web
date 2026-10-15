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

The iOS Runner builds the retained upstream C source as a static archive using
`scripts/bundle_nginx_ios.sh`, then links `libqfli_nginx.a`. It builds separately
for each requested arm64/x86_64 device/simulator target and checks every archive
object's Apple platform before creating the final archive. The source checksum
is verified before applying the separate `patches/embedded.patch`.

`native/nginx/embedded` owns one pthread running Nginx's single-process event
engine. It wakes Stop through a socketpair and reclaims connections, HTTP request
pools, backend state, files and mappings before reporting completion. It does
not install process signal handlers, redirect host stderr, modify the process
environment, or launch a child. Sessions use monotonic tokens and are serialized
until their completed worker is released. `EmbeddedNginxBridge.swift` exposes
this lifecycle through `qflistudio/nginx`; the shared Dart session preserves
configuration checks, health-token validation, diagnostics and middleware.

The cross-target configure probes compile and link against the selected iOS SDK;
type sizes and little endian byte order are checked with target static assertions.
Numeric runtime probes and the historical Darwin timer bug probe are skipped;
sendfile and legacy OSAtomic are disabled. No configure probe executes iOS code
on the macOS build host. Native device verification remains required.

The identical embedded engine passed Linux HTTP/proxy/error/stop checks and
100 lifecycle cycles under memory sanitizers. The Windows process integration
and Android application smoke also pass. Xcode, Apple hardware and an iOS
simulator are unavailable here: Apple compilation, signing and execution remain
unverified. These Linux results do not establish an iOS runtime pass.

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
QFLI_NGINX_BUILD_ROOT=<windows-visible-dir> \
  bash scripts/build_nginx_embedded.sh ohos <output> \
  /path/to/openharmony/native <arm64-v8a|x86_64>
```

The real upstream source cross-compiles with the OpenHarmony SDK into the
embedded archive `libqfli_nginx.a`. `ohos/entry/src/main/cpp/CMakeLists.txt`
links that archive into the NAPI module `libqfli_nginx_napi.so`
(`externalNativeOptions` with `abiFilters` `arm64-v8a` + `x86_64`),
`ohos/entry/src/main/ets/entryability/NginxBridge.ets` exposes the
`qflistudio/nginx` channel, and `EmbeddedNginxHost` drives it.
`ohos_socket_compat.h` adapts the SDK's `CMSG_NXTHDR` signed comparison without
disabling warnings. The Windows SDK `clang.exe` needs WSL path translation and a
Windows-visible build root; `native/nginx/embedded/ohos_cc.sh` handles both.

The standalone `scripts/build_nginx_ohos.sh` (`libnginx_exec.so`) is retained but
**not shipped**: `module.executableBinaryPaths` made `bm install` fail with
`9568449 ERR_INSTALL_CHECK_BIN_FILE_FAILED` on a HarmonyOS 7.0 phone, even though
the ELF was a valid PIE. The signed dual-ABI HAP now installs with no
executableBinaryPaths, and the in-app smoke passes HTML/CSS/404, native HTTP and
WebSocket proxying, diagnostics, the native access log, port-conflict, stop,
restart and `engine: auto` on the real phone. See `VALIDATION.md`.

## Product Integration

`.qfli/web.json` selects `engine: "auto" | "nginx" | "webforge"`. Auto uses the
packaged native binary when available. Explicit Nginx selection fails if the
binary is missing or fails startup; it never silently substitutes another engine.

Nginx owns the public loopback listener. A private Dart middleware listener
provides safe project files, SPA fallback, browser diagnostics and live reload.
Each session validates native configuration, forwards native access/error logs,
and stops the native engine and middleware together. Process hosts use `nginx -t`
and signals; the iOS host uses the embedded lifecycle ABI.

The embedded addon omits upstream process creation, daemon and process-title
sources. Its build rejects those objects and checks static archive imports for
fork/exec/process signals, retaining `undefined-symbols.txt`. Configuration-only
daemon/master disabling does not make upstream process sources compile on iOS.
Each build creates a new archive to remove obsolete members from reused outputs.

`HASHES.sha256` covers the retained source, patches, libraries and native binaries:

```bash
sha256sum --check vendor/nginx/HASHES.sha256
```

Mobile runtime claims require device verification in addition to successful
cross-compilation and packaging. See `VALIDATION.md` for evidence and remaining
checks. Android x86_64 application execution passed on an API 37 emulator with
16 KiB memory pages; arm64/32-bit devices remain unverified. iOS native Nginx
build and device execution remain unverified.
