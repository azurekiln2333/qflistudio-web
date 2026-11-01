# Web R8/R9 panels and debugger readiness

Review date: **2026-10-23, Asia/Shanghai**. Web HEAD inspected:
`e0f81a56230ec27890b67eb9ac0c1df71a805c71`. Shared-core HEAD initially inspected:
`0ec321c974c524a57cedcfcc39f09bb8ab7f50e7`; debugger contract:
`f8edb0424e40afc5e8dba6a874cb240f467ffd7b`.

This is a source/evidence review. No Flutter, build, device, port-forward, or test
command was run. Only this research document was written. The shared-core owner
was editing its editor/debug UI during this review; uncommitted files below are
observations of work in progress, not accepted or frozen product behavior.

## Current exposed behavior

| Surface | Currently exposed behavior and source | Acceptance boundary |
| --- | --- | --- |
| Tools → 本地服务 | Inline `WebServerToolsView` starts/stops a real `WebRuntimeSession`, shows its actual engine and loopback URL, copies/opens that URL, and displays newest-first request/console records. `lib/pages/web_tools_overview.dart:76`, `lib/pages/web_tools_page.dart:59,109,118,250,275`. | This is a working product surface, rather than a future panel proposal. Its own session is independent of an editor-started preview. |
| Request records | `WebRequestEvent` contains method, URI/path, HTTP status and elapsed time. Dart middleware publishes completed requests except its long-lived SSE endpoint; Nginx tails its actual JSON access log every 200 ms, excludes SSE, and publishes the same type. `lib/services/web_runtime_session.dart:3`, `web_dev_server.dart:121`, `nginx_session.dart:125,208`. | Tools subscribes to all request events. Shared `WebPreviewSession` currently exposes only URL/debug stream/stop, so the editor does not receive this product-specific request stream through that interface. |
| Browser console/errors | HTML receives a script wrapping `console.log/info/warn/error`, `error`, and `unhandledrejection`, POSTing JSON to same-origin `/__webforge/debug`. The endpoint checks Origin when present, limits bodies to 16 KiB and message text to 4000 UTF-16 units; Dart retains at most 500 records before dropping a batch. `web_dev_server.dart:367,504`. | This is browser log forwarding, without runtime pause/stack state. Current error payload contains message/level, not structured filename/line/column or stack frames. |
| Native server diagnostics | Nginx stderr/output and error.log become debug-stream lines; HTTP errors also enter that stream. `nginx_session.dart:125,182,245`. | Native server diagnostics are separate from JavaScript VM execution state. |
| Editor terminal | Ordinary HTML Run starts the product factory, subscribes to `debugStream`, appends lines to `TerminalPane.appendDebug`, opens the preview URL, and stops the prior session on replacement. Preview is stopped on editor disposal. Core committed `lib/editor/editor_page.dart` at `0ec321c`, and `terminal_pane.dart:1043`. | Closing the terminal cancels the preview-log subscription while the preview server remains alive. Reopening the terminal does not itself resubscribe; another Run does. New panel integration should retain preview-log ownership independently of visibility. |
| Output / Debug Console / Ports | At the initial inspected core HEAD, `_BottomPanel` contains terminal, AI and Problems. Separate Output/Debug Console/Ports widgets exist in untracked `lib/editor/editor_output_panel.dart`, alongside untracked debug controller/widgets/tests. | The pending widgets are not evidence of user-reachable integration. The Ports widget is designed to show and stop only its supplied preview, with no discovery or network requests; it does not know about the Tools view's separate session. |
| Breakpoints / step controls | `webProfile` supplies `WebRuntime.start` and `WebCodeAnalyzer`, and does not supply `StudioProfile.debugger`. No Web `StudioDebugger` provider exists. `lib/main.dart:26–45`. | Web has no delivered native breakpoint/step acceptance. QuickJS deliberately compiles only; runtime debugging must control the browser target that executes the page. |
| Offline terminal | Main Tools has a shared terminal entry. Web has `offlineOnly == true` and no `terminalCommandDelegate`; sandbox built-ins remain available, unsupported commands report their limitation, and online terminal controls are hidden. `test/web_terminal_release_test.dart`. | Cancellation tests install a test-only delegate; they do not prove a Web JavaScript host toolchain exists. |

Tools retains **200 log lines**, offers Clear, and cancels subscriptions/stops its
session on widget disposal (`web_tools_page.dart:73–106`). The integrated Tools
layout deliberately retains the server widget while scrolling
(`web_tools_overview.dart:41–48`). These are useful existing lifecycle choices.

Production preview ownership matters: OHOS `openUrl` launches a system
`ohos.want.action.viewData` ability, Android launches ACTION_VIEW, and iOS presents
SFSafariViewController. None of these paths returns an owned CDP target/session
to Dart. The OHOS agreement-reader Web component is unrelated to project preview
and must not be treated as a debugger target.

## Recorded tests and native evidence

All entries below were read, not rerun. A test title alone does not establish
what its assertions execute.

| Evidence | What it establishes | What it does not establish |
| --- | --- | --- |
| `research/integration-tests-current.log`, modified 2026-10-22 16:21:26 UTC | Most recent of the three integration logs inspected: **171 passed, 1 failed**. Its six native Nginx tests, 12 Dart server tests and terminal tests finish successfully. | The complete current suite is not green. The failing current-file preview assertion is at product test line 304, expected true/actual false. |
| `research/integration-tests-final.log`, modified 2026-10-22 06:46:04 UTC | Earlier **172/172** pass, including request diagnostics, terminal log rendering, offline gating and Tools controls. | Filename “final” does not make it current after the later core changes. |
| `test/web_dev_server_test.dart:303,320` and corresponding log cases | Real loopback HTTP 404 produces a debug line; malformed debug JSON is rejected; manual JSON POST produces the expected debug line and retained buffer entry. | Despite its title, the “browser errors” case does not execute a browser or overflow the buffer; it sends one HTTP POST. It cannot prove injection timing, actual console capture, or the retention-limit boundary. |
| `test/nginx_session_test.dart:66` and corresponding successful log case | Actual desktop Nginx serves the page/assets, injected bridge text exists, manual diagnostic POST reaches `debugStream`, a real 404 reaches `requests`, and stop refuses a new connection. | It does not execute browser JavaScript. |
| `test/web_terminal_release_test.dart:174` and corresponding successful log case | Calling real `TerminalPane.appendDebug` displays an error in the transcript under the Web profile. Other cases verify real sandbox built-ins, unknown-command feedback, exit codes and offline gates. | A direct append does not prove browser → HTTP bridge → session → editor composition. |
| `research/ohos-runtime.json` and `web-ohos-runtime-acceptance.md` | Actual x86_64 OHOS emulator execution: **15/15**, QuickJS compile-only version, embedded Nginx 1.31.6, HTML/CSS 200, missing JS 404, a real request-log event, post-stop refusal and owned-fixture cleanup. HAP SHA-256 `fd9fb56ad444fb76067009a9580f740c26675b871d6c4613e903c1495094a01b`. | Alternate-entry adapter/lifecycle acceptance; it launches no browser and does not prove normal editor panels, browser console capture, breakpoints, arm64 execution or physical-device signing. |
| `research/ohos-481-final.json` and `.device.json` | Existing saved run attaches to an actual test-only ArkWeb 144.0.7559.59 target, validates exact packaged catalogs and executes every example through local CDP. | Its saved outcome is **474/481**, not a pass. It is a catalog run, not a Debugger-domain test or production debugger provider. Root's subsequent full native rerun was in progress during this review. |

The current preview failure is already assigned to the shared-core owner. Root
confirmed an actual regression: normal Run must respect an explicitly configured
Web root such as `public`, rather than passing a project-root default entry outside
that document root to `urlForFile`. Do **not** change the product test merely to
accept the new behavior. Preserve ordinary/default preview and explicit current-file
preview as distinct, validated operations, then rerun their real HTTP and editor
composition checks after the owner repairs the flow.

No available native record proves the newly proposed Output/Debug Console/Ports
widgets. The own-bundle emulator window was released after the earlier native run
and cleanup; the exact emulator later disconnected. This review performed no
reconnection or device work.

## How the new core contract applies

`f8edb04` adds `lib/services/debug_session.dart`, optional
`StudioProfile.debugger`, and the authoritative
`../qfli_studio_core/.trellis/spec/frontend/offline-debugger.md`. The spec explicitly
states that the contract alone does not implement editor controls, adapters or
device acceptance.

A Web provider must validate physical project containment and entry/source
identity, reject unsupported snapshots, report actual backend-confirmed breakpoint
locations, publish bounded immutable full snapshots with increasing revisions,
bind frame/command use to the current pause token, and complete `done` only after
the actual controlled runtime and native resources finish cleanup. Console is
read-only; the contract exposes no arbitrary expression-evaluation command.

Shared in-flight `EditorDebugController` currently recognizes `.js`/`.mjs` but
does not map `.html`/`.htm`, and checks both the active file language and the
configured entry language before launch. Web's normal entry is HTML. Browser
debugging therefore needs a coordinated HTML-entry mapping with the C/core owner;
installing a JavaScript provider alone would not make the normal Web project
launchable through that controller. CSS files must not gain pretend executable
breakpoints merely because they belong to a Web project.

The pending core panel design already provides a reasonable destination for
actual data: ordinary run/tool output, separate read-only preview/debug messages,
and the real owned preview URL/stop operation. Reuse those stores and lifecycle
owners after integration; avoid creating another product transcript database.

## Browser-native debugging is feasible research, with a concrete missing adapter

Current primary documentation, inspected on 2026-10-23:

- **[S1] OpenHarmony ArkWeb debugging guide**:
  `https://raw.githubusercontent.com/openharmony/docs/master/en/application-dev/web/web-debugging-with-devtools.md`
  documents app-controlled Web debugging, its default disabled state, and local
  forwarding for inspection. It discusses inspecting loaded JavaScript sources.
- **[S2] OpenHarmony WebviewController API reference**:
  `https://raw.githubusercontent.com/openharmony/docs/master/en/application-dev/reference/apis-arkweb/arkts-apis-webview-WebviewController.md`
  documents `setWebDebuggingAccess(enable, port)` from API 20. The recorded Web
  emulator uses API 26. An available API is not evidence that every CDP command
  works in a packaged product.
- **[S3] Chrome DevTools Protocol, Debugger domain**:
  `https://chromedevtools.github.io/devtools-protocol/tot/Debugger/`
  documents breakpoint installation/resolution, script identity and source
  retrieval, paused call frames, resume, pause and step commands. URL breakpoints
  can remain unresolved until the matching script appears; verified locations
  must use the backend's returned/resolved location. Its zero-based coordinates
  require conversion to the core contract's one-based source positions.

**Recommendation/inference:** an offline, app-owned ArkWeb preview plus a local
CDP `StudioDebugger` provider is a viable next implementation path. Existing
native catalog attachment reduces transport uncertainty, but does not remove the
following implementation and acceptance work:

1. Create and own the project preview Web component/target on an explicit Debug
   action; enable its debugger only for that session. Validate same-device local
   endpoint access and target identity. A separately opened system browser has
   no target ownership contract in today's product.
2. Serve the selected project entry and map only its canonical local script URLs
   to source paths. External and inline scripts need distinct mapping. Production
   HTML currently receives an inserted bridge, which changes source positions:
   either record exact insertion offsets or use a debugger-specific serving path
   that retains exact authored source. Never reuse catalog-harness identity as
   proof of a production target.
3. Implement actual breakpoint/resolution, pause/resume/steps and cleanup against
   observed protocol support. Start with stack frames and primitive inspection
   only where proven safe; advertise variables or unsaved snapshots only after
   implementing them. Save-first with empty snapshots is allowed by the contract.
4. Run real pause/step/stop acceptance on the packaged target, including an entry
   pause, an external local JS file, inline-script coordinates, CRLF/Unicode,
   stale pause tokens, page navigation, root switching and stop while paused.
   Require target/worker destruction and listener cleanup, not only socket close.

This path requires new product native/WebView and Dart adapter code plus shared
UI integration. It is an open R8 deliverable, not a justified blanket “Web cannot
debug” conclusion and not an already delivered feature.

## Web-owned feasible follow-up work

| Priority / owner | Concrete work | Acceptance |
| --- | --- | --- |
| First: C/core owner, Web verifies | Repair the explicit-root normal-preview regression and finish shared panel wiring. Keep preview-log subscriptions alive when switching/closing panels; stop the actual preview through Ports. | Current-file/explicit-root tests green; logs still arrive after panel changes; no stopped or foreign-root session remains. |
| First: Web | Add a widget acceptance case for the existing inline server: start a real loopback session, request 200/404, POST a diagnostic, observe engine/address/request/log text, clear, stop and dispose. | Real service actions and visible results; narrow/large-text layout; post-stop connection refusal and no late setState. Existing Tools tests mainly establish controls and navigation. |
| First: Web | Add browser-driven acceptance for the production injected console bridge, covering head/body logs, uncaught error and unhandled rejection; feed the real session stream into the actual UI. | Browser-originated events, exact payloads, no external requests, bounded retention and teardown. A manual HTTP POST is insufficient. |
| First: Web | Verify and repair early-head capture if the browser test confirms the source-derived limitation. `web_dev_server.dart:226` inserts the bridge immediately before `</head>`; an earlier head script executes before the wrappers/listeners exist. | A log/error in a head script before the closing head is captured once, as are later body events. Preserve user source and correct debugging source positions. |
| Next: Web + C/core | Supply the controlled ArkWeb/CDP debugger described above and coordinate HTML-entry language support. | Actual backend pauses and locations with capability-gated UI and packaged-target acceptance. |
| Next: Web + C/core | Decide whether editor Ports should also represent a Tools-started preview. Current widgets own separate sessions; shared `WebPreviewSession` lacks product request telemetry. | One explicit session registry/telemetry contract if aggregation is required; no guessed process/port scan and no duplicate runtime launch. |

Offline acceptance must remain explicit: current UI hides the arbitrary HTTP tool
and external-proxy editor, but `WebProjectConfig.parse` still accepts existing
HTTP(S) proxy targets, and the production external browser has no product-owned
request interception. These are narrower facts than enforced network isolation.
Before declaring a debugger session offline, reject non-loopback proxy targets
for that session and block/record non-loopback page/subresource/WebSocket traffic
inside the controlled view. Preserve configuration bytes when rejecting an
unsupported existing configuration. The catalog harness already performs a
separate request-blocking check; it does not establish this production policy.

## R9 Web highlighting status

Core `lib/editor/highlight_themes.dart:33,50,69,82,132` registers offline CSS,
JavaScript and XML/HTML grammars. `.html`/`.htm` map to HTML/XML; `.css` maps to CSS;
`.js`/`.mjs` map to JavaScript. HTML explicitly registers its embedded CSS and JS
grammars rather than depending on automatic language guessing. Web advertises
`.html`, `.css`, `.js`; no missing mapping was found for those advertised types.

Core `test/highlight_preferences_test.dart:181` checks actual tokenized embedded
CSS and JavaScript while preserving exact source text. Its mixed-language case
also contains standalone `main.js`, `style.css`, `index.html`, and JSX/tagged-CSS
coverage exists in a separate current test. The available older
`build/editor-analysis-tests.log` ends **16/16 passed**, including HTML embedded
grammars. The later `build/highlight-review.log` ends with one failure in the
mixed-language test's **JSON token expectation**, with HTML embedded-grammar
coverage passing. Current source expects JSON `attr` explicitly, but this review
found no fresh focused all-pass run covering the complete current test file.
Do not present the older log as current cross-language acceptance.

Web's independent `web-editor-analysis.md` and
`build/content/web-editor-analysis-test.log` prove **2/2 host editor cases** for
real QuickJS unsaved diagnostics, precise wavy ranges, Problems navigation,
repair clearing and owner-root changes. The 15-case native report separately
proves OHOS parser loading and offsets. Neither is an on-device screenshot/test
of current HTML/CSS/JS highlight spans or the new panels.

For the Web portion of R9, retain the existing shared grammar implementation and
obtain current focused grammar evidence plus normal-editor OHOS visual/token
acceptance after shared changes freeze. C/C++ header/linking and Python module
management remain their respective product owners' R9 work; this Web report
does not close the cross-product requirement.

## Recommendation for the acceptance ledger

Record Web logs and local server/request lifecycle as implemented with the exact
host/native boundaries above. Keep R8 open for production panel composition and
the browser debugger adapter; keep its device gate open until the actual new
controls/runtime are measured. Keep Web R9 evidence scoped to advertised grammar
coverage and existing host/editor/native-parser checks, with current highlight UI
acceptance still pending. Root should refresh log/HAP/core identities after the
running native catalog pass and shared-core repairs settle.
