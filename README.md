# QFLIWebForge

[简体中文](README.md) | [繁體中文](README.zh-Hant.md) | [English](README.en.md)

QFLIWebForge 是手机上的网页 IDE。
它在本机预览 HTML、CSS 和 JavaScript 项目。
它把控制台输出送回编辑器。

## 产品定位

- 产品名是 QFLIWebForge。
- 仓库名是 `qfli_web`。
- 应用包名是 `com.azurekiln.qfli.webforge`。
- 应用版本是 1.0.0+1。
- 界面来自共享包 `qfli_studio_core`。
- 本仓库只保留 Web 档位和 Web 工具。

## 功能

### 编辑器与预览

- 共享编辑器支持语法高亮和多文件编辑。
- 项目模板有空白和 HTML 两种。
- 预览服务只监听 `127.0.0.1`。
- 端口 0 自动选择空闲端口。
- 支持静态文件、SPA 回退和目录索引。
- 支持 HTTP 代理和 WebSocket 代理。
- 代理目标只允许本机回环 IP。
- 支持实时刷新。
- 支持控制台、错误和请求诊断。
- 支持当前文件预览。
- 长按运行按钮可预览当前文件。

### 双引擎

- `.qfli/web.json` 的 `engine` 选择引擎。
- `auto` 优先用打包的 Nginx。
- `auto` 在引擎缺失时回退 Dart 中间件。
- `auto` 在 iOS 和 HarmonyOS 先探测嵌入引擎。
- `nginx` 只用 Nginx。缺失时启动失败。
- `webforge` 用 Dart 中间件。
- Nginx 是上游 1.31.6。
- Android 和桌面用进程托管。
- iOS 和 HarmonyOS 用进程内嵌入生命周期。
- 显式 `nginx` 不会回退到其他引擎。

### 离线工具

- 本机服务面板显示地址、请求和控制台。
- JSON、URL 和 Base64 编解码只在本机计算。
- 文档资源检查找出缺失和外部引用。
- CSS 工具算颜色、对比度、盒模型和优先级。
- HTML 工具查标签配对和可访问性。
- 工具页提供终端入口。
- 共享内核决定终端的命令与权限。

### 代码分析

- HTML 用 `html` 解析器。
- CSS 用 `csslib` 解析器。
- JavaScript 用 QuickJS 2026-06-04。
- QuickJS 只编译，不运行代码。
- 分析未保存的缓冲区。
- 缺失原生库时报告不可用。
- 不可用不会伪装成无错误。

### 离线课程

- 课程有 481 个主题。
- 每个主题配 1 个教程和 1 个示例。
- 语言分布：HTML 160、CSS 160、JavaScript 161。
- 每个示例是可预览的 `.html` 文件。
- 浏览器检查提供示例的语义断言。
- HTML 示例 006 故意引用缺失图片。
- 教程和示例说明采用简体中文。

## 离线边界

- 产品隐藏登录、云同步和 Git 入口。
- 产品隐藏 HTTP 客户端和外部代理入口。
- 工具只在本机计算。
- 预览只连回环地址。
- 代理目标必须是字面回环 IP。
- 每个响应带离线 CSP。
- CSP 保留内联脚本和本机资源。
- CSP 允许同源 object 文档和 data/blob 资源。
- CSP 不阻止系统浏览器打开普通链接。
- 离线不等于隔离整个系统浏览器。

## 快速开始

开发要求：

- 需要 Flutter SDK。
- Dart 版本要求 ^3.11.5。
- 构建 HAP 需要 Flutter OHOS SDK。
- 共享编辑器来自同级 `qfli_studio_core`。
- 安装依赖可能联网。
- 产品运行离线。
- 产品不依赖远程服务。

先检出同级 `qfli_studio_core`。目录结构如下。

```text
checkout-parent/
  qfli_studio_core/
  qfli_web/
```

1. 检出同级 `qfli_studio_core`。
2. 在本仓库运行 `flutter pub get`。
3. 连接设备。
4. 运行 `flutter run`。
5. 打开一个 HTML 项目。
6. 点击运行按钮。
7. 查看预览。

可选的 `.qfli/web.json` 配置：

```json
{
  "engine": "auto",
  "port": 0,
  "spaFallback": false,
  "root": ".",
  "proxies": [
    { "prefix": "/api", "target": "http://127.0.0.1:8080" }
  ]
}
```

发布构建命令：

```text
flutter build apk --release
flutter build hap --release
```

切换到发布构建时保留 pub 步骤。
`--no-pub` 可能保留旧插件注册表。

## 目录

```text
qfli_web/
├── lib/                产品代码
│   ├── main.dart       档位和启动
│   ├── pages/          工具页和 Web 视图
│   ├── content/        离线课程适配器
│   └── services/       预览、引擎和配置
├── test/               单元和组件测试
├── integration_test/   设备集成测试
├── tool/               原生引擎与验收入口
├── scripts/            内容、构建和浏览器检查
├── native/             嵌入引擎与语法分析桥接
├── vendor/             上游源码、补丁和许可
├── assets/             图标、许可和课程 JSON
├── android/ ios/ macos/ linux/ windows/ ohos/   平台外壳
└── web/                Flutter Web 外壳
```

## 验证

```text
python -X utf8 scripts/emit_content.py
python -X utf8 scripts/test_emit_content.py
python -X utf8 scripts/audit_web_content.py --product --report build/content/audit.md
npm ci
npx playwright install chromium
npm run verify:content
flutter analyze --no-pub lib test integration_test tool
flutter test --no-pub --concurrency=1
```

- 内容脚本重复运行得到相同字节。
- 结构审计检查 ID、映射和唯一性。
- 浏览器检查逐个运行示例。
- 默认 `flutter test` 只运行 `test/`。
- 静态分析不运行集成测试。
- 设备集成测试需要连接设备。
- 原生引擎另有设备冒烟测试。

设备集成与冒烟命令：

```text
flutter test -d DEVICE integration_test/nginx_runtime_test.dart
flutter test -d DEVICE integration_test/content_import_test.dart
flutter run --debug --no-pub -d DEVICE -t tool/nginx_smoke.dart --no-resident
```

- 只有 `[NGINX_SMOKE] PASS` 才算通过。
- 构建成功不算运行证据。

## 平台限制

证据来自历史记录。日期写在单元格里。
历史通过不代表当前候选版本通过。

| 平台 | 打包 | 运行证据 |
| --- | --- | --- |
| Windows x64 | 官方 Nginx 1.31.6 | 2026-10-01 真实二进制集成测试通过 |
| Android x86_64 | NDK PIE，16 KiB 对齐 | 2026-10-01 至 10-03 API 37 模拟器冒烟通过 |
| Android arm64 | APK 已打包 | 2026-10-15 真机原生和内容冒烟通过 |
| Android armv7 | APK 已打包 | 真机运行未验证 |
| HarmonyOS arm64/x86_64 | 嵌入 NAPI 共享库 | 2026-10-12 签名包真机冒烟通过 |
| Linux x86_64 | 上游源码 CMake | 2026-10-02 独立引擎通过。Flutter 应用未验证 |
| macOS arm64/x86_64 | Xcode 打包并签名 | 未运行。无 Apple 构建机 |
| iOS arm64 | 静态库和 Swift 通道 | 未运行。无 Apple 构建机 |

发布签名状态：

- Android release 用 debug key，属于验证包。
- 商店分发需要正式签名。
- OHOS 现阶段没有可达设备目标。
- OHOS 当前包运行未验证。
- iOS 和 macOS 需要 Apple 构建机和签名。
- Windows 全量 Flutter 构建缺 Visual Studio C++ 工具。

当前验证范围：

- 2026-10-22 桌面与移动视口通过 481 项检查。
- 同日 ArkWeb 检查为 474 项通过、7 项失败。
- 失败项已修源码，原生复验仍待运行。
- 2026-10-26 两套引擎的 CSP 回归通过。
- 该修复以 5bd2e3a 发布到五个远端。
- 2026-10-26 C895 全套验证通过。
- 格式、测试、分析、内容四个阶段全部通过。
- 测试 321 项全部通过，失败 0 项。
- 格式检查处理 11 个文件，改动 0 处。
- 静态分析检查 4 个目标，无问题。
- 内容检查 481 对通过，问题 0。
- 验证结束时退出码 0，活动进程数 0。
- 子任务用时 99.981 秒，在自身窗口内。
- C904 认定完整交接证明用时 158.019 秒，未超 180 秒。
- 自有预览策略和资源代理已在本机验证基础范围。
- ArkWeb 集成仍待完成。
- 本轮未运行 OHOS 验证。
- 全产品验收尚未完成。
- 当前工作树尚未完成端到端复验。

## 深入阅读

- 预览和代理契约见 [.trellis/spec/backend/web-runtime.md](.trellis/spec/backend/web-runtime.md)。
- 原生引擎见 [.trellis/spec/backend/native-runtime.md](.trellis/spec/backend/native-runtime.md)。
- 课程验证见 [.trellis/spec/backend/catalog-verification.md](.trellis/spec/backend/catalog-verification.md)。
- 平台证据见 [vendor/nginx/VALIDATION.md](vendor/nginx/VALIDATION.md)。
- 发布检查见 [.trellis/tasks/10-15-webforge-store-readiness/](.trellis/tasks/10-15-webforge-store-readiness/)。
- C843 验收记录见 [web-c843-validation-20261026.md](.trellis/tasks/10-22-standalone-offline-ide/research/web-c843-validation-20261026.md)。
- C895 验收记录见 [web-c895-validation-20261026.md](.trellis/tasks/10-22-standalone-offline-ide/research/web-c895-validation-20261026.md)。

## 许可

- 上游 Nginx 许可见 [vendor/nginx/LICENSE](vendor/nginx/LICENSE)。
- QuickJS 用 MIT 许可，见 [vendor/quickjs/LICENSE](vendor/quickjs/LICENSE)。
- 课程为原创内容，采用 CC BY 4.0。
- 根目录许可见 [LICENSE](LICENSE)，即 GPL-3.0。