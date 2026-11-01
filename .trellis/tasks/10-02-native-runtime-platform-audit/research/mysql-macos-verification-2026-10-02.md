# macOS Oracle Helper Integration

## Delivery

The clean portable MySQL runtime had no macOS application build/package/signing
step. A 15-path patch now integrates that source chain into qfli_sql. Committed
HEAD 497f969 was exported to the isolated mysql-macos/review source snapshot.
Each owning path was clean or absent before delivery; a narrowly generated patch
passed git apply --check before the permission-reviewed owning application.
All 15 delivered files match their reviewed counterparts after CRLF normalization.
Existing selector/cloud, OHOS, agent and generated-plugin work is preserved.

The Xcode Runner phase invokes native/mysql/macos/bundle.py. It builds the native
bridge/parent launcher against complete Oracle 8.4.6 SDKs per requested ABI.
Helpers contain native executables, libraries, plugins, resources and licenses.
CMake BundleUtilities resolves SDK dependencies; native headers validate CPU,
macOS platform and minimum deployment OS. Inputs are thinned, library references
become loader-relative, remaining native RPATHs are removed and the internal
dependency closure is validated. Dylibs/plugins, executables and helper apps are
signed before Runner. Outer Resources stores final signed helper hashes.

Helpers inherit the parent sandbox. Runner owns network client/server permissions
for its private Unix socket. ABI discovery covers native ARM64 and x64/Rosetta;
the explicit QFLI_MYSQL_BUNDLE override retains the flat desktop layout. Injected
pluginDirectory is used for initialization and normal start. Existing Windows,
Linux and Android paths and writable data are preserved.

Patch: research/mysql-macos-delivery.patch
SHA-256: 38094a730e2137d723f785ccd0057942997cd56f187a60780f611697163d84fe
Commit plan: research/mysql-macos-commit-plan.json
The source is applied but uncommitted. One independent macOS commit confirmation
was requested under .trellis/workflow.md; prior Rust/SQL ownership requests were
not repeated.

## Available Verification

- Twelve portable validator regressions passed in both reviewed and owning
  source: legacy/current Mach-O headers, architecture selection, minimum OS,
  iOS/corrupt-input rejection, loader-relative executable/plugin/FFI dependencies,
  external-path rejection and native-code dependency validation. Synthetic input
  headers are validator fixtures, not Apple engine execution.
- Eleven actual Windows Oracle lifecycle checks passed using the previously
  built owning Oracle 8.4.6 bundle. The new explicit pluginDirectory input was
  injected for both initialization and normal execution. Cases cover private
  transport, ownership, prepared exact values, diagnostics, transactions/caps,
  credentials, stop/restart, version mismatch, parent death and InnoDB recovery.
  No Windows native source changed, so the existing delivered native binaries
  were used. The isolated retained fixture is
  D:/AppData/Local/Temp/qfli-mysql-test-1e144f99.
- All 51 owning Flutter tests passed with the actual Windows Oracle bundle and
  retained SQLite DLL; there were no skips. The first reviewed suite passed 45
  and skipped six SQLite cases for its absent default DLL. Pointing at the owning
  native SQLite input then passed all seven SQLite tests, including the repeated
  missing-library negative case. The final owning run used both actual engines.
- Changed Dart files in both source trees analyzed with no issues. Owning git
  diff --check passed. Test-only absolute dependency overrides were excluded from
  the delivery. The normal Android emulator remains connected; no Android
  application/project data was changed by this slice.

Logs under build/native/platform-audit/mysql-macos:

- packaging-validator.log
- windows-lifecycle.log
- source-analysis.log
- flutter-tests.log (initial reviewed run)
- sqlite-regression.log
- owning-flutter-tests.log (51/51, no skips)

## Unavailable Verification And Remaining Work

No macOS host, Xcode, Apple device or verified Oracle macOS SDK exists here.
Native Apple build, code-signature verification, actual Oracle server execution
and sandboxed application-death behavior were therefore not run. Portable tests
and Windows lifecycle success do not establish those Apple outcomes.

Before an Apple build, provide verified complete Oracle SDKs for every requested
architecture and the pinned Oracle source headers. The app's currently declared
10.15 deployment target must meet each SDK native minimum; the packager rejects
newer requirements without silently changing the application target. Full
package, signature, CRUD/persistence/stop and parent-death checks must run on the
actual packaged sandboxed application. Native iOS Oracle hosting and the other
recorded Apple compiler/runtime gaps remain unresolved. The overall goal stays
active and is not a complete-platform pass.
