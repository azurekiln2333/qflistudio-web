# Design — WebForge 专属内容

## 1. 现状与问题（证据）

本产品 `StudioProfile webProfile` 未设置 `contentRepositoryFactory`，因此
`home_page.dart:56` 回退到 `AssetContentRepository()`，读取共享核心的两个聚合资源：

- `qfli_studio_core/assets/content/tutorials.json`（2.69 MB，1620 条）
- `qfli_studio_core/assets/content/examples.json`（1.58 MB，1620 条）

其中 WebForge 可见的 `html`/`css`/`javascript` 条目各 100 教程 + 100 示例。审计结论：

| 指标 | 结果 |
| --- | --- |
| Web 教程标题 | 100 条仅 24 个不同标题，循环 4 次 |
| Web 教程 `explain` | 300 课共用 **1** 段文本 |
| Web 教程 `output` | 只有 200 个不同值，多为 `weighted=22` |
| Web 示例正文 | 归一化编号后仅 **3** 种签名（每类一种） |
| HTML 示例 | 100 条除编号外**完全相同** |
| 概念标签 | 27 个，`可测试实现`/`边界条件`/`发布检查` 各出现 300 次 |
| 标题示例 | `HTML 001: 数据建模与不变量`、`CSS 002: 接口校验与错误边界`（与前端无关） |

结论：这是占位/模板化数据，不含真正的 HTML/CSS/JS 教学价值。

## 2. 边界与契约

### 消费路径（只读，不改）

```
HomePage._sharedContentRepository
  = StudioProfile.current?.contentRepositoryFactory?.call()
    ?? AssetContentRepository();
```

核心契约（不可改，仅实现）：
- `ContentRepository.load() -> ContentCatalog`
- `ContentRepository.tutorials({ContentFilter}) -> List<TutorialContent>`
- `ContentRepository.examples({ContentFilter}) -> List<ExampleContent>`
- `ContentCatalog.fromJson({tutorialsSource, examplesSource})` 解析 `{schemaVersion, entries:[...]}`。
- `ContentCatalogValidator.validate(...)` 做结构/ID 唯一/必填校验。

### 本产品新增（可写）

```
lib/content/webforge_content_repository.dart   # 实现 ContentRepository，读本产品 assets
assets/content/tutorials.json                  # >=100 教程
assets/content/examples.json                   # >=100 示例
scripts/audit_web_content.py                   # 审计：结构/唯一/关联/占位
scripts/run_examples.mjs                       # Playwright 真实执行示例
scripts/emit_content.py                        # 内容生成器（可复现）
test/content/webforge_content_test.dart        # 产品内容契约测试
```

### 接线方式（约束：不改 main.dart）

`main.dart` 属受限文件。`webProfile` 需要新增
`contentRepositoryFactory: WebForgeContentRepository.new`。该字段在
`StudioProfile` 构造里已存在，但值在 `main.dart` 内。**本任务实现仓库与内容，
接线移交主控/wD:p6**：在 `research/` 记录精确 diff 建议并立即上报，不自行改 `main.dart`。

> 备选（若主控批准由本任务完成）：仅新增一行 `contentRepositoryFactory:`，
> 不触碰其它逻辑。默认走“上报+提供补丁”，避免越权。

## 3. 数据设计

沿用核心 JSON schema（`schemaVersion:1`、`{entries:[...]}`），字段对齐
`_parseTutorial` / `_parseExample`：

教程条目：`id, language, type, locale, level, title, summary, concepts, source,
license, updatedAt, lessons[]`；每课：`id, title, summary, concepts, objective,
prerequisites, explain, code, output, pitfalls[], exercises[{prompt,hint,answer}]`。

示例条目：`id, language, type, locale, level, title, summary, concepts, source,
license, updatedAt, code, expectedOutput, inputFixtures, templateType, sourceLessonId`。

ID 约定：`html-tutorial-001` … `js-example-001`（与共享核心同前缀但本文件独立，
校验以本文件作用域内唯一为准）。

## 4. 内容生成策略

- 结构化课程大纲：三语言 × 主题阶梯（入门/进阶/精通）。
- 生成器 `emit_content.py` 用**课程大纲数据**（人工设计的每课主题、要点、代码骨架）
  产出 JSON；每课代码是**真实、独立、可运行**的前端片段，非填空模板。
- 示例代码直接从教程课提炼可直接运行的最小完整文件（HTML 含 `<style>/<script>`
  或独立 CSS/JS 片段 + 配套驱动），并附带 Playwright 断言锚点（如
  `data-check="..."`、`console.log` 标记）。
- 禁止循环套壳：审计脚本会检测正文归一化后是否重复、`explain` 是否唯一。

## 5. 验证设计

1. **结构/schema**：`ContentCatalog.fromJson` + `ContentCatalogValidator`。
2. **唯一/占位**：脚本统计标题、explain、code、output 的唯一度；归一化后重复即失败。
3. **关联**：示例 `sourceLessonId` 必须在教程课 ID 集合内。
4. **真实执行**：Playwright 加载每个 HTML 示例 / 教程代码，捕获 console、断言
   `expectedOutput` 关键标记；CSS/JS 片段包进测试页执行。
5. **产品测试**：`test/content/webforge_content_test.dart` 断言数量、类型覆盖、
   ID 唯一、无重复正文、无空字段、关联完整。

## 6. 兼容与回滚

- 不删共享核心 web 条目 → 其他产品不受影响；WebForge 仅通过工厂切换到本产品资源。
- 回滚 = 移除 `contentRepositoryFactory` 接线（回到共享资源）+ 删除本产品新增文件。

## 7. 不做的事

- 不修改 `qfli_studio_core` 任何文件/资源。
- 不修改 `main.dart`、`web_tools_page.dart`、平台原生工程。
- 不运行平台构建；不做与内容无关的重构。
