# GitHub migration and cloud-only delivery

## Goal

Preserve Web source and Trellis progress, reconcile all branches into GitHub main, verify cloud-only six-platform delivery, synchronize the E drive clone and hand off through Herdr.

## Leadership

Codex leads this task. The source workspace Codex in `w64:p1` owns the scope,
the dependency pins, the signing policy, the platform list and the final
acceptance decision. The destination workspace Codex in `w6V:p1` owns
acceptance in the migrated clone. Claude, Pi and Herdr work inside that lead. A
recorded Codex decision is the source of truth for this task. It overrides an
older paragraph in this document set and an agent's own preference.

The user approved all migration plans on 2026-11-27. Implementation does not
wait for a further approval round. An agent that disagrees reports the conflict
and stops. It does not silently change a pin, drop a platform, widen a signing
claim or mark work complete. Report a model-capacity failure without changing
the selected model.

## Requirements

- Preserve reviewed Web source and all durable Trellis progress on GitHub.
- Exclude generated builds, dependency caches, signing secrets and agent
  runtime state.
- Review every local and configured remote branch. Integrate unique reviewed
  work into main without force-pushing.
- Use only GitHub in the destination. Compare committed trees and clean status
  after `pull --ff-only`.
- Run builds, tests, lint, package verification and dependency installation on
  GitHub-hosted runners only. No local execution path exists for any agent.
- Deliver exactly six platforms: Windows, Linux, macOS, iOS, Android and OHOS.
  The application workflow covers them in one run. The native workflows keep
  their existing coverage.
- Produce six platform package sets. Linux delivers a `tar.gz` bundle and a
  `DEB`. Windows delivers a `zip` and an installer `EXE`. Android, iOS, OHOS and
  macOS deliver one file each. A missing `DEB` or `EXE` leaves that platform
  incomplete.
- Accept a debug-key APK and an unsigned IPA and HAP as migration artifacts
  after hosted package-content checks pass. Missing signing credentials do not
  block them. Distribution signing, provisioning, notarization and store and
  device acceptance remain later release-readiness work.
- Record a missing toolchain explicitly. A skipped OHOS job does not establish
  six-platform delivery.
- Use Flutter tag `3.41.10-ohos-1.0.0` at peeled commit
  `244a0e8abb3085e8675589b13e219af8c41cb7aa` and Core commit
  `8e031313ffc8d531c5a6b4d131f721f35da04c86` in every cloud check and package
  job. Record the Web source SHA with both dependency SHAs. Do not float a
  branch, use `latest` or resolve a ref per job.
- Resolve all 17 cloud test failures recorded by run `45858109136`. Preserve
  the failing behavior as test coverage. Do not skip tests or weaken assertions
  to obtain a green run.
- Preserve meaningful task statuses. A source merge, a skipped job, a debug-key
  APK or an unsigned package is not platform acceptance.
- Delivery goes through the push gate. No agent runs `git push`. After the
  local branch is `main` and the tree is clean, the agent writes
  `D:/MyNewProjects/_orchestra/push/qflistudio-web.json` and stops. The
  orchestration script pushes to GitHub `main`, writes
  `push/qflistudio-web.result.json` and reports through Herdr. Never push to a
  mirror URL and never force-push.
- Deliver a verified handoff to the destination workspace Codex in `w6V:p1`
  and a scoped cleanup plan. The handoff records actual run outcomes, not an
  expectation.

## Acceptance Criteria

- [ ] Durable Trellis scripts, guidance, tasks and approved integrations survive a clean clone.
- [ ] No generated or private material is newly staged.
- [ ] Reviewed source is on GitHub main and both local main trees match it.
- [ ] Both source workspaces are clean. The destination has exactly one GitHub remote.
- [ ] GitHub Actions runs pass for the cloud source and test gates. All 17 failures from run `45858109136` are resolved. Each work item records its passing run URL and Web source SHA.
- [ ] Cloud checks record the exact Flutter peeled SHA and Core SHA above, the Web source SHA and actual outcomes. Every package job uses the same pinned dependencies.
- [ ] Six-platform coverage, artifact signing states and toolchain and installer blockers are documented. Linux `DEB` and Windows installer `EXE` are present or reported as blockers. Unsigned IPA and HAP and debug-key APK acceptance is separate from release readiness.
- [ ] The destination workspace Codex in `w6V:p1` acknowledges the final SHA and the cloud-only and push-gate rules. The acknowledgement is recorded verbatim.
- [ ] Cleanup preserves vendor inputs, task evidence and unresolved Git recovery objects.

## Notes

- Source: `D:/MyNewProjects/qfli_web`. Destination:
  `E:/MyNewProjects/QFLIProjects/qflistudio-web`.
- Herdr confirms the plural QFLIProjects directory. The singular directory does
  not exist.
- At the initial audit, all five remote main branches started at
  `1fed59c2a5137560b393ffaea2c9363ead83bbd9`. This is historical evidence. It
  is not the current delivery SHA.
- The user approved continuation after the audit summary on 2026-11-26.
- Shared WSL distributions serve sibling products. Inventory them. Do not
  unregister them in this repository task.
