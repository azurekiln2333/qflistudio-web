# Web analyzer follow-up review

Date: 2026-10-23 (Asia/Shanghai)

Status: the authorized narrow `.jsx` guard and regression are implemented and
passed in the coordinated repair8 host run on 2026-10-24 (20/20 analyzer cases).
The combined runtime/Tools gate remains failed; see the execution update below.

## Result and scope

No Java-style successful empty result without an actual parser invocation was
established. One concrete normal-callsite capability mismatch is confirmed by
source inspection: the shared controller labels `.jsx` as `javascript`, so the
Web provider sends JSX documents unchanged to its ordinary JavaScript backend.
A narrow Web-only unsupported-grammar guard was recommended and subsequently
implemented as recorded below; no shared-core change is required.

The initial review was read-only over the Web provider, native/stub availability
handling, existing tests, and shared editor controller/presentation. At that
stage only this report was added. A later explicit allocation authorized changes
to the Web provider, its existing analyzer test file, and this report. No
shared-core, device, browser, native compiler, build, Flutter/Dart test, or
Flutter/Dart analysis operation was performed. Review examples below are
source-derived traces, not fresh executable reproductions. Existing test
coverage is cited without claiming a new run or extending earlier acceptance
results. Line references in the review refer to the pre-fix hashes below.

## Pre-fix finding: normal `.jsx` requests reach the JavaScript-only backend

`lib/services/web_code_analyzer.dart:25` checks normalized absolute ownership.
Lines 34–49 validate snapshot membership, uniqueness, and active revision. Lines
56–63 normalize the requested language and reject unsupported language names.
The JavaScript branch at line 95 reads the extension only to choose `.mjs`
module grammar and `.js` classic/module fallback. It has no JSX grammar or
transformation and does not reject `.jsx`.

The real editor call chain is:

1. `../qfli_studio_core/lib/editor/editor_analysis_controller.dart:319` maps
   `.jsx` to `javascript`; line 177 supplies that language to the request.
2. The Web provider accepts `javascript`, obtains `active.text`, and dispatches
   it unchanged to JavaScript parsing. A document such as `component.jsx` with
   valid JSX `const view = <div />;` consequently reaches a backend that only
   understands JavaScript. There is no JSX capability-unavailable decision
   before parsing. Any syntax diagnostic from this path describes the wrong
   grammar, rather than establishing that the JSX document is invalid.
3. If the same `.jsx` document currently contains only JavaScript-compatible
   source such as `const value = 1;`, actual JavaScript compilation can succeed
   with empty diagnostics. This is a completed JavaScript parse, not evidence
   that the backend was skipped or that invalid JSX was accepted. However, the
   UI provides no JSX-coverage qualification.

These are source-derived branch predictions, not newly observed native results.

The user-visible acceptance chain is concrete: the controller sets
`checked = result.unavailableReason == null` at line 224, and
`editor_problems_bar.dart:9` displays `本地检查未发现问题` for a checked empty
result. The spec at `.trellis/spec/backend/web-code-analysis.md:102` requires
unsupported grammar to remain explicit. A JSX-unavailable outcome would also
avoid presenting valid JSX as erroneous JavaScript.

The Web product profile advertises `.html`, `.css`, and `.js`
(`lib/main.dart:36`), so this is not a missing promised JSX implementation. The
problem is that the shared editor can open a JSX path and routes it into the
installed Web analyzer without an explicit unsupported-grammar outcome.
`supportedFileExtensions` is used for runnable-file behavior, not as a guard in
the analyzer dispatch path. `.tsx` already becomes `typescript` and is rejected
by the provider's unsupported-language branch.

### API extension/language mismatch is not independently a confirmed defect

A direct provider request for `notes.txt`, `language: 'css'`, a matching owned
snapshot/revision, and source `a { color: red; }` reaches actual CSS parsing.
That behavior is confirmed by the source, but the public `CodeAnalysisRequest`
contract does not require `language` to match the extension or forbid an
explicit language override. It could be legitimate for a manual language mode.
This example therefore does not independently prove a false-clean or API
contract violation. The same qualification applies to a deliberately overridden
`.css` request analyzed as JavaScript.

Do not infer that every unknown file in an ordinary Web project follows this
path: the controller falls back to project type, and `web` is not an accepted
provider language. The concrete normal-callsite finding is the explicit `.jsx`
mapping above.

### Recommended Web-only change

Conservatively return explicit unavailable for known unsupported grammar paths
such as `.jsx` before JavaScript parsing. `.tsx` may be included defensively,
though its current ordinary route already rejects `typescript`. Preserve the
current language aliases, case normalization, and `.js`/`.mjs`/`.cjs` grammar
behavior. No shared-core mapping change is necessary.

Add focused regressions for `.jsx` requested as `javascript`, covering both valid
JSX and JavaScript-only contents; both should report the documented unsupported
JSX capability rather than claim full JSX coverage or emit JavaScript-only
syntax errors. The guard should work before native-backend availability affects
the result. Retain positive checks for case-insensitive supported extensions,
language aliases, `.htm`, `.mjs`, and `.cjs`.

A blanket extension/request-language matching rule is a separate product/API
policy decision. Adopt it only if explicit language override is ruled out or
documented accordingly. The available contract does not justify imposing it as
part of this finding. Existing tests cover unsupported `json` language, but do
not cover the normal `.jsx` routing mismatch.

## Other boundaries traced

| Boundary | Current behavior and evidence |
| --- | --- |
| Unsupported language | Provider lines 56–63 return explicit unavailable; existing test at `test/web_code_analyzer_test.dart:276` covers `json`. |
| Project and snapshot identity | Provider lines 25–49 require normalized owned paths, reject duplicate/foreign snapshots, and require the active revision; existing negative coverage begins at test line 255. Shared controller lines 151–185 capture the active file's owning root and same-root snapshots. |
| Unsaved source | Provider lines 65–69 parse `active.text`; no disk read supplies source. Shared controller line 183 captures observed editor text. Existing Web test at line 208 checks unsaved CSS over a clean saved file without overwriting it. |
| Stale results | Shared controller lines 248–267 require matching generation, active path/root, unique open files, current revisions, current controller text, and owner root. Shared tests cover changed buffers (line 135) and closing/switching roots (line 248). |
| Missing provider, timeout, exception | Shared controller lines 90–123 invalidate previous checked state and provide a reason; lines 236–240 preserve a failure as unavailable. Existing shared test at line 217 distinguishes timeout/provider failure from clean. |
| Missing or failed JavaScript backend | Native adapter lines 87–99 and 118–124 return explicit unavailable for missing library, limits, invalid status/range; only successful native compilation returns clean. Stub lines 3–8 always return unavailable. Web test at line 224 preserves independent HTML diagnostics together with QuickJS unavailability; native stack-failure coverage begins at line 379. |
| Unsupported parser grammar | CSS capability handling preserves explicit unavailable rather than false source errors; existing tests begin at line 119. HTML external scripts and data MIME scripts are intentionally outside source-only JavaScript coverage, as reflected by the test at line 243 and the current spec. |

No additional availability, snapshot, revision, or unsaved-source false-clean
gap was established in this review. This is a source-trace conclusion, not a
claim of fresh runtime validation.

## Reviewed source snapshot before the narrow fix

SHA-256 values were read on 2026-10-23:

| File | SHA-256 |
| --- | --- |
| `lib/services/web_code_analyzer.dart` | `9b5ba0a223aff5ef4cfc18e3d0e5fbdfa782828ac86c2ac65d8db515b86d1c68` |
| `test/web_code_analyzer_test.dart` | `2e30dcb67a1399bed704ede92263f5fb36d5011c03bddded90336444b4b175b7` |
| `../qfli_studio_core/lib/editor/editor_analysis_controller.dart` | `7b6e83e668c7eb3abe8b6b2b127bff39f52f32d5bb0c21fb0ca8f8b0113be20b` |

Primary contract reviewed: `.trellis/spec/backend/web-code-analysis.md:102`
requires unsupported language/grammar or unavailable backends to remain explicit
and reserves a clean result for actual completed parsing of the covered grammar.

## Authorized narrow implementation

`lib/services/web_code_analyzer.dart:65` now returns
`CodeAnalysisResult(unavailableReason: '当前未提供 JSX 离线语法后端')` when the
normalized language is `javascript` and the lowercased active extension is
`.jsx`. This uses the existing unavailable-result semantics before
`Isolate.run` or native library access. It adds no helper, changes no public
interface, and imposes no general extension/language consistency rule.

One regression test was added at `test/web_code_analyzer_test.dart:291`:

- Valid JSX `const view = <div />;` in `component.jsx` returns a JSX-specific
  unavailable reason and no ordinary JavaScript syntax diagnostic.
- JavaScript-only `const value = 1;` in uppercase `component.JSX` also reports
  unsupported JSX capability, covering case normalization and the previous
  JS-compatible clean-result branch.
- An explicit `notes.txt`/CSS request still parses successfully, preserving
  language override behavior outside the narrow guard.

The test supplies an intentionally absent native-library path and asserts the
JSX-specific reason, so it cannot accidentally pass merely because QuickJS is
missing. Removing the new guard would instead produce a QuickJS availability
reason or ordinary parser output. It was unrun at the source handoff; the
execution update below records its later actual result.

Static verification: `git diff --check` passed for the two Dart files; manual
diff review found only the four-line provider guard and one regression test.
No formatter, analyzer, test, browser, build, or native/device process was run.
That source-only handoff did not establish executable acceptance.

Post-edit SHA-256 values:

| File | SHA-256 |
| --- | --- |
| `lib/services/web_code_analyzer.dart` | `3b7f5db4f6d8b4bc0d6a7cfccb70cacff655c1932cb024893ecc5d7e48e6debc` |
| `test/web_code_analyzer_test.dart` | `84dd5920dad95c080ca1484c2e65a680786810f944369250da42cbc30cbcfcc4` |

## Root cause and prevention

The cause is a cross-layer capability assumption plus a test-coverage gap: the
core's generic `.jsx` language label lost the JSX distinction, while the Web
provider assumed every `javascript` request could use its JavaScript-only
backend. Snapshot and availability handling were not the cause. No earlier
failed code fix was attempted in this follow-up.

The prevention mechanism is the provider-owned unsupported-grammar decision and
the regression above, including the positive explicit-language override control.
The related `.tsx` normal route already becomes unsupported `typescript`; no
broader shared mapping or extension policy change is warranted by this trace.

Knowledge captured for the integrator's spec update: known `.jsx` paths analyzed
as JavaScript must be explicitly unavailable until a JSX backend exists; do not
infer a blanket extension/request-language matching contract from that rule.
Spec files were outside this worker's three-file edit allocation and were not
modified.

## Coordinated execution update, 2026-10-24

[Repair8 test log](web-runtime-repair8-tests.log) records all20 analyzer cases
passing, including the JSX guard and supported explicit CSS override. The run
also passed34 bridge/offline-policy/browser cases, then failed both Tools
lifecycle cases at the Clear gesture. [Scoped analysis](web-runtime-repair8-analysis.log)
returned exit1 with only two `avoid_print` infos in browser evidence logging;
neither info belongs to the analyzer implementation or regression.

All230 raw input hashes matched before/after. The [owned Job report](web-runtime-repair8-job.json)
records root82596 exit1, active0 and a successful terminal publisher releasing
to Java. This establishes the focused analyzer regression's host execution,
not a passing combined gate or a fresh native/device result. Subsequent fixture
and logging lint corrections remain unrun until the next named host window.

[Repair9](web-runtime-repair9-job.json) subsequently passed the same20 analyzer
cases and scoped analysis (`No issues found`), with all230 raw hashes stable.
It passed both Clear gestures but still ended54PASS/2FAIL because the2s strict
TCP refusal probes timed out after Stop. This newer result clears the logging
infos without establishing a passing Tools gate, full analysis or device proof.

[Repair10](web-runtime-repair10-job.json) then passes57/57 across six files,
including all20 analyzer cases, actual-profile named workspace and both Tools
lifecycle layouts. Scoped11-file analysis is clean and234 raw hashes match.
This closes the focused host regression while full app/native/device gates
remain separate.
