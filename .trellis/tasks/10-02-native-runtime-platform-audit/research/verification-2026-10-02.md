# Native Verification, 2026-10-02

## Delivered Commits

- qfli_web c7614f8: Linux/macOS Nginx build, packaging and discovery (earlier).
- qfli_dart 138affc: official desktop SDK and Kernel compiler (earlier).
- qfli_sql 7269c12: native SQLite mobile/desktop/Apple FFI integration.
- qfli_python e4d0e40: native desktop/Apple FFI integration and Windows port.
- qfli_lua 31e0107: native Apple integration, Windows UTF-8 filenames, Android
  16 KiB build settings and application source/bytecode verification.
- qfli_go 68f91a5: native iOS archive/FFI integration and common platform routing.

All changes were committed separately in their owning repositories. Existing
cloud SQL, OHOS agreement/startup and agent metadata changes were preserved.
For SQL, runner staging selected the native platform default against HEAD;
the separate PreferredSqlEngine cloud changes remained in the working tree.

## SQL

The actual Windows C build succeeded. The owning-repository tests passed 48/48.
The staged source was independently exported; only test dependency paths were
changed to reach the adjacent shared core. Its native C build, 48/48 Flutter
tests and core static analysis passed. Full analysis retains four pre-existing
informational lints.

Both the actual repository and the independently staged source passed all seven
Android cases on emulator-5560, API 37, x86_64, actual 16 KiB pages. Six exercise
the real FFI engine; the seventh opens the default workbench and edits a cell,
checks the saved database, executes SQL, saves a query and reopens its library.
Compact SQL navigation is located by tooltip, because labels disappear below
480 logical pixels. No repository is injected into that page gate.

The ordinary `lib/main.dart` debug APK was subsequently reinstalled successfully
and launched at `com.azurekiln.qfli.sqlab/.MainActivity`. Its running process was
confirmed (PID 9021), with no AndroidRuntime crash output. This restores the
normal workbench after the integration-test target; the earlier seven cases
remain the functional application evidence.

All SQLite LOAD segments in arm64-v8a, armeabi-v7a and x86_64 APK libraries had
0x4000 alignment. That inspection is not an ARM runtime pass.

The committed runtime was built on Linux with GCC 13. Its linked C harness
passed 5/5: nullable output, transactional scripts, real SQL errors, truncation
as failure and prepared values with embedded NUL/SQL NULL.

## Python

Windows initially failed to link mp_lexer_new_from_file. POSIX/VFS readers had
been disabled, so the upstream lexer omitted this adapter. The custom Windows
reader now supplies it using the actual upstream mp_lexer_new.

The repaired Windows DLL passed 34/34 standalone Dart FFI cases, including
Unicode paths/imports, finite input, stderr, real file I/O, syntax/runtime
errors, exit codes, truncation, state reset and eight concurrent invocations.
The Linux desktop SO passed the existing 65/65 native C cases when the host
test executable linked this SO. The two tracked port-header hashes match.

All 43 preceding Flutter tests passed. A new default-runner test then passed
against the actual DLL, proving project imports, input.txt, stdout/stderr,
compile-only without side effects and persisted native file output.
The staged source subsequently passed all 44 tests and full static analysis.
Its deliverable dependency paths remain relative. The fresh Android x86_64
APK built and installed successfully. Launching the ordinary app at
`com.azurekiln.qfli.pyflow/.MainActivity` loaded MicroPython 1.24.1 (ecfdd5d) and
passed all 36 application-native self-check cases in process 8554. These include
compilation/execution, fresh interpreter state, syntax/runtime errors, stdin and
EOF, shared text/binary input cursor, stderr, exit codes, real upstream math,
sibling/package imports, persistent text/binary files, project-path protection,
compile-only without side effects, Unicode paths/output and garbage collection.

```text
I/QfliPyNative( 8554): Loaded MicroPython 1.24.1 (ecfdd5d)
I/QfliPyNative( 8554): PASS sibling-import
I/QfliPyNative( 8554): PASS package-import
I/QfliPyNative( 8554): PASS text-file
I/QfliPyNative( 8554): PASS binary-file
I/QfliPyNative( 8554): PASS compile-only
I/QfliPyNative( 8554): PASS gc-roots
I/QfliPyNative( 8554): Native self-check passed 36/36
```

Read the result with `adb -s emulator-5560 logcat -d -v brief -s QfliPyNative
AndroidRuntime`. The native self-check covers the installed engine/JNI bridge;
it is separate from the Windows default-runner Flutter test.

The current Python API has no cancellation hook or reusable bytecode output.
These are unresolved requirements, not verified capabilities.

## Lua

The owning task's existing source review and real Windows checks were inspected:
native CTest passed 1/1, all 44 Flutter tests and full analysis passed, and the
standalone AOT CLI loaded its adjacent DLL to check, compile and run bytecode.
Apple wiring compiles the shared bridge and all 32 Lua library C files in Runner;
there is still no Apple build/runtime evidence on this Windows host.

The existing release APK (69,981,813 bytes) was installed on emulator-5560 and
launched through its ordinary `com.azurekiln.qfli.script/.MainActivity` entry.
An isolated `LuaNativeAudit` project was created in the real UI. Its default
`src/main.lua` printed `Hello, QFLIStudio+!` and exited 0. The editor's native
syntax check passed and its compile action generated `src/main.luac`. The source
was then replaced with `dofile[[src/main.luac]]`; a subsequent run loaded the
retained bytecode and printed the same output, exit 0. A probe target was not
installed. Screenshots are under `build/native/platform-audit/lua-android-*`.

The platform implementation and owning validation task were committed in Lua.
Startup/content/OHOS changes remain outside that native-platform commit. Linux
application/native Lua execution and Android ARM execution remain unverified.

## Go

The owning task and chat's prior evidence were inspected: 38 working-tree
application tests, clean analysis, three real Android FFI cases, Windows SDK
operations/cancellation, and Linux SDK/native-source tests passed. Apple archive
build/link configuration has source evidence only; there is no Apple execution.

Delivery selected the runtime imports/profile metadata in `lib/main.dart`
against HEAD, leaving the separate startup changes in the working tree. The
actual index was exported into the ignored `go-staged` directory. Only that
verification copy used absolute shared-core paths; the product's dependency
paths remain relative. All 18 tests in this delivered source and full analysis
passed with the actual official Go SDK enabled, including SDK operations and
cancellation. The 38-test working-tree pass includes other undelivered features
and is not the staged-source count.

Initial verification attempts encountered Dart/Go compiler memory-allocation
failures. The successful retry limited this verification process to Flutter
`--concurrency 1`, `GOMAXPROCS=2`, and `GOFLAGS=-p=1`; product settings were not
changed. The native iOS/routing changes and their evidence were committed in Go.

## Linux Nginx

The retained upstream source hash was checked by build_nginx_desktop.sh.
The native Linux executable reported nginx/1.31.6, passed configuration
validation, and passed static HTTP, native HTTP proxy, 404 and listener-stop
checks. Reproducible test inputs are nginx-linux-smoke.sh/conf/marker.txt.
The expected missing-file log corresponds to the 404 assertion.

This does not prove Linux Flutter packaging, private Dart middleware, SSE or
WebSocket integration. Windows/Android retain their separately recorded app
integration evidence.

## Python Controlled Runs And Artifacts

Implemented upstream MicroPython per-run cancellation and bytecode persistence
in a new reviewed snapshot, build/native/platform-audit/python-lifecycle. FFI
and Android JNI both return a run handle before execution finishes. Atomic
tokens remain alive through queued work and worker cleanup; loop/sleep stops
preserve earlier output, return 130, and do not interrupt other runs.

Windows DLL built successfully. Real FFI regression passed 34/34. Full Flutter
suite passed 57/57, including native loop/sleep/pre-start/queued stop, recovery,
entry/import .mpy reload without source, invalid artifacts and project path
checks; mobile/desktop widget compile/stop workflows also passed. Source analysis
of lib/test/tool passed. A preceding full-directory analysis hit host commit
memory exhaustion; it produced no source verdict and was replaced by the source
analysis run with a 256 MiB parent VM budget. Product settings were not changed.

The reviewed 23-file patch was applied to qfli_python and committed as 2f5ed81,
feat(python): add native cancellation and reusable bytecode artifacts. The owning
repository rebuilt its Windows DLL and independently passed all 57 tests and
source analysis. Startup, OHOS, agent metadata and pre-existing untracked desktop
README changes were not included. Test-only absolute dependency paths stayed in
the snapshot; historical patch files remain untracked research.

The ordinary x86_64 debug APK was installed on emulator-5560. PID 19804 logged
MicroPython 1.24.1 (ecfdd5d), all 46 JNI cases and 46/46 completion. An isolated
UI project, PythonLifecycleAudit, stopped a real loop and retained native-before
plus KeyboardInterrupt, exit 130. The tools page compiled main.py to main.mpy;
after main.py was renamed to main.py.audit-source, main.mpy executed with
compiled-native 42, artifact-stderr and exit 0. Existing AndroidImportDemo was
preserved. Screenshots live under build/native/platform-audit/python-android-*.

The final release APK (PID 32507) was also installed and passed real UI
compilation, loop stop and source-free main.mpy execution after shrinking.
No AndroidRuntime errors were recorded. Its native LOAD alignment is 0x4000;
debug/release APKs passed zipalign -c -P 16 4. Native dependencies are libm.so,
libdl.so and libc.so. Release APK SHA256:
51EEA2F6D3805F960E1484C2F32DF5901D015D0B560F88A0E97EE37C387281D2,
26,971,354 bytes. Debug APK SHA256:
F9638F457A9B91FC1672B58486BCA12C5AAB2094BFF251FEBCA4248375E9803E,
68,968,589 bytes. This is the pre-release debug snapshot, not the final release.

Apple source/link integration includes the new exports; execution is skipped
without Apple hardware/Xcode. No Android ARM devices or MSVC GUI tools exist.
The earlier 65-case Linux result is not new lifecycle evidence; re-execution of
this slice awaits WSL approval-service recovery. OHOS retains the old channel
capabilities and C ABI; new artifact/stop operations are not advertised there.

## Android Java Delivery

Delivered qfli_java ea7b4df, fix(java): support x86_64 and 16 KiB Android JDKs.
The existing full OpenJDK 17.0.20 image was exported from qfli-java-build, not
replaced with an evaluator or rebuilt from scratch. Structured LLVM inspection
found 46 relevant ELF files. The launcher/JVM were aligned, but the pinned 2021
libandroid-spawn.so package had 4 KiB LOAD alignment. Staging correctly failed.

GitHub direct downloads timed out. The same fixed Termux commit's unmodified
spawn source/header/license were obtained through its public CDN, retained in
the owning repository with SHA-256 provenance, and rebuilt by the original
Android Clang wrapper. All 46 image files then passed x86_64, 16 KiB alignment,
offset/address congruence and DT_NEEDED dependency closure. Staging now checks
all Android launchers, helpers and libraries. The build recipe supports both
ABIs and packages the spawn BSD license with upstream JDK legal notices.

Android installation selects its data ABI from the actual packaged ELF header.
DataInputStream.readFully retains minSdk 28 API compatibility. The owning local
Mobile JDK spec was updated; this repository intentionally ignores its specs.
The committed native README files retain the delivery contract and evidence.

The review snapshot passed 19/19 Windows Flutter tests, including real host-JDK
compilation, stdin, UTF-8, errors and exit codes. Source analysis of lib/test/tools
passed. Bash syntax checks of the owning build/wrapper passed. The Android smoke
APK passed all eight application-native checks on emulator-5560, API 37, 16 KiB
pages. PID 29972 emitted QFLI_JDK_SMOKE ok:true with java-version, javac-version,
multiple-sources, stdin, utf8, compiler-diagnostics, exit-code and cancel.

The normal app was restored, built again in qfli_java and installed. The editor
created JavaNativeAudit and ran its real Main.java through javac/JVM; output was
Hello, QFLIStudio+!, exit 0. The final owning APK's 46 native files all pass 16 KiB
ELF checks, and zipalign -c -P 16 4 passed. SHA-256:
BBB63C656BB2D3903331EC698E6481B54AB5938A01A2E64655FF05186EF9929E,
180,699,601 bytes. It includes both staged data ZIPs but only x86_64 native code.
Ignored evidence is under build/native/platform-audit/java-android: elf-audit.json,
apk-elf-audit.json, android-smoke.log, normal-ui.xml and normal-run.png.

An initial Android build hit host memory exhaustion; a smaller test-only Gradle
heap then exhausted metaspace. The next incremental build succeeded. The owning
build passed with per-command memory limits; its Gradle properties were preserved.
Unrelated startup/OHOS/metadata changes were excluded from ea7b4df. No Apple or
Android ARM/API 28 execution was run. The cached old ARM image must be rebuilt
with the new recipe before claiming its 16 KiB compatibility.

## Environment and Pending Gates

- The emulator's previous 2 GiB configuration exhausted memory. It was
  restarted with 3 GiB and existing disk data; about 1.9 GiB was initially free.
- Apple hardware/Xcode, Android ARM devices and Visual Studio C++ tools are
  absent. Apple runtime, ARM runtime and full Windows GUI builds were skipped.
- WSL is available again and was used for real Linux native execution.
- Restoring the normal SQL APK initially returned automatic approval review
  HTTP 503 twice. Those installation actions did not execute. Subsequent
  approved updates installed both ordinary APKs successfully; SQL was launched
  and Python's fresh native self-check passed 36/36.
- The optional Python formatter also hit the same review-service failure.
  Compiled tests, full analysis and staged whitespace checks passed.
- The new Java x86_64 image and owning ordinary APK passed complete native
  alignment/dependency and real application checks; ea7b4df delivers the fix.
- Two subsequent read-only WSL inspections of that Java image failed at
  automatic approval review with HTTP 503. Neither inspection executed. The
  service reported no available channel for codex-auto-review. Preserve the
  earlier Linux passes. Subsequent WSL inspection/export and native compilation
  recovered, so manual image export and review-service repair are no longer
  prerequisites for the Java slice.

The audit remains in progress. Native Dart iOS, Rust target builds, Java/Web iOS,
local Oracle MySQL outside OHOS, outstanding language delivery and unavailable
target validation must not be reported as complete.

## Android Dart Delivery

Delivered qfli_dart 1765860, feat(dart): integrate native Android SDK and kernel
execution. The complete real upstream Dart 3.13.5 Android SDK is pinned to
Termux recipe d0f94da1e578a0c9550a84d408bc8ed0003882ec, source hash
2da077bf89f3a14ae5a741728549371d87013265df49b8cace6475bd9ffc59e3.
Both package sizes/SHA-256 values matched the lock. The Linux preparation
script independently downloaded, verified, extracted and dereferenced the ARM64
image. Its absolute vm_platform_strong.dill alias is repaired during export.

Both SDK images passed full staging: 15 native files per ABI, 1,025 x86_64 data
files and 1,024 ARM64 data files. Every native ELF passed architecture and
16 KiB LOAD checks. All 30 use only libc.so, libm.so, libdl.so and liblog.so.
Native code, including every AOT snapshot, is installed through extracted
jniLibs. Data/library paths and content markers are provisioned in files/dart-sdk
on a Kotlin executor and connected to installed native code by symlinks.

Android uses upstream dartvm for source/.dill execution and Kernel compilation,
with no evaluator fallback. Native run feeds input.txt and EOF, preserves streams
and native exits, and kills its owned process on Stop. Tools can execute their
saved .dill without saving/recreating its source. Public runner dispatch and
the tools compiled-run button have real source-free coverage.

The review snapshot and owning repository each passed 34/34 Flutter tests and
source analysis. The application smoke emitted QFLI_DART_ANDROID_SMOKE ok:true,
PID 15143: native-version, self-package-import, stdin, async-file-io, utf8,
source-free-kernel, compiler-diagnostics, exit-code and cancel (9/9). Device:
emulator-5560, API 37, x86_64, actual 16,384-byte pages.

The ordinary application created DartNativeAudit. Its editor ran main.dart with
Hello, QFLIStudio+!, exit 0. The tools page compiled build/src/main.dill and ran
it with exit 0 after moving main.dart to main.dart.audit-source; no new source
file was created. Tools ran a real loop, displayed native-loop-started, and Stop
returned 130. The original audit source was restored afterwards.

The final ordinary APK was built in qfli_dart, and all 30 packaged SDK ELF hashes
match the audited staged inputs. zipalign -c -P 16 4 passed. APK SHA-256:
0C594E3EB5FEBDCFB3B25D0C048828225B0B250046882B9AE0E5B5289917D2F8,
425,181,855 bytes. The update initially exhausted Android installation space;
package-manager uninstall -k preserved data/cache before reinstalling the same
signature. The final owning APK retained DartNativeAudit and its editor again
produced the actual greeting and exit 0. No AndroidRuntime crash was observed.

Host allocation failures interrupted the initial test/analysis/build attempts.
Releasing only this task's idle Gradle/Kotlin and dedicated WSL processes,
serial verification and per-command build memory limits resolved them. The local
default NDK 28.2 image is incomplete; qfliDartNdkVersion selected the installed
27.0.12077973. A compile failure from unavailable Os.unlink was corrected to
public Os.remove. The build gate was checked to reject a 32-bit target mixed
with x86_64. Snapshot-only Gradle memory and absolute dependency paths were
excluded from the delivery patch. Existing OHOS and agent changes remain dirty.

Committed Android/native docs and the existing tracked backend specs retain the
contracts. The ignored local frontend spec was updated without adding it to the
commit. Evidence lives under build/native/platform-audit/dart-android:
android-smoke.log, elf-audit.json, apk-elf-audit.json, editor-run.png,
tools-artifact.png, tools-stop.png and owning-editor-run.png.

Android ARM runtime, Apple execution and full Windows GUI builds were not run:
the devices/Xcode/MSVC toolchains are absent. Native iOS Dart remains a real
implementation gap; this Android delivery does not complete the overall audit.
