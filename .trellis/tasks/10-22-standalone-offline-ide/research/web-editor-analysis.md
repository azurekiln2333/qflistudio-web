# Web editor analysis acceptance

Captured 2026-10-22. Owned files for this acceptance slice are `test/web_editor_analysis_test.dart` and this record. Shared core and product analyzer/profile sources are read-only to this worker.

## Final result

The independent rerun after the C owner's shared-core repair passed **2/2 tests**, exit code 0:

| Viewport | Actual parser | Result |
| --- | --- | --- |
| 1280 × 900 | Native QuickJS through `WebCodeAnalyzer` | Passed |
| 390 × 844 | Native QuickJS through `WebCodeAnalyzer` | Passed |

```powershell
D:/ProgramFiles/flutter_ohos/bin/flutter.bat test --no-pub --concurrency=1 test/web_editor_analysis_test.dart *> build/content/web-editor-analysis-test.log
```

The final log ends `00:04 +2: All tests passed!`. No test changes were made to accommodate the shared-core repair. Both cases now execute every assertion: initial real clean result; unsaved CRLF/emoji syntax error at UTF-16 `[41,42)`; visible Problems count/message and `main.js:2:35` location; wavy underline only on the erroneous semicolon with the theme's error color; Problems-row navigation to exactly that token; clean Problems and absent waves after an unsaved repair; a second owner-root buffer's independent syntax error; and returning to the repaired first file without stale diagnostics. Both disk sources remain equal to their original valid content throughout, and the repaired first buffer remains dirty and unsaved. No Flutter exception remains.

## Boundary and fixture

The missing evidence was the complete product analyzer-to-editor path: the actual `WebCodeAnalyzer` must consume an unsaved JavaScript buffer through the real shared `EditorPage`, show a Problems entry and wavy decoration, navigate to its exact token, and clear both after repair. Existing service tests and shared scheduler tests do not independently establish that composition.

The new test mounts real `EditorPage` with real `AuthStore`, temporary `ProjectStore`/`SettingsStore`, and a product-derived offline test profile. It installs an actual `WebCodeAnalyzer(nativeLibraryPath: ...)`, with the path set explicitly to the existing rebuilt native parser. There is no mocked analyzer, delayed substitute, synthetic diagnostic, user-code execution, or production test hook. The installed production `webProfile.codeAnalyzer` type is checked separately by the parent suite.

The two cases use 1280 × 900 and 390 × 844. Each starts with valid, three-line JavaScript on disk, uses the public editor controller to replace it with an unsaved two-line CRLF/emoji syntax error, checks the native error's exact UTF-16 range, and uses the same public controller `buildTextSpan` API that the renderer calls to inspect the core-installed wavy decoration. It then drives the actual Problems status, list row and navigation selection; repairs the buffer; and switches to a second owner root with another unsaved error before returning to the clean first buffer. File contents are asserted unchanged throughout; autosave is disabled.

## Native identity

| Property | Value |
| --- | --- |
| Platform | Windows x64 host |
| Library | `build/native/web_syntax/windows/qfli_web_syntax.dll` |
| Bytes | 1,351,317 |
| SHA-256 | `11967d444d1cb681b813bc3836da7e4be969a6e11320c077d64757ef2a93dce2` |

This test fails when its required real native library is missing. It does not silently skip native acceptance or use the platform-name resolver instead of the explicit path.

## Initial defect and shared repair

```powershell
D:/ProgramFiles/flutter_ohos/bin/flutter.bat test --no-pub --concurrency=1 test/web_editor_analysis_test.dart
```

Initial focused execution: **0 passed, 2 failed**. Its output is preserved as `build/content/web-editor-analysis-initial-test.log`. Both viewports opened the source, finished the real initial syntax check and visibly reported `本地检查未发现问题`. Both then failed when changing the rendered three-line buffer into a two-line invalid buffer.

The first exception is a genuine shared editor repaint ordering defect:

```text
RangeError: Invalid value: Not in inclusive range 0..1: 2
CodeLines.[]
_CodeHighlighter._buildSpan
_CodeFieldRender._buildDisplayRenderParagraphs
_CodeFieldRender.forceRepaint
_CodeLineEditingControllerImpl.forceRepaint
EditorFileDiagnostics.update
EditorAnalysisController.requestAnalysis
EditorAnalysisController._synchronize
EditorController._markDirty
_CodeLineEditingControllerImpl.text=
```

The earlier `EditorFileDiagnostics.update` invoked synchronous `forceRepaint()` during the content-change notification. The controller already contained the new two-line `CodeLines`, while the renderer still traversed the former third display line. Its access to line index 2 threw before the normal render/content synchronization could complete. The subsequent `analysis.checked == false` assertion was a consequence, not the primary failure.

The minimal fix request was sent to the parent for the C/shared-core owner. The owner repaired `EditorFileDiagnostics.update` to invalidate diagnostic state immediately, coalesce one repaint after the frame's render reconciliation, request a visual update, and avoid repaint after disposal. The owner also independently passed this exact suite (`build/content/core-live-editor-repair.log`), reported 22 focused core tests passing, and published core commit `ef34591` (`feat(core): integrate offline content filters and editor diagnostics`). The independent product rerun above verifies the repaired composition. The test retains the real three-to-two-line replacement as regression coverage. No caller workaround, ignored exception, weakened fixture, or shared-core edit by this worker was introduced.

## Final source identity

| File | SHA-256 |
| --- | --- |
| `test/web_editor_analysis_test.dart` | `5b23798a4d961eaf5bd705a657718441c9b3bcd564b5df16b2185a8e7f4f866d` |
| `lib/services/web_code_analyzer.dart` | `9b5ba0a223aff5ef4cfc18e3d0e5fbdfa782828ac86c2ac65d8db515b86d1c68` |
| Core `lib/editor/editor_analysis_controller.dart` | `7b6e83e668c7eb3abe8b6b2b127bff39f52f32d5bb0c21fb0ca8f8b0113be20b` |
| Core `lib/editor/editor_diagnostics.dart` | `0627318dbeb531b3ca3f6eef60397e41e8e24ce959aeb2f0aa4ac240df0bdb2d` |
| `build/content/web-editor-analysis-test.log` | `dce4003b8a2cf4324d92b7a2b8925786575619a523919e38edfb1cad9a561947` |

## Static checks and coordination

```powershell
D:/ProgramFiles/flutter_ohos/bin/dart.bat format test/web_editor_analysis_test.dart
D:/ProgramFiles/flutter_ohos/bin/dart.bat analyze test/web_editor_analysis_test.dart
```

Formatting completed and focused analysis reports **No issues found**. The suite uses `OpenFile` and public core widget/controller APIs, so it adds no direct undeclared dependency on the core's vendored `re_editor` package.

The parent reported the existing product full 165-test suite and 19 analyzer tests passing; this worker did not rerun them. The parent explicitly handed over the exclusive focused Flutter slot after the shared repair and another worker's five catalog tests. This worker ran only the two acceptance cases, then explicitly released the slot again. No pub, native build, platform build or Hvigor command was run for this slice.

These are host acceptance checks. They do not establish OHOS parser loading or target editor behavior; that remains part of the independent current-HAP device gate.
