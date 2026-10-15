# WebForge 专属内容：从入门到精通教程与示例

## Goal

WebForge 目前从共享核心 `qfli_studio_core/assets/content/{tutorials,examples}.json`
读取 HTML/CSS/JavaScript 教程与示例。审计确认这部分内容是**机器生成的占位数据**：
100 个 HTML 教程只循环 24 个与前端无关的后端/接口标题，300 个 Web 课共用同一段
`explain`，100 个 HTML 示例除编号外正文完全相同。用户要求清除本产品原有内容来源，
改为 WebForge 专属、完整、循序渐进、可离线运行、中文讲解的 100+ 教程与 100+ 示例。

## Requirements

- 审计并记录当前 WebForge 实际读取的 HTML/CSS/JavaScript 教程/示例的占位、重复、
  不可运行与残缺情况（逐条，量化）。
- 新建 WebForge 专属内容：`>=100` 个教程、`>=100` 个示例，覆盖 HTML、CSS、
  JavaScript 三类。
- 内容实质不同、循序渐进（入门→进阶→精通）、中文讲解，每条含：目标、概念、
  先修、讲解、可运行代码、预期输出、练习（含提示与答案）、坑点。
- 每个示例的代码可独立运行（真实浏览器执行验证），含预期输出与关键坑点。
- 通过已有的 `StudioProfile.contentRepositoryFactory` 接口与核心
  `ContentRepository` / `ContentCatalog` 数据契约提供本产品内容，**不改共享核心数据**。
- 本产品新增 `assets/content/`（本产品专属），并在 `pubspec.yaml` 注册。
- 适配手机离线预览（内容随包，字符串资源，无网络依赖）。
- 不改 `lib/main.dart`、`web_tools_page.dart`、平台原生代码与共享核心；需接线
  `main.dart` 时通知主控。

## Acceptance Criteria

- [x] `research/content-audit.md` 逐条记录原始 HTML/CSS/JS 内容的占位/重复证据与量化
      （24 标题循环、300 课共用 1 段 explain、示例正文归一化后仅 3 种签名）。
- [x] 新内容共 301 条：教程 301（html 100 / css 100 / javascript 101），
      示例 301 与教程一一对应。交付 `type` 统一为 `html`（可独立预览、导入默认
      `index.html`），学科由 `language` 保留（html/css/javascript）。
- [x] JSON 通过核心 `ContentCatalog.fromJson` 解析；
      `ContentCatalogValidator.validate(enforceReleaseMinimum, requiredTypes:{html})` 无 issue；
      `scripts/audit_web_content.py --product` 输出 0 issue。
- [x] 无占位：标题、`explain`、`code`、`output` 全量唯一；示例正文归一化后 301/301 唯一。
- [x] 教程-示例关联完整：每个示例 `sourceLessonId` 指向存在的教程课；无悬挂引用。
- [x] `scripts/` 审计脚本（`audit_web_content.py`）输出“0 issue”报告并入库。
- [x] 真实浏览器逐条执行（`scripts/run_examples.mjs`，Playwright Chromium，每例独立
      context）。语义断言由逐例 oracle 提供：`js_example_assertions.mjs`（101 条 JS 具体
      console/DOM/交互/canvas 期望）与 `web_markup_assertions.mjs`（p6，200 条 HTML/CSS）；
      marker 仅作 sanity，不作语义验证。**最终 301/301 通过、mapping issues 0**。
- [x] 新增产品侧内容测试 `test/content/webforge_content_test.dart`（由主控按 language 覆盖/
      html 导入合同维护）；`flutter analyze` 无 issue、82 项测试通过。
- [x] 本产品可独立运行；未改共享核心与受限文件（`lib/main.dart`、`web_tools_page.dart`、
      平台原生、`qfli_studio_core`）。

## Constraints

- 只写 `D:/MyNewProjects/qfli_web`；不改 `../qfli_studio_core` 及共享内容。
- 不改 `lib/main.dart`、`lib/pages/web_tools_page.dart`、平台原生工程。
- 不做平台构建；`git add` 显式指定自身文件，禁用 `git add .`。

## Notes

内容放置于本产品 `assets/content/`，由产品 `lib/content/` 下的
`WebForgeContentRepository` 实现核心接口读取。共享核心的 web 占位条目保持不动
（其他产品共用该文件，禁止删改）。
