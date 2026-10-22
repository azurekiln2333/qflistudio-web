# Offline curriculum verification

## 1. Scope / Trigger

Apply to authored curriculum modules, `emit_content.py`, semantic oracles,
`run_examples.mjs`, OHOS test-only harness and current-artifact evidence.

## 2. Signatures

```text
python -X utf8 scripts/emit_content.py
python -X utf8 scripts/test_emit_content.py
python -X utf8 scripts/audit_web_content.py --product --report <path>
node scripts/run_examples.mjs --report <path> [--viewport 390x844]
node scripts/run_examples.mjs --ohos-cdp <local-forward-URL> --report <path>
python scripts/prepare_ohos_catalog.py [--check]
python scripts/run_ohos_catalog.py --device <exact-live-target> --production-hap <path> --test-hap <path> --report <path> [--run]
  [--unsigned-emulator]
```

Expansion modules export `COVERED_IDS` and
`assertExpansionExample(page, example, addCheck) -> boolean`.

## 3. Contracts

- Preserve stable IDs and subject `language`; every executable import remains
  `type: html`. Each topic has a distinct complete document, real explanations,
  expectations and exercise. Derive examples and tutorial code from one source.
- Inject one `webforge-check` marker at a structural closing body/html tag.
  Skip comments, quoted attributes, script/style/raw-text/RCDATA and template
  content, recognizing case and whitespace. Preserve all other source bytes.
  A script string containing `</body>` cannot become a marker insertion point.
- Require exactly one semantic oracle per example. Assert actual DOM, computed
  style, console values or interactions; a marker or nonempty output is not a
  semantic pass. Every lesson must map to identical example code after stripping
  the known marker. Reject duplicate IDs/bodies and missing mappings.
- Block every external request. Preserve exact authored documents and missing
  assets; no runner-provided helper fixture may make an incomplete lesson pass.
  Only the exact intentional missing-image teaching path has an exception, with
  a semantic oracle proving its broken-image behavior.
- Host runs own independent contexts. OHOS attaches to one existing test-only
  ArkWeb page, never creates/closes a native target/context. Its incognito Web
  receives one isolated origin per case. Clear cookies, per-origin storage and
  window.name, then detach only this run's listeners/routes. Native content is
  supplied by the test resource interceptor, never the Node host.
- Bootstrap is at `http://127.0.0.1:19999/__qfli_catalog/bootstrap` and exposes
  `__QFLI_OHOS_CATALOG__`: schemaVersion 1, backend `arkweb-test`, runId,
  manifest, examples, tutorials, cases and public environment. Manifest has exact
  UTF-8 byte lengths/SHA256 and counts. Verify its source and parsed payload.
  Cases use distinct `http://127.0.0.1:20000+index/index.html` origins.
- Environment identifies bundle `com.azurekiln.qfli.webforge`, module
  `entry_test`, ability `TestAbility`, plus osFullName, integer sdkApiVersion
  and deviceType. Persist only these public fields; do not collect private IDs.
- The production source set never enables catalog CDP. Only the test ability
  handles `qfliCatalogCdp`, port and singleton `qfliCatalogStop` teardown. The
  device driver verifies the exact live target, signatures/profile/bundle,
  current source/staging/main+test HAP bytes and complete native runner report.
  Coordinate a target's exclusive window; remove only this driver's own new
  forward and stop only its test ability, including after partial launch failure.
- Signature/profile verification is the default. Explicit `--unsigned-emulator`
  permits ordinary unsigned installation only after the selected live target
  reports `const.product.model=emulator` and `uname -m=x86_64`, checked again
  before installing. Require real x86_64 ELF64 Flutter/app/syntax/nginx libraries.
  Record `signingMode=unsigned-emulator`, public emulator identity and
  `signature.verified=false`; this provides no signed or physical-device proof.
  Do not change device security/enrollment or use another product's identity.
- JSON reports persist catalog/code hashes, every assertion/log/resource error,
  runtime/browser/environment and complete/partial status. `--limit`/`--filter`
  are partial evidence. Host `--viewport` never overrides a native viewport.
  Native `page.viewportSize()` may be null; use actual `window.innerWidth` for
  responsive expectations. Unsupported transport or platform behavior stays a
  failed/open gate, with no host fallback.

## 4. Validation & Error Matrix

| Condition | Outcome |
| --- | --- |
| Duplicate/unknown option or missing argument | Reject before execution |
| Missing or overlapping semantic oracle | Entry fails |
| External/broken unexpected resource, page error | Entry fails |
| Stale HAP/hash, wrong ability, reused origin | Native bootstrap rejected |
| Missing HDC target, invalid/stale signature/profile | No install/launch/forward |
| Browser/partial/empty-assertion report supplied as OHOS | Driver rejects |
| Driver cleanup fails | Failing exit; record remaining resource |
| Unsigned current HAP builds | Packaging evidence only; installation stays open |

## 5. Good / Base / Bad Cases

- Good: all current IDs execute semantic checks on ArkWeb with exact current
  signed archives and source hashes, recording real native limitations.
- Base: full host catalog passes and current unsigned HAP compiles; record
  those separately while device execution remains open.
- Bad: call 301 existing entries 180 newly added entries, accept a 60-case filter
  as the full catalog, or substitute an older signed archive after editing code.

## 6. Tests Required

Run emitter tests, full schema audit and the entire semantic catalog. Cover
desktop/mobile responsive branches and mutation checks for repaired oracles.
Run `node --test scripts/catalog_device_contract.test.mjs` and
`python scripts/test_ohos_catalog_driver.py`. Prove rejection of changed bytes,
wrong identity, external/reused origins, unsigned/stale HAPs, missing live
targets and host/partial reports; assert no device mutation before preflight
and targeted teardown after launch failure. Rebuild/stage after catalog edits.
Inspect current production/test archives, native ABI/exports and source
separation. Full signed native execution is a separate mandatory gate.

## 7. Wrong vs Correct

Wrong: `source.replace('</body>', marker + '</body>')` also edits a literal
inside JavaScript and can inject multiple markers. Correct: tokenize structural
closing tags, insert once, and regression-test script/comment/template decoys.

Wrong: treat signer exit 0, old signed HAP, or desktop Chromium as an OHOS pass.
Correct: verify explicit signer success/profile identity, exact archive content,
fresh installation and exhaustive native semantic results independently.
