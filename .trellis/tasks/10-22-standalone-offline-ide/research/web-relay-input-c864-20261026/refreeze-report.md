# C864 refreeze, source only

New window. New directory. The historical directory `web-relay-input-20261026`
is preserved byte for byte and is not rewritten.

Nothing ran except the pinned `snapshot()` call plus one `git rev-parse`. No SDK,
no Job, no grant, no READY, no channel message, no native or OHPM recapture, no
product or core edit. No new protocol, receipt or authorization path.

## Files in this directory

| File | Purpose |
| --- | --- |
| `capture-app-full-inputs.py` | pinned pin check, then `snapshot()` only |
| `app-full-inputs.json` | full 332-file capture with per-file hashes |
| `build-readiness-input.py` | manifest builder, read only |
| `readiness-input.json` | the freeze manifest |
| `refreeze-report.md` | this note |

Nothing else is written here. The old builder's native and OHPM default captures
are not recaptured and are not dependencies of this one.

## Scope, exactly what was captured

Full app input snapshot, current core work, seven pins, five formatter paths.
Nothing wider.

## Seven frozen pins

| Role | File | SHA256 | Match |
| --- | --- | --- | --- |
| observer | `run-web-observed-relay-window.py` | `D1943BD1…6552B3` | yes |
| test | `test_web_observed_relay_window.py` | `81D61C8B…60DEDC` | yes |
| wrapper | `run-web-relay-window.py` | `401F61D4…DB0FDB3` | yes |
| authorization | `web_relay_authorization.py` | `84445442…7A1DE4` | yes |
| runner | `run-web-app-window.py` | `D80C46E1…5922A19` | yes |
| worker | `run-web-app-worker.ps1` | `074AC022…7FB8B78` | yes |
| helper | `run-web-owned-window.py` | `9DF7A943…A7DFBE` | yes |

The wrapper's own internal pins for runner, worker, helper and authorization
still equal these live hashes.

## Five formatter paths, four repair files

| Path | Bytes | SHA256 | Repair |
| --- | --- | --- | --- |
| `lib/services/owned_preview_policy.dart` | 16038 | `9F0319AF…715802` | yes |
| `lib/services/owned_preview_resource_broker.dart` | 11793 | `56FD917C…AF13D5` | yes |
| `test/owned_preview_policy_test.dart` | 17688 | `9324590B…7B639` | yes |
| `test/owned_preview_resource_broker_test.dart` | 19030 | `FFB4E6EC…ACC3F8` | yes, new and **UNRUN** |
| `test/web_offline_browser_test.dart` | 9073 | `506C3972…29D098` | no |

The fixture cleanup is new and has never run. The production broker bytes did run
in C843, and the gate failed there: 320 PASS and 1 FAIL. Neither the production
bytes alone nor the combined candidate is a pass.

## Current heads and work

- Product HEAD `d863397122f2a3f0e3f6df5cbe066873f959d902`, branch
  `feat/offline-web-ide`, subject "docs(web): record observed app validation
  results". Read live from git, never hardcoded.
- Core HEAD `5b3c48c7d1c1822d0ee348b68eb6b33f3bba54d0`, branch `main`.
- Core work: 42 entries, 42 hashed, `completeWipFiles: true`, rollup recorded.

## Full inputs

332 files, canonical
`7B87BB2676D7E90892536BCAB0158132064A19660972D93B0B08450A3937F7B5`, core HEAD
`5b3c48c7…`. Per-file hashes are lowercase, as the frozen `hexdigest()` emits.

## Historical 164 freeze and the 864 supervisor override

The historical freeze `863F97CE…` binds 164 files and is **not** claimed as a
164-hash match today. Its live state is measured:

- 164 bound, **163 unchanged**, 0 missing,
- exactly one change: `lib/services/process_supervisor.dart`,
  parent `25BA430C…` replaced by `095DE8C17C66DC206FE170B3F99B7447D8660F183085ECB338F97484FF0E5BFC`,
  which matches the stated 864 override exactly.

The manifest records this as an explicit new override beside the historical
binding. It does not rewrite the historical freeze.

## Permitted changes against the preserved parent capture

Delta of the 332-file set against `web-relay-input-20261026/app-full-inputs.json`:

- added: none,
- removed: none,
- changed: `../qfli_studio_core/lib/services/process_supervisor.dart` and
  `test/owned_preview_resource_broker_test.dart`.

`permittedOnly: true`, `unexpectedChanges: []`. Those two are the supervisor
replacement and the fixture cleanup. Nothing else moved.

## Not proven

- No formatter, test, analysis, content or gate phase ran for this input.
- The combined candidate, production bytes plus the fixture cleanup, is UNRUN.
- The broker production bytes were exercised in C843 and the gate failed there:
  320 PASS, 1 FAIL. No new pass is claimed.
- No READY publication, channel message, grant or successor was made.
- The supervisor was imported only to call `snapshot()`. Its guard held, and
  `load_helper`, `run` and `execute` were never called.
- The historical freeze remains a source binding, not a tested acceptance.