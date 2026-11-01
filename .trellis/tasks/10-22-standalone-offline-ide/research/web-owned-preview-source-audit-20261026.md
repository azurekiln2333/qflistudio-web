# Product-owned ArkWeb preview: source audit and gap register

Date: 2026-10-26 (Asia/Shanghai). Parent task: `10-22-standalone-offline-ide`.
Method: read-only inspection of the current worktree. No Flutter, SDK, Hvigor,
native compile, browser, WSL or device run happened. Every "not run" claim stays.

## 1 Source that already exists

| File | What it actually contains | Limit |
| --- | --- | --- |
| `ohos/entry/src/main/ets/entryability/OfflinePreviewPolicy.ets` | One pure export `isOfflinePreviewUrl(string): boolean`. Rejects whitespace, C0/C1 controls and backslash. Accepts only `https?://` + `127.0.0.1` or `[::1]` + explicit decimal port 1..65535, optionally followed by path/query/fragment. No imports, no I/O. | URL syntax only. It is not a resource broker and does not classify methods or subresources. |
| `ohos/entry/src/main/ets/entryability/EntryAbility.ets` | Channel `qflistudio/platform` with `startupProgress`, `openUrl`, `shareText`, picker methods. `openUrl` validates with the policy above, then calls `startAbility({action:'ohos.want.action.viewData'})`. `configureFlutterEngine` also wires `configureNginxChannel`. `onDestroy` calls `stopActiveNginx()`. | No Web component, no preview channel, no debug lease, no broker. Preview leaves the app as another ability. |
| `ohos/entry/src/main/ets/pages/Index.ets` | `FlutterPage` plus `StartupSplash` progress overlay and `EVENT_BACK_PRESS`. | No mount point for an owned Web component. |
| `ohos/entry/src/ohosTest/ets/testability/TestAbility.ets` | Test-only debugging switch. `qfliCatalogCdp=tcp` takes a port 1025..65535 on API 20+. `qfliCatalogCdp=unix` calls the one-argument `setWebDebuggingAccess(true)`. Disables on window-stage destroy, ability destroy and stop want. | Compiled into the ohosTest HAP only. Production never imports it. |
| `ohos/entry/src/ohosTest/ets/testability/pages/Index.ets` | Incognito `Web` at a fixed bootstrap URL. `onInterceptRequest` delegates to `CatalogHarness.response`. | No `blockNetwork`, no navigation override, no permission or popup denial. A test route, not a preview. |
| `ohos/entry/src/ohosTest/ets/testability/CatalogHarness.ets` | Synchronous broker. `response(url, method)` returns `WebResourceResponse` with `setResponseData`: 405 for non-GET/HEAD, 200 for bootstrap and known documents, 404 inside a fixed loopback port range, 403 for everything else. Returns `null` for `data:`, `blob:` and `about:blank`. | Synchronous only. No `setResponseIsReady`, no async pending response, no byte or in-flight bounds, no session origin, no deadline. |
| `ohos/entry/src/ohosTest/ets/testability/pages/SelfCdp.ets` and `SelfCdpProof.ets` | Test-owned incognito `Web` with `onInterceptRequest`, `onLoadIntercept`, `onOverrideUrlLoading` (all keyed to one random bootstrap URL, fail-closed 403 after close) and `onPageEnd`. Proof client runs bounded HTTP `/json/list`, one exact target match, WebSocket upgrade and `Runtime.evaluate (6*7)`. | Test-only. No Debugger domain, no breakpoints, no pause/step, no production import. |
| `ohos/entry/src/main/cpp/web_cdp_transport.{h,cpp}`, `web_cdp_transport_napi.cpp`, `types/libqfli_web_cdp_transport/index.d.ts` | Self-only abstract Unix transport. `openSelf(): {status, handle}` plus `read`/`write`/`close` as decimal-string handles. `CMakeLists.txt` builds `qfli_web_cdp_transport` as SHARED and links `libace_napi.z.so` and pthread with 16 KiB page alignment. `ohos/entry/oh-package.json5` registers the module. | Ships in the main HAP but has no product caller. The only importer is ohosTest. Compile and device behavior unverified here. |
| `../qfli_studio_core/lib/services/debug_session.dart` | Frozen contract: `StudioDebugger`, `DebugCapabilities`, `DebugLaunchRequest`, `DebugBreakpoint`, `DebugPauseToken`, `DebugThread`, `DebugPhase`, `DebugCommand`. | Contract only. No ArkWeb adapter exists on either side. |
| `lib/services/web_project_config.dart`, `web_dev_server.dart`, `nginx_session.dart` | `offlineContentSecurityPolicy` = `default-src 'self' data: blob:; script-src 'self' 'unsafe-inline' 'unsafe-eval' blob:; style-src 'self' 'unsafe-inline' data: blob:; connect-src 'self' blob:; form-action 'self'; base-uri 'self'; object-src data: blob:`. Non-literal-loopback proxy targets are rejected before any bind. Loopback serving plus early head bridge injection. | This is the serving side. It cannot confine an in-app Web component. |

## 2 Code that is actually missing

- Production owned Web component. `ohos/entry/src/main/ets/pages/` holds only `Index.ets` and `AgreementReader.ets`.
- The `qflistudio/web_preview` method channel and its `qflistudio/web_preview/events` event channel. A tree-wide grep finds only `qflistudio/platform`.
- `lib/services/owned_web_preview.dart` (lease, native protocol, URL ownership, cleanup).
- `lib/services/ohos_cdp_transport.dart`, `cdp_wire.dart`, `web_debugger.dart`, `web_debug_session.dart`.
- Any Dart FFI binding for `libqfli_web_cdp_transport.so`. `lib/` has zero occurrences of `cdp`.
- Any Dart reference to `StudioDebugger` or `debug_session`. The Web product installs no debugger.
- A production `setWebDebuggingAccess` owner. The only callers are in `ohosTest`.
- A production asynchronous broker. `setResponseIsReady(false)` appears nowhere.
- Production `blockNetwork`, navigation override, permission, popup and download denial.

## 3 First block safe to implement independently

New file `lib/services/owned_preview_policy.dart`. Pure Dart, `dart:core` only, no
platform channel, no FFI, no engine access. It is the single owner of broker
decisions, so later ETS and native work consume one written contract.

```dart
enum OwnedPreviewDecision { allow, forbidden, methodNotAllowed, invalidTarget }

const int kOwnedPreviewMaxInFlight = 16;
const int kOwnedPreviewMaxResponseBytes = 2 << 20;
const int kOwnedPreviewMaxRetainedBytes = 16 << 20;
const Duration kOwnedPreviewRequestDeadline = Duration(seconds: 5);
const String kOwnedPreviewExtraPolicy =
    "connect-src 'none'; worker-src 'none'; frame-src 'none'";

OwnedPreviewDecision classifyOwnedResource({
  required String url, required String method, required String origin});
bool isOwnedNavigationAllowed({required String url, required String origin});
String buildOwnedContentSecurityPolicy(String base);
```

Why this block is safe and checkable with source alone. Every function is pure and
total. The accept/reject table is written in the doc comment. No runtime, no SDK,
no device and no build step can change the verdict, so a reviewer can diff the
table against the code. It imports nothing from `ohos/` and nothing from
`qfli_studio_core`, so it cannot break platform or shared-core code. Unit tests
can land beside it and stay unrun until a normal test window opens.

Rules the table must carry. The origin is the exact runtime origin including
port, compared as a parsed `Uri`, never by prefix. Methods other than GET and
HEAD return `methodNotAllowed`. Any `data:`, `blob:`, `about:`, `file:`,
`resource:` or custom scheme returns `invalidTarget` rather than a pass.
Userinfo, fragments on the request URL, backslash, encoded path escapes and
non-ASCII controls all fail. `buildOwnedContentSecurityPolicy` must emit an
intersecting policy, because the current base CSP already allows
`connect-src 'self' blob:` and inline eval.

## 4 Broker coverage the owned preview must close

`onInterceptRequest` alone is not a boundary. Each class below needs an explicit
decision and its own measured result before any claim.

- fetch/XHR: `onInterceptRequest` cannot read POST bodies, so non-GET returns 405. Page fetch and XHR must be refused by `connect-src 'none'` in the intersecting CSP. ArkWeb enforcement is unverified.
- frame: subframe documents reach interception, but the frame initiator and main-frame flag need separate handling. `frame-src 'none'` plus a recheck on every served document. Frame POST navigation is outside `onOverrideUrlLoading`.
- navigation: require both `onLoadIntercept` and `onOverrideUrlLoading`, then recheck again in interception. The override callback omits POST, so it cannot be the only gate. External, custom and file navigation must fail closed with an error, never fall through to the system browser.
- worker: `worker-src 'none'` is the only stated lever. Whether `onInterceptRequest` sees Worker and SharedWorker script loads, and `importScripts`, is unproven. Treat workers as unsupported in v1 and say so.
- Service Worker: keep the API off and register no `setServiceWorkerWebSchemeHandler`, because that handler is application-global and would alter unrelated Web components such as `AgreementReader`. Incognito is not a denial guarantee.
- WebSocket: the handshake is not an HTTP resource response, so interception does not cover it. Only `connect-src 'none'` plus `.blockNetwork(true)` are candidates. Enforced-block evidence is missing.
- Also uncovered today: `blockNetwork` behavior against synthetic intercepted responses, popup and multi-window, download handlers, page permissions, geolocation and native file access.

## 5 Honest status

Nothing in section 4 has a recorded ArkWeb measurement. No owned preview exists, so
no offline or debugging acceptance is claimed. The transport has source and host
fixture evidence only. R8 (debugger composition) and the owned-browser part of R10
stay open.
