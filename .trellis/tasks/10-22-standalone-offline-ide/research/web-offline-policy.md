# Production preview proxy boundary — October 23

Latest executed checkpoint: **18/18 proxy-policy tests and both engine browser
policy cases pass**, inside a combined **32 pass / 4 fail** run. The four
bridge/Tools failures and subsequent unrun repairs are recorded below; current
OHOS and owned-view navigation acceptance remain open.

## Change boundary

The offline UI hides network tools, but existing `.qfli/web.json` proxy targets
can still reach arbitrary HTTP(S) hosts. The behavior belongs in configuration
validation and both actual preview engine startup paths, before binding or native
host access. Root owns `web_project_config.dart`, `nginx_session.dart` and the new
`web_offline_policy_test.dart`; the console bridge worker's server file receives
only the agreed validation call at startup.

`WebProjectConfig.validateOffline()` accepts literal loopback IP addresses only,
with existing HTTP(S), no-credentials/query/fragment requirements. It does not
resolve hostnames. Both parsed persisted configuration and directly supplied
configuration are checked. Rejecting an old configuration leaves its bytes intact.
Existing real loopback HTTP/WebSocket/Nginx support remains useful offline.

Both actual engines now attach a same-origin CSP on all responses, including
errors/proxy paths. It preserves inline/local script and style execution and
data/blob resources. Browser-facing API calls use same-origin proxy routes to
validated local upstreams. An upstream CSP cannot overwrite the product policy.
External script/style/image/frame/fetch/WebSocket/form attempts are tested through
the actual preview, with a fail-closed browser route that records any request
escaping the response policy. The route is a safety net, not the policy under test.

This does not establish complete navigation isolation: the current system-browser
preview still needs an app-owned view and request policy for ordinary links/new
windows. The remaining CDP debugger and shared core are outside this source batch.
Reference: W3C CSP Level 3, https://www.w3.org/TR/CSP/ (`default-src`, `connect-src`,
`form-action`, `base-uri`; fetch directives differ from navigation directives).

## Initial authored verification plan (historical)

Eleven focused tests cover eight non-loopback/wildcard/hostname/mapped-address
targets through all startup paths, a direct configuration with an occupied port,
accepted numeric IPv4/IPv6 HTTP(S), and a real local upstream request plus stop.
The recording native host must receive zero calls on rejection. Actual test
execution waits for C's global memory slot release; static edits are not a pass.

Two further actual-browser checks cover WebForge and real desktop Nginx, asserting
the response policy plus local execution and blocked external attempts. They also
await a serialized test window. No claim of current OHOS policy execution is made.

## Independent response-header and redirect review

Read-only review on October 23 identified two additional boundaries that the
literal configured target plus resource CSP do not cover. Root owns the fixes
and tests below. **These findings and validation plans are not green runtime
evidence**; this review started no Flutter, browser, native or device process.

### Upstream reporting headers

At review time, `WebDevServer._proxy` excluded only the upstream
`content-security-policy` response header, and the generated Nginx configuration
hid only `Content-Security-Policy`. An allowed loopback upstream could still
supply `Content-Security-Policy-Report-Only`, `Reporting-Endpoints`, `Report-To`
or `NEL`. Forwarding those headers lets the upstream configure browser
reporting independently of the product's resource restrictions.

The precise CSP trace is:

1. W3C CSP Level 3 §5.5, “Report a violation”, processes a policy's `report-uri`
   endpoints, resolving each against the protected resource URL. It creates a
   POST whose request destination is `report` and whose body is the serialized
   violation report, then invokes Fetch.
2. §6.8.1, “Get the effective directive for request”, explicitly returns null
   for request destination `report` (as well as a null destination). Consequently
   the preview's `connect-src 'self'`/`default-src` fetch restrictions are not
   a reporting-endpoint fence.
3. A proxied HTML response carrying, for example, a report-only
   `script-src 'none'; report-uri <second-origin>/reports` can therefore cause
   reporting when an authored inline script runs, even while the enforcing
   product policy permits that local inline script.

Normative reference: https://www.w3.org/TR/CSP/#report-violation and
https://www.w3.org/TR/CSP/#effective-directive-for-a-request. This is a
reporting-specific issue, separate from the already recorded full navigation
isolation limitation.

Root's correction plan uses one shared five-header deny set:
`Content-Security-Policy`, `Content-Security-Policy-Report-Only`,
`Reporting-Endpoints`, `Report-To`, and `NEL`. Both Dart proxy filtering and
generated Nginx `proxy_hide_header` directives must derive from the same set;
the product then applies its own enforcing CSP.

Required verification:

- Serve a real loopback upstream response containing all five headers through
  both actual engines. Require no forwarded reporting-policy headers, exactly
  the product CSP, and preserved unrelated headers/status/body.
- Cover an upstream redirect without following it at the proxy; its response
  must still carry the product policy and no reporting configuration.
- In an authorized browser window, use a second-origin loopback HTTP sentinel
  as the report endpoint, so no external host is contacted. A report-only
  inline-script violation must not cause sentinel requests after filtering.
  Preserve a negative control/header assertion so a missing filter cannot
  pass merely because report delivery is delayed or unavailable.

Existing offline browser fixtures only exercise project static responses and
missing assets; they do not establish the upstream-header filtering contract.

### WebSocket handshake redirects

The installed SDK source
`D:/ProgramFiles/flutter_ohos/bin/cache/dart-sdk/lib/_http/websocket_impl.dart`
shows `WebSocket.connect(customClient: ...)` calling the custom client's
`openUrl('GET', uri)` and then `request.close()`. It does not set
`followRedirects = false`, unlike the ordinary HTTP proxy path. Thus checking
only the initial literal-loopback target does not establish the destination
of every connection made by that custom client.

Root's correction plan adds a connection factory that validates each actual
destination as a literal loopback address before connecting, and does not
permit a proxy/DNS path to bypass that decision. It must preserve real valid
loopback HTTP and WebSocket traffic, including IPv6 where available.

The regression uses an allowed numeric-loopback upstream that redirects a
handshake to `localhost` at a real second listener. The initial target passes
configuration validation, but the redirected hostname must be rejected before
DNS/connection, so the sentinel observes no request. `localhost` is deliberately
forbidden by the literal-IP contract while keeping this test local. Actual
request failure and zero sentinel connections are required; an injected
client/rewritten WebSocket implementation cannot prove this path.

The existing IPv6 cases verify parsing/validation only. A separate actual
`::1` upstream forwarding case would establish connection behavior for each
supported engine; lack of IPv6 support must remain explicit rather than being
inferred from successful configuration parsing.

## Continuation source corrections and pending verification

The shared five-header set is now consumed by both engines. The connection
factory now selects `SecureSocket.startConnect` for HTTPS and
`Socket.startConnect` for HTTP. The installed Dart SDK's
`lib/_http/http_impl.dart:2683` calls a custom factory directly; only its
default-factory branch adds TLS. Consequently a plain `Socket.startConnect`
for every scheme would silently send plaintext requests to HTTPS targets.
The SDK WebSocket path converts WSS to HTTPS before calling the same client.
These are local SDK source findings, not executed TLS acceptance.

The pending `web_offline_policy_test.dart` suite now also has raw local
HTTPS/WSS listeners requiring TLS record bytes `0x16, 0x03`, a real redirected
WebSocket hostname sentinel, and actual `::1` forwarding for both engines.
IPv6 binding failure is a visible skip. Each engine's reporting-header test
checks both HTTP 200 and 302, preserves the exact body, unrelated header and
Location, and requires the product CSP with no four reporting headers.
The browser fixture checks the proxied report-only response and a separate
real loopback sentinel; it does not mock the browser WebSocket or reporting API.

JavaScript syntax checking and `git diff --check` passed for the continuation
edits. The latest executed focused Flutter result remains **22 passed / 5
failed** in `web-runtime-repair3-tests.log`; the subsequent fixture corrections,
connection/TLS/header changes and new cases have **not yet been executed**.
Go287 released to Rust288/290, with C211 then Web219 named next. This slice
started no Flutter, Chromium, native compiler, WSL, HAP or device operation.

## Executed focused window after C297

Web300 accepted C297's explicit host release. The first four-file command,
session **47003**, terminated with exit **1** before executing test cases:
the arrow expression assigned to `findProxy` captured the following cascade.
Parenthesizing the lambda fixes that Dart parse boundary. Its failure is kept
in `web-runtime-repair4-tests.log`.

The same four-file retry, session **33184**, terminated with exit **1** after
the test reporter's **28 seconds**, with **32 passed / 4 failed** in
`web-runtime-repair5-tests.log`. The offline-policy file passed **18/18**:
saved/direct invalid targets, configuration preservation, real IPv4 forwarding
and stop, redirected WebSocket hostname denial, raw HTTPS/WSS TLS ClientHello,
both engines' actual IPv6 forwarding and 200/302 reporting-header preservation.
Neither IPv6 case was skipped. The desktop native engine was Nginx **1.31.6**.

Both real-browser offline cases passed with Chromium **156.0.8078.4**. Each
executed local script/style/eval, observed CSP blocking script/style/image/frame/
fetch/WebSocket/form attempts before the safety route, and received no escaped
WebSocket/report sentinel requests. Proxied local scripts still returned marker
42 with no report-only violations or forwarded reporting headers.

The four failures remain separate: two console-bridge tests lose BOM in their
browser source observation, while two Tools lifecycle cases expose a missing
expected log observation and actual 320px/2x project-dropdown overflow. They
are not recorded as offline-policy failures or a passing full runtime/UI suite.
The subsequent raw-HTTP bridge observation and Tools repairs need another run.

Web304/305 explicitly released the host window to JSON286; own-workspace
Win32 Dart/tester/Nginx inventory was empty. JSON306 accepted and JSON307
released to Lua. No build or device operation occurred in this Web window.
These host results do not establish owned-view navigation isolation or OHOS
execution; R8/R10 whole-product gates remain open.
