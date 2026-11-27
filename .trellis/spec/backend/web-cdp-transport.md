# OHOS self-only CDP transport and test proof

## 1. Scope / Trigger

Read this before changing the OHOS Web CDP native connector, NAPI package,
same-process protocol client, debugging switch owner or test ability route.
The source owners are
[`web_cdp_transport.h`](../../../ohos/entry/src/main/cpp/web_cdp_transport.h),
[`web_cdp_transport.cpp`](../../../ohos/entry/src/main/cpp/web_cdp_transport.cpp),
[`web_cdp_transport_napi.cpp`](../../../ohos/entry/src/main/cpp/web_cdp_transport_napi.cpp),
[`SelfCdpProof.ets`](../../../ohos/entry/src/ohosTest/ets/testability/SelfCdpProof.ets)
and the test-only
[`SelfCdp` page](../../../ohos/entry/src/ohosTest/ets/testability/pages/SelfCdp.ets).

As of **2026-10-23**, the native integration has source/static-review evidence;
the separate exact-source host protocol fixture passed 24/24. Actual
native and API26 ArkTS compilation, current-HAP packaging, module import and
same-app ArkWeb execution are pending. A declared API, prepared regression,
successful build or host protocol fixture is not an OHOS debugger pass.
This transport does not enable ArkWeb, advertise product capabilities or provide
a production debugger. See the
[implementation record](../../tasks/10-22-standalone-offline-ide/research/web-cdp-transport.md),
[test-proof record](../../tasks/10-22-standalone-offline-ide/research/web-self-cdp-proof.md)
and [owned-preview plan](../../tasks/10-22-standalone-offline-ide/research/web-owned-preview-plan.md)
for evidence boundaries. Existing release/build coordination still applies.

## 2. Signatures

The default-visible C ABI consists of exactly four operations:

```c
int64_t qfli_web_cdp_open_self(void);
int qfli_web_cdp_read(int64_t handle, uint8_t *buffer, size_t capacity);
int qfli_web_cdp_write(int64_t handle, const uint8_t *bytes, size_t length);
int qfli_web_cdp_close(int64_t handle);
```

The local module `libqfli_web_cdp_transport.so`, registered as
`qfli_web_cdp_transport`, exposes the corresponding NAPI declarations:

```ts
interface OpenResult { status: number; handle: string; }
interface ReadResult { status: number; bytes: ArrayBuffer; }
openSelf(): OpenResult;
read(handle: string, capacity: number): ReadResult;
write(handle: string, bytes: ArrayBuffer): number;
close(handle: string): number;
```

The test client is single-use. Its public surface is `bootstrapUrl: string`,
`response(address: string, method: string): WebResourceResponse`,
`run(callback: (report: SelfCdpReport) => void): Promise<void>` and
`cancel(): void`. Reports contain `stage: string`, `state: string` and
`detail: string`; `QfliSelfCdp` is the hilog tag. Only an observed
`complete: pass` after actual replies and native cleanup proves that narrow
test sequence. It has not yet been observed on OHOS.

## 3. Contracts

### Native endpoint, ownership and I/O

- `open_self()` computes only the abstract Unix address
  `\0webview_devtools_remote_<getpid()>`. Its sockaddr length includes the leading
  NUL and actual name bytes, excluding the trailing formatting NUL. Do not use
  `strlen()` over `sun_path`. No caller-selected PID/path/host/port, endpoint scan,
  `/proc` discovery, listener, forward or TCP fallback is permitted.
- Create the stream with `SOCK_NONBLOCK | SOCK_CLOEXEC`. Required missing socket
  features fail closed; do not substitute a blocking socket. There are no runtime
  environment variables that select an endpoint or enable debugging.
- A fixed mutex-protected library table permits **8** live handles across all
  callers. Positive int64 tokens increase monotonically and never repeat in that
  library lifetime; exhaustion returns `-EOVERFLOW`. Handles are not raw file
  descriptors. Every successful handle, including pending/failed ones, remains
  caller-owned until Close retires it.
- `EINPROGRESS` may yield a pending handle. Each read/write checks readiness with
  zero-timeout `poll`, then `SO_ERROR`, before transferring bytes. An AF_UNIX
  connect `EAGAIN` has **not** queued a pending connection: close that new fd and
  return `-EAGAIN` without allocating a token. A caller may retry a fresh Open
  within its deadline; the current narrow proof instead reports that Open error.
- Before any application bytes, require supported `SO_PEERCRED`, exact `ucred`
  size and `peer.uid == getuid()`. This checks the **server endpoint reached by
  this client**. It does not authenticate ArkWeb itself or establish ArkWeb's
  authorization of **incoming debugger clients**. A same-UID endpoint can still
  require identity verification, and foreign-UID listener denial is a separate gate.
- Read/write spans must be nonnull and **1..65536** bytes. C validates nullness
  and length; the trusted caller must own the actual allocation. No pointer is
  retained. Positive read/write results are actual counts; retry only a write's
  unaccepted suffix. `EAGAIN`/`EWOULDBLOCK` normalize to `-EAGAIN`; interrupted
  transfers return `-EINTR` without an internal retry loop.
- Read EOF is sticky zero and preserves a potentially writable half. Terminal
  connect/transfer failure closes the fd and latches errno while retaining token
  ownership. Writes use `MSG_NOSIGNAL`, without altering process signal handlers.
- Close retires the token before closing the fd and never retries a failed
  `close`, including EINTR. Positive stale/unknown Close is zero; nonpositive
  Close is `-EINVAL`. Stale read/write is `-EBADF`, without touching another fd.

### Decimal NAPI boundary

- Open returns `{status: 0, handle: "<positive int64>"}` on allocation, possibly
  pending; operational failure returns negative errno and `handle: ""`.
  Keep handles as strings: Number conversion can round valid int64 tokens.
- Handle inputs must be canonical `[1-9][0-9]{0,18}` and at most `INT64_MAX`.
  Reject signs, leading zero, whitespace, embedded NUL, fractions, overflow and
  nonstring inputs. Argument counts are exact.
- Read capacity must be an integer in **1..65536**. A positive `status` equals
  the returned ArrayBuffer's exact length; EOF/error/EAGAIN returns an empty
  buffer. Write accepts only a real, nonempty ArrayBuffer up to 65536 bytes,
  without coercing typed-array views or SharedArrayBuffer.
- Invalid arguments throw `INVALID_ARGUMENT`. Wrapper allocation/publication
  failures throw `CDP_TRANSPORT_NAPI`; they close the owned connection if an
  Open/read/write result could otherwise be lost. Operational errno is returned.
- Each NAPI environment owns its own token set. Valid foreign/stale read/write
  returns `-EBADF`; Close of a nonowned positive token is harmless zero. An
  environment cleanup hook closes only its tokens; FFI callers retain their own
  responsibility. This environment isolation is not a renderer security boundary.

### Opt-in test ability and bounded protocol proof

- Only the `ohosTest` TestAbility may select `testability/pages/SelfCdp` with
  `qfliSelfCdpProof=true` and `qfliCatalogCdp=unix`. Reject other modes for this
  route. The ability owner calls the **one-argument**
  `setWebDebuggingAccess(true)` and disables it on owned stop, load failure,
  window destruction and ability destruction. The page never changes this switch.
- `TestAbility` is a singleton. Mode is read in `onCreate`; `onNewWant` handles
  only `qfliCatalogStop=true`. Stop the owned old test instance and cold-start a
  fresh one with both opt-in parameters. Sending mode wants to the live catalog
  ability does not change its route or switch it to this proof.
- The page owns one incognito Web at a fresh 192-bit random synthetic loopback
  bootstrap URL. Return its scriptless static HTML through interception, with
  `default-src 'none'; base-uri 'none'; form-action 'none'`. All other resources
  receive 403; a closed/missing proof owner must also return an explicit 403,
  because `null` permits a real load. Both navigation callbacks deny when the
  page is not alive or the URL differs. These source guards do not prove every
  ArkWeb scheme/POST/worker/network-isolation behavior.
- Through `openSelf()` only, GET `/json/list` with fixed Host `localhost`.
  Require HTTP200 bounded Content-Length JSON, one exact random-URL page match,
  and exactly `ws://localhost/devtools/page/<that target ID>`. Do not select the
  first target, open a returned host, or execute project JS before identity proof.
- A second self-only Unix handle upgrades that exact path. Validate HTTP101,
  Upgrade/Connection tokens and the SHA-1/Base64 accept of a fresh 16-byte key;
  reject duplicate headers, extensions, subprotocols and HTTP body framing.
  Mask every client frame using fresh cryptographic bytes. Validate unmasked
  server frame bits/opcodes/lengths/continuations/UTF-8; handle Ping/Pong/Close.
- `Page.getFrameTree` must confirm the same main-frame URL before actual
  `Runtime.enable` and fixed `Runtime.evaluate` `(6 * 7)`. Require a remote number
  42 without exception details; receiving an unrelated event or schema does not
  count. This does not establish Debugger breakpoints, pause/step or editor UI.
- Bound bootstrap load to **10 s**, RPC run to **20 s**, active/poll work to
  **3000** turns, native reads to **4 KiB**, HTTP headers to **16 KiB**, discovery
  to **64 KiB / 128 targets**, complete WS messages to **256 KiB / 256 frames**,
  and events before each reply to **128**. Poll retries use a cancellable 10 ms
  timer. Use fatal `util.TextDecoder.create('utf-8', { fatal: true })` decoding.
  Cap report detail at 512 characters and visible transcript at 8 KiB.
- On success send a masked normal-close frame; always close native handles in
  `finally`. `cancel()` closes only this module's handles and wakes/rejects its
  pending work. Page disappearance cancels before stopping its Web and guards
  late visible updates. Page stop/close does not prove target/socket removal.

## 4. Validation & Error Matrix

| Condition | Required result |
| --- | --- |
| C span null/zero/>65536 | `-EINVAL` before transport state access |
| Native table full / token exhaustion | `-EMFILE` / `-EOVERFLOW`, no new fd leak |
| Missing peer support / wrong peer UID | Fail closed (`-ENOTSUP` or actual option errno / `-EACCES`) before bytes |
| AF_UNIX Open EAGAIN | Negative result with no handle; fresh Open required for retry |
| Pending/no readable bytes/write backpressure | `-EAGAIN`; caller polls asynchronously with a deadline |
| Read EOF / terminal error | Sticky zero / latched negative errno, retaining token until Close |
| Native Close EINTR/error | Return errno after retirement; never retry fd Close |
| Malformed NAPI handle/capacity/buffer/count | Throw `INVALID_ARGUMENT`; no transport mutation |
| Valid foreign NAPI token | Read/write `-EBADF`; Close zero; original owner's fd survives |
| NAPI result cannot be published after I/O | Retire owned connection and throw `CDP_TRANSPORT_NAPI` |
| Proof mode with TCP/missing Unix opt-in | Fail initialization; never open a proof TCP listener |
| Bootstrap absent, ambiguous target or foreign main URL | Visible bounded fail; no evaluate or fallback attachment |
| Bad discovery/upgrade/frame/RPC, EOF or timeout | Visible exact-stage failure and native cleanup |
| Page disposed while work is pending | Cancel owned transport/timer; explicit403 callbacks; no late visible state |
| Actual ArkWeb cannot be reached over self Unix | Record gate failure; no TCP fallback, fake success or ordinary Run substitution |

## 5. Good/Base/Bad Cases

- **Good:** current owned test HAP, a fresh Unix-only instance and no forwards;
  exactly one random target and its frame URL agree, actual Runtime replies
  return 42, native handles close, and separately recorded teardown/security
  probes satisfy their own assertions.
- **Base:** source and prepared fixtures exist, but compile/HAP/device evidence
  is pending. Report precisely this status and leave R8/R10 gates open.
- **Bad:** display debugger controls because the `.so` exists; claim inbound
  authorization from a successful same-UID client check; attach to the first
  target; convert tokens to Number; or silently enable TCP after Unix failure.

## 6. Tests Required

Run only in the globally coordinated host/device window. The real connector
fixture command is `bash scripts/test_web_cdp_transport.sh /explicit/output`.
It builds the exact C++ connector and executes
[`test/native/test_web_cdp_transport.py`](../../../test/native/test_web_cdp_transport.py).
Require real abstract-socket assertions for no-engine fd cleanup, null/oversized
spans and canaries, binary/short I/O, EAGAIN, half-close, default SIGPIPE survival,
eight-handle exhaustion, fresh-Open backlog recovery, stale tokens and concurrent
close/reuse. The prepared fixture is not a recorded pass. Pending-connect,
int64-exhaustion and foreign-UID branches need their own evidence.

Compile the actual OHOS CMake target and NAPI wrapper for arm64-v8a and x86_64;
inspect ELF machine, 16 KiB load alignment and four exported C symbols. Run full
Hvigor API26 ArkTS/ArkUI compilation, local package resolution and current-HAP
archive checks. Test NAPI exact arguments, int64 boundaries, empty/error buffers,
environment isolation/cleanup and post-I/O allocation failure. An SDK declaration
or a standalone weaker type check cannot replace the application build.

Protocol regressions must exercise actual proof source with bounded deterministic
transport fixtures for partial I/O/EINTR/EAGAIN, malformed or oversized HTTP,
wrong/ambiguous target, host/path/accept mismatch, masked client frames, server
fragmentation/control/invalid UTF-8, RPC errors, timeout and cancellation cleanup.
Such host fixtures establish protocol behavior only; they do not establish an
ArkWeb connection, inbound authorization or a device result.

The exact-source fixture `node scripts/test_self_cdp_protocol.mjs` recorded
24/24 passing cases on 2026-10-23; see the active task's
`research/web-self-cdp-protocol.md` for its frozen source hash, boundary doubles,
independent byte decoder and coverage limits. Its SDK TypeScript transpilation
does not type-check ArkTS, resolve real imports or execute the native connector.

The real same-app gate records current HAP SHA, core revision, OS/API/ArkWeb/ABI,
own PID/socket name, fresh cold-start wants, actual proof reports and no HDC
forwards/TCP listeners. Independently verify current ArkWeb inbound client policy,
controlled foreign-UID denial, static-switch/socket disappearance, owned-target
removal, stop/relaunch and release-artifact behavior. A forced system-debug
setting or unverified listener policy leaves that gate open. Actual
Debugger-domain breakpoints/pause/resume/steps, owned-preview offline behavior
and shared editor composition remain later separate acceptance stages.

## 7. Wrong vs Correct

**Wrong:** call `setWebDebuggingAccess(true, 9222)`, forward the device port,
attach to `targets[0]`, then describe a console reply as secure product debugging.

**Correct:** enable the one-argument Unix-only lease in its test owner; reach only
the own-PID abstract socket, verify the fresh random target and main-frame URL,
consume actual expected replies, and close owned resources. Report inbound
authorization, no-listener and release cleanup results independently; leave every
unproven product capability unavailable.

**Wrong:** `const handle = Number(openSelf().handle)` or return `null` from an
interceptor after clearing its owner.

**Correct:** retain the exact decimal string for all native operations; cancellation
retires that ownership, and detached-page callbacks return explicit403 and deny
navigation instead of permitting an uncontrolled real load.
