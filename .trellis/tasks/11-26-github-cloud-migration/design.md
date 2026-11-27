# Migration design

The old repository owns pending Web changes. GitHub is the publishing
authority. The destination is an independent clean clone. Delivery goes through
the push gate request file, never through `git push`. Never force-push.

## Leadership and boundaries

Codex leads this migration. The source workspace Codex in `w64:p1` owns the
scope, the pins, the signing policy and the final acceptance decision. The
destination workspace Codex in `w6V:p1` owns acceptance in the migrated clone.
Claude, Pi and Herdr work inside that lead. A recorded Codex decision is the
source of truth for this design.

The planning editor changes only Trellis documents and the instruction docs.
Pi p2, p4 and p5 own disjoint implementation files. Workers do not mutate Git.
All builds, tests, lint, package and source checks, dependency installs and SDK
downloads run on GitHub-hosted runners only. Source and Git metadata reads are
allowed.

A push is a gate, not a draft action. No agent runs `git push`. After the local
branch is `main` and the tree is clean, the agent writes
`D:/MyNewProjects/_orchestra/push/qflistudio-web.json` with the repo name, the
full `HEAD` SHA and any `allow` entries. The orchestration script validates the
request, pushes to GitHub `main`, writes
`D:/MyNewProjects/_orchestra/push/qflistudio-web.result.json` and reports the
result through Herdr. Never push to a mirror URL and never rewrite history.

Restore versioning of durable Trellis support and selectively reviewed
integrations. Exclude local session pointers, private history, build output and
caches. Preserve existing line endings and historical evidence. Operational
context manifests become repository-relative.

The integration ignore rules use a narrow allowlist. Each of the six reviewed
integration roots is excluded, reopened for directory traversal only, and then
each reviewed template file is allowed by its exact path. An unreviewed file
inside those roots stays ignored. `.trellis/.runtime`, agent session
directories and the single-space scratch directory stay excluded.

Canonical sibling folder: `qflistudio-core`. Dart package and import:
`qfli_studio_core`. Align pubspec, lockfile path metadata, scripts, cloud
checkout and docs.

## Immutable cloud inputs

| Input | Required value |
| --- | --- |
| Flutter tag | `3.41.10-ohos-1.0.0` |
| Flutter peeled commit | `244a0e8abb3085e8675589b13e219af8c41cb7aa` |
| Core commit | `b756b2eaf9fb941d6bdad30a7ba4262d7341e2ce` |

Cloud checks and all package jobs use this same pair of dependency commits. The
Flutter revision is the peeled commit, not an annotated tag-object SHA. Each job
records the resolved revisions and Web source SHA. Do not resolve moving `main`
independently or substitute the later core-migration SHA without a reviewed plan
update. No floating tag, branch or `latest` value is allowed.

## Cloud delivery

Preserve the Apple repair evidence recorded in `audit.md`. Any further native
repair must retain tests and platform support. Review the pending application
workflow. Complete hosted source and test gates and truthful package and signing
outcomes. Keep native and Flutter intermediates in Actions caches and artifacts.
Existing hash-pinned vendor binaries are product inputs, not disposable output.

Delivery scope is exactly six platforms: Android, iOS, OHOS, Linux, Windows and
macOS. Linux ships a `tar.gz` bundle and a `DEB`. Windows ships a `zip` and an
installer `EXE`. Android, iOS, OHOS and macOS ship one file each. A platform
whose second output is missing stays incomplete. No platform may be added,
dropped or silently substituted.

Accept a debug-key APK and unsigned IPA and HAP migration artifacts after hosted
package-content checks pass. Missing signing credentials do not block these
artifacts. Distribution signing, provisioning, notarization and store and device
acceptance remain later release-readiness work. Report each artifact with its
real signing state.

A job definition is not an artifact. Six job definitions do not prove six
artifacts. Missing OHOS toolchain remains an explicit build blocker. A failed or
skipped OHOS job is not six-platform delivery. A green run that skips a platform
does not establish that platform's acceptance. The tracked OHOS profile remains
sanitized. Future signing material comes only from Actions secrets. Never read,
restore or migrate private local signing backups.

## Test-repair handoff

The evidence source is `research/flutter-test-failures-45858109136.md` in this
task. It records the 17 failures from Actions run `45858109136`. The ordered
repair checklist and exclusive file ownership live in `implement.md`. Pi p5
retains `.github/workflows/app-packages.yml`. Pi p4 retains
`scripts/verify_app_package.py` and `installer/`. Pi p2 retains
`.github/workflows/cloud-check.yml` and `scripts/check_source_policy.py`.

Assign each test or production repair file to one owner. Shared-file edits wait
for the current owner to finish. A changed file must not be edited by a second
worker in parallel. Every repair requires a passing GitHub Actions run with the
pinned dependencies. Source inspection, a skipped test or a weakened assertion
is not acceptance.

## Integration and handoff

The plan is approved by the 2026-11-27 directive, so implementation does not
wait for another review round. After cloud acceptance, the local `main` is
brought level with GitHub. Both local main trees must match GitHub. Preserve old
`.git` and dangling dropped-stash objects until recovery review. Do not delete
old data first.

Handoff records the main and tree SHA, source comparisons, workflow IDs, the
pinned dependency SHAs and the external gates. Send the final SHA to the
destination workspace Codex in `w6V:p1` through Herdr and record its
acknowledgement verbatim. A model-capacity failure is reported, not hidden by a
silent model change.

## Status language

Use only these states in this document set.

- Planned: assigned but not started.
- In progress: a worker holds the file and a run is pending.
- Blocked: a named external gate is missing, such as the OHOS toolchain.
- Passed: a recorded Actions run URL and SHA cover the claim.

Do not write "done", "complete", "verified" or "delivered" without a matching
run URL and SHA. A merged commit is not a passed platform gate.
