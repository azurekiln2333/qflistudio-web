# OHPM `file:` 依赖解析结论, 2026-10-26

只读源码调查。
未执行 OHPM、Hvigor、SDK、native、WSL 或设备。
未修改锁文件与 runner。
对象是 `@ohos/ohpm` 26.0.0.630。

## 偏移口径

OHPM 的 JS 文件压缩成一行。
下列偏移来自 Python `str.find`。
它是解码后的字符索引，不是字节偏移。
这些文件若是纯 ASCII，字符索引等于字节偏移。
本报告未逐一检查这一点。

## 结论

执行 `--module entry --exclusion_project` 时，
新增依赖 `file:./src/main/cpp/types/libqfli_web_cdp_transport`
不单独访问 registry。
判据是类型分派，不是缺少 `--offline` 选项。

## 证据

### 类型分派

- `tools/ohpa/Ohpa.js`：`fromFile(` @1416。
- 它按 `isLocalFile(rawSpec)` 选 File 或 SourceCode。
- `isLocalFile(` @1511 取 `h.isFile`。
- `h.isFile=` @3197 为 `/[.](?:tgz|tar.gz|tar|har)$/i`。
- 我们的 specifier 无归档后缀，故为 SourceCode。
- `parseDependency.js` 只在 `.har` 时改判 File。

### 元数据

- `MetaDataFetcherFactory.js` @419 把 SourceCode 送给
  `SourceCodeMetadataFetcherImpl`。
- 只有 Tag、Range、Version 走 `RegistryMetaDataFetcherImpl`。
- `SourceCodeMetadataFetcherImpl.js` 读本地 `oh-package.json5`。
- 入口是 `readLockPkgFromSourceDir(` @815。
- 它标记 `RegistryType.local` @1416。
- 该文件只取 `RegistryType` 常量，不调用 fetch。

### lock 与缓存

- `InstallationMetadataFetcher.js` 的 `getLockSpec(` @943 查 lock。
- `tryFetchFileResultFromLockPkg(` @2027 要求 lock 条目、mtime 一致
  与内容 hash。
- 未命中就回落 `fetchWithImplementor(` @1586，仍是本地读取。
- 当前 entry lock 无 CDP 条目，故走本地读取。
- lock 写入在 `install.js` @2169 的 `flushAllLockers()`。
- lock 条目来自 `getLockPkgFromMetaData.js`。
- 条目的 `registryType` 保持 local。
- `getPinnedVersion.js` @879 在单版本加 local 或 lock 或 tag 时提前返回。
- 回退函数 `getVersionByDistTags` 只查表，不发请求。

### 安装与链接

- `dep-install/index.js` @817 把 SourceCode 送给
  `installSourceCodeArtifactDep`。
- 该函数 @967 遇 `isLink` 为真即返回，不拷贝。
- `install/common/definitions.js` @231 默认 `link:!0`。
- 链接动作在 `DepNodeSymlinker.js` @2559，函数是 `symLinkDir(...)`。
- 结果形态与现有 `libqfli_nginx_napi.so` 一致。

### 项目根依赖

- `getModuleRootDirs.js` @1297：`exclusion_project` 为真时不加项目根。
- `--module entry` 只加 entry 根。
- 唯一 registry 依赖 `@ohos/hypium 1.0.6` 不进图。

### 其它网络出口

- `DistTags` 只服务 dist-tags 命令。
- `core/cache/index.js` 只服务 cache 命令与 publish。
- `dependency-check` 是独立命令。
- `getAuditRegistry` 无外部调用者。
- `core/audit/*` 无 axios、http 或 net 调用。
- `PackageLockerManager.js` @7537 的 `getRegistryList` 只比较配置前缀。

## 未知

- 运行时是否零出站尚未验证。
- 源码无调用点，但本报告不能证明启动期不发请求。
- `getProxyAgent` 只在 fetch 路径调用。
- 去掉 `--exclusion_project` 或加 `--install_all` 后，
  `@ohos/hypium` 是否联网取决于 lock 与缓存命中，未验证。
- `checkAndReassignResolvedField` 缺 integrity 时二次读取，次数未实测。
- `isNeedChildren` 对 SourceCode 恒为真，故会进入子节点展开。
- types 包无依赖字段，展开为空集。此点已确认。

## 最小验证

1. 纯静态检查：entry 根集合只有 entry。
2. 纯静态检查：entry manifest 只有两个 `file:` 依赖。
3. 另开授权窗口，在无出站网络下执行同一 argv。
4. 事后检查 entry lock 出现 CDP 条目。
5. 该条目的 `registryType` 应为 local。
6. 检查 `entry/oh_modules` 出现同名 junction。
7. 检查 `.ohpm` 三处出现该键。
8. 检查 `registryUrls` 集合不变。
9. 同一窗口开 `log_level=debug`。
10. 检查日志有无 `fetchPackageReal` 行。
11. 反向对照：含 registry 依赖的临时工程应出现该行。
   若对照不出现该行，则日志判据不可信。

- 日志出现该行时，它支持「未拉取 registry」这一判断。
- 日志不出现该行时，它只能支持，不能证明零出站。
- 第 3 至 11 项完成前，门禁保持 BLOCKED。
- 前置缺失是源图不完整。
- 这不等于已证实的网络失败。