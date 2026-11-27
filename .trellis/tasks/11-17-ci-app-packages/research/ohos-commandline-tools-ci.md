# Research: HarmonyOS Command Line Tools for `flutter build hap` on Linux CI

- **Query**: What a `ubuntu-24.04` GitHub Actions job must set up so `flutter build hap --release` works with the OpenHarmony Flutter fork and a self-hosted "Command Line Tools for Linux" archive (layout, env vars, unsigned behaviour, network, prerequisites, community examples).
- **Scope**: mixed (fork source on disk, project files, Huawei documentation, GitHub repositories)
- **Date**: 2026-11-17

Legend: **[V]** = verified from source or documentation (citation given). **[I]** = inferred, not observed.

Nothing in this file was executed on Linux. The Linux archive itself was not downloaded.

Source line numbers refer to the working tree at `D:\ProgramFiles\flutter_ohos`. Its git HEAD is tag `3.27.5-ohos-1.0.1`, but `design.md:43-46` records that the working tree holds the `3.41.10` release. Line numbers can differ in a clean clone of either tag.

---

## Ready-to-use list

`$TOOLS` is the unpacked `command-line-tools` directory. It is the directory that contains `bin/`, `sdk/`, `tool/` and `hvigor/`. The zip has `command-line-tools/` as its single top-level directory, so `TOOLS=<unpack-dir>/command-line-tools`.

### Environment

```bash
# SDK root. The fork reads these two, in this order, after the `ohos-sdk` config key.
export DEVECO_SDK_HOME="$TOOLS/sdk"        # [V] ohos_sdk.dart:296-297
export HOS_SDK_HOME="$TOOLS/sdk"           # [V] ohos_sdk.dart:298-299

# Node bundled in the archive. hvigorw uses $NODE_HOME/bin/node when NODE_HOME is set.
export NODE_HOME="$TOOLS/tool/node"        # [V] variable is read (hvigorw:33-46, hvigor_utils.dart:67-70)
                                           # [I] the path tool/node (see Q1)

# hvigorw and ohpm; node and npm; hdc (optional).
export PATH="$TOOLS/bin:$TOOLS/tool/node/bin:$TOOLS/sdk/default/openharmony/toolchains:$PATH"
                                           # [V] $TOOLS/bin holds hvigorw and ohpm (Huawei doc)
                                           # [V] bare `npm` and bare `hvigorw` are run from PATH (hvigor_utils.dart:208-215, hvigor.dart:97-110)
                                           # [I] node/npm live at $TOOLS/tool/node/bin

# Java. JDK 17 for tools older than 26.0.0, JDK 21 for tools 26.0.0 and newer.
export JAVA_HOME=<JDK 17 or 21>            # [V] Huawei doc ide-command-line-building-app
```

On GitHub Actions these go to `$GITHUB_ENV` and `$GITHUB_PATH`. They must be in effect before `flutter pub get`, not only before the build (see Q2, "pub get").

### One-time setup in the job

```bash
sudo apt-get install -y libgl1-mesa-dev    # [V] Huawei doc; also in ErBWs/setup-ohos README

# hvigor refuses to start without ~/.npmrc.
cat > ~/.npmrc <<'EOF'
registry=https://repo.huaweicloud.com/repository/npm/
@ohos:registry=https://repo.harmonyos.com/npm/
EOF
                                           # [V] fork README.md:137-144, Huawei doc ide-hvigor-faqs

ohpm config set registry https://ohpm.openharmony.cn/ohpm/
ohpm config set strict_ssl false           # [V] both lines from Huawei doc ide-command-line-building-app
```

Not needed:

- `OHOS_BASE_SDK_HOME`, `TOOL_HOME`: the fork does not read them. **[V]** no match in `packages/flutter_tools/lib`.
- `HDC_HOME`, `SIGN_TOOL_HOME`: appear only in message strings (`base/user_messages.dart:198,216`). **[V]**
- `flutter config --ohos-sdk`: it overrides the env vars when set (`ohos_sdk.dart:294-295`). **[V]**
- `mkdir -p build/ohos/hap`: the copy creates its parent (`error_handling_io.dart:299-303`, `createSync(recursive: true)`). **[V]**

### Build command

```bash
flutter build hap --release --no-codesign
```

- Default `--target-platform` is `ohos-arm64`. **[V]** `build_hap.dart:39-44`
- `--no-codesign` skips the signing check that otherwise throws after Hvigor succeeds. **[V]** `build_hap.dart:46-49`, `hvigor.dart:433-435`
- With `signingConfigs: []` and without `--no-codesign`, the command exits non-zero after a successful Hvigor build. **[V]** `hvigor.dart:326-335`

### Expected output

- Hvigor output: `ohos/entry/build/default/outputs/default/entry-default-unsigned.hap` **[V]** `project.dart:1305-1347`
- Copy made by the Flutter tool: `build/ohos/hap/entry-default-unsigned.hap` **[V]** `hvigor.dart:445-453`

### Which archive

A Command Line Tools release of the `6.1.1` line carries API 24. **[V]** for the mapping `6.1.1` = API 24 (Huawei doc uses the string `"6.1.1(24)"`). The community action `ErBWs/setup-ohos` uses build `6.1.1.280` in its README; that this exact build reports `apiVersion 24` is **[I]**. After unpacking, `"$TOOLS/sdk/default/sdk-pkg.json"` field `data.apiVersion` states the real value.

---

## Findings

### Files Found

| File Path | Description |
|---|---|
| `D:\ProgramFiles\flutter_ohos\packages\flutter_tools\lib\src\ohos\ohos_sdk.dart` | SDK discovery, env var names, node path |
| `D:\ProgramFiles\flutter_ohos\packages\flutter_tools\lib\src\ohos\hvigor_utils.dart` | `local.properties` writer, `npm install` of the hvigor plugin |
| `D:\ProgramFiles\flutter_ohos\packages\flutter_tools\lib\src\ohos\hvigor.dart` | hvigorw lookup, `assembleHap`, signing check, copy to `build/ohos/hap` |
| `D:\ProgramFiles\flutter_ohos\packages\flutter_tools\lib\src\commands\build_hap.dart` | `flutter build hap` options |
| `D:\ProgramFiles\flutter_ohos\packages\flutter_tools\lib\src\commands\config.dart` | `--ohos-sdk`, `--ohpm-home` config keys (64-65, 186-191) |
| `D:\ProgramFiles\flutter_ohos\packages\flutter_tools\lib\src\project.dart` | `OhosProject`: output file name, `local.properties` path, pub-get hook |
| `D:\ProgramFiles\flutter_ohos\packages\flutter_tools\lib\src\cache.dart` | OHOS artifact base URL and override variable (562-582) |
| `D:\ProgramFiles\flutter_ohos\packages\flutter_tools\lib\src\flutter_cache.dart` | OHOS artifact list (588-612, 1021-1041) |
| `D:\ProgramFiles\flutter_ohos\packages\flutter_tools\lib\src\base\error_handling_io.dart` | `copySync` creates the destination parent (287-303) |
| `D:\ProgramFiles\flutter_ohos\packages\flutter_tools\lib\src\ohos\ohos_doctor.dart` | doctor probes `ohpm`, `node`, `hvigorw` on PATH (94-130) |
| `D:\ProgramFiles\flutter_ohos\packages\flutter_tools\hvigor\src\plugin\flutter-hvigor-plugin.ts` | Hvigor plugin: reads `flutter.sdk`, ohpm overrides, runs `flutter assemble` |
| `D:\ProgramFiles\flutter_ohos\README.md` | FAQ 6 (`.npmrc`), FAQ 9 (JDK zip64), migration notice |
| `D:\ProgramFiles\Huawei\DevEco Studio\tools\hvigor\bin\hvigorw` | Local hvigorw launcher (node selection) |
| `D:\ProgramFiles\Huawei\DevEco Studio\tools\ohpm\bin\ohpm` | Local ohpm launcher (node selection) |
| `D:\MyNewProjects\qfli_web\ohos\build-profile.json5` | Project profile: SDK versions, signing configs |
| `D:\MyNewProjects\qfli_web\ohos\oh-package.json5` | devDependency `@ohos/hypium 1.0.6` |
| `D:\MyNewProjects\qfli_web\ohos\hvigor\hvigor-config.json5` | modelVersion 5.1.0, empty dependencies |
| `D:\MyNewProjects\qfli_web\ohos\hvigorfile.ts` | imports `flutter-hvigor-plugin` |

### Q1. Archive layout and versions

| Item | Path | Status |
|---|---|---|
| Top-level directory | `command-line-tools/` | **[V]** Huawei doc `ide-commandline-get` |
| `hvigorw`, `ohpm`, `codelinter`, `hstack` | `$TOOLS/bin/` | **[V]** same doc |
| hvigor launcher script | `$TOOLS/hvigor/bin/hvigorw` | **[V]** Huawei doc `ide-command-line-building-app` (node memory note, line 15 of that file) |
| Embedded SDK | `$TOOLS/sdk/default/openharmony`, `$TOOLS/sdk/default/hms` | **[V]** for `openharmony` (doc gives `sdk/default/openharmony/toolchains`); **[I]** for `hms` (fork expects it, local DevEco has it) |
| SDK version file | `$TOOLS/sdk/default/sdk-pkg.json`, field `data.apiVersion` | **[V]** the fork reads this file (`ohos_sdk.dart:338-355`); **[I]** that the Linux archive ships it |
| hdc | `$TOOLS/sdk/default/openharmony/toolchains/hdc` | **[V]** doc sets `HDC_HOME` to that directory |
| hap-sign-tool | `$TOOLS/sdk/default/openharmony/toolchains/lib/hap-sign-tool.jar` | **[V]** same doc |
| node | `$TOOLS/tool/node/bin/node` | **[I]** the fork computes `dirname(sdkPath)/tool/node` on Linux (`ohos_sdk.dart:384-402`) and `<node>/bin/npm` (`ohos_sdk.dart:44-70`) |

Huawei states the SDK is embedded: "HarmonyOS SDK已嵌入命令行工具中，无需额外下载配置". **[V]**

Archive file name pattern: `commandline-tools-linux-x64-<version>.zip`. **[V]** doc example `commandline-tools-linux-x64-5.0.3.XXX.zip`.

Version and API level:

- HarmonyOS `6.1.1` corresponds to API 24. **[V]** Huawei doc `ide-hvigor-build-profile-app` shows the string `"6.1.1(24)"`.
- Local DevEco Studio is `26.0.0.105` with `apiVersion "26"`. **[V]** `D:\ProgramFiles\Huawei\DevEco Studio\sdk\default\sdk-pkg.json`. This install builds the project today.
- The public OpenHarmony SDK used by `.github/workflows/native-ohos-build.yml` is `6.1.0.31`, API 23. It is a different product from the Command Line Tools.

SDK older or newer than `targetSdkVersion`:

- For `runtimeOS: HarmonyOS`, `compileSdkVersion` need not be set. It defaults to the tool's built-in SDK. If set, it must equal the tool's SDK version. `targetSdkVersion` defaults to `compileSdkVersion`. **[V]** Huawei doc `ide-hvigor-build-profile-app`.
- The project sets `targetSdkVersion 6.1.1(24)` and no `compileSdkVersion`.
- Exact Hvigor behaviour when the tool's SDK is older than `targetSdkVersion` could not be determined.
- A newer tool with an older target works locally on Windows (26.0.0 building target 24). **[V]** locally, **[I]** for Linux.

### Q2. What the fork reads

**SDK root, HarmonyOS flavour** (`HmosSdk.localHmosSdk`, `ohos_sdk.dart:291-335`). First present wins; it is an else-if chain:

1. `flutter config` key `ohos-sdk` (294-295)
2. env `DEVECO_SDK_HOME` (296-297)
3. env `HOS_SDK_HOME` (298-299)
4. fallback: `hdc` on PATH, then four parents up (310-322). `<sdk>/default/openharmony/toolchains/hdc` resolves to `<sdk>`.

Validity (338-381): each subdirectory's `sdk-pkg.json` gives `data.apiVersion`. The SDK is valid when the mapped directories exist, or when the API 10 layout (`hmscore` + `openharmony`) exists.

**SDK root, OpenHarmony flavour** (`OhosSdk.localOhosSdk`, `ohos_sdk.dart:126-174`): `ohos-sdk` config, then `OHOS_HOME`, then `OHOS_SDK_HOME`. It needs numeric API directories with `toolchains`. The Command Line Tools layout (`default/`) does not match it. `HarmonySdk.locateHarmonySdk` (86-96) prefers `OhosSdk`, then `HmosSdk`.

Constant names: `ohos_sdk.dart:14-18` (`OHOS_HOME`, `OHOS_SDK_HOME`, `HOS_SDK_HOME`, `DEVECO_SDK_HOME`).

**`ohos/local.properties`** (`hvigor_utils.dart:32-92`; file path from `project.dart:1349`):

| Key | Value | Line |
|---|---|---|
| `hwsdk.dir` | `hmosSdk.sdkPath` | 65 |
| `nodejs.dir` | env `NODE_HOME`, written only when the variable is set | 67-70 |
| `flutter.sdk` | Flutter root | 72 |
| `flutter.versionName` | build name | 80 |
| `flutter.versionCode` | build number | 86 |

When no HarmonyOS SDK is found the function exits with "No Hmos SDK found. Try setting the HOS_SDK_HOME environment variable." (37-39, 110-118).

**hvigorw** (`hvigor.dart:97-110`): `ohos/hvigorw` when that file exists, else bare `hvigorw` from PATH. The project does not track `ohos/hvigorw`.

**npm** (`hvigor_utils.dart:183-216`): when `ohos/hvigorfile.ts` contains `flutter-hvigor-plugin`, the tool rewrites `ohos/package.json` to one `file:` dependency on `<flutterRoot>/packages/flutter_tools/hvigor` and runs bare `npm install` in `ohos/`. The exit code is not checked (208-215).

**ohpm**: the Dart side does not call `ohpm` on this path. Only `OhosDartBuilder` does (`ohos_builder.dart:451,464`), and this project uses the Hvigor plugin path. The `ohpm-home` config key is stored (`config.dart`) but no use was found in the build path.

**node**: the Dart side computes a node path (`ohos_sdk.dart:384-402`) but hvigorw selects node itself. The local launcher uses `$NODE_HOME/bin/node` when `NODE_HOME` is set and fails when that path is invalid; otherwise it uses `node` from PATH (`hvigorw:33-46`). The local ohpm launcher tries `node` on PATH first, then `$NODE_HOME/node`, then `$NODE_HOME/bin/node` (`ohpm:4-26`). That the Linux archive's launchers are identical is **[I]**.

**pub get**: `OhosProject.ensureReadyForPlatformSpecificTooling` (`project.dart:1362-1376`) calls `updateLocalProperties` and `installHvigorPlugin`. A `flutter pub get` in a project with `ohos/` therefore needs the SDK env vars and `npm` on PATH. **[V]** The OHOS feature is on by default (`features.dart:156-171`, config key `enable-ohos`).

**Build sequence** (`hvigor.dart:388-461`): install plugin, update `local.properties`, assemble HSPs, `hvigorw assembleHap -p product=<flavor> -p buildMode=<mode> --no-daemon` plus `-p FLUTTER_TARGET=...`, `-p TARGET_PLATFORM=...` (140-164, 715-749).

**Hvigor plugin** (`flutter-hvigor-plugin.ts`): reads `flutter.sdk` from `ohos/local.properties` (55-56). It sets ohpm overrides for `@ohos/flutter_ohos` and `flutter_native_<arch>` to `.har` files under `<flutter.sdk>/bin/cache/artifacts/engine/<platform>-release/` (152-173). It runs `<flutter.sdk>/bin/flutter --quiet assemble ... ohos_aot_bundle_release_<platform>` through `execSync` (251-357).

### Q3. Empty `signingConfigs`

Spec line under review: `.trellis/spec/backend/release-verification.md:65` — "OHOS Hvigor succeeds but no signature | Report unsigned build separately; Flutter wrapper may exit 1".

The line is correct for the default flags. **[V]**

Sequence after Hvigor returns (`hvigor.dart:429-453`):

1. Non-zero Hvigor exit gives a ToolExit (429-431).
2. `if (shouldCodesign) checkOhosSignedInfo` (433-435).
3. `checkOhosSignedInfo` (326-335): when `app.signingConfigs` is a List and is empty, it calls `throwToolExit` with the message "请通过DevEco Studio打开ohos工程后配置调试签名(...)". The process exits non-zero.
4. `getSignedFile(throwOnMissing: true)` (438-444).
5. Copy to `build/ohos/hap/<basename>` (445-453).

| Case | Result | Status |
|---|---|---|
| `signingConfigs: []`, default `--codesign` | Hvigor builds `entry-default-unsigned.hap`. The tool then throws at step 3. No copy to `build/ohos/hap`. | **[V]** |
| `signingConfigs: []`, `--no-codesign` | Step 3 is skipped. The tool expects `entry-default-unsigned.hap`, copies it, exits 0. | **[V]** from source; exit 0 not observed |
| `signingConfigs` key absent, default `--codesign` | Step 3 passes (not a List). Step 4 fails: "Hvigor build failed to produce an hap file..." because it looks for `-signed.hap`. | **[V]** |
| Committed profile unchanged | `signingConfigs` holds two entries with absolute Windows paths. Those files do not exist on Linux. The Hvigor failure mode was not determined. | — |

File name rule (`project.dart:1305-1347`): `<module>/build/<flavor>/outputs/<flavor>/<moduleName>-<flavor>-<signed|unsigned>.hap`, unless the module profile sets `targets[].output.artifactName` (1445-1460). `ohos/entry/build-profile.json5` sets none.

`--no-codesign` prints a warning (`build_hap.dart:80-86`).

Huawei doc `ide-hvigor-build-profile-app` on `products[].signingConfig`: "如果没有配置，默认不签名". **[V]** With signing configured and files present, Hvigor produces both `xxx-signed.hap` and `xxx-unsigned.hap`. **[V]** `ide-command-line-building-app`.

`design.md:93-98` plans `signingConfigs: []`, plain `flutter build hap --release`, and tolerance of exit 1 when a fresh `*-unsigned.hap` exists. Per the table, that path ends at step 3 and leaves no file under `build/ohos/hap`.

### Q4. Network at build time

| What | Endpoint | Configured by | Status |
|---|---|---|---|
| Flutter OHOS engine artifacts (`ohos-arm64{,-profile,-release}/artifacts.zip`, gen_snapshot `ohos-arm64-release/linux-x64.zip`) | `https://flutter-ohos.obs.cn-south-1.myhuaweicloud.com/flutter_infra_release/flutter/<engine version>/...` | env `FLUTTER_OHOS_STORAGE_BASE_URL` overrides the base | **[V]** `cache.dart:562-582,1015-1036`, `flutter_cache.dart:588-612,1021-1041` |
| Pub packages | pub host in use | `PUB_HOSTED_URL` | standard |
| ohpm packages: `@ohos/hypium 1.0.6` | `https://ohpm.openharmony.cn/ohpm/` | `ohpm config set registry`, or `~/.ohpm/.ohpmrc` | **[V]** registry URL from Huawei doc and local `.ohpmrc`; the package URL returned HTTP 200 from this Windows machine |
| hvigor npm packages (and pnpm) | `https://repo.huaweicloud.com/repository/npm/`, scope `@ohos` at `https://repo.harmonyos.com/npm/` | `~/.npmrc` | **[V]** fork README FAQ 6, Huawei doc |
| `flutter-hvigor-plugin` | local `file:` dependency; its own devDependency is `@ohos/hvigor 5.2.2` | `ohos/package.json` (generated) | **[V]** `hvigor_utils.dart:183-216`, `hvigor/package.json` |
| `flutter.har` / embedding | local file from the Flutter cache via ohpm overrides | — | **[V]** `flutter-hvigor-plugin.ts:152-173` |

- The repository has no `.npmrc` and no `.ohpmrc`. **[V]**
- A missing `~/.npmrc` gives "Error: The hvigor depends on the npmrc file. Configure the npmrc file first." **[V]** fork `README.md:137`, Huawei doc `ide-hvigor-faqs`.
- Huawei's pipeline doc runs `ohpm install --all` before the build. **[V]** Whether Hvigor runs the ohpm install itself on the plugin path is **[I]**; the Dart side does not.
- Huawei's offline section mentions pnpm `10.28.2` under `~/.hvigor/wrapper/tools/`. **[V]**
- Reachability of these endpoints from GitHub-hosted runners was not tested.

### Q5. Linux prerequisites

| Requirement | Value | Status |
|---|---|---|
| OS | Linux 64-bit, GLIBC 2.28 or newer | **[V]** Huawei doc `ide-command-line-building-app` |
| RAM | 8 GB minimum, 16 GB recommended | **[V]** same doc |
| Java | JDK 17 for tools older than 26.0.0; JDK 21 for 26.0.0 and newer | **[V]** same doc |
| Java zip64 | `Invalid CEN header (invalid zip64 extra data field size)` is tied to JDK-8313765 | **[V]** fork `README.md:162` |
| OpenGL | `apt install -y libgl1-mesa-dev`, needed for texture compression | **[V]** same doc |
| Node | hvigorw honours `NODE_HOME`, else PATH | **[V]** launcher script |
| Node memory | line 15 of `command-line-tools/hvigor/bin/hvigorw`, `NODE_OPTS="--max-old-space-size=..."` | **[V]** doc and local script |
| Project path | no directory whose name starts with a dot | **[V]** same doc |
| File names | Linux is case sensitive (`caseSensitiveCheck`) | **[V]** same doc |
| Daemon | `--no-daemon` recommended for CI; the fork already passes it | **[V]** doc `ide-hvigor-commandline`, `hvigor.dart:140-164` |

Whether the runner's own Node conflicts with the bundled Node was not determined. The bundled Node version was not determined. With `NODE_HOME` set, hvigorw ignores PATH for node. ohpm tries PATH `node` first.

### Q6. Community examples

| Repository | What it is | Read |
|---|---|---|
| `ErBWs/setup-ohos` (GitHub, 13 stars) | Composite action plus `setup.sh` | README only |
| `ErBWs/ohos-sdk` | Hosts tool archives as releases for the action | not read |
| `DaLongZhuaZi/harmonyos-ci` | Docker images for API 23 and 26; has `.github/scripts/strip_signing.py`, `.github/workflows/build.yml`, `docker/harmonyos-ci.Dockerfile`, `docs/CI_Guide.md` | file list only |
| `springtwr/harmonyos-clt` | Dockerfile | file list only |

`ErBWs/setup-ohos` README, **[V]**:

```yaml
- uses: ErBWs/setup-ohos@v2
  with:
    version: 6.1.1.280
    cache: true
```

- Installs to `~/ohos-sdk`.
- Sets `HOS_SDK_HOME=/home/runner/ohos-sdk/command-line-tools/sdk`.
- Sets `OHOS_NDK_HOME=/home/runner/ohos-sdk/command-line-tools/sdk/default/openharmony`.
- Lists `sudo apt-get install -y libgl1-mesa-dev` as a dependency.
- Outputs `sdk-version` and `api-version`.

This matches `$TOOLS/sdk` as the SDK root and `command-line-tools/` as the top-level directory.

No public workflow that runs `flutter build hap` on a Linux runner was read end to end.

### External References

- [命令行工具获取 (ide-commandline-get)](https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/ide-commandline-get) — archive layout, PATH line, embedded SDK
- [搭建流水线 (ide-command-line-building-app)](https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/ide-command-line-building-app) — Linux prerequisites, JDK, registries, `libgl1-mesa-dev`, output paths, hap-sign-tool path
- [hvigorw 命令行 (ide-hvigor-commandline)](https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/ide-hvigor-commandline) — `--no-daemon`, `--node-home`
- [工程级 build-profile.json5 (ide-hvigor-build-profile-app)](https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/ide-hvigor-build-profile-app) — `signingConfig` default, SDK version rules, `"6.1.1(24)"`
- [Hvigor FAQ (ide-hvigor-faqs)](https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/ide-hvigor-faqs) — `.npmrc` error
- [ErBWs/setup-ohos](https://github.com/ErBWs/setup-ohos) — community action
- [DaLongZhuaZi/harmonyos-ci](https://github.com/DaLongZhuaZi/harmonyos-ci), [springtwr/harmonyos-clt](https://github.com/springtwr/harmonyos-clt) — community Docker images
- [Flutter OH 环境搭建指导](https://gitcode.com/openharmony-tpc/flutter_samples/blob/master/ohos/docs/03_environment/OpenHarmony-flutter%E7%8E%AF%E5%A2%83%E6%90%AD%E5%BB%BA%E6%8C%87%E5%AF%BC.md) — linked from the fork README; not fetched

Huawei pages were read through the document API, not the rendered pages.

### Related Specs

- `.trellis/spec/backend/release-verification.md:35-36` — current OHOS artifact directory; old `build/ohos/hap/*signed.hap` is not proof
- `.trellis/spec/backend/release-verification.md:51-53` — builder defaults to arm64
- `.trellis/spec/backend/release-verification.md:65` — unsigned build may exit 1 (confirmed for default flags, see Q3)
- `.trellis/spec/backend/native-runtime.md:164`
- `.trellis/tasks/11-17-ci-app-packages/design.md:70,87-99` — OHOS job design
- `.trellis/tasks/11-17-ci-app-packages/research/flutter-fork-ci-artifacts.md` — Flutter ref selection

## Caveats / Not Found

- **Fork version.** `design.md` pins `3.41.10-ohos-1.0.0`. The original query named `3.27.5-ohos-1.0.1`. All source citations come from the local working tree, which `design.md` says holds 3.41.10 content. A clean clone of `3.27.5-ohos-1.0.1` was not compared.
- **Fork location.** The fork README states the repositories moved to the `CPF-Flutter` organisation (`https://gitcode.com/CPF-Flutter/flutter_flutter`) and the old repository is no longer maintained (`README.md:4`). `design.md:51` clones from `openharmony-tpc/flutter_flutter`.
- **Archive not inspected.** The Linux zip was not downloaded. The layout comes from Huawei documentation, the fork's Linux path logic, the local Windows DevEco install and one community README. `tool/node`, `sdk/default/hms` and `sdk/default/sdk-pkg.json` are inferred for Linux.
- **API 24 build number.** Only the `6.1.1` = API 24 mapping is documented. No official list mapping tool build numbers to API levels was found.
- **SDK older than target.** The exact Hvigor result was not determined.
- **Committed signing configs.** `ohos/build-profile.json5` at HEAD has non-empty `signingConfigs` with Windows absolute paths. Behaviour on Linux without stripping was not determined.
- **Exit code with `--no-codesign`.** Read from source only. Not run.
- **Runner network.** Access from GitHub-hosted runners to `ohpm.openharmony.cn`, `repo.huaweicloud.com`, `repo.harmonyos.com`, `flutter-ohos.obs.cn-south-1.myhuaweicloud.com` and `gitcode.com` was not tested.
- **Bundled Node version** and any conflict with the runner's Node: not determined.
- **Hvigor auto-install of ohpm dependencies** on the plugin path: inferred.
- **Community scripts.** `setup.sh` of `ErBWs/setup-ohos`, the `ErBWs/ohos-sdk` release list, and the Dockerfiles and workflow of `DaLongZhuaZi/harmonyos-ci` and `springtwr/harmonyos-clt` were not fetched. The shell tool was unavailable for the last part of this session.
- **Linux launchers.** `hvigorw` and `ohpm` launcher behaviour was read from the Windows DevEco install's POSIX scripts.
