# CSS expansion research — 60 new topics (css-101…160)

Owner: WebForge CSS author (this session). Root owns integration, aggregate
generation, runner wiring and commits.

## Status

| Item | State |
| --- | --- |
| Existing CSS baseline audit (100/100) | **Done** — fresh host replay: 100 pass, 0 fail, 0 mapping issues, 0 oracle coverage gaps |
| Existing CSS oracle quality audit | **Done** — 47/100 cases carry at least one non-literal or host-bound expectation; 4 real defects found (below) |
| Root confirmation that the full 301 baseline passes | **Done** — root reported 301/301 examples, 1822 assertions, 0 mapping issues (`research/browser-baseline.md`) |
| New topic plan (css-101…160) | **Done** — 60 topics below, each with a concrete oracle design |
| `scripts/curriculum/css_expansion.py` (`CSS_EXTRA`) | **Done** — 60 entries, self-verified |
| `scripts/css_expansion_assertions.mjs` | **Done** — 60 cases, 543 assertions, mutation-tested |
| Ready for root integration | **Yes** — see §7 |

Nothing in this turn modified an existing repository file. Audit tooling and
reports live only in this task's `research/` directory:

- `css-baseline-audit.mjs` / `css-baseline-report.md` — task-local replay of the
  unmodified runner semantics for the CSS subset (read-only w.r.t. the repo,
  never writes the runner's canonical report path).
- `css-oracle-static-audit.mjs` / `css-oracle-static-audit.md` — static scan of
  the 100 CSS oracle cases for non-literal expectations.
- `css-viewport-probe.mjs` / `css-viewport-probe.md` — the same oracle replayed
  at 1280×720 / 800×1180 / 412×915.
- `css-feature-probe.mjs` / `css-feature-probe.txt` — feature support of the
  exact bundled Chromium used by verification.

## 1. Baseline result (fresh, this machine, this checkout)

```
examples: 301 (html 100, css 100, javascript 101)
CSS replay: 100 pass / 0 fail, 362 addCheck calls,
            oracle coverage gaps 0, lesson<->example mapping issues 0,
            zero external requests, zero broken internal resources,
            zero page errors.
Chromium (bundled Playwright 1.64.1): 156.0.8078.4
```

So the CSS half of the 301 baseline is currently **green on the host**, which
matches the historical 2026-10-15 report (301/301). This does not replace the
root-run full 301 gate, and it says nothing about OHOS execution.

## 2. Real defects found in the existing CSS baseline

### 2.1 Oracle defects (false negatives on a correct document)

Reproduced by replaying the **unmodified** oracle at a non-desktop viewport
(`css-viewport-probe.md`). The runner never sets a viewport, so these oracles
silently depend on Playwright's 1280×720 default:

| id | defect | evidence |
| --- | --- | --- |
| `css-example-011` | Lesson is a 1/2/3-column breakpoint ladder; oracle only asserts the desktop 3-column state and names it "three columns at 1280px". The document is *correct* at 800px (2 columns, exactly as its `expectedOutput` says) but the check fails. | tablet `cols=2` → FAIL; phone `cols=1` → FAIL |
| `css-example-044` | Asserts `max-width(65ch) < viewport`; `65ch` legitimately exceeds a 412px viewport, so correct CSS fails. | phone `609.883 < 412` → FAIL |
| `css-example-051` | Holy-grail collapses to 1 column under its own media query; oracle asserts 3 named columns unconditionally. | phone `396px` single track → FAIL |
| `css-example-064` | Responsive hamburger menu: oracle asserts **only** the desktop state (`burger hidden`, `menu flex`) and never verifies the mobile branch or the toggle. At phone width the desktop assertions fail, and the lesson's actual teaching point (☰ toggles the menu) is **unverified at every width**. | phone: `burger hidden` FAIL, `menu flex` FAIL |

Root decision needed (p6 owns `web_markup_assertions.mjs`; this session must not
edit it): either pin the viewport inside those four cases
(`await page.setViewportSize({width:1280,height:720})`) and add the missing
mobile/toggle assertions for 064, or accept them as host-only. Until fixed, any
narrow-viewport harness (including the OHOS catalog harness) will disagree with
the acceptance run on documents that are actually correct.

### 2.2 Weak expectations (pass without proving the lesson)

47/100 cases contain at least one check that cannot fail for the wrong reason.
Worst offenders, with the exact consequence:

| id | weak check | why it is weak |
| --- | --- | --- |
| `css-example-041` | `'badge has ::after block'` evaluates `borderTop !== null` where `borderTop = position` | tautology — `position` is always a non-null string; asserts nothing about `::after` |
| `css-example-029` | `printRule.includes('print') \|\| printRule.length > 0` | the fallback makes it true whenever any print rule exists |
| `css-example-090` | `padding === '8px' \|\| padding === '16px'` | accepts both breakpoint branches, so a broken media query cannot be detected |
| `css-example-015` | `grid-template-columns !== 'none'` ("auto-fit minmax columns resolve") | any grid passes, including a single fixed column |
| `css-example-036` | `box-shadow !== 'none'`, `text-shadow !== 'none'` | no blur/offset/colour literal |
| `css-example-035` | `disabledOpacity < 1` | no literal opacity |
| `css-example-021` | `filter.includes('grayscale') && includes('contrast')`, `backdrop.includes('blur')` | no amounts |
| `css-example-050` | toggle switch driven by setting `.checked` in the page instead of clicking the label | the real user interaction (label click) is never exercised |
| `css-example-002` | `\|width − viewport/2\| ≤ 24` | viewport-bound tolerance, not a literal |

These stay as-is unless p6 asks for a fix list; they are recorded here because
the new module must not repeat the pattern.

### 2.3 Content-level observations

- Baseline `explain` strings are short: 63–196 chars, ~100 typical. The delivery
  requirement for the expansion is a full explanation, so new entries target
  ≥180 chars of `explain` plus 4–7 concepts, 3 pitfalls and an exercise.
- Baseline lessons deliver one code document each and `emit_content.py` derives
  the example from it, so an expansion entry needs exactly one complete document.
- The `<output id="webforge-check">` marker is **injected by
  `emit_content.py::example_document()`**, not authored into lessons. New lesson
  code must therefore **not** contain the marker (double markers would break
  `markerPresent === 1` in the runner).

## 3. Contract for the two new files

### 3.1 `scripts/curriculum/css_expansion.py`

Same shape as the existing curriculum modules (`css_data*.py`, `supplement.py`):

```python
CSS_EXTRA = [ { ... }, ... ]   # exactly 60 dicts, ids 101..160 in list order
```

Per-entry schema (identical keys/types to the existing modules — `emit_content.py`
reads these directly, no generator change needed):

| key | type | rule for this expansion |
| --- | --- | --- |
| `t` | str | Chinese lesson title, unique, not a paraphrase of any of the 100 existing titles |
| `level` | str | `beginner` \| `intermediate` \| `advanced` |
| `obj` | str | one-sentence objective; becomes `summary` |
| `pre` | list[str] | prerequisite lesson names, may be `[]` |
| `con` | list[str] | 4–7 concept tokens |
| `explain` | str | ≥180 chars, Chinese, explains mechanism + when to use + failure mode |
| `code` | str | one complete offline HTML document: `<!doctype html>`, `lang="zh-CN"`, `<meta charset="utf-8">`, inline `<style>`, no external URL of any kind, **no `webforge-check` marker** |
| `out` | str | expected visual/computed result, phrased in concrete values |
| `pit` | list[str] | exactly 3 real pitfalls |
| `ex` | list[tuple[str, str, str]] | ≥1 `(prompt, hint, answer)` |

Integration (root): `emit_content.py` appends the module **last** in the css
chain so index-derived ids land on 101…160:

```python
+ css_data5.CSS5
+ supplement.CSS6
+ css_expansion.CSS_EXTRA
```

Resulting ids: `css-tutorial-101…160`, `css-example-101…160`,
`css-tutorial-1NN-lesson`. No id may collide with the existing 100.

### 3.2 `scripts/css_expansion_assertions.mjs`

Mirrors the p6 module contract exactly:

```js
export const COVERED_IDS = [...];                                  // css-example-101…160
export async function assertExpansionExample(page, example, addCheck) // -> bool
```

`addCheck(name, ok, detail?)`; returns `false` for any id it does not own.
Root's integration hunk inside `web_markup_assertions.mjs` (p6 file, root edits):

```js
const expansion = await import('./css_expansion_assertions.mjs').catch(() => null);
// inside assertMarkupExample, before the final `return false`:
if (expansion && expansion.COVERED_IDS.includes(id)) {
  return expansion.assertExpansionExample(page, example, addCheck);
}
// and merge into COVERED_IDS:
...(expansion ? expansion.COVERED_IDS : []),
```

Oracle rules for the new module (stricter than the baseline):

1. **Literal expectations only.** Every check compares a computed style, a
   geometry relation, an interaction outcome or the parsed CSSOM against a
   literal from the authored document. No `!== 'none'`, no `\|\|` fallbacks, no
   "non-empty", no substring-only checks.
2. **Viewport independence.** Any check that reads geometry or a media query
   first calls `page.setViewportSize()` to a value the example explicitly
   supports (e.g. 960×640), so the oracle cannot depend on the runner default or
   on the OHOS harness width. Layout assertions use ratios/relations plus at
   least one literal px value.
3. **Real interaction.** Toggles/hover/focus are driven by `click`, `hover`,
   `focus`, `type`, `press` on the real control (label clicks, checkbox clicks,
   keyboard Tab), never by writing `el.checked` / adding classes from the oracle.
   Where a real interaction is impossible (`::-webkit-autofill`, `@media print`),
   assert the parsed CSSOM declaration **plus** an observable computed value.
4. **Self-contained.** Examples use only inline CSS/SVG/data URIs; no external
   request, no test fixture, no extra file. Assertions never inject styles or
   markup into the page.
5. **≥5 checks per example**, of which ≥2 are literal computed-style values and
   ≥1 is semantic (geometry relation, interaction outcome, or CSSOM structure).

Self-verification (before handoff, task-local harness, not a repo file): build
the 60 documents the same way `emit_content.py` does, run
`assertExpansionExample` against them, and assert schema/offline rules
(unique titles, `explain` length, no `http(s)://`, no marker, code is a complete
document). Report pass/fail per id.

## 4. The 60 topics

Feature support was probed on the bundled Chromium 156 (`css-feature-probe.txt`):
everything below is supported, including `@layer`, `@scope`, `@property`,
`@starting-style`, `subgrid`, `:has()`, `:nth-child(… of S)`, `text-wrap: balance`,
`color-mix()`, `oklch()`, `light-dark()`, `mask-composite`, `field-sizing`,
`scroll-driven animations`, `animation-composition`, `position-anchor`.
Deliberately avoided: `container-type: style` (unsupported), `line-clamp`
shorthand (unsupported), and anything needing a network fetch.

Legend for "oracle": **C** = literal computed values, **G** = geometry/layout
relation, **I** = real interaction driven by the oracle, **O** = parsed CSSOM /
rule declaration. Every row uses C plus at least one of G/I/O.

### A. Cascade, layers and scope (101–106)

| id | title | level | key concepts | oracle |
| --- | --- | --- | --- | --- |
| 101 | 级联层 @layer：给样式排优先级 | intermediate | `@layer`, layer order, unlayered wins | C color of 3 same-specificity cards; O layer names in order |
| 102 | @layer 与 !important 的反转规则 | advanced | layer order, `!important` reversal | C colour when both layers use `!important`; C colour of ordinary layered vs unlayered |
| 103 | @scope：把样式限制在作用域内 | advanced | `@scope`, `:scope`, donut boundary (`to`) | C matched/unmatched colour inside nested scopes; O scope rule prelude |
| 104 | @property：类型化自定义属性 | advanced | `syntax`, `inherits`, `initial-value`, typed interpolation | C initial value on unset element; I transition to another literal after class toggle, G size change |
| 105 | :where() 零权重与 :is() 的权重差 | advanced | specificity of `:is()`/`:where()`, `:not()` | C colour resolved by an override that only wins under `:where()`; C `:is()` case keeps the more specific rule |
| 106 | :nth-child(An+B of S) 过滤计数 | intermediate | `of S` filter, `An+B`, `:nth-last-child` | C colour of filtered 2nd/3rd matches; G item order count |

### B. Selector state and native validation (107–113)

| id | title | level | key concepts | oracle |
| --- | --- | --- | --- | --- |
| 107 | :has() 让父级跟随子级状态 | intermediate | `:has(> …)`, `:has(:checked)`, `:has(+ …)` | I click a radio → C card border/background literal; C sibling highlight |
| 108 | :focus-within 表单组整体聚焦 | intermediate | `:focus-within`, `:focus-visible`, `outline-offset` | I `focus()` input then Tab → C fieldset border literal, C outline offset |
| 109 | :user-invalid 原生校验反馈 | advanced | `:user-invalid`, `:valid`, `required`, `type=email` | I type invalid then blur → C border red literal; I type valid → C green literal; C empty state untouched |
| 110 | :target 纯 CSS 标签页 | advanced | `:target`, fragment links, `:target::before` | I click each link → C active panel display/colour; G only one visible |
| 111 | :empty 空状态占位 | beginner | `:empty`, `::before` placeholder, whitespace caveat | C min-height of empty box, C `::before` content literal, G non-empty sibling unaffected |
| 112 | @counter-style 自定义序号标记 | advanced | `@counter-style`, `system`, `symbols`, `suffix`, `::marker` | C `::marker` content of 3 items; G marker widths differ; O counter-style rule parsed |
| 113 | ::file-selector-button 自定义上传按钮 | intermediate | `::file-selector-button`, `appearance` | C button background/radius literal; C input border; I click real file button is not driven — assert CSSOM + base styling |

### C. Flex / Grid / box tree (114–123)

| id | title | level | key concepts | oracle |
| --- | --- | --- | --- | --- |
| 114 | flex 简写与 flex-basis: 0 vs auto | advanced | `flex: 1`, `flex-basis`, shrink, content size | G three item widths with literal px; C `flex-basis` literal |
| 115 | flex order 视觉顺序与无障碍顺序 | intermediate | `order`, DOM vs visual order, tab order | G `boundingBox().x` order vs DOM order; C `order` values |
| 116 | flex-wrap 与 align-content 多行对齐 | intermediate | `flex-wrap`, `align-content`, `row-gap` | G row tops differ for `align-content: flex-start`; C `align-content` literal |
| 117 | inline-flex 与基线对齐 | intermediate | `inline-flex`, `vertical-align`, `align-items` | G inline box baseline offset vs sibling text; C display literal |
| 118 | subgrid：子网格继承父网格轨道 | advanced | `subgrid`, `grid-column: 1/-1`, alignment | G child cells align to parent track x-positions (literal px, viewport pinned); C `grid-template-columns: subgrid` |
| 119 | repeat(auto-fill) 与 minmax 自适应 | intermediate | `auto-fill`, `minmax()`, track count | G column count at two pinned widths (literal counts); C gap literal |
| 120 | grid-auto-rows 与隐式行 | intermediate | implicit rows, `grid-auto-rows`, `grid-auto-flow` | G row heights literal for 3 implicit rows; C `grid-template-rows` of explicit part |
| 121 | place-items 与 place-content 的区别 | intermediate | `justify-*` vs `align-*`, `place-*` shorthand | C four resolved longhands literal; G cell position inside track |
| 122 | display: contents 展开盒树 | advanced | `display: contents`, box tree, accessibility caveat | G child left edge equals grandparent content edge; C `display: contents`; C wrapper has no background painted (G height 0) |
| 123 | contain: layout paint 隔离渲染 | advanced | `contain`, containment, `content-visibility` | C `contain` literal; G clipped overflow inside contained box vs visible outside |

### D. Sizing units and positioning (124–131)

| id | title | level | key concepts | oracle |
| --- | --- | --- | --- | --- |
| 124 | min() / max() / clamp() 组合运算 | intermediate | `min()`, `max()`, `clamp()`, `calc()` | C width literal at two pinned viewports (clamped values) |
| 125 | fit-content 与 max-content 的取舍 | advanced | `width: fit-content`, `max-content`, `min-content` | G three boxes with distinct literal widths for identical text |
| 126 | inset 逻辑属性定位 | intermediate | `inset-inline-start`, `inset-block-end`, `writing-mode` | C resolved `left/bottom` literals; G position inside relative parent |
| 127 | sticky 侧栏与 scroll-margin-top 锚点 | advanced | `position: sticky`, `scroll-margin-top` | I scroll → G sticky top stays literal; I click in-page anchor → G heading offset by scroll-margin literal |
| 128 | dvh / svh 动态视口单位 | intermediate | `dvh`, `svh`, `vh`, mobile chrome | C `height` literal for `50dvh`/`50svh` at pinned viewport; G hero fills half |
| 129 | cqi / cqw 容器查询单位 | advanced | `container-type`, `cqi`, `cqw` | C font-size literal from `5cqi` at pinned container width; G container resize via media-free width class |
| 130 | ch / cap 排版单位与行宽 | intermediate | `ch`, `cap`, `max-width` | C `max-width` literal px for `60ch`; G measured line box width equals it |
| 131 | overflow: clip 与 overflow-clip-margin | advanced | `overflow: clip`, `overflow-clip-margin` | C `overflow` literal; G visible bleed equals margin literal; C `overflow-clip-margin` |

### E. Colour (132–136)

| id | title | level | key concepts | oracle |
| --- | --- | --- | --- | --- |
| 132 | oklch 感知均匀色阶 | advanced | `oklch()`, lightness/chroma/hue | C five swatch colours exactly matching the authored `oklch`→rgb literals; G lightness monotonic |
| 133 | color-mix() 就地混色 | intermediate | `color-mix(in oklab/srgb, …)` | C mixed background equals authored rgb literal; C 25/75 mix literal |
| 134 | light-dark() 与 color-scheme | advanced | `color-scheme`, `light-dark()` | C light value by default; I `emulateMedia({colorScheme:'dark'})` → C dark literal |
| 135 | 相对颜色 rgb(from …) | advanced | relative colour syntax, channel maths | C derived colour literal (e.g. `rgb(from #3366cc r g b / 50%)` → rgba literal) |
| 136 | repeating-linear-gradient 条纹 | intermediate | repetition, colour stops, tile size | C `background-image` full literal string; C `background-size`; G stripe geometry via `background-position` |

### F. Painting and masking (137–142)

| id | title | level | key concepts | oracle |
| --- | --- | --- | --- | --- |
| 137 | mask-image 渐隐遮罩 | advanced | `mask-image`, `mask-size`, `mask-repeat` | C mask longhands literal; G element clipped (pixels transparent) via `getComputedStyle` + canvas probe of an inline SVG mask? use CSSOM-only: assert computed `mask-image` + `-webkit-mask-image` literal |
| 138 | mask-composite 遮罩合成 | advanced | `mask-composite: intersect/exclude`, layered masks | C computed `mask-composite` literal list; O rule text; G union vs intersect area differs by geometry |
| 139 | background-blend-mode 双色混合 | intermediate | `background-blend-mode`, layered gradients | C blend mode literal; C two-layer `background-image` string with both gradients |
| 140 | border-image 渐变边框 | advanced | `border-image-source/slice/width`, `border-radius` caveat | C `border-image-source` literal contains authored gradient; C `border-top-width`; G corner not rounded |
| 141 | text-emphasis 重点符号 | intermediate | `text-emphasis-style/color/position` | C `text-emphasis-style/color` literal; G emphasised line height grows |
| 142 | -webkit-text-stroke 描边字 | intermediate | stroke width/colour, paint order | C `-webkit-text-stroke-width/color` literal; C fill colour literal |

### G. Typography (143–148)

| id | title | level | key concepts | oracle |
| --- | --- | --- | --- | --- |
| 143 | text-wrap: balance 平衡折行 | intermediate | `text-wrap: balance/pretty/wrap` | C `text-wrap` literal; G balanced heading line count at pinned width vs `wrap` sibling |
| 144 | hyphens 与 overflow-wrap 断词 | intermediate | `hyphens: auto`, `overflow-wrap: break-word`, `lang` | C long word does not overflow (scrollWidth ≤ clientWidth); C hyphenation literals `hyphens`/`overflow-wrap` |
| 145 | font-variant-numeric 数字对齐 | beginner | `tabular-nums`, `proportional-nums` | C `font-variant-numeric` literal; G digit column widths equal within 0.5px |
| 146 | text-decoration-skip-ink 下划线避让 | intermediate | `skip-ink`, `thickness`, `offset` | C `text-decoration-skip-ink` literal; G underline offset literal |
| 147 | box-decoration-break 跨行高亮 | advanced | `clone`, `slice`, inline fragmentation | C `box-decoration-break` literal; G two decorated line boxes (client rects ≥2) |
| 148 | text-box-trim 去掉行首空隙 | advanced | `text-box-trim`, `text-box-edge` | C `text-box-trim` literal; G trimmed box top closer to glyph top than untrimmed sibling |

### H. Motion (149–154)

| id | title | level | key concepts | oracle |
| --- | --- | --- | --- | --- |
| 149 | @starting-style 与离散过渡 | advanced | `@starting-style`, `transition-behavior: allow-discrete`, `display` | I click to open → G panel becomes visible and opacity reaches literal 1; I click to close → G hidden after transition |
| 150 | animation-fill-mode 与延迟序列 | intermediate | `forwards`, `both`, `animation-delay`, `steps()` | C `animation-fill-mode/delay/duration` literals; G final transform literal after wait |
| 151 | cubic-bezier 自定义缓动 | advanced | `cubic-bezier()`, `steps()`, `linear()` | C `transition-timing-function` literal; I hover → G intermediate offset falls in the eased, not linear, band at a sampled time |
| 152 | 滚动驱动动画（animation-timeline） | advanced | `animation-timeline: view()/scroll()`, `animation-range` | I scroll → G progress width grows monotonically with literal values at two scroll offsets |
| 153 | prefers-reduced-motion 降级 | intermediate | media query, motion preference | I `emulateMedia({reducedMotion:'reduce'})` → C `animation-name: none` + `transition-duration: 0s`; default → C animation name literal |
| 154 | animation-composition 叠加动画 | advanced | `replace`, `add`, `accumulate` | C `animation-composition` literal; G composed translate equals sum literal |

### I. Scroll, form and anchor interactions (155–160)

| id | title | level | key concepts | oracle |
| --- | --- | --- | --- | --- |
| 155 | scroll-snap 纯 CSS 横向卡片 | intermediate | `scroll-snap-type`, `scroll-snap-align`, `scroll-padding` | I `scrollBy` → G snapped card x equals a literal multiple; C snap longhands |
| 156 | scrollbar-gutter 防布局跳动 | advanced | `scrollbar-gutter: stable`, overflow | G content x identical with and without scrollable overflow (literal px equality) |
| 157 | overscroll-behavior 阻断滚动链 | intermediate | `overscroll-behavior: contain`, nested scrollers | C `overscroll-behavior` literals on both scrollers; G inner scroll does not move outer scrollTop |
| 158 | field-sizing 自适应输入框 | advanced | `field-sizing: content`, `min/max-width` | C `field-sizing` literal; I type text → G textarea width grows to a literal range, capped by `max-width` |
| 159 | appearance: none 自定义 select | intermediate | `appearance`, custom arrow via background, `:focus-visible` | C `appearance: none`, C radius; I focus → C outline literal; G arrow reserved padding |
| 160 | 锚点定位（position-anchor）工具提示 | advanced | `anchor-name`, `position-anchor`, `position-area`, `anchor()` | C `anchor-name`/`position-anchor` literals; G tooltip box sits within literal px of the anchor edge at pinned viewport |

Every row above is deliberately chosen so the assertion is a *value the lesson
teaches*, not a proxy for "the page loaded".

## 5. Authoring checklist (executed only after the root baseline gate)

1. Write `CSS_EXTRA` (60 entries, schema above; ids implied by list order
   101…160). One complete offline document per entry, no marker, no external URL.
2. Write `css_expansion_assertions.mjs` with `COVERED_IDS` (101…160) and
   `assertExpansionExample`, obeying the five oracle rules in §3.2.
3. Run the task-local self-verification harness: schema/offline checks + every
   example executed against its own oracle at its pinned viewport, plus the
   oracle replayed at a second viewport to prove viewport independence.
4. Report per-id pass/fail, the exact commands, and the residual risks. Root
   integrates `emit_content.py`, `web_markup_assertions.mjs` dispatch, runs the
   full 481-example browser gate, regenerates assets, and commits.

## 6. Risks

- Root's generator change is index-based: if `CSS_EXTRA` is inserted anywhere
  except last, all css ids shift and every existing oracle breaks. Only append.
- If p6 imports the expansion module at the top of `web_markup_assertions.mjs`
  with a static `import`, a syntax error in the new file would take the whole
  markup oracle down; the suggested dynamic import keeps baseline failures
  isolated.
- `scroll-driven`, `@starting-style`, `field-sizing`, `position-anchor` are
  recent features: they are verified present in Chromium 156 here, but the OHOS
  ArkWeb engine version is unproven (device gate is open), so their oracles also
  assert the authored declaration via CSSOM where possible.
- Baseline defects in §2.1 remain open until p6/root decides; this session must
  not edit `web_markup_assertions.mjs`.

## 7. Authoring result (this session)

Both files are authored and self-verified. Nothing outside the two owned paths
was modified.

| File | Content | Contract |
| --- | --- | --- |
| `scripts/curriculum/css_expansion.py` | `CSS_EXTRA` — 60 lessons (`_B1`…`_B11` batches, summed in the final line) | same schema as the shipped curriculum (`t, level, obj, pre, con, explain, code, out, pit, ex`) |
| `scripts/css_expansion_assertions.mjs` | `CSS_CASES` map, `COVERED_IDS`, `assertExpansionExample(page, example, addCheck) -> bool` | mirrors `assertMarkupExample` in `web_markup_assertions.mjs` |

### Verification evidence

- `css-expansion-verify.mjs` — **60/60 examples pass, 543 assertions, 0 schema
  issues**. Each example is rendered exactly as `emit_content.py` will emit it
  (including the injected `<output id="webforge-check">` marker) and executed
  twice: pinned 960×720 and a second viewport.
- Viewport portability: the whole suite also passes at **360×640, 412×915,
  800×1180, 1280×900 and 1920×1080**. Two oracle cases (`css-example-130`,
  `css-example-157`) were caught reading host-dependent geometry by this sweep
  and now pin their own viewport — the same defect class reported in §2.1
  against the baseline.
- `css-expansion-mutation.mjs` — **60/60 mutations detected**. Each lesson is
  broken with one targeted semantic edit (wrong colour, wrong size, removed
  rule, flipped enum). Every mutation turns at least one check red, so no
  assertion set is vacuous.
- `check_ids.py` — append-last integration yields exactly `css-example-101` …
  `css-example-160`, with no title or document-body collision against the
  shipped 100.

### Content metrics

- 60 unique lessons, 60 unique documents, no `<script>`, no network reference,
  no external font, no `@import`. The single `data:` URI is an inline SVG arrow
  (`css-example-159`); its `xmlns` string is an XML namespace identifier, not a
  fetch, and the harness confirms zero external requests.
- `explain` length: min 181 / median 253 chars (baseline median ~100) — every
  lesson carries a real explanation, not a caption.
- Oracle strength: 4–9 `addCheck` per lesson, **average 6.0** (baseline
  average 3.6), and at least one interaction check wherever the lesson teaches
  an interactive state (click, `:hover`, `:focus`, typing, `emulateMedia`,
  programmatic scroll, wheel).
- Difficulty: 2 beginner / 27 intermediate / 31 advanced; every lesson has 4
  concepts, exactly 3 pitfalls and 1 exercise, and every `pre` entry names a
  real shipped lesson title.

### Notes for root integration

1. Append `CSS_EXTRA` **last** in the css chain (`… + supplement.CSS6 +
   css_expansion.CSS_EXTRA`). Any other position shifts ids.
2. Import the oracle lazily inside the dispatch path so a syntax error in the
   new module cannot take the baseline down.
3. Not covered by this portion: `html_expansion.py` (HTML101…160) and
   `js_expansion.py` / `js_expansion_assertions.mjs` (JS102…161) — other
   workers. Integration must wire all three the same way.
4. The four baseline oracle defects in §2.1 are still open and untouched.
