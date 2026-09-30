# Web Runtime Contracts

## 1. Scope / Trigger

Use this contract when changing project configuration, preview startup, static
serving, proxying, browser diagnostics, live reload, or the Web tools page.
The product owns these capabilities; `qfli_studio_core` owns shared editor hooks.

## 2. Signatures

```dart
Future<WebDevServer> WebDevServer.start(String projectPath);
Future<WebRuntimeSession> WebRuntime.start(String projectPath);
Future<NginxSession> NginxSession.start(String projectPath, {required String executable});
Future<WebProjectConfig> WebProjectConfig.load(String projectPath);
WebProjectConfig WebProjectConfig.parse(String projectPath, Map<String, dynamic> data);
Future<void> WebPreviewSession.stop();
```

`WebRuntimeSession` extends `WebPreviewSession` with `engineName` and `requests`.
`webProfile.webPreviewFactory` uses `WebRuntime.start`. The editor subscribes
to `debugStream` and opens `url`; it stops the previous session before running
again and stops the active session on disposal. Do not also start a second
preview through `RunnerService.runProject`.

## 3. Contracts

- The listener binds `127.0.0.1`. Port zero requests an available ephemeral port.
- `.qfli/web.json` stores `root: String?`, `port: int`, `spaFallback: bool`, and
  `proxies: [{prefix: String, target: String}]`, plus
  `engine: "auto" | "nginx" | "webforge"` (default `auto`).
- Native Nginx owns the public loopback port. An ephemeral private WebForge
  middleware retains static-path protection, SPA behavior, diagnostics and SSE.
  Its Origin checks use the public Nginx port. Both belong to one session.
- Native HTTP proxies and WebSocket upgrades run in Nginx. HTTPS rules use the
  middleware because the native build does not include OpenSSL. Generate native
  locations for both schemes: longer HTTPS prefixes must still beat HTTP parents.
- Each native session uses its own temporary prefix, validates `nginx -t`, checks
  the session-token header through `/__webforge/health`, tails JSON access logs
  in bounded reads, and forwards stderr. Version/config/signal commands kill
  their child on timeout. Stop uses `-s stop`, with a bounded kill fallback, then
  stops middleware, cancels streams and removes the prefix.
- Display the running session's actual `engineName`. Explicit Nginx never
  substitutes another engine. On HarmonyOS, `auto` handles a native exec EACCES
  by selecting WebForge; other startup errors still propagate.
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
| Invalid engine value | FormatException before binding |
| Explicit Nginx with missing binary | Startup error |
| Explicit Nginx with exec permission denied | ProcessException; no substitution |
| Auto on HarmonyOS with exec permission denied | WebForge session, labeled WebForge |
| Occupied native port | Startup fails and cleans temporary prefix / middleware |
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
- `test/nginx_session_test.dart`: real upstream binary/header, native HTTP and
  WebSocket proxies, overlapping HTTP/HTTPS prefix priority, diagnostics, native
  access logs, SSE streaming, port conflict and post-stop connection failure.
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

## Native Packaging & Evidence

- Retain upstream source/Windows archive hashes in `vendor/nginx/SOURCE.json`;
  retained build inputs and binaries are covered by `HASHES.sha256`.
- Android API 24 PIE executables ship as `jniLibs/<abi>/libnginx_exec.so` with
  legacy library extraction. `nginxPath` returns `applicationInfo.nativeLibraryDir`.
  Do not extract to writable app data and assume chmod enables execution.
  Application smoke passed on the API 37 x86_64 emulator with actual 16 KiB
  pages. This does not prove arm64/32-bit device execution.
- HarmonyOS packages native files under `entry/libs/<abi>/`; `nginxPath` resolves
  `applicationInfo.nativeLibraryPath`. Declare each native executable in
  `module.executableBinaryPaths` using module-relative paths, such as
  `libs/x86_64/libnginx_exec.so`. The original package installed this file with
  mode 100644 and app `Process.run(..., ['-v'])` returned EACCES, while system
  `echo` worked. The manifest change passes signed dual-ABI packaging; app
  execution after the change remains unverified. Shell execution is insufficient.
- WSL Windows compiler invocation uses `/init <executable> <argv[0]> <args>`.
  Normalize CRLF compiler output before configure writes generated C strings.
  Scope LF Git attributes to shell scripts, patches and native source inputs.
- Run `tool/nginx_smoke.dart` on each device ABI and require its PASS marker.
  APK/HAP builds and shell `-V` alone cannot satisfy this gate. Restore the normal
  `lib/main.dart` target for deliverable builds. See `vendor/nginx/VALIDATION.md`.
