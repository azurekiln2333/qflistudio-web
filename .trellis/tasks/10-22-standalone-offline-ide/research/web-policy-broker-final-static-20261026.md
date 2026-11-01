# 纯策略与 broker 接口静态复核, 2026-10-26

父任务 `10-22-standalone-offline-ide`。
本轮只读复核，未改任何代码。
未运行 Dart、Flutter、SDK、测试、设备或浏览器。
所有结论来自源码阅读与文本检查。
运行行为一律标为未验证。

检查对象：

| 文件 | 字节 | 角色 |
| --- | --- | --- |
| `lib/services/owned_preview_policy.dart` | 15060 | 纯策略，判定唯一来源 |
| `lib/services/owned_preview_resource_broker.dart` | 11495 | 字节 broker，消费者 |
| `test/owned_preview_resource_broker_test.dart` | 17768 | broker 测试 |
| `test/owned_preview_policy_test.dart` | 17428 | 策略测试 |

文中的行号指当前文件行号。

## 结论

接口对策略的调用正确，默认端口与 CSP 语义正确。
曾发现一处阻断问题，位于 broker 测试的 origin 期望值。
消费者已修复该期望，见文末追加复核。
修复后未发现新的阻断问题。

## 阻断问题：默认端口 origin 的测试期望相反

`test/owned_preview_resource_broker_test.dart:470` 把 `'http://127.0.0.1'` 列入
「非法 origin」，并期望构造抛错。

策略现在允许省略端口。
`_parseOwnedOrigin` 只拒绝显式端口越界（`owned_preview_policy.dart:227`）。
`http://127.0.0.1` 解析后有效端口为 80，因此 origin 合法。

broker 构造检查用同一判定：

```dart
classifyOwnedResource(url: '$origin/', method: 'GET', origin: origin)
```

代入后返回 `allow`，构造不抛错。
于是 `expect(..., throwsArgumentError)` 失败。

同表其余两项目前仍然成立：
`'http://localhost:3000'` 是 DNS 名，拒绝。
`'http://127.0.0.1:3000/path'` 带路径，拒绝。

处理建议：把该用例改成显式端口，或改为断言「策略接受默认为 80 的 origin」。
本条属于消费者文件，本轮未改。
状态：已修复，见文末追加复核。

## 接口一致性

broker 只使用策略的公开面。
用到的判定只有 `classifyOwnedResource`。
CSP 只用 `buildOwnedContentSecurityPolicy`。
上限只读六个常量，未复制数值字面量。
策略的公开面本轮未变：六个常量、一个枚举、三个函数。
私有 helper 变化不影响 broker。

CSP 基线传的是内置常量：

```dart
buildOwnedContentSecurityPolicy(WebProjectConfig.offlineContentSecurityPolicy)
```

没有传项目字符串或用户输入，符合契约。
函数抛 `ArgumentError` 时 broker 不捕获。
构造因此失败关闭，不会退化成只发附加策略。
这一点正确。

方法值原样透传，没有 trim 或转大写。
`fetch` 的默认值是字面量 `'GET'`。
`'get'` 与 `' GET '` 在判定阶段就返回 `methodNotAllowed`。
broker 测试也断言这两种输入得到 405。

连接阶段做了二次判定。
`connectionFactory` 重新调 `classifyOwnedResource`。
它另外要求 `InternetAddress.tryParse` 命中回环地址。
这是纵深防御，与策略一致，不冲突。

## 默认端口

策略按有效端口比较。
`_effectivePort` 在缺端口时按 scheme 取 80 或 443（`owned_preview_policy.dart:444`）。
broker 建连用 `uri.port`，缺端口时同样是 80 或 443。
两侧口径一致。

需要记录的 SDK 事实（只读 `uri.dart`，未运行 SDK）：

- `int get port => _port ?? _defaultPort(scheme);`
- `bool get hasPort => _port != null;`
- `_makePort` 在端口等于 scheme 默认值时返回 `null`

后果是显式 `:80` 在解析后归一化掉。
因此 `hasPort` 可能为 `false`，不能拿它当合法性条件。
策略已不再要求 `hasPort` 为真，与 SDK 行为一致。

端口不同仍然拒绝。
策略测试覆盖了三类：换个端口、换 scheme、默认对非默认。
broker 侧由同一判定保证，没有第二套端口逻辑。

## UTF-8 与转义

策略先检查转义格式，再完整解码一个组件。
随后只按 Unicode 字符判定。
拒绝 C0、DEL 与 C1 控制字符。
不按单个 octet 拒绝 0x80 到 0x9F。
因此 `%E4%B8%AD%E6%96%87` 与原文中文都合法。
`%20` 解码为空格，文件名里的空格合法。
原生空白与控制字符仍然拒绝。

路径与 query 的检查范围不同。
路径拒绝解码后的反斜杠。
路径拒绝 `.`、`..` 与隐藏段，`.well-known` 例外。
路径拒绝编码斜杠 `%2F`，大小写都拒绝。
query 不做分隔符与点段检查。
query 只做控制字符检查。
所以 `?next=%2Fhome` 与 `?p=%2E%2E` 合法。
只解码一次，`%252F` 不再解。

broker 侧不做二次 URL 解析逻辑。
它把原串交给 `Uri.parse` 后交给 `HttpClient`。
因此中文路径在网线上的字节形态未验证。
见末尾未验证清单。

## GET 与 HEAD

方法只接受字面量 `GET` 与 `HEAD`。
判定与 broker 实际发出的方法使用同一个字符串。
不存在判定通过但发出别的方法的路径。

HEAD 不读取响应体。
broker 跳过字节读取，保留状态码与类型头。
报告 `content-length: 0`，不报告实体长度。
这是可接受的简化，但不等同于真实 HEAD 语义，属非阻断观察。

## CSP 多策略语义

策略返回「基线 + 逗号 + 附加策略」。
基线字节原样保留，不改写任何指令。
`script-src` 保持原值，没有加入 `data:`。
基线里的 `connect-src 'self' blob:` 保留，拒绝值由第二条策略提供。

broker 只写一个 `content-security-policy` 响应头。
头值是上面那条序列化策略列表。
按 CSP 的序列化策略列表语义，UA 分别强制两条策略。
效果是交集，正是需要的收紧。
同一条 policy 内重复指令才有保留旧值的风险。
当前输出没有重复指令：基线本身不含逗号，附加策略也不含。

broker 不复制上游响应头。
它只写自己的六个头：类型、长度、CSP、`no-store`、`nosniff`。
上游的 CSP-Report-Only、Reporting-Endpoints、Report-To、NEL 不会泄漏。
上游 `set-cookie` 与 `refresh` 同样不复制。
broker 测试对这些头逐条断言缺席。

空基线在策略侧抛 `ArgumentError`。
broker 只传常量，因此这条路径不会触发。
即使触发也是构造失败，属失败关闭。

## 非阻断观察

错误响应不计入保留字节。
`_error` 创建的响应不进租约集合，也不加 `_retainedBytes`。
体积很小，但理论上可累积，属资源计数边界而非安全问题。

3xx 一律回 502。
契约原文要求「不跟随，并对 Location 重新判定」。
broker 选择直接拒绝，比契约更严，不构成放行。
记录为措辞差异。

MIME 只用于选择字节上限。
它从不参与放行判定。
声称任意 MIME 最多改变上限档位，不会放宽到 `maxResponseBytes` 之外。
与「resource kind 不可信」一致。

SSE 回 415，超限回 413，超时回 504，停止后回 410。
状态码与判定枚举的映射和策略文档一致。

`HttpClient` 未配置证书回调。
https 回环的自签证书会失败。
当前运行时是 http 回环，属已知限制。

## 未验证清单

以下均未运行验证，不得据此声称可用：

- 两条 CSP 在 ArkWeb 上的实际强制结果。
- `connect-src 'none'` 对 fetch、XHR、WebSocket 的实际拦截。
- `worker-src 'none'` 与 `frame-src 'none'` 的实际效果。
- `HttpClient` 对中文路径在请求行上的实际字节形态。
- `followRedirects = false` 与 3xx 的实际行为组合。
- 真实 socket 上的默认端口连接。
- broker 测试与实际策略测试的通过情况。
- 任何设备或原生集成。

本轮没有产生离线结论。
纯策略不等于隔离已实现。

## 本轮只读凭据

做过的事：读取四个文件、读 SDK 的 `uri.dart` 与 `socket.dart` 声明、文本检查行号。
没有做过的事：运行 Dart、Flutter、SDK、测试、Job、浏览器或设备，未改代码，未提交。

## 追加复核：默认端口测试已修复, 2026-10-26

消费者改动了 broker 测试文件。
本轮只读确认，未改任何代码，未运行任何测试。

复核的修订：`test/owned_preview_resource_broker_test.dart`

- 字节 18588。
- SHA256 `BFE8D1575BC3D3669B6C161273E8688BD4DBD657F4AD6AFF8BEF768EC081C1A9`。

改动一：非法 origin 列表删去无端口项。
该列表现在只留 `http://localhost:3000` 与 `http://127.0.0.1:3000/path`。
两者依旧应当抛错，理由未变。

改动二：新增默认端口用例。
用例名 `accepts normalized default-port origins without creating a client`。
它位于第 467 行。
用例对 `http://127.0.0.1` 与 `https://[::1]` 两个 origin 构造 broker。
它断言 `broker.origin` 回显原值。
它断言 `activeRequests` 为 0。
随后 `await broker.dispose()`。
用例全程不发请求，不建连接。

静态检查两个 origin 都合法：

- `http://127.0.0.1` 省略端口，有效端口为 80。
- `https://[::1]` 省略端口，有效端口为 443。
- 构造检查用 `'$origin/'` 作目标，两例均在 scheme、host 与有效端口上同源。
- 两例方法均为字面量 `GET`，因此判定返回 `allow`，构造不抛错。

用例名中的 “without creating a client” 成立。
`HttpClient` 只在 `fetch` 内创建，构造函数只创建 `_policy`。

`dispose` 在无活动请求与无租约时直接完成。
因此该用例不需要真实 socket。

覆盖评价：两个新 origin 互补。
`http://127.0.0.1` 覆盖 http 加 IPv4 默认端口。
`https://[::1]` 覆盖 https 加 IPv6 默认端口。
两个 origin 合计覆盖了 scheme 与地址族的组合。

仍未验证：该用例的实际运行结果。
本轮未运行 Dart 与测试，因此仍不能声称通过。
隔离仍未实现，结论不变。
