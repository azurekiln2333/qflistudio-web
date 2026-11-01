# Web real-surface acceptance defects for the sole core integrator

## Current status (October 23)

The R4 precedence and R6 repaint defects below were repaired in coreef345913;
actual Web catalog5/5 and QuickJS EditorPage2/2 verified the composition. Their
original observations are preserved below.

A new R7/default-preview regression appeared in core0ec321c: the full Web
rerun has171pass/1fail at `web_preview_current_file_test.dart:304` (ordinary tap
no longer reads the preview session default URL). It is also a real explicit-root
failure: a project-root `index.html` must not override `.qfli/web.json` root
`public`, whose normal URL serves `public/index.html`. Calling
`urlForFile(project/index.html)` instead rejects a file outside the document
root. Long press should resolve the actual active file; ordinary tap should use
the owner-root session's configured default URL. C received exact evidence in
global162 and published the correction as core
`e025805b60435fdedafd33e60082dc660afebe5a`
(`fix(preview): retain the session document root on project run`). The repair
keeps the active owning project while ordinary tap uses `session.url`; only
long press resolves the selected file.

The owner-provided actual focused run in
`build/content/core-owner-preview-recheck.log` ends **9 passed, all tests
passed**. It includes the real HTTP root/file cases, default-tap/current-file
long-press behavior and cleanup when resolution fails. This closes the
specific focused preview regression. A fresh complete Web suite on the
current integrated worktree is still pending; the earlier171pass/1fail result
remains historical failure evidence. Web did not edit common core or weaken
its test.

## R4 subject vs executable type

`qfli_studio_core/lib/pages/local_content_pages.dart:435` currently uses:

```dart
_contentLanguage(String type, String language) =>
    languageKey(type.trim().isEmpty ? language : type);
```

All Web entries import as `type: html`, but their subject `language` is
html/css/javascript. Prioritizing executable type collapses every one of the
481 subjects into HTML and breaks chips and title badges. Prefer nonempty
subject language, with executable type only as the legacy empty-language
fallback. Real product asset/UI test is being added in
`qfli_web/test/web_catalog_language_test.dart`; do not patch the consumer assets
to use non-executable CSS/JS import formats.

## R6 reentrant diagnostic repaint while editor line count changes

The real `EditorPage` test with actual QuickJS DLL reproduces at two widths:
start with three valid JS lines ending in CRLF, replace unsaved controller text
with two invalid JS lines. The dirty listener synchronizes analysis immediately
and forces decoration repaint before re_editor's old rendered line indices have
been replaced. `_CodeHighlighter._buildSpan` asks new CodeLines for index2,
whose current valid indices are0..1, causing RangeError.

Observed call chain:

```text
EditorController._markDirty -> EditorAnalysisController._synchronize
-> requestAnalysis -> EditorFileDiagnostics.update
-> editor_diagnostics.dart:38 forceRepaint
-> re_editor/_code_field.dart:722
-> re_editor/_code_highlight.dart:78 CodeLines[2]
```

Reproducer: `qfli_web/test/web_editor_analysis_test.dart`; log
`qfli_web/build/content/web-editor-analysis-test.log`. The analyzer is genuine,
not mocked. Product checker made no core edits. Please fix reentrant repaint at
the owning layer while retaining stale-result/dirty-buffer behavior, and publish
the handoff so focused Web acceptance can rerun.

The Web Flutter command slot is now free for the owning core investigation.
