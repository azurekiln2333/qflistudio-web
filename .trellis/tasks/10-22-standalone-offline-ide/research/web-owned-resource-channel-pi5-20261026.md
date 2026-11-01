# Owned preview resource channel: minimum integration contract (Pi5)

Date 2026-10-26. Author Pi5. Source inspection only.

No SDK, Dart, Flutter, browser, native, device or Job command was run. No product,
core or script file was modified. This document proposes a contract. It does not
consume or replay any grant, and it does not claim any runtime result.

Inputs read:

- `.trellis/tasks/10-22-standalone-offline-ide/research/web-owned-preview-integration-independent-review-20261026.md` (sha256 `0bc843df68b6438532aeda2ad8ff2fc7a8521ceb761258e8a3cb280155531bab`)
- the actual OHOS bridge, Dart session and broker sources listed in section 1
- the installed Flutter OHOS embedding under `D:\ProgramFiles\flutter_ohos\engine\src\flutter\shell\platform\ohos\flutter_embedding\flutter\src\main\ets\`

## 1. What already exists, by path

| Path | What it actually provides |
| --- | --- |
| `ohos/entry/src/main/ets/entryability/EntryAbility.ets` | `configureFlutterEngine` registers `configureNginxChannel(flutterEngine)` and a `qflistudio/platform` handler with `startupProgress`, `openUrl`, `shareText` and picker methods. `onDestroy` calls `stopActiveNginx()`. |
| `ohos/entry/src/main/ets/entryability/NginxBridge.ets` | One `MethodChannel(..., 'qflistudio/nginx')`, `setMethodCallHandler`, five methods `version`/`start`/`poll`/`stop`/`release`, a module-level `activeToken`, and `stopActiveNginx()` exported for `onDestroy`. |
| `ohos/entry/src/main/ets/entryability/OfflinePreviewPolicy.ets` | `isOfflinePreviewUrl`: literal loopback plus explicit decimal port, rejecting control characters and backslashes. |
| `lib/services/nginx_host.dart` | `EmbeddedNginxHost.channel = MethodChannel('qflistudio/nginx')`; `_EmbeddedInstance._waitForExit` polls every 50 ms and calls `release`. Dart owns lifecycle ordering; native only forwards. |
| `ohos/entry/src/main/cpp/web_cdp_transport.h` | Four C functions, `QFLI_WEB_CDP_MAX_TRANSFER = 64 * 1024`, `QFLI_WEB_CDP_MAX_CONNECTIONS = 8`, abstract socket `webview_devtools_remote_<pid>` only. Raw nonblocking client transport. |
| `ohos/entry/src/main/cpp/web_cdp_transport_napi.cpp` | NAPI module `qfli_web_cdp_transport`, per-environment handle table, `napi_add_env_cleanup_hook` teardown, ArrayBuffer in/out. |
| `lib/services/owned_preview_policy.dart` | `classifyOwnedResource({url, method, origin})` at `:115`, `isOwnedNavigationAllowed` at `:143`, `buildOwnedContentSecurityPolicy` at `:167`, `enum OwnedPreviewDecision` at `:104`. |
| `lib/services/owned_preview_resource_broker.dart` | `OwnedPreviewResourceBroker({origin, maxInFlight, maxResponseBytes, maxRetainedBytes, maxDebugTextBytes, requestDeadline, debugTextLimit})`; `fetch(url, {method})` at `:114`; `dispose()` at `:172`; `activeRequests`/`retainedBytes`/`isDisposed` at `:110-112`; `OwnedPreviewResource{statusCode, headers, bytes, isReleased, release()}` at `:14-51`. |
| `lib/services/web_runtime_session.dart` | `WebRuntimeSession implements WebPreviewSession` adding `engineName` and `requests`. |
| `qfli_studio_core/lib/services/studio_profile.dart` | `webPreviewFactory` at `:145-147`; `abstract interface class WebPreviewSession {url, debugStream, stop}` at `:302-306`. |
| `qfli_studio_core/lib/services/web_preview_file.dart` | `WebFilePreviewSession` at `:12`. |
| `qfli_studio_core/lib/editor/editor_page.dart` | `:1473` calls the factory, `:1490` resolves the current-file URL, `:1501` `await RunnerService.openUrl(targetUrl)`. |
| `qfli_studio_core/lib/services/runner_service.dart` | `_ohosChannel = MethodChannel('qflistudio/platform')` at `:51-52`; `openUrl` at `:226-238` forwards to it and swallows `MissingPluginException`/`PlatformException`. |

Embedding facts that the contract depends on, verified in the installed
`flutter_ohos` sources:

- `plugin/common/MethodChannel.ets`: `invokeMethod(method, args, callback?)` exists on the native side, so one channel is bidirectional.
- Same file, `MethodCallHandler` doc: the handler runs "on the platform thread (OpenHarmony main thread) by default". Native must not block waiting for Dart.
- Same file, `MethodResult` doc: "The result may be submitted asynchronously and on any thread." A pending call can therefore be held and answered later.
- `plugin/common/StandardMessageCodec.ets`: `value instanceof Uint8Array` writes tag `UINT8_ARRAY`; decode returns `Uint8Array`. Binary payloads are supported both directions.
- `util/ByteBuffer.ets`: `checkWriteCapacity` grows at 1.5x with a 512-byte floor; the `buffer` getter returns `this.dataView!.buffer.slice(0, this.mByteOffset)`. A grown buffer is returned up to the written offset, so a large payload is not truncated.
- `plugin/common/EventChannel.ets`: `setStreamHandler`, `onListen`/`onCancel`, `EventSink.success`/`error`. Push-only; it carries no reply.

## 2. Channel reuse decision

**Do not reuse an existing named channel. Add one dedicated channel and reuse the
existing registration and teardown pattern.**

Evidence:

1. `qflistudio/nginx` is a five-method lifecycle ABI keyed on a single module-level `activeToken` (`NginxBridge.ets`). The broker resource exchange has a different identity model and a different lifetime. Overloading this channel would make one `activeToken` carry two lifecycles.
2. `qflistudio/platform` is owned on the Dart side by shared core (`runner_service.dart:51-52`) and carries `openUrl` semantics that this review is explicitly not allowed to change. `MethodChannel.ets` states "Identically named channels will interfere with each other's communication." A product-side Dart channel with that same name would collide with the shared-core one.
3. `libqfli_web_cdp_transport.so` is a raw devtools socket client with a fixed endpoint. It is imported only by `ohos/entry/src/ohosTest/ets/testability/SelfCdpProof.ets`, so it is test-only, and its API has no notion of an ArkWeb pending response.

Reuse what is safe: the `MethodChannel` + `setMethodCallHandler` pattern, registration inside `EntryAbility.configureFlutterEngine`, and `onDestroy` teardown as `stopActiveNginx()` already does.

## 3. Minimum channel schema

Channel name: `qflistudio/web_owned_resource`. Codec: `StandardMethodCodec`
(native default) paired with Dart `MethodChannel` default. One channel, both
directions.

### Dart to native

| Method | Arguments | Result |
| --- | --- | --- |
| `session.prepare` | `sessionId`, `origin`, `limits{maxInFlight, maxResponseBytes, maxRetainedBytes, requestDeadlineMs}`, `policy{csp, navigationAllowed}`, `entryUrl` | `{sessionId, accepted: true}` or error `DENIED` |
| `session.release` | `sessionId` | `{sessionId, released: true}` |
| `lease.ack` | `sessionId`, `requestId`, `leaseId`, `deliveredBytes` | `{released: true}` |
| `lease.drop` | `sessionId`, `requestId`, `leaseId`, `reason` | `{released: true}` |

`origin` must be the same string the Dart session registered, because
`classifyOwnedResource` compares against the registered origin and rejects
anything else as `forbidden`. Native must not carry its own classifier: it passes
the intercepted URL and method through unchanged.

### Native to Dart

| Method | Arguments | Result |
| --- | --- | --- |
| `request.fetch` | `sessionId`, `requestId`, `url`, `method` | `{leaseId, status, headers, body}` where `body` is `Uint8Array`; or error `{code, message, details}` |

`request.fetch` returns a held `MethodResult`. Native fills the pending ArkWeb
response only after the Dart reply arrives or its own deadline elapses.

Error codes Dart must emit, and native must treat as a terminal response:

| Code | Meaning | Native maps to |
| --- | --- | --- |
| `STALE_SESSION` | `sessionId` is not the live session | status 410 |
| `UNKNOWN_REQUEST` | `requestId` already settled | status 410 |
| `LEASE_MISMATCH` | requested lease is no longer held | status 410 |
| `BROKER_REJECTED` | broker returned a non-2xx `OwnedPreviewResource` | that `statusCode` |

Note: the broker already returns non-2xx as `OwnedPreviewResource` values, not
exceptions (`_error` at `:294`). So `BROKER_REJECTED` should carry the broker's
`statusCode` and `headers`, and native should construct the ArkWeb response from
them. That keeps 400/403/405/413/415/502/503/504 on one path.

### Identity rules

| Field | Owner | Rule |
| --- | --- | --- |
| `sessionId` | Dart | Generated by Dart before `session.prepare`. Non-repeating across the process. Native treats it as opaque. |
| `requestId` | Native | Monotonic per session, never reused. Native keys pending responses by it. |
| `leaseId` | Dart | Generated when `broker.fetch` resolves. One `leaseId` maps to exactly one `OwnedPreviewResource` instance. |

## 4. Lifecycle bound to the broker

### Prepare

1. Dart resolves the project configuration, rejects every proxy, and picks the
   origin. Then it constructs `OwnedPreviewResourceBroker(origin: origin, ...)`.
2. Dart calls `session.prepare` with that origin and the broker's own limits.
3. Native applies blocking and restrictive Web settings **before** loading
   `entryUrl`. No page load precedes this step.
4. Only after `prepare` succeeds does Dart mount. If `prepare` fails, Dart calls
   `broker.dispose()` and reports no session.

### Request

1. Native intercepts, holds the pending response, generates `requestId`, and
   calls `request.fetch`. It must return from the handler immediately; the
   handler runs on the platform thread.
2. Dart validates that `sessionId` is live, then calls
   `broker.fetch(url, method: method)`. The broker again enforces origin, method
   and limits, so a forged URL cannot bypass `classifyOwnedResource`.
3. Dart stores the returned `OwnedPreviewResource` under a fresh `leaseId` and
   replies with `{leaseId, status, headers, body}`.
4. Native validates `sessionId` and `requestId` against the live session, fills
   the pending response, marks it ready, and then sends `lease.ack`.

### Timeout ordering

The broker's own `requestDeadline` defaults to `kOwnedPreviewRequestDeadline`
(5 s) and is clamped by the constructor to `<= 5 s`. Native must use a pending
deadline `N` strictly greater than the broker deadline `D`, for example
`N = D + 1 s`.

Reason: the broker already turns a deadline into a 504 `OwnedPreviewResource`
through `_cancel`. If native's deadline were shorter or equal, native would
synthesize its own timeout and race the broker's, producing two different
answers for one request. With `N > D`, the broker's answer always arrives first
and native's deadline is only a last-resort backstop.

### Late bytes

A Dart reply for an already settled `requestId` must not reach the Web
component. Native must instead send `lease.drop{sessionId, requestId, leaseId,
reason: "LATE"}` so Dart can call `release()` on that lease. Without this the
Dart-side `_retainedBytes` stays held until session stop, and a latched
`retained-byte limit reached` 503 would follow, which is the failure class
already fixed in the broker.

Dart must treat `lease.drop` for an unknown or already released `leaseId` as a
no-op, because `release()` is already idempotent (`:38-45`).

### Stop

1. Dart calls `session.release`, then `broker.dispose()`.
2. `dispose()` turns every active operation into a 410 `OwnedPreviewResource`
   and releases every lease. Dart must still answer the currently held
   `request.fetch` calls with those 410 values, so native can finish every
   pending response instead of leaving the Web component waiting.
3. Native stops intercepting and removes the component.
4. `EntryAbility.onDestroy` must call the new bridge teardown the same way it
   calls `stopActiveNginx()`. Ability teardown and the Dart stop path must reach
   the same cleanup.

### Replacement

`session.prepare` with a different `sessionId` while one is live must be rejected
with `DENIED unless` the old session was released first. Dart must `dispose()`
the old broker before preparing a new one. Native must answer any `request.fetch`
carrying a stale `sessionId` with `STALE_SESSION` rather than letting it fall
through to default network loading.

## 5. Byte ownership and bounds

Copy semantics. `StandardMessageCodec.writeBytes` copies into the native buffer,
and `ByteBuffer.buffer` slices a copy for the reply, so:

- Native owns its copy the moment the reply is decoded.
- Dart owns the lease until `lease.ack`, `lease.drop` or session stop.
- Dart retains at most `maxRetainedBytes` across leases, enforced by the broker.

Native's own retained bound is therefore already implied:
`maxInFlight * maxResponseBytes`. Native must additionally reject any reply whose
`body.length` exceeds `maxResponseBytes` and treat it as a failed transfer that
still produces an explicit response.

Per-message cost: one full-size copy on the native side per reply, plus the
broker's own copy. No size limit is documented in
`plugin/common/BinaryMessenger.ets` (`send(channel, message, callback?)`), but no
limit being documented is not a proof of no limit. The largest message this
contract can produce is one `maxResponseBytes` body, default `2 << 20`.

## 6. Shared core editor gap

The editor entry cannot be covered by a product-owned session factory. The
actual call chain is:

```
editor_page.dart:1473  StudioProfile.current?.webPreviewFactory?.call(projectPath)
editor_page.dart:1490  targetUrl = server.url  |  server.urlForFile(entryOverride)
editor_page.dart:1501  await RunnerService.openUrl(targetUrl)
runner_service.dart:226-238  _ohosChannel.invokeMethod('openUrl', {'url': url})
EntryAbility.ets openUrl  isOfflinePreviewUrl -> ohos.want.action.viewData
```

That last step always starts an external ability. A product session that returns
a well-formed loopback URL will therefore still open the system browser, and a
session that returns a fabricated URL to avoid that would break the real browser
path for every other caller.

`StudioProfile` exposes only `webPreviewFactory` (`:145-147`) and
`WebPreviewSession` exposes only `url`, `debugStream` and `stop`
(`:302-306`). There is no ownership or opener hook.

Two minimal hooks would close the gap. Either is enough; both are core changes
and are requested here, not made:

- **Hook A.** Add an optional capability interface, for example
  `abstract interface class WebOwnedPreviewSession { String get origin; }` in
  core, and have `editor_page.dart` skip `RunnerService.openUrl` when
  `server is WebOwnedPreviewSession`.
- **Hook B.** Add `Future<bool> Function(String url)? webPreviewOpener` to
  `StudioProfile`, defaulting to null. `editor_page.dart:1501` uses it when
  non-null and falls back to `RunnerService.openUrl` otherwise.

Hook A keeps the decision with the session object and needs no second product
field. Hook B keeps platform opening in the profile. Either way the existing
external `openUrl` handler and its diagnostics stay untouched, which is what the
prior review requires.

The Tools entry (`lib/pages/web_tools_page.dart:138-147`) is a separate path. It
calls the same channel directly, so it can adopt the owned session in the same
slice without a core change. A Tools-only slice must state that narrower scope
and must not claim the editor now uses owned preview.

## 7. Requested native C API

**None is required for this slice.** The resource path is ArkTS plus Dart:

- interception and response filling are ArkWeb ArkTS APIs,
- the fetch itself is the existing Dart `HttpClient` path inside the broker,
- the channel is `MethodChannel` over the existing engine messenger.

The existing `QFLI_WEB_CDP_*` C API is not reusable here. It opens only
`webview_devtools_remote_<pid>` with `SO_PEERCRED` checks and caps transfers at
64 KiB; it is a devtools socket client, not a resource transport.

One case would require a new C API: if byte transfer must bypass the JS heap to
avoid the copy in section 5. That would need a shared-memory or ring-buffer ABI
with its own lifetime and teardown contract, which is a larger change than this
slice. This document does not request it.

## 8. Minimal missing behavior, in order

1. **Dart session owner.** A class that constructs the broker, calls
   `session.prepare`, answers `request.fetch`, and maps leases. Nothing in
   production constructs a broker today: `web_runtime.dart:47` selects Nginx or
   WebDevServer only.
2. **Native bridge file plus registration.** A new ArkTS module modeled on
   `NginxBridge.ets`, registered in `EntryAbility.configureFlutterEngine`, with
   teardown called from `onDestroy`.
3. **A production Web owner.** `ohos/entry/src/main/ets/pages/Index.ets:69`
   mounts only `FlutterPage`, so no owned Web component exists.
4. **Static owned mode prerequisites** (both are pre-existing gaps named by the
   prior review, unchanged by this document):
   - `web_project_config.dart:57-69` still accepts literal-loopback proxy
     targets. Owned static mode needs every proxy rejected before binding.
   - `web_dev_server.dart:245-247` injects the bridge script into `.html`/`.htm`
     GET responses, and that script posts to `/__webforge/debug` (`:567`) and
     opens `EventSource('/__webforge/events')` (`:576`). Static owned mode must
     serve without injection. `nginx_session.dart:86` starts `WebDevServer` as
     its middleware, so changing only the direct entry leaves a second path.
5. **Explicit editor hook** (section 6) if the editor entry is in scope.
6. **Session tests** for stale session, unknown request, duplicate
   acknowledgement, late reply dropping a lease, stop during fetch, and
   replacement.

## 9. Non-claims

- I did not run any test. Nothing here asserts that current suites pass.
- The `request.fetch` byte capacity is unverified at runtime. The codec and
  `ByteBuffer` paths are verified by reading; the platform message limit is not.
- ArkWeb interception, pending response readiness, `blockNetwork` behaviour with
  synthetic responses, service-worker and cache behaviour, and teardown are all
  unverified. They need a real ArkWeb run and are outside this review.
- The schema is a proposal. It is not an agreed contract until the author and the
  coordinator accept it.
- No acceptance criteria are invented here. The only acceptance statements are
  the ones that must come from an actual ArkWeb run.
