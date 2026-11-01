# OHPM local-dependency gap handoff, 2026-10-26

Read-only source preparation for the eleven-product parent. No OHPM, Hvigor,
SDK, native, WSL, Flutter, browser, HDC or device process was started. No lock,
junction, manifest, platform file, core file or existing runner was modified.
Only two research files exist for this subject: this handoff and
[`run-web-ohpm-window.py`](run-web-ohpm-window.py).

## Status: BLOCKED, no execution path

`run-web-ohpm-window.py` reports the gap and never starts OHPM. It has no option
that authorizes registry access and no deferred "later network" path. The
precondition is missing rather than tested: the declared local dependency is
absent from the generated resolution surfaces, so the source graph is
incomplete before any tool runs.

```
python -X utf8 .trellis/tasks/10-22-standalone-offline-ide/research/run-web-ohpm-window.py
{"status": "BLOCKED", "reason": "source graph incomplete: the declared local
 dependency is absent from the generated resolution surfaces, so local-only OHPM
 resolution is unproven; OHPM is not started", "runnable": false,
 "ohpmStarted": false, ...}
```

Exit code 1, no process, no file. `--snapshot-only` prints the same surfaces
without writing. A named `--grant` with a fresh `--run-name` writes one
`refusal.json` for that grant and still starts nothing. A future executable
window would need a new reviewed design, not a flag added to this supervisor.

Cause of the gap: the generated locks and module map predate the CDP
declaration. Regenerating them needs OHPM, which is exactly the unproven local
resolution. Hand-editing them, or creating a manual junction, would fabricate a
map instead of proving resolution, so neither is done.

## Exact local-dependency gap

`libqfli_web_cdp_transport.so` is declared but absent from every resolution
surface. `libqfli_nginx_napi.so` is present in all of them, so the difference is
specific to the CDP package, not to local packages in general.

| Surface | nginx NAPI | CDP transport |
| --- | --- | --- |
| `entry/oh-package.json5` dependency | present | present (`file:./src/main/cpp/types/libqfli_web_cdp_transport`) |
| `entry/oh-package-lock.json5` specifiers + packages | present | **absent** |
| `oh_modules/.ohpm/lock.json5` `overrideDependencyMap.entry` | present | **absent** |
| `oh_modules/.ohpm/lock.json5` `modules.entry.dependencies` | present | **absent** |
| `oh_modules/.ohpm/lock.json5` `packages` | present | **absent** |
| `entry/oh_modules/libqfli_*` | Junction to the types directory | **absent** |
| types package source | `types/libqfli_nginx_napi` | `types/libqfli_web_cdp_transport` (present) |

Checked and not the gap:

- `ohos/oh-package-lock.json5` (root) holds only the dev `@ohos/hypium@1.0.6`
  registry entry. The root manifest declares no dependencies, so this file is
  not the surface that should carry the CDP package.
- `ohos/.hvigor/dependencyMap/*.json5` record module paths and the override map,
  not per-module dependency entries, so they contain no CDP row for the same
  reason.
- The types package is complete: name `libqfli_web_cdp_transport.so`, version
  `1.0.0`, `types: ./index.d.ts`, exports `openSelf/read/write/close`.
- `SelfCdpProof.ets` already imports `libqfli_web_cdp_transport.so`, so the
  unresolved surface is resolution, not source.

## Frozen inputs

Hashes match the earlier native audit for the shared files: entry manifest
`7bfeb446…`, entry lock `c0a9b4cd…`, module map `79f4df23…`, CMakeLists
`7879c264…`. Recorded here as well: CDP `index.d.ts` `a4a94492…`, CDP types
manifest `222cae56…`, `SelfCdpProof.ets` `775c65e3…`, dependency-map files
`cbac85fb…` / `39c89710…`, root lock `afefb3b8…`.

## Runner surface

- `--snapshot-only`: hash the 12 inputs, print `surfaces`, `gap` and hashes.
  No grant, no process, no write, no bytecode.
- `--grant <id> --run-name <fresh>`: write one `refusal.json` under a fresh
  evidence directory that records the grant, blocker, gap, surfaces and source
  hashes. No phase, no Job, no publication, no lock or junction change.
- No arguments: print the blocker without writing.

The report always states `ohpmStarted: false`, `processStarted: false` and
`executionPath: "none"`.

## Still open

- The resolution surfaces remain incomplete; regenerating them requires OHPM.
- CDP native outputs remain absent for both ABIs; the native window is separate.
- Hvigor API26 ArkTS/ArkUI compilation is the real import/type gate.
- Module import, same-app ArkWeb protocol and device evidence remain unrun.
- The existing release HAP and locks must be preserved before any tool change.

## Root review checklist

1. Confirm the gap table against `--snapshot-only` output, not this prose.
2. Treat the blocker as an incomplete source graph, not as a failed network test.
3. Confirm no lock, junction or manifest was edited by hand, and that the runner
   still has no execution path.
4. Keep native and application windows separate from this resolution subject.