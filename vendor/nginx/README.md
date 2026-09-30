# Nginx Runtime

The product uses actual upstream Nginx 1.31.6. `SOURCE.json` records the official
source/Windows archives and SHA-256 values. The compressed upstream source is
retained here; generated build trees live under `build/native/nginx/`.

## Windows

`assets/runtime/nginx/windows/nginx.exe` is the official Windows binary. CMake
installs it and the upstream license into the application bundle's
`data/nginx/` directory. It can also be exercised from the checkout by Dart tests.

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
