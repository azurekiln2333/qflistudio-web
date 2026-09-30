# Web Runtime Contracts

## 1. Scope / Trigger

Use this contract when changing project configuration, preview startup, static
serving, proxying, browser diagnostics, live reload, or the Web tools page.
The product owns these capabilities; `qfli_studio_core` owns shared editor hooks.

## 2. Signatures

```dart
Future<WebDevServer> WebDevServer.start(String projectPath);
Future<WebProjectConfig> WebProjectConfig.load(String projectPath);
WebProjectConfig WebProjectConfig.parse(String projectPath, Map<String, dynamic> data);
Future<void> WebPreviewSession.stop();
```

`webProfile.webPreviewFactory` starts the product server. The editor subscribes
to `debugStream` and opens `url`; it stops the previous session before running
again and stops the active session on disposal. Do not also start a second
preview through `RunnerService.runProject`.

## 3. Contracts

- The listener binds `127.0.0.1`. Port zero requests an available ephemeral port.
- `.qfli/web.json` stores `root: String?`, `port: int`, `spaFallback: bool`, and
  `proxies: [{prefix: String, target: String}]`.
- The root is explicit or chosen from root `index.html`, then `src/index.html`.
  UI saves and server startup both validate through `WebProjectConfig.parse`.
- Proxy targets are HTTP(S) URLs without query, fragment, or credentials.
  Prefix matches have path-segment boundaries; the longest prefix wins.
- HTTP proxies preserve methods, query, bodies, status, redirects, and headers.
  Strip hop headers and headers named by `Connection`. Preserve compressed bytes
  with `HttpClient.autoUncompress = false`.
- WebSocket proxies forward text, binary messages, and negotiated subprotocols.
  Both peers are tracked and closed on stop. Never forward reserved close codes
  1005, 1006, or 1015 as wire close codes.
- `POST /__webforge/debug` accepts JSON with `message: String` and optional
  `level: String`. Payloads are limited to 16 KiB; rendered lines to 4000 characters.
- `GET /__webforge/events` emits SSE `data: reload`. Set
  `HttpResponse.bufferOutput = false`; `flush()` alone did not stream data in
  the Windows integration test. Debounce native file events by 180 ms.
- Request events include method, URI, status, and duration. HTTP errors also
  enter the editor debug stream.
- `qflistudio/platform.openUrl` accepts `{url: String}`. Android launches an
  HTTP(S) intent; iOS presents Safari inside the app to retain foreground service
  execution. macOS needs network client and server entitlements.

## 4. Validation & Error Matrix

| Condition | Outcome |
| --- | --- |
| Invalid JSON, root, port, SPA flag, or proxy rule | Startup fails with a specific configuration error |
| Traversal, hidden project files, symlink escape | 403 |
| Missing asset | 404, never the SPA HTML |
| Extensionless HTML navigation with SPA fallback | Root HTML |
| Static request outside GET/HEAD | 405 |
| Invalid debug JSON | 400 |
| Debug event from a foreign Origin | 403 |
| Debug event larger than 16 KiB | 413 |
| Upstream connection / WebSocket failure | 502 |
| Upstream timeout | 504 |

## 5. Good / Base / Bad Cases

- Good: a `src/index.html` template loads its relative CSS/JS; `/api/items?q=7`
  forwards to `/v1/items?q=7`; a WebSocket proxy echoes binary data.
- Base: a root-level static project runs with an ephemeral loopback port.
- Bad: `/missing.js` receives SPA HTML, proxy redirects are followed internally,
  or a second preview listener remains active after an editor run.

## 6. Tests Required

- `test/web_dev_server_test.dart`: static assets, traversal/symlinks, SPA rules,
  proxy request/response fidelity, redirects, WebSocket protocol/messages/stop,
  a real SSE file-change event, malformed events, and error diagnostics.
- `test/web_app_test.dart`: product hook wiring and root/src entry behavior.
- `test/web_tools_navigation_test.dart`: existing navigation and persisted settings.
- `test/web_tools_page_test.dart`: actual HTTP transport and visible codec results.
- Run `flutter analyze --no-pub` and `flutter test --no-pub`. Native platform
  builds and device checks provide separate evidence; Dart tests do not validate
  Swift, entitlements, Android intents, or HarmonyOS browser behavior.

## 7. Wrong vs Correct

```dart
// Wrong: a dynamic map result can fail at runtime for Connection headers.
result.addAll(value.split(',').map((item) => item.trim().toLowerCase()));

// Correct: add each normalized token through the typed set boundary.
for (final item in value.split(',')) {
  result.add(item.trim().toLowerCase());
}
```

The Dart engine is a local development server. Advertise Nginx only when a real
upstream Nginx binary is packaged, launched, verified, and stopped correctly.
