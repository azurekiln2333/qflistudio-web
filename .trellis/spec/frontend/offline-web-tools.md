# Offline Web tools

## 1. Scope / Trigger

Apply when changing `WebToolsOverview`, `lib/widgets/web_tools/`, or the
`web_source_scan`, `web_markup_inspector` and `web_css_tools` services. These
product-owned tools inspect local source; shared editor analysis and native
preview remain separate contracts.

## 2. Signatures

```dart
WebToolsOverview({required ProjectStore store, VoidCallback? onOpenTerminal});
WebSourceInspectorInlineView({required ProjectStore store});
WebMarkupCheckInlineView();
WebCssToolsInlineView();

Future<WebDocumentScan> WebMarkupInspector.scanDocuments(String rootPath);
Future<WebDocumentInspection> WebMarkupInspector.inspectFileAsync(
    String documentPath, {required String rootPath});
WebDocumentInspection WebMarkupInspector.inspectFile(
    String documentPath, {required String rootPath});
WebDocumentInspection WebMarkupInspector.inspectSource(String source, {
  required String documentPath, required String rootPath,
  bool Function(String)? exists, String? Function(String)? readText,
});
List<WebFinding> WebMarkupInspector.structureFindings(String source);
List<WebFinding> WebMarkupInspector.accessibilityFindings(String source);
String WebMarkupInspector.formatHtml(String source);

CssColor? CssColor.parse(String text);
double? CssColor.contrastRatio(CssColor first, CssColor second);
CssStylesheet WebCssTools.parse(String source);
List<WebFinding> WebCssTools.diagnostics(String source);
List<CssColorUse> WebCssTools.findColors(String source);
List<CssSpecificity> WebCssTools.specificities(String source);
List<CssDuplicateProperty> WebCssTools.duplicateDeclarations(String source);
CssBoxModel? WebCssTools.boxModel(List<CssDeclaration> declarations,
    {double? contentWidth, double? contentHeight});
String WebCssTools.format(String source);
```

`WebSourceLocation` has 1-based `line`/`column` and a 0-based UTF-16 `offset`.
`WebFinding` carries `code`, `message`, `location` and error/warning/hint severity.
`WebDocumentScan` returns `documents` and `truncated`. Inspection returns
`documentPath`, `rootPath`, `references`, `findings`, `cssFiles` and derived counts.

## 3. Contracts

- Render server, codec, resource, CSS and markup controls directly in Tools.
  Keep the server/codec views in finite-height embedded panels and the controls
  column in one retained sliver child: scrolling must not dispose a running
  preview. Terminal uses `onOpenTerminal`; no extra Web feature-hub route.
  Render shared cards with `ToolsGridSliver(tools: commonTools)` from
  `package:qfli_studio_core/pages/tools_grid.dart`, with product-owned
  `SliverPadding`; keep shared card geometry and actions in the core widget.
- Tools expose no external fetch or login. Source inspectors/formatters/codecs
  do not write project files; existing server settings persist validated config
  under the state-management contract. Resource inspection classifies URLs
  without loading them. Preview remains loopback-only; the offline product hides
  arbitrary HTTP/proxy-entry controls.
- Discover `.html`/`.htm` asynchronously, without following directory links or
  entering `.git`, `.qfli`, `.dart_tool`, `node_modules` or `build`. Stop at the
  200-document / 10,000-entry discovery budgets and surface `truncated`.
- UI disk inspection calls `inspectFileAsync`, whose synchronous disk/parser
  work runs through `Isolate.run`. Never call synchronous recursive listing or
  file inspection from build/setState. Check `mounted` and request generation
  after each await; invalidate on selection/disposal and detach store listeners.
- Confine the document and resource paths to the canonical project root,
  resolving existing ancestors so a missing child of an escaping symlink is
  rejected too. Follow stylesheet links and local CSS imports with cycle
  suppression; do not decode icons/other links as text stylesheets.
- Disk HTML/CSS files have a 1 MiB per-file limit; `inspectSource` also rejects
  more than 1 Mi UTF-16 units. Inspect at most 500 references and 32 stylesheets.
  Report incomplete scans instead of calling them clean. `base href` is detected
  as an unresolved inspection boundary. Dynamic script requests are outside this
  static check and must be assessed in preview logs.
- Reference kinds are localFile/siteRoot/missing/inline/external/escaping/invalid.
  Missing, external, escaping, invalid, error or incomplete results suppress
  `isOfflineClean`. References from CSS files retain their stylesheet `origin`
  and its own source coordinates. Entity decoding, data-URI srcset commas, CSS comments and
  quoted URL-looking content must preserve correct classification.
- HTML/CSS findings are literal-source inspections, not a full grammar/compiler
  verdict. Pasted CSS has a 128 Ki UTF-16-unit service limit; both source fields
  set `maxLength` to 131072. CSS parsed findings and colors each cap at 200;
  diagnostics may add an unterminated-comment finding. Output widgets
  display at most 30 findings, 40 references or 24 CSS result rows with omissions
  indicated where supported; discovery and inspection limits remain explicit.
- Formatting produces a separate copyable result. Preserve script/style/pre/
  textarea text, mixed/inline spacing and root inline fragments. Keep malformed
  HTML tag structures with unmatched/mismatched scanned tags and unsafe root
  fragments unchanged. A raw-text close needs the complete tag
  name followed by HTML whitespace, `/` or `>`; `</scripture>` is script text.
  CSS formatting retains scopes, at-rules, comments, string bytes and custom
  property case; input with scanner diagnostics, oversized input and custom-property block values
  retain original source. Never rebuild a formatter from the flat inspection
  rule list.
- Colors cover hex, RGB/HSL, 148 named colors and transparent; reject unsupported
  functions and nonfinite/malformed numbers. Inspect declaration values, not
  selectors, strings or URL fragments. Contrast requires opaque colors.
- Compare specificity lexicographically by `(ids, classes, types)`, including
  functional-selector maxima and zero-weight `:where`. Nesting `&` is explicitly
  “依赖嵌套父规则，未计算”. Box calculations model supported single-rule physical
  shorthand/longhand declarations and important/order; sum only px/unitless zero
  with effective border style. They do not compute cascade, logical properties,
  variables or browser layout. Duplicate declarations do not imply the last
  value wins: validity and important still apply.

## 4. Validation & Error Matrix

| Condition | Required behavior |
| --- | --- |
| Missing/unreadable/non-UTF-8 document | Finding, empty result as appropriate; no throw or clean verdict |
| Outside document or escaping resource/symlink | Reject before content read; error and no stylesheet traversal |
| Missing local resource | `missing-resource`; clean=false |
| External URL | `external-reference`; no request; clean=false |
| Document/reference/stylesheet limit or `base href` | Explicit incomplete finding; clean=false |
| Discovery budget reached | `truncated=true`; visible discovery-cap message |
| Unreadable/oversized stylesheet | Finding; remaining bounded scan continues; clean=false |
| Selection changed/disposed during await | Ignore stale result; no late setState |
| Unsupported color / translucent contrast / non-px sum | Null/unavailable result; no guessed numeric answer |
| Formatter detects unsafe/unsupported input | Preserve source; never discard tokens to obtain output |

## 5. Good / Base / Bad Cases

- Good: inspect a document whose local stylesheet imports another stylesheet;
  report a missing image or external URL with its stylesheet origin and line.
- Base: paste `.a{color:red}` into the inline CSS panel and copy a separately
  formatted result; the project file remains unchanged.
- Bad: display “可直接离线预览” after skipping a large stylesheet, follow a
  symlink outside the root, or insert a newline between root spans and change
  `AB` into `A B`.

## 6. Tests Required

```text
flutter test --no-pub --concurrency=1 test/web_css_tools_test.dart test/web_markup_inspector_test.dart test/web_tools_overview_test.dart test/web_tools_navigation_test.dart test/web_tools_page_test.dart
flutter analyze --no-pub lib test
```

- Services: assert source coordinates, missing/error/incomplete clean=false,
  real symlink confinement, icon/UTF-8 failure handling, CSS import-chain origin,
  excluded-directory discovery and the 201-document truncation case. Snapshot
  tests inject both `exists` and `readText` to avoid accidental real disk reads.
- CSS: verify named-color values, malformed functions, string/comment/URL/selector
  exclusions, namespace/functional/legacy/nth-child specificity and an ID versus
  101 classes. Cover important/order, border style, zero/non-px and border-box
  minimums. Preserve CSS scope/string/custom-case bytes and idempotence.
- HTML: compare raw/script/pre/textarea and mixed/root inline text before/after
  formatting. Test raw-tag prefix decoys and mixed-case/whitespace/slash closes.
- Widgets: drive actual inline results and terminal callback, no Web hub route;
  test real project load/removal, disposal while scanning and 320px/2x text.
  Advance PageView animation, then use `tester.runAsync` for real I/O/isolate
  work while observing the public busy indicator before `pumpAndSettle`.
- Browser semantics stay outside widget suites. Task fixture
  `web-tools-format-fixture.dart` generates output with production services;
  `web-tools-browser-check.mjs` compares executed script, computed styles and
  rendered fragments while aborting/recording requests. Require zero requests.
  Host results do not prove OHOS or whole-product completion; current status is
  recorded in `research/web-tools-independent-review.md` under the active task.

## 7. Wrong vs Correct

Wrong: recursively `listSync` the entire tree, then filter `node_modules` and
stop after 200 HTML matches; flatten parsed rules to format CSS; rank selectors
as `ids * 10000 + classes * 100 + types`.

Correct: skip excluded directories before entering them, await bounded discovery
and background inspection, and guard results with request generation. Format
original tokens with preserved scopes/raw content, and use
`CssSpecificity.compareTo` for lexicographic ordering.

```dart
final generation = ++_generation;
final result = await WebMarkupInspector.inspectFileAsync(path, rootPath: root);
if (!mounted || generation != _generation) return;
setState(() => _inspection = result);
```
