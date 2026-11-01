# Inline local-server lifecycle acceptance — 2026-10-23

Current status: both first-run lifecycle cases failed inside the combined
**32 pass / 4 fail** checkpoint. The dropdown/fixture corrections below are
source-only and await the next named test window.

Current status: the first actual focused run is retained below as **32 pass /
4 fail overall**, including both lifecycle cases failing. The narrow production
layout and fixture repairs are source-only and await the root's next authorized
execution window; no new passing layout/lifecycle result is claimed.

## Change boundary

Added only `test/web_server_tools_lifecycle_test.dart`. The existing Tools
tests establish navigation, offline entry visibility, settings persistence and
other tool results; this suite targets the missing complete lifecycle through
the real inline server controls and their production runtime. No production,
shared-core, native, browser or device source was modified.

The test installs the real `webProfile`, registers a real temporary local
project in `ProjectStore`, writes `.qfli/web.json` with `engine: webforge` and
`port: 0`, and mounts `webProfile.toolsTabBuilder`. This invokes the same
`WebToolsOverview`/`WebServerToolsView` used by the shared Tools tab. It does not
inject a substitute server, access private widget state, or call button
callbacks directly.

## Assertions authored

Both the 800 px/light/default-text case and the 320 px/dark/2x-text case perform
the complete sequence:

1. Reveal and tap the real inline Start control; wait using bounded real I/O
   intervals and public controls. Read the displayed `WebForge` engine and
   exact `http://127.0.0.1:<port>/` address.
2. Request the actual endpoint using the existing server-suite HTTP helper:
   verify the exact authored HTML marker with HTTP 200, a missing JS path with
   HTTP 404, and a JSON diagnostic POST accepted with HTTP 204.
3. Reveal the lazy UI transcript and assert actual successful/failed request
   lines, the `[web.http]` error line, and the supplied `[web.warn]` diagnostic.
4. Tap Clear and verify its disabled empty-transcript state. Send another
   diagnostic to the same running endpoint and verify its new visible line.
5. Tap Stop, wait for idle controls, and require real socket refusal through an
   HTTP request. Restart through Start and require another real successful
   response.
6. Unmount the whole Tools tree; require eventual connection refusal from the
   restarted endpoint, then advance real I/O and widget pumping and check for
   framework exceptions. Verify the project Web configuration was not changed.

The test uses public `ScrollableState.position` to reveal controls and lazy log
rows within the embedded ListView, following the existing inline overview test
pattern. These are scrolling operations, not runtime instrumentation.

Teardown always unmounts the tree, checks refusal for every recorded owned
endpoint, restores the profile/HTTP overrides/view settings, disposes the store
and deletes only the created temporary directory.

## Evidence and pending gate

The direct SDK `dart format test/web_server_tools_lifecycle_test.dart` command
completed successfully. `git diff --check` is also part of the static handoff.
**Flutter execution and analysis are pending**: C's shared-host exclusive
resource window remains active, so this authoring pass started no Flutter,
browser, native build or device process.

After root explicitly provides a test slot:

```powershell
flutter test --no-pub --concurrency=1 test/web_server_tools_lifecycle_test.dart
```

Run the affected analyzer check in that authorized window as well. Until the
test actually runs, the authored cases do not count as passing widget or
layout acceptance.

The manual diagnostic POST deliberately proves the real HTTP → runtime stream
→ inline UI path. It does not prove browser-console injection, real browser
execution, Nginx, ArkWeb or native device behavior; those have their own suites
and evidence gates.

## First actual run and source-only repair

Root ran the combined focused checks and saved
[web-runtime-repair5-tests.log](web-runtime-repair5-tests.log): **32 pass / 4 fail**.
Two failures belong to this lifecycle suite; the other two are separate browser
bridge cases. The earlier authoring-only/pending record above is historical.

- The regular-light case reached the manual POST and visible `[web.warn]`
  assertion, then failed to find the expected `POST /__webforge/debug 204 … ms`
  request row. Its failure teardown also reported that the recorded endpoint
  still accepted HTTP. This is a failed lifecycle case, not a partial pass.
- The 320 px/dark/2x case reported a **308 px horizontal RenderFlex overflow**
  inside the project `DropdownButtonFormField`, whose inner row had only142 px.
  It then failed to find `WebForge` after scrolling to the copy-address button.
  No successful Stop/restart/disposal result is established by that run.

The authorized repair changes only `lib/pages/web_tools_page.dart`,
`test/web_server_tools_lifecycle_test.dart` and this report. The production
dropdown now uses `isExpanded: true`, matching the existing product resource
inspector's MD3 project selector. This constrains the selected text alongside
the dropdown icon so its existing ellipsis can apply. It preserves the project
label, full text semantics, selection callbacks and reachable settings button.

The fixture repairs retain all response, console, request-log, unchanged-config
and strict refusal assertions:

1. `_reveal` now scans the public scroll position repeatedly with bounded20 ms
   real I/O intervals, at most250 iterations. Previously it stopped at the first
   estimated scroll extent without a real wait. `_receiveDebug` emits its
   console line before awaiting `response.close`; `_handle` records the POST in
   `finally` after that completion. A client receiving204 therefore does not
   establish that the later request event is already rendered. The POST204 row
   assertion is preserved; the server does not intentionally suppress it.
2. Engine text and address are each revealed before their own assertions. The
   lazy ListView may evict the preceding engine text when the large-text address
   row/copy button is revealed. The URL is recorded as soon as the address is
   obtained, before later assertions can fail, so failure cleanup can check it.
3. `_expectRefused` now pumps between individual real HTTP attempts. Previously
   all100 attempts ran inside one `runAsync` block. Widget disposal starts the
   actual `server.stop()` asynchronously; its first await cancels the filesystem
   watcher. A continuation captured by the fake-async disposal zone needs a pump
   even while real socket probes run. The installed Flutter test binding's
   `runAsync` schedules real timers/microtasks separately from the widget clock.
   This source trace explains a fixture scheduling gap; without a rerun it is
   not proof that the recorded refusal failure is fully resolved.

Only an actual `SocketException` satisfies refusal. Timeout, a successful HTTP
response and other exceptions do not count. Framework errors remain visible,
including a new explicit no-exception assertion after initial layout and the
existing final one; no exception is discarded or intercepted. No private State,
replacement runtime or direct callback invocation was introduced.

This repair pass ran only lightweight reads and static checks. Flutter tests,
Dart formatting/analysis, Chromium, native/WSL/HAP builds and device commands
were not started because the root had released the shared host slot. The root
must rerun both lifecycle layouts and the affected analyzer check in a later
explicitly granted window before adopting a pass.

## Repair7 observation and next source-only fixture repair

The root's `web-runtime-repair7-tests.log` reached **34 passed** before the
regular-light lifecycle case failed at the clear-control assertion:
`find.byTooltip` returned a `RawTooltip`, which cannot be read as an `IconButton`.
All preceding real 200/404/POST204, request-row and visible warning assertions
were reached before that failure. Failure teardown then repeated two-second
HTTP probe timeouts until the owned Job deadline. This is a failed/incomplete
run; the narrow layout, restart/disposal completion and analyzer suite were not
established by it.

Only this fixture and this note changed in the follow-up. Clear/copy now locate
the actual public `IconButton` by its `tooltip` property, retaining enablement
assertions and real tap gestures. The refusal helper uses short native TCP
connections to the same recorded loopback endpoint and destroys every connected
probe socket. A live listener can complete a TCP handshake without its
fake-async HTTP handler answering, allowing the pump between attempts to advance
the production disposal continuation.

Refusal requires a `SocketException` with an OS connection-refused code: 61 or
111 for the supported POSIX hosts, Windows WSA10061, or Windows1225. Microsoft's
[system error reference](https://learn.microsoft.com/en-us/windows/win32/debug/system-error-codes--1000-1299-)
defines `ERROR_CONNECTION_REFUSED` as1225; that primary page was fetched on
2026-10-24 and the local Windows error-message API agrees. Other errors and
timeouts are rethrown in the widget test zone, so `runAsync` cannot silently
turn them into refusal or repeatedly capture the same timeout. All prior
response/log/clear/restart/configuration/framework-exception assertions remain.

These follow-up edits are **UNRUN**. No formatter, Dart analysis, Flutter test,
browser, native build or device process was started by this repair author.

## Repair8 observation and inner-scroll-only follow-up

The root's `web-runtime-repair8-tests.log` ends **54 passed / 2 failed**. Both
lifecycle layouts reached Clear, but its real tap missed: the control's center
was above the root viewport (regular y=-96; narrow y=-250). The shared
`tester.ensureVisible(target)` had scrolled both the inner server ListView and
the outer Tools overview. A built target alone therefore did not establish a
usable control. Neither RawTooltip casts nor RenderFlex overflow recurred.

The next source-only repair first aligns the outer server panel, then uses its
inner public `ScrollPosition.ensureVisible(..., alignment: 0.5)` to reveal each
target. The installed Flutter `scroll_position.dart` API explicitly scrolls
only that position. The bounded lazy scan returns only for a hit-testable
target; real taps and all semantic assertions remain intact.

Failure teardown also reported Windows10060 from the 200ms native connect
deadline; that timeout correctly did not count as refusal. The deadline is now
two seconds to allow Windows refusal to settle. Only the previous explicit
refused-error set passes; timeouts and other errors still fail outside
`runAsync`. These follow-up edits are **UNRUN**; no formatter, analysis, Flutter,
browser, native build or device operation was started for them.

## Repair9 stop proof and host-specific connect deadline

The root's `web-runtime-repair9-tests.log` again ends **54 passed / 2 failed**,
with scoped analysis exit0 and unchanged source snapshots. Clear is now reached
and succeeds in both layouts. Both cases then complete the real Stop gesture,
observe Start enabled and Stop disabled, and fail at the first refusal probe
with Windows10060 after its two-second limit. Restart and final disposal proof
remain unestablished.

The installed Dart SDK pinpoints that error: the stack's
`socket_patch.dart:1151` is the explicit `Socket.connect` timeout branch, which
cancels the connection task and constructs Windows10060 itself. It is not an
observed native connection-refused result. Source also shows Tools enables
Start only after awaiting `server.stop()`, WebDevServer awaits
`HttpServer.close(force: true)`, and the SDK returns the underlying server-socket
close future. The earlier unawaited-disposal scheduling explanation does not
account for this explicit-Stop checkpoint; source alone still cannot prove the
listener's actual state.

The root independently ran a lightweight Python control against only its own
ephemeral loopback listener (port61709): the live positive connection succeeded,
then after closing the listener a two-second cap timed out at2.0072771s, whereas
a five-second cap returned actual Windows10061 at2.0320263s. This is host timing
evidence, separate from Dart or product acceptance. The next source-only change
therefore changes only the probe deadline to five seconds. Strict refused codes
remain unchanged; Windows10060, timeout and every unrelated error still fail.
The full lifecycle suite must actually rerun before adopting a pass. This
read-only investigation and narrow edit ran no Dart/Flutter/formatter/analyzer,
browser, native build or device process.

## Repair10 executed pass — 2026-10-24

This is the latest executed checkpoint; the earlier failed and pending records
above remain historical. Under grant `C537-Go545-Web548`,
[web-runtime-repair10-tests.log](web-runtime-repair10-tests.log) ends **57/57
passed**, including the real Web named-workspace reconstruction case and both
inline lifecycle layouts: regular light and 320px/dark/2x text. Both lifecycle
cases complete real HTTP 200/404 and POST 204, visible requests/warnings, Clear
and subsequent logging, Stop with strict connection refusal, restart, final
disposal refusal, unchanged configuration and no framework exceptions.

[web-runtime-repair10-analysis.log](web-runtime-repair10-analysis.log) reports
**11 items, no issues**. The
[result JSON](web-runtime-repair10-result.json) records format/test/analyze
exit 0, no exception and `sourceSnapshotsIdentical: true`; the before/after
snapshots retain 234 identical source hashes. The worker ran from
2026-10-24T06:19:49.5199468Z to 2026-10-24T06:20:37.8376679Z. The
[Job record](web-runtime-repair10-job.json) confirms worker PID 91884 exit 0,
terminal and active processes 0, elapsed 48.57s; publisher PID 91528 also exited 0
with active 0 and delivered the release. Channel 549 handed the host to Note.
This focused pass establishes these Web cases, not completion of the broader
eleven-product acceptance task.

## Five-dimension bug retrospective

1. **Root cause category — implicit fixture assumptions.** Tooltip lookup was
   assumed to return an `IconButton`; a built nested control was assumed to be
   tappable; and a two-second connect deadline was assumed sufficient to
   observe native refusal on this Windows host.
2. **Why successive fixes failed.** Repair7 exposed the `RawTooltip` cast,
   repair8 exposed outer-scroll movement and the 200ms deadline, and repair9
   proved Clear and explicit Stop but still preempted the host's approximately
   2.03s refusal response with a 2s cap. Each correction exposed a separate
   remaining assumption; none of those failed checkpoints proved the complete
   lifecycle. Repair10 supplies that executed proof with the measured 5s cap.
3. **Prevention.** Find the public button by its tooltip property before
   inspecting its type, align the outer panel and scroll only the inner
   position, require hit-testability before real taps, and calibrate native
   probe timing with an owned listener. Keep strict refusal codes 61/111/1225/
   10061; timeout 10060 and unrelated errors must still fail. Preserve the full
   response/log/Clear/Stop/restart/disposal assertions.
4. **Systematic expansion.** Review similar widget fixtures for these same
   finder, nested-scroll and native-I/O assumptions. This evidence does not
   require a production or shared-core architecture change; the production
   dropdown overflow correction has its own retained repair5 record above.
5. **Knowledge capture.** The existing
   [frontend quality guidelines](../../../spec/frontend/quality-guidelines.md)
   already capture the public-button finder, inner-only reveal with hit
   testing, strict refusal and measured 5s deadline. This report records the
   final executed result without changing those guidelines or other sources.
