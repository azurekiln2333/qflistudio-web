# Rust Android runtime continuation

## Current boundary

The owning Rust repository has existing uncommitted cross-platform changes.
Review and build against a copied source snapshot under
`build/native/platform-audit/rust-android/review`. Preserve the original source,
toolchains, OHOS/startup edits and unrelated metadata. Delivery and commit
ownership must be resolved before including those existing changes.

The independent tutorial/example task already exists as
`10-01-content-code-import`, completed with WebForge commit `d1ef042`.
The delayed task-creation reply does not require another task.

## Verified inputs

- Rust 1.98.1, commit `48a229ceaefd4985c50990b14116b6d856af0985`.
- Complete official compiler source archive SHA256:
  `be1816e7f6c40abb90245ad6e024bed2a7e88d7dda4561e4d5470207df616b9f`.
- Full source and Miri fingerprint verification passed after recovering an
  interrupted extraction. Complete source is separate from rustc-dev browsing
  source and the earlier sparse Miri checkout.
- Official Linux Android NDK r27, version 27.0.12077973, archive SHA256:
  `2f17eb8bcbfdc40201c0b36e9a70826fcd2524ab7a2a235e2c71186c302da1dc`.
- Official bootstrap target standard-library archive hashes, verified against
  the installed pinned channel manifest:
  - x86_64-linux-android:
    `fe51f7fd73553b197b5c4be776df681958a23ff65bc8c95dd2e176d14443a506`.
  - aarch64-linux-android:
    `d7c4949bb77b007bed188c9b15b8267a3222dc9b9c517f05d1899f9e885fb79e`.
- WSL distribution `qfli-java-build`; independent work root
  `/root/qfli-rust-android`. Original toolchain remains unchanged; bootstrap
  uses its independently copied `stage0` toolchain with both Android targets.
- Connected Android x86_64 emulator `emulator-5560`, page size 16384.

## Concrete failures and fixes in the review snapshot

1. Windows memory pressure interrupted concurrent preparation processes.
   Keep the compiler source unpublished until extraction completes; stage it
   in a temporary directory, validate it, then rename it into place. Preserve
   an existing incomplete directory with a unique name. A verified source
   marker permits later reuse. Four actual archive/recovery tests pass.
2. Compiler bootstrap built Android std but then failed with missing `core`
   while compiling cross-host compiler dependencies. Install matching official
   Android target std in the independent stage0 toolchain. Add a bootstrap
   preflight for the required target core/std inputs.
3. Scope the task's Linux processes to a memory cgroup: 2 GiB RAM, up to 4 GiB
   swap, one compiler job. No unrelated process was stopped.
4. Official rustc-dev private metadata in the copied stage0 toolchain conflicted
   with source-built metadata. Remove only installation-recorded, hash-matched
   private files from the independent toolchain and generated sysroot; preserve
   the original toolchain and target std. Bootstrap now rejects this conflict
   before compilation.
5. Full compiler CLI assembly attempted global assembly through absent LLVM.
   Build the stage1 driver only, then build the upstream Cranelift Cargo crate
   against the generated compiler-private sysroot with dual proc macros. Use
   Cargo artifact messages to locate the backend. This embedded route passed.
6. First Android source execution failed with E0514: upstream's default source
   archive build description changed the metadata version string. Use supported
   `build.description = ""`; retain exact commit/version validation. Incremental
   compiler rebuild and adapter repackaging passed. The failed device log remains
   `android-integration.log`; later successful execution is recorded separately.
7. Flutter test uses a generated `flutter_test_listener.*/listener.dart` entry,
   so integration-directory detection alone missed the test package. The first
   test tool installed then uninstalled the ordinary Rust application ID.
   Detect generated listeners, support explicit `qfliIntegrationTest=true`, and
   prebuild/audit the test APK before invoking Flutter test so its initial package
   object also uses the isolated ID. The ordinary app has since been restored.

## Verification

- Owning runner/assets/editor tests: 45 passed, 9 skipped because Rust was not
  originally on the test PATH. These are not native Android execution evidence.
- Enabling Windows Rust reached 17 passes and four failures during memory
  pressure; one compiler explicitly reported LLVM out of memory. Keep this
  failed run recorded rather than claiming a clean desktop suite.
- Independent Windows Cargo metadata check and actual program execution passed;
  output `desktop Rust smoke`, expected process exit 17. This does not establish
  that all four failures were solely environmental.
- After limiting the Linux workload's memory, the actual Windows Rust/Cargo
  runner suite passed 21/21, including all four previously failing cases and
  process-tree cancellation. Preserve the failed first log and successful
  `compiler-tests-r2.log` as separate evidence.
- Snapshot native assets/runner/desktop runner and focused tests: static analysis
  passed. New Android integration test: static analysis passed.
- Actual x64 Android driver and Cranelift backend bootstrap passed. Miri adapter
  compilation and packaging passed; three Android native libraries passed ABI,
  16 KiB LOAD and dependency checks. Guest MIR hashes match retained provenance.
- Source-archive recovery and bootstrap-preflight regression tests: 6/6 pass,
  including preservation of the standard-library metadata version identity.
- First device run: 0/5 passed due to E0514; stop case then timed out waiting for
  output. Preserve this failure independently of the next run.
- Actual ARM64 source driver, Cranelift backend and Miri adapter builds passed
  in separate output directories. Packaging verifies its own native provenance
  and the same retained guest MIR hashes. No ARM64 device execution is claimed.
- Isolated x86_64 device run after the metadata fix: 5/5 passed in
  `android-integration-r2.log`. Covers modules/generics, stdin/EOF/UTF-8,
  stdout/stderr, nonzero guest exit, real compiler diagnostics, execution/output/
  guest-memory limits, cancellation and a subsequent fresh run.
- Editor workflow: 1/1 passed in `android-editor-r4.log`; actual saved sources
  run, stop and execute freshly through the native engine.
- Eight reviewed source paths were applied to qfli_rust through
  `rust-android-r1.patch`: build_rustc_host.py, its regression tests, native
  README, Android Gradle, main.dart, device tests, native-runtime spec and
  pubspec.yaml. Owning pubspec.lock adds the corresponding test dependencies.
  Existing generic runtime WIP was preserved and remains a delivery dependency.
- Generated x64 and ARM64 native/data packages were delivered through the
  owning packaging script; all six ordinary APK runtime native files match
  package hashes and pass ABI, public dependency and 16 KiB alignment checks.
- Owning source analysis is clean; Flutter suite passed 65 with 8 skipped
  Windows embedded-Miri cases due to missing matching native library/sysroot.
- Owning ordinary dual-ABI APK built, installed and started successfully.
  Its actual AndroidRustNative editor project ran src/main.rs, printed
  `Hello, QFLIStudio+!` and exited 0. The ordinary package remains installed;
  the separate integration-test package was removed. Screenshot:
  `build/native/platform-audit/rust-android/ordinary-editor-run.png`.
- The missing-package Gradle preBuild gate fails as intended. Its temporarily
  hidden generated manifest was restored. The owning Gradle memory settings
  were preserved; successful builds used temporary process overrides with
  Android Studio JBR 21 and serial workers.
- Android runtimeStatus is available only for x64, which has device evidence.
  ARM64 is packaged but still reports unavailable pending actual execution.
- Exact proposed commit source was independently exported from HEAD plus the
  40 paths in rust-commit-plan.json. Only the verification copy's dependency
  paths were adapted to reach shared core. Its Flutter suite passed 65 with 8
  missing-input embedded skips, full analysis passed and bootstrap tests passed
  6/6. Logs are proposed-tests.log and proposed-analysis.log beside the snapshot.

## Remaining delivery and requirements

- Resolve commit ownership for the preexisting generic assets/runner, C ABI,
  packaging helpers and platform runtime integration. Review the precise
  proposed source commit independently; do not silently stage other work.
- Commit authorized Rust source and root evidence separately. Generated runtime
  inputs remain ignored/reproducible through the owning build/package scripts.
- Verify actual ARM64 execution when a matching device becomes available.
- Keep unavailable Apple build/execution and remaining platform requirements
  explicit. The overall native runtime task remains in progress.

## Logs

Windows evidence is under `build/native/platform-audit/rust-android/`.
WSL compiler logs are under `/root/qfli-rust-android/compiler-x64/`.
ARM64 logs are under `/root/qfli-rust-android/compiler-arm64/`.
