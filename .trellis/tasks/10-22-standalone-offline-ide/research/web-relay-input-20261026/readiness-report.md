# Web relay readiness input, 2026-10-26

Source-only readiness input for the four policy and broker repair files. Nothing
ran beyond the read-only captures named below. No grant was read or consumed. No
READY was published. No channel message was sent. No product or core source file
was edited.

Directory: `.trellis/tasks/10-22-standalone-offline-ide/research/web-relay-input-20261026/`

Manifest: `readiness-input.json`

## 1. Snapshot-only commands discovered first

Each frozen runner documents one read-only entry point.

| Runner | Read-only command | What it starts |
| --- | --- | --- |
| `run-web-relay-window.py` | no arguments | `snapshot()` only |
| `run-web-app-window.py` | `--snapshot-only` | hash and core HEAD only |
| `run-web-native-window.py` | `--snapshot-only` | hash only |
| `run-web-ohpm-window.py` | `--snapshot-only` | hash of 12 surfaces only |

All four exited 0 with empty stderr. Captures: `captures.json` plus four
`*.stdout.json` files.

Reviewed mode was never executed. `--execute-reviewed`, `--grant`, `--run-name`,
`--next-owner` and `--authorization` are absent from every command. The capture
script refuses those flags in code.

Relay snapshot reports `execution: false`, `processStarted: false`,
`executionState: REVIEWED_GRANT_REQUIRED`, `frozenMatch: true`, `mismatches: []`.

## 2. Correction: `--snapshot-only` carries no hashes

The app runner's `--snapshot-only` branch prints only four summary fields: the
file count, the core HEAD, the helper hash and the runtime paths. It calls
`snapshot()`, then prints `len(source["files"])`. The per-file hashes are dropped
before printing.

So the earlier input was wrong to treat that summary as a hash set. A count
without hashes cannot bind anything.

## 3. Full read-only inputs, `app-full-inputs.json`

`capture-app-full-inputs.py` verifies the three frozen pins, imports the pinned
`run-web-app-window.py` under a private module name, and calls `snapshot()`
directly. `snapshot()` was inspected before the import:

- it reads and hashes files, and resolves tool paths with `shutil.which`,
- it runs exactly one subprocess: `git -C <core> rev-parse HEAD`,
- `execute()`, which starts a Job through `helper.OwnedJob()`, is reached only
  from `main()`, which sits behind `if __name__ == "__main__":`.

The script asserts the guard held. It never calls `load_helper`, `run` or
`execute`, and it has no grant argument. One subprocess ran:
`git -C core rev-parse HEAD`.

Result: `app-full-inputs.json`, 332 files with real per-file `path`, `bytes` and
`sha256`.

| Field | Value |
| --- | --- |
| Files | 332 |
| Canonical files SHA256 | `0FA1747B8869149BB10D62A89764C5D5EE17FC27603FBF58150A7C47D851C300` |
| File SHA256 | `2DDB7E3846BAE9550DAEF5574CC21169407EDD8932373CAF088F1F115E9C572C` |
| Core HEAD | `64f0aa75a773c632a1101ce16e1900615b274960` |
| Per-file hash case | lowercase, as the frozen `hashlib.hexdigest()` emits |

All five formatter paths appear in this snapshot with matching bytes and matching
hashes. The frozen snapshot emits lowercase hex; the manifest cases them up for
comparison, and the bytes match exactly.

The full capture was refreshed after the product commit below. The canonical
`filesSha256` stayed `0FA1747B…`, so the commit changed no input file.

## 4. Frozen interface

| File | Pinned SHA256 | Live match |
| --- | --- | --- |
| `run-web-app-window.py` | `D80C46E1…92A19` | yes |
| `run-web-app-worker.ps1` | `074AC022…B8B78` | yes |
| `run-web-owned-window.py` | `9DF7A943…D7FBE` | yes |

Protocol `web-relay-format-app/v1`. Window 180 s.

Reviewed authorization module `web_relay_authorization.py` hashes to
`84445442…`, which equals the wrapper pin. This proves the bytes are the reviewed
ones. It proves no authority.

## 5. Formatter paths and repair files

The wrapper names exactly five formatter paths. The first four are the repair set.

| Path | Bytes | SHA256 | Repair |
| --- | --- | --- | --- |
| `lib/services/owned_preview_policy.dart` | 16038 | `9F0319AF…15802` | yes |
| `lib/services/owned_preview_resource_broker.dart` | 11793 | `56FD917C…13D5` | yes |
| `test/owned_preview_policy_test.dart` | 17688 | `9324590B…2B639` | yes |
| `test/owned_preview_resource_broker_test.dart` | 19454 | `6F41B712…8A913` | yes |
| `test/web_offline_browser_test.dart` | 9073 | `506C3972…29D098` | no |

The four repair files keep the hashes the current review holds. Their sizes
differ only against the older static review record: broker 11495 to 11793, and
broker test 18588 to 19454. That is a note against the older review, not a hash
mismatch against the current one.

## 6. Product and core metadata

Product HEAD `26b5d14fa1ec8df46f4331625bf72fef6aea7f27`, branch
`feat/offline-web-ide`, subject "test(web): add reviewed terminal observer
controls". That commit adds exactly three research files and no product source.
`researchOnly: true`.

| Committed file | Bytes | SHA256 |
| --- | --- | --- |
| `…/research/run-web-observed-relay-window.py` | 26038 | `D1943BD1…6552B3` |
| `…/research/test_web_observed_relay_window.py` | 23212 | `81D61C8B…60DEDC` |
| `…/research/web-observed-relay-handoff-20261026.md` | 4953 | `F1987825…D96344` |

Observer hash checks, bound in the manifest as `observers`:

- final observer `run-web-observed-relay-window.py` expects
  `D1943BD1E622FC3CA5FE327E1473A141B3AF992CF48FC61F078F3140FC6552B3` and the live
  working bytes still match.
- test `test_web_observed_relay_window.py` expects
  `81D61C8B0F639222725DF141AB9E63FD07280C9C053EBC065775BB777E60DEDC` and the live
  working bytes still match.

Hash was rechecked after the commit. The commit did not alter working bytes, so
both hashes hold.

Core HEAD `64f0aa75a773c632a1101ce16e1900615b274960`, branch `main`. Core status
has 42 entries, all 42 hashed, `completeWipFiles: true`, rollup
`E6A927615BFB2BF30C3C…`.

## 7. Two authoritative inputs

- Freeze manifest `863F97CEB34FCB491780F1BA4AC38DADF472E1BA28C0CF0F7A522F89BA4E04D0`,
  `qfli_c` commit `0851e56`, binding **164 files**; all 164 hashes match the live core.
- Full app inputs of **332 files**, canonical
  `0FA1747B8869149BB10D62A89764C5D5EE17FC27603FBF58150A7C47D851C300`.

The old C782 input `web-app-c782-20261026/source-before.json` also holds 332
files, at core `2f9039a3…`. It is not reusable. Same count, stale metadata.

## 8. Defect found and fixed in this build

The core status read stripped the whole porcelain output. That erases the leading
status space of line one, so slicing the codes then cut the first filename
character. The first row became code `M ` and path
`trellis/spec/frontend/index.md`, a path that does not exist, with its hash
dropped.

Fixed by splitting the raw output and keeping each line exactly, and by expanding
untracked directories with `--untracked-files=all`. If a directory ever survives
expansion, `completeWipFiles` is false and the directory is listed in
`wipDirectoryEntries`. It is not counted as a hashed file.

## 9. Drift risks

1. `--snapshot-only` binds no hashes. A count alone must never be treated as a
   hash set. Only the direct `snapshot()` capture binds bytes.
2. `run-web-relay-window.py` is not in the frozen pin set. Edits are invisible to
   `frozen_mismatches()`. Live hash recorded: `401F61D4…DB0FDB3`.
3. The five formatter paths are named, not pinned. Any edit after this input
   invalidates it.
4. The core worktree is live: this build saw 42 entries, the wider session saw 44.
   The rollup is point-in-time.
5. The 164-file freeze binds a working tree, not a clean commit.
6. The 332-file capture is recomputed per run. Any input file change alters the
   count and the canonical hash. It was refreshed after commit `26b5d14` and did
   not change.
7. Status is read in universal-newline mode; a filename with a raw CR would
   split. None exists now.
8. Windows host paths only. Nothing transfers to OHOS or a device.

## 10. Not proven

- No formatter, test, analysis, content or gate phase ran for this input.
- No reviewed authorization record was created, read or consumed.
- No successor name, channel message or READY publication was made.
- The frozen supervisor was imported only to call `snapshot()`. Its main is
  guarded, and `load_helper`, `run` and `execute` were never called.
- A dirty core worktree is recorded, not validated.
- Runtime acceptance stays closed. No formatter, test, analysis, content or gate
  phase ran, so a policy or broker pass is not claimed. Source READY is a separate
  matter: the reviews plus the full capture bind the exact bytes, so source READY
  may be published without waiting for a gate run.

## 11. Source READY freeze

These bytes are frozen for source READY. Any later edit to any of them voids the
freeze.

| Frozen item | SHA256 |
| --- | --- |
| Readiness manifest | `226CB055D74439B6B7319D9796AEC62D70329144FDAB35FFEBBFD295AC7DA91A` |
| Full 332-file inputs | `2DDB7E3846BAE9550DAEF5574CC21169407EDD8932373CAF088F1F115E9C572C` |
| Canonical files digest | `0FA1747B8869149BB10D62A89764C5D5EE17FC27603FBF58150A7C47D851C300` |
| App snapshot capture | `BB10387ECD6056570696F1B96F5DBA194F5AECF771F1C5C1606659FDEBE0B46C` |
| Freeze manifest | `863F97CEB34FCB491780F1BA4AC38DADF472E1BA28C0CF0F7A522F89BA4E04D0` |
| Final observer | `D1943BD1E622FC3CA5FE327E1473A141B3AF992CF48FC61F078F3140FC6552B3` |
| Observer test | `81D61C8B0F639222725DF141AB9E63FD07280C9C053EBC065775BB777E60DEDC` |

Independent check by root at `2026-10-26T04:59:42Z`: all 332 paths, hash bytes
and byte counts drifted 0 against the full inputs. The full-input hash and the
manifest hash matched the values above.

Scope of the freeze: source review and capture. Runtime acceptance stays closed.