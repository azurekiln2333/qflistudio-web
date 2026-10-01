# Native Runtime Platform Audit

## Boundary

Preserve the full user objective across C/C++, Lua, Python, Dart, Java, Go,
Rust, SQL and WebForge. Each runtime needs both a real engine and the platform
build, package, load and execution path. Existing task metadata is not proof
of implementation or of successful execution.

## Current Evidence

Other products have independent active conversations and dirty worktrees.
Inspect the files and verify each proposed patch against its original files
before applying it. Never overwrite unrelated changes or infer completion from
the existence of another task. The native Dart desktop files were clean when
the source snapshot was taken; its OHOS files have unrelated user changes.

Dart desktop support was delivered in qfli_dart commit 138affc. It uses the
official SDK's C++ VM, preserves stdout/stderr and program exit codes, supports
stop, and produces reusable Kernel .dill artifacts. Compiler front-end code in
the official SDK is itself written in Dart; this does not make the VM a Dart
interpreter. EVC remains a separate existing portable backend until a native
mobile port is implemented. Do not claim native mobile Dart support.

## Delivery

Review and test the Dart patch in a snapshot under
build/native/platform-audit/dart-review. That snapshot is generated evidence,
not the delivered Dart product. Export a narrowly scoped patch, check it against
the real repository, then apply with the required sibling-directory permission
and commit in qfli_dart. Test-only absolute dependency paths must not enter the
patch. Keep cross-product evidence in this task and engine contracts in the
owning repositories.

Windows and Linux bundle the full SDK through CMake so snapshots, platform
libraries and licenses remain next to the VM. macOS bundles separate arm64/x64
SDK trees, selects the current ABI, and signs Mach-O inputs with sandbox
inheritance and the VM's JIT entitlement. Missing target SDKs fail packaging.
Apple execution remains unverified without an Apple host.

## Python Run Lifecycle And Artifacts

Add a per-invocation opaque cancellation token, retaining the existing tokenless
C ABI for OHOS. Only the worker reads VM state; cancellation threads atomically
set a token flag. Check it before execution, in upstream VM hooks, and during
bounded sleep intervals. Keep the token alive through queued and executing work,
release it after the worker completes, and make late cancellation harmless.
The runner must return its streams, exit future and cancel callback before the
native worker finishes. Android retains Kotlin/JNI routing and registers each
token before submitting execution; the channel exposes prepareRun and cancel.

Use upstream persistent-code save/load for bytecode-only .mpy artifacts. Compile
without executing, save through the existing project file path contract, and
support running .mpy entry files with source/input/path/exit/error behavior intact.
No custom bytecode format or runtime substitute is allowed. Synchronize port
configuration and generated headers; retain the new FFI symbols on Apple.
Verify real Windows native execution and Android JNI plus normal app workflow.
Apple execution is explicitly unavailable on this host.

## SQLite Platform Integration

SQL's current primary local engine is SQLite. Its retained upstream amalgamation
and existing script bridge are implemented only through the OHOS channel. Add a
local FFI plugin under native for Android, Windows, Linux, iOS and macOS. Compile
the same retained source, including the existing script bridge, for each target.
Use prepared SQLite statements for structured grid queries with matching NULL,
parameter, single-statement, row-limit and output-limit behavior. Run blocking
native calls on an isolate. Explicit injected channels retain their behavior.

This slice changes SQL native packaging, the SQLite invocation boundary, tests
and its engine contract. Cloud MySQL and the existing OHOS bridge retain their
ownership. Local native Oracle MySQL outside OHOS remains an unresolved gap.

## Android Java Delivery

Use the existing OpenJDK 17 Android x86_64 image built in qfli-java-build.
Export a dereferenced image into this task's ignored build evidence and audit
every packaged ELF's ABI, 16 KiB LOAD alignment and required shared libraries.
Stage the full upstream modules and native JVM with the owning stage.ps1;
Android executes launchers in nativeLibraryDir and installs data in files/usr.
The layout manifest joins these two locations through library symlinks.

The behavior gap is the earlier failed 16 KiB emulator launch. Delivery owns
the Android build recipe, dependency lock, staging validation, ABI selection,
runtime documentation and device evidence. Preserve unrelated startup/OHOS
changes. Verify version probes, multiple sources, stdin, UTF-8, diagnostics,
exit status and cancellation inside the application, then restore its normal
entry point. Android ARM and Apple execution remain unavailable here.
