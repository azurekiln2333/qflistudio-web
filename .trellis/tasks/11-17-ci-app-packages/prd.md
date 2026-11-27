# CI: build cloud artifacts for six platforms

## Goal

One GitHub Actions workflow builds the QFLIWebForge application package for
Android, iOS, OHOS, Linux, Windows and macOS. The developer downloads packages
from GitHub instead of building each platform locally.

## Background

- At the initial audit, existing workflows (`native-build.yml`,
  `native-apple-build.yml`, `native-ohos-build.yml`) built native libraries
  only. Their artifacts were not APK, HAP or IPA. This is historical context,
  not the current application-workflow status.
- The canonical sibling directory is `../qflistudio-core`. The Dart package
  and import name remains `qfli_studio_core`. Every platform job must use the
  same immutable core commit recorded below.
- The tracked OHOS profile is sanitized: `signingConfigs` is empty and the
  product has no `signingConfig`. SDK, product and bundle settings remain
  tracked. CI signing material may come only from Actions secrets. Any local
  original or backup stays outside migration and must not be staged.
- HarmonyOS command-line tools have no public fixed download URL.
- Android currently defaults to a debug-key release APK. iOS has no Apple
  signing team or provisioning profile.
- Windows ships the tracked `assets/runtime/nginx/windows/nginx.exe` and builds
  the QuickJS DLL with GCC/Clang (`windows/CMakeLists.txt:55-89`).
- Linux and macOS build Nginx during the application build
  (`linux/CMakeLists.txt:101-124`, `scripts/bundle_nginx_macos.sh`).
- `.trellis/spec/backend/release-verification.md` requires unsigned and
  debug-key builds to be reported as such, and forbids committing private
  signing data.

## Immutable cloud inputs

This package plan shares the migration plan's exact dependency pins:

| Input | Required value |
| --- | --- |
| Flutter tag | `3.41.10-ohos-1.0.0` |
| Flutter peeled commit | `244a0e8abb3085e8675589b13e219af8c41cb7aa` |
| Core commit | `1ae4674a4b153701b0c3b3ff04b1a1b77a318611` |

Every cloud check and package job records these resolved commits and its Web
source SHA. A later dependency change requires coordinator review.

## Requirements

- R1. A new workflow builds these packages from one commit:

  | Platform | Package | Signing |
  | --- | --- | --- |
  | Android | APK (arm64-v8a, armeabi-v7a, x86_64) | debug-key artifact accepted for migration. Distribution signing is later release readiness |
  | iOS | unsigned IPA | unsigned accepted for migration |
  | OHOS | unsigned HAP (arm64) | unsigned accepted for migration |
  | Linux | `tar.gz` bundle and `DEB` (x86_64) | not signed |
  | Windows | `zip` of the x86_64 Release directory and installer `EXE` | not signed |
  | macOS | `dmg` containing the `.app` | ad-hoc, not notarized |

  The Linux `DEB` and the Windows installer `EXE` are part of the delivery. A
  platform that produces only its archive is incomplete.

- R2. Triggers: manual `workflow_dispatch`, a `v*` tag, and a push that changes
  the workflow, the setup action, `pubspec`, `scripts/`, `vendor/`, `assets/`,
  `installer/`, any platform directory, `lib/`, `test/` or `integration_test/`.
- R3. A `v*` tag run publishes all built packages plus `SHA256SUMS` to a
  GitHub Release for that tag. Other runs keep packages as Actions artifacts
  for 14 days.
- R4. The OHOS job downloads the public HarmonyOS command-line tools archive
  from the pinned URL in the workflow and verifies the pinned SHA-256 before
  unpacking. The job fails with an `OHOS toolchain blocker` when the archive is
  unreachable or its hash differs. The job also fails when the SDK API version
  in `sdk/default/sdk-pkg.json` is not 24, the product target `6.1.1(24)`. A
  different SDK records a wrong API in the HAP, so the mismatch is a failure and
  not a warning. A non-zero exit from `flutter build hap` also fails the job even
  when a HAP file exists. This is a toolchain outcome, not a
  signing-credential gate. A failed or skipped OHOS job is not six-platform
  delivery.
- R5. Migration artifacts require no signing credential. Android may use the
  debug key, iOS may be unsigned, and OHOS may be unsigned. Optional signing
  secrets may be supported later for distribution readiness, but absent
  credentials do not block migration artifacts. Local builds are outside this
  task's verification boundary.
- R6. Each reachable job verifies its package before upload. The archive must
  contain the Flutter application payload and product native runtime for every
  shipped ABI.
- R7. Each run's summary states the artifact signing state, any toolchain
  blocker, the Web source SHA, the Flutter peeled commit and the immutable
  core commit used by every package job.
- R8. No private signing data is committed in the migrated tracked source.
  The tracked OHOS profile stays sanitized with empty `signingConfigs` and no
  product `signingConfig`. CI credentials, if later enabled, come only from
  Actions secrets. Local originals and backups stay outside migration and are
  never staged. This source-tree rule does not rewrite Git history; root
  coordinates any credential rotation if historical exposure is confirmed.
- R9. `docs/` describes how to trigger the workflow, download packages, set
  optional future signing secrets, and what each package's limits are. Chinese
  text follows the controlled-Chinese rules in `AGENTS.md` and passes the
  cloud lint gate.
- R10. Work is reviewed on `ci/app-packages` first. Source workspace Codex in
  `w64:p1` leads. Destination workspace Codex in `w6V:p1` accepts the migrated
  clone. Root stages, commits, pulls and dispatches the workflows. No agent
  runs `git push`. Delivery goes through the push gate request file
  `D:/MyNewProjects/_orchestra/push/qflistudio-web.json`. Do not broadcast to
  legacy or mirror push URLs.
- R11. One run produces six platform package sets: `APK`, `IPA`, `HAP`, Linux
  `tar.gz` plus `DEB`, Windows `zip` plus installer `EXE`, and `DMG`. Each
  archive passes its content check before upload. The Linux `DEB` is assembled
  from the verified bundle and compared file by file after `dpkg-deb --extract`.
  The Windows `EXE` is compiled by the official Inno Setup 6.7.4, downloaded
  from its pinned release URL and checked for SHA-256 and Authenticode signer on
  the runner. The job then silently installs it, compares the payload file by
  file with the built tree and uninstalls it. The macOS `DMG` is mounted and its
  `.app` checked before detach. That mount check is an intended contract pending
  a hosted run.

## Acceptance Criteria

- [ ] A run at the gate-published `main` SHA records actual outcomes for
      Android, Linux, Windows, macOS and iOS, and uploads packages only after
      content checks. Debug-key APK and unsigned IPA are acceptable migration
      artifacts.
- [ ] Six platform package sets exist, including the Linux `DEB` and the
      Windows installer `EXE`, or the missing output is reported as a blocker.
- [ ] The OHOS job reports its real outcome. An unreachable or mismatched
      tools archive produces a visible toolchain blocker. It is not a
      signing-credential failure or a six-platform pass.
- [ ] A reachable OHOS job uploads a fresh unsigned HAP or reports the actual
      toolchain failure. It never claims unobserved success.
- [ ] Each reachable package passes the content check inside its job.
- [ ] A passing GitHub Actions run reports signing state, toolchain blockers,
      the Web source SHA and the exact Flutter/core commits above. Every
      package job uses the same pinned dependencies.
- [ ] The tag-release path is reviewed and runs only when the tag is delivered
      through the push gate.
- [ ] Tracked source contains no signing secrets. CI credentials appear only as
      optional Actions secret references.
- [ ] Documentation lint and package checks run on GitHub-hosted runners only.
- [ ] This package task preserves native-workflow coverage. The migration
      task owns native repairs and records their passing Actions runs.
- [ ] Store signing, notarization, store upload and device acceptance remain
      later release-readiness work.

## Out of Scope

- iOS signing, TestFlight and App Store upload.
- macOS Developer ID signing and notarization.
- OHOS HAP signing and AppGallery upload.
- Windows code signing and MSIX packaging. The Windows installer `EXE` is in
  scope through Inno Setup. Pi p4 owns `installer/`.
- Linux `rpm`, AppImage and Flatpak. Linux arm64.
- Device or emulator installation tests of the built packages.
- CI on Gitee, GitLab, CNB or GitCode mirrors.
- Local builds, tests, lint, package verification, dependency installation or
  SDK downloads. Run these only on GitHub-hosted runners.
- Committing any local OHOS signing backup or private signing material.
- Migrating unreviewed sibling-core working-tree changes. CI uses the pinned
  published core commit above, not a local sibling working tree.
- Repairing the 17 cloud test failures. The migration plan owns that work and
  requires a passing cloud test run before final integration.

## Risks and Deferred Items

- A pinned Flutter revision does not prove all platform builds pass. Engine
  artifacts may need a hosted fix-and-rerun cycle.
- The OHOS job depends on the pinned command-line tools archive. An unreachable
  archive or a hash mismatch fails that build and remains a platform blocker,
  independent of signing.
- Migration artifacts may be unsigned or debug-key signed. Distribution
  signing, notarization, store upload and device acceptance remain later
  release-readiness gates.
- A debug-key APK may fail to upgrade an installation signed with another
  key. Do not claim distribution-signing continuity.
