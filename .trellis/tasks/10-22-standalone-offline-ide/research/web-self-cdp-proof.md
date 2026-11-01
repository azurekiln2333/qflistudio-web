# Test-owned same-process CDP first proof source

Authored 2026-10-23, Asia/Shanghai. **Source only; API26 ArkTS compilation,
packaging and actual OHOS execution are pending.** No build, browser, device,
forward, listener or shared-core mutation was performed for this slice.

## Change boundary

The missing behavior is an application-originated connection to the default
ArkWeb abstract Unix socket and an actual protocol reply from the uniquely owned
Web target. The new test-only `SelfCdpProof.ets` owns bounded discovery, HTTP/WS
validation, client masking and the fixed RPC sequence. `pages/SelfCdp.ets` owns
one incognito static Web and visible/hilog stage reporting. Neither file changes
the application-wide debugging switch. The root coordinator has now integrated
the opt-in ability route, test pages manifest and local NAPI package dependency;
the independent native target is also present in CMake. These are source
integration observations, not build/import/device results. This author changed
none of those integration files.

The files introduce no endpoint input: the only native connect operation is
`libqfli_web_cdp_transport.so.openSelf()`. Its existing NAPI declaration uses an
opaque positive int64 decimal-string handle. Returned CDP URLs cannot supply a
PID, socket path, host or port to that module.

## Exact source behavior

1. Generate a fresh 192-bit bootstrap token using the SDK crypto random API.
   Own exactly one Web with a synthetic `http://127.0.0.1:19998` URL containing
   that token. Return its static HTML through `onInterceptRequest`, without a
   script, event handler, subresource or project-authored JS. All other resource
   requests receive 403; both navigation interceptors permit only that exact URL.
   The response CSP is `default-src 'none'; base-uri 'none'; form-action 'none'`.
2. After the exact bootstrap `onPageEnd`, GET `/json/list` through `openSelf()`
   with the fixed HTTP Host `localhost`. Require HTTP200 JSON with a bounded
   Content-Length; fail visibly on chunked/unknown-length responses, invalid
   headers, duplicates or an oversized target list. Match the exact random URL;
   reject zero/multiple matches and anything except a page target.
3. Require the discovery endpoint to be exactly
   `ws://localhost/devtools/page/<that target ID>`. Open a second **self-only**
   Unix handle and send that exact path with fixed Host `localhost`. Generate a
   fresh 16-byte WS key; verify HTTP101, Upgrade/Connection tokens and the exact
   SHA-1/Base64 `Sec-WebSocket-Accept`. Reject extensions, subprotocols, HTTP body
   framing and unexpected host/path/credentials/query/fragment syntax.
4. Mask every client frame with a fresh cryptographic mask. Receive bounded
   unmasked server text/continuation/control frames; reject reserved bits,
   unexpected opcodes, nonminimal lengths, invalid continuation/control framing
   and bad UTF-8. Answer Ping with a masked Pong. A server Close/EOF fails the
   unfinished proof. There is no compression and no binary-CDP fallback.
5. Send actual `Page.getFrameTree` and require the main-frame URL to equal the
   bootstrap. Only then send `Runtime.enable` and fixed `Runtime.evaluate`
   expression `(6 * 7)`, requiring an actual remote number result of 42 without
   exception details. The success marker is emitted only after those replies
   and successful native transport close. It does not claim Debugger-domain
   breakpoint, pause, step, source-map or editor-panel support.
6. Send a masked normal-close frame after success and always close native handles
   in `finally`. `cancel()` immediately closes the module's own handles, wakes an
   outstanding polling timer and rejects the run. The page calls it before Web
   stop on `aboutToDisappear`; it suppresses late visible state updates.

Bounds are 10 seconds for bootstrap load, 20 seconds for the complete RPC run,
3000 active/poll work turns,
4 KiB per native read, 64 KiB per native write, 16 KiB HTTP headers, 64 KiB JSON
discovery, 128 targets, 256 KiB complete WS message, 256 frames per message,
128 CDP events before each requested reply, 512 detail characters per report and
8 KiB visible transcript. Reads/writes honor partial results and retry only
`-EAGAIN`/`-EINTR` asynchronously with a 10 ms timer; zero-write, EOF, other errno,
timeout and cancellation are explicit failures. Synchronous random generation
handles only 4/16/24-byte requests; no blocking socket operation is introduced.

## Root integration status and contract

- Source now registers `testability/pages/SelfCdp` in the ohosTest pages manifest
  and `libqfli_web_cdp_transport.so` as a local entry package dependency.
- `TestAbility.onCreate` now recognizes `qfliSelfCdpProof=true`, requires
  `qfliCatalogCdp=unix`, rejects other modes for this proof and selects the exact
  route above. Its owner enables `setWebDebuggingAccess(true)` using **one
  argument**. No production ability imports this page or enables debugging.
- **Cold-start requirement:** TestAbility is a singleton. `onNewWant` currently
  handles only the owned `qfliCatalogStop=true` request; it does not update mode
  or change routes. Terminate the owned existing test instance, then start a
  fresh one with both opt-in parameters so `onCreate` selects this proof. Adding
  proof wants to an already running catalog ability is not a valid proof launch.
- Existing ability lifecycle remains responsible for disabling debugging on
  page load failure, stop want, window destruction and ability destruction.
  Page `aboutToDisappear` cancels its own socket operations; this is additional
  cleanup and cannot replace the static switch owner's cleanup.
- Public proof API is `bootstrapUrl`, `response(address, method)`,
  `run((SelfCdpReport) => void): Promise<void>` and `cancel(): void`.
  The exact log tag is `QfliSelfCdp`. Reports identify the stage and state;
  `complete: pass` is the intended runtime marker, **not yet observed**.
- Record the actual release/test HAP SHA, ABI, OS/API/ArkWeb version, process PID,
  default socket name, complete observed reports, and explicit absence of HDC
  forwards/TCP debug listeners during the later coordinated device run.

## Source review corrections

Root review changed UTF-8 construction to the installed SDK's
`util.TextDecoder.create('utf-8', { fatal: true })` factory. Decode failures remain
explicit; this is an SDK-signature correction, not an ArkTS compilation pass.

The page's resource callback now returns an explicit403 if `!alive` or the proof
owner has been cleared. Returning `null` would permit a real request during
teardown. Both load/navigation guards also deny when `!alive`, even if the URL
still equals the former bootstrap. Native cancellation still happens before Web
stop, and late visible reports remain guarded by the page's alive flag.

## Remaining evidence and limits

The default socket may fail or reject the same-process client on the real engine;
that is a real gate failure, not a reason to open a TCP fallback. The fixed HTTP
Host/content-length policy is intentionally narrow; a different actual ArkWeb
response must be inspected and justified before source changes.

The page has no authored network-capable fixture and returns explicit responses
for intercepted requests. It deliberately does not claim measured complete
ArkWeb isolation, interception of every scheme/POST/worker or owned-preview
parity. No `blockNetwork(true)` compatibility result is inferred from source.

The native client's same-UID **server-peer** check does not establish ArkWeb's
**inbound client authorization** rule. Current server authorization, controlled
foreign-UID denial, absence of TCP listeners, static-switch/socket disappearance,
owned-target removal, release-artifact behavior and teardown/relaunch remain
separate stage-A gates. Full Debugger-domain behavior and editor composition are
also still open. No pass is reported from source review or a HAP build alone.

## Verification record

- Read project before-dev, native/error/quality and shared thinking guidelines,
  the task PRD/design/implementation plan and `web-owned-preview-plan.md`.
- Checked the installed official API26 SDK declarations for random/SHA-1,
  Base64/text encoding, own process PID and Web interception/navigation hooks.
- The three new UTF-8 files pass static final-newline, trailing-whitespace and
  conflict-marker checks. This checks text hygiene only.
- The resulting C ABI, decimal NAPI, opt-in lifecycle and acceptance contracts
  are captured in [Web CDP Transport](../../../spec/backend/web-cdp-transport.md)
  using the required seven-section executable-spec structure.
- No tests or compilation have run in this slice, because the shared heavy-work
  resource window belongs to another coordinator. API26 ArkTS type checking,
  adversarial protocol regressions and a real same-app Unix proof are pending.

### Supplementary protocol result after source handoff

The later exact-source Node fixture passed **24/24** protocol cases with source
SHA `775c65e32f50542a52cd38c7a4be794fffc446670b0e6b4f43f54e693c144653`.
See [the protocol report](web-self-cdp-protocol.md) for the actual command,
independent byte oracle and coverage limits, and
[the follow-up source review](web-cdp-followup-review.md) for current ownership
and import-boundary checks. That supersedes only the earlier unrun status for
those host protocol cases. TypeScript transpilation with SDK/NAPI doubles does
not type-check ArkTS or establish actual native module import, connector
execution, same-app ArkWeb access or stage-A security/teardown acceptance.
