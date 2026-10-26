# QFLIWebForge

Languages: **English** · [简体中文](README.md) · [繁體中文](README.zh-Hant.md)

QFLIWebForge is a web IDE for phones. It previews HTML, CSS and
JavaScript projects on the local machine. It sends console output back to the
editor.

## Product identity

- Product name: QFLIWebForge.
- Repository name: `qfli_web`.
- Application ID: `com.azurekiln.qfli.webforge`.
- Application version: 1.0.0+1.
- The interface comes from the shared `qfli_studio_core` package.
- This repository keeps only the Web profile and the Web tools.

## Features

### Editor and preview

- The shared editor provides syntax highlighting and multi-file editing.
- Project templates are empty and HTML.
- The preview server listens on `127.0.0.1` only.
- Port 0 selects a free port.
- Static files, SPA fallback and directory index are supported.
- HTTP and WebSocket proxies are supported.
- Proxy targets accept literal loopback IP addresses only.
- Live reload, console, error and request diagnostics are supported.
- A long press on Run previews the current file.

### Dual engines

- The `engine` field in `.qfli/web.json` selects the engine.
- `auto` prefers packaged Nginx and falls back to the Dart middleware when the
  engine is missing.
- `auto` probes the embedded engine first on iOS and HarmonyOS.
- `nginx` uses Nginx only. Startup fails when it is missing.
- `webforge` uses the Dart middleware.
- Nginx is upstream 1.31.6.
- Android and desktop host Nginx as a process.
- iOS and HarmonyOS run the embedded engine in process.
- An explicit `nginx` request never falls back to another engine.

### Offline tools

- The local server panel shows the address, requests and console output.
- JSON, URL and Base64 codecs compute locally.
- Document inspection reports missing and external references.
- CSS tools compute color, contrast, box model and specificity.
- HTML tools check tag pairing and accessibility.
- The Tools page provides a terminal entry point.
- The shared core determines terminal commands and permissions.

### Code analysis

- HTML uses the `html` parser.
- CSS uses the `csslib` parser.
- JavaScript uses QuickJS 2026-06-04.
- QuickJS compiles the unsaved buffer only. It never runs code.
- A missing native library reports unavailable, never clean source.

### Offline curriculum

- The curriculum has 481 topics.
- Each topic pairs one tutorial with one example.
- Language split: HTML 160, CSS 160, JavaScript 161.
- Every example is a previewable `.html` file with a semantic assertion.
- HTML example 006 deliberately references a missing image.
- Tutorial and example prose is written in Simplified Chinese. The code is
  HTML, CSS and JavaScript.

## Offline boundary

- The product hides login, cloud sync and Git entries.
- The product hides HTTP client and external proxy entries.
- Tools compute on the local machine.
- Preview connects to loopback only.
- Proxy targets must be literal loopback IP addresses.
- Every response carries an offline content policy.
- The policy allows inline scripts, local resources, same-origin object documents
  and data/blob assets.
- The policy does not stop a system browser from opening ordinary links.
- Offline covers the product runtime, not the system browser.
- The product does not depend on a remote service.

## Quick start

Development requirements:

- A Flutter SDK is required.
- The Dart SDK must satisfy `^3.11.5`.
- Building a HAP requires the Flutter OHOS SDK.
- The shared editor comes from the sibling `qfli_studio_core` package.
- Installing dependencies may use the network.
- The product runs offline after installation.

Check out `qfli_studio_core` as a sibling directory first.

```text
checkout-parent/
  qfli_studio_core/
  qfli_web/
```

1. Check out the sibling `qfli_studio_core`.
2. Run `flutter pub get` in this repository.
3. Connect a device.
4. Run `flutter run`.
5. Open an HTML project.
6. Tap Run.
7. View the preview.

Optional `.qfli/web.json` configuration:

```json
{
  "engine": "auto",
  "port": 0,
  "spaFallback": false,
  "root": ".",
  "proxies": [
    { "prefix": "/api", "target": "http://127.0.0.1:8080" }
  ]
}
```

Release builds:

```text
flutter build apk --release
flutter build hap --release
```

Keep pub enabled when switching from integration or debug to release. With
`--no-pub` the generated plugin registrant can keep referencing the dev-only
integration-test plugin.

## Repository layout

```text
qfli_web/
├── lib/                Product code
│   ├── main.dart       Profile and bootstrap
│   ├── pages/          Tools page and Web views
│   ├── content/        Offline curriculum adapter
│   └── services/       Preview, engines and configuration
├── test/               Unit and widget tests
├── integration_test/   Device integration tests
├── tool/               Native engine and acceptance entry points
├── scripts/            Content, build and browser checks
├── native/             Embedded engine C ABI and syntax bridge
├── vendor/             Upstream source, patches and licenses
├── assets/             Icon, licenses and curriculum JSON
├── android/ ios/ macos/ linux/ windows/ ohos/   Platform runners
└── web/                Flutter Web shell
```

## Verification

Content checks:

```text
python -X utf8 scripts/emit_content.py
python -X utf8 scripts/test_emit_content.py
python -X utf8 scripts/audit_web_content.py --product --report build/content/audit.md
```

- Re-running the content scripts produces identical bytes.
- The structure audit checks IDs, mapping and uniqueness.

Browser content check. The first install uses the network:

```text
npm ci
npx playwright install chromium
npm run verify:content
```

- The browser check runs every example.

Host analysis and unit/widget tests:

```text
flutter analyze --no-pub lib test integration_test tool
flutter test --no-pub --concurrency=1
```

`flutter test` without `-d` runs the host suites under `test/` only. It does not
run `integration_test/`. Static analysis reads those files but never runs them.

Device execution needs a connected device and one file at a time:

```text
flutter test -d DEVICE integration_test/nginx_runtime_test.dart
flutter test -d DEVICE integration_test/content_import_test.dart
flutter run --debug --no-pub -d DEVICE -t tool/nginx_smoke.dart --no-resident
```

- Only `[NGINX_SMOKE] PASS` counts as a native engine pass.
- A successful build is not execution evidence.

## Platform limits

Evidence comes from recorded runs. Dates stay in the cells.

| Platform | Packaging | Runtime evidence |
| --- | --- | --- |
| Windows x64 | Official Nginx 1.31.6 | 2026-10-01 real-binary integration tests passed |
| Android x86_64 | NDK PIE, 16 KiB alignment | 2026-10-01 to 10-03 emulator smoke passed on API 37 |
| Android arm64 | Packaged in the APK | 2026-10-15 physical-device native and content smoke passed |
| Android armv7 | Packaged in the APK | Physical-device execution not verified |
| HarmonyOS arm64/x86_64 | Embedded NAPI shared library | 2026-10-12 signed HAP device smoke passed |
| Linux x86_64 | Upstream source through CMake | 2026-10-02 standalone engine passed. Flutter app not verified |
| macOS arm64/x86_64 | Xcode bundles and signs | Not run. No Apple build host |
| iOS arm64 | Static archive and Swift channel | Not run. No Apple build host |

Release signing state:

- Android release uses the debug key. It is a validation package.
- Store distribution needs production signing.
- OHOS has no reachable device target at present.
- OHOS runtime is not verified for the current package.
- iOS and macOS need an Apple build host and signing.
- The full Flutter Windows GUI build lacks Visual Studio C++ tools here.

Current state of the working tree:

- The last complete 481-example Chromium run passed on 2026-10-22 for desktop
  and mobile viewports.
- The 2026-10-22 native ArkWeb run reported 474 passed and 7 failed. The failing
  examples were repaired in source. A native re-run is pending.
- On 2026-10-26, the production CSP browser regressions passed for both engines.
- That fix was published as 5bd2e3a to five remotes.
- On 2026-10-26, the C895 full validation passed.
- All four phases passed: format, tests, analysis and content.
- The test phase passed all 321 tests with 0 failures.
- Formatting processed 11 files and changed 0.
- Static analysis checked 4 targets and found no issues.
- The 481-pair content audit passed with 0 issues.
- The validation exited 0 and left 0 active processes.
- The child run took 99.981 seconds, inside its own window.
- C904 recorded the complete handoff proof at 158.019 seconds, within the 180-second limit.
- The owned-preview policy and broker primitives are host validated.
- ArkWeb integration remains open.
- This host run did not validate OHOS.
- All-product acceptance remains open.
- The current tree is not re-verified end to end.

Treat each row as dated evidence with its recorded scope. A historical pass does
not certify the current candidate.

## Further reading

- Preview and proxy contracts: [.trellis/spec/backend/web-runtime.md](.trellis/spec/backend/web-runtime.md).
- Native engine: [.trellis/spec/backend/native-runtime.md](.trellis/spec/backend/native-runtime.md).
- Curriculum verification: [.trellis/spec/backend/catalog-verification.md](.trellis/spec/backend/catalog-verification.md).
- Platform evidence: [vendor/nginx/VALIDATION.md](vendor/nginx/VALIDATION.md).
- Release checks: [.trellis/tasks/10-15-webforge-store-readiness/](.trellis/tasks/10-15-webforge-store-readiness/).
- The C843 acceptance record: [web-c843-validation-20261026.md](.trellis/tasks/10-22-standalone-offline-ide/research/web-c843-validation-20261026.md).
- The C895 acceptance record: [web-c895-validation-20261026.md](.trellis/tasks/10-22-standalone-offline-ide/research/web-c895-validation-20261026.md).
- Current offline IDE work: [.trellis/tasks/10-22-standalone-offline-ide/](.trellis/tasks/10-22-standalone-offline-ide/).

## License

- Upstream Nginx license: [vendor/nginx/LICENSE](vendor/nginx/LICENSE).
- QuickJS uses the MIT license: [vendor/quickjs/LICENSE](vendor/quickjs/LICENSE).
- The curriculum is original content under CC BY 4.0.
- Root license: [LICENSE](LICENSE), GPL-3.0.
