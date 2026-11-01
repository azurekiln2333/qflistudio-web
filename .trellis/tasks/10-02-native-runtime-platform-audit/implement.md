# Implementation

- [x] Inspect every product's current runner and related task records.
- [x] Complete WebForge Linux/macOS build, packaging and discovery (c7614f8).
- [ ] Complete actual embedded Nginx integration for iOS.
  - [x] Implement the retained upstream single-process native library and isolated lifecycle ABI.
  - [x] Compile and verify the identical native engine on available Linux, including repeated cleanup and host-state preservation (9 real-library cases and 100 sanitizer/descriptor/sigaction/stdio cycles).
  - [x] Remove upstream process/daemon sources that still compile forbidden iOS fork calls; add archive dependency checks and repeat normal/sanitized 9-case and 100-cycle gates (2026-10-03).
  - [x] Add iOS static archive/Xcode build integration and native MethodChannel lifecycle source; Apple compile/link/device gates remain unavailable.
  - [x] Connect shared Nginx session host selection and verify available regressions (38 Windows tests, clean source analysis and actual Android smoke PASS; ordinary build 4002 restored).
  - [x] Reconnect Android with a read-only emulator overlay, repeat the full application smoke on build 4003 and restore ordinary build 4004 (2026-10-03).
  - [ ] Update contracts/evidence and prepare the owning commit; explicitly skip unavailable Apple build/runtime gates.
- [x] Implement and review native Dart desktop run and Kernel compilation in a source snapshot.
- [x] Run 33 Dart snapshot tests and static analysis on Windows.
- [x] Verify SDK bundle installation and execution independently of the source SDK (5 installed-bundle tests).
- [x] Apply the verified Dart patch to qfli_dart and commit its own paths (138affc; 33 owning-repository tests and clean analysis).
- [ ] Complete native mobile Dart; Android is delivered, native iOS remains unresolved.
  - [x] Recover upstream recipe and verify x86_64 SDK package SHA-256; actual Android VM version probe passed.
  - [x] Verify ARM64 input and stage/package both full native SDKs with data/installed-code layout; 30 ELF files pass ABI, 16 KiB LOAD and system dependency checks.
  - [x] Route Android execution and Kernel compilation through the real VM; support stdin, EOF, artifacts and stop.
  - [x] Verify in-app 9/9 checks, ordinary editor/tools workflows, source analysis and 34 owning-repository tests; deliver 1765860.
  - [ ] Implement native iOS SDK/VM/compiler integration; no Apple execution claim without an available environment.
- [x] Deliver the existing Android x86_64 OpenJDK image (ea7b4df).
  - [x] Export and audit every packaged ELF and shared-library dependency (46 ELF files; rebuild the retained upstream spawn library).
  - [x] Stage, build and execute all eight in-app JDK smoke checks on the 16 KiB emulator (API 37, emulator-5560).
  - [x] Restore and verify the normal Java app, review native changes and commit separately (ea7b4df; owning APK editor run exit 0).
- [x] Replace the stale Android ARM64 4 KiB JDK package with a fresh real upstream 16 KiB build.
  - [x] Build with current pinned recipe in an independent WSL ext4 directory.
  - [x] Export/audit every native input and dependency, then stage only ARM64 while preserving x64 and OHOS (71 image and 44 staged ELF files; 215 preserved input hashes unchanged).
  - [x] Verify owning dual-ABI APK inputs (89 JDK and 3 framework ELF files, exact Gradle strip provenance, both data archives and ZIP alignment); record ARM physical-device execution as unavailable.
  - [x] Apply the narrow runtime documentation and local spec evidence; verify ordinary x64 project creation/editor execution and JDK cold-install/editor recovery on task-owned emulator-5562.
  - [ ] Commit the two tracked Java documentation paths after the required plan confirmation; generated artifacts and the existing ignored spec remain outside Git.
- [x] Verify and deliver Python desktop/Apple FFI (e4d0e40): Windows 34 native FFI cases, Linux 65 C cases, 44 staged Flutter tests, clean analysis and Android x86_64 regression build.
- [x] Install and execute the fresh Python APK; application-native MicroPython self-check passed 36/36 on emulator-5560. Restore and launch the ordinary SQL APK.
- [x] Add native Python cancellation and reusable compiler artifacts (2f5ed81).
  - [x] Implement token ownership, VM interruption and bounded sleep cancellation.
  - [x] Connect early runner results and cancellation through FFI and Android JNI.
  - [x] Compile/load upstream .mpy artifacts and expose project compilation.
  - [x] Run real Windows native/runner and Android regression/lifecycle cases: 34 native FFI cases, 57 Flutter tests, clean source analysis, Android 46 JNI cases and normal debug/release UI compile/stop/artifact execution.
  - [x] Review the narrow delivery patch, update the runtime contract and commit (2f5ed81); the owning repository rebuilt its DLL and passed 57/57 tests plus clean source analysis.
- [x] Deliver SQLite Android/desktop/Apple FFI (7269c12): Windows build, 48 staged Flutter tests and 7 Android backend/default-workbench cases.
- [x] Verify standalone Linux Nginx (4 checks) and SQLite C library (5 checks).
- [ ] Complete local native MySQL platform lifecycle beyond OHOS.
  - [x] Deliver Windows/Linux Oracle service ownership, credentialed native FFI and desktop bundles (qfli_sql 0e02cb2).
  - [x] Verify staged and owning Windows/Linux installed runtime bundles, each with 11 real-engine checks; staged/owning Flutter tests pass 51/51 with clean changed-source analysis.
  - [ ] Build and integrate the Android server and connect local engine selection to the workbench/editor.
    - [x] Deliver Android Oracle/OpenSSL x86_64 and ARM64 build, installed code/resources, FFI and private server lifecycle (qfli_sql 497f969).
    - [x] Pass two real x86_64 application integration cases, owning 51/51 tests, changed-source analysis and ordinary APK query/version inspection.
    - [x] Audit eight staged native inputs and all six x86_64 owning APK native files for ABI, 16 KiB LOAD, dependencies and Oracle input identity.
    - [ ] Commit the applied local engine selector and its device tests; overlapping existing cloud SQL/core API work awaits the requested ownership decision.
  - [ ] Complete macOS bundle/signing and native iOS hosting; portable desktop source alone does not establish Apple delivery.
    - [x] Integrate per-ABI macOS Oracle helper build, dependency relocation, validation and signing source into Xcode; actual Apple packaging remains unverified.
    - [x] Connect helper discovery and plugin paths; pass 12 portable validators and 11 Windows Oracle lifecycle checks, and deliver 15 clean owning paths.
    - [ ] Commit the macOS integration paths after the project-required commit-plan confirmation.
    - [ ] Build/run on an Apple host; this host lacks Xcode and Oracle macOS SDK inputs.
- [ ] Complete Rust Android/Apple and C/C++/Java iOS support where native lifecycle integration is missing.
  - [x] Verify actual C/C++ Android x64 compiler/program path in an isolated app (8/8); fix natural-exit pipe destruction and deliver tool/spec to qfli_c, with clean tool analysis and 16/16 channel regressions.
  - [x] Build/audit the ordinary owning C/C++ app and verify project creation plus C++ editor Run/exit 0 on task-owned x64 emulator-5562 (API 37, 16 KiB); original emulator-5560 lacked installation space and its apps/data were preserved.
  - [ ] Commit the narrow C/C++ pipe fix, audit tool and Android runtime spec; preserve unrelated owning runtime WIP.
  - [x] Recover independent pinned Rust/NDK inputs and pass Windows Rust/Cargo runner checks (21/21).
  - [x] Build actual x64 Android driver, Cranelift backend and Miri adapter; audit three native libraries and guest MIR provenance.
  - [x] Fix source-archive metadata identity and add bootstrap recovery/preflight regression checks (6/6).
  - [x] Pass isolated Android source-execution (5/5) and editor save/run/stop/fresh-run (1/1); retain the first E0514 failure separately.
  - [x] Build/package/audit ARM64 separately; six native files in the owning dual-ABI APK match packaged hashes and pass ABI/dependency/16 KiB checks.
  - [x] Apply eight verified source paths and generated native/data packages to qfli_rust; owning analysis is clean and tests pass 65 with 8 explicitly skipped Windows embedded cases.
  - [x] Restore and launch the ordinary Rust app; AndroidRustNative editor prints Hello, QFLIStudio+! and exits 0.
  - [ ] Resolve existing Rust runtime WIP ownership, verify the exact commit contents and commit in qfli_rust.
  - [ ] Build/package native Apple compiler hosts; no Apple build/execution evidence is available on this host.
- [x] Audit and deliver Lua/Go platform integration separately (31e0107, 68f91a5). Lua's ordinary Android release app passed source/check/compile/bytecode reload; Go's exact staged source passed all 18 tests and analysis, with prior Android 3-case and Linux/Windows SDK evidence retained.
- [ ] Complete Lua default stdin integration discovered during Linux verification.
  - [x] Build the owning retained Lua 5.4.8 C source on Linux; native CTest passes with Unix Makefiles after the unavailable Ninja attempt and transient WSL startup failure.
  - [ ] Add per-state project input.txt / missing-file EOF, with host stdin preservation and regular-file validation.
  - [ ] Verify native Linux/Windows outcomes and deliver the narrow owning patch; preserve other WIP and skip unavailable Apple gates.
- [x] Rebuild the delivered Python Linux SO and pass 65 native plus 10 actual cancellation/artifact checks; full Linux Flutter GUI remains unverified.
- [ ] Verify all available environments and explicitly record every unavailable test target.
- [ ] Perform a full requirement audit before marking this goal complete.

## Verification

Use actual engine execution to establish a runtime pass. Mock channels, a shared
library filename, syntax checks and task planning files are insufficient. Retain
stdout/stderr, exit, compile artifacts, imported files and stop assertions.
The Windows Flutter application cannot currently be built because Visual Studio
C++ tools are absent; standalone engine and Flutter test execution are available.
WSL is now available: Python, SQLite and Nginx native execution was verified.
The earlier Android installation review failures were resolved: both ordinary
debug APKs were installed successfully, Python passed 36/36 native self-checks,
and SQL's normal application was restored and launched without AndroidRuntime
errors. Two subsequent read-only Java image inspection requests through WSL
returned automatic approval review HTTP 503; neither action executed. Apple
hardware/Xcode and Android arm64/32-bit devices are absent. Do not run or claim
tests for an unavailable native environment. See research/verification-2026-10-02.md.
