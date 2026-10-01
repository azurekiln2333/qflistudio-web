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
- The existing new Java x86_64 image's launcher and JVM have 0x4000 LOAD
  alignment. The image's complete dependencies, staged package and real app
  execution still need verification; its owning changes are uncommitted.
- Two subsequent read-only WSL inspections of that Java image failed at
  automatic approval review with HTTP 503. Neither inspection executed. The
  service reported no available channel for codex-auto-review. Preserve the
  earlier Linux passes and keep Java staging/execution pending; the user was
  asked to repair the review service or manually export the existing image.

The audit remains in progress. Dart mobile, Rust target builds, Java/Web iOS,
local Oracle MySQL outside OHOS, outstanding language delivery and unavailable
target validation must not be reported as complete.
