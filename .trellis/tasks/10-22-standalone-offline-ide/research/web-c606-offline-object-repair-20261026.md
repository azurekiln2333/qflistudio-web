# C606 application gate and same-origin object repair

Status: C606 ran and FAILED. The revised source below has NOT been run.
Date: 2026-10-26, Asia/Shanghai. All eleven products remain in progress.

## Actual gate

Grant C606-Web180-20261026, ACCEPT608, final terminal RELEASE610, correction613.
[Final Job report](web-app-c606-20261026/job.json) records 113.072 seconds.
[Tests](web-app-c606-20261026/tests.stdout.log) end at 196 passes and 2 failures.
Both failures occur in production CSP browser checks at unchanged HTML137.
The object-src violation has an empty blocked URI and the author probe stays
at its initial waiting state. Neither engine reaches the HTML138 assertion.

Format: 11 files, zero changes. Full lib/test/integration_test/tool analysis:
No issues found. Product content audit: 481 paired topics, zero issues.
All validation Jobs and publisher are terminal with active-process count zero.
There was no forced cleanup. All 328 before/after input records match.
Core HEAD is 2f9039a3ba95449679b17257b0313c1ee3644a2c with live WIP;
this is not clean-published-core-only evidence.

The total window FAILED independently: ACCEPT608 to final RELEASE610 took
393.996 seconds against 180 allowed. The root relay occurred in a later model
round, 280 seconds after the runner publisher became terminal. A prospective
single-command relay wrapper is separate source work, not a passing gate.

## Root cause and candidate

The prior candidate permitted object data/Blob schemes but omitted self.
The actual shipped object initially has no data attribute. Chromium's
[csp_directive_list.cc](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/third_party/blink/renderer/core/frame/csp/csp_directive_list.cc)
(lines 702-709 observed from the primary source) checks an empty object URL
against the policy fallback URL. Its header identifies this fallback as the
object check without a source. This explains why checking only the eventual
Blob URL missed the initial policy decision. Current upstream source is not
proof for every installed ArkWeb version; a real rerun remains necessary.

The revised object-src is `'self' data: blob:`. It allows documents served by
the exact preview origin, including its port, as well as the intended local
schemes. It adds no arbitrary HTTP(S) source, wildcard or external host.
No catalog or tutorial bytes were changed for this repair.

The baseline browser fixture now loads a real same-origin object document.
A second loopback origin serves as the negative sentinel for object and embed.
Both must generate object-src violations before the browser abort route, with
zero escaped requests and zero sentinel hits. Report matching permits the browser
to strip a cross-origin path; it requires both rejection events and never
substitutes the abort route for browser enforcement. Existing external-domain object,
embed, script, style, image, frame, fetch, socket, form and report checks remain.
All five shipped-content assertions remain intact, including the exact HTML137
probe/content/bounds and HTML138's actual rendered SVG child frame.

## Frozen revised sources

```text
27697cdac9bf3e3f8f1c569f1b2999a0f068032163571282902826014858acdd  lib/services/web_project_config.dart
506c39720b1ea9badd7bf716c2b790cbb7e2b773ee1d896e34612a7f4c29d098  test/web_offline_browser_test.dart
fcfd2cb2880556375db36a56ad64223f42d85c29207483ac6cf1412815c944ce  scripts/test_web_offline_browser.mjs
```

Node syntax and scoped whitespace checks passed. Revised Dart format/analysis,
production browser behavior and the current full suite are UNRUN. C606's
analysis pass belongs to its earlier raw hashes, not this revised candidate.
The historical repair10 57/57 result is likewise not acceptance of this source.

## Prevention

Root-cause categories: implicit assumption and integration coverage gap.
Scheme matching alone did not establish empty-initial-object behavior.
The two-engine real-catalog regression exposed it. Keep that regression and the
same-origin/cross-origin object matrix. Do not rewrite the teaching example or
relax the loaded-document assertion to make the policy check pass.

A fresh named gate must verify format, both engine browser cases, full analysis
and complete current-source tests. Full481 desktop/mobile, native transport,
ArkTS/HAP, installed OHOS and debugger/owned-preview gates remain separate.
