# GitHub Actions run evidence — 2026-11-27

This report records GitHub metadata for source commit
`ab12fa6313acee4cd2709796ee333561f8d0f8dd` only. Evidence came from GitHub
Actions run and job APIs and run artifact-list APIs. No artifact was downloaded.
The selected session model is `gpt-6.1-sol` (`PI_MODEL`).

## Native workflows: successful

All three runs completed successfully on `main` at the source SHA above.
They establish the listed native workflow outcomes only. They do not establish
Flutter test success, app-package success, six-platform package delivery,
installation or signing acceptance.

### Native build — run 45969409234

[Run 45969409234](https://github.com/azurekiln2333/qflistudio-web/actions/runs/45969409234)
completed at `2026-11-27T08:56:20Z`.

| Job | Result |
| --- | --- |
| Android armeabi-v7a native libraries | success |
| Android arm64-v8a native libraries | success |
| Android x86_64 native libraries | success |
| Linux native regression tests | success |

| Artifact | SHA-256 digest | Expires |
| --- | --- | --- |
| `native-linux-test-logs` | `d34727ee3b5007c0f15204c81d1b1675b710ef1547e85a6e326e7cbb24f04b20` | 2026-12-11T08:56:15Z |
| `native-android-armeabi-v7a-logs` | `8ca8fadd2521e78c9a228481df665b3d6499e076051b33a280dd2dcae26c9160` | 2026-12-11T08:55:59Z |
| `native-android-arm64-v8a-logs` | `02dbdc5d28fe9c596423e2f07413c542aec91d18cea9e203864672feff23181b` | 2026-12-11T08:56:01Z |
| `native-android-x86_64` | `a3bf67091d603662c9c012337ddba9ce9a92d3889d9cdf17f7ca850d3e608ecf` | 2026-12-11T08:56:03Z |
| `native-android-x86_64-logs` | `d80e4df0530a8d86f5daf8eb7d4b0025a02ebe08d7820360a44aa9e524ed78be` | 2026-12-11T08:56:06Z |
| `native-android-armeabi-v7a` | `ca5e3397431b1f8166925359e430423e9e72366bcd609b557034d3cdd9a67349` | 2026-12-11T08:55:58Z |
| `native-android-arm64-v8a` | `de78cebde4eb3cebabface2ce00ab7147e4fa9226480ead077d7f68de2c7efbf` | 2026-12-11T08:56:00Z |

### Native Apple build — run 45969409276

[Run 45969409276](https://github.com/azurekiln2333/qflistudio-web/actions/runs/45969409276)
completed at `2026-11-27T08:56:58Z`.

| Job | Result |
| --- | --- |
| iOS iphonesimulator x86_64 native libraries | success |
| iOS iphonesimulator arm64 native libraries | success |
| iOS iphoneos arm64 native libraries | success |
| macOS x86_64 native libraries and tests | success |
| macOS arm64 native libraries and tests | success |

| Artifact | SHA-256 digest | Expires |
| --- | --- | --- |
| `native-ios-iphonesimulator-arm64-logs` | `f70cfcc66caaedd5fb8c420f02e6ed219cb3f896350b8b2ded4f04fb9375bc2a` | 2026-12-11T08:55:43Z |
| `native-ios-iphoneos-arm64` | `a09bb0e758fb45d3fc24998e64ba4a1643a377405bf806cae24343434dd3c2cc` | 2026-12-11T08:56:52Z |
| `native-ios-iphoneos-arm64-logs` | `e9141995bfa19f07994fddeb7ddce43e5e4d912166b02c6ea79d741ac2d9a1ea` | 2026-12-11T08:56:54Z |
| `native-ios-iphonesimulator-x86_64` | `379a6ae1137d0ef3917ab5d3838f5cbc9e92543875bb8f30481a15b710e8a293` | 2026-12-11T08:55:52Z |
| `native-ios-iphonesimulator-x86_64-logs` | `0d22ab6419a9a99a3af255a5c1deac516179e2ab595be23d0dd2b78d035a1c95` | 2026-12-11T08:55:54Z |
| `native-macos-arm64` | `a67b2769cdb5339a2593ba0c69d2b4fb0b17e97245bb1301cac97a6367656bb3` | 2026-12-11T08:56:21Z |
| `native-macos-x86_64-logs` | `8567fdd4e343f264c660677087056a52650ac2013e46f4a8f49fbf5aa378552d` | 2026-12-11T08:56:06Z |
| `native-macos-arm64-logs` | `8be32db0cd8fa9f4709ffd9999c12b60ebdda105350069e0a88e7bc0475534ab` | 2026-12-11T08:56:21Z |
| `native-macos-x86_64` | `4fdd1dff47d40edfc949fe47b39f5a74345a0ebcbc7a600a93eb237e0fbfc5a6` | 2026-12-11T08:56:05Z |
| `native-ios-iphonesimulator-arm64` | `a3e543f1bf348069411a60df9603ffe2922464c0356e9bc4ee3d22128557aaee` | 2026-12-11T08:55:42Z |

### Native OHOS build — run 45969409494

[Run 45969409494](https://github.com/azurekiln2333/qflistudio-web/actions/runs/45969409494)
completed at `2026-11-27T08:57:06Z`.

| Job | Result |
| --- | --- |
| OHOS arm64 and x86_64 native libraries | success |

| Artifact | SHA-256 digest | Expires |
| --- | --- | --- |
| `native-ohos` | `2fabe347701bbf867ef27928646401321f1c752edfe47c617f2bd4468ca7ea5c` | 2026-12-11T08:56:59Z |
| `native-ohos-logs` | `5c4ab98894b67fd2c32240e26c2e9577d062d5faf235f0d107cba7120f70200d` | 2026-12-11T08:57:01Z |

## Cloud checks and app packages: workflow validation failed

Both runs were triggered by the same push and source SHA. Workflow validation
failed before any job ran. GitHub reported `.github/workflows/cloud-check.yml`
line 87: `runner.temp` is invalid in a job-level `env` value. The package
workflow has the same workflow-validation failure. Pi p2 owns the workflow fix.

| Workflow | Run | Outcome | Jobs | Artifacts |
| --- | --- | --- | --- | --- |
| `cloud-check.yml` | [45969407193](https://github.com/azurekiln2333/qflistudio-web/actions/runs/45969407193) | failure | none | none |
| `app-packages.yml` | [45969409158](https://github.com/azurekiln2333/qflistudio-web/actions/runs/45969409158) | failure | none | none |

Therefore there is no passing cloud-check, Flutter test, or app-package evidence
yet. Do not count these failures as test or package attempts that passed.

## Core pin decision

The 2026-11-27 `core-last.md` decision keeps Core at
`476a30acee21dc486ee2849dd8064a7be665e4d5`. A later `CORE_REF` bump remains
pending and is not a blocker. Do not change the pin independently.

## Scope and limits

This record reports native workflow results and API-listed artifacts only.
Artifact digests are GitHub metadata; no payload was fetched or inspected.
Native-library success does not satisfy app tests, package verification,
installer completeness, signing, installation, or six-platform delivery.
