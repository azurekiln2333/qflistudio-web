# Error Handling

> How `qfli_web` surfaces failures. The runtime never hides a bad state behind a
> silent fallback; callers can always tell whether a real engine served the
> request.

---

## Error Types

| Source | Type | Where raised |
|--------|------|--------------|
| Invalid `.qfli/web.json` | `FormatException` | `WebProjectConfig.parse` |
| Missing project/root directory | `FileSystemException` | `WebProjectConfig.parse` |
| Missing explicit Nginx binary | `StateError` | `WebRuntime.start` |
| Native start/config/lifecycle failure | `PlatformException` (`NGINX_START`, `NGINX_SESSION`, `INVALID_ARGUMENT`) | embedded host channel |
| Exec permission denied (HarmonyOS) | `ProcessException` (errno 13) | `ProcessNginxHost` |
| Bind/Socket failure | `SocketException` | server `start` |

`WebProjectConfig.parse` is the single validation gate. UI saves and server
startup both call it (see `_WebProjectSettingsDialogState._save` in
`lib/pages/web_tools_page.dart`), so an invalid config fails the same way in both
paths. Reference: `lib/services/web_project_config.dart`.

## Error Handling Patterns

- **Validate at the boundary, throw a typed error.** Reject invalid `root`,
  `port`, `spaFallback`, `proxies` and `engine` with `FormatException` before any
  socket is bound. Matrix in `web_project_config.dart` `parse`.
- **Never silently substitute an engine.** Explicit `engine: "nginx"` must
  throw when the binary is missing (`StateError('当前设备没有可用的 Nginx
  运行文件')`, `web_runtime.dart`). `engine: "auto"` can select `WebDevServer`
  when no process binary is available. On iOS/OHOS it probes the embedded host
  version and falls back when that channel is unavailable or reports no real
  Nginx version. Explicit Nginx selection still propagates startup failures.
- **Clean up on failure.** `NginxSession.startWithHost` wraps startup in
  `try/catch` and stops the session/bridge and deletes the temp prefix before
  rethrowing. Any partial startup must not leak a listener or prefix.
- **Stop before restart.** A second run stops the previous session first; the
  editor stops a freshly-started preview session if URL resolution fails (see
  `qfli_studio_core` `editor_page.dart` HTML branch and
  `test/web_preview_current_file_test.dart`).
- **Surface to the user, don't swallow.** UI catches and shows a snackbar
  (`web_tools_page.dart` `_start`/`_openBrowser`). Internal optional operations
  (file watching, log tailing) may be swallowed only when explicitly justified;
  see the `// File watching is optional...` comment in `web_dev_server.dart`.

## API / HTTP Error Responses

The served surface has a fixed status contract (full table in
[Web Runtime](./web-runtime.md)):

| Condition | Status |
| --- | --- |
| Traversal, hidden project files, symlink escape | 403 |
| Missing asset | 404 (never SPA HTML) |
| Static request outside GET/HEAD | 405 |
| Invalid debug JSON | 400 |
| Debug event from foreign Origin | 403 |
| Debug event > 16 KiB | 413 |
| Upstream connect/WebSocket failure | 502 |
| Upstream timeout | 504 |

## Debug Output / Diagnostics

There is no logging framework. Failures are surfaced through the runtime's debug
streams and native diagnostics, consumed by the editor terminal and the Web
tools page:

- `WebRuntimeSession.debugStream` carries browser console lines and HTTP errors.
- The native engine's `error.log` is tailed with bounded reads and forwarded as
  `[nginx] ...` lines (`nginx_session.dart` `_readErrorLog`).
- Never write tokens, credentials or absolute user paths into user-visible
  diagnostics; the session token is emitted only as the `X-WebForge-Session`
  header, not logged.

## Common Mistakes

- Returning the SPA `index.html` for a missing asset instead of 404.
- Falling back to WebForge when the user explicitly selected Nginx.
- Leaving the temp prefix, bridge listener or a `StreamController` open after a
  failed start.
- Assuming `capabilities` are always present — an older session without
  `WebFilePreviewSession` must error, not open the default page.
