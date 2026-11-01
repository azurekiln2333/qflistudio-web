# Independent source review: owned preview to ArkWeb

Date: 2026-10-26. Scope: source inspection only. No SDK, Dart, Flutter, browser, native, device or Job command was run. Product files were not edited. This review does not consume or replay a runtime grant.

## Concrete finding

The broker has no production consumer. Production OHOS still opens the system browser. The smallest next integration is an owned static preview vertical slice: one production Web owner, one native/Dart resource channel, a Dart session that owns the broker, and an explicit product entry. It must include static runtime configuration before any page loads. Adding a Web widget alone cannot establish the intended boundary.

The proposed Tools entry is real, but it is not the editor entry. A Tools-only slice must state that narrower scope. It cannot claim that the editor now uses owned preview.

## Actual entry paths

- `lib/main.dart:37` assigns `webProfile.webPreviewFactory = WebRuntime.start`.
- `lib/services/web_runtime.dart:47` loads project configuration and selects embedded Nginx or WebDevServer. It does not construct an owned broker or Web component.
- `lib/pages/web_tools_page.dart:138` opens the Tools session URL through `qflistudio/platform.openUrl` on OHOS.
- Shared core `../qfli_studio_core/lib/editor/editor_page.dart:1473` independently calls the profile factory. At `:1490` it resolves an explicit current-file URL. At `:1501` it calls `RunnerService.openUrl`.
- Shared core `../qfli_studio_core/lib/services/runner_service.dart:226` forwards that URL to the same platform channel. It catches platform and missing-plugin failures. A product-owned session factory alone cannot replace this final opener.
- `ohos/entry/src/main/ets/entryability/EntryAbility.ets:61` checks `isOfflinePreviewUrl` and starts an external viewData ability. This is an external browser path.
- `ohos/entry/src/main/ets/pages/Index.ets:69` mounts only FlutterPage. There is no production owned Web component.

The current review does not authorize shared-core edits. Covering the editor requires an agreed core hook or another explicit integration design. Silently repurposing the general openUrl handler would also alter unrelated callers and would conflict with the existing plan to preserve that handler.

## What existing code actually provides

`entryability/NginxBridge.ets:58` provides engine messenger registration and Dart-to-native MethodCall handling. `lib/services/nginx_host.dart:122` provides Dart invocation and lifecycle polling examples. Neither contains native-to-Dart resource callbacks, pending ArkWeb responses, byte delivery, response acknowledgements or leases. They are channel registration patterns, not an existing resource transport.

`ohos/entry/src/ohosTest/ets/testability/pages/Index.ets` provides test-only Web/controller/interception syntax. `testability/CatalogHarness.ets:136` synchronously returns source strings. At `:159` it constructs WebResourceResponse and sets status, MIME, encoding and headers. It does not call setResponseIsReady and does not prove asynchronous delivery. Its null return for data/blob/about is a test harness behavior, not a production policy contract.

`lib/services/owned_preview_policy.dart` supplies the shared classification, navigation and CSP decisions. `lib/services/owned_preview_resource_broker.dart:38` supplies releaseable response ownership and `:172` disposal. Native code must consume these outcomes without implementing a competing origin classifier.

## Minimum missing protocol and lifecycle

1. Prepare an exact session identity and origin before mounting Web. Establish network blocking and restrictive settings before project navigation.
2. Return a pending response from interception. Deliver each request to Dart with sessionId and requestId. Native code must never synchronously wait for Dart on the UI thread.
3. Dart classifies the unchanged URL/method and fetches through the session broker. Transfer bytes, status and generated headers through an explicitly defined binary codec. Preserve response bytes rather than decoding arbitrary files as UTF-8.
4. Native code validates the matching live session/request, fills the pending response, then marks it ready. Reject foreign, stale or duplicate replies.
5. Acknowledge the matching response lease after native ownership is established. Define whether native copies or retains bytes. Bound native retained bytes as well as Dart retained bytes.
6. Give every failed, denied, timed-out or cancelled HTTP(S) request an explicit response. Never fall through to default network loading.
7. Stop accepting new work on stop/replacement. Complete pending responses, release their leases and remove the component. Ignore late replies by identity. Ability teardown must trigger the same cleanup.

An EventChannel is not established as necessary by existing code. Choose it only if the lifecycle event contract needs it. A method callback plus explicit acknowledgement can carry the resource exchange, but its codec and threading behavior still require verification against the installed Flutter OHOS bridge.

## Static runtime prerequisite

`WebProjectConfig.validateOffline` currently accepts literal-loopback proxy targets (`lib/services/web_project_config.dart:56`). The proposed static owned mode requires rejection of every configured proxy, including those targets. Validate before starting either server.

`WebDevServer` unconditionally injects its browser bridge into HTML GET responses (`lib/services/web_dev_server.dart:247`). That script posts debug messages (`:567`) and opens EventSource (`:576`). The owned static policy blocks these channels. Disabling injection is therefore part of this slice. Nginx also starts WebDevServer as its middleware (`lib/services/nginx_session.dart`, startWithHost), so changing only the direct WebDevServer entry would leave a second path.

Keep this mode explicit. Existing external preview behavior and its diagnostics have different contracts.

## Reusable tests and evidence boundary

- `test/owned_preview_policy_test.dart`: exact origin, method, path, default-port, navigation and CSP cases.
- `test/owned_preview_resource_broker_test.dart`: request limits, deadlines, leases, cancellation and redirects. These are host-side transport checks.
- `test/web_preview_current_file_test.dart`: root and current-file URL behavior.
- `test/nginx_host_test.dart`: channel/lifecycle mocking patterns.
- `test/web_dev_server_test.dart`: HTML injection, SSE, browser debug and proxy fixtures. Add meaningful assertions that the new explicit static mode omits injection and rejects proxies before binding.

Add session tests for stale replies, duplicate acknowledgement, failed transfer, stop during fetch and replacement. A host test cannot validate ArkWeb interception or UI-thread behavior.

Actual ArkWeb acceptance remains required for pending responses, binary delivery, blockNetwork with synthetic responses, navigation and popup/download/permission restrictions, cache/service-worker behavior and teardown. Debugger activation and same-app CDP remain a separate later slice. This report makes no clean-core or runtime-pass claim. Current shared-core WIP remains outside this review.

