# Follow-up research: csslib / html parser integration vs. the existing scanners

Date: 2026-10-22 · Status: **research only** — no source, test, build or spec change was
made while producing this document. Product writes are on hold with the native checker.

Scope of the question: if WebForge adopts `package:html` and `package:csslib`, can they
reuse the existing `WebSourceIndex` / `WebFinding` contract instead of duplicating the
scanners in `lib/services/web_source_scan.dart`, `web_markup_inspector.dart` and
`web_css_tools.dart`?

## 0. Verified starting state

`pubspec.yaml` (working tree, **not** written by me) already declares:

```yaml
  html: ^0.15.6      # resolved 0.15.7
  csslib: ^1.0.2     # resolved 1.0.2
```

`pubspec.lock` marks both as `direct main`. Nothing in `lib/`, `test/`, `integration_test/`
or `tool/` imports them yet, and `qfli_studio_core` does not use them (core only declares
`xml`). Both packages plus their transitive deps (`source_span` 1.10.2, `petitparser`
7.0.2) are present in the local pub cache, so an offline build does not need the network —
this matters because the product is offline-only.

Everything below was measured by running throwaway probe programs in `%TEMP%` against the
repo's own `.dart_tool/package_config.json`. No repository file was executed or modified.

## 1. Answer in one line

**Yes, they can share the result contract, but they cannot share `WebSourceIndex` — and
they should not replace all of the scanners.** Adopt them as an *additional, authoritative
diagnostics source* behind one adapter that converts `SourceSpan` → `WebSourceLocation`;
keep the existing scanners for everything the packages do not produce (value inspection,
a11y, `srcset` candidates, CSS `url()`/`@import` resolution, colour/box-model/specificity).

## 2. What the packages actually give you (measured)

### 2.1 `html` 0.15.7

```dart
final parser = HtmlParser(source, generateSpans: true);
final doc = parser.parse();
parser.errors;                 // List<ParseError>, populated after parse
doc.querySelectorAll('img');   // DOM with per-node spans
```

Probe on a deliberately broken document:

```
errors: 2
  expected-doctype-but-got-start-tag @ 1:1 :: Unexpected start tag (html). Expected DOCTYPE.
  expected-one-end-tag-but-got-another @ 7:1 :: Unexpected end tag (body). Missing end tag (div).
  <title> span 23-30 start 2:1
  <img>   span 55-72 start 5:1   @src=a.png valueSpan=65-70
  <div>   span 73-78 start 6:1
  <span>  span 78-84 start 6:6
```

Findings that change the design:

- `ParseError` exposes `errorCode`, `span`, `line`, `column` (0-based) and a human
  `message` resolved from `errorMessages`. This is **spec-accurate HTML5 error reporting**,
  i.e. a real superset of my `unclosed-tag` / `stray-end-tag` heuristics: my hand-rolled
  stack reported "`<div>` 在 `</body>` 之前没有闭合"; the package reports
  `expected-one-end-tag-but-got-another` with the same position **plus** a DOCTYPE finding
  my scanner never had.
- `Node.sourceSpan` and `Node.attributeValueSpans[name]` give exact value offsets, so a
  finding can point at the *attribute value* (`65-70`) instead of the tag start — a real
  improvement over my current `token.start` anchoring.
- `element.attributes` is the browser-normalised attribute map, so quoting, `>` inside
  values, duplicate attributes and raw-text (`<style>`, `<script>`) handling stop being my
  problem. `<style>` content is available as `style.text` (verified).
- It does **not** do accessibility, `srcset` candidate splitting, `url()` resolution or
  resource existence. Those stay mine.

### 2.2 `csslib` 1.0.2

```dart
final errors = <css.Message>[];
final sheet = css.parse(source, errors: errors);
```

Probe on `.a { color: #fff; color: #000; } @media (...) {...} .c { color blue; }`:

```
messages: 1
  MessageLevel.severe 3:12:parsing error expected :
  rule [.a] span 0-2 @ 1:1
     color: … span=5 @1:6
     color: … span=18 @1:19
  rule [.c] span 84-86 @3:1
     color: … span=89 @3:6
```

Findings that change the design:

- `parse(..., errors:)` produces `Message(level, message, span)` and `Message.describe`
  already renders `line:column:message` (0-based internally, +1 for display). It caught
  `color blue` as `parsing error expected :` — a real superset of my
  `declaration-without-colon` / `unclosed-block` scanner, with proper `MessageLevel`.
- AST nodes carry `SourceSpan`: `RuleSet.span`, `Declaration.span`,
  `SelectorGroup.span.text` (the selector text is **not** a `Selector.text` property —
  `Selector` exposes `simpleSelectorSequences`; use the span text or a `SimpleSelector`
  walk). `ImportDirective.import` gives `@import` targets.
- It gives **no** duplicate-property analysis, no specificity, no colour conversion, no
  box-model expansion, and no `url()` extraction — my value-add tools are unaffected.
  Declaration values come back as opaque `Expression`/`Expressions` nodes, so
  `CssColor.parse` on the span text is still the way to convert colours.

### 2.3 Cost (this is the constraint that shapes the recommendation)

| Input | Operation | Time |
| --- | --- | --- |
| 127 KB HTML (2 000 `<div>`/`<img>`/`<p>`) | `HtmlParser(..., generateSpans: true).parse()` | **72 ms** |
| same | `parse()` without spans | 35 ms |
| 75 KB CSS (2 000 rules) | `css.parse()` | **54 ms** |

For comparison the current hand-written scanners are sub-millisecond on the same inputs
(they are single-pass over the literal text). So:

- Do **not** swap the live-as-you-type panels (`WebCssToolsInlineView`,
  `WebMarkupCheckInlineView`) over to these packages: 50–70 ms per keystroke on a phone is
  a dropped-frame machine.
- Do use them for **on-demand** actions (a "深度检查" button, project-level document
  inspection, pre-export validation) with a debounce/explicit trigger, and a size cap.

## 3. Reuse vs. duplicate, concretely

`WebSourceIndex` exists to turn a raw `offset` into `line:column`. The packages never give
an offset-only result — every `ParseError`, `Message` and node carries a `SourceSpan` whose
`start` already has 0-based `line`/`column` (and `offset`). Therefore:

| Concern | Recommendation |
| --- | --- |
| `WebSourceLocation` / `WebFinding` / `WebFindingSeverity` | **Reuse unchanged.** This is the shared contract; UI (`WebFindingList`), capping and severity colours stay. |
| `WebSourceIndex` | **Keep, do not duplicate.** It remains the only mapping for my own scanners (`findColors`, `srcset`, `url()`, a11y, box model). Do **not** route package spans through it — that would be a second, lossy mapping. |
| Span → contract adapter | **New, single, ~20 lines** (`WebSourceLocation.fromSpan(SourceSpan)` = `start.line + 1`, `start.column + 1`, `start.offset`), plus `ParseError`/`Message` → `WebFinding` mappers. One place, unit-testable, no UI change. |
| HTML tag/structure scanning | **Replace** `WebMarkupInspector.structureFindings` with `html`'s `parser.errors` for the error classes the package reports. Keep my optional-end-tag tolerance only if it produces findings the package doesn't (verify per error code; otherwise delete it and its tests). |
| HTML reference extraction | **Prefer `html` DOM traversal** (`attributes`, `attributeValueSpans`, `style.text`) over my tokenizer; keep `_resolve` (classification, existence, escaping) and `_srcsetCandidates` — the package does neither. |
| CSS structure diagnostics | **Replace** `WebCssTools.diagnostics`/`parse`-based findings with `css.parse(errors:)`; keep `CssStylesheet`/`CssRule` **only** if the UI still needs `declarations` for box model — otherwise read them from the AST and drop my parser. |
| CSS value tools (`CssColor`, contrast, specificity, duplicates, box model) | **Keep** — nothing in `csslib` provides them. Duplicates/specificity/box model must stay hand-written; only their *rule/declaration enumeration* would switch to the AST. |
| Colours inside strings/comments | `csslib` strips comments and tokenises strings correctly, so `isInsideQuotedRun` + `stripCssComments` become unnecessary **for the AST path**; they are still needed for the offset-preserving raw-text path. Prefer the AST and retire them if the raw path goes away. |
| `formatHtml` / `format` | **Keep** — neither package ships a formatter for this purpose (`csslib` has `css_printer.dart`/`tree_printer.dart`, which print a *normalised* tree and would destroy the user's formatting; my 重排缩进 is an intentional, documented rewrite). |
| Accessibility findings | **Keep** — `html` has no a11y checks. |
| Offline gate | **Keep** — both packages are pure Dart, no IO, no network; nothing changes for R10. |

Net effect if adopted as recommended: roughly **−150 lines** of hand-rolled tag/declaration
scanning deleted, **+~40 lines** of adapter/mapping, no change to `WebFinding`, no change to
any widget, and one new dependency already present in `pubspec.yaml`/`pubspec.lock`.

## 4. Recommended sequencing (when the root reopens product writes)

1. Add `lib/services/web_parser_adapter.dart` (span/error mappers only) + unit tests that
   assert `line:column` parity with `WebSourceIndex` on the same inputs. This is the
   contract test that proves the two mappings agree — write it *before* deleting anything.
2. Switch `WebMarkupInspector.inspectSource` reference extraction to the `html` DOM, keep
   `_resolve`/`srcset`/CSS following. Re-run the 12 markup tests; expect identical
   classifications.
3. Add package errors as an **extra** finding source (dedupe by `(code, offset)`), keeping
   my findings until the error-code mapping is proven, then delete the superseded ones.
4. Only then consider replacing `WebCssTools.parse` rule enumeration with the `csslib` AST,
   keeping `CssColor`/specificity/duplicates/box-model logic and their tests intact.
5. Gate all package parsing behind the on-demand action (size cap + explicit trigger), not
   the keystroke path.

Rollback is trivial: each step is one service file plus its tests, and the adapter is
additive.

## 5. Verified official references

Every URL below was fetched during this research (HTTP 200) and the quoted claim was read
from that page. This section also **corrects** the reference table in
`research/web-tools-results.md`: that table's VS Code/JetBrains feature *names* were
paraphrases without sources; the wording below is what the pages actually document.

| Claim used in the implementation | Verified source | What the page actually says |
| --- | --- | --- |
| HTML diagnostics / embedded validation | <https://code.visualstudio.com/docs/languages/html> | "The HTML language support performs validation on all embedded JavaScript and CSS" (`html.validate.scripts`, `html.validate.styles`); also documents formatting and Emmet. It does **not** use the phrases "Cannot find file" or "unclosed tag". |
| CSS lints incl. duplicates, box model, colour | <https://code.visualstudio.com/docs/languages/css> | Lint table contains `duplicateProperties` — "Warn about duplicate properties in the same ruleset"; `boxModel` — "Do not use width or height when using padding or border"; `hexColorLength` — "Warn when using hex numbers that don't consist of three or six hex numbers"; `argumentsInColorFunction`; `emptyRules`; `zeroUnits`. |
| Problems panel severity model | <https://code.visualstudio.com/docs/getstarted/userinterface#_problems-panel> | Documents the Problems panel as the place errors/warnings are surfaced. |
| CSS specificity shown for selectors | <https://www.jetbrains.com/help/webstorm/css.html> | "For selectors, WebStorm also shows their **specificity**." (links to W3C Selectors 3) |
| CSS colour preview / change colour | same page | "WebStorm shows preview for absolute, relative, and mixed colors", gutter icons, "Toggle color preview", "Change color" intention. |
| WebStorm inspection workflow | <https://www.jetbrains.com/help/webstorm/code-inspection.html> | Inspections + severities + Problems view. **Note:** the public help does not document per-inspection names such as "Unresolved file reference" or "Duplicate property", so the earlier table's use of those names is unsupported. |
| HTML editing / link-related assistance | <https://www.jetbrains.com/help/webstorm/html.html> (canonical: `editing-html-files.html`) | HTML editing reference; no "unresolved link" inspection name is documented. |
| CSS colour value syntax | <https://developer.mozilla.org/en-US/docs/Web/CSS/color_value> | Canonical reference for `#hex`, `rgb()`, `hsl()` and named colours. |
| Specificity, `:where()`, `:not()`, `:is()` | <https://developer.mozilla.org/en-US/docs/Web/CSS/Specificity> | "`:where()` and its parameters aren't counted … their value is 0-0-0"; "`:not()`, `:is()`, `:has()` … pseudo-classes themselves add no weight. The parameters in these selectors, however, do. The specificity weight of each comes from the selector parameter in the list of selectors with the highest specificity." — exactly the implemented algorithm. |
| Void elements | <https://developer.mozilla.org/en-US/docs/Glossary/Void_element> | "A void element is an element in HTML that cannot have any child nodes… Void elements only have a start tag; end tags must not be specified." |
| WCAG AA contrast thresholds | <https://www.w3.org/TR/WCAG21/#contrast-minimum> | SC 1.4.3: "at least 4.5:1", and "Large-scale text … at least 3:1" — the two thresholds the tool reports. |
| `package:html` API (`generateSpans`, `errors`, `sourceSpan`) | <https://pub.dev/documentation/html/latest/parser/HtmlParser-class.html> | Documents `errors → List<ParseError>` and `generateSpans` — "True to generate SourceSpans for the Node.sourceSpan property". |
| `package:csslib` API (`parse(input, {errors})`) | <https://pub.dev/documentation/csslib/latest/parser/parse.html> | Signature `StyleSheet parse(Object input, {List<Message>? errors, PreprocessorOptions? options})`. |
| Package sources | <https://github.com/dart-lang/tools/tree/main/pkgs/html>, <https://github.com/dart-lang/tools/tree/main/pkgs/csslib> | Matches the `repository:` field in each cached `pubspec.yaml` (html 0.15.7, csslib 1.0.2). |

Two corrections for the earlier report, to keep the record honest:

1. The JetBrains rows named inspections that its public help does not document. The
   *behaviours* (specificity display, colour preview) are documented; the inspection names
   were not verifiable and should not be cited.
2. The VS Code rows attributed "link validation / Cannot find file" to the HTML docs. The
   page documents embedded JS/CSS validation only; the resource-resolution behaviour belongs
   to the language service implementation, not that doc page. The *feature* is real and my
   tool implements it, but the citation was wrong.

No claim above is inferred from memory: each was read from the fetched page during this
session, and the two links that returned 404/empty on first probe
(`webstorm/analyzing-css.html`, a MDN HEAD request) were replaced with the working
canonical pages listed here.
