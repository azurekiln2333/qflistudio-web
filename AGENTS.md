<!-- TRELLIS:START -->
# Trellis Instructions

These instructions are for AI assistants working in this project.

This project is managed by Trellis. The working knowledge you need lives under `.trellis/`:

- `.trellis/workflow.md` — development phases, when to create tasks, skill routing
- `.trellis/spec/` — package- and layer-scoped coding guidelines (read before writing code in a given layer)
- `.trellis/workspace/` — per-developer journals and session traces
- `.trellis/tasks/` — active and archived tasks (PRDs, research, jsonl context)

If a Trellis command is available on your platform (e.g. `/trellis:finish-work`, `/trellis:continue`), prefer it over manual steps. Not every platform exposes every command.

If you're using Codex or another agent-capable tool, additional project-scoped helpers may live in:
- `.agents/skills/` — reusable Trellis skills
- `.codex/agents/` — optional custom subagents

Managed by Trellis. Edits outside this block are preserved; edits inside may be overwritten by a future `trellis update`.

<!-- TRELLIS:END -->

## Delivery policy

This policy applies to every agent and overrides historical instructions that
ask for local validation. It applies to both the old and migrated workspaces.

### Source of truth

Codex leads this project. The source workspace Codex in `w64:p1` owns the
architecture decision, scope and the final acceptance decision. The destination
workspace Codex in `w6V:p1` owns acceptance in the migrated clone. Their
reviewed decisions are the source of truth for version pins, platform scope,
signing policy and delivery status. Claude, Pi, Herdr and any other agent
implement and review within that lead. A recorded Codex decision overrides an
agent's own preference, an older task artifact and an uncommitted plan. If an
agent believes a decision is wrong, it reports the conflict and waits. It does
not silently substitute a different pin, platform list, signing claim or
completion status.

Three rules follow from this leadership.

- Only Codex decisions and reviewed artifacts define what counts as done.
- An agent reports a blocking conflict. It does not resolve it by editing
  another owner's document or by weakening a gate.
- Historical evidence stays as recorded. A later decision supersedes it with
  a new dated record, not by rewriting the old one.

### Gate-only pushes

Never run `git push` in this repository, or in any repository of this product
line, from an agent session. The push gate is a request file. A push happens
only after the local branch is `main`, the working tree is clean and the
request is written.

1. Finish the reviewed change and record its plan in the task artifacts.
2. Confirm the current branch is `main` and that
   `git status --porcelain --untracked-files=all` prints nothing.
3. Confirm `HEAD` is the exact commit that should reach GitHub.
4. Write `D:/MyNewProjects/_orchestra/push/qflistudio-web.json` with this
   shape: `{"repo": "qflistudio-web", "commit": "<full HEAD SHA>",
   "allow": [{"path": "<path>", "reason": "<reason>"}]}`.
5. Stop and wait. The orchestration script validates the request, pushes to
   GitHub `main`, writes `push/qflistudio-web.result.json` and reports the
   result through Herdr.

Only reviewed material may appear in the request. A hard-blocked path, a
secret, a build artifact or a file above the size limit stays out. Never
force-push, never rewrite pushed history, never delete a remote branch and
never push to a mirror such as CNB, Gitee, GitCode or GitLab.

A skipped job, a green job that skipped a platform, or a local source review
is not a passed gate. A request whose tree carries generated output, private
material or signing data stays unwritten.

### Cloud-only execution

- Edit source locally. Run all builds, tests, lint and package verification in
  GitHub Actions on GitHub-hosted runners. Do not use this PC as a self-hosted
  runner, directly or through WSL, Docker, an emulator or another local folder.
- Do not run Flutter/Dart/Gradle/Hvigor/CMake/compiler commands locally. Do not
  install dependencies, SDKs or browser tooling locally. Do not download build
  artifacts, intermediary files, caches or test results into the workspace.
- Local text inspection, Git status/diff/ref/hash checks, source synchronization,
  Trellis metadata updates and Herdr communication are allowed. Use Python -B
  for metadata scripts so they do not create __pycache__.
- Keep source, reviewed task progress, specifications, scripts and sanitized
  final evidence in Git. Keep generated output, runtime pointers, private
  sessions, credentials and signing keys excluded. Never blanket-add ignored
  directories. Existing hash-pinned vendor/runtime inputs remain authoritative.
- Use the canonical sibling folder qflistudio-core. The Dart package name
  remains qfli_studio_core. Record the exact core SHA in cloud verification.
- The destination workspace uses one remote, origin, with only the GitHub URL
  https://github.com/azurekiln2333/qflistudio-web.git for fetch and push. The
  source workspace keeps its mirror remotes and their refs inside `.git`, and
  root narrows only the origin push URL to GitHub. The external backup holds
  the former Git config. A gate request therefore cannot broadcast to a mirror.
- Coordinate agents through Herdr. Read the current task artifacts before
  editing. Divide file ownership. Root is authorized to stage, commit, pull
  and dispatch workflows. Any agent push goes through the gate request only.
- The destination workspace Codex is `w6V:p1`. Hand the final SHA to that pane
  and record its acknowledgement verbatim.
- A green skipped job, unsigned package or portable bundle is not proof of an
  installable signed release. Record actual cloud run IDs and signing status.
- Keep task status honest. A merged source commit, a skipped job, a debug-key
  APK, an unsigned IPA or an unsigned HAP is not platform or release
  acceptance. Say which platform, gate and run produced the evidence.
- Never unregister a shared WSL distribution or delete the old workspace
  before the migration handoff and recovery-data review are complete.

### Six-platform scope

Delivery covers exactly these six platforms and no others.

| Platform | Migration artifact | Signing state |
| --- | --- | --- |
| Android | APK, arm64-v8a, armeabi-v7a, x86_64 | debug key until distribution signing |
| iOS | IPA, arm64 | unsigned |
| OHOS | HAP, arm64 | unsigned |
| Linux | `tar.gz` and `DEB`, x86_64 | not signed |
| Windows | `zip` and installer `EXE`, x86_64 | not signed |
| macOS | `dmg`, arm64 | ad-hoc, not notarized |

A job definition is not an artifact. Six job definitions do not prove six
artifacts. Missing toolchain, such as HarmonyOS command-line tools, is a
separate blocker from signing. Report a skipped platform as a blocker and do
not count it toward six-platform delivery.

### Exact pins

Every cloud check and package job uses these exact inputs. No floating branch,
no `latest` and no independent per-job resolution.

| Input | Exact value |
| --- | --- |
| Flutter tag | `3.41.10-ohos-1.0.0` |
| Flutter peeled commit | `244a0e8abb3085e8675589b13e219af8c41cb7aa` |
| Core commit | `1ae4674a4b153701b0c3b3ff04b1a1b77a318611` |

Use the peeled commit for an annotated tag, not the tag-object SHA. A pin
change requires a reviewed decision in both task plans. Record the Web source
SHA with both dependency SHAs in every run summary.

### Unsigned artifact policy

Migration artifacts do not need signing credentials.

- Android may ship a debug-key APK. Say that it uses the debug key.
- iOS may ship an unsigned IPA. Say that it is unsigned.
- OHOS may ship an unsigned HAP. Say that it is unsigned.
- Linux, Windows and macOS ship unsigned or ad-hoc packages as listed above.

A missing signing credential never blocks a migration artifact. Distribution
signing, provisioning, notarization, store upload and device acceptance stay
later release-readiness work. Never read, restore, stage or migrate a private
signing backup. Tracked signing configuration stays sanitized, and any future
CI credential comes only from Actions secrets.

### Six package outputs

One workflow run produces one package set per platform. Linux ships two files,
Windows ships two files, so the set holds more files than platforms.

| Platform | Output files |
| --- | --- |
| Android | `APK` |
| iOS | `IPA` |
| OHOS | `HAP` |
| Linux | `tar.gz` and `DEB` |
| Windows | `zip` and installer `EXE` |
| macOS | `DMG` |

The Linux `DEB` and the Windows installer `EXE` are part of the migration
delivery. A missing `DEB` or `EXE` leaves that platform incomplete even when
its archive exists.

The controlled-Chinese lint command below also runs in GitHub Actions only.

改写中文技术文本时套用受控中文规则：一句一动作、主动语态、一词一义（同一概念全篇同一个词）、不用分号连接动作、句长（指令 ≤ 25 字、说明 ≤ 40 字）、去掉虚动词（进行 / 加以 + 名词）、套话（需要注意的是、在一定程度上）、营销形容词（无缝、强大、赋能、闭环）与含糊词（若干、一些、相关）。
不得改动情态（可能 / 也许）：置信度是内容。
机械首查用 python <repo>/scripts/ste-lint-zh.py <文件>。

# QFLI product workspace rules

These rules apply to every agent and every repository under this directory.
The user requires all builds and tests to run on GitHub-hosted runners.

- Do not run local builds, tests, benchmarks, emulators, or native compilation.
- Do not run dependency installation, SDK installation, or dependency restore.
- Do not download build artifacts, installers, SDKs, or build caches to this workspace.
- Do not run Flutter, Dart, Gradle, CMake, Ninja, Xcode, Hvigor, or package-manager commands that generate output.
- Read and edit source locally. Inspect Git metadata and text without creating build or test outputs.
- Run validation through the repository's GitHub Actions workflows. Read results through GitHub API or log output.
- Keep artifacts on GitHub. Record immutable source revisions, run IDs, job conclusions, checksums, and signing limitations in Trellis.
- Keep durable Trellis tasks, specs, research, journals, and project instructions in version control. Keep local runtime/session state and secrets ignored.
- Use GitHub as the sole remote for migrated clones. Check both fetch and push URLs.
- Preserve another agent's work. Coordinate repository ownership and handoff through Herdr.
- Do not delete shared WSL distributions or old source workspaces without the owning coordinators' preservation decision.
- Folder names follow GitHub repository names. Shared core is `qflistudio-core`; its Dart package name remains `qfli_studio_core`.

Each repository must also commit these restrictions in its own AGENTS.md or project policy so fresh clones on another PC retain the rules. This parent file is a convenience copy, not a substitute for versioned repository policy.

Initial coordinated writer: SQL coordinator, Herdr w62:p1, 2026-11-26.
