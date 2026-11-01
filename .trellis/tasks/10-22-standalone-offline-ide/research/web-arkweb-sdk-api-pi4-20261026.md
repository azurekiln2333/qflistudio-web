# ArkWeb 拦截响应 SDK 面核查（pi4，2026-10-26）

只读核查。未运行 SDK、工具、浏览器、native 代码、Job 或网络请求。
只读取本地文件。只写入本文件。

## 1. 核查对象

目标问题有三个。

1. 已安装 OHOS SDK 是否提供 `onInterceptRequest` 的异步响应能力。
2. 同一套 API 能否传输二进制资源体。
3. 现有测试 `CatalogHarness` 与生产 `FlutterPage` 各用什么承载方式。

## 2. 已安装 SDK 身份

证明来自文件内容，不来自记忆。

| 项 | 值 | 来源 |
| --- | --- | --- |
| `hwsdk.dir` | `D:\ProgramFiles\Huawei\DevEco Studio\sdk` | `ohos/local.properties` |
| 默认 SDK 根 | `...\sdk\default\openharmony` | 目录存在 |
| `apiVersion` | `26` | `ets\oh-uni-package.json` |
| `platformVersion` | `26.0.0` | 同上 |
| `version` | `26.0.0.105` | 同上 |
| `releaseType` | `Release` | 同上 |
| 工程 compat | `5.1.0(18)` | `ohos/build-profile.json5` |
| 工程 target | `6.1.1(24)` | 同上 |

机器上另有 `OpenHarmony\Sdk\20` 与 `OpenHarmony\Sdk\23`。
两者都无 `native\sysroot\usr\include\web\` 头文件目录中的 scheme handler。
`Sdk\20` 完全没有 `web\` 头文件。`Sdk\23` 有。默认 SDK（API 26）有。

下文凡标「已验证」者，均指默认 SDK 的 API 26 文件。

## 3. ETS 面：已验证

声明文件 `ets\component\web.d.ts`，299447 字节，8906 行。

### 3.1 拦截入口

```
web.d.ts:6612  onInterceptRequest(callback: Callback<OnInterceptRequestEvent, WebResourceResponse>): WebAttribute;
```

`@since 9`，`@syscap SystemCapability.Web.Webview.Core`。

同处文档（`:6606-6608`）写明返回值语义：

> If the response value is null, the Web will continue to load the resources. Otherwise, the response value will be used

即返回 `null` 表示放行，返回对象表示接管。

### 3.2 回调是同步的，已验证

`Callback` 声明在 `ets\component\common.d.ts:26369`：

```
declare interface Callback<T, V = void> { (data: T): V; }
```

调用签名返回 `V`，不是 `Promise<V>`。
所以 `onInterceptRequest` 的回调必须**同步**返回一个 `WebResourceResponse` 实例。
回调内无法 `await`。

### 3.3 事件载体

```
web.d.ts:4647  declare interface OnInterceptRequestEvent { request: WebResourceRequest; }
```

`WebResourceRequest`（`web.d.ts:2748`）只读取值方法如下。

| 方法 | 行 | `@since` |
| --- | --- | --- |
| `getRequestHeader(): Array<Header>` | 2767 | 8 |
| `getRequestUrl(): string` | 2777 | 8 |
| `isRequestGesture(): boolean` | 2789 | 8 |
| `isMainFrame(): boolean` | 2798 | 8 |
| `isRedirect(): boolean` | 2810 | 8 |
| `getRequestMethod(): string` | 2824 | 9 |

该类无请求体读取方法。`onInterceptRequest` 文档另注明 POST 无法取体（`:6598`）。

### 3.4 响应体与就绪状态

`WebResourceResponse`（`web.d.ts:2828`）关键成员如下。

| 成员 | 行 | 签名 | `@since` |
| --- | --- | --- | --- |
| `setResponseData` | 2928 | `(data: string \| number \| Resource \| ArrayBuffer): void` | 9（`ArrayBuffer` 自 11） |
| `getResponseDataEx` | 2860 | `(): string \| number \| ArrayBuffer \| Resource \| undefined` | 13 |
| `setResponseCode` | 2978 | `(code: number): void` | 9 |
| `setReasonMessage` | 2958 | `(reason: string): void` | 9 |
| `setResponseMimeType` | 2948 | `(mimeType: string): void` | 9 |
| `setResponseEncoding` | 2938 | `(encoding: string): void` | 9 |
| `setResponseHeader` | 2968 | `(header: Array<Header>): void` | 9 |
| `setResponseIsReady` | 2988 | `(IsReady: boolean): void` | 9 |
| `getResponseIsReady` | 2997 | `(): boolean` | 13 |

`setResponseData` 的参数注释（`:2912-2921`）逐项给出含义：

> string type indicate strings in HTML format.
> number type indicate file handle.
> Resource type indicate `$rawfile` resource.
> ArrayBuffer type indicate binary data. [since 11]

由此得到两条已验证结论。

- 二进制体由 `ArrayBuffer` 承载，API 11 起可用。
- 二进制体也可由**文件句柄号码**（`number`）承载。

**不存在** `setResponseDataEx` 方法。三个 SDK（20、23、26）都只有 getter 版本。
`Sdk\20` 在 `web.d.ts:3745`、`Sdk\23` 在 `:4286`、API 26 在 `:2928`，三处写法一致。
所以任何「用 `setResponseDataEx` 传流」的设想与已安装面不符。

## 4. Native 面：已验证

头文件 `native\sysroot\usr\include\web\arkweb_scheme_handler.h`，41795 字节。

### 4.1 二进制体流式传输

```
:1026  OH_ArkWebResourceHandler_DidReceiveResponse(const ArkWeb_ResourceHandler*, const ArkWeb_Response*)
:1041  OH_ArkWebResourceHandler_DidReceiveData(const ArkWeb_ResourceHandler*, const uint8_t* buffer, int64_t bufLen)
:1055  OH_ArkWebResourceHandler_DidFinish(const ArkWeb_ResourceHandler*)
:1068  OH_ArkWebResourceHandler_DidFailWithError(const ArkWeb_ResourceHandler*, ArkWeb_NetError)
:1083  OH_ArkWebResourceHandler_DidFailWithErrorV2(const ArkWeb_ResourceHandler*, ArkWeb_NetError, bool completeIfNoResponse)
:1013  OH_ArkWebResourceHandler_Destroy(const ArkWeb_ResourceHandler*)
```

全部 `@since 12`，`DidFailWithErrorV2` 为 `@since 20`。

`DidReceiveData` 取 `uint8_t*` 与 `int64_t`，即**真正的二进制分块**。
文档措辞（`:1048`）为 pass response body data，未限制单次调用次数。
`DidFinish` 文档（`:1063`）写明「no more data available」，即显式终止。

这是 ETS 面不具备的能力：ETS 只能一次给整块体，native 可多次投递。

### 4.2 响应构造

```
:816   void OH_ArkWeb_CreateResponse(ArkWeb_Response** response)
:825   void OH_ArkWeb_DestroyResponse(ArkWeb_Response* response)
:837   int32_t OH_ArkWebResponse_SetUrl(ArkWeb_Response*, const char* url)
:885   int32_t OH_ArkWebResponse_SetStatus(ArkWeb_Response*, int status)
:909   int32_t OH_ArkWebResponse_SetStatusText(ArkWeb_Response*, const char* statusText)
:934   int32_t OH_ArkWebResponse_SetMimeType(ArkWeb_Response*, const char* mimeType)
:959   int32_t OH_ArkWebResponse_SetCharset(ArkWeb_Response*, const char* charset)
:985   int32_t OH_ArkWebResponse_SetHeaderByName(ArkWeb_Response*, ...)
```

响应对象由调用方创建，也由调用方销毁（`:812` 注释）。

### 4.3 注册与回调

```
:680   int32_t OH_ArkWeb_RegisterCustomSchemes(const char* scheme, int32_t option)
:715   bool OH_ArkWeb_SetSchemeHandler(const char* scheme, const char* webTag, ArkWeb_SchemeHandler*)
:806   int32_t OH_ArkWebSchemeHandler_SetOnRequestStop(ArkWeb_SchemeHandler*, ArkWeb_OnRequestStop)
:219   typedef void (*ArkWeb_OnRequestStart)(const ArkWeb_SchemeHandler*, ArkWeb_ResourceRequest*, const ArkWeb_ResourceHandler*, bool* intercept)
:249   typedef void (*ArkWeb_OnRequestStop)(const ArkWeb_SchemeHandler*, const ArkWeb_ResourceRequest*)
```

`intercept` 为 `bool*` 出参。置 true 才接管，置 false 则放行。

`ArkWeb_OnRequestStart` 文档（`:216-217`）有一句硬约束：

> This will be called on the IO thread.

`OH_ArkWeb_RegisterCustomSchemes` 的返回值表（`:674-675`）写明：

> `ARKWEB_SCHEME_REGISTER_FAILED` 17100102 - Register custom schemes should be called before create any ArkWeb.

`ArkWeb_CustomSchemeOption`（`:52-91`）共 8 个位标志，含 `STANDARD`、`LOCAL`、`SECURE`、`CORS_ENABLED`、`FETCH_ENABLED`、`CODE_CACHE_ENABLED` 等。

## 5. 已验证与假设的分界

### 5.1 已验证（可当场指到行）

- `onInterceptRequest` 回调是同步的：`Callback<T,V>` 为 `(data: T): V`。
- 异步就绪机制存在：`setResponseIsReady(false)` 后可再置 true（`:2988`）。
- 二进制体两条路：`ArrayBuffer`（`:2928`，API 11 起）与文件句柄号码（`:2912-2921`）。
- native 可多次投递二进制分块，并以 `DidFinish` 终止（`:1041`、`:1055`）。
- 自定义 scheme 必须在任一 ArkWeb 创建前注册（`:674-675`）。
- `ArkWeb_OnRequestStart` 在 IO 线程触发（`:216-217`）。

### 5.2 假设（已安装 SDK 无法证明）

以下各条我都**没有**找到支撑文本。列为假设，不得当成事实使用。

- **H1** ArkWeb 在 `setResponseIsReady(false)` 后等待多久。安装的 `.d.ts` 无任何超时描述。
- **H2** 超时后 ArkWeb 的行为：报错、静默失败，还是回退到网络请求。
- **H3** `number` 文件句柄的**所有权**：ArkWeb 是否关闭该 fd，何时关闭。
- **H4** ArkWeb 复制 `ArrayBuffer`，还是仅引用原缓冲区。回调返回后修改缓冲区是否可见。
- **H5** `setResponseIsReady(true)` 的线程要求。ETS 侧文档未写。
- **H6** `DidReceiveData` 单次与累积的字节上限。
- **H7** 是否支持 `Range` 请求与 206 分段响应。
- **H8** `HEAD` 请求在 native 路径的处理责任归属。

这八条都需要真机或源码才能定论。本文件对它们不作判断。

## 6. 超时与响应生命周期约束

### 6.1 ETS 路径

同步契约带来第一个约束：回调内不能 `await`。
所以「先异步读取文件，再 `return response`」这种写法不成立。
唯一合法的延后方式如下。

1. 建 `WebResourceResponse`。
2. 立刻 `setResponseIsReady(false)`。
3. 同步 `return` 该对象。
4. 之后异步填数据。
5. 最后 `setResponseIsReady(true)`。

第 5 步之前 ArkWeb 处于何种等待状态，安装的 SDK 未说明（见 H1、H2）。
也就是说「异步就绪」这一半是已验证的 API，另「等待多久」那一半是空白。
把空白当无限等待，是没有依据的推断。

一处容易误读的旁证：`web.d.ts:2982` 只写 `@param { boolean } IsReady whether the response is ready`。
全文没有说明调用顺序、线程或超时。所以协议细节只能靠实测。

### 6.2 Native 路径

生命周期约束是从签名与注释直接读出的。

- `DidReceiveResponse` 先于 `DidReceiveData`。`DidFailWithErrorV2` 的注释（`:1079-1081`）以「`DidReceiveResponse` has not been called」为前提描述自动补建响应，反证了次序。
- 每次请求最终必须落到 `DidFinish` 或 `DidFailWithError(V2)` 之一。否则请求无终止点。
- `ArkWeb_Response` 由调用方 `Create` 与 `Destroy`（`:812`、`:825`）。
- `ArkWeb_ResourceHandler` 需 `Destroy`（`:1013`）。
- `OnRequestStart` 在 IO 线程，不能在该线程做长阻塞 I/O。
- 取消侧由 `OnRequestStop`（`:249`）通知，实现需能放弃已投递一半的响应。

`OH_ArkWeb_SetSchemeHandler` 的注释（`:686-687`）另给一条次序：

> SchemeHandler should be set after the BrowserContext created.

即注册 scheme 在建上下文之前，挂 handler 在建上下文之后。两次次序方向相反。

### 6.3 对「离线预览」的推论

如果要用 ArkWeb 拦截本地文件，ETS 路径一次给整块体，受内存限制。
native 路径可分块，但要求接管线程、注册时机与销毁责任都对。
两条路都依赖 `onInterceptRequest` 或 scheme handler，即依赖**当前页面是 ArkWeb `Web` 组件**。
这一点正是第 7 节的关键差别。

## 7. 现有测试与生产承载方式对比

### 7.1 测试侧 `CatalogHarness`

文件 `ohos\entry\src\ohosTest\ets\testability\CatalogHarness.ets`。

```
:136  response(address: string, method: string): WebResourceResponse | null
:158  private document(source: string, code: number, mime: string): WebResourceResponse
:159    const response = new WebResourceResponse();
:160    response.setResponseData(source);
```

`document` 依次设 `setResponseData`、`setResponseCode`、`setReasonMessage`、`setResponseMimeType`、`setResponseEncoding('utf-8')`、`setResponseHeader`。

要点如下。

- 体一律是 `string`。没有一次 `ArrayBuffer`，也没有一次文件句柄号码。
- 从不调用 `setResponseIsReady`。全部同步就绪。
- MIME 只用 `text/html` 与 `text/plain`。
- `:147-148` 注释明确不合成伴生资源：图片、脚本、样式缺失就保持缺失。

挂接处在 `pages\Index.ets:54-56`：

```
.onInterceptRequest((event: OnInterceptRequestEvent) => {
  return this.harness.response(event.request.getRequestUrl(), event.request.getRequestMethod());
})
```

另两个测试文件同一写法。`pages\SelfCdp.ets:95-109` 关闭后回 403 文本。
`SelfCdpProof.ets:211-225` 同样只给字符串体。

工程内检索结果：`setResponseData` 共 3 处调用（`CatalogHarness.ets:160`、`SelfCdpProof.ets:217`、`SelfCdp.ets:107`）。
`setResponseIsReady` 0 处。`getResponseIsReady` 0 处。
`ArrayBuffer` 在 ohos 源码中出现于 `PickerBridge.ets:51`（`fs.read` 读盘）与 `SelfCdpProof.ets:328`（CDP 写管道），都不进资源响应。

### 7.2 生产侧 `FlutterPage`

文件 `D:\ProgramFiles\flutter_ohos\engine\src\flutter\shell\platform\ohos\flutter_embedding\flutter\src\main\ets\embedding\ohos\FlutterPage.ets`，13307 字节。

结构是一个 `XComponent` 承载面：

```
XComponent({ id: this.viewId, type: this.xComponentType, libraryname: 'flutter' })
```

配合 `FlutterManager.getInstance().getFlutterView(this.viewId)`、`onSurfaceCreated`、`onSurfaceDestroyed`。

要点如下。

- 没有 `Web` 组件。
- 没有 `onInterceptRequest`。
- 没有 `WebResourceResponse`。
- 在 `D:\ProgramFiles\flutter_ohos` 全目录检索 `onInterceptRequest`，命中 0 个文件。

所以生产路径不经过 ArkWeb 资源拦截。Flutter 侧内容由 `libflutter.so` 与 Dart 层负责。

### 7.3 对比结论

| 项 | 测试 `CatalogHarness` | 生产 `FlutterPage` |
| --- | --- | --- |
| 承载组件 | ArkWeb `Web` | `XComponent`（`libflutter.so`） |
| 资源拦截 | `onInterceptRequest` | 无 |
| 响应体类型 | 仅 `string` | 不适用 |
| 异步就绪 | 未使用 | 不适用 |
| 二进制体 | 未使用 | 不适用 |

一句话：拦截能力目前只存在于测试侧，且只用了字符串与同步就绪。
生产侧没有这个面。

因此，本仓库没有任何代码走过「ArkWeb 二进制资源传输」。
第 3 节与第 4 节写的 API 是存在的，但都是未运行的通路。

## 8. 未运行与不确定

- 本文件未编译、未运行、未上真机。
- 第 3、4、7 节的每条都来自读取文件，行号可复核。
- 第 5.2 节 8 条假设未验证。
- 未验证 native 路径在真机上能否与现有 `libqfli_web_cdp_transport` 共存。
- 未验证 API 26 头文件能否在 compat 18 的工程里安全使用。头文件存在不等于运行期可用。

## 9. 边界

- 未改任何产品代码。
- 未改 `../qfli_studio_core`。
- 未改 SDK 目录内任何文件。
- 未运行 SDK、hvigor、hdc、浏览器、native 构建或网络请求。
- 本文件为唯一写入。
