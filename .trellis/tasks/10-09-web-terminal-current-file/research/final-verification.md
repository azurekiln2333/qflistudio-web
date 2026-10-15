# Final verification

## Outcome and ownership

The user's right-hand pi worker (Herdr pi-web-terminal, wD:p2) completed the Web
integration and regression tests under Codex supervision. The Java workspace
owns the shared continuous terminal/Run gestures. Both products consume the same
qfli_studio_core working tree.

Codex reviewed and applied research/core-web-preview-file.patch through the
approved sibling-directory filesystem operation. WebDevServer and NginxSession
implement the optional WebFilePreviewSession capability. A regular tap keeps the
default session URL; long press resolves the active HTML using the actual root
and public listener. Browser/copy actions use that same target. Invalid targets
do not silently open the default page, and startup/attachment failures stop the
new session.

## Delivered source delta

- qfli_web/lib/services/web_dev_server.dart: per-file preview capability.
- qfli_web/lib/services/nginx_session.dart: public-port per-file preview capability.
- qfli_web/test/web_preview_current_file_test.dart: 9 regression cases.
- qfli_studio_core/lib/services/web_preview_file.dart: optional capability and
  shared canonical path/URI resolver.
- qfli_studio_core/lib/services/local_web_server.dart: legacy server capability.
- qfli_studio_core/lib/editor/editor_page.dart: HTML target selection and cleanup.
- qfli_web/.trellis/spec/backend/web-runtime.md: executable contract and checks.

Existing unrelated Web Nginx/iOS/OHOS work and the concurrent Java terminal work
were retained. The Java peer later reformatted one line in the HTML error display
and added terminal resizing/scrolling changes elsewhere in editor_page.dart.
A comparison against the proposed file confirmed the per-file HTML behavior
remains present; the final tests below ran against that current shared tree.

## Tests

1. pi ran the full Web/app/native suite sequentially:
   flutter test --no-pub --concurrency=1 test/web_preview_current_file_test.dart
   test/web_app_test.dart test/web_dev_server_test.dart test/nginx_session_test.dart
   test/nginx_host_test.dart test/web_tools_navigation_test.dart test/web_tools_page_test.dart
   Result: 47 passed, 0 failed. Raw output: research/test-web-suite.log.
   The new 9-case suite is included in these 47; it is not an additional count.

2. Codex independently ran from qfli_web:
   flutter test --no-pub --reporter expanded --concurrency=1
   ../qfli_studio_core/test/editor_run_test.dart
   ../qfli_studio_core/test/terminal_pane_test.dart
   ../qfli_studio_core/test/shell_command_test.dart
   Result: 61 passed, 0 failed; process exit 0.
   Raw output: research/shared-core-final.log.
   Coverage includes Main/Main2/Main gestures, saving before launch, continuous
   transcript/prompt, nonzero diagnostics, cancellation, session state, real shell
   commands, scrolling, panel resizing and compact viewport behavior.

3. pi ran flutter analyze --no-pub lib test.
   Result: No issues found. Raw output: research/analyze-lib-test.log.

4. Codex checked task-owned Web diffs for whitespace errors, compared the applied
   core helper/server against the reviewed proposal, and inspected the final
   HTML browser/copy target flow.

Total distinct passing tests above: 108.

## Visual and evidence limits

Codex inspected the terminal render captures from the Java workspace, including
the later phone-dark.png and editor-phone-expanded.png under:
D:/MyNewProjects/qfli_java/.trellis/tasks/10-09-terminal-shell-panel-fixes/research/screenshots/

Commands/output and the prompt occupy one scrollable transcript; the input is
not a separate bottom block. Successful completion text is suppressed and the
Java runner uses java Main/java Main2 titles without a JDK suffix.

These are Flutter render-harness images. Real WebForge, legacy LocalWebServer
and native Nginx HTTP responses were tested. The HTML widget tests deliberately
fail debug attachment after recording the chosen URL, proving gesture routing
and failure cleanup without opening an external browser. Actual browser/WebView
end-to-end UI and new platform installation were not performed in this task.

The earlier intermediate core compilation failures were resolved by the Java
workspace; all final suites passed. Broad workspace analysis includes historical
build/native/platform-audit snapshots, so the relevant live lib/test scope was
used. No commit or push was requested or performed.


## Delivery follow-up (2026-10-15)

The reviewed product runtime/current-file code and tests were delivered in
e673e48. The final82-test WebForge suite and116 shared regressions pass with
the current core; Android native/content integration also passes. Current
release artifacts and OHOS signing limits are recorded in
`../../10-15-webforge-store-readiness/results.md`. Earlier results above remain
dated historical evidence.
