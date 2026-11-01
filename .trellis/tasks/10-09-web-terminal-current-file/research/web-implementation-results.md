# Web implementation — commands and raw results

Task: `10-09-web-terminal-current-file`
Run environment: Windows, `flutter test --no-pub --concurrency=1`, one runner at
a time. No commits, no pushes, core not written.

## Web source changes

| File | Change |
| --- | --- |
| `lib/services/web_dev_server.dart` | import core `web_preview_file.dart`; `WebDevServer implements WebRuntimeSession, WebFilePreviewSession`; `urlForFile` uses `config.root`. |
| `lib/services/nginx_session.dart` | same import/interface; `urlForFile` uses public `url` + `_bridge.config.root`. |
| `test/web_preview_current_file_test.dart` | new regression suite (real HTTP + editor URL-selection/widget). |
| `lib/main.dart`, `WebRuntime.start`, persisted config | unchanged. |

Baselines of the modified web files are preserved under
`research/web-baseline/lib/services/`.

## What each layer proves

- **Real HTTP success** (`WebDevServer`, core `LocalWebServer`, `NginxSession`):
  index → main2 → index, derived and explicit roots, nested/space/CJK/`#`/`%`
  names, relative assets, `x-webforge-engine: nginx` over the public port, and
  post-stop connection refusal.
- **Editor URL selection and failure cleanup** (widget group): tap reads the
  default URL; long press resolves the active file; a session that fails to
  resolve is stopped. The fake session's `debugStream` throws `StateError`, so
  the flow never launches a browser.
- **Not covered**: an actual browser/WebView end-to-end open. No
  `RunnerService`/`openUrl` interception and no test-only production hook.

## Final results (all green)

### 1. New regression suite

```
flutter test --no-pub --concurrency=1 test/web_preview_current_file_test.dart
```

Result: **All tests passed! (9/9)** — log: `test-new-file.log`.

### 2. Full Web/app/native suite, ordered single process

```
flutter test --no-pub --concurrency=1 \
  test/web_preview_current_file_test.dart \
  test/web_app_test.dart \
  test/web_dev_server_test.dart \
  test/nginx_session_test.dart \
  test/nginx_host_test.dart \
  test/web_tools_navigation_test.dart \
  test/web_tools_page_test.dart
```

Result: **All tests passed! (47/47)** — log: `test-web-suite.log`.

The core-importing suites (`web_app_test`, `web_tools_navigation_test`,
`web_tools_page_test`) compile and pass in this run. An earlier run in the same
session saw them fail to compile against an intermediate, mid-edit snapshot of
the sibling core `lib/editor/terminal_pane.dart`; that snapshot has since been
completed by the Java workspace, so it is **not** an outstanding blocker.

### 3. Analyze

```
flutter analyze --no-pub lib test
```

Result: **No issues found! (ran in 2.4s)** — log: `analyze-lib-test.log`.

Consolidated command/result record: `web-implementation-final.log`.

## Notes

- `flutter analyze --no-pub lib test` is clean for the Web changes and the new
  test.
- Core is read-only here; nothing in the core tree was written by this task
  beyond the already-approved patch applied by the reviewer.
