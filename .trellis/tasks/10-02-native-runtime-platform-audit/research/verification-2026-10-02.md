# Native Verification, 2026-10-02

## Delivered Commits

- qfli_web c7614f8: Linux/macOS Nginx build, packaging and discovery (earlier).
- qfli_dart 138affc: official desktop SDK and Kernel compiler (earlier).
- qfli_sql 7269c12: native SQLite mobile/desktop/Apple FFI integration.
- qfli_python e4d0e40: native desktop/Apple FFI integration and Windows port.

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
- A subsequent read-only WSL inspection of that Java image again failed at
  automatic approval review with HTTP 503. The inspection did not execute.
  Preserve the earlier Linux passes and keep Java staging/execution pending.

The audit remains in progress. Dart mobile, Rust target builds, Java/Web iOS,
local Oracle MySQL outside OHOS, outstanding language delivery and unavailable
target validation must not be reported as complete.
