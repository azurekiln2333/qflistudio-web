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
Future<NginxSession> NginxSession.startWithHost(String projectPath, {required NginxHost host});
Future<WebProjectConfig> WebProjectConfig.load(String projectPath);
WebProjectConfig WebProjectConfig.parse(String projectPath, Map<String, dynamic> data);
void WebProjectConfig.validateOffline();
Future<void> WebPreviewSession.stop();

// Optional capability; existing WebPreviewSession/factory signatures stay intact.
abstract interface class WebFilePreviewSession implements WebPreviewSession {
  String urlForFile(String absolutePath);
}
String webPreviewUrlForFile({
  required String baseUrl,
  required String documentRoot,
  required String filePath,
});
```

`WebRuntimeSession` extends `WebPreviewSession` with `engineName` and `requests`.
`webProfile.webPreviewFactory` uses `WebRuntime.start`. The editor subscribes
to `debugStream` and opens the resolved preview URL; it stops the previous session
before running again and stops the active session on disposal. Do not also start a second
preview through `RunnerService.runProject`.

## 3. Contracts

- The listener binds `127.0.0.1`. Port zero requests an available ephemeral port.
- A normal Run tap opens `server.url`. Long press requires the optional
  `WebFilePreviewSession` and calls `urlForFile` with the active absolute path.
  The browser and copy-address action use that same target URL. No persisted
  project/Web configuration changes and no silent fallback to the default page.
- File URLs use the session's actual document root and public listener. The
  shared resolver canonicalizes the file/root, verifies containment and file
  existence, rejects hidden segments except `.well-known`, and encodes raw
  path segments once with `Uri`. Never append a project-relative path to the URL.
- Cancel the old preview debug subscription and clear/stop the old session before
  replacement. If startup, target resolution or debug attachment fails, stop the
  newly created session and clear its references.
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
- iOS uses `EmbeddedNginxHost` through `qflistudio/nginx`. The native pthread
  retains the same configuration/middleware/health-token checks. Configuration
  checks finish/release their worker before server start. Stop waits for actual
  native cleanup/release before deleting the prefix or stopping middleware.
  The embedded error.log is tailed with bounded reads alongside access.log.
- Display the running session's actual `engineName`. Explicit Nginx never
  substitutes another engine. On iOS and HarmonyOS the embedded engine is the
  only native path; `auto` probes the embedded channel's `version` first and
  falls back to WebForge when the shared library or its channel is absent.
  Explicit `nginx` on those platforms surfaces the embedded startup error.
- The root is explicit or derived from the safe HTML entry returned by
  `RunnerService.findEntry`, including `.qfli/project.json`'s `entryFile`.
  Legacy projects retain root `index.html`, then `src/index.html` discovery.
  `WebProjectConfig.indexFile` is relative to the canonical root and defaults
  to `index.html`. `/` and SPA navigation use it; subdirectories keep their own
  `index.html`. An explicit Web root wins when the entry lies elsewhere.
  Nginx passes `indexFile` to its private middleware. UI saves and server startup
  both validate through `WebProjectConfig.parse`.
- Proxy targets are HTTP(S) URLs without query, fragment, or credentials.
  Only literal loopback IPs are accepted (`InternetAddress.tryParse(host)` with
  `isLoopback`); DNS names, LAN/public IPs, wildcards and IPv4-mapped IPv6 are
  rejected. Prefix matches have path-segment boundaries; the longest prefix wins.
  Parsing and both engine startup paths call `validateOffline()` before binding
  or native host calls, including an explicitly supplied configuration. Rejecting
  a persisted rule must not rewrite the user's configuration. Hidden proxy UI
  alone does not enforce this policy, and this policy alone does not isolate an
  externally opened browser's resources or navigation.
- The Dart proxy client uses direct connections and checks every actual socket
  destination, including WebSocket handshake redirects, as a literal loopback
  IP before DNS/connection. A custom `HttpClient.connectionFactory` owns TLS:
  use `SecureSocket.startConnect` for HTTPS (including converted WSS) and
  `Socket.startConnect` for HTTP. Never send plaintext HTTP to an HTTPS target.
- HTTP proxies preserve methods, query, bodies, status, redirects, and headers.
  Strip hop headers and headers named by `Connection`. Preserve compressed bytes
  with `HttpClient.autoUncompress = false`.
- WebSocket proxies forward text, binary messages, and negotiated subprotocols.
  Both peers are tracked and closed on stop. Never forward reserved close codes
  1005, 1006, or 1015 as wire close codes.
- `POST /__webforge/debug` accepts JSON with `message: String` and optional
  `level: String`. Payloads are limited to 16 KiB; rendered lines to 4000 characters.
- Inject the browser log bridge before authored head scripts, at the actual
  HTML5 head opening span. With an implicit head, insert after an actual doctype
  or at the source start. Preserve document mode, UTF-8 BOM and authored source;
  map parser-normalized CRLF offsets back to the original UTF-16 boundary. A
  comment, quoted attribute, script/style/title literal or unclosed trailing
  comment cannot choose or swallow the insertion point. Console/error/rejection
  events must reach the production debug stream once from a real browser.
- Both preview engines attach `WebProjectConfig.offlineContentSecurityPolicy`
  to every response, including errors and proxied responses. It restricts
  resources/connect/form/base targets to the preview origin, preserving authored
  inline JavaScript/styles, local assets and data/blob resources. Middleware
  proxy responses cannot overwrite it. Both engines strip the shared
  `offlineProxyPolicyHeaders` set: CSP, CSP-Report-Only, Reporting-Endpoints,
  Report-To and NEL. Nginx derives its `proxy_hide_header` lines from that set
  and adds the product policy. CSP report delivery is not constrained by
  `connect-src`, so hiding only the enforcing CSP is insufficient. Local APIs
  remain available through validated loopback proxy
  paths. CSP is not a claim of complete system-browser navigation isolation;
  ordinary links/new windows still require a controlled preview view.
- Preserve the shipped local resource schemes explicitly in the more-specific
  directives: `style-src 'self' 'unsafe-inline' data: blob:`,
  `connect-src 'self' blob:` and `object-src 'self' data: blob:`. A directive overrides
  `default-src`; its allowed schemes are not added to the default list. The
  shipped HTML027 data stylesheet, HTML097 Blob stylesheet, HTML137 Blob HTML
  object, HTML138 data SVG embed and JS017 Blob JSON fetch must work unchanged
  through both production engines. Objects may load from the exact preview
  origin, data or Blob URLs. Other HTTP(S) origins must fail before the network
  guard. Do not infer Blob permission from `'self'`, or add network/script-data
  permission to make a local fixture pass. The
  [October24 compatibility repair](../../tasks/10-22-standalone-offline-ide/research/web-offline-catalog-policy-20261024.md)
  and its expanded browser regression passed both production engines in the
  authorized C782 desktop run on2026-10-26. See the
  [C782 scope record](../../tasks/10-22-standalone-offline-ide/research/web-c782-validation-20261026.md).
  This does not establish ArkWeb or the full catalog gate.
- Object policy must allow the exact preview origin as well as data/Blob.
  An authored `<object type="text/html">` can be checked before its script
  assigns the Blob URL. C606 failed both engines with an empty blocked URI
  when `object-src` omitted self. Preserve the original teaching source and
  verify actual loaded object content. Also require another loopback port's
  object/embed to produce CSP violations with zero route/sentinel hits.
  [C606 and the revised candidate](../../tasks/10-22-standalone-offline-ide/research/web-c606-offline-object-repair-20261026.md)
  record the earlier failures. C782 subsequently passed the unchanged teaching
  examples and cross-port object/embed negatives for both production engines.
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
| Non-loopback or DNS-name proxy target | `FormatException` before bind/native host; persisted bytes unchanged |
| Invalid engine value | FormatException before binding |
| Explicit Nginx with missing binary | Startup error |
| Explicit Nginx with exec permission denied | ProcessException; no substitution |
| Auto on iOS/HarmonyOS with a missing embedded library or channel | WebForge session, labeled WebForge |
| Explicit Nginx on iOS/HarmonyOS with a missing embedded library | Embedded startup error; no substitution |
| Embedded destroy path | `onDestroy` stops, polls and releases the token; a later `start` cannot hit `-EBUSY` |
| Occupied native port | Startup fails and cleans temporary prefix / middleware |
| Current HTML missing, directory, outside document root, or hidden | `FileSystemException`; no default-page fallback |
| Long press with a legacy session lacking file capability | `StateError`; new session is stopped |
| Failed per-file resolution or debug attachment | New session stopped; no stale session/debug subscription |
| Traversal, hidden project files, symlink escape | 403 |
| Missing asset | 404, never the SPA HTML |
| Extensionless HTML navigation with SPA fallback | Root HTML |
| Static request outside GET/HEAD | 405 |
| Invalid debug JSON | 400 |
| Debug event from a foreign Origin | 403 |
| Debug event larger than 16 KiB | 413 |
| Upstream connection / WebSocket failure | 502 |
| Upstream timeout | 504 |
| Authored data/Blob stylesheet, local Blob JSON or data/Blob embedded object | Allowed by the explicit local scheme policy; assert actual rendered/output behavior |
| External object/embed or other forbidden resource | CSP violation before any request reaches the test abort route |

## 5. Good / Base / Bad Cases

- Good: a `src/index.html` template loads its relative CSS/JS; `/api/items?q=7`
  forwards to `/v1/items?q=7`; a WebSocket proxy echoes binary data.
- Good: importing HTML as `src/lesson.html` previews it at `/` with working
  relative assets, through both WebForge and native Nginx.
- Good: with `main2.html` active, default/selected/default URLs serve the expected
  HTML while both `.qfli/project.json` and `.qfli/web.json` remain unchanged.
- Base: a root-level static project runs with an ephemeral loopback port.
- Bad: `/missing.js` receives SPA HTML, proxy redirects are followed internally,
  or a second preview listener remains active after an editor run.

## 6. Tests Required

- `test/web_dev_server_test.dart`: static assets, traversal/symlinks, SPA rules,
  proxy request/response fidelity, redirects, WebSocket protocol/messages/stop,
  a real SSE file-change event, malformed events, and error diagnostics.
  Its real-browser bridge cases run both production engines, asserting exact
  source retention through raw HTTP bytes (Chromium's response-body observation
  consumes a UTF-8 BOM), document mode and head/body console/error/rejection POSTs
  consumed from the production `debugStream`.
- `test/nginx_session_test.dart`: real upstream binary/header, native HTTP and
  WebSocket proxies, overlapping HTTP/HTTPS prefix priority, diagnostics, native
  access logs, SSE streaming, port conflict and post-stop connection failure.
- `test/web_offline_policy_test.dart`: persisted and directly supplied forbidden
  targets fail before native host use or occupied-port binding; literal IPv4/IPv6
  HTTP(S) loopback remains valid; real IPv4/IPv6 forwarding works, with an
  explicit skip if IPv6 cannot bind. Real WebSocket redirects to a disallowed
  hostname never reach a local sentinel. Raw HTTPS/WSS sentinels observe a TLS
  ClientHello rather than a plaintext GET. Both engines strip all upstream
  reporting headers on 200/302 while preserving unrelated headers/body/Location.
- `test/web_offline_browser_test.dart`: real browser executes local/inline
  scripts/styles while external script/style/image/frame/fetch/WebSocket/form
  attempts produce policy violations before reaching the test's abort route.
  Run through both production engines; inspect policy on 200/404 responses and
  absence of proxied report-only policy, with a real report/WebSocket sentinel.
  Copy exact current catalog source for HTML027/097/137/138 and JS017 into the
  temporary served project; assert actual colors/font, embedded document/SVG
  content and Blob fetch output, with no catalog CSP violations. Keep external
  object/embed negatives and zero escaped requests. An unrestricted catalog
  runner or synthetic `local.css` success cannot replace production-policy
  compatibility. The authorized C782 run passed this expanded regression on
  both production engines. Its full suite still had4 failures in the new owned
  policy/broker. Final coordination publication exceeded180s. OHOS remains open.
- Both server suites cover a custom imported HTML entry. The WebForge suite
  also checks SPA navigation and an explicit root pointing to build output.
- `test/web_preview_current_file_test.dart`: actual default/selected/default HTTP
  responses, derived/explicit roots, encoded filenames, invalid targets, relative
  assets, native public listener and stop. Its widget tests exercise real Run
  gestures and inject a debug-attachment failure to verify URL selection and
  cleanup without launching an external browser; that is not browser UI evidence.
- `test/web_app_test.dart`: product hook wiring and root/src entry behavior.
- `test/web_tools_navigation_test.dart`: existing navigation and persisted settings.
- `test/web_tools_page_test.dart`: actual HTTP transport and visible codec results.
- `test/web_server_tools_lifecycle_test.dart`: regular and320px/2x inline layouts
  perform real Start, HTTP200/404 and console POSTs, visible log Clear, subsequent
  diagnostics, Stop with strict native TCP refusal, restart and widget disposal
  with endpoint refusal. Preserve configuration bytes and fail framework
  exceptions; a timeout never substitutes for refusal. Repair10 passed both
  layouts with the measured5s probe budget.
- Run `flutter analyze --no-pub` and `flutter test --no-pub`. Native platform
  builds and device checks provide separate evidence; Dart tests do not validate
  Swift, entitlements, Android intents, or HarmonyOS browser behavior.

## 7. Wrong vs Correct

```dart
// Wrong: ignores the file captured by the long-press gesture.
await RunnerService.openUrl(server.url);

// Correct: the session resolves its actual serving root and public endpoint.
final String targetUrl;
if (entryOverride == null) {
  targetUrl = server.url;
} else if (server is WebFilePreviewSession) {
  targetUrl = server.urlForFile(entryOverride);
} else {
  throw StateError('preview does not support individual files');
}
await RunnerService.openUrl(targetUrl);
```

```dart
// Wrong: a dynamic map result can fail at runtime for Connection headers.
result.addAll(value.split(',').map((item) => item.trim().toLowerCase()));

// Correct: add each normalized token through the typed set boundary.
for (final item in value.split(',')) {
  result.add(item.trim().toLowerCase());
}
```

The Dart engine is a local development server. Advertise Nginx only when a real
upstream executable or embedded library is packaged, started, verified, and stopped correctly.

## Native Packaging & Evidence

- Linux builds the retained upstream C source through its CMake dependency and
  uses `install(PROGRAMS ...)` under `data/nginx/`. Configure probes require a
  native target host; reject a cross-built runner instead of packaging a host
  executable. `scripts/build_nginx_desktop.sh linux [OUTPUT]` also supports a
  checkout build under `assets/runtime/nginx/linux/` for integration tests.
- macOS runs `scripts/bundle_nginx_macos.sh` in the Runner target. Build both
  configure probes, final objects and linking with the same `ARCHS`; bundle the helper
  under `Contents/Helpers/nginx`, its license under `Contents/Resources/nginx/`,
  and sign the helper with the parent signing identity and sandbox inheritance
  before the outer application. Parent network client/server rights are needed.
  A copied unsigned helper or executable in Flutter assets is insufficient.
- `WebRuntime.nginxExecutable()` resolves Linux `data/nginx/nginx`, macOS
  `Contents/Helpers/nginx`, then platform-specific checkout paths. Desktop tests
  use that same discovery and exercise automatic engine selection as well as
  explicit Nginx. Missing native builds produce a visible skip, never a pass.
  Apple builds and Linux app execution remain unverified; consult VALIDATION.
  The 2026-10-02 WSL standalone build passed native static/proxy/404/stop checks.
  Keep that engine evidence distinct from Linux Flutter middleware integration.
- iOS links an upstream static archive through the Runner's Build Embedded Nginx
  phase and Flutter/Nginx.xcconfig. The SDK/ARCHS-specific build verifies target
  type sizes/byte order without executing target configure probes. Every object
  must match the iOS device/simulator platform before the final archive is linked.
  The Swift bridge retains the ABI through actual calls. Apple build/sign/runtime
  gates remain unverified without Xcode/devices; Linux embedded evidence is separate.
- Retain upstream source/Windows archive hashes in `vendor/nginx/SOURCE.json`;
  retained build inputs and binaries are covered by `HASHES.sha256`.
- Android API 24 PIE executables ship as `jniLibs/<abi>/libnginx_exec.so` with
  legacy library extraction. `nginxPath` returns `applicationInfo.nativeLibraryDir`.
  Do not extract to writable app data and assume chmod enables execution.
  Application smoke passed on the API 37 x86_64 emulator with actual 16 KiB
  pages. This does not prove arm64/32-bit device execution.
- HarmonyOS runs the embedded engine, not a standalone executable. The shared
  library is delivered as `libqfli_nginx_napi.so` under `entry/libs/<abi>/`,
  produced by the `externalNativeOptions` CMake target which links the
  per-ABI `libqfli_nginx.a` embedded archive. `module.executableBinaryPaths`
  must NOT be used: the standalone PIE form makes `bm install` fail with
  `ERR_INSTALL_CHECK_BIN_FILE_FAILED` on HarmonyOS 7.0. The NAPI bridge exports
  `version/start/poll/stop/release` over `qfli_nginx_*` and backs the
  `qflistudio/nginx` channel, matching the iOS bridge. `EntryAbility.onDestroy`
  stops, polls and releases the active token. Signed dual-ABI packaging and
  device install are verified; on-device embedded execution still awaits an
  unlocked screen for the end-to-end smoke.
- WSL Windows compiler invocation uses `/init <executable> <argv[0]> <args>`.
  Normalize CRLF compiler output before configure writes generated C strings.
  Scope LF Git attributes to shell scripts, patches and native source inputs.
- Run `tool/nginx_smoke.dart` on each device ABI and require its PASS marker.
  APK/HAP builds and shell `-V` alone cannot satisfy this gate. Restore the normal
  `lib/main.dart` target for deliverable builds. See `vendor/nginx/VALIDATION.md`.

## Embedded Lifecycle ABI

`qfli_nginx_version() -> const char*`, `qfli_nginx_start(prefix, test) -> int64_t`,
`qfli_nginx_poll(token, int* exit) -> int`, `qfli_nginx_stop(token) -> int`,
and `qfli_nginx_release(token) -> int` are the only public native exports.

The Flutter channel contract is:

| Method | Arguments | Success result |
| --- | --- | --- |
| version | none | upstream version string |
| start | `{prefix: String, test: bool}` | positive int64 token |
| poll | `{token: int}` | null while running; int exit code after cleanup |
| stop | `{token: int}` | null after a stop request is sent |
| release | `{token: int}` | null after joining/releasing the completed worker |

Native negative POSIX errors become `NGINX_START` / `NGINX_SESSION` platform
errors; malformed payloads become `INVALID_ARGUMENT`. C poll returns 0 pending,
1 completed, or a negative error. C start returns -EBUSY while a job remains
owned; release returns -EBUSY before completion. Old stop/release tokens are
harmless and cannot stop a later job. Polling can resume during Stop after a
transient channel error. Native core settings require daemon/master off and
zero timer_resolution/debug_points, including in configuration-test mode.

The worker blocks SIGPIPE only in its thread. It never installs host signal
handlers, sets process titles/environment, redirects descriptors or uses process
exit. The event backend's done action must be retained before partial init can
fail. Every terminal path releases arrays allocated outside the cycle pool.

Embedded CORE_SRCS must omit ngx_process.c, ngx_process_cycle.c, ngx_daemon.c
and ngx_setproctitle.c. Disabling master/daemon in configuration alone still
compiles fork, which is unavailable in the iOS SDK. The addon supplies the event
engine globals and rejecting ngx_execute/ngx_os_signal_process implementations;
ngx_debug_point cannot signal the host. The build rejects process-management
objects and forbidden process imports in the static archive on Linux and iOS.
Retain undefined-symbols.txt as build evidence. Optional event timer imports
remain compiled upstream but timer_resolution must be zero before event init.
Create the archive in the fresh build directory before replacing the output;
ar rcs on an existing archive retains removed process-management members.

Wrong: destroy an active HTTP request pool directly. Upstream cleanup finalizes
request references and can free that same pool recursively. Correct: retain the
main request while running ngx_http_terminate_request, then synchronously run
ngx_http_terminate_handler and close its connection. The build omits native
threads/AIO/HTTP2/HTTP3; do not enable them without extending this cleanup contract.

Process-global statics must stay consistent across `qfli_nginx_main` calls. The
editor runs `nginx -t` during validate and then the server, which is two Nginx
`main()` calls in one process; anything static outside the cycle survives the
`-t` run. A stale `ngx_cached_time` left `ngx_time()` at 0; that equals the
freshly zeroed access-log `disk_full_time`, and `ngx_http_log_handler` then
treats every entry as a disk-full duplicate and writes nothing, so the real
session's access.log stays empty. Root cause: `ngx_time_init()` points
`ngx_cached_time` at `cached_time[0]` without resetting the static slot cursor,
and `ngx_time_update()`'s same-second early return
(`cached_time[slot].sec == sec`) did not repoint the pointer, so a second cycle
in the same second left it on the zeroed slot. Fix
(`vendor/nginx/patches/embedded-time-cache.patch`): set `ngx_cached_time = tp;`
in that early return. A `qfli_nginx_reset_time()` that re-ran `ngx_time_init()`
did not help (it hit the same early return) and was removed. Guards: the
`native/nginx/embedded/access_log_probe.py` scenarios (`server-only`,
`test-then-server`, `server-then-server`, `test-then-restart`) and
`test_embedded.py::test_access_log_after_configuration_check`. When adding
engine state, prefer cycle-owned data; for any new static, prove it stays
consistent across runs.

Required gates are `native/nginx/embedded/test_embedded.py` (real library) and
`test_lifecycle.c` (100 cycles with leak detection), `test/nginx_host_test.dart`
(channel cleanup/error/diagnostic behavior), the unchanged real process suite,
and the Android application smoke. Apple device and simulator builds remain
separate gates, never inferred from Linux compilation or mocked channel tests.
