# Design: application package workflow

## Files

| File | Change |
| --- | --- |
| `.github/workflows/app-packages.yml` | new workflow |
| `.github/actions/setup-app-build/action.yml` | new composite action: core checkout, Flutter fork, `pub get` |
| `scripts/verify_app_package.py` | new: package content check and SHA-256 (R6), owned by Pi p4 |
| `scripts/prepare_ohos_ci_profile.py` | new: strip signing from the CI working copy |
| `installer/windows/qfli-webforge.iss` | new: pinned Inno Setup script for the Windows installer `EXE` |
| `android/app/build.gradle.kts` | read optional `android/key.properties` (R5) |
| `android/.gitignore` | confirm `key.properties` and `*.jks` are ignored |
| `docs/app-packages.md` | new user guide (R9) |
| `docs/native-builds.md` | one pointer line to the new guide |

This package task does not own the three native workflows. Test-repair
ownership is recorded in the migration task's `implement.md`. Pi p5 owns
`.github/workflows/app-packages.yml`. Pi p4 owns `scripts/verify_app_package.py`
and `installer/`. Pi p2 owns `.github/workflows/cloud-check.yml` and
`scripts/check_source_policy.py`. Root stages, commits,
pulls and dispatches. No agent runs `git push`.

## Workflow shape

```text
on: workflow_dispatch | push tags v* | push paths [workflow, action, pubspec, scripts, vendor, assets, installer, platform directories, lib, test]
permissions: contents: read          (release job alone gets contents: write)
concurrency: app-packages-${{ github.ref }}, cancel-in-progress

jobs
  cloud-check  reusable call to cloud-check.yml
  android  ubuntu-24.04      needs cloud-check
  linux    ubuntu-24.04      needs cloud-check
  windows  windows-2022      needs cloud-check
  macos    macos-15          needs cloud-check
  ios      macos-15          needs cloud-check
  ohos     ubuntu-24.04      needs cloud-check
  release  ubuntu-24.04      needs all six package jobs, only on refs/tags/v*
```

Every package job needs the `cloud-check` job, so a failed source or test gate
stops the packages. The release job fails closed: it skips when any needed job
is a failure, a cancellation or a skip. A missing HAP therefore stops a tag
release instead of publishing a partial one.

Jobs use separate jobs, not a matrix: each platform's steps differ too much.

## Shared setup (composite action)

Inputs: `flutter-ref` (tag `3.41.10-ohos-1.0.0`), `flutter-revision`
(peeled commit `244a0e8abb3085e8675589b13e219af8c41cb7aa`), `core-ref`
(commit `b756b2eaf9fb941d6bdad30a7ba4262d7341e2ce`) and `precache`
(platform flags). These match the migration plan. Each cloud check and package
job verifies and records the same dependency commits before building. A moving
branch, an annotated tag-object SHA or per-job ref lookup is not reproducible.

Historical fork investigation is retained in
`research/flutter-fork-ci-artifacts.md`. Its local-install observations do not
replace the exact peeled-commit requirement above. Do not substitute the older
`3.27.5-ohos-1.0.1` tag.

1. Clone the public core repository into
   `$GITHUB_WORKSPACE/../qflistudio-core` at the pinned `core-ref`.
   The Dart package/import name remains `qfli_studio_core`.
   Fail before building if the SHA is missing or cannot
   be resolved. Reuse this exact SHA in all six package jobs and report it in
   every job summary. `actions/checkout` cannot write outside the workspace,
   so the action uses an explicit clone/fetch of that commit.
2. Clone `https://gitcode.com/openharmony-tpc/flutter_flutter.git` at
   `flutter-ref` to `$RUNNER_TEMP/flutter`. Verify `HEAD` equals
   `flutter-revision`, using the peeled commit for an annotated tag.
   Fail on a mismatch. Add `bin` to `GITHUB_PATH`.
3. `flutter --version`, assert the Dart version satisfies `^3.11.5`.
4. `flutter pub get` (pub-enabled, per release-verification contract).
5. Write core commit and Flutter revision to `GITHUB_ENV` and the step summary.

Print the Web source SHA, Flutter tag, verified Flutter peeled SHA and core
commit in each job summary. All cloud check and package jobs use the same
pinned inputs. Key Flutter/pub caches on the immutable Flutter/core commits,
runner platform and `pubspec.lock`.

## Per-platform build

| Job | Toolchain steps | Build command | Package |
| --- | --- | --- | --- |
| android | Java 17, NDK `27.0.12077973` via sdkmanager, optional `key.properties` from secrets | `flutter build apk --release` | `build/app/outputs/flutter-apk/app-release.apk` |
| linux | `apt-get install clang cmake ninja-build pkg-config libgtk-3-dev liblzma-dev` | `flutter build linux --release` | `tar -czf` of `build/linux/x64/release/bundle` plus a `DEB` built with `dpkg-deb` from the same verified bundle |
| windows | Python on PATH; MinGW GCC on PATH ahead of LLVM Clang so `find_program(NAMES clang gcc)` resolves a GNU-target compiler; official Inno Setup 6.7.4 downloaded from its pinned release URL and checked for SHA-256 and Authenticode signer before use | `flutter build windows --release` | zip of `build/windows/x64/runner/Release` plus installer `EXE` from `installer/windows/qfli-webforge.iss` |
| macos | default Xcode | `flutter build macos --release` | `hdiutil create` dmg from the `.app` |
| ios | default Xcode | `flutter build ios --release --no-codesign` | `Payload/Runner.app` zipped as `.ipa` |
| ohos | download the pinned command-line tools archive, verify its SHA-256, unpack, export `DEVECO_SDK_HOME`, `HOS_SDK_HOME` and PATH for `hvigorw`, `ohpm`, node, then run `prepare_ohos_ci_profile.py` | `flutter build hap --release --no-codesign --target-platform ohos-arm64` | fresh unsigned HAP from the hosted build |

The Linux `DEB` and the Windows installer `EXE` belong to the migration
delivery. A platform that uploads only its archive is incomplete.

Package file names: `qfli-webforge-<version>-<platform>[-<arch>].<ext>`, with
`<version>` from the tag, else `pubspec` version plus short SHA.

### Windows compiler

`windows/CMakeLists.txt:58` prefers `clang`. On the hosted runner that is LLVM
Clang with an MSVC target, which the file's own comment excludes. `flutter
build windows` passes no custom CMake arguments. The job therefore puts the
runner's MinGW `bin` first on PATH and hides Clang from `find_program` by
setting `QFLI_SYNTAX_CC` through the CMake cache environment
(`CMAKE_PROGRAM_PATH`). The implement step verifies which mechanism the
installed Flutter honors and uses the smallest one that works. `CMakeLists.txt`
is changed only if neither works, and then only to honor an environment
variable.

### OHOS

- The workflow pins the tools archive URL and its SHA-256. The job downloads
  both archive parts, joins them, verifies the hash, then unpacks. A mismatch
  fails the job with an `OHOS toolchain blocker` message.
- The job reads the SDK API version from `sdk/default/sdk-pkg.json` and compares
  it with `OHOS_TARGET_API` (24, product `6.1.1(24)`). A mismatch fails the job.
  The HAP records the API of the SDK that built it, so a different SDK is a
  wrong-API artifact, not a warning.
- `flutter build hap` must exit zero. A non-zero exit fails the job even when a
  HAP file exists, and a HAP from an earlier run cannot stand in for this build.
- `prepare_ohos_ci_profile.py` rewrites the sanitized profile in the runner's
  working copy for an unsigned build. Tracked `ohos/build-profile.json5` has
  empty `signingConfigs` and no product `signingConfig`; preserve SDK, product
  and bundle settings. Never read or stage the ignored local original backup.
  Future CI credentials must use GitHub Actions secrets.
- This migration builds unsigned for OHOS. Missing signing material does not
  fail artifact creation. An unreachable tools archive or a hash mismatch is a
  separate toolchain blocker. A failed or skipped job is not OHOS delivery.
- Default target is arm64 only.

#### Retained research history

The following source-review findings are retained from the initial design
investigation. Run all builds, lint, package/source checks and dependency
resolution on GitHub-hosted Actions only. Do not run them locally.

- The HarmonyOS tools must be unpacked and exported before `flutter pub get`.
  Platform tooling generation requires the SDK when the OHOS feature is enabled.
  The five non-OHOS jobs disable that feature before resolving packages. The
  OHOS job enables it after exporting SDK paths.
- The hosted OHOS job may use `flutter build hap --release --no-codesign`
  and upload its fresh unsigned HAP. Missing signing material does not fail
  migration artifact creation.
- `prepare_ohos_ci_profile.py` must operate on the tracked sanitized profile.
  It must not restore or read any local signing backup.
- Environment, `$TOOLS` being the unpacked `command-line-tools` directory:
  `DEVECO_SDK_HOME=$TOOLS/sdk`, `HOS_SDK_HOME=$TOOLS/sdk`,
  `NODE_HOME=$TOOLS/tool/node`, PATH gains `$TOOLS/bin`, the node `bin` and
  `$TOOLS/sdk/default/openharmony/toolchains`. `tool/node` is inferred. The
  job locates `node`, `hvigorw` and `ohpm` in the archive and fails with a
  message naming the missing one.
- `apt-get install libgl1-mesa-dev`. `~/.npmrc` uses
  `registry=https://repo.huaweicloud.com/repository/npm/` and
  `@ohos:registry=https://repo.harmonyos.com/npm/`. `ohpm config set registry
  https://ohpm.openharmony.cn/ohpm/`.
- JDK 17 for tools older than 26.0.0, JDK 21 for newer. The Java version is a
  workflow-level variable.
- Pin and report the selected Flutter repository URL, tag and resolved
  revision for the run.

### Signing and release-readiness boundary

Migration artifact jobs require no signing credentials. Accept a debug-key
Android APK and unsigned iOS IPA/OHOS HAP after hosted package-content checks
pass. Their summary must state signing explicitly. Missing credentials never
gate these artifacts. Distribution signing, iOS provisioning, macOS
notarization, OHOS AppGallery signing and device/store acceptance remain later
release-readiness work. Any future signing material must come only from Actions
secrets. The tracked OHOS profile is sanitized; local originals/backups stay
outside migration. Source inspection cannot establish whether an older Git
history exposed credentials; root coordinates credential rotation if that
exposure is confirmed.

`build.gradle.kts` may retain its optional key-properties branch for a later
release flow. No local key file is an input to this task's validation.

## Verification script

`scripts/verify_app_package.py --platform <p> --package <file>` opens the
archive (zip or tar.gz) and asserts required members, then writes
`<file>.sha256`. The installer paths are the intended contract; each one needs
a hosted run before it counts as evidence.

| Platform | Required members or installer check |
| --- | --- |
| android | per ABI: `lib/<abi>/libapp.so`, `libflutter.so`, `libnginx_exec.so`, `libqfli_web_syntax.so` |
| ios | `Payload/Runner.app/Runner`, `Frameworks/App.framework/App`, `Frameworks/Flutter.framework/Flutter` |
| ohos | `libs/arm64-v8a/libapp.so`, `libflutter.so`, `libqfli_nginx_napi.so`, `libqfli_web_cdp_transport.so`, `libqfli_web_syntax.so` |
| linux | `qfli_web`, `lib/libapp.so`, `lib/libqfli_web_syntax.so`, `data/nginx/nginx` |
| windows | `qfli_web.exe`, `flutter_windows.dll`, `qfli_web_syntax.dll`, `data/app.so`, `data/nginx/nginx.exe` |
| macos | `Contents/MacOS/*`, `Contents/Helpers/nginx`, `Contents/Frameworks/App.framework` |
| linux DEB | `dpkg-deb --extract` then the full payload under `opt/qfli-webforge` compared file by file with the verified bundle, plus `usr/bin/qfli-webforge` and the desktop entry |
| windows EXE | silent install into a temporary directory, payload compared file by file with the built `Release` tree, SHA-256 per file, then silent uninstall |
| macos DMG | mount the image, check the `.app` inside it and detach. Intended contract, pending hosted evidence |

Exact member paths are confirmed against the first real build of each
platform. A check is corrected to match the product's real layout; it is not
weakened to pass.

## Release job

Runs on `refs/tags/v*` when no needed job failed. The release job fails closed:
if any needed job is a failure, a cancellation or a skip, the release does not
run. Download only verified package artifacts, write a combined `SHA256SUMS`,
and use `gh release create "$TAG" --verify-tag --generate-notes` for those
files. The release body carries the signing-state table and dependency SHAs
from R7. No agent runs `git push`. The tag publication path exists in the
workflow, but the push gate currently delivers `main` only. Tag delivery needs a
separate authorized gate run and is not implemented yet. Do not describe a tag
release as available through the current gate.

## Trade-offs

- One workflow with six jobs, not six workflows: one trigger, one release.
- Flutter fork cloned at the recorded tag and verified against its pinned
  peeled commit. An upstream outage fails the run. The cache may reduce
  repeated downloads.
- Core must come from the immutable SHA selected by root, never a moving
  `main` ref or independent per-job resolution.

## Rollback

Root owns rollback. Root stages, commits, pulls and dispatches. No agent runs
`git push`; the gate performs the push. Review exact paths before reverting any
workflow, profile or dependency change. Preserve unrelated work and historical
cloud evidence. A rollback must not restore private signing material.
