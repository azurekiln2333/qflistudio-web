# Native platform-channel offline URL boundary

Date: **2026-10-23, Asia/Shanghai**. This slice supplies the policy and regression
for the native URL-validation gap in `qflistudio/platform.openUrl`. The integrated
EntryAbility guard permits only explicit-port
HTTP(S) URLs whose original authority is literal `127.0.0.1` or `[::1]`.

**Current-worktree fixture result: 13/13 scenario groups passed after root
integrated the guard; the earlier 12/13 failing baseline is preserved below.**
The worktree includes pre-existing startup-progress implementation; a separate
explicit profile verifies a clean HEAD-plus-guard candidate without that work.
The saved candidate run also passed **13/13**, with the `absent` startup profile
and **116** actual-handler dispatches; source identities were independently
rechecked below. No ArkTS
compilation, OHOS intent launch, browser or device evidence is claimed here.

## Ownership and integration

This slice adds exactly three files:

- [OfflinePreviewPolicy.ets](../../../../ohos/entry/src/main/ets/entryability/OfflinePreviewPolicy.ets)
  owns the pure original-string predicate.
- [test_native_offline_channel.mjs](../../../../scripts/test_native_offline_channel.mjs)
  executes the actual EntryAbility and policy source with boundary doubles.
- This report records the contract and actual verification state.

The root completed the narrow existing-file integration in
[EntryAbility.ets](../../../../ohos/entry/src/main/ets/entryability/EntryAbility.ets):
import `isOfflinePreviewUrl` from `./OfflinePreviewPolicy` and reject before
constructing the `Want`:

```ts
if (!isOfflinePreviewUrl(url)) {
  result.error('OFFLINE_ONLY', 'Only explicit-port loopback HTTP(S) preview URLs are allowed', null);
  return;
}
```

No existing EntryAbility/startup/share/picker/Nginx implementation was edited by
this slice. Their relevant dispatch/lifecycle behavior is checked by the new
fixture rather than changed to accommodate it.

Repository HEAD already contains the window/share/picker/Nginx behavior, but
does not contain the worktree's pre-existing `startupProgress` handler. The
publishable URL-guard change does not include that unrelated startup work. The
harness therefore selects the expected startup behavior explicitly rather than
requiring that pre-existing work to publish the URL regression.

## Policy contract

`isOfflinePreviewUrl(input: string): boolean` also rejects nonstring runtime
values: a channel `as string` assertion is erased during execution. It never
coerces an arbitrary object's `toString`, resolves a hostname, looks up a listener,
decodes/canonicalizes an endpoint or rewrites the original URL.

Accepted authorities are exactly `127.0.0.1:<port>` and `[::1]:<port>`, under
case-insensitive `http://` or `https://`. Ports use canonical decimal digits with
no sign or leading zero and range **1..65535**. A path, query or fragment may
follow. Ordinary Unicode/percent-encoded path data and encoded query values are
preserved; the channel forwards the exact accepted original string.

Rejected input includes credentials, hostname/DNS aliases, LAN/public/wildcard
addresses, other 127/8 spellings, abbreviated/octal/hex/integer IPv4 aliases,
IPv4-mapped IPv6, noncanonical/zone-qualified IPv6, missing/invalid ports, other
schemes, raw backslashes, raw whitespace, and raw C0/C1 controls. The anchored
literal authority ends before `/`, `?` or `#`; later path/query text cannot change
which authority the predicate accepts.

This is an endpoint filter, not handler authentication or proof of session
ownership. Any matching loopback port satisfies this predicate. It does not
provide owned-Web navigation/resource isolation or prevent an external system
browser from subsequently navigating elsewhere. Those broader R8/R10 preview
gates remain separate.

## Supplementary actual-handler fixture

The harness reads and transpiles the actual EntryAbility and policy files with
the installed official SDK's existing TypeScript file:

```text
D:/ProgramFiles/Huawei/DevEco Studio/sdk/default/openharmony/ets/build-tools/ets-loader/node_modules/typescript/lib/typescript.js
```

It uses `transpileModule` and `vm.Script`, without source replacement or
extracted copies of the handler. The policy import resolves to the actual helper
exports. SDK/Flutter/plugin/Nginx/picker boundaries are explicit doubles: the
actual EntryAbility creates a captured `MethodChannel`, and tests dispatch its
real registered `onMethodCall` handler. The harness reads local source/SDK files;
native channel, picker/file operations, share panel, Nginx engine, intent,
browser and endpoint lookup remain doubles.

The **13** prepared scenario groups cover **12 accepted/81 rejected URL vectors**
through both the pure policy and the actual handler; accepted values must produce
the exact original `viewData` Want, and rejected values must settle with
`OFFLINE_ONLY` before any `startAbility`. Other cases check browser-launch error
propagation, profile-specific valid/invalid startup progress behavior, exact share record
and error mapping, all five picker delegations with original call arguments,
unknown-method behavior, dark/light window background and superclass continuation,
plugin/Nginx configuration, and Nginx stop before superclass destruction.

Picker/Nginx assertions establish preserved delegation/lifecycle ordering at the
EntryAbility boundary; they do not revalidate those modules' internal native or
filesystem behavior. `transpileModule` does not perform semantic ArkTS checking,
SDK type resolution or actual OHOS linkage.

From the repository root, after the root's guard integration:

```powershell
node scripts/test_native_offline_channel.mjs
```

The default `--startup-progress present` profile asserts clamping, event identity
and `INVALID_PROGRESS` behavior for the current worktree. An explicit `--entry
<path>` selects another complete EntryAbility source file; relative paths resolve
from the command's working directory. The policy remains the actual workspace
`OfflinePreviewPolicy.ets`, and neither source is rewritten or extracted. For the
root's clean HEAD-plus-only-import/guard candidate, use:

```powershell
node scripts/test_native_offline_channel.mjs --entry "<clean-candidate-path>" --startup-progress absent
```

The `absent` profile dispatches all **13** valid and invalid `startupProgress`
calls and asserts `notImplemented` with no emitted events. It does not silently
skip those cases. Both profiles execute the same **93 URL vectors**, all other
regressions and the same **116 actual-handler dispatches** when passing. The
script prints the selected startup profile, entry path and exact source hashes;
an invalid profile or missing entry file fails.

`QFLI_OHOS_TYPESCRIPT` may override the path to an already-installed SDK copy;
there is no dependency installation/download. The script prints actual SDK path,
TypeScript version and both source SHA-256 hashes, and verifies neither source
changed during execution. Limits are **500 ms per channel result**, **5 seconds
for the test loop**, and **1 second per initial VM module evaluation**. Local SDK
loading/transpilation occurs before the test-loop watchdog.

## Actual verification record

### Historical failing baseline, before guard integration

- Ran `node scripts/test_native_offline_channel.mjs` with Node **v24.15.0** and
  installed SDK TypeScript **4.9.5**. Observed exit **1**, **12/13** scenario groups
  passing, **36** actual-handler dispatches, **14.6 ms** test-loop time and about
  **0.44 seconds** for the complete tool invocation.
- All **12 accepted/81 rejected** pure-helper vectors passed. All 12 accepted
  handler vectors preserved exact original Want URIs. Launch errors and every
  startup/share/picker/window/Nginx scenario passed.
- The actual-handler rejection group failed on its first vector, the empty
  string: the unintegrated handler called `startAbility` and returned success
  instead of `OFFLINE_ONLY`. The remaining 80 handler-rejection vectors were not
  reached in that group. This is direct fixture evidence of the pre-integration
  source gap, not a guarded-handler pass.
- Root was notified of the ready helper and exact import/guard. Its live-agent
  status later reported a tool-service HTTP429 error; this slice preserved the
  explicit prohibition on editing existing EntryAbility WIP. The guard and
  subsequent green actual-handler run were pending root recovery at that point.
- Exact source hashes during the baseline run:

  ```text
  OfflinePreviewPolicy.ets d0173a6295fdb4a87fd4333b4c60134c55072646102bf907e06b8ec2efc95369
  EntryAbility.ets         ee3f99a49cf7170f99cfa555a120e5cd7b6f3e9831c05a293017b5962d69ce37
  ```

### Parent-reported passing run, after guard integration

- Root subsequently recovered, integrated the import and pre-Want guard, and ran
  `node scripts/test_native_offline_channel.mjs`. Root reported exit **0**,
  **13/13** scenario groups passing, **12 accepted/81 rejected URL vectors**,
  **116** actual-handler dispatches and **23.2 ms** test-loop time.
- The guarded-handler result covers all rejection vectors that the historical
  baseline could not reach. This is a lightweight actual-source fixture pass;
  the SDK/Flutter/plugin/picker/Nginx/intent/browser boundaries remain doubles.
- Current source hashes were independently read and match the guarded sources:

  ```text
  OfflinePreviewPolicy.ets d0173a6295fdb4a87fd4333b4c60134c55072646102bf907e06b8ec2efc95369
  EntryAbility.ets         9fb0ed1a4353fda08b46f43d1ecaf92770d0e2661c5f6b66e2563919b27c5938
  ```

- This report records the parent's run without rerunning the unchanged suite.

### Changed harness, explicit present-profile verification

- After adding the entry/profile flags, ran
  `node scripts/test_native_offline_channel.mjs` once against the current
  worktree. Output selected `startup-progress=present`; exit was **0**, all
  **13/13** scenario groups passed, with **12 accepted/81 rejected URL vectors**,
  **116** actual-handler dispatches and **13.4 ms** test-loop time (about
  **0.49 seconds** for the complete invocation).
- Both source hashes remained the same as the parent-reported guarded run
  above. This pass includes the worktree's pre-existing startup behavior and
  does not establish that behavior as part of the URL-guard change.
- Clean HEAD-plus-guard verification under `--startup-progress absent` is pending
  receipt of the root-owned candidate path. No alternate EntryAbility source was
  created or existing EntryAbility edited by this slice.

- Native SDK compiler, Flutter, WSL, browser, HDC and device operations were not
  invoked for this channel-fixture slice.
- Actual ArkTS build, installed artifact, browser-intent behavior and complete
  owned-preview offline isolation remain pending independent gates.

### Saved clean HEAD-plus-guard candidate, absent-profile verification

On **2026-10-23**, this documentation refresh read the root's actual
[candidate-run log](native-offline-candidate.log) and independently compared its
inputs with the current files. This supersedes the earlier pending-candidate
statement while preserving that historical record. The unchanged suite was not
rerun by this refresh.

The saved invocation selected
`--entry build/content/EntryAbility-offline-candidate.ets --startup-progress absent`.
It records **13/13** scenario groups, **12 accepted/81 rejected URL vectors**,
**116 actual-handler dispatches** and **13.5 ms** test-loop time. Both valid and
invalid startup-progress groups passed by receiving `notImplemented` without
events; those calls were executed rather than skipped. The log does not include
a process exit-code field, so this refresh reports its explicit result lines
without inventing separate terminal-exit evidence.

Read-only comparison used product HEAD
`e0f81a56230ec27890b67eb9ac0c1df71a805c71`. After newline normalization, the
[candidate source](../../../../build/content/EntryAbility-offline-candidate.ets)
equals HEAD's complete EntryAbility plus exactly the policy import and pre-Want
guard shown above. No `startupProgress` handler is present. The actual current
worktree EntryAbility remains a separate present-profile source.

| Input or saved evidence | Independently read SHA-256 |
| --- | --- |
| HEAD EntryAbility blob | `72967aa5c1a3a6d539b4fccc3b4a4c79510d477def2f378da5aa831e701a40b0` |
| Current OfflinePreviewPolicy, matching the log | `d0173a6295fdb4a87fd4333b4c60134c55072646102bf907e06b8ec2efc95369` |
| Candidate EntryAbility, matching the log | `2babb7944a2386fc59db38eaaff33f44fba405839933fe4438d63a8fccfcae31` |
| Current worktree EntryAbility, unchanged from the present-profile record | `9fb0ed1a4353fda08b46f43d1ecaf92770d0e2661c5f6b66e2563919b27c5938` |
| Saved candidate-run log | `b2eefc972c2883e6342085c8aea05485538464cb5e7bf5082a7b5bc8afc1803b` |

The log identifies the installed SDK TypeScript **4.9.5** and the same policy
path used by the other profile. This remains an actual-source channel fixture
with SDK/plugin/picker/Nginx/intent/browser boundary doubles. It establishes
neither semantic ArkTS compilation nor an installed OHOS result, browser
navigation isolation or debugger acceptance. This refresh started no test,
compiler, Flutter, Chromium, WSL, HAP or device process and changed no source.
