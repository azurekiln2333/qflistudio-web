# Self-only CDP follow-up source review

Reviewed **2026-10-23, Asia/Shanghai** using the Trellis check checklist within
the parent's explicit read-only/no-build boundary. This review found **no new
confirmed source defect** in the resource, concurrency, environment-cleanup or
protocol paths inspected. That finding is a source-review result, not native,
ArkTS, HAP or ArkWeb acceptance. No compiler, test runner, Flutter, Chromium,
WSL, CMake, HAP, HDC or device operation was started. Only this report was added.

## Evidence and current protocol result

Read the task PRD/design/implementation plan, backend
[CDP contract](../../../spec/backend/web-cdp-transport.md),
[native implementation record](web-cdp-transport.md),
[proof record](web-self-cdp-proof.md), actual connector/NAPI/proof/page source,
both regression harnesses and the installed official API26 SDK declarations.

The separately executed
[protocol fixture report](web-self-cdp-protocol.md) records **24/24 passed** with
SDK TypeScript **4.9.5** and Node **v24.15.0**. This review did not rerun it. A
read-only file hash check confirmed the current `SelfCdpProof.ets` still matches
that report's SHA-256:

```text
775c65e32f50542a52cd38c7a4be794fffc446670b0e6b4f43f54e693c144653
```

Those 24 cases are supplementary host protocol-fixture evidence only. Actual
C++/NAPI execution, API26 ArkTS/ArkUI compilation, current-HAP import and the
same-process ArkWeb Unix connection remain unverified by this review.

## Resource and concurrency trace

- In [the connector](../../../../ohos/entry/src/main/cpp/web_cdp_transport.cpp),
  Open/Read/Write/Close all hold the same `ConnectionLock`. A Close retires its
  table entry before closing its descriptor, and monotonically increasing
  int64 tokens prevent a later slot reuse from becoming an old handle. A stale
  positive Close therefore cannot race another connector operation into closing
  a newer descriptor.
- Immediate Open failures close their new fd without allocating a token.
  AF_UNIX `EAGAIN` is correctly returned as a failed fresh Open, rather than
  retaining an unqueued connection. Pending completion performs zero-timeout
  readiness and SO_ERROR checks, then validates the peer before application
  bytes. Failed pending/terminal transfers close the fd and retain the latched
  failure/token until explicit Close.
- EOF is sticky for reads while the write half remains available. Partial write
  counts are returned without silently retrying a prefix; sends use
  `MSG_NOSIGNAL`. Close is not retried on EINTR, so a reused OS fd cannot be
  affected by a retry. These are the inspected branches; their actual OHOS
  syscall behavior was not executed.
- In [the NAPI wrapper](../../../../ohos/entry/src/main/cpp/web_cdp_transport_napi.cpp),
  each callback carries its own `EnvironmentHandles`. Syntactically valid
  nonowned read/write is rejected before the C call; nonowned Close does not
  touch a library token. The cleanup hook closes only the environment's positive
  entries before deleting its owner. Registration failure deletes the still
  unused owner; partial export failure leaves it with the registered cleanup
  hook so any already-exported callback data is not freed early.
- NAPI argument-array capacity is bounded to three and requests one extra
  argument beyond each operation's expected count, allowing extra arguments to
  be rejected. Decimal parsing checks int64 overflow before multiplication.
  ArrayBuffer pointers are used only synchronously. Read bytes are copied before
  properties are published. Open/read/write result-publication failure retires
  the owned token instead of leaving a stream with a lost byte result.

No resource leak or close/reuse violation was established in these source traces.
The prepared Linux fixture actually targets these C ABI paths, but no native
fixture result was produced or inferred in this review.

## API26 declaration and lifecycle comparison

The installed SDK declarations match the used `TextDecoder.create`, fatal
UTF-8 options, `TextEncoder.encodeInto`, Base64 helper, random-byte and SHA-1
digest calls, own process PID, and Web request/navigation callback fields.
The cleanup-hook, callback-data, ArrayBuffer and module-registration C signatures
also match the wrapper. No additional API26 declaration mismatch was found.
This comparison does not run ArkTS semantic checks or ArkUI compilation.

The prior source corrections are present: closed-page interception returns an
explicit403 instead of `null`, and both navigation guards deny when `!alive`.
The page cancels its own proof before Web stop and guards late visible text.
The singleton TestAbility still selects mode only in `onCreate`; `onNewWant`
handles the stop request only. The documented cold-start requirement therefore
matches the current source, and a mode want delivered to an existing catalog
instance must not be presented as a successful proof launch.

## Fixture independence and limits checked

[The Node harness](../../../../scripts/test_self_cdp_protocol.mjs) reads and
transpiles the entire actual proof module without extracting/replacing its
HTTP, WS or RPC methods. Cases use its public constructor/response/run/cancel
surface. Independent outgoing-byte decoders check actual accepted prefixes,
Host/path, the random key/accept relationship, client mask bytes, control echoes,
RPC order and parameters. Error cases check the visible failure and absence of
`complete: pass`; cleanup checks detect outstanding handles, duplicate Close,
timers, truncated emitted frames and fixture assertions swallowed by source.
This did not reveal a substituted parser or self-fulfilling protocol oracle.

The fixture deliberately substitutes SDK and NAPI imports. In particular its
transport is an enumerable JavaScript object, whereas the native exports use
SDK `napi_default` property descriptors. SDK TypeScript's CommonJS namespace
helper enumerates properties; the real ArkTS loader has its separate native
module mapping. Consequently this fixture cannot verify the actual native
namespace import. That concrete boundary difference is **not** a confirmed
ArkTS import failure and is not counted as a new source bug; actual module
import remains part of the pending OHOS build/runtime gate.

The report already limits its coverage: no real 20-second expiry, full set of
boundary values/close codes, NAPI allocation/environment failures or native
syscalls is established by the 24 cases. The source's cancellation/work bound
and selected malformed-byte paths are meaningful supplementary checks without
closing those remaining gates.

## Acceptance boundary retained

The outbound same-UID server-peer check remains separate from ArkWeb's inbound
client authorization. This source review supplies no new evidence of foreign-UID
denial, absence of a CDP TCP listener, socket/target disappearance, release-HAP
behavior, Debugger-domain operations or editor composition. There is no TCP
fallback in the inspected connector/proof. R8/R10 stay open until their actual
native and owned-view acceptance records exist.
