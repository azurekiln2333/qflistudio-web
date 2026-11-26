# Research: flutter-fork-ci-artifacts

- **Query**: Can a fresh clone of the OpenHarmony Flutter fork (`gitcode.com/openharmony-tpc/flutter_flutter`, tag `3.27.5-ohos-1.0.1`) fetch its Dart SDK and engine artifacts for Android, iOS, Linux, Windows, macOS and OHOS on clean GitHub-hosted runners?
- **Scope**: mixed (local read-only inspection of `D:\ProgramFiles\flutter_ohos` + HTTP probes of the real artifact URLs)
- **Date**: 2026-11-17

## Headline finding (read first)

**The local install is not tag `3.27.5-ohos-1.0.1`.** Its `.git` HEAD points at that tag, but the working tree holds the files of release **`3.41.10-ohos-1.0.0`** (called "3.41.9-ohos-1.0.0" in its own release note). A clean clone of tag `3.27.5-ohos-1.0.1` yields a different SDK: Dart **3.6.2**, not 3.11.5.

This project's `pubspec.yaml` line 7 declares `sdk: ^3.11.5`. So with the tag named in the task:

- Artifact download: works for every target (all URLs return 200, see below).
- `flutter pub get`: expected to fail on SDK constraint, on every target (inferred from the constraint and the verified Dart version; not executed).

The ref that reproduces the local install is tag **`3.41.10-ohos-1.0.0`** in the same repository. Its three version files match the local working tree exactly, and all its artifact URLs also return 200. The annotated tag object is `0337f5378a33614354edde7d8ae8473be5994572`. Its peeled commit is `244a0e8abb3085e8675589b13e219af8c41cb7aa`, confirmed against both the upstream peeled ref and GitHub Actions run 45850614959. Pin the peeled commit when comparing a checkout's HEAD.

## Per-target verdict

"Fetch" = every URL the tool constructs for that target answered HTTP 200 to an anonymous HEAD request from this machine. Hosts differ per column because the tool filters artifacts by host OS.

| Target | Host runner | Fetch at tag `3.27.5-ohos-1.0.1` | Fetch at tag `3.41.10-ohos-1.0.0` | Evidence |
|---|---|---|---|---|
| Dart SDK + tool bootstrap | ubuntu-24.04 (linux-x64) | yes | yes | `dart-sdk-linux-x64.zip` 200 on OHOS bucket |
| Dart SDK + tool bootstrap | windows-2022 (windows-x64) | yes | yes | `dart-sdk-windows-x64.zip` 200 |
| Dart SDK + tool bootstrap | macos-15 (darwin-arm64) | yes | yes | `dart-sdk-darwin-arm64.zip` 200 |
| Android (arm, arm64, x64 release) | linux | yes | yes | gen_snapshot `android-*-release/linux-x64.zip` 200; Maven POMs on `download.flutter.io` 200 |
| iOS release | macos | yes | yes | `ios-release/artifacts.zip` 200 (also `ios`, `ios-profile`) |
| Linux x64 release | linux | yes | yes | `linux-x64-release/linux-x64-flutter-gtk.zip` 200 (+debug, profile) |
| Windows x64 release | windows | yes | yes | `windows-x64-release/windows-x64-flutter.zip` 200 (+debug, profile, cpp wrapper) |
| macOS release | macos | yes | yes | `darwin-x64-release/{framework,artifacts,gen_snapshot}.zip` 200 (+debug, profile) |
| OHOS (arm64, x64) | linux / windows / macos | yes | yes | `ohos-*-{profile,release}/{linux,windows,darwin}-x64.zip` 200; HAR `ohos-*/artifacts.zip` 200 |
| **Project resolves (`pub get`)** | all | **no (inferred)** | yes (inferred) | pubspec `sdk: ^3.11.5`; tag SDK zip contains Dart 3.6.2; 3.41.10 SDK zip contains Dart 3.11.5 |

No 404 was returned for any needed artifact in either revision set. The only 404 was `dart-sdk-windows-arm64.zip` at the 3.27 tag, which is only requested on Windows-on-ARM hosts.

Unknown, not verifiable from this machine:

- Reachability and throughput of `gitcode.com` and `flutter-ohos.obs.cn-south-1.myhuaweicloud.com` from GitHub's runner networks. The probes show anonymous public HTTPS access with no credentials. They do not show how GitHub's network performs against these hosts.
- Whether the OHOS toolchain (DevEco command-line-tools: OHOS SDK, hvigor, ohpm, node) can be fetched on a runner. It is not part of the fork's cache. The README points to `developer.huawei.com` for it.

## Verified facts

### V1. Local working tree does not match its HEAD (file reads + read-only git)

- `git log -1`: HEAD = `12587c79e88aacf3172a84e536f226457d037594`, tag `3.27.5-ohos-1.0.1`.
- `git reflog`: only two entries — clone, then `checkout: moving from br_3.22.0-ohos-1.0.4 to 3.27.5-ohos-1.0.1`.
- `git status --short`: 7863 modified tracked files, 643 untracked (for example `DEPS`, `DEPS_ohos`, `engine/`, `bin/internal/content_aware_hash.sh`, `update_engine_version.sh`).
- Version files, HEAD versus working tree:

| File | At HEAD (the tag) | Working tree |
|---|---|---|
| `bin/internal/engine.version` | `e672b006cb34c921db85b8e2f482ed3144a4574b` | `42d3d75a56efe1a2e9902f52dc8006099c45d937` |
| `bin/internal/engine.ohos.version` | `9715615d6dd8204da2cbc77ce61053312d723621` | `ab1841593ed352873a3d26cb41e942e90b813be0` |
| `bin/internal/engine.ohos.har.version` | `61e44f02e062e66d68b773ca654a6428648e5027` | `97a3efd6c9de0776f78f93c265f49491aa5d1089` |
| `packages/flutter/pubspec.yaml` sdk | `>=3.3.0-0 <4.0.0` | `^3.9.0-0` |
| `README.en.md` base version | Flutter 3.27.4 | Flutter 3.41.9 |

- The tool reports `3.27.5-ohos-1.0.1` because it derives the version from the git tag, while engine revision and Dart version come from the working-tree files. This explains the "3.27 framework with Dart 3.11.5 and a 2026 engine" oddity.
- Working-tree `release-notes/Flutter 3.41.9-ohos 1.0.0 ReleaseNote.md` line 65: SDK `3.41.9-ohos-1.0.0`, displayed as `3.41.10-ohos-1.0.0` because of the version parsing rule.

### V2. Which remote ref matches the local tree (raw file fetches from gitcode)

`https://raw.gitcode.com/openharmony-tpc/flutter_flutter/raw/<ref>/bin/internal/<file>`:

| Ref | engine.version | engine.ohos.version | engine.ohos.har.version | Matches local |
|---|---|---|---|---|
| `3.41.10-ohos-1.0.0` | 42d3d75a… | ab184159… | 97a3efd6… | **yes, all three** |
| `3.41.10-ohos-1.0.1` | 42d3d75a… | 3fb08d34… | 3fb08d34… | no |
| `3.41.9+ohos-1.0.2` | 42d3d75a… | 4cbeea6a… | 4cbeea6a… | no |
| `3.41.9+ohos-1.0.4-beta` | 42d3d75a… | 84a3a1fb… | f04bb0fc… | no |
| branch `oh-3.41.9-release` | 42d3d75a… | c9424ec9… | 8ef880dd… | no |
| branch `oh-3.41.9-dev` | 42d3d75a… | 84a3a1fb… | 5f2a9671… | no |

`git ls-remote --tags` confirms both `refs/tags/3.27.5-ohos-1.0.1` (12587c79…) and `refs/tags/3.41.10-ohos-1.0.0` (0337f537…) exist on `https://gitcode.com/openharmony-tpc/flutter_flutter.git`. Newer 3.27 tags also exist (`3.27.5-ohos-1.0.2` … `1.0.8`). `info/refs?service=git-upload-pack` answers 200 anonymously.

### V3. Dart version inside the SDK zips (read `dart-sdk/version` via HTTP range requests)

| Zip | Dart version |
|---|---|
| OHOS bucket `9715615d…/dart-sdk-linux-x64.zip` (tag 3.27.5-ohos-1.0.1) | 3.6.2 |
| OHOS bucket `ab184159…/dart-sdk-linux-x64.zip` (3.41.10-ohos-1.0.0, = local) | 3.11.5 |
| OHOS bucket `3fb08d34…` (3.41.10-ohos-1.0.1) | 3.11.5 |
| OHOS bucket `4cbeea6a…` (3.41.9+ohos-1.0.2) | 3.11.5 |
| Google bucket `e672b006…` | 3.6.1 |
| Google bucket `42d3d75a…` | 3.11.5 |

### V4. Where artifacts come from (same design in both revisions)

Two buckets are used at the same time. Paths are identical on every host OS; only the file names differ by host.

1. **OHOS bucket**, default `https://flutter-ohos.obs.cn-south-1.myhuaweicloud.com`, override variable `FLUTTER_OHOS_STORAGE_BASE_URL`:
   - Dart SDK: `<base>/flutter_infra_release/flutter/<engine.ohos.version>/dart-sdk-<os>-<arch>.zip`
     - tag: `bin/internal/update_dart_sdk.sh` lines 19-20, 128-129; `update_dart_sdk.ps1` lines 23, 45-53, 70; `shared.bat` line 24.
     - 3.41 tree: `update_dart_sdk.sh` reads `bin/cache/engine.ohos.stamp`, written by `update_engine_version.sh` from `bin/internal/engine.ohos.version`.
   - `sky_engine.zip`, `flutter_patched_sdk.zip`, `flutter_patched_sdk_product.zip` (`cache.dart` `updateInner`, tag lines 968-989).
   - `flutter-web-sdk.zip` (`flutter_cache.dart`, `FlutterWebSdk`).
   - Host tools `FlutterSdkOhos`: `linux-x64/artifacts.zip`, `windows-x64/artifacts.zip`, `darwin-<arch>/artifacts.zip`.
   - OHOS gen_snapshot `OHOSGenSnapshotArtifacts`: `ohos-{arm64,x64}-{profile,release}/{linux,windows,darwin}-x64.zip`.
   - OHOS HARs `OHOSInternalBuildArtifacts`: `<base>/flutter_infra_release/flutter/<engine.ohos.har.version>/ohos-{arm64,x64}[-profile|-release]/artifacts.zip`.
2. **Google bucket**, default `https://storage.googleapis.com`, override variable `FLUTTER_STORAGE_BASE_URL`, version `<engine.version>`:
   - `flutter_gpu.zip`, `font-subset.zip`, Android gen_snapshot and embedding, iOS, Linux, Windows, macOS engine artifacts, `ios-usb-dependencies`, gradle wrapper, material fonts.
   - Android Maven: `https://storage.googleapis.com/download.flutter.io/io/flutter/<artifact>/1.0.0-<engine.version>/…`.

`FLUTTER_STORAGE_BASE_URL` does not redirect OHOS-bucket downloads, and `FLUTTER_OHOS_STORAGE_BASE_URL` does not redirect Google-bucket downloads (`cache.dart` tag lines 487-535). Neither variable is required: with both unset, the defaults are the two hosts above. `bin/internal/engine.realm` is empty in both revisions, so no realm path segment is added.

The Dart SDK always comes from the OHOS bucket, never from Google, on all three host OSes.

### V5. HTTP probes (anonymous `curl -I -L`, all from this machine, 2026-11-17)

Abbreviations: `O27` = `https://flutter-ohos.obs.cn-south-1.myhuaweicloud.com/flutter_infra_release/flutter/9715615d6dd8204da2cbc77ce61053312d723621`, `H27` = same host `/61e44f02e062e66d68b773ca654a6428648e5027`, `G27` = `https://storage.googleapis.com/flutter_infra_release/flutter/e672b006cb34c921db85b8e2f482ed3144a4574b`.
`O41` = OHOS host `/ab1841593ed352873a3d26cb41e942e90b813be0`, `H41` = OHOS host `/97a3efd6c9de0776f78f93c265f49491aa5d1089`, `G41` = Google `/42d3d75a56efe1a2e9902f52dc8006099c45d937`.

| Path under base | Tag 3.27.5-ohos-1.0.1 | 3.41.10-ohos-1.0.0 |
|---|---|---|
| `O/dart-sdk-linux-x64.zip` | 200 (210952699 B) | 200 (203042184 B) |
| `O/dart-sdk-windows-x64.zip` | 200 (227435108 B) | 200 (199105903 B) |
| `O/dart-sdk-darwin-arm64.zip` | 200 (210875649 B) | 200 (202329561 B) |
| `O/dart-sdk-darwin-x64.zip` | 200 | 200 |
| `O/dart-sdk-windows-arm64.zip` | 404 (not needed on x64) | not probed |
| `O/sky_engine.zip` | 200 | 200 |
| `O/flutter_patched_sdk.zip`, `O/flutter_patched_sdk_product.zip` | 200, 200 | 200, 200 |
| `O/flutter-web-sdk.zip` | 200 | 200 |
| `O/linux-x64/artifacts.zip` | 200 | 200 |
| `O/windows-x64/artifacts.zip` | 200 | 200 |
| `O/darwin-arm64/artifacts.zip`, `O/darwin-x64/artifacts.zip` | 200, 200 | 200, 200 |
| `O/ohos-arm64-profile/{linux,windows,darwin}-x64.zip` | 200 x3 | 200 x3 |
| `O/ohos-arm64-release/{linux,windows,darwin}-x64.zip` | 200 x3 | 200 x3 |
| `O/ohos-x64-profile/{linux,windows,darwin}-x64.zip` | 200 x3 | 200 x3 |
| `O/ohos-x64-release/{linux,windows,darwin}-x64.zip` | 200 x3 | 200 x3 |
| `H/ohos-arm64/artifacts.zip`, `-profile`, `-release` | 200 x3 | 200 x3 |
| `H/ohos-x64/artifacts.zip`, `-profile`, `-release` | 200 x3 | 200 x3 |
| `G/flutter_gpu.zip` | 200 | 200 |
| `G/engine_stamp.json` | not used by this revision | 200 |
| `G/{linux-x64,windows-x64,darwin-arm64}/font-subset.zip` | 200 x3 | 200 x3 |
| `G/android-{arm,arm64,x64}-release/linux-x64.zip` | 200 x3 | 200 x3 |
| `G/android-{arm,arm64,x64}-profile/linux-x64.zip` | 200 (arm probed) | 200 x3 |
| `G/android-arm64-release/windows-x64.zip` | 200 | not probed |
| `G/android-*-{profile,release}/darwin-x64.zip` | 200 (arm64-release probed) | 200 x6 |
| `G/android-{arm,arm64,x64}-release/artifacts.zip` | 200 x3 | 200 x3 |
| `G/ios/artifacts.zip`, `ios-profile`, `ios-release` | 200 x3 | 200 x3 |
| `G/linux-x64-{debug,profile,release}/linux-x64-flutter-gtk.zip` | 200 x3 | 200 x3 |
| `G/windows-x64-{debug,profile,release}/windows-x64-flutter.zip` | 200 x3 | 200 x3 |
| `G/windows-x64/flutter-cpp-client-wrapper.zip` | 200 | 200 |
| `G/darwin-x64/{framework,gen_snapshot}.zip` | 200 x2 | 200 x2 |
| `G/darwin-x64-profile/{framework,artifacts,gen_snapshot}.zip` | 200 x3 | 200 x3 |
| `G/darwin-x64-release/{framework,artifacts,gen_snapshot}.zip` | 200 x3 | 200 x3 |
| Maven POM `flutter_embedding_release`, `arm64_v8a_release`, `armeabi_v7a_release`, `x86_64_release` at `1.0.0-<engine.version>` | 200 x4 | 200 x4 |

Not probed in either set: gradle wrapper, material fonts, `ios-usb-dependencies` (these are upstream Google-bucket artifacts unrelated to the fork's engine revisions).

### V6. Local `bin/cache` contents

- `bin/cache/artifacts/engine/` contains: `android-{arm,arm64,x64}-{profile,release}/windows-x64` (gen_snapshot.exe), `common`, `ohos-{arm64,x64}[-profile|-release]` (HARs and `windows-x64/gen_snapshot.exe`), `windows-x64[-profile|-release]`.
- It contains no `linux-*`, `darwin-*` or `ios*` directories. This is consistent with host filtering on a Windows machine (`_platform.isLinux` / `isMacOS` guards in `flutter_cache.dart`), so the local cache gives no evidence either way for Linux, macOS or iOS.
- Stamps: `engine.stamp` and `windows-sdk.stamp`, `android-sdk.stamp` = `42d3d75a…`; `engine-dart-sdk.stamp`, `flutter_sdk_ohos.stamp`, `ohos-sdk.stamp` = `ab184159…`; `ohos-internal-build-artifacts.stamp` = `97a3efd6…`. `dart-sdk/version` = 3.11.5.
- Signs of hand population:
  - The working tree was replaced without a git operation (V1). Git has no object for any 3.41 commit (`git cat-file -t 62357a93…` fails).
  - Mixed dates: directories under `artifacts/engine/ohos-*` and the `gradle_wrapper`, `ios-deploy`, `material_fonts`, `usbmuxd` stamps date from 2025-12-30, while Dart SDK, tool snapshot and engine files date from 2026-09-01/02. The cache was reused across the tree replacement, not recreated.
  - `bin/cache/downloads/storage.googleapis.com/flutter_infra_release/flutter/e69de29bb2d1d6434b8b29ae775ad8c2e48c5391` exists. `e69de29b…` is git's hash of an empty blob, so at least one run resolved the engine version to an empty-content hash.
  - `flutter.version.json` reports `"channel": "[user-branch]"`, `"repositoryUrl": "unknown source"`.
- The engine files themselves carry coherent download-time stamps (2026-09-02 00:22-00:28) and match the URL layout in V4. Nothing shows the artifact files were copied in by hand; the evidence of manual work concerns the source tree.

### V7. Build commands and feature flags

- Both revisions ship `build_apk`, `build_appbundle`, `build_ios`, `build_linux`, `build_macos`, `build_windows`, `build_hap`, `build_har`, `build_hsp` under `packages/flutter_tools/lib/src/commands/`.
- `features.dart` (tag lines 96-144; working tree lines 135-183): `flutterLinuxDesktopFeature`, `flutterMacOSDesktopFeature`, `flutterWindowsDesktopFeature`, `flutterAndroidFeature`, `flutterIOSFeature` are `Feature.fullyEnabled`. `flutterOhosFeature` is `enabledByDefault: true` on master, beta and stable.
- No `flutter config --enable-*-desktop` call is needed. (Read from source; the commands were not executed on Linux or macOS.)

### V8. README / release-note statements

Tag `3.27.5-ohos-1.0.1` `README.en.md`:

- "Flutter Tools commands are currently supported on Linux, Mac and Windows."
- `PUB_HOSTED_URL=https://pub.flutter-io.cn` and `FLUTTER_STORAGE_BASE_URL=https://storage.flutter-io.cn` appear under the comment "Domestic mirror". `PUB_CACHE` is shown as a custom path example.
- OHOS toolchain: API 18, DevEco Studio 5.1 or command-line-tools 5.1, Java 17, and `TOOL_HOME`, `DEVECO_SDK_HOME`, plus `ohpm`, `hvigor`, `node` on `PATH`.
- Common Problem 1: after changing `FLUTTER_STORAGE_BASE_URL`, delete `<flutter>/bin/cache`.
- Common Problem 12: `flutter build hap` needs no `--local-engine`; artifacts come from the cloud.
- The README never mentions `FLUTTER_OHOS_STORAGE_BASE_URL`; it exists only in the scripts and `cache.dart`.
- No statement about git mirror settings.

3.41 working tree: release note lists minimum application build API **OpenHarmony API 20**, recommended API 23. `ohos_sdk.dart` lines 15-18 reads `OHOS_SDK_HOME`, `HOS_SDK_HOME`, `DEVECO_SDK_HOME`.

## Environment and setup for the workflow

Substantiated by the findings above. Choice of ref is the open decision.

```sh
# Ref: the task names 3.27.5-ohos-1.0.1 (Dart 3.6.2).
# The ref equal to the local install is 3.41.10-ohos-1.0.0 (Dart 3.11.5).
git clone --branch <ref> https://gitcode.com/openharmony-tpc/flutter_flutter.git "$FLUTTER_ROOT"
export PATH="$FLUTTER_ROOT/bin:$PATH"
flutter --version        # triggers Dart SDK download from the OHOS bucket and builds the tool
flutter precache --<platform>   # android | ios | linux | windows | macos | ohos (not executed in this research)
```

Environment variables:

| Variable | Value for GitHub runners | Basis |
|---|---|---|
| `FLUTTER_STORAGE_BASE_URL` | leave unset (default `https://storage.googleapis.com`) | verified default in `cache.dart`; README labels the alternative as a domestic mirror |
| `FLUTTER_OHOS_STORAGE_BASE_URL` | leave unset (default Huawei OBS bucket) | verified default in scripts and `cache.dart`; no other host for these files was found |
| `PUB_HOSTED_URL` | leave unset (default pub.dev) | README labels `pub.flutter-io.cn` as a domestic mirror |
| `PUB_CACHE` | optional | README shows it as a custom path only |
| `FLUTTER_REALM`, `FLUTTER_PREBUILT_ENGINE_VERSION` | leave unset | 3.41 `update_engine_version.sh`: if set, they override the pinned engine version and realm |
| `DEVECO_SDK_HOME` (or `OHOS_SDK_HOME` / `HOS_SDK_HOME`), `ohpm`/`hvigor`/`node` on `PATH`, Java 17 | required for the OHOS job only | README; `ohos_sdk.dart` lines 15-18 |

Host prerequisites read from the scripts: `git`, `curl`, `unzip` on Linux and macOS (`update_dart_sdk.sh`); PowerShell on Windows (`update_dart_sdk.ps1`, uses BITS then `Invoke-WebRequest`).

## Verified versus inferred

Verified by request or file read: everything in V1-V8, including every HTTP status in V5 and every Dart version in V3.

Inferred, not executed:

- `flutter pub get` fails at tag `3.27.5-ohos-1.0.1` because Dart 3.6.2 does not satisfy `^3.11.5`.
- A clean clone of `3.41.10-ohos-1.0.0` behaves like the local install. Basis: three matching version files and the release note. The full trees were not diffed, because the local clone has no 3.41 git objects.
- A shallow clone (`--depth 1`) still resolves the version from the tag. Not tested.
- Download behaviour from GitHub runner networks equals behaviour from this machine.
- `flutter precache` / `flutter build` succeed on Linux and macOS. Only URL existence and source were checked.

## Workaround for the non-buildable case

The only non-buildable case found is "project requires Dart ^3.11.5, tag ships Dart 3.6.2". Smallest substantiated workaround: clone tag `3.41.10-ohos-1.0.0` from the same repository instead of `3.27.5-ohos-1.0.1`. It is the revision the local machine has actually been building with, and all its artifacts were probed with status 200.

No artifact-level workaround is needed: no required artifact returned 404.

## Files Found

| File Path | Description |
|---|---|
| `D:\ProgramFiles\flutter_ohos\bin\internal\engine.version` | Google-bucket engine revision |
| `D:\ProgramFiles\flutter_ohos\bin\internal\engine.ohos.version` | OHOS-bucket revision (Dart SDK, host tools, OHOS gen_snapshot) |
| `D:\ProgramFiles\flutter_ohos\bin\internal\engine.ohos.har.version` | OHOS-bucket revision for HAR artifacts |
| `D:\ProgramFiles\flutter_ohos\bin\internal\update_dart_sdk.sh` / `.ps1` | Dart SDK download, OHOS bucket URL |
| `D:\ProgramFiles\flutter_ohos\bin\internal\update_engine_version.sh` | 3.41 tree only: writes `bin/cache/engine.stamp`, `engine.ohos.stamp` |
| `D:\ProgramFiles\flutter_ohos\bin\internal\shared.sh` / `shared.bat` | Bootstrap; no URL logic of their own |
| `D:\ProgramFiles\flutter_ohos\packages\flutter_tools\lib\src\cache.dart` | `storageBaseUrl`, `ohosStorageBaseUrl`, `EngineCachedArtifact.updateInner` |
| `D:\ProgramFiles\flutter_ohos\packages\flutter_tools\lib\src\flutter_cache.dart` | Artifact classes and per-host binary directory lists |
| `D:\ProgramFiles\flutter_ohos\packages\flutter_tools\lib\src\features.dart` | Platform feature flags |
| `D:\ProgramFiles\flutter_ohos\packages\flutter_tools\lib\src\ohos\ohos_sdk.dart` | OHOS SDK environment variable names |
| `D:\ProgramFiles\flutter_ohos\release-notes\Flutter 3.41.9-ohos 1.0.0 ReleaseNote.md` | States the 3.41.9 / 3.41.10 naming and API levels |
| `D:\MyNewProjects\qfli_web\pubspec.yaml` | Line 7: `sdk: ^3.11.5` |

Tag-side content was read with `git show HEAD:<path>`; working-tree content was read directly.

## Related Specs

None consulted; the question concerns the external SDK, not project code conventions.

## Caveats / Not Found

- `python ./.trellis/scripts/task.py current --source` reported no active task. The output path was taken from the caller's instruction.
- An early `git status` in the Flutter directory may have refreshed its index stat cache. Later git calls used `GIT_OPTIONAL_LOCKS=0`. No tracked file, ref or cache file was changed.
- No release note for `3.27.5-ohos-1.0.1` specific to non-China networks was found; the tag's notes directory was not read beyond the README.
- No mirror of the OHOS bucket outside Huawei OBS `cn-south-1` was found in the fork's sources.
- OHOS toolchain acquisition on a hosted runner was not researched.
