# Read-only native review — embedded Nginx / OHOS NAPI / lifecycle

Scope: read-only inspection of the native lifecycle paths this product ships.
No file outside `tool/nginx_smoke.dart`, `integration_test/nginx_runtime_test.dart`
and this task's own docs was modified. No `flutter`/`dart` was run.

Files inspected:

- `native/nginx/embedded/qfli_nginx.c`, `qfli_nginx.h`, `qfli_nginx_internal.h`
- `native/nginx/embedded/test_lifecycle.c`
- `ohos/entry/src/main/cpp/nginx_napi.cpp`, `include/qfli_nginx.h`, `CMakeLists.txt`,
  `types/libqfli_nginx_napi/{index.d.ts,oh-package.json5}`
- `ohos/entry/src/main/ets/entryability/{EntryAbility.ets,NginxBridge.ets}`
- `ohos/entry/{build-profile.json5,src/main/module.json5}`
- `ios/Runner/{AppDelegate.swift,EmbeddedNginxBridge.swift}`
- `lib/services/{nginx_host.dart,web_runtime.dart}`
- generated build-time patch `build/native/nginx/embedded.regen.patch`

## Findings

### N1 — HIGH: the native lifecycle sources are untracked (release integrity gap)

`git ls-files` does not track any of:

- `native/nginx/**` — the whole embedded engine wrapper, its internal header,
  the lifecycle C test, and the build helper scripts.
- `ohos/entry/src/main/cpp/**` — `nginx_napi.cpp`, `include/qfli_nginx.h`,
  `CMakeLists.txt`, the NAPI `types/` package, and `prebuilt/<abi>/libqfli_nginx.a`.
- `ohos/entry/src/main/ets/entryability/NginxBridge.ets`.
- `ios/Runner/EmbeddedNginxBridge.swift`.
- `scripts/build_nginx_embedded.sh`, `scripts/bundle_nginx_ios.sh`,
  `scripts/test_nginx_embedded.sh`.

`git check-ignore` returns nothing for them (exit 1); they are untracked, not
ignored (the `.gitignore` `native/` rule only covers
`apps/qfli_c/native/third_party/picoc/` and `**/native/build/`). Contrast with
Android, where `android/app/src/main/jniLibs/<abi>/libnginx_exec.so` **is**
tracked.

Impact: a clean checkout has no OHOS NAPI bridge, no iOS bridge, no embedded
wrapper, no CMake, and no OHOS prebuilt archive. The HAP and iOS app can only be
built from this working tree. This directly threatens the store-readiness claim.

Action needed (owner of the native track, not this task): `git add` the sources
and prebuilt archives above, or record why the prebuilt `.a` is intentionally
out-of-band. This task cannot stage them (not its files).

### N2 — LOW: `qfli_nginx_internal.h` is not self-contained

The header declares `ngx_log_t *qfli_nginx_initial_log(void);` but only forward
declares `struct ngx_cycle_s` / `struct ngx_connection_s`. `ngx_log_t` is a
typedef, so this header cannot be included before the nginx headers. In practice
it is always included after them in `qfli_nginx.c`, so it compiles — a hygiene
issue only. No runtime effect.

### N3 — LOW: `qfli_nginx_stop` reports success for an unknown-but-in-range token

`qfli_nginx_stop(token)` returns `0` whenever `0 < token <= qfli_last_token`,
even if that token belongs to an already-released job, and only forwards the
stop when `qfli_active` matches. `qfli_nginx_release` for a stale in-range token
also returns `0` without doing anything. The lifecycle test
(`test_lifecycle.c`) relies on repeated release being harmless, and the Dart
side (`_EmbeddedInstance._waitForExit`) ignores the return, so this is
intentional and safe. Recorded only so a future reader does not "fix" it into a
stricter contract and break the idempotent-release path.

### N4 — observed correct: lifecycle ABI matches the documented contract

- `start` validates prefix (`absolute`, ≤4096, directory), returns a positive
  token or negative POSIX error, and rejects a second start with `-EBUSY` while
  a job is owned.
- `poll` returns 0 pending / 1 completed (+exit code) / negative for an invalid
  token.
- `release` returns `-EBUSY` before completion and joins+releases afterward.
- SIGPIPE is blocked only on the worker thread (`pthread_sigmask` in
  `qfli_run`), and `test_lifecycle.c` asserts the host `sigaction` handlers and
  stdio descriptors are preserved across 100 cycles. This matches the spec's
  "never installs host signal handlers" requirement.

### N5 — observed correct: OHOS build does not use `executableBinaryPaths`

`ohos/entry/build-profile.json5` configures only `externalNativeOptions`
pointing at `src/main/cpp/CMakeLists.txt` with `abiFilters [arm64-v8a, x86_64]`.
`module.json5` contains no `executableBinaryPaths`. The CMake selects a per-ABI
`prebuilt/<abi>/libqfli_nginx.a` static archive and links a SHARED
`libqfli_nginx_napi`. This matches the spec's HarmonyOS rule (a standalone PIE
form makes `bm install` fail).

### N6 — observed correct: bridge failure mapping is consistent

OHOS `NginxBridge.ets` + `nginx_napi.cpp` and iOS `EmbeddedNginxBridge.swift`
map malformed payloads to `INVALID_ARGUMENT`, a negative start to
`NGINX_START`, and other negative lifecycle statuses to `NGINX_SESSION` —
matching the Dart `EmbeddedNginxHost` expectations and the spec table.
`EntryAbility.onDestroy` calls `stopActiveNginx()` so a destroyed ability stops
the worker before Dart necessarily releases its token; iOS mirrors this in
`deinit` with a bounded 200×50ms poll+release. Both are bounded and idempotent.

### N7 — NOTE: NAPI `Init` module struct

`nginx_napi.cpp` registers a NAPI module whose `Init` returns `exports` and
defines the five properties. The `napi_module` is registered via
`__attribute__((constructor))`, so the shared library self-registers on load,
which is what `import { version, start, poll, stop, release } from
'libqfli_nginx_napi.so'` in `NginxBridge.ets` expects. Consistent with
`types/libqfli_nginx_napi/index.d.ts`. No issue found.

## Overall

No *functional* defect was found in the C lifecycle, the OHOS NAPI bridge, the
iOS bridge, or the Dart `nginx_host` dispatch; the documented ABI and failure
mapping hold. The one release-critical problem is **N1 (untracked native
sources)** — it is a version-control/delivery gap rather than a code bug, and it
is outside this task's file ownership to fix.
