# C/C++ Android Native Execution

## Source And Boundary

The owning repository is D:/MyNewProjects/qfli_c. Its archived mobile LLVM task
and commits a3c1d4b, 2a16d36, 398b093 and 4f86187 establish local compiler builds,
dual-ABI packaging, native channels and startup integration. That task explicitly
deferred device execution. The user's current Android-debugging instruction
authorizes this separate cross-product application gate.

Export HEAD 99adbf4 into build/native/platform-audit/c-android-delivery/review.
Only the verification copy uses absolute shared-core dependencies, an isolated
com.azurekiln.qfli.forge.platformaudit application ID, x86_64-only native filters
and the audit entry point. Existing Web/iOS/desktop/OHOS work remains preserved.
The test calls the actual packaged native Android runner; no C fallback is used.

## Failure And Fix

The first actual app run passed C source execution. C++ standard library and
exceptions printed the expected exception 42 but reported exit 127 with
java.io.InterruptedIOException: read interrupted by close() on another thread.
NativeCompilerBridge.invoke had waited for the child, then called cancelProcess
before awaiting its pipe readers. Android Process.destroy closes those pipes
even if the child has already exited, racing the remaining output drain.

The narrow fix checks exitValue before destroy. A completed Process keeps its
pipes open until both readers finish; a live Process still receives destroy.
Process-group termination remains intact so inherited child pipes cannot keep
the read futures alive. exitValue supports API 24 without a newer isAlive API.
No error suppression or fabricated success status was added.

## Actual Device Results

emulator-5560, API 37, x86_64, actual page size 16384. Fixed source passed 8/8:

- Real C compilation/execution, stdout and exit 0.
- C++ vector/numeric standard library and thrown/caught exceptions, exit 0.
- C main plus C++ helper and project header, nonconstant libm, stdin, separate
  stdout/stderr and nonzero exit 17.
- Real compiler diagnostics, exit 1, no stale stdout.
- Real linker diagnostics, exit 1, no stale stdout.
- A SIGSEGV user program, exit 139, with the Flutter application still alive.
- Stop of a parent and forked heartbeat child, exit 130; child writes cease.
- Fresh successful source execution after errors, crash and stop.

The app emitted QFLI_C_ANDROID_AUDIT with ok:true in process 12690. Logs:
device-audit.log retains the original failure; device-audit-r2.log retains all
eight passes. Kotlin in the delivered repository matches the device-tested
source after CRLF normalization. The final test entry's subsequent changes only
add braces and switch print to Flutter's synchronous debug logging.

## Packaging And Environment

The first scratch APK lacked the compiler resources and was rejected before
installation. The generated, previously audited native inputs were then copied
to the scratch source's standard native/build/android-package location. Its
owning verification script passed all four x64 native hashes, ELF/dependencies/
16 KiB alignment and resource archive hashes/header checks.

The first install failed with insufficient storage. A stopped task-owned Oracle
probe under /data/local/tmp/qfli-oracle-audit-20261002 occupied 204 MiB. Its
253 files (212377270 bytes) were completely pulled into the ignored local
mysql-android/device-probe-archive before that exact temporary directory was
removed. No ordinary application or project data was removed.

Only the isolated test package was replaced for the repaired run. After success,
it was uninstalled and the existing ordinary Rust application was foregrounded.
No native audit or standalone Oracle process remains required for this work.

## Delivery And Checks

The verified three-path patch was applied to qfli_c:

- android/app/src/main/kotlin/com/example/qflistudio/c/NativeCompilerBridge.kt
- tool/android_native_audit.dart
- .trellis/spec/backend/android-runtime.md

The new tool's owning analysis is clean. Existing Android and iOS channel
regressions passed 16/16; the iOS cases mock the channel and do not establish
Apple engine execution. The owning Kotlin diff passes git diff --check.
The patch contains no preexisting cross-platform WIP. Commit is still pending.

ARM device execution, Apple package/execution and
the separate browser implementation remain open. This is an Android backend
execution pass and a narrow bug fix, not whole-goal completion.

## Ordinary Editor Follow-up

Built the ordinary owning application from its preserved current working tree,
with the delivered pipe fix and normal lib/main.dart entry. The first direct
Gradle invocation could not run because its generated wrapper was absent.
Flutter regenerated it; that build compiled source but failed in packageDebug
without a detailed underlying cause. A serial JBR 21 build with a temporary
1 GiB heap passed (owning-build-r3.log). The prior 768 MiB package failure was
not reproduced and is not attributed to a product source defect.

The dual-ABI APK passed all eight native input/resource archive/ABI/dependency/
16 KiB checks. The original emulator-5560 rejected this ordinary APK and its
smaller x64 split APK for insufficient storage. No installed ordinary app or
project was removed to make room. A fresh task-owned Qfli_Native_Audit_20261002
AVD was created in this task's ignored build evidence, using the same installed
Google Play ps16k x64 system image, then started headlessly as emulator-5562.
Its Android SDK version is 37 and getconf PAGESIZE returns 16384.

The reviewed x64 split APK installed successfully there. Through the ordinary
GUI, created AndroidCppNative with the C++ template and opened src/main.cpp.
Clicked the normal editor Run button. Its terminal identifies Android Clang cpp,
prints Hello, QFLIStudio+!, and displays finished, exit code 0. The retained
source includes iostream/std::cout/std::endl; the ordinary Android Clang route
was used. Screenshot and fresh UI XML confirm the completed result. The
application remained alive, and its retained process log has no AndroidRuntime
fatal/InterruptedIOException entry. This is one ordinary editor workflow pass;
the earlier eight isolated cases retain their separate backend evidence.

APK: D:/MyNewProjects/qfli_c/build/app/outputs/flutter-apk/app-x86_64-debug.apk
SHA-256: adeaca855525ac70900c05e8588f9b157a1b03bcb0a3787e7a2d0239faa33b02
Source/package inputs include preserved preexisting runtime WIP. This application
execution does not authorize adding that WIP to the pending three-path fix.

Additional evidence under build/native/platform-audit/c-android-delivery:

- owning-build-r2.log (package failure), owning-build-r3.log (success),
  owning-build-x64.log (ordinary x64 split success)
- owning-apk-audit.log (both ABIs), owning-x64-apk-audit.log
- owning-editor-run.png, owning-editor-run.xml, owning-editor-logcat.log
- ordinary-emulator-stdout.log, ordinary-emulator-stderr.log

The task-owned emulator-5562 was stopped after verification. Its isolated files
and evidence remain in the workspace; the original emulator-5560 was preserved
and stays connected. A narrow spec-only checked patch records the new ordinary
editor evidence in qfli_c. Source commits and unavailable Apple/ARM checks retain
their existing pending status.
