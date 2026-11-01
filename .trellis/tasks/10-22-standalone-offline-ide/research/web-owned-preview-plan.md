# Product-owned OHOS preview and local CDP plan

Reviewed **2026-10-23, Asia/Shanghai**. This is an R8/R10 implementation proposal,
not delivered debugger or offline-browser acceptance. Web HEAD remains
`e0f81a56230ec27890b67eb9ac0c1df71a805c71`; observations also include current
uncommitted Web repairs. The shared debugger contract is
`f8edb0424e40afc5e8dba6a874cb240f467ffd7b`.

Only this research file was written. No Flutter, browser, build, device, HDC,
port-forward, package-install, or source-changing operation was performed.

## Decision

Implement an **application-owned ArkWeb component**, a restricted resource broker,
and a product `StudioDebugger` adapter. Keep Flutter and the controlled view in
the same application. Use the documented **default abstract Unix-domain CDP
socket**, reached by a small product native client, rather than opening a CDP
TCP listener or requiring a desktop/HDC connection.

This is a concrete implementation direction with two early acceptance gates:
same-application Unix-socket access/security and ArkWeb's actual offline behavior.
Neither gate has been passed by the existing catalog runner. Failure of a gate
requires an explicit implementation change; it does not establish that Web
debugging is impossible. Do not publish a safe production debugger until those
gates pass, and do not substitute ordinary Run when Debug fails.

The first debugger scope is saved, static HTML/HTM with authored local JS/MJS,
real breakpoints and control of the main page. Local API proxies, POST bodies,
WebSockets, Service Workers, worker debugging, transpilation and source maps are
separate extensions. Unsupported configurations fail before loading project code,
without changing project files. This limited scope must be visible in the product;
it must not silently replace existing general-preview behavior with partial parity.

## What the evidence establishes

| Evidence inspected | Established fact | Limit |
| --- | --- | --- |
| `EntryAbility.ets`, `qflistudio/platform.openUrl` | Current OHOS HTML preview starts `ohos.want.action.viewData`, handing the URL to another ability. | No returned owned Web component, target identity or CDP lifecycle. |
| `ohosTest/.../TestAbility.ets` and `testability/pages/Index.ets` | A test-only ability enables ArkWeb debugging and owns an incognito `Web` with `onInterceptRequest`. | Production does not import this ability; do not repurpose the agreement reader as preview evidence. |
| `CatalogHarness.ets` | Test responses return exact packaged HTML and deny unrecognized HTTP resources. | Its `data:`/`blob:`/`about:blank` branches return null; the harness does not prove complete network isolation. |
| `research/ohos-481-final.device.json` and `.json` | The saved actual ArkWeb 144 run uses HDC `tcp:9222` to device `tcp:9222`, and reports 474/481. | This is host-to-test TCP attachment, not same-app Unix access, a Debugger-domain test, or a passing catalog result. |
| Installed ETS/native SDK metadata | Both are API **26**, version **26.0.0.105**. | Typings and native headers do not prove runtime permissions or kernel behavior. |
| Current `WebProjectConfig` and serving code | `validateOffline()` already rejects nonliteral/nonloopback proxy hosts before serving; CSP is already applied. Early-head bridge injection is now present. | These repairs supersede those gaps in the earlier readiness report; this slice did not validate them. A system browser is still outside product interception. |
| Frozen `debug_session.dart` and core spec | Save-first launch, actual breakpoint locations, pause tokens, bounded immutable snapshots and actual cleanup are contractual. | Core provides neither an ArkWeb adapter nor native acceptance. |

Current source pointers: [production ability](../../../../ohos/entry/src/main/ets/entryability/EntryAbility.ets),
[native root page](../../../../ohos/entry/src/main/ets/pages/Index.ets),
[test ability](../../../../ohos/entry/src/ohosTest/ets/testability/TestAbility.ets),
[test Web page](../../../../ohos/entry/src/ohosTest/ets/testability/pages/Index.ets),
[test resource harness](../../../../ohos/entry/src/ohosTest/ets/testability/CatalogHarness.ets),
[host driver](../../../../scripts/run_ohos_catalog.py),
[current configuration](../../../../lib/services/web_project_config.dart),
[serving and injection](../../../../lib/services/web_dev_server.dart),
[core contract](../../../../../qfli_studio_core/lib/services/debug_session.dart),
[core executable conventions](../../../../../qfli_studio_core/.trellis/spec/frontend/offline-debugger.md).
The earlier [readiness report](web-panels-debug-readiness.md) remains useful for
panel ownership, but its proxy-policy and late-head-injection observations are
historical rather than the current worktree state.

## CDP transport and listener security

### What is verified from primary sources

1. `setWebDebuggingAccess(boolean)` exists from API 9; default debugging is off.
   The official debugging guide describes a domain socket named
   `webview_devtools_remote_<application PID>` and forwards it with
   `localabstract:`. The PID is explicitly the process hosting the Web component.
   This identifies an abstract socket, not a filesystem socket path. [S1]
2. The API 20 overload takes `(boolean, port)` and no bind address. The installed
   SDK explicitly says specifying a port creates a TCP server socket **instead
   of** a Unix-domain socket; valid explicit ports are 1025 through 65535.
   Neither the signature nor this SDK comment promises a loopback bind. [S2, L1]
3. The official guide describes that TCP overload as wireless debugging between
   tools and device on the same LAN, using the device's LAN IP. Therefore
   `setWebDebuggingAccess(true, 9222)` cannot be accepted as a documented
   localhost-only security boundary. The existing host forward's localhost URL
   says nothing about the device listener's bind address. [S1]
4. The public `web_webview` NAPI implementation forwards enable/port to NWeb,
   maintains static enable/port state, and exposes no bind-address control there.
   It also returns early when `web.debug.devtools` is set. This makes ordinary
   method return insufficient evidence of the desired listener state. [S3]
5. The installed native SDK provides `AF_UNIX`, `sockaddr_un`, `getpid()`,
   `getuid()` and `SO_PEERCRED`. The bundled Dart SDK documents Unix sockets for
   Linux, macOS and Android, without documenting OHOS. Direct Dart Unix support
   on this Flutter/OHOS build is consequently **unproven**, not assumed absent.
   A product native connector avoids depending on that undocumented Dart path.
   [L2, L3]

The public OpenHarmony CEF snapshot contains a generic remote-debugging factory
binding `127.0.0.1`; its repository head is from January 2024. The public Chromium
patch also adds OHOS support for reading Unix peer credentials. Neither shows
the current ArkWeb 144 API 20 listener or its current peer-authorization rule.
These are useful implementation clues, **not** evidence that the installed
engine binds TCP only to loopback or permits a same-UID CDP peer. [S4, S5]

### Proposed no-listener connector

Enable debugging with the one-argument API only during an explicit Debug lease.
The native connector computes its own name from `getpid()` and connects to
`AF_UNIX/SOCK_STREAM`, using a leading NUL and the exact length for the abstract
address. It does not accept a caller-provided path, PID, hostname or port; it does
not scan `/proc`, enumerate other applications, bind, listen or create HDC forwards.
Do not use `strlen()` over the leading-NUL address or treat it as a pathname.

The connector returns opaque, generation-checked handles. A nonblocking raw-byte
C ABI is enough; Dart owns bounded HTTP discovery, WebSocket framing and CDP:

```c
int64_t qfli_web_cdp_open_self(void);  /* positive owned handle or negative errno */
int qfli_web_cdp_read(int64_t handle, uint8_t *buffer, size_t capacity);
int qfli_web_cdp_write(int64_t handle, const uint8_t *bytes, size_t length);
int qfli_web_cdp_close(int64_t handle);
```

Specify `read`: positive byte count, zero EOF, `-EAGAIN` pending; `write`: actual
accepted byte count or negative errno, including partial writes. Cap each operation
at 64 KiB, use nonblocking connect/read/write, and make Close idempotent. Never
block the Flutter UI isolate or ArkUI callback while waiting for CDP. Dart's pump
has a cancellable short timer and stops independently of an outstanding CDP RPC.
Native handles are not public file descriptors and an old handle cannot close a
later connection. If another transport is chosen, retain these ownership rules.

Use a bounded HTTP GET of `/json/list` over this socket, then open a second
self-socket connection for the selected page WebSocket upgrade. Accept only a
relative `/devtools/page/...` path obtained from the selected target; discard any
returned host/port and reject credentials, fragments and unexpected paths. Validate
HTTP upgrade status, `Sec-WebSocket-Accept`, framing, lengths, close/ping/pong and
fragmentation. Mask client frames, do not negotiate compression, and cap a complete
CDP message at 1 MiB. Add an explicit retained build dependency for SHA-1/handshake
validation if needed; no runtime download is involved. Avoid an improvised adapter
pretending that a native byte stream is a `dart:io Socket`.

### Required first target proof

Before broader adapter work, a disposable product-owned bootstrap must establish:

- A connection from the **application's own native client** reaches its default
  abstract socket with HDC disconnected/no forwards. Record engine, API, ABI,
  product HAP identity, own PID/socket name and protocol response; no private
  device identifiers are needed.
- Exactly one target matches a cryptographically random per-launch bootstrap URL.
  `Page.getFrameTree` confirms that same main-frame URL. Never attach to the first
  target, the agreement page, or the catalog ability.
- `Runtime.enable`, `Debugger.enable`, an actual breakpoint/pause/resume/step and
  target removal work through this same-app connector. Schema presence alone is
  insufficient.
- Determine the current socket's peer authorization: establish a documented or
  current-source-backed same-UID rule and, where a controlled second app is used,
  require an unrelated UID to be denied. Kernel credentials being readable does
  not establish that ArkWeb checks them. Also verify no CDP TCP listener exists
  during the Unix-only session and the socket disappears after disabling it.
- If the device has a system-forced debug setting, listener creation/removal or
  cross-UID restrictions cannot be established, report that exact result. Do not
  mark the connection secure or ship a TCP fallback. Session tokens protect
  product channels/target selection; they cannot authenticate ArkWeb's separate
  debugger socket.

The official release-version warning is relevant because this product is an IDE:
an explicit, short-lived debugger is intentional, but its exposure still needs
the above concrete proof. This review found no documented `debuggable:true`
manifest prerequisite and no proof that enabling the API is restricted to debug
HAPs. Test the actual release artifact. [S2]

This is a static, application-wide debugging switch, not an API that authenticates
or enables only one Web target. Serialize Debug with any unrelated Web component,
including the agreement reader, so it is not present during the debug lease.
Choosing the correct target in Dart prevents wrong-target control but does not
hide other targets from a peer that can reach the socket. The static destroy-mode
and service-worker APIs likewise require application-level coordination. [S2, S3]

## Owned preview and offline boundary

Use the existing Flutter `EntryAbility` and root ArkUI page. Mount one separate
`OwnedWebPreview` component while Flutter remains alive. Native visibility may
switch between preview and editor without removing the controlled Web component;
Stop removes it. A breakpoint can reveal the Flutter editor while preserving the
paused target. Opening a second project replaces/stops only the owned lease;
it must not attach to or stop another Tools/runtime owner accidentally.

For the first static mode, use all of these layers before loading project bytes:

| Layer | Concrete behavior | Evidence/acceptance limit |
| --- | --- | --- |
| Web network switch | Set `.blockNetwork(true)` from initial construction. | SDK describes blocking network resource loads. Actual compatibility with synthetic intercepted responses, WebSockets and worker paths must be measured. [S6, L1] |
| Resource interception | Every HTTP(S) resource returns an owned response. Return a pending `WebResourceResponse` with `setResponseIsReady(false)`, then populate bytes/headers/status and set ready true. Never return null for unrecognized HTTP(S), callback errors, cancellation or timeout. | Official APIs support returned responses and asynchronous readiness; `onInterceptRequest` cannot obtain POST bodies. [S7, S8] |
| Broker | Permit GET/HEAD only for the **exact registered session origin**, including port. Dart fetches only that origin's existing runtime using a dedicated `HttpClient`, `findProxy = (_) => 'DIRECT'`, `followRedirects = false`, identity encoding, bounded bytes and deadline. All other URLs receive an explicit 403; unsupported methods receive 405. | Web itself need not make a network request. An ArkUI interception callback must not synchronously wait for Dart. |
| Config | Reuse current physical-root resolution and `validateOffline()`. For initial static Debug, reject any proxy rule, including loopback rules, before starting/attaching. | This is a declared first-version restriction; later body/stream/proxy support may reuse the existing loopback-only policy. Preserve configuration bytes. |
| Headers | Preserve the existing offline CSP baseline and enforce an additional policy containing `connect-src 'none'; worker-src 'none'; frame-src 'none'; form-action 'none'`. Apply to every generated HTML response, including errors/bootstrap. | Use a separate intersecting CSP policy or replace the parsed directives; appending duplicate directives inside one policy can retain the earlier value. This version blocks page XHR/fetch/WebSocket APIs, frames and workers. CSP and engine blocking require actual target acceptance. |
| Navigation | `onOverrideUrlLoading` allows only validated owned-session page URLs; reject external/custom/file/resource navigation. Interception rechecks all resource URLs and redirects. | The override callback explicitly omits POST, so it is not the sole policy boundary. [S7, L1] |
| Auxiliary behavior | Do not create popup controllers or start download handlers/external abilities. Deny page permissions, geolocation and native file access; expose no JS-to-native filesystem/CDP proxy. | Test popup, download, custom-scheme and permission paths on the target. |
| Storage/workers | Start incognito with a fresh session origin. Do not reuse a prior page's persistent worker/storage state. Workers are unsupported in v1. | Incognito is not itself a network-denial guarantee. [L1] |

An exact session origin can remain the existing loopback runtime URL, so relative
assets and `urlForFile` keep their canonical URL behavior. Intercepted resource
requests are forwarded only by trusted Dart code; the Web engine remains blocked.
Use one broker path for bootstrap, successful resources, 404s and blocked requests.
Do not allow every loopback port: another local app/service is outside this lease.
Reject userinfo, malformed/ambiguous URLs, unexpected schemes and encoded path
escapes; retain the existing canonical-path and symlink protections at the server.

Set an initial broker bound of 16 requests in flight, 2 MiB per static response,
16 MiB retained aggregate bytes and a 5-second request deadline. Return a visible
resource error when exceeded. Debug additionally caps each authored HTML/JS text
at 128 KiB so an escaped source response fits the 1 MiB CDP-message bound.
Long-lived SSE and WebSocket streams are not buffered
to completion. The initial mode disables the injected browser bridge and live
reload rather than hanging on its SSE endpoint. A later normal-Run parity slice
can implement an explicit native reload notification and streamed resources;
Debug should stop/relaunch after a source change until exact reload identity exists.

`onInterceptRequest` alone does **not** establish full offline isolation. The
current official description covers redirects and resource responses, but this
review found no specific guarantee covering WebSocket handshakes, DNS/preconnect,
all worker traffic or all external-intent paths. `WebSchemeHandler` and the
application-global `setServiceWorkerWebSchemeHandler` are available from API 12
for later body/worker interception. Their existence does not prove WebSocket
coverage; a global service-worker handler must not silently affect unrelated
Web components. Do not turn off `blockNetwork` merely to make a failing fixture
work. [S7, S9, S2]

The offline acceptance must record zero forbidden connection attempts, not just
an error returned by an unreachable Internet address. Use controlled local/LAN
sentinels plus browser/request evidence for navigation, image/CSS/font/script,
redirect, fetch/XHR, WebSocket, Worker/SharedWorker/ServiceWorker, blob/data-created
code, iframe, beacon/form, popup/download and custom schemes. Test with transport
available as well as disconnected. If a path bypasses the block and headers,
keep that path unsupported and repair enforcement before claiming R10 completion.

## Narrow product file boundary

The following are proposed paths, not edits made by this review.

| Product file | Responsibility |
| --- | --- |
| `ohos/entry/src/main/ets/entryability/WebPreviewBridge.ets` (new) | Validate channel payloads, own the one Web lease/controller state, handle callbacks, publish lifecycle/policy events, and disable debugging on teardown. |
| `ohos/entry/src/main/ets/pages/OwnedWebPreview.ets` (new) | Actual incognito Web, fixed policy attributes, pending resource responses, navigation/permission/popup handling and component detach acknowledgement. |
| `ohos/entry/src/main/ets/pages/Index.ets` | Mount/show/hide the owned component with Flutter retained; remove on confirmed Stop. |
| `ohos/entry/src/main/ets/entryability/EntryAbility.ets` | Configure the preview channel and call its final teardown. Resolve registered preview URLs to the owned component, retaining generic URL-opening behavior for unrelated app links. A registered preview failure must return an error, never fall through to the system browser. |
| `ohos/entry/src/main/cpp/web_cdp_transport.cpp` (new), `CMakeLists.txt` | Build a separate small shared FFI library providing the self-socket C ABI; no Nginx ABI or engine changes. |
| `lib/services/owned_web_preview.dart` (new) | Product lease, native method/event protocol, bounded resource broker, URL ownership and actual cleanup. Both editor and Tools callers use the same native lease rules. |
| `lib/services/ohos_cdp_transport.dart`, `cdp_wire.dart` (new) | FFI byte pump, bounded HTTP/WebSocket protocol and cancellable CDP request/event dispatch. No arbitrary endpoint attachment API. |
| `lib/services/web_debugger.dart`, `web_debug_session.dart` (new) | Frozen `StudioDebugger` contract, source identity, breakpoint state, pause generations, real frames/commands/output and cleanup. |
| `lib/services/web_runtime.dart`, `web_dev_server.dart`, `nginx_session.dart` | Explicit owned/raw serving option with console injection disabled; return/register the product-owned wrapper on OHOS. Keep public factory signature compatible. Default/selected-file URL logic and real engine identity remain authoritative. |
| `lib/main.dart` | Supply the accepted product debugger and owned preview composition. Do not install an adapter merely because an API number is high enough. |
| `pubspec.yaml` / lock, if needed | Explicit build-time dependency for an audited WebSocket handshake implementation; no network requirement in the installed app. |

No production import of `ohosTest`, no changes to catalogs or agreement-reader
behavior, no new exported ability, no shared-core patch in this product slice,
and no native executable installation are needed by this direction.

## Public channel payloads

Proposed channel: `qflistudio/web_preview`; events:
`qflistudio/web_preview/events`. StandardMessageCodec binary bytes must be verified
on the actual OHOS Flutter bridge. Each request/event contains `schemaVersion: 1`
and an unpredictable `sessionId`; native events also carry an increasing `sequence`.
Reject stale or unknown IDs before changing controller/runtime state.

| Method / direction | Payload | Result |
| --- | --- | --- |
| `prepare`, Dart → native | `{schemaVersion, sessionId, origin, bootstrapUrl, mode: 'staticPreview'|'staticDebug'}` | `{sessionId, prepared: true}` after validation only. No project code loaded. Origin must be the exact runtime registered by this Dart owner. |
| `open`, Dart → native | `{schemaVersion, sessionId, url}` | `{sessionId, webId, attached: true}` after its own controller attaches to the bootstrap. Debug mode enables only the one-argument socket API. |
| `resource`, native → Dart callback | `{schemaVersion, sessionId, requestId, url, method, headers, isMainFrame}` | `{requestId, status, reason, mimeType, encoding, headers, body: Uint8List}`; bounds checked on both sides. No native path/PID/CDP access is exposed to page code. |
| `navigate`, Dart → native | `{schemaVersion, sessionId, url}` | Dispatch acknowledgement after policy validation; a later lifecycle event reports load/failure. Debug uses this only after CDP setup and breakpoint installation. |
| `present`, Dart → native | `{schemaVersion, sessionId, visible: bool}` | Acknowledgement; hiding preserves the target. |
| `stop`, Dart → native | `{schemaVersion, sessionId}` | Stop-request acknowledgement, **not** proof of cleanup. |
| `poll`, Dart → native | `{schemaVersion, sessionId}` | `{state, componentDetached, debuggingDisabled, cleanupError?}`; only a fully cleaned session becomes `closed`. |

Events: `attached`, `load`, `navigationBlocked`, `resourceBlocked`, `console`,
`renderExited`, `stopping`, `closed`, `failure`. Include only bounded data needed
for the UI; URLs have credentials stripped, console text is capped, and errors
contain stable code plus message. Native `console` is the ordinary-preview source;
Debug uses CDP console events to avoid duplicates. No event includes a source-root
filesystem listing, debugger endpoint, native descriptor or arbitrary evaluation.

Proposed stable failure codes: `INVALID_ARGUMENT`, `STALE_SESSION`,
`PREVIEW_BUSY`, `PREVIEW_POLICY`, `PREVIEW_RESOURCE_LIMIT`, `PREVIEW_ATTACH`,
`CDP_CONNECT_SELF`, `CDP_PROTOCOL`, `CDP_UNSUPPORTED`, `SOURCE_CHANGED`,
`PREVIEW_CLEANUP`. Every partially created lease is cleaned before launch errors
are returned. Stream cancellation and method timeouts may not abandon a native view.

## Launch, commands and teardown

1. Validate canonical physical project/root/entry containment, including symlinks
   and aliases, before executing anything. Accept only an HTML/HTM entry in v1.
   Reject nonempty `documents` and unsupported `stopOnEntry` immediately. Check
   config/mode restrictions and capture an immutable, bounded manifest of authored
   HTML/JS source bytes from disk. The Debug broker must serve those captured
   sources or reject a changed/missing/previously unknown executable source; a
   watcher alone does not close a read-versus-edit race. No autosave or source write.
2. Acquire the product-owned lease; stop an earlier lease through its actual owner
   before replacement. Do not start a second runtime through `RunnerService`.
   Start the existing loopback runtime with raw authored HTML serving and register
   its exact origin. A Tools listener may continue only under its existing owner;
   it cannot be mistaken for this debugger's target.
3. Create the Web at an intercepted bootstrap URL containing the random session
   token, with policy already active and no project JS. Await controller attachment.
   In Debug mode enable default Unix debugging, connect the native client, select
   exactly that bootstrap target, and verify its main frame. Do not issue
   `Target.createTarget` or require browser-context creation; the native view owns it.
4. Enable actual required domains, subscribe before navigation, install requested
   URL breakpoints, then load the selected entry. Publish `pending` until a returned
   or `breakpointResolved` location has an authenticated project script/source.
   The first project script must not run during target discovery.
5. On `Debugger.paused`, advance generation, copy bounded call frames, and publish
   the pause token. On resume/step dispatch, invalidate it immediately and clear
   frames. A subsequent pause receives a new token. Unsupported commands, old
   tokens and unknown threads fail without changing execution. One main-page
   thread is advertised; worker threads are not synthesized.
6. `command()` completes at dispatch acknowledgement, not the next pause. A CDP
   command queue must not hold Stop behind `resume`, a pending breakpoint, a hung
   request or paused JavaScript. Keep native Stop and transport cancellation usable
   even if the renderer runs an infinite loop.
7. Stop first prevents new broker work/navigation, settles every pending resource
   response with a local error, and invalidates pause/script/handle state. Remove
   the component using API 20 `FAST_MODE`, confirm component detach and query the
   still-open self transport for owned target absence. Then disable default
   debugging, close native handles and confirm that reconnecting to the self
   socket fails; stop/release the backing runtime and subscriptions. Restore the
   application's configured destroy-mode policy after detachment. Only after these
   acknowledgements may `done` complete and a terminal snapshot be published.
8. `controller.stop()` only stops loading; it is not JS runtime destruction.
   `terminateRenderProcess()` affects every Web sharing that renderer, so it is
   an escalation only when this lease's exclusive renderer ownership is proven.
   A unique `sharedRenderProcessToken` prefers reuse rules, but does not document
   guaranteed isolation. Never kill the agreement reader or another owned session
   to manufacture cleanup. If cleanup cannot be proved, retain `stopping` with a
   cleanup diagnostic and retry; do not falsely publish `terminated`. [S2, L1]

Navigation/reload invalidates execution contexts, script/frame IDs, remote handles
and pause tokens. The first implementation restarts Debug after an authored source
change or root switch rather than continuing against stale disk bytes. Stop,
Dispose, Back, editor disposal, application background policy, ability destruction,
startup failure, transport loss and renderer failure must converge on one idempotent
cleanup owner. Backgrounding should stop the first-version debug lease; returning
does not silently relaunch it. Test that policy instead of relying on visibility.

## Authored source mapping

The raw owned-serving mode is essential: current production HTML injects a bridge
before authored scripts. Do not debug those changed bytes while pretending they
are the editor's physical source. In owned Debug, use CDP `Runtime.consoleAPICalled`
and exception events from initial attachment and serve unchanged authored HTML/JS.
Do not serialize/rewrite the DOM, normalize newlines or add sourceURL directives.

- Maintain an effective response URL → canonical physical file → exact delivered
  bytes/text digest table in the broker. Directory index and SPA fallback map to
  the **actual** served HTML file. Query/fragment aliases can share identity only
  when the delivered source matches. Bind the table to this session/navigation.
- Accept a `scriptParsed` URL only from the owned target/execution context and
  verify `Debugger.getScriptSource` against the broker's source/span. A URL or
  `sourceURL` comment is not proof of a project file. Anonymous/eval/blob/data,
  external, injected, transformed or unverifiable scripts remain real frames with
  `location: null`; do not jump to a similarly named local file.
- Standalone authored JS locations convert CDP zero-based lines/columns to core
  one-based physical positions. For ordinary inline scripts, retain
  `scriptParsed.startLine/startColumn/endLine/endColumn` and verify the exact
  HTML source span. Chrome's official frontend treats raw inline positions as
  resource coordinates and subtracts the origin offsets only when converting to
  script-relative source. Therefore do **not** add the inline start offset twice:
  physical HTML positions are raw resource positions plus one. `hasSourceURL`
  changes that frontend conversion; reject navigable mapping for that special case
  in v1 unless an explicit, tested source map exists. [S10, S11]
- Preserve CRLF, UTF-8 BOM handling and UTF-16 column semantics. Compare actual
  script text, not a server byte hash directly to CDP's `scriptParsed.hash`.
  Verify astral characters and first-line inline columns on ArkWeb itself before
  claiming exact HTML breakpoint locations.
- Request breakpoints by exact owned URL and `physicalLine - 1`, or by verified
  script ID where necessary. Only backend-returned/resolved locations can verify
  them. A nonexecutable line may remain pending or be rejected; never choose a
  nearby line locally. Refuse to map a backend resolution into a different root.
- CSS has no executable line breakpoints. TS/JSX, source maps, pretty printing and
  generated build-output→author-source mapping are unsupported until explicit
  contracts exist. A real backend frame without trustworthy authored source is
  still displayed with a null location.

## First truthful core capabilities

The production capability object is installed only after the corresponding native
acceptance, not inferred from API 26 or ArkWeb's version string:

```dart
DebugCapabilities(
  breakpointUpdate: DebugBreakpointUpdate.launchOnly,
  outputDelivery: DebugOutputDelivery.live,
  supportsPause: true,
  supportsStepInto: true,
  supportsStepOver: true,
  supportsStepOut: true,
  supportsDocumentSnapshots: false,
  supportsStopOnEntry: false,
  supportsStackFrames: true,
  supportsVariables: false,
)
```

Each true flag requires its own real target case. If a command is unavailable,
reduce the advertised provider capability before exposure or fail launch with the
specific unsupported backend; never show a fake successful action. Breakpoint
replacement after launch is explicitly unsupported in this first version.

`supportsLanguage` may accept `html` and `javascript` so a JS editor tab can launch
an HTML project; launch still requires an HTML/HTM entry. A direct JS-only entry
fails explicitly rather than generating an untracked wrapper. **C/core coordination
is required:** its current `_language` table maps JS/MJS but not HTML/HTM. Add that
mapping and permit the HTML entry through the shared controller under C ownership.
Do not make CSS appear executable to bypass the active-file language gate.

Publish complete immutable bounded snapshots, including output-only revisions.
Suggested bounds: 64 frames, 200 breakpoint results, 64 KiB console rolling tail,
4 KiB per rendered console record, and a bounded pending-RPC/event queue. Mark
truncation. `stdout`/`stderr` need not be invented for browser code; use the real
console/exception channel and leave `exitCode` null when ArkWeb has no program
exit code. Render CDP primitive values and supplied descriptions conservatively;
do not call page `JSON.stringify`, getters, `Runtime.evaluate` or
`callFunctionOn` to format output. No watches/evaluation or locals API is added.

## Acceptance sequence and ownership

| Stage | Required evidence | Owner boundary |
| --- | --- | --- |
| A: transport/security | Same-app Unix proof, unique bootstrap target, actual release artifact, no TCP listener, current peer rule, teardown/relaunch. | Web native/product. Do this before committing to a large CDP adapter. |
| B: owned offline static preview | Normal selected/default HTML, relative CSS/JS/binary assets, 404, exact root, policy errors, every forbidden-traffic class, no system-browser launch, stop/dispose/back/background. | Web product; preserve current-file/root behavior. Report the static limitations visibly. |
| C: real debugger | External JS and inline HTML breakpoints, returned/resolved locations, pause/resume/each step, real stack, exceptions/early console, CRLF/BOM/Unicode, stale tokens, unsupported snapshots, source changes, infinite-loop/paused Stop, transport loss and actual target cleanup. | Web adapter + frozen core contract. Host protocol tests are supplementary. |
| D: editor composition | HTML entry allowed, gutter breakpoint → native pause → correct source line, shared controls/capability gating, Output/Debug Console/Ports visibility, panel hide/reopen without lost subscriptions, repeated root/session switching. | C owns shared editor/widgets; Web supplies real sessions/telemetry. No duplicated panel store or debugger UI. |
| E: broader preview parity | Local proxy/body/stream/WebSocket/live-reload behavior with strict offline checks; workers only if deliberately supported. | Separate Web extension. Do not imply this from A–D. |

Use dedicated unit/protocol tests for URL ownership, malformed/bounded frames,
source mapping and stale-handle cleanup; then a small product integration fixture
through the actual OHOS page and Flutter editor. A mocked channel, manually POSTed
console message, host Chromium run, saved test-only catalog CDP session or a
successful HAP build cannot replace stages A–D. Observe the shared device/build
window before any later native action. This research acquired no such window.

R8 remains open until actual shared-editor debugger/panel composition is accepted.
R10's server-side loopback/CSP repairs can be credited independently; complete
owned-browser offline enforcement remains open until stage B's measured result.

## Primary references and reproducibility

Only official documentation, official SDK files and upstream implementation/protocol
sources were used for technical claims. All network sources were read on
2026-10-23. Pinned repository revisions prevent a later `master`/`main` move from
silently changing the evidence.

- **S1** — [OpenHarmony DevTools debugging guide](https://github.com/openharmony/docs/blob/f41b9345badd47c7ab0c263344cd7f4b5a549afb/en/application-dev/web/web-debugging-with-devtools.md): default domain-socket/PID convention, `localabstract` forwarding and API 20 LAN wireless-debug workflow.
- **S2** — [OpenHarmony WebviewController reference](https://github.com/openharmony/docs/blob/f41b9345badd47c7ab0c263344cd7f4b5a549afb/en/application-dev/reference/apis-arkweb/arkts-apis-webview-WebviewController.md): debugging overloads, release warning, scheme/service-worker APIs, destroy mode and renderer-termination scope.
- **S3** — [OpenHarmony current NAPI controller source](https://github.com/openharmony/web_webview/blob/bca62eeacad0d102b7b673267c2736d7c4b28e94/interfaces/kits/napi/webviewcontroller/napi_webview_controller.cpp): `SetWebDebuggingAccess`, static state, port forwarding and system-parameter early return. This is not the installed closed/current kernel's socket factory.
- **S4** — [OpenHarmony CEF snapshot](https://github.com/openharmony/third_party_cef/blob/2d0c18b9d7d860756a453a52af896ba830a329e5/libcef/browser/devtools/devtools_manager_delegate.cc): generic `TCPServerSocketFactory("127.0.0.1", port)`. Revision is from 2024-01-24, not ArkWeb 144 acceptance.
- **S5** — [OpenHarmony Chromium adaptation patch](https://github.com/openharmony/third_party_chromium/blob/b41796c46179caa4838f06c7bbf956b25d33bf26/patch/0003-ohos-1115.patch): `unix_domain_server_socket_posix.cc` OHOS peer-credential support. Revision is from 2024-01-15; no current DevTools authorization guarantee is inferred.
- **S6** — [OpenHarmony Web attributes](https://github.com/openharmony/docs/blob/f41b9345badd47c7ab0c263344cd7f4b5a549afb/en/application-dev/reference/apis-arkweb/arkts-basic-components-web-attributes.md): `blockNetwork`.
- **S7** — [OpenHarmony Web events](https://github.com/openharmony/docs/blob/f41b9345badd47c7ab0c263344cd7f4b5a549afb/en/application-dev/reference/apis-arkweb/arkts-basic-components-web-events.md): `onInterceptRequest`, returned responses, redirects and POST-body limitation; navigation/auxiliary callbacks.
- **S8** — [OpenHarmony WebResourceResponse](https://github.com/openharmony/docs/blob/f41b9345badd47c7ab0c263344cd7f4b5a549afb/en/application-dev/reference/apis-arkweb/arkts-basic-components-web-WebResourceResponse.md): binary responses and explicit asynchronous readiness.
- **S9** — [OpenHarmony WebSchemeHandler](https://github.com/openharmony/docs/blob/f41b9345badd47c7ab0c263344cd7f4b5a549afb/en/application-dev/reference/apis-arkweb/arkts-apis-webview-WebSchemeHandler.md): request interception/body-handler extension point.
- **S10** — [Official CDP JavaScript protocol](https://github.com/ChromeDevTools/devtools-protocol/blob/7245ec551bc9d450170193456ab3965bb7e716cb/json/js_protocol.json) and [browser protocol](https://github.com/ChromeDevTools/devtools-protocol/blob/7245ec551bc9d450170193456ab3965bb7e716cb/json/browser_protocol.json): real Debugger/Runtime/Page operations, events and location fields. Protocol definition does not establish ArkWeb method support.
- **S11** — [Chrome DevTools frontend Script mapping](https://github.com/ChromeDevTools/devtools-frontend/blob/5de307634fdbc4192a3cd8503d33016321ba7c65/front_end/core/sdk/Script.ts): `rawLocationToRelativeLocation`, `relativeLocationToRawLocation` and inline-origin offsets. Confirm behavior on the actual target.
- **L1** — Installed official SDK `D:/ProgramFiles/Huawei/DevEco Studio/sdk/default/openharmony/ets/oh-uni-package.json`, `api/@ohos.web.webview.d.ts` and `component/web.d.ts`. Metadata: API 26, `26.0.0.105`; relevant declarations include TCP-vs-Unix comment at line 4825, `onInterceptRequest` at 6612, `blockNetwork` at 7017, `onOverrideUrlLoading` at 7486, `sharedRenderProcessToken` at 3504 and renderer termination at 4381.
- **L2** — Installed official native SDK `D:/ProgramFiles/Huawei/DevEco Studio/sdk/default/openharmony/native/oh-uni-package.json`, `sysroot/usr/include/sys/socket.h`, `sys/un.h`, `unistd.h`: matching version, Unix address family/layout, peer-credential constant and own-process identity functions.
- **L3** — Bundled Flutter/OHOS Dart SDK `D:/ProgramFiles/flutter_ohos/bin/cache/dart-sdk/lib/io/socket.dart`, lines 7–11: documented Unix platforms omit OHOS. This is a documentation limit, not a measured OHOS failure.
