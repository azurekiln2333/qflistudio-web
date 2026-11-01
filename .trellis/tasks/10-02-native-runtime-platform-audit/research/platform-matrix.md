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
| Dart | Official SDK C++ VM / official Kernel compiler on Android and desktop; dart_eval on iOS/OHOS | lib/native_dart_toolchain.dart, lib/android_dart_sdk.dart; native/dart-sdk/android, bundle.cmake and bundle_macos.sh; 138affc, 1765860 |
| Java | OpenJDK javac + native JVM | lib/java_runner.dart, lib/mobile_jdk.dart; native/openjdk/android and ohos; iOS bridge absent |
| Go | Official SDK desktop; vendored Yaegi native interpreter with C ABI on mobile | lib/go_runner.dart, lib/go_platform.dart, lib/native_go_bridge_ffi.dart; native/go_runtime; tool/build_ios_go_runtime.sh; 68f91a5 |
| Rust | rustc/Cargo desktop; pinned rustc/Miri embedded adapter | lib/rust_runner.dart, lib/native_miri_assets.dart; native/miri_adapter; scripts/package_miri_runtime.py |
| SQL | Retained upstream SQLite C source; separate Oracle MySQL native port | lib/sqlite_ffi.dart, lib/sql_database.dart, lib/sql_runner.dart; native/runtime, platform FFI plugin; native/mysql OHOS |
| WebForge | Upstream Nginx plus WebForge middleware; embedded upstream C event engine for iOS | lib/web_runtime.dart; vendor/nginx; native/nginx/embedded; desktop/Apple build recipes; c7614f8 and pending embedded slice |

## Platform Integration

| Product | Android | Windows / Linux | macOS | iOS |
| --- | --- | --- | --- | --- |
| C/C++ | Dual-ABI LLVM package/bridge delivered as a3c1d4b, 2a16d36 and 398b093; fresh actual x64 app gate passed 8/8 after a pipe-drain fix applied to owning source; fix commit pending | Installed/bundled Clang/GCC discovery, native process compilation and execution | Same installed/bundled compiler path | Static LLVM/WasmEdge bridge/build/resource integration is implemented as uncommitted WIP; Apple package/build/execution unavailable |
| Lua | CMake shared library, FFI load and application runner | CMake builds and bundles shared library, FFI discovery | Runner compiles native engine; process symbol loading | Runner compiles native engine; retained FFI process symbols; restricted subprocess APIs |
| Python | Shared C engine, per-run JNI cancellation and upstream .mpy compile/load; 46/46 debug native cases and real debug/release UI workflows | Local FFI plugin and controlled worker lifecycle; Windows native cancellation/artifacts passed; earlier Linux engine execution passed | Shared C source pod, process-symbol loader and retained controlled FFI exports | Shared C source pod, process-symbol loader and retained controlled FFI exports |
| Dart | Complete pinned upstream SDK for ARM64/x86_64; installed native/data layout, real VM/Kernel, stdin/artifacts/stop; in-app x86_64 9/9 and ordinary UI passed (1765860) | Full official SDK bundled via CMake, process run and .dill compilation | Per-ABI SDK bundle, helper signing/JIT entitlements and architecture selection | Existing evaluator; native VM/compiler missing |
| Java | ARM64/x86_64 OpenJDK recipes and launch bridge; x86_64 in-app 8/8 and normal editor execution passed on 16 KiB emulator (ea7b4df); stale ARM64 package now rebuilt/audited with 16 KiB alignment, ordinary dual-ABI APK x64 editor also passed | Installed JDK discovery and real process run | Installed JDK discovery and real process run | Runner currently rejects platform; no native JVM bridge |
| Go | Packaged native interpreter SO and cancellable C ABI | Official SDK commands; installed SDK required | Official SDK commands; installed SDK required | C archive Xcode build/link, retained C ABI and process-symbol loader |
| Rust | Source-built pinned rustc/Cranelift/Miri for x64 and ARM64 packaged in owning repo; x64 source tests 5/5, editor workflow 1/1 and ordinary app exit 0; source commit pending WIP ownership | Cargo/rustc process backend; Windows real runner cases 21/21; generic embedded runtime packaging source exists | Desktop compiler path plus generic runtime framework packaging source | Native Miri routing/framework packaging source exists; compiler-private libraries and actual build remain required |
| SQL SQLite | Local plugin builds retained C source, FFI runs on isolate; native query and default workbench paths wired | CMake plugin builds/packages DLL/SO; real FFI loader and database operations | CocoaPods compiles retained source and retains every FFI symbol | CocoaPods compiles retained source and retains every FFI symbol |
| SQL MySQL | Oracle 8.4.6/OpenSSL builds for x86_64 and ARM64, installed code/data, private lifecycle and FFI delivered (497f969); x86_64 actual application tests pass | Native Oracle lifecycle/FFI and complete bundles delivered (0e02cb2); owning Windows/Linux each pass 11 checks | Per-ABI Oracle helper build/package/signing and ABI discovery source applied; Apple SDK/build/run unavailable; commit pending | Native server hosting missing |
| WebForge | PIE Nginx in extracted jniLibs, native-directory path bridge, current actual app smoke passes | Windows retained binary; Linux upstream-source CMake build/bundle/discovery | Upstream-source per-architecture helper build/sign/discovery | Embedded upstream pthread/ABI, iOS SDK/ARCHS static recipe, Swift channel and Dart host source implemented; Apple build/runtime unavailable |

## Evidence and Required Work

| Product | Evidence inspected | Unresolved requirement |
| --- | --- | --- |
| C/C++ | Fresh isolated x64 app 8/8: C/C++, mixed sources/headers/libm/stdin/streams/exit, compiler/linker failures, crash isolation, parent/child stop and fresh execution. Ordinary owning APK passed dual-ABI native/resource audits, then its x64 variant created a C++ project and editor Run printed the actual greeting with Android Clang cpp/exit 0 on API 37/16 KiB emulator-5562. Fix delivered and tool analysis plus 16 channel regressions pass | Commit the narrow pipe fix/tool/spec. ARM device execution absent. Original emulator-5560 lacked ordinary APK installation space; its data was preserved. Existing iOS/Web work remains uncommitted; Apple build/execution and browser compiler/runner completion are not established; preserve concurrent work |
| Lua | 31e0107 delivered; prior Windows CTest, 44 Flutter tests/analysis and AOT DLL execution; ordinary Android release app passed source execution, syntax checking, compilation and compiled-bytecode reload through the real editor | Apple/Linux application execution and Android ARM runtime unverified |
| Python | e4d0e40 platforms and 2f5ed81 lifecycle/artifacts; new slice passed 34 native FFI cases, staged and owning-repo 57/57 Flutter tests and clean source analysis; Android 46/46 JNI cases plus debug/release UI compile/stop/source-free .mpy execution; fresh owning Linux CMake SO passed 65 native and 10 lifecycle/artifact checks | Apple/MSVC/full Linux GUI unverified; arbitrary blocking native I/O is not cancellable |
| Dart | 138affc desktop and 1765860 Android delivered; owning repo 34 tests/clean source analysis; upstream Android SDK 3.13.5 in-app 9/9 and ordinary Run/compile/source-free .dill/Stop passed; all 30 staged and owning-APK SDK ELF files pass checks | Native iOS integration missing; Android ARM runtime, Apple and Linux execution unverified |
| Java | ea7b4df delivered x64 runtime: in-app JDK 8/8, 19 Windows Flutter tests and clean source analysis; ordinary APK editor exit 0. Fresh ARM64 recovery: all 71 exported ELF files and 44 owning staged files passed; ordinary dual-ABI APK passed all 89 JDK plus 3 framework ELF checks, exact Gradle strip provenance, data archive hashes and ZIP alignment; 215 preserved x64/OHOS inputs unchanged; task-owned x64 emulator ordinary and JDK cold-install editor runs exit 0 | Android ARM/API 28 execution unavailable; recovery evidence documentation commit awaits the required confirmation. Native iOS JVM integration remains missing. First task-emulator launch stayed on splash; restart and separate JDK cold-install/editor checks passed, with the cause of that first observation unisolated |
| Go | 68f91a5 delivered; prior Android 3 cases, Windows six SDK actions, Linux backend/native tests and 38 working-tree tests; exact staged native-platform source independently passed 18 tests and full analysis | No Apple execution or Linux Flutter GUI pass; installed SDK is a stated desktop prerequisite |
| Rust | Actual Android x64/ARM64 source compiler/backend/adapter builds and package audits; six owning APK native hashes/ABI/dependencies/16 KiB checks; x64 isolated 5/5 and editor 1/1, ordinary editor exit 0; owning 65 tests passed, 8 embedded Windows cases skipped; clean analysis | Runtime source delivery is applied but uncommitted pending existing WIP ownership. ARM64 device execution absent. Apple target compiler/package builds remain required. Matching Windows embedded adapter/sysroot absent; ordinary Windows Rust/Cargo runner is separately verified |
| SQL | SQLite 7269c12; desktop Oracle 0e02cb2 with Windows/Linux 11 checks each. Android Oracle 497f969: two real x86_64 in-app cases passed, both 64-bit builds/staging passed, owning ordinary APK returned 8.4.6. macOS helper integration source applied separately; 12 portable validators, 11 actual Windows lifecycle regressions and 51/51 owning Flutter tests pass, with clean changed-source analysis | Applied/tested engine selector overlaps existing uncommitted cloud SQL/core work and awaits commit ownership decision. macOS source commit and actual Oracle Apple SDK build/sign/sandbox execution remain pending. Native iOS hosting, ARM device execution and desktop GUI remain unverified or missing |
| WebForge | c7614f8; 38 Windows tests and clean source analysis; actual Android app smoke PASS repeated on build 4003 and normal build 4004 restored; Linux embedded engine 9/9 cases plus 100 ASan/UBSan/LSan lifecycle cycles repeated after removing process/daemon sources, with host state preserved and forbidden process-import gate passing; HarmonyOS embedded NAPI engine installed and in-app smoke PASS on a HarmonyOS 7.0 phone (`[NGINX_SMOKE] PASS ... log port-conflict stop restart auto`), plus an `nginx -t`-before-server access-log defect root-caused and fixed with a real-library regression | Embedded slice source/spec/evidence commit pending. Apple native build/link/sign/device gates, Linux Flutter GUI and Android ARM runtime remain unverified. OHOS detail lives in task `10-11-ohos-nginx-embedded` |

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
  Later WSL export and native compilation succeeded; Android Java delivery
  completed after rebuilding its single incompatible spawn dependency.
- Windows HTTPS downloads of the Termux Dart recipe/index ended in Schannel TLS
  handshake failures. Later pinned recipe retrieval through the public CDN and
  both hash-verified SDK downloads through the USTC mirror succeeded. Android
  native delivery and application verification then completed as 1765860.

The complete cross-product goal remains active while these implementation gaps
and delivery requirements remain. Do not turn this matrix into a whole-goal pass.
