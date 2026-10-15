# Preserve Android and OHOS builds while clearing historical audit storage

## Goal

Archive historical audit source and evidence, remove only obsolete audit and temporary emulator trees, retain Android/OHOS incremental caches and verify both release builds.

## Requirements

- Remove only `build/native/platform-audit` and `build/native/validation` after archiving historical source, patches, scripts and small test evidence locally.
- Preserve normal Android/OHOS build inputs, final packages, `build/native/nginx`, `build/app`, `.dart_tool`, Gradle/OHOS caches and platform dependencies.
- Unlink junctions and symlinks without following their targets into SDK, global Pub Cache or other projects.
- Preserve unrelated dirty work and commit only this task's records using Conventional Commits.

## Acceptance Criteria

- [x] The two obsolete generated trees are removed; before/after byte counts and preservation archive hash are recorded.
- [x] Original tracked and untracked source work remains intact.
- [x] Android release APK builds after cleanup.
- [x] OHOS release archive builds after cleanup; product signing is recorded separately.
- [x] No device commands or sibling workspace changes are performed.

## Notes

- Lightweight storage maintenance task; application and build configuration code are unchanged.
- Direct maintenance on `main`, with no PR; use the documented archive branch-validation exception.
