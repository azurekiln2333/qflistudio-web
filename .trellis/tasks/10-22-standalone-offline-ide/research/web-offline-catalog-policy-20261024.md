# Offline preview and shipped local catalog resources

> Historical candidate. C606 later executed it and failed both production
> browser cases at HTML137. The current candidate adds same-origin object
> permission and has not yet run. See [the C606 repair record](web-c606-offline-object-repair-20261026.md).

Status: **SOURCE REPAIR / EXPANDED BROWSER REGRESSION UNRUN**, 2026-10-24.
The earlier repair10 result57/57 is retained for its original frozen inputs;
it is not a pass for the candidate changes recorded here. No new Flutter,
Chromium, SDK, native, HAP or device gate has run for this repair.

## Verified behavior gap and decision

The production response policy in
[WebProjectConfig](../../../../lib/services/web_project_config.dart) explicitly
allowed only same-origin/inline styles, same-origin connections and no objects.
Those more-specific directives overrode the default local data/Blob permission.
Read-only inspection found real shipped inputs affected by the policy:

| Shipped ID | Actual local resource | Independent expected observation |
| --- | --- | --- |
| HTML027 | `data:text/css` stylesheet | Body blue `rgb(26, 115, 232)` and sans-serif |
| HTML097 | Blob stylesheet | `.lazy` gray `rgb(107, 114, 128)` and italic |
| HTML137 | Blob HTML object | Loaded `#inner`, exact author probe and240x80 object |
| HTML138 | data SVG embed | Loaded80x40 SVG with blue32x32 circle |
| JS017 | Blob JSON passed to `fetch` | `#out` contains `WebForge 本地数据` |

Root explicitly extended the repair from styles to the verified object/Blob
cases under the original all-examples/offline requirement. The policy now uses
`style-src 'self' 'unsafe-inline' data: blob:`, `connect-src 'self' blob:` and
`object-src data: blob:`. Objects do not gain ordinary same-origin/HTTP(S)
permission; scripts do not gain data URL permission. No author source or catalog
is modified. This is no claim of full system-browser navigation isolation.

The scope is exactly the policy file,
[Dart production-engine test](../../../../test/web_offline_browser_test.dart)
and [browser assertions](../../../../scripts/test_web_offline_browser.mjs).
The existing runtime/server APIs and private Job primitive are unchanged.

## Regression source and evidence boundary

The Dart test selects the exact five IDs from current
[examples.json](../../../../assets/content/examples.json), writes each decoded
code string unchanged to a fresh temporary project and runs the same assertions
through WebForge and real Nginx. Browser checks observe styles, loaded embedded
documents/SVG and the authored Blob fetch result. The SVG check observes the
actual opaque child frame; a correctly sized empty embed is insufficient.

All existing external script/style/image/frame/fetch/WebSocket/form checks and
the real report/WebSocket sentinels are retained. Two distinct external object/
embed hosts must trigger `object-src` violations, with zero requests escaping
to the abort route. Legitimate data URLs have no network origin and are allowed
by that guard; the browser must still enforce the response policy itself.

Frozen source SHA256 values:

```text
a7e0b04e1015f6bfb1d750ef014480c421ee78505461e46317f8108c5d0180df  lib/services/web_project_config.dart
9248c360042de71bfdd3e77ce0d99a894f1f3faf0dd9d93c9a4f50086dc55d80  test/web_offline_browser_test.dart
7d81c980ef365122a5803f7dcee61a1b12a3d738b2acb12abc65463d0d310ebe  scripts/test_web_offline_browser.mjs
```

`node --check` passed without executing the script or browser. Dart format,
analysis, the expanded production-browser tests, policy mutation controls and
complete current app/catalog gates remain **UNRUN** pending a fresh named
host handoff. Actual results must retain current source hashes, both real engine
identities, the five catalog observations, external violations and cleanup.
Root and the independent source reviewer found no further material source/API
issue; actual SVG child-frame exposure and timing remain runtime checks.
The [source-only preflight](web-source-ready-20261024.json) retains exact hashes,
five catalog code digests,327 app inputs and49 native immutable inputs. Python
AST, PowerShell parsing, Node syntax, whitespace and212 local links passed;
no browser, Flutter, compiler, HAP or device execution followed from those checks.

## Bug retrospective

1. **Root cause: implicit assumption plus coverage gap.** A specific CSP directive
   does not inherit the schemes listed under `default-src`. The positive
   production-policy fixture only used a conventional local stylesheet.
2. **Why earlier checks missed it.** The exhaustive host catalog validates
   documents under its own harness, while the production browser test proved
   external blocking. Neither combined the real shipped local resource forms
   with the production response headers. No executed failed/fixed browser run is
   claimed for this source review.
3. **Prevention.** Keep both unchanged catalog positives and real external
   negatives in the production-engine test. Removing any required local scheme
   must fail its actual behavior check; removing an external restriction must
   expose a forbidden request/violation failure.
4. **Systematic expansion.** The audit also distinguished JS142 Blob byte APIs
   from actual fetch, and retained JS148's existing Blob worker permission.
   No unrelated scheme, catalog rewrite or browser API mock was added.
5. **Knowledge captured.** The exact schemes, five IDs and observed behavior
   are now part of the [runtime contract](../../../spec/backend/web-runtime.md).
   Fresh execution is mandatory before publication or acceptance.

## Primary policy reference

The [CSP3 source-expression matching algorithm](https://www.w3.org/TR/CSP3/#match-url-to-source-expression)
defines explicit scheme matching and excludes Blob URLs from the `'self'`
branch. The [policy inheritance section](https://www.w3.org/TR/CSP3/#security-inherit-csp)
describes inheritance for local embedded documents. These primary sources were
read on2026-10-24; specification rules do not replace actual Chromium or OHOS
execution evidence. The change grants local resource schemes only and leaves
owned-preview, native authorization and complete offline isolation gates open.
