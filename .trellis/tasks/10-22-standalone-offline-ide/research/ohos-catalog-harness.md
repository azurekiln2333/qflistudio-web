# Test-only OHOS ArkWeb catalog harness

## Implemented boundary and reason

Only `ohos/entry/src/ohosTest/`, `scripts/prepare_ohos_catalog.py`, `scripts/run_ohos_catalog.py`, `scripts/test_ohos_catalog_driver.py`, and this research artifact are owned by this worker. The production ability, production ArkUI page, production profile, catalogs, shared core, and root-owned browser runner were not edited. A test-only ArkWeb component renders exact packaged example source; existing independent Playwright semantic oracles remain the host assertions. This is an ArkWeb content-runtime test, separate from production Nginx lifecycle/integration tests.

The installed SDK `ets/api/@ohos.web.webview.d.ts` declares the single-boolean debugger API since API9 and `(boolean, port)` since API20. The latter creates a TCP socket and requires port1025..65535. SDK API18 compatibility therefore needs Unix mode; do not call the API20 overload on an older phone. `onInterceptRequest` supplies a response without fetching the request; its explicit null result permits the engine's normal data/blob handling.

## Preparation and provenance

```powershell
python scripts/prepare_ohos_catalog.py
python scripts/prepare_ohos_catalog.py --check
```

Default copies:

```text
ohos/entry/src/ohosTest/resources/rawfile/ohos_catalog/examples.json
ohos/entry/src/ohosTest/resources/rawfile/ohos_catalog/tutorials.json
ohos/entry/src/ohosTest/resources/rawfile/ohos_catalog/manifest.json
```

They are generated/ignored rather than duplicate tracked catalogs. The script copies bytes exactly, validates nonempty unique example/tutorial/lesson inventories, exact example-to-lesson code equality and full coverage, and refuses a moving source snapshot. Rerun preparation after expansion and require `--check` immediately before packaging. Individual outputs replace atomically; native SHA checks reject a mixed/partial staging snapshot rather than report ready.

Native `CatalogHarness.prepare` reads those resources through the test ability's resourceManager. It checks path/schema, byte length and real SHA256 using cryptoFramework before exposing bootstrap. Missing files or hashes show failure and no ready catalog. No hardcoded expected sample count exists; a finite upper bound45536 reflects one unique local port per case (20000..65535), not a pass threshold.

## Exact bootstrap contract (agreed with root)

Initial native Web address:

```text
http://127.0.0.1:19999/__qfli_catalog/bootstrap
```

It sets one trusted host-readable variable:

```javascript
window.__QFLI_OHOS_CATALOG__ = {
  schemaVersion: 1,
  backend: 'arkweb-test',
  runId: '<native timestamp>',
  environment: {
    bundleName: 'com.azurekiln.qfli.webforge',
    moduleName: 'entry_test',
    abilityName: 'TestAbility',
    osFullName: '<native public OS name>',
    sdkApiVersion: 24,
    deviceType: 'phone'
  },
  manifest: {
    schemaVersion: 1,
    kind: 'qfli-ohos-catalog',
    files: {
      examples: {path: 'ohos_catalog/examples.json', bytes: 0, sha256: '<64 hex>'},
      tutorials: {path: 'ohos_catalog/tutorials.json', bytes: 0, sha256: '<64 hex>'}
    },
    counts: {examples: 0, tutorials: 0, lessons: 0}
  },
  tutorials: {/* complete parsed tutorials.json, preserving every field */},
  examples: {/* complete parsed examples.json, preserving every field */},
  cases: [
    {id: '<example id>', origin: 'http://127.0.0.1:20000',
     url: 'http://127.0.0.1:20000/index.html'}
  ]
};
```

Counts and SDK numbers above illustrate field types only. Runtime catalog values come from the complete packaged catalog; environment values come from `context.abilityInfo` and public `deviceInfo` properties. No serial, UDID or signing material is exposed. Catalog JSON is escaped for `<` only while embedding the bootstrap script; round-trip is exact, including code with `</script>` and all original fields.

Case i uses port20000+i. This Web component is incognito and must be recreated for each complete run. Origins differ for DOM storage; cookies ignore ports, so the root runner clears its isolated context's cookies before every case and resets `window.name`. Avoid global WebStorage.deleteAllData because the test feature shares app storage and should not clear unrelated data. All runner-created state is within the test incognito component.

For each case, interception returns the exact `example.code`, UTF8 text/html, status200 and no-store. Query/fragment variants identify the same source. No helper scripts, tests, missing-resource substitutes or companion assets are inserted. Any absent local file returns404; the existing intentional `/missing.png` lesson remains a genuine missing image. All nonlocal HTTP requests return403 without network access. data/blob/about handling remains native; root also blocks and records every non-current-origin request before it can be fetched. Semantic assertions must still fail on attempted external traffic.

## Test-only debugger lifecycle

`TestAbility.onCreate` inspects explicit Want parameters:

- `qfliCatalogCdp = 'tcp'`, optional numeric `qfliCatalogPort` (default9222): enables API20 TCP mode.
- `qfliCatalogCdp = 'unix'`: enables API9+ Unix-domain debugging.
- Anything else: CDP remains disabled.

Only test source imports debugger enabling. Window teardown and ability teardown disable the same debugger mode; renderer disposal stops page activity. Invalid ports or unsupported TCP API fail initialization rather than silently advertise readiness. No release-build flag or production entry point enables this debugger.

The test module declares singleton launch. `qfliCatalogStop = true` in a new Want disables CDP and calls `terminateSelf()` on this test ability. The host driver uses this narrowly targeted cleanup; it never force-stops the entire WebForge bundle or another app. The stop request is recorded as a request, not falsely reported as observed UI teardown.

Build invocation executed successfully with the real local Hvigor task graph, from `ohos/`:

```powershell
hvigorw --mode module -p product=default -p module=entry@ohosTest -p buildMode=debug -c properties.enableSignTask=false assembleHap --no-daemon
```

Physical-device/default installation requires a signature valid for the actual WebForge bundle; the explicitly guarded unsigned x86_64 emulator mode is described below. Do not borrow another product's identity or profile. Inspect resulting archives: only test HAP should contain testability/CatalogHarness code and `rawfile/ohos_catalog/*`; production HAP must not include any debugger enable call or generated test rawfiles. Compare the test rawfile catalogs byte-for-byte with production HAP `resources/rawfile/flutter_assets/assets/content/{examples,tutorials}.json` and the final working-tree catalogs; a test HAP alone does not prove production assets match.

After a matching signed test feature is installed and the actual device is known, launch the test ability explicitly (verify the final feature module identity in the built module.json):

```powershell
hdc -t <device> shell aa start -b com.azurekiln.qfli.webforge -m entry_test -a TestAbility --ps qfliCatalogCdp tcp --pi qfliCatalogPort 9222
hdc -t <device> fport tcp:9222 tcp:9222
Invoke-RestMethod http://127.0.0.1:9222/json/list
node scripts/run_examples.mjs --ohos-cdp http://127.0.0.1:9222 --report <current-report.md>
```

For Unix mode discover the actual debugger socket; do not assume a PID/socket label:

```powershell
hdc -t <device> shell cat /proc/net/unix
hdc -t <device> fport tcp:9222 localabstract:<observed-debugger-socket>
```

Record the exact local/remote forwarding pair from `hdc fport ls`, remove only that pair with `hdc -t <device> fport rm tcp:9222 <remote-spec>` afterwards, and close the test ability. Pass local and remote as two separate process arguments; a single quoted `"tcp:9222 tcp:9222"` argument is rejected by the observed Windows HDC. Never restart shared HDC services to create a target. A TCP endpoint should expose `/json/list` and a usable CDP WebSocket; this is a pending real-device capability check.

## Signed-device driver

```powershell
# Read-only preflight; the exact target must already be live.
python scripts/run_ohos_catalog.py --device <actual-target> --production-hap <current-signed-main.hap> --test-hap <current-signed-test.hap> --sign-tool <official-sdk-hap-sign-tool.jar> --report build/content/ohos-catalog.md

# After coordinating exclusive use of that target, opt in to install/launch/run.
python scripts/run_ohos_catalog.py --device <actual-target> --production-hap <current-signed-main.hap> --test-hap <current-signed-test.hap> --sign-tool <official-sdk-hap-sign-tool.jar> --run --report build/content/ohos-catalog.md
```

The driver requires all three identity inputs. It never auto-selects a target, starts an emulator or restarts device services. An absent/nonmatching target, including literal `[Empty]`, fails before HAP reads or device mutations. The actual current empty-target `--run` negative was exercised; it produced only failure evidence.

Preflight verifies exact source/staging bytes, correct main/test bundle/module/ability/version, singleton cleanup support in compiled test code, test rawfile/manifest presence, absence of test-harness leakage into production, and production native-engine packaging. Both archives must pass the installed official SDK `verify-app` and `verify-profile`; profiles must bind the WebForge bundle, be currently valid, and use the same verified certificate chain. HAP hashes are rechecked against mutation. **The installed signer CLI can exit zero after printing `verify-app failed` for an unsigned HAP.** The driver therefore requires explicit operation success plus real verification outputs; process exit status alone is insufficient.

Provisioning content can include private device identifiers. The driver reads exported profiles only in an automatically removed temporary directory and saves only bundle, profile type/validity and public hashes. Default-mode public target evidence is limited to `const.ohos.fullname`, `const.ohos.apiversion` and `const.product.devicetype`; the explicit emulator mode below also records its public model/architecture. Target selection is recorded by SHA256 rather than the raw connection key. Signature verification does not establish device trust/installability; the device's actual install acknowledgment is a separate run gate.

With `--run`, the driver checks an unused host/HDC port, rechecks target/artifacts/source, installs the exact verified main and test HAPs together, launches only `TestAbility`, establishes only its own local CDP forward, waits for the exact native bootstrap, and invokes `scripts/run_examples.mjs --ohos-cdp ... --report ...` without filtering/limits. Native report acceptance requires every source ID and code hash, nonempty successful assertions, complete mapping/counts, the exact manifest/source hashes, and public native environment matching the selected HDC target. Source changes during execution invalidate the result. Host Chromium reports and incomplete/native failures are rejected.

For API9..19 use `--cdp-mode unix`. The driver observes abstract sockets before/after launch and requires one newly created devtools socket; several candidates fail rather than guessing. `--unix-socket <exact-observed-name>` can explicitly select a socket, but it must exist after launch. No PID/socket label is synthesized. Actual ArkWeb socket discovery remains unverified until a device is available.

Each attempt writes `<report-stem>.device.json`; semantic output and `<report-stem>.runner.log` are separate. Cleanup removes only the newly created forward and sends only the singleton test ability's stop Want, including after semantic/transport failure. Forward-removal or stop-request failure produces a failing exit status. No full-bundle force-stop, uninstall, global WebStorage deletion or other app cleanup is performed.

## Explicit unsigned x86_64 emulator mode (2026-10-22)

The parent observed an ordinary `hdc install -r` of the current unsigned production HAP succeed, then observed `EntryAbility` launch successfully. Parent-owned public target reads identify `const.product.model` as `emulator`, `uname -m` as `x86_64`, and OS name `OpenHarmony-7.0.0.105`. The installation observation is recorded in `research/ohos-current-unsigned-install.log`. This worker did not perform those operations. An emulator accepting an unsigned HAP establishes neither a verified signature nor physical-device installability.

The new mode must be explicitly selected; omitting the flag retains the complete official SDK signature/profile/bundle/validity/same-certificate gate above. No signature failure automatically falls back to emulator mode.

```powershell
# Read-only target/archive preflight with an explicit emulator boundary.
python scripts/run_ohos_catalog.py --device <exact-live-emulator-target> --production-hap <current-unsigned-main.hap> --test-hap <current-unsigned-test.hap> --unsigned-emulator --report build/content/ohos-emulator-catalog.md

# Parent/device owner only, after obtaining the exclusive target window.
python scripts/run_ohos_catalog.py --device <exact-live-emulator-target> --production-hap <current-unsigned-main.hap> --test-hap <current-unsigned-test.hap> --unsigned-emulator --run --report build/content/ohos-emulator-catalog.md
```

Before inspecting archives, this mode requires the exact requested target in the live HDC list, then queries the target's actual `const.product.model` and `uname -m`. Only the exact values `emulator` and `x86_64` are accepted; a phone/blank model, AArch64, 32-bit x86 or blank architecture fails before installation. Before the ordinary install, the driver rechecks target presence and both identity values. It never starts an emulator, changes device security settings, disables verification on the target, borrows a signing identity, or retries an unsigned install with a bypass.

All existing source/staging/main+test archive identity/catalog/manifest/version/harness-separation checks remain. The production HAP must additionally contain `libapp.so`, `libflutter.so`, `libqfli_web_syntax.so` and `libqfli_nginx_napi.so` under `libs/x86_64/`. Each must have the inspected SHA-256 and a little-endian ELF64 header with machine 62 (x86_64); a directory label alone cannot pass. The parent's independent `audit_hap.py` remains the broader current dual-ABI/native-dependency audit; the driver introduces no external-report dependency.

The `.device.json` records `signingMode: "unsigned-emulator"`, public `emulatorIdentity` model/architecture, the normal OS/API/device-type evidence, and the exact archive/runtime/code hashes. Both artifact signature records explicitly contain `verified: false`, `verification: "not-performed"` and a no-signature/profile-proof reason. No certificate/profile-verification claim is emitted. Default runs record `signingMode: "official-signature"` and still require positive official verification. Java/the signing tool are required only in that default mode.

After installation, both modes require the same actual native bootstrap, exhaustive ArkWeb semantic report, per-entry source hashes/assertions, source stability and targeted cleanup. A host report, partial catalog or failed assertion remains a failure even when the emulator accepted installation. Cleanup still removes only this driver's new forward and sends only `qfliCatalogStop` to its singleton test ability.

Validation for this change: `python -X utf8 scripts/test_ohos_catalog_driver.py -v` passes **13/13 host regression methods**, including multiple identity/ABI/member subcases. They prove guarded dispatch/reporting/cleanup with explicit HDC/runner fixtures, not actual device execution. Cases cover absent live targets in both modes; non-emulator and wrong ABI; omitted explicit flag retaining signature rejection; all four missing x86_64 members and a wrong ELF machine; identity changing before installation; accepted ordinary-install/full-report path; stale catalogs; host-report rejection; and cleanup after failure. No device, Flutter, native-build or Hvigor command was run by this worker for this mode.

## Windows HDC cleanup correction (2026-10-22)

The parent completed the first native ArkWeb catalog attempt against the current emulator: 481 cases executed, 443 passed and 38 failed. That attempt's semantic/device evidence remains preserved as `research/ohos-481-initial.*`; content/oracle failures are being investigated separately. Installation and the explicit unsigned-emulator route worked. The parent also observed a distinct host-driver cleanup failure: `fport rm` received its local/remote pair as one combined process argument. The actual Windows HDC rejected that form; a parent-issued ordinary removal with two separate arguments succeeded, after which the forwarding list was empty. This worker performed no device operation.

The driver now calls `device.call("fport", "rm", local, remote)` with the two original owned forwarding values as separate arguments. It still checks that the owned local port is absent afterward, reports cleanup failure as a failing exit, and independently requests only the singleton test ability's stop Want. It does not broaden cleanup to other forwards or the application bundle.

The dedicated regression runs the complete fixture driver on both semantic success and semantic failure. Its HDC adapter rejects a combined local/remote argument and accepts only the exact separate-argument tuple. Before the driver correction it fails, preserving evidence in `build/content/ohos-catalog-cleanup-regression-before.log`; after correction the complete Python suite passes **14/14 methods** in `build/content/ohos-catalog-driver-tests.log`. These are host driver regressions and do not turn the native attempt's 38 semantic failures into passes. Python syntax and owned-file whitespace/diff checks also pass; no device, Flutter or build command was run for the correction.

## Root runner requirements and outstanding CDP constraints

The root owns `scripts/run_examples.mjs`. Its `--ohos-cdp` mode must:

1. Attach to the already existing default CDP context/page. Do not create a browser context, create/close a target or close the connected native browser.
2. Find the exact bootstrap page; reject missing schema/backend/manifest, mismatched raw bytes/SHA256, incomplete case IDs, duplicate origins, mismatched host/native catalog payloads or absent oracle ownership before executing anything.
3. Navigate to each announced native `case.url`, reuse all existing topic-specific oracles and interaction stimuli, capture page errors/console/resources, isolate storage/cookies/window.name, and require the complete inventory. No `--limit` prefix is a full pass.
4. Record backend ArkWeb version/user agent, target/application/HAP identity, exact catalog/native hashes, IDs, assertion totals, native errors and every capability failure. Externally reported Chromium results are separate.
5. Treat unsupported CDP features, file-input injection, hover/mouse/input emulation, permission APIs, audio behavior, computed layout and iframe handling as real unresolved target differences. Do not turn unsupported transport into semantic passes. `page.viewportSize()` can be null on a persistent context; use actual `window.innerWidth` for the same layout assertion, or configure a verified viewport through supported CDP emulation. Existing oracle calls at CSS IDs using viewportSize must be reviewed.

Installed Playwright1.64.1 documents CDP as lower fidelity than its own protocol. ArkWeb's debug server may expose only page targets or a reduced CDP command set. First prove attach, Runtime.evaluate, navigation, request interception, locator/input actions and existing-page lifecycle before spending a full catalog run. If the browser-level Playwright attachment requires unsupported commands, a narrowly documented transport adapter is needed; a JavaScript-only evaluator cannot replace DOM/CSS oracles.

## Validation actually performed by this worker

- Preparation and `--check`: PASS for current301 examples,301 tutorials/301 lessons.
- Four meaningful preparation negatives: empty catalog, duplicate example, source-mismatched pair and missing lesson all rejected; atomic output copy remains byte-identical.
- Official installed SDK modified TypeScript4.9.5 compiler plus ArkTS1.1 linter, using its API/kit/component declarations: `CatalogHarness.ets` and `TestAbility.ets` have zero syntax/type/linter diagnostics. This is a direct SDK checker result, not a complete Hvigor module/HAP build.
- Real Hvigor debug `entry@ohosTest` HAP compilation, including the ArkUI page and singleton stop handler: PASS, final run15.064s. The first build caught `null` not assignable to `WebResourceResponse`; declaring `WebResourceResponse | null` fixed it. The earlier standalone SDK check used `strictNullChecks:false` and did not prove the real build contract. Full packaging is now separately proven. Existing Flutter SDK/deprecation/syscap warnings remain; no signingConfig is available.
- Real `CatalogHarness` logic transpiled through that SDK compiler and executed with resourceManager/crypto/response adapters:301 exact code responses, full bootstrap/tutorial/example round-trip,301 unique origins, query/fragment source identity, missing image404, external403, wrong method405 and corrupted rawfile SHA rejection all PASS. This verifies harness logic only, not ArkWeb/CDP execution.
- `git diff --check` for owned source paths: PASS.
- Host adapter rerun after environment fields:301 exact source/query responses and unique origins, exact full catalogs and public environment round-trip, missing404/external403/method405, data-URL native handling, and corrupt SHA rejection PASS. This remains host logic evidence, not native execution.
- `python scripts/test_ohos_catalog_driver.py -v`:7 test methods PASS, including multiple target/archive/report mutation subcases and failure-after-launch targeted cleanup. These use explicit host fixtures/mocks and cannot claim device execution.
- Official signer validation of the actual current unsigned test HAP: rejected as required. Cryptographic inspection of historical `build/ohos/hap/entry-default-signed.hap` succeeds, but its production content paths differ from current delivery and archive preflight rejects it; it is not used for current runtime evidence.
- Root independently reports the current desktop Chromium baseline:301/301 examples,1822 semantic assertions,0 mapping issues; full product86 tests and analysis clean. This worker did not rerun those checks.

Current hashes of staged catalogs (rerun after expansion): examples433365 bytes, SHA256 `784332d5217f9f644d69dca8596dfe96e26e67ce7413a8f1fff65d9113e2fa13`; tutorials752513 bytes, SHA256 `9841d2093c69b471bc1b928537ca0f083bf88b1c0730aaca21761c063f000616`.

Current compiled test artifact: `ohos/entry/build/default/outputs/ohosTest/entry-ohosTest-unsigned.hap`,161646241 bytes, SHA256 `5b8c000d60573cd3f56d5760b01e7c2ce98ff2bb568a4fe1cb81bbc1cab531cb`; `ets/modules.abc` SHA256 `197a837758a35fe0c5871abd0ab2d2fcc86bb579f259804e36b4fa544549fd37`; SDK compile version26.0.0.105, compatible API18, target API24. Built module is `entry_test` feature, `TestAbility` exported singleton. Packaged test catalogs and manifest match the above source/staging bytes. Build log: `build/content/ohos-catalog-hvigor.log`; full sanitized archive inspection: `build/content/ohos-test-hap-inspection.json`. These ignored outputs describe this301-item baseline only; expansion requires restaging and a new test build.

Read-only review of root runner: native path attaches to exactly one existing target, validates bootstrap/content before executing, uses per-case origins and storage reset, removes each case's listeners/routes, and disconnects without creating/closing native targets. Unsupported setup fails rather than becoming a semantic pass. Root has now validated and persisted the exact six public environment fields into reports; the driver consumes the same field names. Root reports19/19 Node contract tests, including the new environment boundaries. Root also owns the remaining nullable viewport correction through the markup-oracle owner; the new host-only viewport option does not alter the native driver. Real Fetch interception, permission/input support and CDP lifecycle behavior still need native evidence.

Not verified: packaged resource lookup in the running test module; debug endpoint availability and browser/CDP compatibility; signed current-artifact installation; native stop-Want UI teardown; actual Unix socket discovery; every OHOS semantic assertion. No device operation was performed by this worker. HDC had no connected target at the verified preflight attempt; later shared-target use must be coordinated through the parent. These remain explicit open gates and cannot be replaced by the successful host/build checks.
