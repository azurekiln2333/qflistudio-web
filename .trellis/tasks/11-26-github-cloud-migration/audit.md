# Read-only migration audit — 2026-11-26

## Repository identity and baseline

- Source: D:/MyNewProjects/qfli_web (Herdr w64, coordinator p1).
- Destination: E:/MyNewProjects/QFLIProjects/qflistudio-web (Herdr w6V, coordinator p1).
- GitHub repository: azurekiln2333/qflistudio-web.
- Both baseline HEADs: 1fed59c2a5137560b393ffaea2c9363ead83bbd9.
- Both baseline trees: 5496a0d3cad6d6c2001a166aa88d91a5d079f967.
- All five configured remote hosts advertised only main at that baseline. The distinct GitLab SSH push endpoint agreed.
- Local main and ci/app-packages had no unique commits. No live stashes, extra registered worktrees or unmerged index entries existed.
- Destination was clean and had exactly one GitHub origin fetch/push URL. Source
  origin had five push URLs. That source count is historical: the source now
  keeps its mirror remotes with mirror refs inside `.git`, and only the origin
  push URL is narrowed to GitHub.

The auditor compared all 1,013 tracked paths: none missing; 244 differences were CRLF-only, and two were intended edits. Do not normalize unrelated files. Git fsck completed successfully in both repositories. Source .git retains dangling blobs and dropped WIP stash 71c569c (2026-10-15) with index parent c42b691; these are recovery history, not live branch work. Preserve source .git until reviewed.

## Pending source and progress

Baseline pending work comprised android/app/build.gradle.kts and docs/native-builds.md, plus the application package workflow/action, two package scripts, package documentation and eight 11-17-ci-app-packages task artifacts.

The old ignore policy omitted 28 Trellis Python support scripts, workflow/configuration, the inner ignore file, provenance, agent roles, 43 shared skill files, the workspace index and five specs. Tracked indexes already referenced the missing specs. Complete durable instructions are therefore required, not just existing tracked task files. Private runtime and cached Python files stay excluded.

Before this task there were six in-progress task records and eleven completed records. Two completed tasks were archived; nine remained in the tasks root. Preserve their statuses. Existing signing, ARMv7 execution and device-verification gaps are not closed by this migration. Operational manifests in 10-11-ohos-nginx-embedded used absolute D-drive paths and require repository-relative references.

A malformed root directory named one ASCII space contains 1,042 extracted/scratch Nginx files. Ordinary git status warns on this path. It is excluded as scratch, not copied or staged. Its cleanup must use an exact inspected literal path.

## Initial cloud evidence

At the baseline commit, latest runs were dated 2026-11-17:

| Workflow | Run ID | Observed outcome |
| --- | --- | --- |
| Native build | 44002019083 | Success: Linux and three Android ABIs |
| Native OHOS build | 44002019041 | Success |
| Native Apple build | 44002019131 | Failure: three iOS and two macOS jobs |

Apple logs identify iOS pwritev availability against the iOS 13 minimum and incorrect lipo argument ordering. Preserve the minimum target and use Nginx's existing fallback.

No application-package workflow existed remotely. No repository secrets or releases were returned by gh. No existing workflow ran Flutter analyze/tests. The pending package workflow independently fetched moving core main in six jobs, and a missing OHOS toolchain could produce a green no-package result. These must not be treated as complete six-platform delivery.

Core coordinator confirmed the canonical sibling folder qflistudio-core, while Dart package/import stays qfli_studio_core. Published tested baseline: 476a30acee21dc486ee2849dd8064a7be665e4d5; its core-check run 45656065902 succeeded. The core migration's final SHA is separate and was not yet available.

## Coordination

All four source Pi agents confirmed gpt-6.1-sol. Communications used Herdr. The destination coordinator acknowledged the freeze and cloud-only rule. No local builds, tests, dependency installs, artifact downloads or WSL startup/cleanup were performed by this migration audit.

## Apple repair verified on GitHub

GitHub Actions [run 45827112830](https://github.com/azurekiln2333/qflistudio-web/actions/runs/45827112830) succeeded on source commit `3b947c83c4f2ab15f74fdbef3cca1cdb3ea6ffb2`. All five jobs passed. The jobs built and linked the iOS device arm64 and simulator arm64/x86_64 libraries, verified the Mach-O targets, and ran the macOS arm64/x86_64 syntax and HTTP smoke tests. The run published five native archives and five log artifacts. App signing and device installation remain separate.

## Dated disposition: consumed process pointers — 2026-11-27

Root moved ten reviewed process job pointers out of
`.trellis/tasks/10-22-standalone-offline-ide/research/` and committed the
removal as `768bf77` on 2026-11-27. The files are transient process state, not
outcome records. Backup location:
`D:/MyNewProjects/_migration-backup/qflistudio-web-20261127/transient-pointers`.

| Removed pointer |
| --- |
| `web-app-c606-20261026/job.json` |
| `web-app-c782-20261026/job.json` |
| `web-app-c843-20261026/job.json` |
| `web-app-c895-20261026/job.json` |
| `web-owned-job-self-control-20261024.json` |
| `web-runtime-repair6-job.json` |
| `web-runtime-repair7-job.json` |
| `web-runtime-repair8-job.json` |
| `web-runtime-repair9-job.json` |
| `web-runtime-repair10-job.json` |

Boundaries of the disposition:

- The ten table rows are the only removed paths. The commit reports 1,125
  deletions across ten files.
- Every final outcome, grant, script and narrative record stays in the task.
- No directory was deleted. The four `web-app-c*-20261026/` directories and
  their relay and observed siblings remain on disk.
- Git keeps the deleted blobs reachable through commit `768bf77` in history.
  Garbage collection cannot remove them while that history remains reachable.
  A reviewed restore reads the backup copy, not `git reflog`.
- This disposition does not retire the old root `D:/MyNewProjects/qfli_web`.
  `.git` and dropped-stash objects remain preserved.

