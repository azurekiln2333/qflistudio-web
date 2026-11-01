# CSP 三文件与三语 README 最终静态核对

日期：2026-10-26，Asia/Shanghai。
范围：CSP 三文件、契约文字、三语 README。
本轮只做源码与文档静态核对。
未启动 Flutter、Dart、浏览器、SDK、native、WSL 或设备。
未编辑生产文件。未提交。

## 复核对象哈希

```text
27697cdac9bf3e3f8f1c569f1b2999a0f068032163571282902826014858acdd  lib/services/web_project_config.dart
506c39720b1ea9badd7bf716c2b790cbb7e2b773ee1d896e34612a7f4c29d098  test/web_offline_browser_test.dart
fcfd2cb2880556375db36a56ad64223f42d85c29207483ac6cf1412815c944ce  scripts/test_web_offline_browser.mjs
d3608f2018edcb6ba872d7a820af5c98061c8db415b9646852af23fc024147cb  .trellis/spec/backend/web-runtime.md
a306586f2dc01d38bfd0f82449c037593f2a510e921ae18d167e33ba54b7abd6  README.md
4473503131c2306167eb48fbb02c1dfa92279f8ecc46d3b3f5252935e5a251e3  README.en.md
1f7e43516fcd5ce44e000c20fc57c184d12be3d3d280923bdfe89f9e01c226eb  README.zh-Hant.md
```

## 一 策略常量

`lib/services/web_project_config.dart` 第 22-26 行定义统一策略。
第 26 行含 `object-src 'self' data: blob:`。
同一常量由三处挂载：

```text
lib/services/web_dev_server.dart:142
lib/services/nginx_session.dart:340
lib/services/owned_preview_resource_broker.dart:79
```

结论：两个引擎与 owned preview 共用同一策略文字。
静态上无分叉。
`'self'` 之外只有 `data:` 与 `blob:`。
无通配、无外部主机、无任意 HTTP(S) 源。

## 二 测试装配

`test/web_offline_browser_test.dart`：

- 34 行统计 `escapedObjects`。
- 38-39 行把 `/object` 与 `/embed` 计入同一计数。
- 48-50 行定义两个不同 path 的 loopback 负例。
- 74-75 行把两条负例注入 fixture。
- 83-84 行写同源 `local-object.html`。
- 138 行把两条负例传给 JS。
- 163 行断言 `escapedObjects` 为 0。
- 206 行放同源 object 正例。
- 211-212 行放两个 loopback 负例。

结论：真实 sentinel 覆盖两个不同 path。
若任一负例逃过 CSP，sentinel 必打点。
Dart 断言会失败。

## 三 浏览器观察脚本

`scripts/test_web_offline_browser.mjs`：

- 11-14 行取哨兵源。
  它断言哨兵源不同于预览源。
  它断言两条负例同源。
  它断言负例长度为 2。
- 51 行等待 `>= 2` 次 `object-src` 拒绝。
  匹配接受 `origin` 或 `origin + 路径`。
- 57-58 行等待同源 object 文档内容。
- 77 行断言 `escapedRequests` 为空。
- 81-82 行再断言 `>= 2`。
- 85 行保留外部域 object/embed 负例。
- 183 行结束时再断言 `escapedRequests` 为空。

结论：跨源 `blockedURI` 只留 origin 也能匹配。
匹配仍要求精确源与端口。
`127.0.0.1:1234` 与 `127.0.0.1:12345` 不会混同。

## 四 契约一致

`.trellis/spec/backend/web-runtime.md`：

- 127 行写 `object-src 'self' data: blob:`。
- 131-133 行写 object 可加载精确预览源、`data` 或 Blob。
- 131-133 行写其他 HTTP(S) 源必须在网络守卫前失败。
- 138-145 行记录 C606 与 loopback 负例要求。

三处互不矛盾。
契约文字与代码常量一致。

## 五 三语 README 当前证据

README.md：

- 84 行：每个响应带离线 CSP。
- 85 行：CSP 保留内联脚本、本机资源和 data/blob。
- 86 行：CSP 不阻止系统浏览器打开普通链接。
- 87 行：离线不等于隔离整个系统浏览器。
- 223 行：2026-10-24 内容策略修复仍属源码变更。
- 224 行：该修复的浏览器回归测试尚未运行。
- 225 行：当前工作树尚未完成端到端复验。

README.en.md：

- 80 行：Every response carries an offline content policy.
- 81 行：The policy keeps inline scripts, local resources and data/blob assets working.
- 82 行：The policy does not stop a system browser from opening ordinary links.
- 232 行：The 2026-10-24 content policy repair is source only and has not been run.
- 233 行：The current tree is not re-verified end to end.

README.zh-Hant.md：

- 84 行：每個回應帶離線 CSP。
- 85 行：CSP 保留內嵌指令碼、本機資源和 data/blob。
- 86 行：CSP 不阻止系統瀏覽器開啟一般連結。
- 87 行：離線不等於隔離整個系統瀏覽器。
- 223 行：2026-10-24 內容策略修復仍屬原始碼變更。
- 224 行：該修復的瀏覽器迴歸測試尚未執行。
- 225 行：目前工作樹尚未完成端對端複驗。

差异：en 把源码变更与未运行合为 232 一行。
zh 与 zh-Hant 分列 223 与 224。

## 六 验证通过后需更新的精确位置

| 文件 | 行号 | 现状 | 更新动作 |
| --- | --- | --- | --- |
| README.md | 85 | 只列内联脚本、本机资源、data/blob | 补同源 object 文档 |
| README.md | 223 | 修复仍属源码变更 | 写实际结果 |
| README.md | 224 | 浏览器回归尚未运行 | 写实际结果 |
| README.en.md | 81 | 只列 inline/local/data/blob | 补 same-origin object |
| README.en.md | 232 | source only and not run | 写实际结果 |
| README.zh-Hant.md | 85 | 只列內嵌指令碼、本機資源、data/blob | 補同源 object 文件 |
| README.zh-Hant.md | 223 | 修復仍屬原始碼變更 | 寫實際結果 |
| README.zh-Hant.md | 224 | 迴歸測試尚未執行 | 寫實際結果 |

保持原样：

- README.md 与 README.zh-Hant.md 的第 84、86、87 行。
- README.en.md 的第 80、82、83 行。
- README.md 与 README.zh-Hant.md 的第 225 行、README.en.md 的第 233 行。这几行是总体验证范围。
- 三语 README 都未写 `object-src` 字面。

本轮不动任何 README。

## 七 未验证项

- 格式阶段未运行。
  候选修复已落地，结果仍未证实。
- analysis 未运行。
- WebForge 与 Nginx 两个引擎的真实浏览器用例未运行。
- 完整当前套件未运行。
- native、OHOS、设备未运行。
- `object-src 'self'` 对空 `data` 回退的实际行为未在本机复验。
- README 的更新时机取决于上条具名窗口结果。

## 八 边界

本轮只读。
本轮只写入本文件。
未编辑生产文件。
未提交。