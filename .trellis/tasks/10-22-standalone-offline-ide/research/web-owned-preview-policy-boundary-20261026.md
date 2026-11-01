# 自有预览纯策略：API 建议（根固定）, 2026-10-26

父任务是 `10-22-standalone-offline-ide`。
本文件固定 API，供之后的异步 resource broker 复用。
本步不写代码，不建服务器，不改 ETS。

## 定位

这是纯策略，不是 ArkWeb 集成。
它没有平台通道、FFI 或 engine 调用。
它只用 `dart:core`。
在 ArkWeb 集成完成前，只能称它为纯策略。
不得称它实现了离线隔离。

## 固定 API

新文件 `lib/services/owned_preview_policy.dart`。

```dart
enum OwnedPreviewDecision { allow, forbidden, methodNotAllowed, invalidTarget }

const int kOwnedPreviewMaxInFlight = 16;
const int kOwnedPreviewMaxResponseBytes = 2 << 20;
const int kOwnedPreviewMaxRetainedBytes = 16 << 20;
const int kOwnedPreviewMaxDebugTextBytes = 128 << 10;
const Duration kOwnedPreviewRequestDeadline = Duration(seconds: 5);
const String kOwnedPreviewExtraPolicy =
    "connect-src 'none'; worker-src 'none'; frame-src 'none'; form-action 'none'";

OwnedPreviewDecision classifyOwnedResource({
  required String url,
  required String method,
  required String origin,
});

bool isOwnedNavigationAllowed({
  required String url,
  required String origin,
});

String buildOwnedContentSecurityPolicy(String base);
```

三个函数都是纯函数。
两个判定函数对全部输入返回结果。
`buildOwnedContentSecurityPolicy` 拒绝夹带第三条策略的基线。
broker 可以直接同步调用，不必 await 策略。
broker 负责异步、超时与并发上限。

## 判定顺序

先判目标合法性，再判 origin 归属，最后判方法。
顺序固定，测试要锁定它。

| 步骤 | 条件 | 结果 |
| --- | --- | --- |
| 1 | 目标不可解析、scheme 非 HTTP(S)、含用户信息、含反斜杠、含控制字符、含非法转义、含非法路径段 | `invalidTarget` |
| 2 | origin 参数非法 | `invalidTarget` |
| 3 | origin 不等于会话 origin | `forbidden` |
| 4 | 方法不是字面量 `GET` 或 `HEAD` | `methodNotAllowed` |
| 5 | 以上都不命中 | `allow` |

外站加 POST 命中第 3 步，返回 `forbidden`。
这样不回显本页面的方法策略。

## origin 精确规则

origin 必须是 `http` 或 `https`。
主机只接受字面量 `127.0.0.1` 与 `::1`。
端口可以省略，省略时按 scheme 取默认值。
`http://127.0.0.1` 就是 80，`https://127.0.0.1` 就是 443。
显式写出默认端口与省略等价。
显式端口为 0 时拒绝，取值上限为 65535。
不接受 `localhost` 这类 DNS 名。
不接受 `127.12.34.56`、`0.0.0.0`、IPv4 映射 IPv6。
不接受带路径、查询、片段或用户信息的 origin。

`Uri` 会把默认端口归一化掉，`hasPort` 可能为 `false`。
因此不得要求 `hasPort` 为真。
比较用解析后的 Uri，比较 scheme、host 与有效端口。
禁止前缀比较，`127.0.0.1.example` 不算同源。
端口不同仍然拒绝。

## 片段只限 broker 请求边界

`classifyOwnedResource` 面向 HTTP 请求。
请求 URL 带片段时返回 `invalidTarget`。
片段不参与网络目标，请求边界不接受它。

`isOwnedNavigationAllowed` 面向页面跳转。
它先去掉片段，再比较 origin 与端口。
同页锚点因此不算外站，也不产生资源请求。
跨源带片段仍然拒绝。

## resource kind 不可信

策略不读取资源类型。
策略不看 MIME、扩展名、`Accept` 或 `isMainFrame`。
判定只看 url、method 与 origin。

原生回调给出的类型字段可能缺失，页面也能影响它。
因此任何类型字段都不能成为放行依据。
类型限制由 CSP 指令表达，不由策略分支表达。

CSP 承载的类型限制：

| 指令 | 取值 | 含义 |
| --- | --- | --- |
| `connect-src` | `'none'` | 禁止 fetch、XHR、WebSocket、EventSource |
| `worker-src` | `'none'` | 禁止 Worker 与 SharedWorker |
| `frame-src` | `'none'` | 禁止子框架 |
| `form-action` | `'none'` | 禁止表单提交 |
| `default-src` | 沿用基线 | 限定文档、脚本、样式、图片、字体、媒体 |
| `script-src` | 沿用基线 | 保留本地 `'self'`、`data:`、`blob:` |
| `object-src` | 沿用基线 | 保留本地 `'self'`、`data:`、`blob:` |

Service Worker 没有对应放行指令。
产品不注册全局注册接口，策略因此不放开它。

## CSP 双策略契约

`buildOwnedContentSecurityPolicy(base)` 返回两个序列化策略。
形式是基线加逗号加附加策略，中间用 `, ` 分隔。
基线字节原样返回，不改写任何指令。
不把 `data:` 塞进 `script-src`，也不给任何指令加 scheme。

按 W3C CSP 的序列化策略列表语义，两条策略各自运行。
效果就是两者的交集，浏览器分别强制。
只有同一 policy 内重复同一指令才有保留旧值的风险。
因此本函数不做逐条指令解析，也不做指令合并。

`base` 只接受内置常量基线。
它不接受项目字符串或用户输入。
基线含逗号、换行或 NUL 时会塞入第三条策略。
这种输入抛出 `ArgumentError`，函数不猜意图。
空基线或纯空白基线同样抛出 `ArgumentError`。
丢掉基线会丢掉 `default-src`，那是放宽而不是收紧。

对当前基线 `WebProjectConfig.offlineContentSecurityPolicy`，
期望输出是基线原文，后接 `, `，再接附加策略：

```
default-src 'self' data: blob:; script-src 'self' 'unsafe-inline' 'unsafe-eval' blob:; style-src 'self' 'unsafe-inline' data: blob:; connect-src 'self' blob:; form-action 'self'; base-uri 'self'; object-src 'self' data: blob:, connect-src 'none'; worker-src 'none'; frame-src 'none'; form-action 'none'
```

基线里 `connect-src 'self' blob:` 与 `form-action 'self'` 保持原样。
附加策略里的 `'none'` 由第二条策略提供。
输出中逗号只出现一次。

## 转义与字符规则

判定在完整解码之后进行，不是逐个 octet 判定。
不要把 0x80 到 0x9F 的单个字节当作控制字符。
UTF-8 多字节序列因此不会误命中拒绝规则。
`%E4%B8%AD%E6%96%87` 解码为中文，属于合法路径。
`%20` 解码为空格，文件名里的空格同样合法。

只拒绝真正的 Unicode 控制字符：C0、DEL 与 C1。
拒绝格式非法的百分号转义。
拒绝原文里的反斜杠、空白与控制字符。

分隔符与点段检查只看解码后的路径。
路径里拒绝编码斜杠 `%2F`，大小写都算。
query 不做编码斜杠检查。
路径里仍拒绝反斜杠。
路径里仍拒绝 `.`、`..` 与隐藏段。
隐藏段允许 `.well-known` 这一例外。

query 不做分隔符与点段检查。
query 里的 `%2F`、`%2E`、`%2E%2E`、`%5C`、`%20` 都不构成越权。
query 只做控制字符检查。
只解码一次，`%252F` 保持字面量，不在本策略重复解码。

## 方法判定

方法只接受字面的 `GET` 与 `HEAD`。
不做 trim，也不做大写归一。
这样判定与 `HttpClient` 实际发出的方法一致。
`get`、`Head`、`GET ` 都返回 `methodNotAllowed`。

## broker 职责边界

策略只给判定，不发起请求。
broker 在 `allow` 之后才可取字节。
broker 不跟随 3xx，先对 `Location` 目标重新判定。
broker 用 `kOwnedPreviewRequestDeadline` 限制单次请求。
broker 用 `kOwnedPreviewMaxInFlight` 限制并发。
broker 用两个字节上限限制响应与保留量。
超限时 broker 返回可见错误，不得静默放行。

broker 调 CSP 函数时只传内置基线常量。
空基线会抛 `ArgumentError`。
broker 捕获它时必须失败关闭，不得退化成只发附加策略。
broker 传给方法参数的值要与它实际发出的方法字面量一致。
不得先 trim 或转大写再传。

## 范围限定

本策略只服务静态预览与静态调试的第一切片。
不扩展到通用 preview。
代理、请求体、流式资源、WebSocket、worker 都不在本步。
静态调试的文本上限单独由 `kOwnedPreviewMaxDebugTextBytes` 表达。

## 明确不做

不建服务器。
不改 `EntryAbility.ets`。
不改 `ohos/entry`，不改 `qfli_studio_core`。
不改锁文件，不改现有 runner。
不运行 Dart、Flutter、SDK、Job 或浏览器。
不提交。

## 未证实的部分

策略是静态判定，它不能证明运行时零出站。
ArkWeb 对 CSP、`connect-src 'none'` 与 blockNetwork 的实际运行行为尚未测量。
`onInterceptRequest` 是否覆盖 WebSocket 握手、worker 与 Service Worker 尚未测量。
因此本步不产出离线结论。
