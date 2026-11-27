# GitHub 应用安装包构建

`App packages` 工作流在 GitHub 托管机上构建应用安装包。
一次运行从同一个提交构建六个平台。
用户可以在源码工作区之外下载安装包。
代理从不下载安装包。

原生库的单独构建见 [GitHub 原生构建](native-builds.md)。

## 所有权与推送

Codex 决定版本固定值与交付范围。
Codex 的评审结论是本文件的依据。
根协调者暂存、提交、拉取并触发工作流。
实现者不暂存、不提交、不推送。
代理从不运行 `git push`。
交付只走门禁请求文件：
`D:/MyNewProjects/_orchestra/push/qflistudio-web.json`。
请求内容包含仓库名、完整提交 SHA 和 `allow` 条目。
协调脚本推送 GitHub `main`，写出
`push/qflistudio-web.result.json`，并经 Herdr 报告结果。
origin 只把 push URL 收窄到 GitHub。
源工作区保留镜像远端，镜像引用留在源 `.git` 内。
外部备份只保存原 Git 设置。

## 不可变输入

每个任务使用下列固定输入。
不使用浮动分支。
不使用 `latest`。

| 输入 | 固定值 |
| --- | --- |
| Flutter 标签 | `3.41.10-ohos-1.0.0` |
| Flutter 剥离提交 | `244a0e8abb3085e8675589b13e219af8c41cb7aa` |
| Core 提交 | `8e031313ffc8d531c5a6b4d131f721f35da04c86` |

Flutter 输入用剥离提交。
带注释标签的对象 SHA 不是这个值。
设置动作克隆标签后核对 `HEAD`。
该动作还核对远端标签指向同一个提交。
不一致时任务失败。
Core 输入必须是完整提交 SHA。
所有打包任务把 Core 检出到 `../qflistudio-core`。
Dart 包名保持 `qfli_studio_core`。

## 安装包

| 平台 | 安装包 | 架构 | 签名状态 |
| --- | --- | --- | --- |
| Android | APK | arm64-v8a、armeabi-v7a、x86_64 | 调试密钥或仓库密钥 |
| iOS | IPA | arm64 | 未签名 |
| OHOS | HAP | arm64 | 未签名 |
| Linux | `tar.gz`、`deb` | x86_64 | 不签名 |
| Windows | `zip`、安装程序 `exe` | x86_64 | 未签名 |
| macOS | `dmg` | arm64 | ad-hoc 签名，未公证 |

安装包文件名格式如下：

```text
qfli-webforge-<版本>-<平台>[-<架构>].<扩展名>
```

标签运行取标签名去掉前缀 `v` 后的文本作为版本。
其他运行取 `pubspec.yaml` 版本加提交短编号。

## 触发

工作流有三种触发方式。

- 在 Actions 页面手动运行。
- 推送 `v*` 标签。
- 推送改动了工作流、设置动作、`pubspec`、`scripts/`、`vendor/`、`assets/`、`installer/`、任一平台目录、`lib/`、`test/` 或 `integration_test/` 的提交。

手动运行的步骤如下。

1. 打开仓库的 [Actions 页面](https://github.com/azurekiln2333/qflistudio-web/actions)。
2. 选择 `App packages`。
3. 点击 `Run workflow`。
4. 选择目标分支。
5. 点击绿色的 `Run workflow` 按钮。

手动运行不接受输入值。
固定输入写在工作流的环境变量里。
工作流合入默认分支后才显示 `Run workflow` 按钮。

`cloud-check.yml` 由 pull request、分支推送和手动运行触发。
打包任务的第一个作业调用它，作为源码与测试门禁。

## 下载

非标签运行把安装包保存为 Actions 产物。

1. 打开对应的运行记录。
2. 核对提交编号。
3. 在页面底部找到 `Artifacts`。
4. 点击所需产物。
5. 解压下载的 ZIP。

下载需要登录 GitHub。
工作流保留产物 14 天。
过期后请重跑工作流。

| 产物名 | 内容 |
| --- | --- |
| `app-package-android` | APK |
| `app-package-ios` | IPA |
| `app-package-ohos` | HAP |
| `app-package-linux` | `tar.gz` 和 `deb` |
| `app-package-windows` | `zip` 和安装程序 `exe` |
| `app-package-macos` | `dmg` |
| `app-build-logs-<平台>` | 构建日志 |

每个安装包附带 `.sha256` 文件。
该文件记录安装包的 SHA-256。
同一产物里还有 `<平台>.summary.md`。
该文件记录签名状态与 SHA-256。
日志产物不含安装包。

标签运行还会发布 GitHub Release。
Release 包含全部安装包、`SHA256SUMS` 和签名状态表。
只有六个打包任务全部成功时才发布 Release。
任一打包任务失败、取消或跳过时，Release 不发布。

## 密钥

在仓库的 `Settings` 中打开 `Secrets and variables`。
选择 `Actions`，然后添加下列密钥。
全部密钥均为可选项。

| 密钥 | 用途 |
| --- | --- |
| `ANDROID_KEYSTORE_BASE64` | 发布密钥库的 Base64 文本 |
| `ANDROID_KEYSTORE_PASSWORD` | 密钥库密码 |
| `ANDROID_KEY_ALIAS` | 密钥别名 |
| `ANDROID_KEY_PASSWORD` | 密钥密码 |

HarmonyOS 命令行工具不使用密钥。
工具压缩包的地址和哈希写在工作流里。
细节见下文 OHOS 一节。

### OHOS

工作流使用公开托管的命令行工具压缩包。
该压缩包由 `ErBWs/ohos-sdk` 发布。
版本目录是 `6.1.1.280`。
压缩包分成两个分片。
工作流下载两个分片后拼成一个文件。
工作流核对拼合文件的 SHA-256 后再解压。
哈希写在工作流的 `OHOS_TOOLS_SHA256` 里。

压缩包须含 `bin/ohpm`、`tool/node/bin/node` 和
`sdk/default/openharmony/toolchains`。
工作流读取 `sdk/default/sdk-pkg.json` 里的 SDK API 版本。
项目目标是 `6.1.1(24)`，对应 API 版本 24。
API 版本不同时，任务失败。
HAP 会记录构建它的 SDK API。
错误的 API 不是警告项。
缺少上述路径时，任务失败。

分片下载失败时，任务失败并写出 `OHOS toolchain blocker`。
失败的任务不产出 HAP。
失败的任务不计入六平台交付。

### Android

四个 Android 密钥必须同时设置。
只设置其中几个时，Android 任务失败。
四个密钥都未设置时，APK 使用调试密钥。

用下列命令生成 Base64 文本：

```text
base64 -w0 release.jks
```

工作流只在托管机上写入密钥库和 `android/key.properties`。
任务结束时，工作流删除这两个文件。
不要把密钥库或 `key.properties` 提交到仓库。
不要在本地读取 `android/key.properties`。
本地与代理都不做签名构建。

## 未签名产物策略

迁移阶段的安装包不要求签名凭据。
缺少签名凭据不阻塞迁移安装包。

- Android 可以用调试密钥打包。摘要必须写明调试密钥。
- iOS 可以打未签名的 IPA。摘要必须写明未签名。
- OHOS 可以打未签名的 HAP。摘要必须写明未签名。
- Linux 和 Windows 不打签名。macOS 只有 ad-hoc 签名。

分发签名、描述文件、公证、商店上传与设备验收属于后续发布准备工作。
工作流不读取、不恢复、不迁移任何本地签名备份。
仓库中的签名项保持清空。
未来的云端签名材料只来自 Actions 密钥。

## 限制

工作流不只核对内容。
它核对安装包、安装程序和磁盘镜象三层。
Windows 安装程序静默安装，逐文件比对载荷哈希，然后卸载。
`deb` 解包后比对完整载荷、桌面入口和启动器。
`dmg` 挂载后核对镜像中的应用。
此项是预期契约，尚待托管运行证据。
Android 任务运行 `apksigner verify --print-certs`。
macOS 任务运行 `codesign --verify` 并核对 ad-hoc 标记。
工作流不接管设备的安装过程。
工作流不在设备或模拟器上运行应用。
构建成功不代表设备运行通过。
作业定义不等于安装包。
六个作业定义不证明六个平台的安装包都产出。
跳过或失败的平台必须单列为阻塞项。

### Android

调试密钥 APK 只用于验证。
调试密钥 APK 不能上架应用商店。
每台托管机的调试密钥不同。
调试密钥 APK 不能覆盖安装另一次运行的 APK。
请先卸载旧版本。
运行摘要按 APK 的实际证书报告签名状态。

### iOS

IPA 未签名。
未签名的 IPA 不能直接安装到设备。
请用自己的证书和描述文件重新签名。
工作流不上传 TestFlight 或 App Store。
IPA 只含真机 ARM64 程序。
它不能用于模拟器。

### OHOS

HAP 未签名。
设备拒绝安装未签名的 HAP。
安装前须用绑定 `com.azurekiln.qfli.webforge` 的证书和描述文件签名。
HAP 的 Flutter 部分只含 arm64 架构。
工作流在托管机上改写 `build-profile.json5` 副本的签名项。
仓库中的 `ohos/build-profile.json5` 保持不变。
`--no-codesign` 让工具跳过签名项核对。
`flutter build hap` 非零退出即任务失败。
本次运行已产出 HAP 也不例外。
旧运行的 HAP 不能顶替本次构建。
没有新 HAP 时，任务失败。

### Linux

`tar.gz` 含 x86_64 的应用目录。
解压后运行其中的 `qfli_web`。
`deb` 从同一个已核对的目录组装。
`deb` 的依赖是 `libgtk-3-0` 或 `libgtk-3-0t64`，以及 `liblzma5`。
工作流不发布 `rpm`、AppImage 或 Flatpak。
工作流在 Ubuntu 24.04 上构建。
应用在更旧的发行版上可能无法运行。

### Windows

`zip` 含 x86_64 的 Release 目录。
解压后运行其中的 `qfli_web.exe`。
安装程序由官方 Inno Setup 6.7.4 编译。
工作流从官方发布地址下载安装程序，而不是用托管机预装版本。
工作流先核对发布包公布的 SHA-256，再核对 Authenticode 签名与签名者。
两项核对通过后才安装编译器并开始编译。
核对失败或缺少编译器时任务失败，不发布未说明的 EXE。
工作流静默安装安装程序，逐文件比对载荷哈希，然后卸载。
程序没有 Authenticode 签名。
Windows 可能在首次运行时显示安全提示。

### macOS

`dmg` 中的应用只含 arm64 架构。
它不能在 Intel Mac 上运行。
应用使用 ad-hoc 签名。
应用未经 Apple 公证。
Gatekeeper 可能阻止首次打开。
请在系统设置的“隐私与安全性”中允许打开。

## 运行摘要

设置动作记录本次运行的固定输入。
记录内容含仓库提交、Core 标签与提交、Flutter 标签与提交、Dart SDK 和版本标签。
每个已产出的安装包写入一行摘要。
该行列出平台、包名、签名状态、Core 提交、Flutter 提交、原生来源和 SHA-256。
请用摘要核对安装包的来源。
旧运行记录不证明后续源码版本通过。
