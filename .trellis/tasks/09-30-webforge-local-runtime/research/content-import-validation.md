# Content Import Verification

Verified on 2026-10-01 in the WebForge product and sibling shared core checkout.

## Implementation Audit

- Tutorial and example catalogs use MD3 title/summary rows; detail routes own code.
- Detail imports accept a custom filename and open the imported file immediately.
- Shared core tests cover existing project identity, restored session precedence,
  overwrite confirmation, cancellation, I/O errors, edited examples and large text.
- Fixed the product integration gap: a custom HTML entry in project metadata now
  determines the default preview root and page. Explicit Web roots still win.
  Both WebForge and the native Nginx middleware carry the selected entry.

## Checks

| Check | Result |
| --- | --- |
| Product `flutter analyze --no-pub` | No issues |
| Core analysis of eight content/import/editor files | No issues |
| Product `flutter test --no-pub` | 32 passed |
| Core `flutter test --no-pub test/content_code_import_test.dart` | 36 passed |
| Android `integration_test/content_import_test.dart` | Passed in 2m 34s |

The device test ran on `emulator-5556`, Android API 37, x86_64, 16 KiB pages.
It loads actual packaged tutorials/examples, drives the real HomePage and detail
controls, checks custom files on disk and the active EditorController file, then
imports edited HTML as `src/custom_preview.html`, requests its root URL through
native Nginx and checks the edited marker. Finally it imports into an existing
project, checks identity and project count, and verifies the original entry.
Test-owned files are removed afterwards; user project registries are not used.

## Environment Findings

The shared emulator and Windows host were under memory pressure. An initial
test exposed an interaction timing problem after scrolling/focusing fields;
the test now settles layout and checks hit targets before tapping. A subsequent
install stalled during Android system-service timeouts. The final full run
passed after confirming this build's Gradle/Kotlin processes were idle and
releasing them. No app behavior was changed to accommodate these test conditions.

Core changes are mixed with other sessions' work. This product commit only owns
the preview integration, Android test dependency/test, and these specifications.
