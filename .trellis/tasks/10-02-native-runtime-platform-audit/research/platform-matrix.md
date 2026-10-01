# Native Platform Matrix

Source roots are `D:/MyNewProjects/qfli_<product>`. Updated 2026-10-02.
An implemented loader or a completed task is not runtime evidence. Other chats'
recorded passes are identified below; they were not all replayed by this audit.

## Engines and Ownership

| Product | Actual engine | Owning source / build boundary |
| --- | --- | --- |
| C/C++ | Clang/GCC desktop, native Clang Android; in-process LLVM/Wasm iOS work in progress | lib/forge_runner.dart, lib/clang_runner.dart, lib/android_clang_runner.dart; native/toolchain; current C chat |
| Lua | Retained upstream Lua 5.4.8 C compiler/VM | lib/lua_toolchain.dart; native/CMakeLists.txt; Android app CMake and Apple Runner source/link integration; 31e0107 |
| Python | Retained upstream MicroPython C compiler/VM | lib/python_runner.dart, lib/python_ffi.dart; native/desktop, windows, linux, apple/podspec.rb; e4d0e40 and controlled lifecycle/artifact delivery 2f5ed81 |
| Dart | Official SDK C++ VM / official Kernel compiler on desktop; dart_eval on mobile | lib/native_dart_toolchain.dart; native/dart-sdk/bundle.cmake and bundle_macos.sh; 138affc |
| Java | OpenJDK javac + native JVM | lib/java_runner.dart, lib/mobile_jdk.dart; native/openjdk/android and ohos; iOS bridge absent |
| Go | Official SDK desktop; vendored Yaegi native interpreter with C ABI on mobile | lib/go_runner.dart, lib/go_platform.dart, lib/native_go_bridge_ffi.dart; native/go_runtime; tool/build_ios_go_runtime.sh; 68f91a5 |
| Rust | rustc/Cargo desktop; pinned rustc/Miri embedded adapter | lib/rust_runner.dart, lib/native_miri_assets.dart; native/miri_adapter; scripts/package_miri_runtime.py |
| SQL | Retained upstream SQLite C source; separate Oracle MySQL native port | lib/sqlite_ffi.dart, lib/sql_database.dart, lib/sql_runner.dart; native/runtime, platform FFI plugin; native/mysql OHOS |
| WebForge | Upstream Nginx plus WebForge middleware; in-process Dart server on iOS | lib/web_runtime.dart; vendor/nginx; scripts/build_nginx_desktop.sh and bundle_nginx_macos.sh; c7614f8 |

## Platform Integration

| Product | Android | Windows / Linux | macOS | iOS |
| --- | --- | --- | --- | --- |
| C/C++ | Native Clang bridge and packaged toolchain; owning chat actively changing compiler/Wasm support | Installed/bundled Clang/GCC discovery, native process compilation and execution | Same installed/bundled compiler path | Native in-process compiler/Wasm design and source work still in progress; no verified deliverable |
| Lua | CMake shared library, FFI load and application runner | CMake builds and bundles shared library, FFI discovery | Runner compiles native engine; process symbol loading | Runner compiles native engine; retained FFI process symbols; restricted subprocess APIs |
| Python | Shared C engine, per-run JNI cancellation and upstream .mpy compile/load; 46/46 debug native cases and real debug/release UI workflows | Local FFI plugin and controlled worker lifecycle; Windows native cancellation/artifacts passed; earlier Linux engine execution passed | Shared C source pod, process-symbol loader and retained controlled FFI exports | Shared C source pod, process-symbol loader and retained controlled FFI exports |
| Dart | Existing evaluator; native VM/compiler missing | Full official SDK bundled via CMake, process run and .dill compilation | Per-ABI SDK bundle, helper signing/JIT entitlements and architecture selection | Existing evaluator; native VM/compiler missing |
| Java | ARM64 OpenJDK image and launch bridge; prior emulator runtime failed | Installed JDK discovery and real process run | Installed JDK discovery and real process run | Runner currently rejects platform; no native JVM bridge |
| Go | Packaged native interpreter SO and cancellable C ABI | Official SDK commands; installed SDK required | Official SDK commands; installed SDK required | C archive Xcode build/link, retained C ABI and process-symbol loader |
| Rust | Mobile now routes to native Miri assets/FFI; matching runtime libraries still need source build and delivery | Cargo/rustc process backend; generic embedded runtime packaging source exists | Desktop compiler path plus generic runtime framework packaging source | Native Miri routing/framework packaging source exists; compiler-private libraries and actual build remain required |
| SQL SQLite | Local plugin builds retained C source, FFI runs on isolate; native query and default workbench paths wired | CMake plugin builds/packages DLL/SO; real FFI loader and database operations | CocoaPods compiles retained source and retains every FFI symbol | CocoaPods compiles retained source and retains every FFI symbol |
| SQL MySQL | Native local server/client lifecycle missing | Native local server/client lifecycle missing | Native local server/client lifecycle missing | Native local server/client lifecycle missing |
| WebForge | PIE Nginx in extracted jniLibs, native-directory path bridge, real app lifecycle | Windows retained binary; Linux upstream-source CMake build/bundle/discovery | Upstream-source per-architecture helper build/sign/discovery | WebForge Dart server; upstream native Nginx missing |

## Evidence and Required Work

| Product | Evidence inspected | Unresolved requirement |
| --- | --- | --- |
| C/C++ | Current runner routes through Clang first; current C chat reports active in-process compiler build | Verify its actual delivered compiler and platform tests; do not overwrite concurrent work |
| Lua | 31e0107 delivered; prior Windows CTest, 44 Flutter tests/analysis and AOT DLL execution; ordinary Android release app passed source execution, syntax checking, compilation and compiled-bytecode reload through the real editor | Apple/Linux application execution and Android ARM runtime unverified |
| Python | e4d0e40 platforms and 2f5ed81 lifecycle/artifacts; new slice passed 34 native FFI cases, staged and owning-repo 57/57 Flutter tests and clean source analysis; Android 46/46 JNI cases plus debug/release UI compile/stop/source-free .mpy execution | Apple/MSVC/full Linux GUI unverified; Linux re-execution of the new lifecycle slice awaits WSL approval recovery; arbitrary blocking native I/O is not cancellable |
| Dart | 138affc delivered; owning-repo 33 tests and clean analysis; standalone SDK installation plus 5 installed-bundle tests | Genuine mobile SDK/VM/compiler packaging; source inputs/download access; Apple/Linux execution unverified |
| Java | Earlier Android attempt failed; latest owning-chat build and live ELF inspection confirm new x86_64 launcher/JVM 0x4000 LOAD alignment | Stage and execute the new image through the actual Android app; audit remaining dependencies and JVM page-size behavior; commit existing platform changes; iOS engine remains missing |
| Go | 68f91a5 delivered; prior Android 3 cases, Windows six SDK actions, Linux backend/native tests and 38 working-tree tests; exact staged native-platform source independently passed 18 tests and full analysis | No Apple execution or Linux Flutter GUI pass; installed SDK is a stated desktop prerequisite |
| Rust | Pinned rustc-dev/Miri design and generic target packaging/FFI source inspected; prior reference fixture evidence exists | Actual target-matching Android/Apple compiler-private source builds and application evidence remain required |
| SQL | 7269c12; Windows native build, all 48 staged tests, 7 staged Android backend/default-workbench cases; all 3 SQLite ABIs 0x4000 aligned; Linux SO 5 C checks; ordinary Android app restored and launched | Oracle MySQL local lifecycle beyond OHOS remains missing; Apple/full Linux GUI unverified |
| WebForge | c7614f8; 33 Windows tests/analysis and prior Android app smoke; fresh Linux upstream build passed static/proxy/404/stop checks | Native iOS Nginx missing; Apple and Linux Flutter application execution plus Android ARM runtime unverified |

## Environment Skips

- No Apple host, Xcode or Apple devices: no macOS/iOS build or execution claim.
- No Android ARM physical device: x86_64 app tests do not establish ARM runtime.
- No Visual Studio C++ tools: full Windows Flutter GUI builds are unavailable;
  standalone native engines and Flutter tests are available and were used.
- WSL became available on 2026-10-02. Python, SQLite and Nginx native engine
  execution passed. Full Linux Flutter application builds remain unverified.
- Earlier Android ordinary-app installation requests returned automatic
  approval review HTTP 503. Subsequent installs succeeded for both SQL and
  Python; Python's application-native self-check passed 36/36. Two later WSL
  read-only inspections of the existing Java image hit review HTTP 503.
  Neither WSL action executed; the service failure is not a compiler result.
- Windows HTTPS downloads of the Termux Dart recipe/index ended in Schannel TLS
  handshake failures. These are failed source downloads, not successful Android
  Dart implementation and not an approval rejection.

The complete cross-product goal remains active while these implementation gaps
and delivery requirements remain. Do not turn this matrix into a whole-goal pass.
