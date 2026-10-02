# Implementation

- [x] Inspect every product's current runner and related task records.
- [x] Complete WebForge Linux/macOS build, packaging and discovery (c7614f8).
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
- [ ] Complete Rust Android/Apple and C/C++/Java iOS support where native lifecycle integration is missing.
- [x] Audit and deliver Lua/Go platform integration separately (31e0107, 68f91a5). Lua's ordinary Android release app passed source/check/compile/bytecode reload; Go's exact staged source passed all 18 tests and analysis, with prior Android 3-case and Linux/Windows SDK evidence retained.
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
