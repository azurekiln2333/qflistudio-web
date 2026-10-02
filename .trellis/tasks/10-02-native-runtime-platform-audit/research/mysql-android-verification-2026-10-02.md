# Android Oracle Delivery Verification

## Delivered Source

SQL repository commit `497f969` adds 19 runtime/build/contract files. Oracle
8.4.6 and OpenSSL 3.5.3 use the pinned archive hashes in its Android README.
Independent WSL source/build trees preserve OHOS work. Both x86_64 and ARM64
servers, bridges and launchers built successfully with NDK27/Bionic.

The local engine selector and integration test were applied to the owning SQL
working tree. They remain uncommitted because they extend preexisting cloud
SQL files and rely on API methods in the shared core's working changes. The
user was asked to choose their commit ownership. This runtime commit does not
claim that a clean committed checkout includes those selector changes.

## Device Evidence

`emulator-5560`, PyFlow_Import_Test, API 37, x86_64, actual page size 16384.
The two cases in integration_test/mysql_native_test.dart passed:

- Actual Oracle version/private transport, workspace CRUD, exact BIGINT,
  NULL/binary/prepared values, ICU Unicode regex, rollback/partial scripts,
  invalid credential rejection, persistent restart and preferred editor runs.
- Actual SQLite/Oracle workbench switching, persisted setting, cell edits,
  old-data clearing and disappearance of the Oracle process when switching.

The ordinary APK was then built from qfli_sql, installed and launched. The
workbench selected local MySQL and SELECT VERSION() returned 8.4.6. A 540x1212
screenshot showed no overlapping text or controls. Device evidence is under
build/native/platform-audit/mysql-android; no ARM or Apple execution is claimed.

## Native And Source Gates

- Both ABI staging audits passed all four native files and 76 resource files
  each: matching ELF64, Android PIE interpreter, 16 KiB LOAD congruence and
  public/packaged dependencies.
- The owning x86_64 APK's six native files passed the same ELF gates. All four
  Oracle native inputs match the resource manifest hashes. No 32-bit native
  payload is advertised by this product APK.
- Owning serial Flutter suite: 51/51 passed, including real Windows Oracle.
- All seven changed Dart source/test files: no analysis issues. Full lib
  analysis previously had one unrelated info in sql_document_service.dart.
- Owning ordinary APK SHA256:
  841d5d1583c2e02932f7514d9b0867a88c286892320abc87161372f3155ba90b.

## Failures Resolved And Limits

The server needed Android liblog for Abseil's log sink. Its final link now
uses Oracle's existing plain CMake signature. The client needed compiler-rt,
emulated TLS and hidden static unwind to load on the target ABI.

The first application run exposed intermittent EINTR during initial Oracle
handshake. Android connections now set upstream MYSQL_OPT_RETRY_COUNT before
connecting. Only interrupted transport operations retry; SQL is never replayed.
Both application cases passed after this change.

Flutter's default Gradle build-type ABI filters overrode defaultConfig. Explicit
requested-ABI filters now apply at both levels. Preserve packaged libc++ symbols
so the final input identity remains equal to the audited export.

Windows committed memory blocked Gradle at first (errno 1455). Gracefully
restarting only the selected test emulator with 2 GiB instead of 3 GiB and using
temporary smaller serial Gradle settings allowed builds. The owning repository's
gradle.properties was preserved; its build used environment overrides.

The first Flutter integration-test invocation used the ordinary application ID.
The tool uninstalled that package and removed its local data when it exited.
Subsequent integration targets use a separate .integrationtest application ID.
The ordinary app was reinstalled, but recovery of the former package's local
data is not established. Emulator restart itself preserved the AVD disk.

An earlier standalone shell probe established Android version loading and
initialization only. Shell-domain Unix socket binding was denied; it is not
counted as an application pass. No temporary standalone server was left running.

macOS bundle/signing, native iOS hosting, ARM execution and the remaining
cross-product native gaps are still open. The overall goal remains active.
