# Observed Web relay handoff

Status: REVIEWED_SOURCE_REAL_RUN_UNRUN. No execution reservation is held.
Date: 2026-10-26. C782 is consumed and released. It cannot authorize this parent.

Parent: `run-web-observed-relay-window.py`.
SHA256: `d1943bd1e622fc3ca5fe327e1473a141b3af992cf48fc61f078f3140fc6552b3`.
Pure tests: `81d61c8b0f639222725df141ab9e63fd07280c9c053ebc065775bb777e60dedc`.
Root independently ran all38 pure fake-Job tests successfully.
Those tests created no real Job, SDK, browser or publisher.
Earlier30-test and36-test evidence belongs to prior revisions.
Real nested-Job and publication validation remains UNRUN.

A NEW actual coordinator grant must contain this exact independent line:

```text
ACCEPT web-observed-relay/v1 sha256=d1943bd1e622fc3ca5fe327e1473a141b3af992cf48fc61f078f3140fc6552b3 boundary=control-job-before-marker/v1
```

The line expressly authorizes the parent control Job after receipt validation,
but before the child wrapper consumes the marker. Only the unchanged wrapper
consumes the atomic marker. It consumes before its SDK or publisher Jobs.
The parent reads the marker without consuming it. Concurrent control parents
may start, but only one wrapper can consume and launch the payload.
A mention, negative mention or missing boundary line is rejected.
This extends the older before-every-Job boundary deliberately.

The same grant must approve `web-relay-format-app/v1`, total<=180 seconds,
successor `c-coordinator`, and exactly these formatting paths:

- `lib/services/owned_preview_policy.dart`
- `lib/services/owned_preview_resource_broker.dart`
- `test/owned_preview_policy_test.dart`
- `test/owned_preview_resource_broker_test.dart`
- `test/web_offline_browser_test.dart`

Then the frozen app runner checks format, full tests, analysis and content
serially within remaining time. No catalog/native/WSL/OHPM/HAP/device extras
or shared-core/sibling writes are included.

Unchanged wrapper:
`401f61d44495dd0a8b681a25746263e589203a9555f30c49106eca791db0fdb3`.
Unchanged authorization module:
`84445442fed9b9382555e02b8812c6321cbd7c7ec5026ff13904c5f5897a1de4`.
Runner/worker/helper retain d80c46e1/074ac022/9df7a943 pins.
A fresh schema3 receipt binds the full independently read actual raw event.
Root independently pins that event. A predicted sequence or old receipt fails.
The new input snapshot must bind current core HEAD plus live WIP.
Core HEAD64f0aa7 does not mean clean core. The old C782 HEAD2f snapshot is stale.
Current preparation lives under `web-relay-input-20261026/`.

The entry uses existing wrapper flags plus `--reviewed-observer-sha256`.
That flag must equal the full parent hash above.
Receipt creation and launch require a new independently inspected actual grant.
The parent retains exact validation Job/process handles until the actual root
is terminal and its Job has zero active processes. Timeout or query uncertainty
records sticky HOLD. Neither condition kills the live validation custodian.

After checking exact wrapper/child phases and publishers, the same invocation
starts the final sender. Its allowance is min(8 seconds, parent remaining time).
Both validation and sender admission checks precede Job construction and process start.
The observer writes sender PID/FILETIME, exit and Job0 separately to
`<run>-observed/final-sender.json`. The sender cannot claim its own terminal state
while sending. C must inspect its recorded result before the next SDK.
C must also independently observe actual outer terminal evidence.

If validation finishes after the parent deadline, no final sender starts.
`local-release.json` retains actual validated resource proof.
`final-sender.json` records denied admission, delivered=false and
coordinatorRelayRequired=true. C must observe the parent actual exit and inspect
local evidence before independently relaying the handoff. That path remains
late and undelivered. It grants no successor and cannot become a bounded pass.

Synchronous Win32/file calls can cross a deadline. Admission checks refuse late
starts but do not provide a hard real-time guarantee. Local timing remains
provisional. C judges actual total from final terminal evidence.
The frozen close helper does not check OS CloseHandle results.
handlesClosed means the close routine returned. Terminal plus Job0 proves release.

C782 remains316PASS/4FAIL. Policy/broker repairs and added regressions are
source-reviewed but UNRUN. Both-engine CSP was validated and published as5bd2e3a
on all5 remotes. This next gate must validate repairs before production commit.

Independent final source reviews: Pi4, Pi5 and relay_safety_audit found no
blocking issue on d1943bd1. The shared review report preserves both Pi final
sections8 and9. Root control log: build/web-observed-relay-pure-controls-20261026.log.
Validation admission denial records wrapperStarted=false, no marker attempt,
releasePublished=false and coordinatorRelayRequired=true. It skips absent reports.
