# Native self-socket transport implementation slice

Date: **2026-10-23, Asia/Shanghai**. Task: R8/R10 product-owned OHOS preview.
This implements the first native transport slice of
[the owned-preview plan](web-owned-preview-plan.md). It does **not** deliver a
Web preview, CDP/WebSocket client, debugger provider or accepted native debugger.

**Validation state: source and static review only.** No compiler, Linux fixture,
OHOS build, WSL operation, Flutter/browser, HDC or device command was run for this
slice. The shared host/device queue remains authoritative. All runtime checks
below are pending until the root grants the appropriate slot.

## Changed files and boundary

- [web_cdp_transport.h](../../../../ohos/entry/src/main/cpp/web_cdp_transport.h)
  defines the four-function C ABI and explicit buffer/status/lifetime contract.
- [web_cdp_transport.cpp](../../../../ohos/entry/src/main/cpp/web_cdp_transport.cpp)
  implements the nonblocking self-only AF_UNIX client and handle table.
- [web_cdp_transport_napi.cpp](../../../../ohos/entry/src/main/cpp/web_cdp_transport_napi.cpp)
  exposes four thin operations to trusted ArkTS, retaining the same endpoint and
  transfer limits. It implements no HTTP, WebSocket or CDP protocol.
- [CMakeLists.txt](../../../../ohos/entry/src/main/cpp/CMakeLists.txt)
  adds only the independent `qfli_web_cdp_transport` shared target. It links the
  SDK NAPI library and pthread; existing Nginx/syntax targets and sources are
  unchanged. The target uses hidden C++ visibility and exports the C ABI.
- [local type package](../../../../ohos/entry/src/main/cpp/types/libqfli_web_cdp_transport/oh-package.json5)
  and [ArkTS declarations](../../../../ohos/entry/src/main/cpp/types/libqfli_web_cdp_transport/index.d.ts)
  follow the existing Nginx package structure without modifying that package.
- [Linux fixture](../../../../test/native/test_web_cdp_transport.py) and
  [explicit harness](../../../../scripts/test_web_cdp_transport.sh) exercise the
  actual connector source when later run. They do not substitute a mocked socket.

No shared-core, product profile/page/ability, preview/runtime, Nginx ABI or syntax
implementation was modified. The parent owns the test-only ArkTS proof.

## Native ABI

```c
int64_t qfli_web_cdp_open_self(void);
int qfli_web_cdp_read(int64_t handle, uint8_t *buffer, size_t capacity);
int qfli_web_cdp_write(int64_t handle, const uint8_t *bytes, size_t length);
int qfli_web_cdp_close(int64_t handle);
```

The sole address is `\0webview_devtools_remote_<getpid()>`. The abstract address
length includes its leading NUL and actual name bytes, excluding the formatting
buffer's trailing NUL. There is no path/host/PID/port argument, listener, network
socket, endpoint scan, `/proc` discovery, forwarding, fork or protocol logic in the
connector. Its own PID convention comes from the official ArkWeb debugging guide;
abstract-name byte/length semantics come from Linux `unix(7)`. [P1, P2]

`socket()` atomically requests `SOCK_NONBLOCK | SOCK_CLOEXEC`. Missing compile-time
flag definitions cause `-ENOTSUP`; socket creation failures preserve errno. There
is no permissive blocking fallback. The descriptor
never leaves the library. A fixed table allows **8** outstanding handles. Positive
int64 tokens increase monotonically, never repeat and fail with `-EOVERFLOW`
instead of wrapping. The table is protected by one pthread mutex; each held-lock
operation performs only bounded nonblocking syscalls and copies at most 64 KiB.
There is no native worker thread or allocation queue.

| Operation/state | Result and ownership |
| --- | --- |
| `open_self`, immediately connected | Positive handle only after validating peer credentials. Caller owns it. |
| `open_self`, `EINPROGRESS` | Positive pending handle. Each read/write first polls with timeout zero and checks `SO_ERROR`; it returns `-EAGAIN` while pending. Caller needs a deadline and must close on expiry. |
| `open_self`, AF_UNIX `EAGAIN` / another immediate failure | Close the new descriptor and return negative errno, with no handle allocated. In particular a full Unix backlog is retried by a **fresh** open; it is not treated as a queued pending connection. [P3] |
| Pending connection becomes ready | Validate peer credentials before allowing any application bytes. A completed error is latched and its descriptor closed; the token remains owned until Close. |
| Read/write has no data/space | `-EAGAIN`, preserving the connection and caller buffer. `EWOULDBLOCK` is normalized to `EAGAIN`. |
| Transfer interrupted before progress | `-EINTR`, without an internal retry loop. Caller may retry or close. |
| Read | Actual positive byte count; zero for EOF. EOF stays sticky for reads and does not close a still-writable half. A later terminal write error supersedes EOF with the latched failure. |
| Write | Actual accepted byte count, including a short write. Retry only the unaccepted suffix. Local acceptance is not peer delivery acknowledgement. [P4] |
| Terminal transfer error | Close the descriptor and latch negative errno for later calls; the token still occupies its slot until Close. |
| Stale/nonpositive read/write handle | `-EBADF`, without touching another slot or descriptor. |
| Close of a positive handle | Retire it before closing. Repeated/unknown positive Close is zero and cannot close a later connection. Nonpositive Close is `-EINVAL`. A close syscall error is returned, but the retired handle is never reused. |

Every read/write length must be **1..65536**, and the pointer must be nonnull.
Invalid spans return `-EINVAL` before touching transport state. C cannot verify
the allocation behind a pointer: the trusted native/FFI caller must own a readable
or writable region of the stated length. No caller pointer is retained.

Writes use `MSG_NOSIGNAL`; no process-wide signal handler or signal mask is changed.
Close is never retried after EINTR because descriptor reuse can make a retry affect
an unrelated descriptor. These choices follow the Linux syscall contracts; they
still need the actual OHOS build/runtime evidence. [P4, P5]

## Outbound peer check is not ArkWeb listener authorization

Both immediate and completed pending connections require `SO_PEERCRED`, an exact
`ucred` result and `peer.uid == getuid()`. A mismatched UID fails `-EACCES` before
read/write; unavailable credential support fails closed. The installed API 26
SDK declares the required socket flags, option, `ucred`, `getpid()` and `getuid()`.
Linux documents this option for connected Unix stream sockets. [P2, L1]

This protects the connector against a different-UID endpoint using its expected
name. It does **not** establish that the peer is ArkWeb, that a same-UID process
cannot spoof a name, or that ArkWeb rejects other incoming clients. The parent
must still bind a random bootstrap to the actual Web target and prove the current
engine's inbound security and socket teardown. No TCP fallback exists here.

## Thin NAPI interface

The new module name is `qfli_web_cdp_transport`, library
`libqfli_web_cdp_transport.so`. It uses the standard SDK module registration and
`napi_add_env_cleanup_hook`; the installed SDK declarations were inspected, but
the wrapper is **not yet compiled or executed**. The exact interface is:

```ts
openSelf(): { status: number; handle: string }
read(handle: string, capacity: number): { status: number; bytes: ArrayBuffer }
write(handle: string, bytes: ArrayBuffer): number
close(handle: string): number
```

- Open status zero means a positive handle was allocated, possibly pending.
  A negative errno returns an empty handle string. The decimal string preserves
  all positive int64 bits without ArkTS Number rounding.
- Handle arguments must be canonical `[1-9][0-9]{0,18}` and at most `INT64_MAX`;
  leading zero, sign, whitespace, NUL, fraction, overflow and nonstring inputs
  throw `INVALID_ARGUMENT` before a native call.
- Read capacity must be an integer in 1..65536. A positive status is the exact
  length of the returned ArrayBuffer; EOF/error/EAGAIN returns an empty buffer.
- Write accepts a real, nonempty ArrayBuffer of at most 65536 bytes; typed-array
  views and SharedArrayBuffer are not implicitly coerced. Return is accepted byte
  count or negative errno. No pointer is held after the callback.
- Argument counts are exact. Operational errno is returned, while invalid
  arguments or NAPI allocation failures throw stable errors.
- Each NAPI environment tracks only its own handles. A syntactically valid
  stale/foreign read/write returns `-EBADF`; Close of a nonowned positive handle
  is harmless. Its cleanup hook closes only its owned handles. FFI-owned handles
  remain the FFI caller's responsibility.
- If result allocation fails after bytes were read/written, close that owned
  handle and throw; do not silently lose a byte prefix and keep a broken stream.

The root registered the following local dependency under
`ohos/entry/oh-package.json5`, observed during this review. **This slice did not
edit the shared manifest or lock.**

```json
"libqfli_web_cdp_transport.so": "file:./src/main/cpp/types/libqfli_web_cdp_transport"
```

Any lock refresh/build remains a serialized parent action. The test-only ArkTS
ability/page can then import these four functions directly, poll EAGAIN with
`setTimeout`, and implement its own bounded discovery/upgrade/protocol proof.
No page JS proxy or production profile/UI is added by this import. A Flutter FFI
alternate entry is unnecessary for this first same-process ArkTS proof.

## Prepared regression and pending validation

The Linux harness later compiles **the exact connector source**, excluding only
the SDK-specific NAPI wrapper, into a small shared library and loads it in Python.
The fixture binds only the documented abstract name for **its own process PID**.
It does not start ArkWeb, contact a device, make TCP connections or override the
production endpoint. Its `/proc/self/fd` observation is only for fd counts, flags
and a freshly created own-client fd: a temporary duplicate sets a small send
buffer to force a real short write. It never discovers a connection endpoint.

The seven prepared cases cover:

1. No-engine connection failure over 100 opens with no descriptor leak.
2. Null/zero/oversized spans, caller-buffer canaries, exact binary short read/write,
   EAGAIN, half-close EOF, writable half retention and idempotent stale Close.
3. Real kernel short writes, buffer backpressure/EAGAIN, exact accepted bytes and
   recovery after the peer drains; actual nonblocking/close-on-exec fd flags.
4. Eight-handle bound, ninth-open failure without leak, generation change and an
   old token's inability to close the new descriptor.
5. Full abstract-Unix backlog returning open `-EAGAIN`, no leaked pending handle,
   and a fresh successful open after accepting the queued connection.
6. Broken-peer writes with SIGPIPE's default action, requiring process survival
   and an unchanged handler, plus failed-handle cleanup.
7. Concurrent reads/closes and slot reuse across real ctypes threads, with bounded
   completion and unchanged descriptor count.

Once a Linux host slot is explicitly granted, the command is:

```sh
bash scripts/test_web_cdp_transport.sh /explicit/output/directory
```

It compiles with `-Wall -Wextra -Werror`, runs the complete fixture under a
30-second timeout and prints all case results. No output artifact or PASS record
exists yet. The EINPROGRESS completion branch, int64 exhaustion, foreign-UID
rejection and NAPI argument/environment cleanup still require separate relevant
evidence; the Linux fixture must not be presented as covering those branches.

### Static audit completed

`trellis-check` was applied within the parent's source-only constraint. The nine
implementation files above have no trailing whitespace, conflict markers or
missing final newline. The Python fixture was parsed with `ast.parse` without
importing or executing it; the local type-package JSON parsed and its declaration
file resolved. All nine local report links resolved. `git diff --check` passed
for the tracked CMake edit. The installed SDK's cleanup-hook, callback-argument,
ArrayBuffer and module declarations were compared with the wrapper.

Manual review followed descriptor ownership through immediate/pending Open,
peer rejection, partial transfer, sticky EOF, terminal failure, token retirement,
environment teardown and result-allocation failure. Read bytes are copied before
publishing the ArrayBuffer to ArkTS. The prepared fixture verifies latched
terminal failures/raw-fd release and forces every concurrency worker to execute
at least one operation. These are source findings, not native test passes.

### Exact deferred native target command

The current release CMake caches for both ABIs point at this workspace and the
installed SDK toolchain. After the parent grants a host build slot, the following
PowerShell block from the repository root builds only the new native target,
one ABI/job at a time, then prints the actual ELF header, load segments and
dynamic symbols. Ninja's normal CMake regeneration consumes the new target.

```powershell
$sdkNative = 'D:/ProgramFiles/Huawei/DevEco Studio/sdk/default/openharmony/native'
$cmake = "$sdkNative/build-tools/cmake/bin/cmake.exe"
foreach ($abi in @('arm64-v8a', 'x86_64')) {
  & $cmake --build "ohos/entry/.cxx/default/default/release/$abi" --target qfli_web_cdp_transport --parallel 1
  if ($LASTEXITCODE -ne 0) { throw "Native target failed for $abi" }
  $library = "ohos/entry/build/default/intermediates/cmake/default/obj/$abi/libqfli_web_cdp_transport.so"
  & "$sdkNative/llvm/bin/llvm-readelf.exe" --file-header --program-headers --dyn-syms $library
  if ($LASTEXITCODE -ne 0) { throw "ELF inspection failed for $abi" }
}
```

Review for the expected AArch64/x86-64 machine, at least 16 KiB load alignment,
the four default-visible `qfli_web_cdp_*` symbols, and the expected NAPI/pthread/
libc++ imports. This command does not package or execute the module. The actual
HAP and same-app proof remain the parent's separate integration commands.

Scheduling estimates, **not measurements**: reserve one compiler job and about
0.5 GiB RAM, allowing roughly two minutes for both small SDK targets. The Linux
harness has one compilation followed by a Python fixture with four reader
threads and at most eight live transport handles; its runtime portion is capped
at 30 seconds. Reserve a separate roughly one-minute Linux slot plus compiler
startup. No HDC/device access is required for these two native checks.

After that, separately build the actual OHOS target and verify exported C symbols,
module import and both packaged ABIs. The next **own application ArkWeb** gate must
use this connector with the one-argument debugging API, no HDC forward/TCP listener,
matching own PID and random bootstrap target, real Runtime/Debugger enable and
pause/control behavior, then actual target and socket cleanup. That gate remains
open. A passing POSIX fixture or build cannot close R8/R10.

## Primary references

- **P1** — [Official OpenHarmony debugging guide](https://github.com/openharmony/docs/blob/f41b9345badd47c7ab0c263344cd7f4b5a549afb/en/application-dev/web/web-debugging-with-devtools.md), pinned official source: abstract socket naming and owning application PID.
- **P2** — [Linux man-pages unix(7)](https://man7.org/linux/man-pages/man7/unix.7.html): abstract address bytes/length, peer credentials and send-buffer behavior. Abstract names have no pathname permission protection.
- **P3** — [Linux man-pages connect(2)](https://man7.org/linux/man-pages/man2/connect.2.html): AF_UNIX EAGAIN, EINPROGRESS, readiness/SO_ERROR and retry semantics.
- **P4** — [Linux man-pages send(2)](https://man7.org/linux/man-pages/man2/send.2.html): actual accepted count, EAGAIN and MSG_NOSIGNAL.
- **P5** — [Linux man-pages close(2)](https://man7.org/linux/man-pages/man2/close.2.html): descriptor reuse, multithreaded Close and why not to retry a failed Close.
- **L1** — Installed official SDK **26.0.0.105**, native `sysroot/usr/include/sys/socket.h`, `sys/un.h`, `unistd.h`, `napi/native_api.h`. `napi_add_env_cleanup_hook`, ArrayBuffer APIs and the actual existing Nginx module/type-package registration were read before implementation. SDK declarations are not runtime proof.
