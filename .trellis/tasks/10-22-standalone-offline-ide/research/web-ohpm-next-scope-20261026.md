# OHPM 本地 file 依赖：现有入口能否完成零出站校验

日期 2026-10-26。只读调查。未运行 ohpm、hvigor、SDK、native 或设备。未发频道。未改代码与锁。

对象是已安装的 `@ohos/ohpm 26.0.0.630`，路径 `D:\ProgramFiles\Huawei\DevEco Studio\tools\ohpm`。

## 结论

静态层面：能。现有入口 `ohpm install --module entry --exclusion_project` 足以完成本地 file 依赖的零出站校验。

两个前提缺一不可。

1. 出站阻断必须由外部施加。整个 `lib` 里 `offline` 出现 0 次。OHPM 没有离线开关。
2. 源图仍不完整。它挡住当前窗口。CDP 依赖未进入任何一张已建立的解析表面。

所以现在不该开窗口。先把表面重建，再谈窗口。

## 一、源码校验结果

| 项 | 位置 | 结论 |
| --- | --- | --- |
| 归档后缀判定 | `lib/tools/ohpa/Ohpa.js` | `isFile=/[.](?:tgz\|tar.gz\|tar\|har)$/i` |
| 类型分派 | `lib/core/dependency/dep-fetcher/MetaDataFetcherFactory.js` | SourceCode 走本地读取类 |
| 本地读取 | `.../implementor/SourceCodeMetadataFetcherImpl.js` | 只读目录与 `oh-package.json5` |
| 归档读取 | `.../implementor/LocalArtifactMetadataFetcherImpl.js` | 只读本地路径，取 mtime |
| har 改判 | `lib/core/dependency/util/parseDependency.js` | 仅 `.har` 由 SourceCode 改判 File |
| 链接默认 | `lib/core/install/common/definitions.js` | `link:!0` |
| 模块根集合 | `lib/core/install/service/getModuleRootDirs.js` | 见下节 |
| 唯一 HTTP 出口 | `lib/core/registry/axiosFetch.js` | 全库仅此一处引入 axios |

本地读取类取 `RegistryType.local`。它引用 `registry` 模块只为取该常量。它不调用任何 fetch。

## 二、模块根集合有一处陷阱

`getInstallModuleRootDirs` 的流程如下。

1. `exclusion_project` 为真时不加工程根。
2. 传入 `--module` 时，追加模块根后立即返回。
3. 未传 `--module` 时落到 `getModuleRootDirs`。该函数在 `install_all` 为真时把工程根加回。

本机 `~/.ohpm/.ohpmrc` 写着 `install_all=true`。默认值也是真。

故只写 `--exclusion_project` 不够。必须同时写 `--module entry`，让流程在第 2 步返回。两个参数都写时，`install_all` 不参与。

## 三、未覆盖的依赖图

现有报告只分析了 SourceCode 分支。以下各项不在其覆盖内。

| 项 | 现状 | 风险 |
| --- | --- | --- |
| `libqfli_web_cdp_transport.so` | entry 清单已声明。三张表面全缺 | 这是当前阻塞项 |
| `@ohos/flutter_ohos` | `.har`，走 File 分支 | 原报告未分析该分支 |
| `flutter_native_arm64_v8a` | `.har`，走 File 分支 | 同上 |
| `flutter_native_x86_64` | `.har`，走 File 分支 | 同上 |
| `integration_test` | 绝对路径在 flutter_ohos 包内 | 出仓依赖，且有子依赖 `file:har/flutter.har` |
| `path_provider_ohos` | 绝对路径在 Pub 缓存内 | 出仓依赖，且有子依赖 `file:libs/flutter.har` |
| `@ohos/hypium 1.0.6` | 工程根 devDependencies | 仅靠双参数排除 |
| 两处 `maskedByOverrideDependencyMap` | override 图遮盖 | 未分析遮盖语义 |
| `~/.ohpm/cache` 与 `metadata_cache` | 跨次运行状态 | 未纳入判定 |

三张表面的实测状态。

| 表面 | CDP | nginx | 结论 |
| --- | --- | --- | --- |
| `entry/oh-package-lock.json5` | 缺 | 有 | 6 条本地，0 条 registry，无 URL |
| `oh_modules/.ohpm/lock.json5` 的 `overrideDependencyMap` | 缺 | 有 | 工程根含 hypium |
| `entry/oh_modules` | 缺 | 有 | 链接未建立 |

types 源目录在位。`index.d.ts` 与 `oh-package.json5` 都在。

故阻塞属源图不全。它不是网络失败，也不是解析失败。

## 四、最小新 grant 范围

一条命令，一个目录，一个有界时长。

**允许的 argv**

```
ohpm install --module entry --exclusion_project --log_level debug
```

**工作目录**：`ohos/`

**网络策略**：零出站。由外部阻断，不依赖 OHPM 参数。

**允许的写入**

- `ohos/entry/oh_modules/libqfli_web_cdp_transport.so` 链接
- `ohos/entry/oh-package-lock.json5`
- `ohos/oh-package-lock.json5`
- `ohos/oh_modules/.ohpm/lock.json5`

**明确排除**

- 不得出现 registry 拉取。不得 publish。不得 audit。
- 不启动 hvigor、SDK、设备。
- 不改清单、不改 CMake、不改 `build-profile.json5`。

**前置条件**

- CDP 的链接与锁条目确实缺失，作为反证基线。
- 双参数齐备。缺 `--module` 即可能把工程根拉回图。

**事后判据**

沿用既有报告的 11 项。其中三项是硬判据。

- `entry` 锁出现 CDP 条目，且 `registryType` 为 local。
- `entry/oh_modules` 出现同名链接。
- debug 日志无 `fetchPackageReal` 行。

**反向对照**：另建临时工程，放一个 registry 依赖。该工程必须出现 `fetchPackageReal` 行。若不出现，日志判据不可信，本次判定作废。

## 五、不能由现有入口完成的部分

- 出站是否为零，OHPM 自己不证明。它没有离线开关，也没有 dry-run 网络审计。
- 启动期是否发请求，源码层面无法穷尽。`axiosFetch` 是唯一出口，但调用链是否在 install 前置阶段触发，未实测。
- 锁与缓存跨次复用。同一工程第二次运行可能与第一次不同。
- 出仓依赖的绝对路径可变动。`integration_test` 与 `path_provider_ohos` 指向本机路径。

## 六、边界

未运行 ohpm、hvigor、SDK、native 或设备。未发频道。未改代码、清单或锁。结论只来自已安装源码的静态阅读与本地表面文件的读取。

源码为压缩单行文件。本报告的结论按函数名与正则原文给出，不引用字符偏移。

## 七、建议顺序

1. 先重建三张表面，让 CDP 进入解析图。
2. 再开一条最小 grant，范围如第四节。
3. 同窗口采集 debug 日志。
4. 跑反向对照。
5. 判据不齐则维持 BLOCKED。不得以日志缺行直接宣布零出站。