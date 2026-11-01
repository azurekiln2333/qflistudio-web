# C843 剩余失败复核（broker deadline 测试，pi4，2026-10-26）

只读复核。未运行 SDK、工具、测试、浏览器、native 代码、Job 或网络请求。
未改产品代码。未改测试。只写入本文件。

## 1. 结论先说

C843 唯一失败的测试是 `owned_preview_resource_broker_test.dart` 的
`deadline aborts the owned request and releases in-flight accounting`。

它抛 `TimeoutException`，一秒后触发。它没有断言失败。它没有源码帧。

我的判定有两条。

1. 失败点是测试的 `await disconnected.future.timeout(...)`，即该测试文件的 `:487`。
2. 这是**测试夹具缺陷**，不是 broker 缺陷。放一个「等对端断开」的哨兵等待
   `HttpResponse.done`，而夹具从不关闭响应，该 future 永远不完成。

因此该测试在现有写法下**必然**超时。它与 broker 的取消行为无关。

第 10 节记录 root 后来的测试修复。它也记录我对修复后源码的只读复核。

## 2. 失败测试与三处限时等待

测试体在 `test/owned_preview_resource_broker_test.dart:448-491`。
它内部有三处一秒限时。

| 行 | 表达式 | 失败后果 |
| --- | --- | --- |
| `:477` | `broker.fetch('.../slow').timeout(1s)` | fetch 未在 1 秒内返回 |
| `:486` | `broker.dispose().timeout(1s)` | dispose 未在 1 秒内完成 |
| `:487` | `disconnected.future.timeout(1s)` | 服务端始终未「看到断开」 |

门禁日志只写「TimeoutException after one second with no source await location」。
它**不告诉我们**是这三处中的哪一处。这一点我不假装知道。

但 `:487` 足以单独解释整个失败。它在该夹具下必然超时。所以无需归因其他两处。

## 3. SDK 源码证据链

路径根为 `D:\ProgramFiles\flutter_ohos\bin\cache\dart-sdk\lib`。

### 3.1 `HttpResponse.done` 的契约

`_http/http.dart:1060` 声明 `abstract interface class HttpResponse implements IOSink`。
所以 `done` 来自 `IOSink`。

`io/io_sink.dart:133-137` 写明：

```
/// A future that will complete when the consumer closes, or when an
/// error occurs.
///
/// This future is identical to the future returned by [close].
Future get done;
```

关键在末句：`done` 与 `close()` 返回同一个 future。
不调用 `close()`，就没有「正常完成」这一路。

### 3.2 `done` 只有两条完成路径

`io/io_sink.dart` 的实现如下。

- `:214-216` `_closeTarget()` 调 `_target.close().then(_completeDoneValue, onError: _completeDoneError)`。
- `:218` `Future get done => _doneCompleter.future;`
- `:220-224` `_completeDoneValue` 是唯一成功完成点。
- `:226-230` `_completeDoneError` 是唯一异常完成点。
- `:266` 该异常完成点由 `_target.addStream(_controller.stream)` 的 `onError` 触发。

所以 `done` 完成需要两件事之一。
一是 `close()` 走通。二是那次挂起的 `addStream` 抛异常。

### 3.3 挂起的 `addStream` 由谁完成

`_HttpResponse` 的 `_target` 是 `_HttpOutgoing`。

- `_http/http_impl.dart:3834-3836` `_HttpOutgoing.addStream` 转给 `_socket.addStream`。
- `_http/http_impl.dart:3846` `_HttpOutgoing.done` 转给 `_socket.done`。

服务端 socket 侧如下。

- `_internal/vm/bin/socket_patch.dart:2692` `_sink = IOSink(_consumer)`。
- `:2556` `class _SocketStreamConsumer implements StreamConsumer<List<int>>`。
- `:2566-2604` `addStream` 返回 `completer.future`，即 `streamCompleter`。
- `:2653-2663` `done()` 是**唯一**完成 `streamCompleter` 的地方。

只有三处调用 `done()`。

| 行 | 触发条件 |
| --- | --- |
| `:2584` | 写入抛异常 |
| `:2589` | 源流抛异常 |
| `:2596` | 源流 `onDone` |

### 3.4 销毁 socket 不完成挂起的 `addStream`

`socket_patch.dart:2764-2771`：

```
void destroy() {
  // Destroy can always be called to get rid of a socket.
  if (_raw == null) return;
  _consumer.stop();
  _closeRawSocket();
  _controllerClosed = true;
  _controller.close();
}
```

`stop()` 在 `:2665-2672`。它只 `sub.cancel()` 并清空 `subscription`。
它**不**调用 `done()`。

`_controller.close()` 关的是**读取侧**控制器。
它与写入侧的 `streamCompleter` 无关。

更进一步：`stop()` 取消了源流订阅。此后源流 `onDone` 也不会再来。
所以 socket 销毁后，那次挂起的 `addStream` **永久**不完成。

### 3.5 官方文档的同向陈述

`_http/http.dart:73-74` 写 `HttpServer` 的行为：

```
/// Likewise, when writing to an [HttpResponse], any [Socket] exceptions are
/// ignored and any future writes are ignored.
```

即服务端写响应时忽略 socket 异常。它不把异常送到 `done`。

## 4. 夹具为什么必然超时

`/slow` 处理器（`:452-470`）的动作按序如下。

1. 注册 `request.response.done.then(...)`，两个分支都 `disconnected.complete()`。
2. `request.response.write('still waiting')`。
3. `await request.response.flush()`。
4. 函数返回。**不调用 `close()`**。

第 2 步把 `write` 走 `_controller`，从而挂起一次 `_target.addStream`。
第 4 步之后不再有写操作。所以写入异常路径（`:2584`/`:2589`）永不触发。
也没有 `close()`。所以源流 `onDone`（`:2596`）永不触发。

由 3.3 与 3.4：该 `addStream` 永不完成。
由 3.2：`done` 永不完成。
所以 `disconnected` 永不完成。`:487` 必然在 1 秒后抛 `TimeoutException`。

这条链与 broker 做了什么无关。即使 broker 行为无误，`:487` 仍会超时。

## 5. `:477` 与 `:486` 为何安全

### 5.1 `:477`（fetch 返回 504）

broker 的 deadline 定时器在 200 毫秒触发。
`lib/services/owned_preview_resource_broker.dart` 的 `_cancel` 做三件事。
一是设 `operation.response` 为 504。二是 `request.abort(...)`。三是 `client.close(force: true)`。

`close(force: true)` 的路径已在源码中确认。

- `_http/http_impl.dart:2895-2898` `_HttpClient.close` 调 `_closeConnections(force)`。
- `:3156-3159` 对每个 target 调 `close(force)`。
- `:2637-2643` `force` 时对 `_active` 每个连接调 `destroyFromExternal()`。
- `:2446-2450` `destroyFromExternal()` 调 `_socket.destroy()`。

客户端 socket 销毁后，读取侧 `_controller.close()`（`socket_patch.dart:2770`）触发 `onDone`。
`_http/http_parser.dart:932-945` 的 `_onDone` 在消息未完成时报
`HttpException("Connection closed while receiving data")`（`:941-943`），并 `_closeIncoming(true)`。

于是 broker 的 `await for (final chunk in incoming)` 抛异常。
`catch (_)` 接住它。随后 `finally` 调用 `operation.result.complete(...)`，值为 504。

所以 `:477` 得一秒内返回。`activeRequests` 此时已是 0。

### 5.2 `:486`（dispose 完成）

`_dispose` 只等 `pending`（即 `_active` 快照）的 `settled.future`。
到 `:486` 时，`:480` 已断言 `activeRequests == 0`。
所以 `pending` 为空。`Future.wait([])` 立即完成。

所以 `:486` 安全。

## 6. broker 是否应当负责

不应当。测试在 `:487` 之前已断言的每一项，broker 都做到了。

- `:478` 状态码 504：由 `_cancel` 设定。
- `:480` `activeRequests == 0`：由 `finally` 的 `_active.remove` 保证。
- `:481` `retainedBytes == 0`：该路径不 retain。
- `:482-485` 随后合法请求得 200，且体为 `ready`。
- `:486` dispose 干净。

`:487` 想额外证明「服务端观察到断开」。这个意图本身在 dart:io 里没有成立的基础。
`HttpResponse.done` 不是断开探测器。它是「响应已发出」的 future。

即使服务端真的观察到断开，`_SocketStreamConsumer.destroy()` 也不完成 `streamCompleter`。
所以这个哨兵在原理上就不该用 `done`。

## 7. 最小夹具修法评估

### 7.1 建议的最小修法

删掉 `disconnected` 的三处代码。

1. 删 `final disconnected = Completer<void>();`（`:451`）。
2. 删 `unawaited(request.response.done.then<void>(...))` 整段（`:458-467`）。
3. 删 `await disconnected.future.timeout(const Duration(seconds: 1));`（`:487`）。

净减约 12 行。不新增任何机制。

### 7.2 保留项的逐条核对

用户要求保留的五项断言，全部不受影响。

| 要求 | 所在行 | 是否保留 |
| --- | --- | --- |
| 504 | `:478` | 保留，未动 |
| active 0 | `:480` 与 `:488` | 保留，未动 |
| retained 0 | `:481` 与 `:489` | 保留，未动 |
| 随后合法重试得 200 | `:482-485` | 保留，未动 |
| dispose 0 | `:486` | 保留，未动 |

所以最小修法满足用户的全部保留条件。

### 7.3 语义代价

删掉哨兵后，测试不再声称「服务端观察到断开」。
这个声称**本来就不成立**，所以删掉是去掉一个不实声称，不是丢失证据。

但应当明确记录：该测试**不**证明服务端侧断连。
它只证明 broker 侧释放了在飞名额与保留字节，且随后仍可用。

### 7.4 若必须保留「服务端观察到断开」的声称

那么不要用 `done`。可选替代如下，按改动量从小到大。

- 写探针：在 `/slow` 处理器里循环写小片段，直到写操作抛异常再 `complete()`。
  写入异常会走 `socket_patch.dart:2584`，从而完成 `done`。这需要循环与超时收尾。
- `detachSocket()`：拿到底层 socket 后监听其异常事件。它必须在写头之前调用，改动较大。
- `server.connectionsInfo()` 轮询：观察连接数回落。它有轮询与竞态，取证较弱。

三者都不是「最小」。若只是修好这个失败，选 7.1。

## 8. 不确定项

以下各条我如实标注。

- 门禁日志没有源码帧，所以它**无法**定位三处等待中的哪一处。这一点无法从日志弥补。
- 我的定位依据是源码。`:487` 在该夹具下必然超时，因此它单独足以解释失败。
- 我**未运行**任何测试。`:477` 与 `:486` 的「安全」来自源码推理，不是来自观察。
- 我未验证「写探针」变体在真机上的时延表现。它只是源码上有据的选项。
- 我未验证其他 320 个测试。本文件只覆盖这一个失败。
- 我未核实四份修复文件的内容。本报告不发布它们。

## 9. 边界

- 未改 `lib/services/owned_preview_resource_broker.dart`。
- 未改 `test/owned_preview_resource_broker_test.dart`。
- 未改 `../qfli_studio_core`。
- 未运行 SDK、hvigor、dart test、浏览器、native 构建或网络请求。
- 本文件为本轮唯一写入。

## 10. Root 修复后的只读复核

### 10.1 应用的改动

Root 只改了测试。它删掉三处 `disconnected` 代码。它未改 broker。

| 项 | 修复前 | 修复后 | 差值 |
| --- | --- | --- | --- |
| 字节 | 19454 | 19030 | -424 |
| 行 | 580 | 568 | -12 |
| `test(` 声明 | 22 | 22 | 0 |

三处代码合计 12 行。

- 一行 `final disconnected = Completer<void>();`
- 十行 `unawaited(request.response.done.then<void>(...))`
- 一行 `await disconnected.future.timeout(const Duration(seconds: 1));`

用户报「13 行」。我数到 12 行。字节差 424 与行差 12 与我的计数一致。我记录 12 行，并标出这一处计数差异。

### 10.2 保留项逐条核对

改动后的测试在 `test/owned_preview_resource_broker_test.dart:448-479`。

| 要求 | 行 | 核对 |
| --- | --- | --- |
| 504 | `:467` | 在 |
| 策略头 | `:468` `expectPolicy(result)` | 在 |
| active 0 | `:469` | 在 |
| retained 0 | `:470` | 在 |
| 随后合法重试 200 | `:471` 到 `:474` | 在 |
| dispose 有上限 | `:475` `.timeout(1s)` | 在 |
| dispose 后全 0 | `:476` 与 `:477` | 在 |

`expectPolicy` 在 `:60-69`。它断言 CSP、`cache-control: no-store`、`x-content-type-options: nosniff` 三项。它未改。

`:467` 的 504 资源由 broker 的 `_error` 构造。`_error` 在 `:294`。它经 `_headers`（`:306`）带上同样三项策略头。所以 `:468` 对这枚 504 成立。

### 10.3 broker 未改的证据

| 项 | 值 |
| --- | --- |
| 字节 | 11793 |
| 行 | 336 |
| mtime | 11:12:16 |
| SHA256 | `56fd917c3b4706e9dcf7b6328ec55f0e1de5c76a6825190f98c90606e6af13d5` |

字节与 mtime 与修复前相同。关键结构仍在原处。`_cancel` 在 `:285`。`_error` 在 `:294`。`_headers` 在 `:306`。`finally` 在 `:272-284`。

### 10.4 只读最终判定

| 文件 | SHA256 | 字节 | 行 |
| --- | --- | --- | --- |
| `test/owned_preview_resource_broker_test.dart` | `ffb4e6ec0bbb532374bc5c25e3a04dc7eee558fd13d8e83f0edfc39151acc3f8` | 19030 | 568 |
| `lib/services/owned_preview_resource_broker.dart` | `56fd917c3b4706e9dcf7b6328ec55f0e1de5c76a6825190f98c90606e6af13d5` | 11793 | 336 |

判定：源码级 PASS。七项保留要求全部在列。broker 未改。

我未运行任何测试。所以这不是运行期 PASS。

### 10.5 限定

- 第 3 节到第 5 节的 SDK 分析预测 fetch 会结算。它是源码推理，不是运行观察。
- 「1 秒内返回」是运行期属性。它取决于运行时、调度与 socket 收尾时序。我无法从源码保证这一条。
- 门禁日志没有源码帧。它无法指出三处等待中的哪一处失败。第 8 节已记这一点。本节不改这一条。
- 我未运行修复后的 22 个测试。它们是否全过，我不知道。
- 我不把「已修复」写成「已验证」。

### 10.6 残留项

- 测试不再声称服务端观察断开。这正确，因为 `done` 不是断开探测器。
- `:475` 的 dispose 上限以 `_active` 为空为前提。`:469` 已断言该前提。
- `/slow` 处理器仍不关闭响应。收尾靠 `serve` 的 `addTearDown(() => server.close(force: true))`。