# Old workspace cleanup after migration

Builds, tests, lint, dependency installation and package verification run in
GitHub Actions only. This applies to both workspaces and every agent.

Source and destination Codex lead the migration. Source workspace Codex in
`w64:p1` owns scope and final acceptance. Destination workspace Codex in
`w6V:p1` accepts the migrated clone. Only a Codex decision and a reviewed task
artifact authorize a cleanup step. An agent that finds a conflict reports it
instead of removing data.

## Required order

1. Complete the GitHub source and Trellis commit and record its full `main`
   SHA. Root stages, commits, pulls and dispatches. No agent runs `git push`.
   Root writes `D:/MyNewProjects/_orchestra/push/qflistudio-web.json` and the
   orchestration script performs the push. Only the origin push URL is narrowed
   to GitHub. The source keeps its mirror remotes and their refs inside `.git`.
   No agent runs `git push`, and no run may broadcast to a mirror.
2. Verify that the destination has only the GitHub origin. Bring `main` level
   with `pull --ff-only`.
3. Compare Git trees and source status in both directories. Record actual cloud
   run outcomes, including signing and toolchain blockers.
4. Obtain the destination Codex acknowledgement in `w6V:p1` of the final SHA
   through Herdr and record it verbatim.
5. Inspect local recovery data and credentials before deleting old data.
6. Remove only explicitly reviewed generated directories inside the old root.

Old root: `D:/MyNewProjects/qfli_web`.
New root: `E:/MyNewProjects/QFLIProjects/qflistudio-web`.

## Delivery facts

Cleanup does not change these facts.

- Six package outputs: Android APK, iOS IPA, OHOS HAP, Linux `tar.gz` plus
  `DEB`, Windows `zip` plus installer `EXE`, and macOS `DMG`. A platform that
  lacks its `DEB` or `EXE` is incomplete.
- Migration packages may be a debug-key APK, an unsigned IPA and an unsigned
  HAP. A skipped platform is a blocker, not a delivery.
- The source keeps its mirror remotes. Their refs stay in the source `.git`,
  and the external backup holds the former Git config. Only the origin push
  URL is narrowed to GitHub, so a gate request cannot broadcast to a mirror.
- A green local status is not a cloud gate. Only a recorded Actions run is.

## Recorded dispositions

| Date | Item | Disposition |
| --- | --- | --- |
| 2026-11-27 | Ten reviewed process job pointers under `.trellis/tasks/10-22-standalone-offline-ide/research/` | Moved to the external backup and removed by commit `768bf77`. Final outcomes, grants, scripts and narrative stay in the task. No directory deleted |

Backup root:
`D:/MyNewProjects/_migration-backup/qflistudio-web-20261127/transient-pointers`.
The backup holds the ten pointer files under their original relative paths. A
restore uses the backup copy after review, not `git reflog`.

A process pointer is transient job state, not an outcome record. Removing it
does not close an outcome. Keep every outcome, grant, script and narrative
record in the task. Git keeps the removed files reachable through commit
`768bf77` in history. Garbage collection cannot remove them while that history
remains reachable.

This document is an inventory and disposition record only. It authorizes no
deletion and no WSL unregistration. Every removal listed here needs its own
reviewed decision.

## Generated-directory candidates

Inspect each candidate before removal. Existence alone is not authorization to
delete a directory that has tracked files, unexpected source or a link target.

- `build/`, `.dart_tool/`, `node_modules/`
- `android/.gradle/`, `android/.kotlin/`, `android/.cxx/`, `android/app/.cxx/`
- `ohos/.hvigor/`, `ohos/build/`, `ohos/entry/build/`
- `ohos/node_modules/`, `ohos/oh_modules/`, `ohos/entry/oh_modules/`
- `windows/flutter/ephemeral/`, `linux/flutter/ephemeral/`,
  `macos/Flutter/ephemeral/`
- generated Python `__pycache__/` directories and ignored local crash logs

Use `git ls-files -- <relative-path>` for each candidate. An empty result is
necessary but not sufficient. Inspect source deltas, links and private data.
Resolve the exact absolute path and require it to remain beneath the old root.
Do not follow junctions, symlinks, SDK links or package-cache links. Keep file
operations in PowerShell with `-LiteralPath`. Do not pass enumerated paths to
another shell. Review a dry-run list before any recursive removal.

The old root also contains a directory named a single ASCII space. It holds
extracted Nginx scratch trees. Ordinary Windows path normalization is unsafe
for this name. Handle it as a separate exact-path cleanup after comparing any
local source changes with retained vendor sources and patches.

Do not use `git clean -fdx`, blanket recursive deletion, `flutter clean`, or a
build-after-clean validation command. Verification remains in GitHub Actions.

## Preserve

- All tracked source, vendor archives, licenses, checksums and patches.
- Existing product inputs such as Windows nginx.exe, Android Nginx jniLibs and
  OHOS prebuilt Nginx archives until cloud production replaces them explicitly.
- `.trellis/tasks`, specifications, scripts, reviewed journals and instructions.
- Old `.git` until dropped-stash and dangling-object recovery is reviewed.
- Private signing data in separate secure storage. Never upload it to GitHub.

## WSL boundary

The read-only inventory found these stopped WSL2 distributions on 2026-11-26:
`Ubuntu`, `qfli-terminal-test`, `qfli-terminal-al3-clean`,
`qfli-terminal-al3-test`, and `qfli-java-build`.

None is uniquely owned by this Web workspace. Their names do not prove that
their data is disposable. Coordinate their source and private-data
preservation with the product owners before unregistering them.
`wsl --unregister` deletes the distribution filesystem. It is not a cache
cleanup. No WSL distribution was started, exported or unregistered during this
Web migration.

## Destination rule

Do not copy any generated-directory candidate, SDK, dependency cache, raw
agent history or private runtime pointer to the new clone. Keep Actions
artifacts and caches in GitHub. Inspect logs remotely. A clean Git status means
clean source state. It does not claim that the old disk caches vanished.
