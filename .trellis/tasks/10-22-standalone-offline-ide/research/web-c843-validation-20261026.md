# C843 Web host validation

Date: 2026-10-26. Actual grant: global843, Web-observed-app-20261026-03.
Verdict: **GATE_FAIL, RESOURCES_RELEASED, ACTUAL_PROOF_WITHIN_180**.
C independently reconciled original tool evidence in global851.

## Binding and execution

Root independently read actual843. Canonical raw pin:
`d7c2c7cf007dab7bab4dcfff64ab3e81682dbd5ee902f8d4db77e330e7f3b8f9`.
The grant contains the exact observer ACCEPT/hash/boundary line.
Fresh preACK332 inputs and42 core WIP entries matched every bound byte.
Core HEAD was64f0aa75a773c632a1101ce16e1900615b274960 plus live WIP.
The preACK memory observation at05:47:14.0600533Z recorded committed60019699712,
limit68444442624, headroom8424742912 bytes and availablePhysical9518MiB.
This point sample did not guarantee capacity.
Receipt and preACK records are under build/web-c843-*.json.

The original functions execution session7698 actually terminated with exit1.
C independently read the terminal poll at05:49:22.935Z.
Validation wrapper PID71720, FILETIME134374672342866742, exited1 with Job0.
Separate final sender PID88116, FILETIME134374673390379035, exited0 with Job0.
Its terminal observation was05:48:59.620316Z. Delivery was true.
Observer heldJobs0 and resourcesReleased=true. No HOLD, forced cleanup or
phase deadline was recorded. No live reservation remains.843 is consumed.

## Results

| Check | Actual result |
| --- | --- |
| Exact five source formatter paths | PASS, five files, zero changes |
| Frozen format check | PASS, eleven files, zero changes |
| Full tests | FAIL,320 passed and1 failed |
| Analysis | PASS, no issues |
| Content | PASS,481 examples and481 tutorials, zero issues |
| Post-format input snapshots | Identical |
| Frozen child elapsed |102.424 seconds |
| Wrapper elapsed |104.560 seconds |
| Observer elapsed |105.387 seconds, local provisional timing |

The sole failing test was owned_preview_resource_broker_test.dart:
"deadline aborts the owned request and releases in-flight accounting".
The log reports TimeoutException after one second with no source await location.
It does not prove which of the test's multiple timed awaits failed.
Diagnosis remains source-only. The four repair files are not published by this
report. Prior C782316PASS/4FAIL remains historical.

## Publication and budget

Global848 is a pending wrapper relay. It is not formal release.
Global849 is the automatic final resource message from the observer invocation.
Its separate final-sender.json proves the sender terminal0 and Job0 afterward.
Global850 corroborates the original outer terminal result.
C read that publication tool's actual terminal0 at05:49:58.617Z.
Fresh preACK05:47:14.145574Z to that result is164.471426 seconds.
Global851 independently accepts that actual proof within180 seconds.
C's later reconciliation append is not asserted to have occurred within180.
Resource release and bounded proof do not promote the failed product gate.

Durable reports: web-app-c843-20261026/job.json,
web-app-c843-20261026-relay/wrapper.json,
web-app-c843-20261026-observed/observer.json,
web-app-c843-20261026-observed/final-sender.json and
web-app-c843-20261026-observed/root-terminal-observation.json.

## Subsequent source boundary

Global852 reopened only shared process_supervisor.dart and its focused tests/spec.
C owns that repair. This makes prior Web readiness snapshots stale for future
execution. It does not alter this historical C843 binding.
No additional SDK/native/WSL/OHPM/HAP/device run was made after release.
All eleven products and actual OHOS acceptance remain open.

After C851 release, root removed only the invalid response.done disconnection
sentinel from the broker deadline fixture. The installed SDK binds that Future
to the response sink, not a guaranteed socket-disconnect notification. Independent
Pi4 and preview_broker reviews support this narrow change. All504, security,
capacity-zero, immediate retry and bounded dispose assertions remain.
The log cannot locate the exact failing timed await, so that cause is a source
inference. The changed fixture is UNRUN. It does not modify C843 historical results
or its identical pre/post execution snapshots. Broker production code is unchanged.
