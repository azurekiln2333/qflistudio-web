# WebForge direct Tools implementation — 2026-10-22

Scope of this slice: R5 (useful language-specific functions **directly** on the main
Tools page, no secondary feature hub) and the Web part of R8 (structured/console
feedback surfaces) for the `qfli_web` product only. Everything below stays offline:
no network calls, no login, no external resource loading. The only listener is the
existing loopback preview.

## 1. What the request asked for

From `research/user-request.txt`:

> 功能卡片是tm神人来的吗 做完独有的功能全部铺在工具页里面 不要做进tm二级页面 …
> 你实在不行你学学jetbrains

So: language-specific Web tooling must live as **actual controls** on the Tools
page, not as cards that push a second "Web 工具" page. The old
`WebToolsOverview` pushed `WebServerToolsView` / `WebCodecToolsView` routes from
cards; that is exactly the pattern being removed.

## 2. Reference features researched (before implementing)

| Product | Feature (official name) | What it actually does | Adopted here |
| --- | --- | --- | --- |
| VS Code | HTML Language Features → *link validation / "Cannot find file"* | resolves `href`/`src` against the workspace, flags missing files | 文档资源检查: `href`, `src`, `srcset`, `poster`, `data`, `url()` |
| VS Code | HTML Language Features → *mismatched/unclosed tag diagnostics* | balanced-tag scanning with ranges in Problems | 结构检查: tag stack, HTML optional-end tags, void elements, `line:column` |
| VS Code | HTML Language Features → *format document* | re-indents the document | 重排缩进 (逐标签重排, explicitly not a browser-grade pretty printer) |
| VS Code | CSS Language Features → *color decorators / color picker* | parses hex/rgb/hsl/named colours | 颜色: `#RGB[A]`, `#RRGGBB[AA]`, `rgb()/rgba()`, `hsl()/hsla()`, 148 named colours |
| VS Code | Problems panel severity model | error / warning / hint with location | `WebFindingSeverity` + `line:column` in every finding |
| JetBrains WebStorm | *Unresolved file reference* inspection | marks broken relative/absolute project references | same resolver, plus "越出项目" and "外部网络" classes |
| JetBrains WebStorm | *CSS specificity* inspection | shows the `(a, b, c)` triple per selector | 优先级: id / class·attribute·pseudo-class / type·pseudo-element |
| JetBrains WebStorm | *Duplicate property* inspection | flags a property declared twice in one rule | 重复声明 (last one wins, positions listed) |
| JetBrains WebStorm | *Box model* / padding-margin inspection | expands 1-4 value shorthands | 盒模型: `padding`, `margin`, `border-width`, `box-sizing`, outer size in px |
| MDN | CSS color values; WCAG 2.1 §1.4.3 contrast | 4.5:1 body text, 3:1 large text | 对比度 `x.xx:1` + AA verdict per colour |
| MDN | Selectors spec (`:where()` = 0, `:not()` = argument) | specificity rules | implemented in `_selectorCounts` |
| MDN | Void elements / optional end tags | `<img>` etc. never close; `<p>`, `<li>`, `<td>` may omit | avoids false "unclosed tag" errors |
| MDN | HTML accessibility basics (`lang`, `alt`, `label`, `<title>`, viewport) | static a11y checks | 结构检查 reports these as warnings/hints |

Deliberately **not** implemented, because the runtime cannot honestly provide it
without a browser engine or a real language server: CSS cascade resolution,
JS/TS syntax validation, `color-mix()` evaluation, full HTML conformance
validation, and any "compiler" branding.

## 3. Implemented files

New product-owned services (pure Dart, no IO except the document reader):

- `lib/services/web_source_scan.dart` — `WebSourceLocation` / `WebSourceIndex`
  (offset → 1-based `line:column`, CRLF-aware), `WebFinding`, CSS comment
  stripping that preserves offsets, quote-run detection.
- `lib/services/web_css_tools.dart` — `CssColor` (hex/rgb/hsl/named/transparent,
  WCAG `relativeLuminance` + `contrastRatio`), `WebCssTools.parse` (rule blocks,
  declarations, structural findings), `findColors`, `specificities`,
  `duplicateDeclarations`, `boxModel`, `format`.
- `lib/services/web_markup_inspector.dart` — bounded HTML tokenizer (quoted
  attributes, comments, doctype, `script`/`style`/`textarea`/`title` raw text),
  `structureFindings`, `accessibilityFindings`, `formatHtml`,
  `inspectFile`/`inspectSource` with `WebResourceReference` classification:
  `localFile`, `siteRoot`, `missing`, `inline`, `external`, `escaping`,
  `invalid`. Follows local `<link rel=stylesheet>` files for `url()` and
  `@import` references (bounded to 32 stylesheets / 1 MB per document).

New product-owned widgets (all inline, no `Navigator.push`):

- `lib/widgets/web_tools/web_tools_panel.dart` — `WebToolPanel`,
  `WebFindingList` (capped), `WebValueRow`, `WebSummaryChips`, `WebToolOutput`,
  `WebEmbeddedPanel`.
- `lib/widgets/web_tools/web_source_inspector_view.dart` — project + document
  pickers (scan capped at 200 HTML files, skips `.git/.qfli/.dart_tool/
  node_modules/build`), counts, findings, reference table, offline verdict.
- `lib/widgets/web_tools/web_css_tools_view.dart` — colour / box model /
  specificity / duplicate modes, live on every keystroke, capped at 24 rows.
- `lib/widgets/web_tools/web_markup_check_view.dart` — HTML ⇄ CSS scanner switch,
  findings, 重排缩进 output with copy.

Changed product-owned page:

- `lib/pages/web_tools_overview.dart` — now a single `CustomScrollView`:
  offline banner → 终端 entry (`onOpenTerminal`) → **embedded** `本地服务`
  (`WebServerToolsView`, 380 px) → **embedded** `Web 编解码`
  (`WebCodecToolsView`, 460 px) → 文档资源检查 → CSS 颜色与盒子 → 结构检查与格式化
  → 通用工具 (`commonTools` cards) → offline note.

`lib/pages/web_tools_page.dart` was **not** modified (root owns the runtime and
the harness); the two embedded views are reused as-is. `lib/main.dart`,
core packages, platform code and curriculum/aggregate content were not touched.

## 4. Layout and lifecycle decisions

- **One scroll surface.** The controls column is a single `SliverToBoxAdapter`
  child, not a `SliverList`, because `SliverList` disposes children that scroll
  out of view — that would dispose `_WebServerToolsViewState` and stop a running
  loopback server mid-session (and drop codec input). Slivers themselves stay
  mounted; only the shared card grid is lazy.
- **Finite inner scrolling.** The reused views keep their own `ListView`; they
  are wrapped in `WebEmbeddedPanel` with an explicit height and
  `clipBehavior: Clip.antiAlias`, so both scroll surfaces stay bounded and the
  page cannot grow unbounded.
- **No new global state.** Every panel is a `StatefulWidget` with local
  controllers disposed in `dispose()`; the only async guard needed is the
  existing one in `WebServerToolsView` (unchanged).
- **Synchronous, capped IO.** Document inspection uses sync reads with a 1 MB
  document cap and reference/stylesheet caps, so it is safe to run from a widget
  callback and cannot stall the frame for an unbounded time.
- **Offline gate unchanged.** `offlineOnly` still hides the HTTP tool and the API
  proxy editor inside `WebToolsPage`; the overview exposes no network entry. The
  inspector reports external references as **errors**, never fetches them.

## 5. Honest capability boundaries (also shown in the UI)

- Findings are *inspections* over the literal source, labelled as such in the
  panel helper text ("不是完整 HTML 校验器").
- Colour functions other than `rgb/hsl` (e.g. `color-mix()`) return "无法解析"
  instead of guessing.
- Contrast requires opaque colours; translucent values report
  "需要不透明颜色才能计算对比度".
- Box-model sums are only computed for `px`; `rem`/`em`/`%` report
  "无法换算" instead of inventing a pixel value.
- `:is()/:not()/:has()` use the max argument; `:where()` counts as zero; exotic
  selectors (`::part`, nesting `&`) are not modelled.
- 重排缩进 is a predictable per-tag rewrite (inline text stays with its tag for
  phrasing/heading elements), not a browser-grade formatter.

## 6. Tests and evidence

New focused suites (all product-owned, no pre-existing dirty test edited):

- `test/web_css_tools_test.dart` — 20 cases: hex/rgb/hsl/named parsing (148 named
  colours, `rebeccapurple` = `#663399`), WCAG ratios (black/white = 21,
  `#777` on white ≈ 4.48), colour scanning that ignores strings/comments,
  specificity (`#nav .item a:hover` = `(1,2,1)`, `:where()` = 0), duplicates,
  box model (`content-box` 320 + 40 + 4 = 362 px; `border-box`; non-px refusal),
  diagnostics (unclosed block, stray `}`, missing colon, unterminated
  comment/string), formatter, `line:column` mapping incl. CRLF and clamping.
- `test/web_markup_inspector_test.dart` — 12 cases: unclosed/stray tags, optional
  end tags and void elements, `script` raw text, quoted `>` in attributes, a11y
  findings (`lang`, `title`, viewport, `alt`, label association, empty
  link/button), reference classification (local / site-root / missing / inline /
  external / escaping / fragment skipped), stylesheet `url()` following,
  missing-document handling, real on-disk project scan, `formatHtml`.
- `test/web_tools_overview_test.dart` — 9 widget cases against the real page:
  every tool is inline with no `Web 工具` route, terminal callback fires, codec
  converts inline (no `BackButton`), CSS panel reports colours/contrast/
  box-model 362 px/`(0, 2, 0)`, duplicate declarations with position, markup
  panel findings + 重排缩进 + HTML⇄CSS switch, real project reference counts
  (`缺失 1`, `外部 1`, `本地 3`, "离线检查未通过"), offline-clean project verdict,
  and a 320×640 @ 2.0 text-scale pass that scrolls to every section.

Commands run (serial, from the repo root):

```
flutter analyze --no-pub lib test          → No issues found
flutter test --no-pub --concurrency=1 test/web_css_tools_test.dart \
  test/web_markup_inspector_test.dart test/web_tools_overview_test.dart \
  test/web_tools_navigation_test.dart      → 47 passed
flutter test --no-pub --concurrency=1 test/web_tools_overview_test.dart \
  test/web_css_tools_test.dart test/web_markup_inspector_test.dart \
  test/web_tools_navigation_test.dart test/web_tools_page_test.dart \
  test/web_app_test.dart                   → 63 passed
flutter test --no-pub --concurrency=1      → 127 passed (full suite)
flutter test --no-pub --concurrency=1 test/startup_test.dart \
  test/web_dev_server_test.dart test/nginx_host_test.dart \
  test/web_terminal_release_test.dart      → 33 passed (re-check)
```

Log: `research/full-test-run.log` (final green run; an earlier interleaved run
reported two failures in suites unrelated to this slice — `startup_test` /
`web_dev_server_test` / terminal suite — and those suites passed both in the
follow-up run and in the full green run; treat as flake, not a regression).

Not verified here: OHOS device execution (`hdc list targets` is Empty on
2026-10-22) and `flutter build hap`. These remain open parent gates; this slice
adds no native code and no new assets, so the packaged surface only gains Dart.

## 7. Integration notes for the root coordinator

1. **`test/web_tools_navigation_test.dart` still passes** without edits: the
   `本地服务` heading is a real heading and the embedded server view sits directly
   beneath it, so `find.text('本地服务')` + `find.byTooltip('项目服务设置')` work.
   It was left untouched (pre-existing dirty file).
2. **Only one product file changed**: `lib/pages/web_tools_overview.dart`.
   Everything else is new. `web_tools_page.dart` is unchanged.
3. **Duplication to watch**: `_CommonToolsGrid` in the overview mirrors the
   `ToolsGrid._grid` geometry formula (card height + text-scale allowance) so the
   shared `commonTools` cards keep the same size. If core later exposes a
   `commonToolsSliver()` helper, the overview should call it instead; the
   core owner should be the one to add it.
4. **Suggested commit** (explicit paths, no unrelated WIP):
   `feat(web-tools): put real offline Web inspections directly on the tools page`
   with:
   ```
   lib/pages/web_tools_overview.dart
   lib/services/web_source_scan.dart
   lib/services/web_css_tools.dart
   lib/services/web_markup_inspector.dart
   lib/widgets/web_tools/web_tools_panel.dart
   lib/widgets/web_tools/web_source_inspector_view.dart
   lib/widgets/web_tools/web_css_tools_view.dart
   lib/widgets/web_tools/web_markup_check_view.dart
   test/web_css_tools_test.dart
   test/web_markup_inspector_test.dart
   test/web_tools_overview_test.dart
   .trellis/tasks/10-22-standalone-offline-ide/research/web-tools-results.md
   .trellis/tasks/10-22-standalone-offline-ide/research/full-test-run.log
   ```
5. **Still open for R5/R8 beyond this slice**: editor inline wavy diagnostics
   with unsaved buffers (core-owned analyzer contract), Problems/Output/Debug
   Console/Ports panels fed by real runtime capabilities, and the same direct-tool
   treatment for the other products (each coordinator). The Web request/console
   transcript is still surfaced by the embedded server view; it is not duplicated.
