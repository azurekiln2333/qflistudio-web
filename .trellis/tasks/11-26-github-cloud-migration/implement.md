# Execution plan

1. Retain the completed read-only audit and dated cloud evidence. Do not
   repeat local verification or overwrite historical task outcomes.
2. This plan, the package task plan and the instruction docs are final for
   implementation. The user approved all migration plans on 2026-11-27. Source
   workspace Codex in `w64:p1` leads. Destination workspace Codex in `w6V:p1`
   accepts the migrated clone. Do not wait for Claude and do not open a new
   approval round.
3. Pi owners repair the cloud test failures in the ordered checklist below.
   Keep existing assertions and coverage. Do not skip a failing test.
4. Pi p2 owns the source and test workflow. Pi p5 owns
   `.github/workflows/app-packages.yml`. Pi p4 owns
   `scripts/verify_app_package.py` and `installer/`. Preserve the Apple repair
   evidence already recorded
   in `audit.md`. Any new native-workflow edit needs an explicit owner first.
5. The planning editor reviews exact publication paths and diffs. Exclude
   generated output, private material and malformed scratch directories.
6. Git delivery uses the push gate. No agent runs `git push`. Confirm the
   branch is `main`, confirm `git status --porcelain --untracked-files=all`
   prints nothing and confirm `HEAD` is the commit to publish. Then write
   `D:/MyNewProjects/_orchestra/push/qflistudio-web.json` with `repo`,
   `commit` and any `allow` entries, and stop. The orchestration script pushes
   to GitHub `main`, writes `push/qflistudio-web.result.json` and reports
   through Herdr. All validation runs on GitHub-hosted runners.
7. Record run URL, run ID, Web source SHA, Flutter peeled SHA, Core SHA and
   actual job outcomes. A failed cloud job means repair source and request the
   gate again.
8. Require passing Actions runs for every work item. Record missing toolchains
   separately. A skipped platform is not six-platform delivery. Missing signing
   credentials do not block debug-key APK or unsigned IPA and HAP artifacts.
   A missing Linux `DEB` or Windows installer `EXE` leaves that platform
   incomplete.
9. After cloud acceptance, bring the source and destination local `main` level
   with GitHub and compare committed trees, status, GitHub head and destination
   remotes. Use `pull --ff-only`. Never force-push.
10. Send the final SHA to the destination workspace Codex in `w6V:p1` through
    Herdr. Record its acknowledgement verbatim. Supply the cleanup
    instructions. Preserve shared WSL and unresolved recovery data. Keep
    distribution signing and device and store acceptance as later work.
    When the selected model fails repeatedly, a lower-tier fallback is
    authorized. Report the failure and the fallback instead of waiting.

## Immutable cloud inputs

| Input | Required value |
| --- | --- |
| Flutter tag | `3.41.10-ohos-1.0.0` |
| Flutter peeled commit | `244a0e8abb3085e8675589b13e219af8c41cb7aa` |
| Core commit | `b756b2eaf9fb941d6bdad30a7ba4262d7341e2ce` |

Use the same pair of dependency commits for `cloud-check.yml` and all package
jobs. Verify resolved commits before checks or builds. The Flutter pin is the
peeled commit, not a tag-object SHA. Checkout the core beside the workspace as
`qflistudio-core`. Keep `qfli_studio_core` as the Dart package/import name.
Changing a pin requires coordinator review in both task plans.

## Verification boundary

Local workers may read source and Git metadata. The planning editor may edit
only the assigned Trellis and instruction documents. Implementation workers may
edit only their assigned files. Workers do not stage, commit, push, pull, merge
or reset. Delivery happens only through the push gate request file.

Run Python and config checks, controlled-Chinese lint, Flutter analyze and
tests, native builds and tests, dependency installation, SDK downloads,
packaging and archive verification on GitHub-hosted runners only. Historical
local-check commands are superseded. A source review is not an executed test.

Accept debug-key APK and unsigned IPA and HAP after hosted package-content
checks pass. Missing signing credentials do not block migration artifacts.
Signing, provisioning, notarization and store and device acceptance remain
later release readiness. Missing OHOS tools remain a separate toolchain
blocker. Never read, restore, stage or migrate private signing backups.

## 修复 17 个云端测试失败

证据：`research/flutter-test-failures-45858109136.md`。
失败基线：run `45858109136`。
Web 基线：`1a05b08117dc69cc8aa160d88f5dc18f0b8d7231`。
该次运行通过 293 项，失败 17 项，跳过 6 项。
失败编号沿用报告的 01–17。
以下为规划分工，尚未派发实现。

1. [ ] p2：补齐浏览器依赖（05、10）。
   独占文件：`.github/workflows/cloud-check.yml`。
   在云端按 lockfile 安装 npm 依赖。
   在云端安装 Chromium 与系统依赖。
   保留 CSP 与 console bridge 断言。
   不改两个浏览器测试文件或 `.mjs` 脚本。
   验收：GitHub Actions run 通过。
   两个浏览器用例必须执行真实断言。
2. [ ] p2：修复 OHOS 启动断言（01–03）。
   独占文件：`test/startup_test.dart`。
   按 Linux 宿主验证真实外壳。
   保留三种 progress bridge 场景。
   失败路径也须释放首帧并卸载应用。
   不为旧 finder 强制产品使用 phone。
   验收：GitHub Actions run 通过。
   三种 bridge 场景必须全部通过。
3. [ ] p2：验证 Android 首帧（04）。
   独占文件：`test/startup_test.dart`。
   先完成第 2 项，避免同文件并行编辑。
   先在云端单跑 Android 用例。
   再在云端运行整份启动测试。
   保留立即发送首帧的断言。
   级联污染仍是待验证假设。
   验收：GitHub Actions run 通过。
   单跑与整文件结果均须通过。
4. [ ] p4：适配合并内容入口（06–09）。
   独占文件：`test/web_catalog_language_test.dart`。
   使用 `TutorialCenterPage` 的两个栏目。
   搜索前显式展开搜索入口。
   用真实内容或加载状态等待就绪。
   保留 481 条资产与科目筛选断言。
   保留 badge、HTML 导入及窄屏覆盖。
   保留 320px 与 2x 文字覆盖。
   验收：GitHub Actions run 通过。
   四个教程及示例用例必须全部通过。
5. [ ] p4：适配外壳与工具导航（12–16）。
   独占文件：`test/web_tools_navigation_test.dart`。
   显式区分 phone 与窄窗口 desktop。
   覆盖四个主入口与内容中心双栏目。
   保留离线入口与 proxy JSON 断言。
   保留设置可达及离线账号隐藏断言。
   保留 320px 与 2x 文字覆盖。
   验收：GitHub Actions run 通过。
   五个导航用例必须全部通过。
6. [ ] p4：适配工作区外壳契约（11）。
   独占文件：`test/web_saved_workspaces_test.dart`。
   phone 场景显式注入设备类别。
   desktop 场景使用真实工作台入口。
   不只修改预期 Tab 数量。
   保留双 owner、文档与游标断言。
   保留目录展开与重建恢复断言。
   保留源文件字节断言。
   验收：GitHub Actions run 通过。
   工作区保存与重建恢复用例须通过。
7. [ ] p2：修复关闭探针竞态（17）。
   独占文件：`test/web_server_tools_lifecycle_test.dart`。
   在有界重试中处理暂态 `ECONNRESET`。
   继续推进异步清理。
   最终必须观察真正的 connection refusal。
   reset、超时或任意 socket 错误不算成功。
   在云端重复验证关闭场景。
   验收：GitHub Actions run 通过。
   重复验证结果与完整 suite 均须通过。
8. [ ] p2 汇总，p4、p5 提供云端证据。
   p2 仅编辑自己独占的门禁文件。
   汇总 01–17 的实际结果。
   保留完整 suite 与失败门禁。
   不删测试、不弱化断言、不新增跳过。
   既有六项 Nginx 跳过仍单列记录。
   跳过不计为功能通过。
   记录 run URL、Web SHA 与固定输入。
   验收：GitHub Actions run 通过。
   01–17 全部通过后才关闭修复清单。

第 1、2、4、5、6、7 项可按独占文件并行。
第 3 项依赖第 2 项。
第 8 项依赖前七项。
每项记录通过的 run URL 与 Web SHA。
同一最终整合 run 可覆盖多个验收项。
工作流门禁与对应测试都必须通过。

当前证据未确认产品源码存在缺陷。
本清单不分配 `lib/` 或 Core 源码。
若隔离后仍失败，先补云端证据。
协调者再为生产文件指定唯一负责人。
不得直接修改 Core pin、pubspec 或 lockfile。
p5 的打包文件不参与测试修复。

## Exclusive file ownership

| Owner | Exclusive paths or responsibility |
| --- | --- |
| Codex `w64:p1` | Leadership, scope, pins, signing policy and final acceptance decision |
| Codex `w6V:p1` | Acceptance in the migrated clone and handoff acknowledgement |
| Planning editor | `.gitignore`, `AGENTS.md`, `docs/app-packages.md`, `docs/workspace-cleanup.md` and the assigned Trellis plan documents |
| Pi p2 | `.github/workflows/cloud-check.yml`, `scripts/check_source_policy.py`, `test/startup_test.dart`, `test/web_server_tools_lifecycle_test.dart`; failure IDs 01–05, 10, 17 |
| Pi p4 | `scripts/verify_app_package.py`, `installer/`, `test/web_catalog_language_test.dart`, `test/web_tools_navigation_test.dart`, `test/web_saved_workspaces_test.dart`; failure IDs 06–09, 11–16 |
| Pi p5 | `.github/workflows/app-packages.yml` and `research/flutter-test-failures-45858109136.md` |

Pi p2 and p4 were idle when this plan was prepared. Pi p5 was working on the
failure report and retains the package files. Do not assign a test file to
multiple workers. If a repair needs a shared production file, assign the whole
file to one owner before editing. Record any transfer here after the previous
owner stops.
