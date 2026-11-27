# Flutter 测试失败分类：run 45858109136

记录日期：2026-11-26。

## 范围与结论

本报告只分析该次云端运行。
本报告未运行本地测试、构建或安装。
本报告未修改源码或工作流。
本报告未执行 Git 写操作。
以下根因假设均需云端复测。

共确认 **17 个失败、293 个通过、6 个跳过**。
建议先修 Web 测试与 runner 配置。
没有证据支持直接归因于 Core 编译失败。
Core 的 UI 契约变化确实影响了旧测试。
这不等于已证明 Core 存在产品缺陷。

| 失败组 | 数量 | 优先归属 | 置信度 |
| --- | ---: | --- | --- |
| OHOS 启动仍断言旧手机外壳 | 3 | Web 测试 | 高 |
| Android 首帧断言 | 1 | Web 测试，可能受前序失败污染 | 中 |
| 浏览器依赖缺失 | 2 | runner 环境 | 已证实 |
| 教程与示例入口契约过时 | 4 | Web 测试 | 高 |
| 工作区测试仍断言旧首页结构 | 1 | Web 测试 | 高，具体断言应结合外壳选择修订 |
| 工具导航仍假设旧手机外壳与五页导航 | 5 | Web 测试 | 高 |
| 关闭端口探针遇到 ECONNRESET | 1 | Web 测试，受 runner 时序影响 | 中 |
| **合计** | **17** | **15 项先查 Web 测试，2 项修 runner 配置** | |

未确认需要修改 Web 产品源码。
未确认需要修改固定 Core 提交。
修复测试时不得删除真实功能断言。
不得用跳过测试换取成功结果。

## 云端证据与固定输入

- Run：https://github.com/azurekiln2333/qflistudio-web/actions/runs/45858109136
- Linux job：https://github.com/azurekiln2333/qflistudio-web/actions/runs/45858109136/job/140041974643
- Source-policy job：`140041707533`，成功。
- 创建时间：`2026-11-26T16:22:10Z`。
- 分支：`ci/app-packages`。
- Web：`1a05b08117dc69cc8aa160d88f5dc18f0b8d7231`。
- Core：`476a30acee21dc486ee2849dd8064a7be665e4d5`。
- Flutter tag：`3.41.10-ohos-1.0.0`。
- 实际 Flutter commit：`244a0e8abb3085e8675589b13e219af8c41cb7aa`。
- `0337f5378a33614354edde7d8ae8473be5994572` 不是本次运行的实际 HEAD。
- Runner：`ubuntu-24.04`，通过 `xvfb-run` 执行。
- 命令：`xvfb-run --auto-servernum flutter test --no-pub --concurrency=1`。
- Node：错误日志记录 `Node.js v22.23.5`。

上述 Core 与 Flutter commit 出现在步骤环境中。
`Record immutable cloud inputs` 也记录了相同值。

以下步骤全部成功：

1. Source-policy 与 actionlint 检查。
2. 固定 Core 与 Flutter 的 setup。
3. QuickJS 测试夹具构建。
4. `flutter analyze --no-pub lib test`。

最终日志原文：

```text
2026-11-26T16:26:16.1850292Z ##[error]293 tests passed, 17 failed, 6 skipped.
```

以下时间均为 Linux job 的 UTC 日志时间。
以下源码行号均对应固定提交。
它们不代表当前脏工作树的行号。

## 共享源码证据

### S1：设备类别不跟随测试的平台变体

Core `lib/app.dart:109-121` 调用 `resolveAppFormFactor`。
它传入 `Platform.operatingSystem`。
它不传入 `defaultTargetPlatform`。

Core `lib/layout/app_form_factor.dart:38,58-67` 把 Linux 判为 desktop。
测试的 `TargetPlatformVariant` 不会把宿主操作系统改成 OHOS。
调整 `tester.view.physicalSize` 也不会把 Linux 变成 phone。

Core `lib/app.dart:226-242` 的外壳选择如下：

- 未就绪或类别未解析：`SplashScreen`。
- phone：`HomePage`。
- desktop/tablet：`LargeScreenWorkbench`。

Core 提供 `QfliApp.formFactor` 测试注入点。
见 `lib/app.dart:30-47`。
需要旧手机外壳的测试应显式选择 phone。
大屏测试应验证真实大屏外壳。
不应修改 Core 的桌面判定来满足旧 finder。

源码：

- https://github.com/azurekiln2333/qflistudio-core/blob/476a30acee21dc486ee2849dd8064a7be665e4d5/lib/app.dart#L109-L121
- https://github.com/azurekiln2333/qflistudio-core/blob/476a30acee21dc486ee2849dd8064a7be665e4d5/lib/layout/app_form_factor.dart#L38-L85
- https://github.com/azurekiln2333/qflistudio-core/blob/476a30acee21dc486ee2849dd8064a7be665e4d5/lib/app.dart#L226-L242

### S2：教程与示例已合并

Core `lib/pages/home_page.dart:108-114` 明确只有四个主页面。
页面为 home、tools、content、profile。
`168-195` 已无单独的示例导航按钮。
`268-277` 为离线产品创建 `TutorialCenterPage`。

Core `lib/pages/local_content_pages.dart:113-181` 定义合并页面。
它不再是 `LocalTutorialsTab` 或 `ExampleCodeTab`。
`245-269` 使用两个内部 Tab 切换教程与示例。
`273-336` 只在打开搜索后创建 `content-query`。

因此，旧 widget 类型或搜索框不能充当加载完成信号。

云端 `16:25:35.9715040Z` 已通过以下测试：
`Web profile factory retains 481 subjects with HTML import types`。
这支持先排查 UI finder，而不是缩减真实课程资产。

源码：

- https://github.com/azurekiln2333/qflistudio-core/blob/476a30acee21dc486ee2849dd8064a7be665e4d5/lib/pages/home_page.dart#L108-L195
- https://github.com/azurekiln2333/qflistudio-core/blob/476a30acee21dc486ee2849dd8064a7be665e4d5/lib/pages/home_page.dart#L268-L283
- https://github.com/azurekiln2333/qflistudio-core/blob/476a30acee21dc486ee2849dd8064a7be665e4d5/lib/pages/local_content_pages.dart#L113-L181
- https://github.com/azurekiln2333/qflistudio-core/blob/476a30acee21dc486ee2849dd8064a7be665e4d5/lib/pages/local_content_pages.dart#L245-L336

### S3：大屏工具和首页入口不是旧手机导航

Core `lib/shell/large_screen_workbench.dart:217-224` 创建嵌入式 `HomeTab`。
它设置 `embedded: true` 和 `showAgentsScope: false`。
`237-253` 保留 tools 与 tutorial 工作台活动。
它仍传入产品的 `toolsTabBuilder`。
工具能力未因旧导航 finder 失败而被证明消失。

Core `lib/pages/home_page.dart:643-648` 提供直接证据。
嵌入模式检测到 `LargeScreenScope` 后返回 `_workbenchProjects`。
它不会进入后面的手机 scope TabBar 布局。
这解释了工作区用例找到 HomeTab 却找不到 Tab。

源码：

- https://github.com/azurekiln2333/qflistudio-core/blob/476a30acee21dc486ee2849dd8064a7be665e4d5/lib/shell/large_screen_workbench.dart#L214-L270

### S4：浏览器依赖尚未安装

Web `package.json:9-10` 固定 `playwright: 1.64.1`。
两个 `.mjs` 脚本直接导入 `playwright`。
本次 `cloud-check.yml:92-113` 没有 npm 安装步骤。
它也没有安装 Playwright Chromium。
日志已直接证明 npm 模块缺失。
Chromium 可用性仍是随后必须确认的前置条件。
本次日志尚未执行到浏览器启动。

源码：

- https://github.com/azurekiln2333/qflistudio-web/blob/1a05b08117dc69cc8aa160d88f5dc18f0b8d7231/package.json#L9-L10
- https://github.com/azurekiln2333/qflistudio-web/blob/1a05b08117dc69cc8aa160d88f5dc18f0b8d7231/.github/workflows/cloud-check.yml#L92-L113

## 逐项失败

### 01. OHOS：available progress bridge

- 文件：`test/startup_test.dart`。
- 名称：`OHOS keeps native startup through home layout with available progress bridge (variant: TargetPlatform.ohos)`。
- 云端位置：`16:25:22.5600851Z` 起。
- 失败行：`startup_test.dart:79:9`。
- 断言原文：

```text
Expected: exactly one matching candidate
  Actual: _TypeWidgetFinder:<Found 0 widgets with type "HomePage": []>
   Which: means none were found but one was expected
```

- 根因假设：S1。bootstrap 已通过 ready 断言，外壳却仍被假定为 phone。Linux 宿主实际选择 desktop。
- 归属：**Web 测试**，高置信度。
- 建议文件：`test/startup_test.dart`。
- 建议修改：断言当前宿主的真实目标外壳。若必须验证手机 HomePage，则先设计可注入的启动测试入口。
- 不建议：仅为通过 finder 而强制产品源码使用 phone。
- 附带日志：`LTPO: Failed to check switch status: MissingPluginException(No implementation found for method checkLTPOSwitchStatus on channel flutter/nativevsync)`。
- 判读：该行不等于失败原因。实际失败是 HomePage 断言。

### 02. OHOS：missing progress bridge

- 文件：`test/startup_test.dart`。
- 名称：`OHOS keeps native startup through home layout with missing progress bridge (variant: TargetPlatform.ohos)`。
- 云端位置：`16:25:22.9155215Z` 起。
- 失败行：`startup_test.dart:79:9`。
- 断言原文：

```text
Expected: exactly one matching candidate
  Actual: _TypeWidgetFinder:<Found 0 widgets with type "HomePage": []>
   Which: means none were found but one was expected
```

- 根因假设：同 01，符合 S1。缺失 progress bridge 没有阻止 ready 断言通过。
- 归属：**Web 测试**，高置信度。
- 建议文件：`test/startup_test.dart`。
- 建议修改：更新外壳断言，保留缺失 bridge 的启动覆盖。

### 03. OHOS：error progress bridge

- 文件：`test/startup_test.dart`。
- 名称：`OHOS keeps native startup through home layout with error progress bridge (variant: TargetPlatform.ohos)`。
- 云端位置：`16:25:23.1862726Z` 起。
- 失败行：`startup_test.dart:79:9`。
- 断言原文：

```text
Expected: exactly one matching candidate
  Actual: _TypeWidgetFinder:<Found 0 widgets with type "HomePage": []>
   Which: means none were found but one was expected
```

- 根因假设：同 01，符合 S1。
- 归属：**Web 测试**，高置信度。
- 建议文件：`test/startup_test.dart`。
- 建议修改：更新外壳断言，保留异常 bridge 的启动覆盖。
- 附带原文：`Startup progress unavailable: PROGRESS_UNAVAILABLE`，共四行。
- 判读：这是本用例主动模拟的错误。`lib/main.dart:69-78` 已捕获该异常。

### 04. Android：立即发送首帧

- 文件：`test/startup_test.dart`。
- 名称：`Android renders its Flutter loading frame immediately (variant: TargetPlatform.android)`。
- 云端位置：`16:25:23.2009341Z` 起。
- 失败行：`startup_test.dart:105:7`。
- 断言原文：

```text
Expected: true
  Actual: <false>
```

- 实际表达式：`expect(binding.sendFramesToEngine, isTrue)`。
- 根因假设：前三项在首帧释放前失败，可能留下 deferFirstFrame 状态。三项均未走到测试的 1100ms 推进与卸载语句。
- 源码证据：`lib/main.dart:57,81-109` 延迟并最终释放 OHOS 首帧。测试 `79` 行先失败，`87-91` 行因此未执行。teardown 没有等待该启动任务收尾。
- 限制：本次没有 Android 单独运行证据。不能把级联假设写成定论。
- 归属：**Web 测试**优先，中置信度。
- 建议文件：`test/startup_test.dart`。
- 建议修改：先修 01-03，并保证失败路径也完成首帧释放与卸载。
- 后续检查：云端单独执行 Android 用例，再执行整份文件。
- 升级条件：若隔离后仍失败，再检查 Web `lib/main.dart`。

### 05. WebForge：离线浏览器策略

- 文件：`test/web_offline_browser_test.dart`。
- 名称：`production WebForge keeps shipped offline resources and blocks external resources and forms`。
- 云端位置：`16:25:26.3617025Z` 起。
- 失败行：`web_offline_browser_test.dart:155:7`。
- 断言与异常原文：

```text
Expected: <0>
  Actual: <1>
Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'playwright' imported from /home/runner/work/qflistudio-web/qflistudio-web/scripts/test_web_offline_browser.mjs
```

- 根因：S4。Node 在导入模块时退出。
- 归属：**runner 环境**，已证实。
- 建议文件：`.github/workflows/cloud-check.yml`。
- 建议修改：在测试前安装 lockfile 对应的 npm 依赖，并安装 Chromium 与系统依赖。
- 不建议修改：CSP 产品代码或该用例的安全断言。
- 判读：未执行 `escapedRequests`、CSP 与课程页面的浏览器断言。不能据此宣称 CSP 回归。

### 06. 教程：desktop

- 文件：`test/web_catalog_language_test.dart`。
- 名称：`Web tutorial subject chips and title badges on desktop`。
- 云端位置：`16:25:42.8716771Z` 起。
- 堆栈：`_waitForCatalog:336:3`，调用方 `173:11`。
- 异常原文：

```text
The following TestFailure was thrown running a test:
The real WebForge catalog did not appear
```

- 根因假设：S2。测试仍寻找 `LocalTutorialsTab` 下的 `content-query`。真实入口已创建 `TutorialCenterPage`，搜索框默认折叠。
- 归属：**Web 测试**，高置信度。
- 建议文件：`test/web_catalog_language_test.dart`。
- 建议修改：通过真实合并入口验证教程栏目。用课程内容或加载状态等待就绪，搜索前显式展开搜索。
- 必须保留：真实产品资产、481 条总数、科目筛选、badge 与 HTML 导入断言。

### 07. 教程：320px / 2x text

- 文件：`test/web_catalog_language_test.dart`。
- 名称：`Web tutorial subject chips and title badges at 320px with 2x text`。
- 云端位置：`16:25:48.8837690Z` 起。
- 堆栈：`_waitForCatalog:336:3`，调用方 `173:11`。
- 异常原文：

```text
The following TestFailure was thrown running a test:
The real WebForge catalog did not appear
```

- 根因假设：同 06，符合 S2。当前失败不是文字溢出断言。
- 归属：**Web 测试**，高置信度。
- 建议文件：`test/web_catalog_language_test.dart`。
- 建议修改：适配合并页面及折叠搜索，保留窄屏与 2x 文字覆盖。

### 08. 示例：desktop

- 文件：`test/web_catalog_language_test.dart`。
- 名称：`Web example subject chips and title badges on desktop`。
- 云端位置：`16:25:49.0884879Z` 起。
- 堆栈：`web_catalog_language_test.dart:160:24`。
- 异常原文：

```text
The finder "Found 0 widgets with icon "IconData(U+0EF66)" descending from widgets with type
"NavigationRail": []" (used in a call to "tap()") could not find any matching widgets.
```

- 根因假设：S2。测试点击 `Icons.code_outlined` 独立导航项。固定 Core 已删除该导航项。
- 归属：**Web 测试**，高置信度。
- 建议文件：`test/web_catalog_language_test.dart`。
- 建议修改：先进入教程中心，再点击内部 examples Tab。
- 后续风险：仍需同步更新旧 `ExampleCodeTab` 与搜索框 finder。

### 09. 示例：320px / 2x text

- 文件：`test/web_catalog_language_test.dart`。
- 名称：`Web example subject chips and title badges at 320px with 2x text`。
- 云端位置：`16:25:49.3467425Z` 起。
- 堆栈：`web_catalog_language_test.dart:160:24`。
- 异常原文：

```text
The finder "Found 0 widgets with icon "IconData(U+0EF66)" descending from widgets with type
"NavigationBar": []" (used in a call to "tap()") could not find any matching widgets.
```

- 根因假设：同 08，符合 S2。
- 归属：**Web 测试**，高置信度。
- 建议文件：`test/web_catalog_language_test.dart`。
- 建议修改：使用合并入口与内部 examples Tab，保留窄屏和大字覆盖。

### 10. WebForge：浏览器早期 console bridge

- 文件：`test/web_dev_server_test.dart`。
- 名称：`real browser bridge captures early head and body events in WebForge`。
- 云端位置：`16:25:51.4907971Z` 起。
- 失败行：`web_dev_server_test.dart:387:7`。
- 断言与异常原文：

```text
Expected: <0>
  Actual: <1>
Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'playwright' imported from /home/runner/work/qflistudio-web/qflistudio-web/scripts/test_web_console_bridge.mjs
```

- 根因：同 05，符合 S4。
- 归属：**runner 环境**，已证实。
- 建议文件：`.github/workflows/cloud-check.yml`。
- 建议修改：安装固定 npm 依赖与 Chromium。
- 判读：未执行实际浏览器 console bridge 断言。不能据此判定注入代码失效。

### 11. 保存工作区与重建应用

- 文件：`test/web_saved_workspaces_test.dart`。
- 名称：`real Web Home saves a named workspace and reopens both owners after app reconstruction`。
- 云端位置：`16:25:58.4429192Z` 起。
- 失败行：`web_saved_workspaces_test.dart:85:7`。
- 断言原文：

```text
Expected: exactly 4 matching candidates
  Actual: _DescendantWidgetFinder:<Found 0 widgets with type "Tab" descending from widgets with type
"HomeTab": []>
   Which: means none were found but some were expected
```

- 根因假设：S1、S3。测试未指定 formFactor，Linux 因此选择 desktop。嵌入式 HomeTab 返回 `_workbenchProjects`，不会创建手机 scope TabBar。
- 证据边界：注册项目的等待已通过。失败发生在保存工作区之前，不能证明工作区持久化失效。
- 归属：**Web 测试**优先，高置信度。
- 建议文件：`test/web_saved_workspaces_test.dart`。
- 建议修改：先明确该用例验证 phone 还是 desktop。phone 用例可注入 `AppFormFactor.phone`；desktop 用例应使用工作台真实项目与工作区入口。
- 必须保留：双 owner、文档内容、游标、展开目录、重建恢复与源文件字节断言。
- 源码定位：Core `lib/pages/home_page.dart:643-648`。该分支解释了零个 Tab。不要只改期望数量。

### 12. 整合工具页面

- 文件：`test/web_tools_navigation_test.dart`。
- 名称：`tools tab is one integrated offline surface`。
- 云端位置：`16:26:06.0240292Z` 起。
- 堆栈：`openTools:74:18`，调用方 `101:11`。
- 异常原文：

```text
The following StateError was thrown running a test:
Bad state: No element
```

- 实际操作：`tester.tap(find.byIcon(Icons.apps_outlined).first)`。
- 根因假设：S1、S3。Linux 选择大屏工作台，旧手机导航图标 finder 为空。
- 归属：**Web 测试**，高置信度。
- 建议文件：`test/web_tools_navigation_test.dart`。
- 建议修改：手机导航用例显式选择 phone，或改走工作台活动入口。
- 必须保留：整合工具页面与离线隐藏网络入口的断言。

### 13. 离线本地服务设置

- 文件：`test/web_tools_navigation_test.dart`。
- 名称：`local server settings stay offline (no API proxy editor)`。
- 云端位置：`16:26:06.4040841Z` 起。
- 堆栈：`openTools:74:18`，调用方 `119:11`。
- 异常原文：

```text
The following StateError was thrown running a test:
Bad state: No element
```

- 根因假设：同 12。测试尚未进入本地服务设置。
- 归属：**Web 测试**，高置信度。
- 建议文件：`test/web_tools_navigation_test.dart`。
- 建议修改：修复外壳选择与工具导航，再验证无 API proxy 编辑器。

### 14. 保留原有 proxy 配置

- 文件：`test/web_tools_navigation_test.dart`。
- 名称：`pre-existing proxy rules are preserved when saving offline`。
- 云端位置：`16:26:06.7394048Z` 起。
- 堆栈：`openTools:74:18`，调用方 `160:11`。
- 异常原文：

```text
The following StateError was thrown running a test:
Bad state: No element
```

- 根因假设：同 12。测试尚未执行配置保存。
- 归属：**Web 测试**，高置信度。
- 建议文件：`test/web_tools_navigation_test.dart`。
- 建议修改：修复真实入口，保留原有 proxy JSON 的完整性断言。

### 15. 顺序访问五页

- 文件：`test/web_tools_navigation_test.dart`。
- 名称：`all five pages are reachable in order`。
- 云端位置：`16:26:07.0280736Z` 起。
- 失败行：`web_tools_navigation_test.dart:179:5`。
- 断言原文：

```text
Expected: exactly one matching candidate
  Actual: _TypeWidgetFinder:<Found 0 widgets with type "NavigationBar": []>
   Which: means none were found but one was expected
```

- 根因假设：S1 导致未出现手机 NavigationBar。S2 还使“五页”要求过时。
- 归属：**Web 测试**，高置信度。
- 建议文件：`test/web_tools_navigation_test.dart`。
- 建议修改：明确设备类别，覆盖四个主入口与教程中心两个栏目。
- 必须保留：profile/settings 可达与离线账号区域隐藏的断言。

### 16. 窄屏大字访问五页

- 文件：`test/web_tools_navigation_test.dart`。
- 名称：`all five pages survive narrow large-text viewport`。
- 云端位置：`16:26:07.5954094Z` 起。
- 堆栈：`openTools:74:18`，调用方 `243:11`。
- 异常原文：

```text
The following StateError was thrown running a test:
Bad state: No element
```

- 根因假设：S1。320px 的窗口没有把 Linux 设备类别变成 phone。随后仍存在 S2 的独立示例导航问题。
- 归属：**Web 测试**，高置信度。
- 建议文件：`test/web_tools_navigation_test.dart`。
- 建议修改：区分窄窗口 desktop 与 phone 场景。更新合并后的入口，保留 320px / 2x 覆盖。
- 旁证：同文件的 `integrated tools grid survives narrow large-text viewport` 在 `16:26:07.3100835Z` 通过。
- 判读：不能把本次 finder 失败解释为整合工具网格溢出。

### 17. 本地服务关闭探针

- 文件：`test/web_server_tools_lifecycle_test.dart`。
- 名称：`inline local server lifecycle: regular light`。
- 云端位置：`16:26:10.1641002Z` 起。
- 堆栈：`_expectRefused:89:31`、`86:38`，调用方 `343:13`。
- 异常原文：

```text
The following OSError was thrown running a test:
OS Error: Connection reset by peer, errno = 104
```

- 根因假设：unmount 后的异步 stop 与真实 TCP 探针存在竞态。Linux 在连接过程中返回 ECONNRESET，而辅助函数只接受 ECONNREFUSED。
- 源码证据：`_expectRefused:79-120` 仅接受 `{61, 111, 1225, 10061}`。其他错误在 `113` 行立即重抛。`342-343` 行卸载后立即探测第二个服务地址。
- 归属：**Web 测试**优先，中置信度。runner 时序是触发条件，不是已证明的随机 runner 故障。
- 建议文件：`test/web_server_tools_lifecycle_test.dart`。
- 建议修改：把 reset 视作有界重试期间的暂态，不视作关闭成功。继续推进清理，最终仍须观察真正的 refusal。
- 不建议：把任意 socket 错误或超时都算成停止成功。
- 旁证：`inline local server lifecycle: 320px dark with 2x text` 在 `16:26:11.9556326Z` 通过。
- 限制：未排除产品停止逻辑缺陷。若持续无法观察 refusal，再检查 Web `lib/services/web_dev_server.dart` 与 `lib/pages/web_tools_page.dart`。

## 独占修复分工建议

以下仅供协调者分配，不构成新的文件授权。

| 修复单元 | 独占文件 | 对应失败 |
| --- | --- | --- |
| Runner 浏览器依赖 | `.github/workflows/cloud-check.yml` | 05、10 |
| 启动断言与首帧收尾 | `test/startup_test.dart` | 01-04 |
| 真实内容入口适配 | `test/web_catalog_language_test.dart` | 06-09 |
| 设备类别与工具导航 | `test/web_tools_navigation_test.dart` | 12-16 |
| 工作区外壳契约 | `test/web_saved_workspaces_test.dart` | 11 |
| TCP 停止探针竞态 | `test/web_server_tools_lifecycle_test.dart` | 17 |

p2 与 p4 可分别领取互不重叠的文件组。
当前证据不要求变更 Core SHA。
当前证据不要求修改 pubspec 或 lockfile。
当前证据不授权修改打包文件。

## 云端复测要求与未覆盖项

1. 先验证 npm 模块与 Chromium 可用。
2. 单独运行启动测试，再运行完整 suite。
3. 保留真实资产与生产预览服务。
4. 验证大屏与手机场景的外壳选择。
5. 验证教程中心的两个栏目。
6. 对关闭竞态运行重复云端验证。
7. 保留 `cloud-check` 的失败门禁。

本次六项跳过均涉及缺少桌面 Nginx。
其中包括 Nginx 浏览器、proxy 与 IPv6 覆盖。
跳过不等于这些功能通过。
浏览器依赖补齐后仍可能暴露后续错误。
本报告不把尚未执行的断言列为成功。

本报告只写入此研究文件。
未向 `w64:p6` 发送消息。
