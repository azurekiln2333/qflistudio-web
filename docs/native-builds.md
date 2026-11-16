# GitHub 原生构建

原生构建在 GitHub 托管机上运行。
编译缓存留在托管机上。
本地只需下载最终产物。

2026-11-17 的首次试跑已通过。
构建分支是 `ci/native-build-20261117`。

- [Linux 与 Android 成功记录](https://github.com/azurekiln2333/qflistudio-web/actions/runs/43923902421)。
- [OHOS 成功记录](https://github.com/azurekiln2333/qflistudio-web/actions/runs/43923264898)。

Linux 与 Android 对应提交 `4044058`。
OHOS 对应提交 `2f98f43`。
后续提交只修正了 Android SDK 工具路径。
这些记录不证明后续源码版本通过。

## 下载

1. 打开仓库的 [Actions 页面](https://github.com/azurekiln2333/qflistudio-web/actions)。
2. 选择 `Native build` 或 `Native OHOS build`。
3. 选择目标分支的成功记录。
4. 核对提交编号。
5. 在页面底部找到 `Artifacts`。
6. 点击所需产物。
7. 解压下载的 ZIP。
8. 解压其中的 `tar.gz`。

下载需要登录 GitHub。
工作流保留产物 14 天。
过期后请重跑工作流。
日志产物名以 `-logs` 结尾。
日志不包含可分发原生库。

## 产物

| 产物名 | 架构 | 内容 |
| --- | --- | --- |
| `native-linux-x86_64` | x86_64 | Nginx、嵌入库、语法库 |
| `native-android-arm64-v8a` | ARM64 | Nginx、语法库 |
| `native-android-armeabi-v7a` | ARMv7 | Nginx、语法库 |
| `native-android-x86_64` | x86_64 | Nginx、语法库 |
| `native-ohos` | ARM64、x86_64 | 嵌入库、NAPI 库、语法库、CDP 库 |

每个压缩包附带头文件和许可证。
`build-manifest.json` 记录提交与文件哈希。
`SHA256SUMS` 列出包内文件哈希。
外层 `.sha256` 记录压缩包哈希。
压缩包不含编译源码树和对象缓存。

Linux 包含这些文件：

```text
bin/nginx
lib/libqfli_nginx.a
lib/libqfli_nginx.so
lib/libqfli_web_syntax.so
```

Android 每个 ABI 包含这些文件：

```text
jniLibs/<ABI>/libnginx_exec.so
jniLibs/<ABI>/libqfli_web_syntax.so
```

`libnginx_exec.so` 是 PIE 程序。
它的 `.so` 后缀用于 Android 打包。
不要用 `dlopen` 加载它。

OHOS 每个 ABI 包含这些文件：

```text
prebuilt/<ABI>/libqfli_nginx.a
embedded/<ABI>/libqfli_nginx.so
libs/<ABI>/libqfli_nginx_napi.so
libs/<ABI>/libqfli_web_cdp_transport.so
libs/<ABI>/libqfli_web_syntax.so
```

`prebuilt/` 提供应用构建所需的静态库。
`embedded/` 提供独立 C ABI 共享库。
`libs/` 提供应用使用的 NAPI 库和语法库。
工作流不构建旧版 OHOS 进程引擎。

## 构建范围

`Native build` 构建 Linux 和 Android 原生层。
Linux 还运行四组原生测试。
测试覆盖语法、生命周期、访问日志和 CDP 传输。
Android 使用 NDK `27.0.12077973`。

`Native OHOS build` 下载公开 OHOS SDK。
SDK 版本为 `6.1.0.31`，对应 API 23。
工作流验证固定 SHA-256。
SDK 下载和解压均发生在 GitHub 托管机上。
本地 SDK `6.1.0.32` 与此版本不同。

这些产物不是 APK、HAP 或 IPA。
原生编译成功不代表设备运行通过。
OHOS 库仍需接入应用构建。
完整应用依赖同级 `qfli_studio_core`。
完整 HAP 还依赖 Flutter OHOS 和 Hvigor。
本次工作流不构建 Windows 或 Apple 原生层。

源码或工作流变动会触发构建。
工作流合入默认分支后可用 `Run workflow` 手动运行。
首次分支试跑由推送触发。

## 本地空间

云构建不会自动删除本地缓存。
仅迁移原生构建也不会消除 Flutter 缓存。
应用构建仍会生成 Dart、Gradle 和 Hvigor 缓存。
当前应用脚本也未自动下载 CI 产物。

| 目录 | 用途 | 清理后的影响 |
| --- | --- | --- |
| `build/` | 应用与原生构建中间文件 | 下次构建重建 |
| `.dart_tool/` | Dart 依赖信息与编译缓存 | 下次解析依赖并重建 |
| `ohos/entry/build/` | OHOS 中间文件与 HAP | 下次 OHOS 构建重建 |
| `android/.gradle/` | 项目 Gradle 缓存 | 下次 Android 构建重建 |
| `vendor/` | 固定上游源码与补丁 | 必须保留 |
| `native/` | 产品原生源码 | 必须保留 |

优先清理旧安装包和独立验证输出。
保留正在使用的增量缓存可缩短下次构建。
删除前应核对文件用途与路径。
本次任务没有删除本地缓存。
