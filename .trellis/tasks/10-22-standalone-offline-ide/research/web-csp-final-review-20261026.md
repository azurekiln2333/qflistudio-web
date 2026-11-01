# CSP 候选最终只读审查

日期：2026-10-26，Asia/Shanghai。
范围：三个待定源文件、生产测试文件格式、三语 README 历史 CSP 说明。
本轮只读审查。
未运行 Flutter、Dart、浏览器、SDK、native、WSL 或设备。
只运行 `scripts/ste-lint-zh.py` 核对本报告。
未动生产文件。未提交。

## 最终哈希

```text
27697cdac9bf3e3f8f1c569f1b2999a0f068032163571282902826014858acdd  lib/services/web_project_config.dart        7292 bytes  2026-10-26 02:30:58
506c39720b1ea9badd7bf716c2b790cbb7e2b773ee1d896e34612a7f4c29d098  test/web_offline_browser_test.dart          9073 bytes  2026-10-26 04:34:21
fcfd2cb2880556375db36a56ad64223f42d85c29207483ac6cf1412815c944ce  scripts/test_web_offline_browser.mjs       11101 bytes  2026-10-26 03:21:57
d3608f2018edcb6ba872d7a820af5c98061c8db415b9646852af23fc024147cb  .trellis/spec/backend/web-runtime.md
a306586f2dc01d38bfd0f82449c037593f2a510e921ae18d167e33ba54b7abd6  README.md                                  8181 bytes  2026-10-26 01:05:04
4473503131c2306167eb48fbb02c1dfa92279f8ecc46d3b3f5252935e5a251e3  README.en.md                               9472 bytes  2026-10-26 01:11:47
1f7e43516fcd5ce44e000c20fc57c184d12be3d3d280923bdfe89f9e01c226eb  README.zh-Hant.md                          8313 bytes  2026-10-26 01:05:04
```

## 与冻结记录对照

三个源文件与 C606 快照的旧哈希不同。
三个源文件与 [修复记录](web-c606-offline-object-repair-20261026.md) 的冻结哈希相同。
修复记录已同步测试文件哈希 `506c3972...`。
修复记录已同步 JS 哈希 `fcfd2cb2...`。

测试文件本轮状态变化：

```text
旧  ff00f9ef540aa82b2d1273ba4c2d75a720905056053b30dbdf6b14d20fcdf45b   9276 bytes
新  506c39720b1ea9badd7bf716c2b790cbb7e2b773ee1d896e34612a7f4c29d098   9073 bytes
```

由根完成。
内容为行尾规范与一处声明拆行。
本轮未运行 formatter，故不能确认格式阶段已通过。

课程字节与 C606 快照相同：

```text
assets/content/examples.json   SAME  b40f900eaf6caa44abc2d1d9fb26d695f8571f8a7394408b99b4dd11632a57cd
assets/content/tutorials.json  SAME  fe05fd1b3164219bba9b259b1aa3564b2052dd816c857c0e076cfed15d077f89
```

HTML137 与 HTML138 的教学源码未改。

## 结论

三个源文件的逻辑审查通过。
无代码逻辑阻断项。
B1 契约矛盾已解除。
B2 的候选修复已落地。实际 format 仍待具名窗口。
B3 行为未验证仍开放。
三语 README 有 8 行待未来授权后更新。本轮保持原文。

## 核对项一：跨源 blockedURI 只保留 origin

事实：跨源 CSP 事件的 `blockedURI` 可能只保留源。
它可能不保留路径。
断言不得依赖完整路径。
当前 JS 已按此修正。

顶层先取哨兵源：

```js
const externalObjectOrigin = new URL(externalObjectUrls[0]).origin;
assert.notEqual(externalObjectOrigin, origin);
assert.equal(externalObjectUrls.length, 2);
assert.ok(externalObjectUrls.every(url => new URL(url).origin === externalObjectOrigin));
assert.equal(new URL(baseUrl).hostname, '127.0.0.1');
```

判定：

```js
(item.directive === 'object-src' && (item.uri === externalObjectOrigin || item.uri.startsWith(`${externalObjectOrigin}/`)))
```

- 比较精确源与端口。
- 另一个 loopback 端口属于不同源。
- 数量门槛为 `>= 2`。
- 两个负例 path 不同。
- 每个负例各产生一次拒绝。
- `uri === origin` 覆盖路径缺失的情况。
- `startsWith(origin + '/')` 覆盖路径保留的情况。
- 该前缀不会把 `127.0.0.1:1234` 与 `127.0.0.1:12345` 混同。
- 端口之后必须是 `/`。

结论：匹配按精确源与端口。
它不依赖完整路径。
它不构成脆弱性。

## 核对项二：HTML137 与 HTML138 原断言

两处断言未变。

HTML137：

- 等待 `#inner` 文本为「运行内联的 HTML 文档」。
- 等待 `#state` 含「内嵌根元素=html」。
- 断言 `embedded.text` 为「运行内联的 HTML 文档」。
- 断言 `embedded.root` 为 `html`。
- 断言 `#state` 全文为
  「type=text/html / data 是 Blob=true / 内嵌根元素=html / 内嵌文本=运行内联的 HTML 文档 / 回退段数=1」。
- 断言 `#figure` 尺寸为 240 × 80。

HTML138：

- 等待 `#state` 含「内部文本=srcdoc 渲染的内容」。
- 用 `data:image/svg+xml` 定位真实子框架。
- 断言 `fill` 为 `rgb(26, 115, 232)`。
- 断言 SVG 为 80 × 40。
- 断言 `circle` 为 32 × 32。
- 断言 `#emb` 尺寸为 80 × 40。

结论：真实内容断言保持原样。
未放宽。

## 核对项三：真实 sentinel 为 0

Dart 侧在第二个 loopback 源上统计三类逃逸：

```dart
var escapedWebSockets = 0;
var escapedReports = 0;
var escapedObjects = 0;
```

两个负例 path 不同：

```text
http://127.0.0.1:<sentinel>/object
http://127.0.0.1:<sentinel>/embed
```

断言：

```dart
expect(escapedRequests, isEmpty);   // 来自 JS 报告
expect(escapedWebSockets, 0);
expect(escapedReports, 0);
expect(escapedObjects, 0);
```

JS 侧同时断言 `escapedRequests` 为空。
若 CSP 未拦截任一负例，请求会到达另一个源。
于是 `escapedRequests` 非空。
或 sentinel 打点。
两个断言都会失败。
保护成立。

## 核对项四：生产测试文件格式

来源：`web-relay-window-incident-20261026.md`。
format 阶段报告 `Changed test/web_offline_browser_test.dart`，退出码 1。
本轮未运行 formatter。
故无法确定唯一原因。

### 候选因素

以下两项都是候选因素：

1. 旧文件 213 行全部为 CRLF。
   `dart format` 输出 LF。
2. 旧文件第 48 行为 81 字符。
   该行是新增语句。

仅凭静态观察无法分清哪一项触发 `Changed`。

### 当前状态

根已完成两项候选修复：

- 行尾已为 LF。
  实测 214 行，CRLF 为 0 行。
- `externalObjectUrl` 声明已拆两行。

当前第 47 至 50 行：

```text
47: [79]       final externalSocketUrl = 'ws://127.0.0.1:${socketSentinel.port}/socket';
48: [31]       final externalObjectUrl =
49: [59]           'http://127.0.0.1:${socketSentinel.port}/object';
50: [79]       final externalEmbedUrl = 'http://127.0.0.1:${socketSentinel.port}/embed';
```

本轮新增行都不超 80 字符。
无行尾空白。
末字节为换行。
文件仍为未跟踪。

### 新增语句清单（现行行号）

```text
34     var escapedObjects = 0;
38-39  } else if (incoming.uri.path == '/object' ||
           incoming.uri.path == '/embed') {
48-49  final externalObjectUrl =
           'http://127.0.0.1:${socketSentinel.port}/object';
50     final externalEmbedUrl = 'http://127.0.0.1:${socketSentinel.port}/embed';
74-75  .replaceAll('__OFFLINE_OBJECT_URL__', externalObjectUrl)
       .replaceAll('__OFFLINE_EMBED_URL__', externalEmbedUrl),
83-84  File(p.join(project.path, 'local-object.html')).writeAsStringSync(
       '<!doctype html><p id="local-object-content">Local object document</p>',
138    'externalObjectUrls': [externalObjectUrl, externalEmbedUrl],
163    expect(escapedObjects, 0);
206    <object id="local-object" type="text/html" data="local-object.html"></object>
211    <object type="text/html" data="__OFFLINE_OBJECT_URL__"></object>
212    <embed type="image/svg+xml" src="__OFFLINE_EMBED_URL__">
```

### 不触动的超长行

以下超 80 行不在 formatter 的拆分范围：

```text
60   89   "script-src 'none'; report-uri http://127.0.0.1:${socketSentinel.port}/report",   (旧代码)
189  94   window.__offlineViolations.push({directive:event.effectiveDirective, uri:event.blockedURI});   (三引号字符串内)
209  89   <object type="text/html" data="https://object.qfli-offline.invalid/remote.html"></object>   (三引号字符串内)
213  100  <form id="external-form" action="https://qfli-offline.invalid/submit"><button>Submit</button></form>   (三引号字符串内)
```

第 60 行是旧代码，C606 的格式阶段曾报零改动。
第 189、209、213 行位于 `_fixture` 三引号字符串内。
formatter 不改字符串内容。

### 实际 format 仍待具名窗口

上述两项修复是否满足格式阶段，尚未实测。
需在具名窗口运行一次格式阶段。
不得以静态观察代替该结果。

本轮未动该文件。

## 核对项五：三语 README 历史 CSP 说明

以下行是历史 CSP 说明。
未来授权通过后，这些行应一起更新。
当前不得提前改成「通过」。

| 文件 | 行号 | 当前文字 | 未来更新方向 |
| --- | --- | --- | --- |
| README.md | 85 | CSP 保留内联脚本、本机资源和 data/blob。 | 补上同源 object 文档 |
| README.md | 223 | 2026-10-24 内容策略修复仍属源码变更。 | 改成实际运行结果 |
| README.md | 224 | 该修复的浏览器回归测试尚未运行。 | 改成实际运行结果 |
| README.en.md | 81 | The policy keeps inline scripts, local resources and data/blob assets working. | 补上同源 object 文档 |
| README.en.md | 232 | The 2026-10-24 content policy repair is source only and has not been run. | 改成实际运行结果 |
| README.zh-Hant.md | 85 | CSP 保留內嵌指令碼、本機資源和 data/blob。 | 補上同源 object 文件 |
| README.zh-Hant.md | 223 | 2026-10-24 內容策略修復仍屬原始碼變更。 | 改成實際執行結果 |
| README.zh-Hant.md | 224 | 該修復的瀏覽器迴歸測試尚未執行。 | 改成實際執行結果 |

补充：

- README.md 与 README.zh-Hant.md 的第 84 行、README.en.md 的第 80 行只写「带离线 CSP」。
  这三行无需变动。
- README.md 与 README.zh-Hant.md 的第 225 行、README.en.md 的第 233 行是总体验证范围。
  它们不属于 CSP 专述，可不动。
- 三语 README 未写 `object-src` 字面。
  故策略文字只在上述行体现。

本轮未动任何 README。

## 阻断项

### B1 契约文字矛盾（已解除）

`web-runtime.md` 已修正。
当前文字为：
「Objects may load from the exact preview origin, data or Blob URLs. Other
HTTP(S) origins must fail before the network guard.」
该文字与第 127 行的 `object-src 'self' data: blob:` 一致。
该文字与第 138-145 行的 object 策略条目一致。
该文字保留「Do not infer Blob permission from `'self'`」的提醒。
`blob:` 仍显式列出。
契约文件哈希为 `d3608f20...`。
B1 关闭。

### B2 格式候选修复已落地（实测待具名窗口）

候选因素为 CRLF 行尾与 81 字符行。
两项候选修复均由根完成。
当前文件为 LF，且第 48 行已拆。
本轮未运行 formatter。
故格式阶段结果仍未证实。
需在具名窗口重跑格式阶段。

### B3 行为未验证（阻塞验收）

format、analysis、两个引擎的浏览器用例、完整当前套件均未运行。
C606 的 analysis 通过属于旧哈希。
它不算本候选的证据。
需一条新的具名窗口验证。

### 非阻断：历史策略文档

`web-offline-catalog-policy-20261024.md` 是冻结历史记录。
该文仍写旧的 `object-src` 策略。
建议标注 superseded。
由修复记录作为现行说明。
不要改写冻结证据。

## 审查边界

本轮只读取三个源文件、契约文字、生产测试文件格式、三语 README。
本轮只写入本文件。
测试文件的 LF 与拆行由根完成。本轮只读核对。
未启动 Flutter、Dart、浏览器、SDK、native、WSL 或设备。
未动生产文件。
未提交。