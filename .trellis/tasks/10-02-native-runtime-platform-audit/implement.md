# Implementation

- [x] Inspect every product's current runner and related task records.
- [x] Complete WebForge Linux/macOS build, packaging and discovery (c7614f8).
- [x] Implement and review native Dart desktop run and Kernel compilation in a source snapshot.
- [x] Run 33 Dart snapshot tests and static analysis on Windows.
- [x] Verify SDK bundle installation and execution independently of the source SDK (5 installed-bundle tests).
- [x] Apply the verified Dart patch to qfli_dart and commit its own paths (138affc; 33 owning-repository tests and clean analysis).
- [ ] Implement native mobile Dart; its existing dart_eval backend does not satisfy this requirement.
- [x] Verify and deliver Python desktop/Apple FFI (e4d0e40): Windows 34 native FFI cases, Linux 65 C cases, 44 staged Flutter tests, clean analysis and Android x86_64 regression build.
- [x] Install and execute the fresh Python APK; application-native MicroPython self-check passed 36/36 on emulator-5560. Restore and launch the ordinary SQL APK.
- [ ] Add native Python cancellation and reusable compiler artifacts.
- [x] Deliver SQLite Android/desktop/Apple FFI (7269c12): Windows build, 48 staged Flutter tests and 7 Android backend/default-workbench cases.
- [x] Verify standalone Linux Nginx (4 checks) and SQLite C library (5 checks).
- [ ] Complete local native MySQL platform lifecycle beyond OHOS.
- [ ] Complete Rust Android/Apple and C/C++/Java iOS support where native lifecycle integration is missing.
- [ ] Audit Lua and Go builds, packaging, ABI loading and execution evidence across platforms.
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
errors. A subsequent read-only Java image inspection through WSL again returned
automatic approval review HTTP 503; that action did not execute. Apple
hardware/Xcode and Android arm64/32-bit devices are absent. Do not run or claim
tests for an unavailable native environment. See research/verification-2026-10-02.md.
