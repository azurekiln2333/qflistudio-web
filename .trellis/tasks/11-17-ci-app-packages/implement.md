# Implementation plan

## Order

1. Source workspace Codex in `w64:p1` leads this task. Destination workspace
   Codex in `w6V:p1` accepts the migrated clone. The user approved all
   migration plans on 2026-11-27, so this plan needs no further approval round.
   Reuse the existing `ci/app-packages` branch. Workers do not create or reset
   branches. Root stages, commits, pulls and dispatches workflows.
2. Review `.github/actions/setup-app-build/action.yml` against the pinned-input
   contract. Root assigns any additional edit before dispatch. Do not recreate
   correct existing files.
3. Pi p4 reviews `scripts/verify_app_package.py`. Root assigns any required
   change to `scripts/prepare_ohos_ci_profile.py` before dispatch.
4. Preserve the optional key-properties branch in `android/app/build.gradle.kts`.
   No signing credential is required for the debug-key migration artifact.
5. Keep tracked `ohos/build-profile.json5` sanitized: empty `signingConfigs` and
   no product `signingConfig`, preserving SDK, product and bundle settings. Do
   not read, stage or migrate the private original backup.
6. Pi p5 completes `.github/workflows/app-packages.yml` within its exclusive
   ownership. Preserve unsigned artifact support and truthful platform outcomes.
   Pi p4 completes `installer/windows/qfli-webforge.iss` within its exclusive
   ownership so the Windows job produces the installer `EXE`.
7. Review `docs/app-packages.md` and the pointer in `docs/native-builds.md`.
   Root assigns any remaining documentation edit before dispatch.
8. Run every lint, source check, build, test, package inspection, dependency
   resolution and SDK download in GitHub Actions only. Do not run local
   verification commands.
9. Review gate: `trellis-check` performs source inspection only. Report cloud
   checks as pending until they have a matching Actions run URL and SHA.
10. Root reviews the exact paths, stages and commits, then delivers through the
    push gate. No agent runs `git push`. When the branch is `main` and the tree
    is clean, root writes `D:/MyNewProjects/_orchestra/push/qflistudio-web.json`
    with the `repo`, the full `commit` and any `allow` entries. The
    orchestration script pushes to GitHub and reports through Herdr. The push
    triggers hosted verification.
11. Root inspects run and job outcomes. Fix failures within exclusive file
    ownership and request the gate again. Record each workflow URL, run ID, Web
    source SHA, Flutter peeled SHA, Core SHA and actual outcome. Each package
    work item requires a passing GitHub Actions run for its affected job.
12. After the reachable cloud jobs pass, root brings `main` level with GitHub and
    may merge the reviewed commits. Never force-push and never push to a mirror.
13. Report the actual OHOS outcome. A missing command-line toolchain is a
    blocker independent of signing. A skipped OHOS job is not six-platform
    delivery.
14. Confirm the six platform package sets. Linux delivers a `tar.gz` and a
    `DEB`. Windows delivers a `zip` and an installer `EXE`. Android, iOS, OHOS
    and macOS deliver one file each. A missing `DEB` or `EXE` leaves that
    platform incomplete and stays an open acceptance item.
15. Record later signing, notarization, store-upload and device-acceptance work
    separately from migration artifact completion. When the selected model
    fails repeatedly, a lower-tier fallback is authorized. Report the failure
    and the fallback instead of waiting.

## Immutable cloud inputs

| Input | Required value |
| --- | --- |
| Flutter tag | `3.41.10-ohos-1.0.0` |
| Flutter peeled commit | `244a0e8abb3085e8675589b13e219af8c41cb7aa` |
| Core commit | `1ae4674a4b153701b0c3b3ff04b1a1b77a318611` |

The setup action accepts `flutter-ref`, `flutter-revision` and `core-ref`.
Use `../qflistudio-core` for the sibling checkout. Keep `qfli_studio_core` as
the Dart package/import name. Cloud checks and all package jobs verify the
same immutable dependencies. A mismatch fails the job. A changed pin requires
review in both task plans.

## Exclusive implementation ownership

- Pi p5: `.github/workflows/app-packages.yml`.
- Pi p4: `scripts/verify_app_package.py`, `installer/` and
  `installer/windows/qfli-webforge.iss` for the Windows installer `EXE`.
- Pi p2: `.github/workflows/cloud-check.yml` and
  `scripts/check_source_policy.py`.
- The migration task's `implement.md` owns the ordered 17-failure repair
  checklist and each test/source file assignment. Do not edit another
  worker's file. Root records any reassignment before work starts.

## Hosted validation boundary

All verification runs on GitHub-hosted runners. Do not execute the former
local-validation command list, install dependencies, download SDKs or invoke
WSL on the developer machine. Root stages, commits, pulls and dispatches
workflows. No agent runs `git push`. Delivery goes through the push gate
request file described in the migration plan.

GitHub Actions records the exact Web source SHA, Flutter peeled SHA and Core
SHA above. Accept an Android debug-key APK and unsigned iOS IPA and OHOS HAP
when package content checks pass. Missing signing credentials do not block
these migration artifacts. The OHOS command-line toolchain is a separate build
prerequisite. If it is absent, report the failed toolchain job as a blocker and
do not claim six-platform delivery. Keep store signing, notarization and device
acceptance as later release-readiness gates.

The run must produce the six platform package sets. Linux delivers a `tar.gz`
and a `DEB`. Windows delivers a `zip` and an installer `EXE`. Android, iOS,
OHOS and macOS deliver one file each. A missing `DEB` or `EXE` leaves that
platform incomplete.


```text
GET https://api.github.com/repos/azurekiln2333/qflistudio-web/actions/runs?branch=ci/app-packages
GET https://api.github.com/repos/azurekiln2333/qflistudio-web/actions/runs/<id>/jobs
```

Anonymous access gives job and step conclusions, not logs. When a failing
step's cause is not clear from its name, ask the user for the log.

## Risky points

- Do not read, copy, stage or publish any local OHOS signing backup.
- Migration cloud artifacts may be unsigned or debug-key signed. Missing
  credentials are not a blocker. Any later signing path uses Actions secrets.
- Do not push tags. The release path runs only when the tag is delivered
  through the push gate.
- Do not broadcast to legacy or mirror push URLs.
- After the merge to `main`, root brings both local clones level with GitHub.

## Rollback points

- Before the gate request: root may discard the uncommitted workflow changes
  while preserving unrelated source.
- After the gate push: keep `main` untouched until hosted results are reviewed.
- After merge: root coordinates a GitHub-only rollback through a new commit.
  Never force-push.
