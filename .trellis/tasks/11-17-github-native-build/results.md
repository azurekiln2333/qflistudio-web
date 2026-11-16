# GitHub native build results — 2026-11-17 (Asia/Shanghai)

## Source and delivery

- Started from clean local `feat/offline-web-ide` at `53353d8`.
- GitHub's feature branch was seven commits behind local source.
- Created and pushed only `ci/native-build-20261117` to the explicit GitHub URL.
- No other origin push URLs were used. No main/feature branch was merged.
- Implementation: `2f98f43`; Android sdkmanager path fix: `4044058`.

## Actual hosted evidence

- Linux + Android: https://github.com/azurekiln2333/qflistudio-web/actions/runs/43923902421
  at `40440585f0c728830e66f6539b41590ee7eeabfa`, all four jobs SUCCESS.
- OHOS: https://github.com/azurekiln2333/qflistudio-web/actions/runs/43923264898
  at `2f98f431308a6bdc9d6968702e5ddce445285d4c`, SUCCESS.
- Linux built desktop/embedded Nginx and QuickJS. Syntax, embedded lifecycle,
  access-log regression and portable CDP transport tests all passed.
- Android built Nginx and QuickJS for ARM64, ARMv7 and x86_64. ELF ABI, entry-point
  shape and minimum 16 KiB LOAD alignment gates passed.
- OHOS SDK 6.1.0.31 checksum/metadata verification passed. ARM64 and x86_64 builds
  produced embedded archive/shared library, Nginx NAPI, CDP NAPI and QuickJS.
  ELF ABI/alignment, C ABI exports, NAPI registration and dependency gates passed.
- First native run `43923264784` failed only at Android sdkmanager (exit 127).
  Hosted images no longer put it on PATH. Resolving the installed absolute path
  fixed all three jobs. Its Linux job passed too.

## Artifacts

| Artifact | Bytes |
| --- | ---: |
| native-linux-x86_64 | 7,188,125 |
| native-android-arm64-v8a | 3,197,781 |
| native-android-armeabi-v7a | 3,116,924 |
| native-android-x86_64 | 3,350,336 |
| native-ohos (two ABI archives) | 13,709,708 |

Each has a separate logs artifact. Artifact IDs, API digests, source commits and
expiry timestamps are recorded in `artifacts.json`. Retention is 14 days.
The Android ARM64 artifact was downloaded from GitHub independently. The outer
archive checksum and all 15 inner SHA256SUMS entries matched. Manifest commit,
NDK and run URL matched the actual build. Source trees/object caches are absent.

## Storage

Measured logical bytes (long-path-aware walk, no symlink following) are recorded
in `storage-audit.json`:

- `build/`: 3,819,505,351 bytes (3.56 GiB).
- `.dart_tool/`: 1,686,238,307 bytes (1.57 GiB).
- `ohos/entry/build/`: 1,255,168,680 bytes (1.17 GiB).
- These three nonoverlapping directories total about 6.30 GiB.
- `build/native/`: 949,368,760 bytes (0.88 GiB), already included in build/.
- An anomalous root directory named one space has 16,230,965 bytes of old Nginx
  extraction/build material. No files or caches were deleted.

Cloud native builds avoid future local native compilation caches only when used
instead of local native compilation. They do not remove existing caches or alter
Flutter/Gradle/Hvigor builds to consume downloaded binaries automatically.

## Verification limits

actionlint 1.7.12, Python syntax, YAML/Bash/embedded Python syntax and Chinese
prose lint passed. Linux-path/space/exit-code checks of ohos_cc.sh passed using
Git Bash; local WSL cannot start because Hyper-V is unavailable.

No Dart/application behavior changed. No local Flutter builds were run. Native
artifacts are not APK/HAP/IPA installers, signing evidence or device execution
evidence. Product README still records open ArkWeb/full end-to-end acceptance.
Windows and Apple builds were not included. Current shared core was not modified.
