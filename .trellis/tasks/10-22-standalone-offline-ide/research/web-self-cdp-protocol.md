# Supplementary self-CDP protocol fixture verification

Date: **2026-10-23, Asia/Shanghai**. The lightweight Node suite passed **24/24**
cases against the exact frozen
[SelfCdpProof.ets](../../../../ohos/entry/src/ohosTest/ets/testability/SelfCdpProof.ets)
source. This is supplementary protocol-fixture evidence. It does **not** establish
ArkTS compilation, native transport behavior, same-app ArkWeb access, debugger
delivery or stage-A security/teardown acceptance.

## Change and execution boundary

Only [scripts/test_self_cdp_protocol.mjs](../../../../scripts/test_self_cdp_protocol.mjs)
and this report were added. No `.ets`, existing report, manifest, shared-core or
native implementation was edited. The root explicitly authorized lightweight
Node tests; no browser, Flutter, native compiler, WSL, HDC or device operation
was invoked for this slice.

The script reads the `.ets` file without rewriting, extracting or replacing its
protocol logic. The installed official SDK's TypeScript `transpileModule`
converts that exact pure protocol source to CommonJS; `vm.Script` evaluates it
with boundary adapters. The file hash is checked again after all cases. Tests
call only the public constructor, `bootstrapUrl`, `response`, `run` and `cancel`;
they never inspect or invoke private protocol methods/fields.

`transpileModule` provides syntax transpilation, **not** semantic TypeScript or
ArkTS type checking, SDK import resolution, NAPI linkage or ArkUI compilation.
The test-only page and TestAbility are not executed by this suite.

## Exact local SDK dependency and command

The default dependency is the existing official SDK file:

```text
D:/ProgramFiles/Huawei/DevEco Studio/sdk/default/openharmony/ets/build-tools/ets-loader/node_modules/typescript/lib/typescript.js
```

Observed bundled TypeScript version: **4.9.5**. Observed Node version:
**v24.15.0**. There is no npm install, package download or dependency fetch.
`QFLI_OHOS_TYPESCRIPT` may point to the corresponding already-installed SDK file
when the SDK resides elsewhere; the script prints the actual path and version.

From the repository root:

```powershell
node scripts/test_self_cdp_protocol.mjs
```

Observed frozen source SHA-256:

```text
775c65e32f50542a52cd38c7a4be794fffc446670b0e6b4f43f54e693c144653
```

## Fixture contract and assertions

Only imports at SDK/NAPI boundaries are substituted:

- `@ohos.security.cryptoFramework`: Node crypto random bytes and incremental
  SHA-1 digest adapters. Random requests are recorded; bootstrap/key/mask bytes
  must correspond to the actual observed draws.
- `@ohos.util`: Node UTF-8 encoder/fatal decoder and Base64 adapters.
- `@ohos.process`: a fixed fixture PID for reporting.
- `libqfli_web_cdp_transport.so`: a byte-queue fixture implementing only
  `openSelf/read/write/close`. It has no network socket, native descriptor or
  endpoint selector. Its opaque handle strings exceed Number's exact integer
  range, so converting a handle to Number would break the fixture.
- `WebResourceResponse`: a response DTO recording the public setter calls.
  Numeric timer adapters retain the source's real 10 ms polling delay and
  20-second run deadline while allowing timer-leak inspection.

The fixture consumes only bytes actually accepted by each write. Independent
HTTP and WebSocket decoders validate the emitted discovery/upgrade requests,
fixed Host/path, fresh 16-byte key, FIN/RSV bits, client masking, minimal lengths,
decoded command IDs/order/parameters, Pong echo and normal-close payload. Server
replies use known byte sequences, with the accept derived independently from
the actual emitted key. The fixture does not call the proof's parser/encoder to
generate expected results.

Every case checks observable reports and closure of every opened fixture handle
exactly once, with no remaining source timer, truncated outgoing request/frame
or hidden fixture assertion failure. Error cases must emit a failure and must
not emit `complete: pass`. The success case also rejects a second public `run`.

## Observed cases

| Group | Count | Actual behavior asserted |
| --- | ---: | --- |
| Bootstrap and complete success | 2 | Static exact GET/HEAD response, denied foreign URL/POST, fixed CSP; split reads, short accepted fixture write counts, read/write EAGAIN and EINTR, fragmented UTF-8 across continuation frames, interleaved Ping/Pong, ordered frame/Runtime commands, number 42 and normal close. |
| Discovery and work bounds | 6 | Mismatched/duplicate bootstrap, foreign returned WS endpoint, duplicate Content-Length, HTTP header overflow and a stream of tiny reads reaching the source work bound. No rejected discovery can open a WS handle. |
| Upgrade and attached identity | 2 | Incorrect SHA-1 accept fails before CDP; wrong attached main-frame URL prevents Runtime commands. |
| Malformed server frames and EOF | 9 | Masked server frame, fragmented/oversized control frame, nonminimal 126/64-bit encoding, unexpected continuation, malformed UTF-8, frame over 256 KiB and EOF inside a payload. |
| RPC and cleanup failures | 4 | 128 events without the requested reply, CDP error reply bytes, evaluate returning 41 and a native-boundary Close error. No complete pass survives these failures. |
| Cancellation | 1 | Cancel while waiting on a real polling timer synchronously retires the fixture handle, emits cancellation, clears timers and produces no late report/pass after later supplied bytes and a 30 ms observation window. |
| **Total** | **24** | **All passed.** |

Observed test-loop duration: **466.7 ms**. The complete Node tool invocation
returned exit code **0** in approximately **0.98 seconds**, including loading and
transpilation. The positive partial-I/O case took **372.2 ms** with real polling
delays. These are observations for this run, not promised performance limits.

## Exact bounds and remaining coverage

Harness-enforced limits are **2 seconds per case**, **10 seconds for the test
execution loop**, **1 second for initial VM module evaluation per case**,
**50,000 transport-boundary calls per case**, and **1 MiB queued/accepted bytes
per direction per case**. SDK loading/transpilation occurs before the execution
loop watchdog. No source timeout is accelerated.

The frozen source separately limits native transfers to 4 KiB reads/64 KiB
writes, HTTP headers to 16 KiB, discovery to 64 KiB/128 targets, complete WS
messages to 256 KiB/256 frames, each reply wait to 128 incoming envelopes,
work to 3000 checkpoints and the RPC run to 20 seconds. The suite exercises
selected overflow/error paths; it does not prove every exact boundary value or
exhaust every malformed header/frame. In particular, actual deadline expiry,
the 64 KiB discovery/128-target edge, 256-frame edge, all close codes and all
possible transport errno/argument/environment states remain outside this run.

These adapters cannot establish native nonblocking/short-I/O behavior, errno
values on OHOS, SO_PEERCRED, NAPI cleanup/environment isolation, inbound ArkWeb
client authorization, absence of real TCP listeners, interception of every Web
request, socket/target disappearance or release-artifact behavior. Those remain
the separate native and real same-app/device gates in
[the owned-preview plan](web-owned-preview-plan.md). The sequence exercised here
contains no Debugger-domain breakpoint, pause, step or editor integration.

Text-hygiene verification covers both newly added UTF-8 files, including final
newlines, trailing whitespace, conflict markers and resolved local report links.
