# Web OHOS source-analysis and preview acceptance

## Status and boundary

**Actual OHOS execution passed all 15 cases on 2026-10-22.** The alternate entry
is `tool/web_ohos_acceptance.dart`, SHA-256
`510ebda01624a64b25eebe16a1027e7d34d69abf983a2fc9bd0f35846242d13a`.
Direct installed Dart SDK analysis reports **No issues found**; Dart formatting
passes. No Flutter process, build, signing, installation or device operation was
run by this implementation worker.

Root built this frozen entry for `ohos-x64`, then installed and launched its
ordinary unsigned HAP on the actual local emulator. The Flutter wrapper emitted
the unsigned/signing warning; installation and execution nevertheless succeeded
on this emulator. This resolves the emulator-only installation gate, with no
physical-device signing claim.

| Captured identity | Actual value |
| --- | --- |
| Acceptance HAP | `build/artifacts/web-native-acceptance-x64.hap` |
| HAP bytes | 42,367,805 |
| HAP SHA-256 | `fd9fb56ad444fb76067009a9580f740c26675b871d6c4613e903c1495094a01b` |
| Shared-core commit recorded by root | `daddce27eed1f9389efed0360a0ca954af422da8` |
| Public emulator model / architecture | `emulator` / `x86_64` |
| Public OS / SDK API | `OpenHarmony-7.0.0.105` / 26 |
| Signing mode | `unsigned-emulator`; `signatureVerified: false` |
| Build log | `research/ohos-runtime-build.log` |
| Structured report | `research/ohos-runtime.json` |
| Own-bundle scoped raw hilog | `research/ohos-runtime.log` |
| Screenshot | `build/content/ohos-runtime-1022.jpeg` |

This worker independently reread the saved artifacts and confirmed the unchanged
entry hash, exact HAP bytes/hash, 15 unique passing case records, one final result
record, and exact agreement between raw hilog JSON and the structured report.
The saved build log records `assembleHap` taking 40.6 seconds followed by the
wrapper's instruction to configure a debug signature in DevEco Studio.
The screenshot visibly shows `PASSED`, both real backend versions and all 15
passing rows. No code change was needed after device execution. The captured
report records the core commit; it does not assert a separately captured clean
working-tree digest.

The observed versions are `QuickJS 2026-06-04 (compile-only, no module resolution)`
and `Nginx 1.31.6`. Actual UTF-16 results match `[39,40)`, `[11,11)` and `[91,92)`.
The native HTTP case records HTML 200, CSS 200, missing JavaScript 404, a real
request-log event and post-stop connection refusal. Both byte/file-set checks
and owned-fixture cleanup passed.

The entry imports the real production `webProfile` from `lib/main.dart` and
calls its `codeAnalyzer` and `webPreviewFactory`. It does not substitute a mock,
parser shim or Dart-only server. It sets the same profile as current without
running the normal application bootstrap. A simple Material page shows live
case status and the actual backend versions for a screenshot.

Only its own `Directory.systemTemp.createTemp` fixture is created or deleted.
Its four files are a deliberately invalid saved JavaScript file, a standalone
local HTML document, local CSS, and `.qfli/web.json` selecting explicit `nginx`
on an ephemeral port. The fixture is deleted in `finally`. Production sources,
user projects, shared core, platform runners and device configuration are not
modified. No external request is made or external browser launched.

## Cases

| Case | Required evidence |
| --- | --- |
| `ohos-profile` | Actual `Platform.operatingSystem == ohos`, real WebCodeAnalyzer, offline profile and preview factory |
| `quickjs-library` | Load packaged `libqfli_web_syntax.so`; call its real version export; exact compile-only/no-module-resolution identity |
| `js-unsaved-clean` | Modern valid unsaved JS parses clean despite a different, invalid saved `app.js` |
| `js-crlf-emoji` | Real QuickJS SyntaxError at original UTF-16 `[39,40)` with CRLF and supplementary characters |
| `js-eof` | Real QuickJS empty insertion range `[11,11)` at EOF |
| `html-embedded-js` | HTML extraction and CRLF/emoji mapping preserve real QuickJS range `[91,92)` |
| `css-supported` | Supported CSS actually parses, with no diagnostics/unavailable result |
| `css-real-error` | csslib reports a genuine declaration error at/after its declaration |
| `css-unavailable` | Valid `@scope` is honestly unavailable, with no false syntax diagnostics |
| `js-no-execution` | Compile filesystem-write/throw/infinite-loop/fetch statements cleanly; sentinel remains absent |
| `js-no-import-read` | A valid module importing an absent local dependency parses without resolving it |
| `sources-unchanged` | Exact byte comparison and file-set comparison for every saved fixture file |
| `native-preview` | Real embedded Nginx version/channel; production factory; Nginx engine and HTTP header; HTML/CSS 200 bodies; missing JS 404; request log; stopped listener refuses a new connection |
| `sources-after-preview` | Preview leaves the same saved bytes and file set intact |
| `fixture-cleanup` | Only this run's fixture is removed |

Every required native-library absence or channel failure fails its case. Explicit
`engine: nginx` and the runtime identity assertion prohibit fallback from being
reported as native success. The Nginx public version comes from the production
embedded channel backed by `libqfli_nginx_napi.so`; the code analyzer uses its
ordinary library-name resolution inside its production isolate.

Sources are small fixed strings. Analysis waits are 5 seconds; version lookup
5 seconds; runtime startup 15 seconds; HTTP stages 3 seconds; request-log wait
3 seconds; stop/fixture deletion 5 seconds. Bodies are capped at 64 KiB and
captured request events at 32. A preview startup that completes after a timeout
retains a late stop handler; the timed-out case remains failed. The HTTP client
uses direct loopback IPv4 only, no environment proxy. The source-only fetch trap
also names loopback rather than any external endpoint.

## Output contract and root execution

Each case emits one public JSON line prefixed with
`QFLI_WEB_OHOS_ACCEPTANCE_CASE:`. Exact ranges and semantic preview results live
in those lines. Errors redact the temporary root and are length-bounded. There
is no private device identifier, source path, signing material or session token
in the structured report.

One final JSON line is prefixed with `QFLI_WEB_OHOS_ACCEPTANCE_RESULT:`. It includes
`schemaVersion: 1`, `status`, public OS/profile/library identities, actual
QuickJS/Nginx versions, `passed`, `failed`, and the complete boolean case map.
The ordinary all-pass report is about 633 UTF-8 bytes including its marker, so it
fits in a single device log record. Acceptance requires `status: passed`,
`passed: 15`, `failed: 0`, every named case true, both real version identities,
and captured matching per-case lines. A missing/truncated marker is not a pass.

Root performed the serialized alternate-entry build, installation, launch, hilog
and screenshot capture. The actual native-acceptance build targeted x86_64 only:

```powershell
flutter build hap --release --target tool/web_ohos_acceptance.dart --target-platform ohos-x64
```

Root subsequently rebuilt the normal product entry with both Flutter ABIs.
The inspected normal HAP is 80,688,547 bytes, SHA-256
`b3ac4a805488789565715dc91037b9859da4333accf563d18c03d0ce3b0cb6d6`.
This build is separate from the successful alternate-entry native run:

```powershell
flutter build hap --release --target lib/main.dart --target-platform ohos-arm64,ohos-x64
```

The catalog driver installed that normal HAP with its matching test HAP and
finished a complete second content run (474/481, seven failures still open).
Its owned CDP forward was removed and its test ability received the targeted
stop. A later normal-Home launch attempt could not run because the exact emulator
target had disconnected. That attempted launch is not a successful restoration
claim. Web released the device window in global channel seq163.

Implementation validation performed without Flutter processes:

```powershell
& 'D:/ProgramFiles/flutter_ohos/bin/cache/dart-sdk/bin/dart.exe' format tool/web_ohos_acceptance.dart
& 'D:/ProgramFiles/flutter_ohos/bin/cache/dart-sdk/bin/dart.exe' analyze tool/web_ohos_acceptance.dart
```

## Claim limits

This successful run proves production Dart source-analysis adapters, FFI loading
and the measured local native preview lifecycle on the tested x86_64 OHOS
emulator. It does
not prove full editor underlines/Problems gestures, multi-root UI persistence,
native breakpoints/debugging, physical-device signing, arm64 execution, all
curriculum entries, or any other product's acceptance. Those remain separate
gates with their own evidence.
