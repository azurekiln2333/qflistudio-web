# 自有预览接入 ArkWeb：最小补丁边界, 2026-10-26

父任务 `10-22-standalone-offline-ide`。
本轮只读准备，未改任何生产文件。
未新增抽象。
未运行 Dart、Flutter、SDK、测试、设备或浏览器。
未提交。
文中行号指当前文件行号。

## 已存在的东西

| 文件 | 关键内容 | 与本次接入的关系 |
| --- | --- | --- |
| `lib/services/owned_preview_policy.dart` | 三个判定函数与六个上限常量 | 判定唯一来源，已固定 |
| `lib/services/owned_preview_resource_broker.dart` | `fetch`、租约、`dispose` | 取字节与限额已就绪，直接复用 |
| `ohos/entry/src/main/ets/entryability/OfflinePreviewPolicy.ets` | `isOfflinePreviewUrl` | 现有 openUrl 的校验，与自有路径无关但可参考 |
| `ohos/entry/src/main/ets/entryability/EntryAbility.ets` | `qflistudio/platform` 通道 | 新通道在此注册 |
| `ohos/entry/src/main/ets/entryability/NginxBridge.ets` | 通道注册与销毁模式 | 新桥接的样板 |
| `ohos/entry/src/main/ets/pages/Index.ets` | 仅 `FlutterPage` | 组件挂载点，目前没有 Web 容器 |
| `ohos/entry/src/ohosTest/.../pages/Index.ets` | 隐身 `Web` 加 `onInterceptRequest` | 组件与拦截样板 |
| `ohos/entry/src/ohosTest/.../CatalogHarness.ets` | 同步 `response` | 要替换成异步就绪形态 |
| `ohos/entry/src/ohosTest/.../TestAbility.ets` | `setWebDebuggingAccess` 开关 | 调试租约样板，仅测试 HAP |
| `lib/services/nginx_host.dart` | `EmbeddedNginxHost.channel` | Dart 侧通道调用样板 |
| `lib/pages/web_tools_page.dart` | `_openBrowser` 调 `openUrl` | 要接自有路径的现有入口 |

自有 broker 的公开面本轮不变：

```dart
OwnedPreviewResourceBroker({required String origin, ...});
Future<OwnedPreviewResource> fetch(String url, {String method = 'GET'});
Future<void> dispose();
int get activeRequests;
int get retainedBytes;
bool get isDisposed;
```

关键事实：构造函数不建连接，`HttpClient` 只在 `fetch` 内创建。
因此“准备会话”与“发起请求”可以分开。

## 最小补丁边界

只列四层改动，不做新抽象。

### 第 1 层：ArkUI 组件（新增）

新文件 `ohos/entry/src/main/ets/pages/OwnedWebPreview.ets`。

它只做四件事：

1. 用 `Web` 加 `incognitoMode: true`，并设 `blockNetwork(true)`。
2. 用 `onInterceptRequest` 把每个 HTTP(S) 请求交给桥接，不自己判定。
3. 用 `onLoadIntercept` 与 `onOverrideUrlLoading` 拒绝外部、自定义与 file 跳转。
4. 不建弹窗控制器，不启下载处理器，不授页面权限。

它复用测试页的组件形态（`testability/pages/Index.ets:48`、`:54`）。
区别是响应要异步就绪，不能用同步 `response`。

### 第 2 层：桥接（新增）

新文件 `ohos/entry/src/main/ets/entryability/WebPreviewBridge.ets`。

职责：

- 注册方法通道 `qflistudio/web_preview`。
- 注册事件通道 `qflistudio/web_preview/events`。
- 持有唯一会话状态与组件控制器引用。
- 把原生资源请求转成通道调用，等 Dart 回包后置就绪。
- 会话结束时关闭调试并上报 `closed`。

注册位置照抄 `NginxBridge.ets:58`、`:63` 的写法。
错误码用计划里已定的稳定集合，不新增。

### 第 3 层：页面挂载（改一处）

`ohos/entry/src/main/ets/pages/Index.ets`。

现在只有 `Column() { FlutterPage(...) }`（`:68`、`:69`）。
改成 `Stack` 承载两者，Flutter 保持存活。
可见性用现有 `eventHub` 事件或 `LocalStorage` 切换，不卸载 Flutter。
`onBackPress` 逻辑不动。

这一步只改挂载与显隐，不改 Flutter 路由。

### 第 4 层：能力注册与销毁（改一处）

`ohos/entry/src/main/ets/entryability/EntryAbility.ets`。

- `configureFlutterEngine` 内，在 `configureNginxChannel(flutterEngine)` 之后
  加一行注册自有预览通道。位置见 `EntryAbility.ets:42`。
- `onDestroy` 内，在 `stopActiveNginx()` 之后加一行自有预览销毁。
  位置见 `EntryAbility.ets` 的 `onDestroy`。

不改 `qflistudio/platform` 的 `openUrl` 分支。
自有路径失败必须返回错误，不得退回系统浏览器。

### Dart 侧消费（新增一个文件，不新增抽象）

新文件 `lib/services/owned_web_preview.dart`。

它只是 broker 的通道消费者：

- 持有 `OwnedPreviewResourceBroker` 实例。
- 处理 `prepare`、`open`、`navigate`、`present`、`stop`、`poll`。
- 处理原生 `resource` 回调，调 broker `fetch`，把状态、类型与字节回包。
- 通道调用模式照抄 `nginx_host.dart` 的 `EmbeddedNginxHost.channel`。

入口替换点：`lib/pages/web_tools_page.dart:147`。
该处现在对 ohos 调 `qflistudio/platform` 的 `openUrl`。
自有路径接入后，它改为走自有会话。
非 ohos 分支保持原样。

共享核心 `qfli_studio_core` 不改。
现有 runner 不改。锁文件不改。

## 可复用点清单

| 复用点 | 位置 | 复用什么 | 需要改造的部分 |
| --- | --- | --- | --- |
| 通道注册 | `EntryAbility.ets:36`、`:42` | 引擎与 `getBinaryMessenger` | 新增一行注册 |
| 通道样板 | `NginxBridge.ets:58`、`:63` | `setMethodCallHandler` 与错误映射 | 换方法名与错误码 |
| Dart 通道调用 | `nginx_host.dart` `EmbeddedNginxHost.channel` | `invokeMethod` 与类型校验 | 换方法名与参数 |
| 页面挂载 | `Index.ets:68`、`:69` | `Column` 承载 `FlutterPage` | 改为 `Stack` |
| 组件形态 | `testability/pages/Index.ets:48` | `Web`、`controller`、隐身 | 加 `blockNetwork` 与导航回调 |
| 拦截回调 | `testability/pages/Index.ets:54` | `onInterceptRequest` 签名 | 改异步就绪 |
| 响应构造 | `CatalogHarness.ets:159` | `WebResourceResponse` 与头设置 | 改 `setResponseIsReady` |
| 回环目标判定 | `CatalogHarness.ets` 的 `127.0.0.1` 正则 | 端口范围思路 | 本策略已用精确 origin，不再用正则 |
| 调试开关 | `TestAbility.ets:35`、`:38`、`:90`、`:92` | 单参数 `setWebDebuggingAccess` 的开与关 | 移入生产桥接，加租约 |

调试开关目前只在测试 HAP。
生产接入要新增生产侧所有者，并保证关闭。
`setWebDebuggingAccess` 是应用级开关，需要与阅读器等其他 `Web` 串行。

## 调用顺序

### 静态预览（无调试）

1. Dart 解析项目与根，拒绝代理规则，启动回环运行时，拿到真实 origin。
2. Dart 构造 `OwnedPreviewResourceBroker(origin: origin)`。
   此步不建连接。
3. Dart 调 `prepare`，带 `schemaVersion`、`sessionId`、`origin`、`bootstrapUrl`。
4. 桥接校验后回 `prepared`，此时不加载项目代码。
5. Dart 调 `open`，桥接让组件挂到随机 bootstrap URL。
   CSP 与 `blockNetwork` 在加载前已生效。
6. 组件发出资源请求，`onInterceptRequest` 交给桥接。
7. 桥接发 `resource` 回调给 Dart，含 `requestId`、`url`、`method`、`isMainFrame`。
8. Dart 调 `classifyOwnedResource`。
   非 `allow` 直接回显式错误。
9. `allow` 时 Dart 调 broker `fetch`，取字节与状态。
10. Dart 回包，桥接置该响应为就绪。
11. 页面脚本或样式到达后，重复第 6 至第 10 步。
12. Dart 调 `present` 切换可见性。
13. `stop` 时桥接先停止新工作，再结算挂起响应，再移除组件，再关调试。
14. Dart `poll` 到 `closed` 才发布终止快照，并调 broker `dispose`。

### 静态调试（后续切片）

在第 5 步之后加：

1. 只用单参数 `setWebDebuggingAccess(true)` 开启，不用 TCP 端口重载。
2. 原生自连接通道接默认抽象 socket。
3. 选中与随机 bootstrap 完全匹配的单一目标。
4. 校验主框架后启用所需域，再加载入口。
5. 停止时先停 broker，再关调试，再确认自连接失败。

调试切片依赖原生传输，不在本步边界内。

## 数据流

```
ArkWeb Web 组件
  onInterceptRequest(url, method)
      -> WebPreviewBridge (ArkTS)
          -> 方法调用 qflistudio/web_preview 的 resource 回调
              -> owned_web_preview.dart
                  -> classifyOwnedResource(url, method, origin)
                  -> OwnedPreviewResourceBroker.fetch(url, method)
                      -> 本机回环 HttpClient (DIRECT, 不跟随重定向)
                          -> 本地运行时
                      <- 字节 + 状态码
                  <- 状态 / 类型 / 字节
          <- 完成挂起响应
  <- 浏览器渲染
```

方向要点：资源请求由原生发起，Dart 是应答方。
Dart 回调不能在 ArkUI 线程同步等待。
挂起响应必须用异步就绪，不能返回 `null`。
Dart 未回包、超时或出错时，桥接要回显式错误，不能放行。

已定上限在两侧都要校验：
单响应 2 MiB，保留 16 MiB，并发 16，单请求 5 秒，调试文本 128 KiB。
超限要回可见错误。

## 与策略和 broker 的接口约束

- 判定只用 `classifyOwnedResource`，不复制 origin 比较。
- 导航只用 `isOwnedNavigationAllowed`，它已去片段。
- CSP 只传内置基线常量给 `buildOwnedContentSecurityPolicy`。
  抛错时失败关闭，不得退化成只发附加策略。
- 方法值原样传递，不做 trim 或转大写。
- broker 保持在 Dart 侧，原生只做转发，不自己取字节。

## 当前缺失的运行证据

以下全部未运行，不得据此声称可用：

- 生产自有 `Web` 组件不存在，页面只有 `FlutterPage`。
- `qflistudio/web_preview` 与事件通道不存在。
- 异步挂起响应（`setResponseIsReady(false)`）未在真机验证。
- `blockNetwork(true)` 与合成拦截响应的实际兼容性未测量。
- `connect-src 'none'`、`worker-src 'none'`、`frame-src 'none'` 的实际强制未测量。
- `onInterceptRequest` 是否覆盖 WebSocket 握手未测量。
- worker、SharedWorker 与 Service Worker 路径未测量。
- `onOverrideUrlLoading` 不含 POST 的缺口未测量。
- 原生到 Dart 的回调在 ArkUI 线程上的时延与顺序未测量。
- 自定义 scheme、下载、弹窗、页面权限路径未测量。
- `setWebDebuggingAccess` 在发布 HAP 上的实际行为未测量。
- 原生自连接通道与默认抽象 socket 未验证。
- broker 的真实 socket 行为未验证，broker 测试与策略测试均未运行。
- 无可用设备目标，当前发布产物未签名。

因此本步只是接线准备。
纯策略不等于隔离已实现，broker 不等于已接入。

## 明确不做

不改 `qfli_studio_core`。
不改现有 runner、锁文件与目录结构。
不新增通道之外的抽象。
不把测试 HAP 的组件或调试开关导入生产。
不放开代理、请求体、流式资源、WebSocket 与 worker。
不提交。

## 本轮只读凭据

读过：两份计划、策略、broker、两个测试、`EntryAbility.ets`、`Index.ets`、
`NginxBridge.ets`、`OfflinePreviewPolicy.ets`、`TestAbility.ets`、
`testability/pages/Index.ets`、`CatalogHarness.ets`、`nginx_host.dart`、
`web_tools_page.dart` 片段。
未运行任何命令，未改任何生产文件。