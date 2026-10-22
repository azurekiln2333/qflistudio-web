# JavaScript curriculum expansion — 60 new topics (js-example-102…161)

Owner: JS expansion worker. Files owned by this worker (new files only):

- `scripts/curriculum/js_expansion.py` — `JS_EXTRA` list of 60 authored lessons.
- `scripts/js_expansion_assertions.mjs` — `COVERED_IDS` + `assertExpansionExample(page, example, addCheck) -> bool`.

Not touched by this worker: `scripts/emit_content.py`, `scripts/run_examples.mjs`,
`scripts/js_example_assertions.mjs`, `assets/content/*.json`, `lib/**`, `test/**`,
existing curriculum data modules. Root owns integration into the emit pipeline,
argument passing in the runner, aggregate regeneration and commits.

## 1. Baseline audit (current source, re-run 2026-10-22)

Ran the real runner against the current catalog (301 entries):

```
node scripts/run_examples.mjs --report .trellis/tasks/10-22-standalone-offline-ide/research/browser-baseline-js-audit.md
```

Result recorded in `research/browser-baseline-js-audit.md`:

- Examples: 301, assertions: 1822, passed: 301, failed: 0.
- Tutorial lessons 301, distinct lesson bodies 301, lesson/example mapping issues 0.
- No external requests, no broken internal resources, no page errors.

Oracle coverage audit of `scripts/js_example_assertions.mjs` for the 101 JS ids:

- All 101 ids appear in at least one assertion table (none unhandled).
- `DOM` 61 ids, `CONSOLE` 48 ids, `INTERACTION_DOM` 32 ids; remainder use the
  targeted per-id blocks (storage, scroll, rAF, observer).
- Minimum per-entry check count for JS is 4 (marker + offline guard + resource
  guard + ≥1 semantic check), so no JS entry is marker-only.
- Existing JS ids `js-example-001…101` are fixed and stay untouched; new ids
  must therefore start at `js-example-102` and end at `js-example-161`.

Conclusion: the JS baseline is green and semantically covered. Baseline repairs
are not required from this worker, and new authoring cannot collide with it
because the new ids are strictly greater than every existing id.

## 2. Authoring rules applied

1. Each lesson is a complete, standalone, offline HTML5 document with inline
   CSS + inline `<script>`; `type: html`, `language: javascript`. No external
   request of any kind (no CDN, font, image URL, fetch to a remote origin, no
   `http(s)://` resource reference).
2. Full schema per lesson: `t`, `level`, `obj`, `pre`, `con`, `explain`, `code`,
   `out`, `pit`, `ex` (prompt/hint/answer triples) — identical to the shape
   consumed by `emit_content.build()`.
3. No two lessons share a document body; no placeholder/`TODO`/`第 N 课` number
   templates; each topic is a genuinely different browser API or JS technique.
4. Assertions must be concrete and per-id: exact DOM text, exact console line,
   computed style value, attribute value, or the observable result of a real
   interaction driven inside the oracle (click/type/input/change/keydown).
   "Non-empty", "element exists", or the check marker alone is never enough.
5. No companion fixture files: everything is inline in the single document, so a
   missing asset can never be masked by a runner-only fixture.
6. Interactions the oracle drives are idempotent and independent of the runner's
   generic stimulus ordering; wherever a handler is order-sensitive the oracle
   first resets the observable state (e.g. sets the field, dispatches one event).

## 3. Topic plan (ids in order)

Each entry states the technique and the concrete, oracle-checkable outcome.
IDs are positional: `102 + index`, i.e. list item 1 → `js-example-102`.

| # | id | Topic | Oracle evidence |
| --- | --- | --- | --- |
| 1 | 102 | `structuredClone` 深拷贝内置类型 | `#out` exact text for clone of Map/Date/nested object; log line |
| 2 | 103 | `Object.groupBy` 分组 | `#out` exact JSON of grouped arrays |
| 3 | 104 | `Array.prototype.at` 负索引 | `#out` exact joined values |
| 4 | 105 | `Array.prototype.flatMap` 展开映射 | `#out` exact list |
| 5 | 106 | `Array.prototype.findLast` / `findLastIndex` | `#out` exact `value/index` |
| 6 | 107 | `Array.prototype.toSorted` / `toReversed` 不可变 | `#out` exact `sorted\|original` |
| 7 | 108 | `String.prototype.replaceAll` 与回调 | `#out` exact replaced text |
| 8 | 109 | 正则命名捕获组 `(?<name>…)` | `#out` exact groups JSON |
| 9 | 110 | 正则后行断言 `(?<=…)`/`(?<!…)` | `#out` exact extraction |
| 10 | 111 | `String.raw` 与转义保持 | `#out` exact raw text |
| 11 | 112 | `Intl.NumberFormat` 百分比与单位 | `#out` exact formatted string |
| 12 | 113 | `Intl.DateTimeFormat` 相对时间/时区固定 | `#out` exact date text (UTC fixed) |
| 13 | 114 | `Intl.ListFormat` / `RelativeTimeFormat` | `#out` exact conjunction text |
| 14 | 115 | `Intl.Collator` 排序（中文 pinyin 关闭，固定 en）| `#out` exact sorted order |
| 15 | 116 | `Number.prototype.toFixed` 与 `Intl` 差异 | `#out` exact both |
| 16 | 117 | `BigInt` 精确整数运算 | `#out` exact huge number |
| 17 | 118 | `Symbol` 与 `Symbol.iterator` 自定义迭代 | `#out` exact spread result |
| 18 | 119 | 生成器委托 `yield*` 与 `return` 值 | `#out` exact collected values |
| 19 | 120 | 异步生成器 `for await...of` | `#out` exact sequence + log |
| 20 | 121 | `Promise.any` / `race` 语义 | `#out` exact winner label |
| 21 | 122 | `Promise.allSettled` 结果映射 | `#out` exact status string |
| 22 | 123 | 手写 `Promise.withResolvers` 模式 | `#out` exact resolved value |
| 23 | 124 | 微任务与宏任务顺序 | `#out` exact ordering string |
| 24 | 125 | `queueMicrotask` 与渲染时机 | `#out` exact order + log |
| 25 | 126 | `AbortController` 取消定时/事件 | `#out` exact `aborted/settled` |
| 26 | 127 | `requestIdleCallback` 降级封装 | `#out` exact executed flag |
| 27 | 128 | `Element.matches` / `closest` | `#out` exact closest id |
| 28 | 129 | `dataset` 与自定义属性同步 | `#out` exact dataset JSON |
| 29 | 130 | `template` 元素与 `content.cloneNode` | `#list` innerHTML exact |
| 30 | 131 | `<dialog>` `showModal`/`close` 返回值 | dialog `open` state + `#out` |
| 31 | 132 | `:defined`/`customElements` 自定义元素生命周期 | `#out` exact lifecycle log |
| 32 | 133 | 影子 DOM（`attachShadow`）隔离样式 | shadow root text + host text |
| 33 | 134 | `Element.animate` Web Animations | animation `playState` |
| 34 | 135 | `CSS.registerProperty` 不可用降级 + `getComputedStyle` | computed value exact |
| 35 | 136 | `IntersectionObserver` 阈值统计 | `#out` exact ratio bucket |
| 36 | 137 | `ResizeObserver` 尺寸变化记数 | `#out` exact count |
| 37 | 138 | `Range` / `Selection` 文本高亮 | selection text exact |
| 38 | 139 | `DOMParser` 解析 HTML 字符串 | `#out` exact parsed title |
| 39 | 140 | `URL` / `URLSearchParams` 构造与改写 | `#out` exact url string |
| 40 | 141 | `TextEncoder`/`TextDecoder` UTF-8 | `#out` exact byte length |
| 41 | 142 | `Blob` 与 `createObjectURL` + `arrayBuffer` | blob size + type |
| 42 | 143 | `btoa`/`atob` 与 UTF-8 安全封装 | `#out` exact round-trip |
| 43 | 144 | `crypto.randomUUID` 与 `getRandomValues` 约束 | UUID v4 正则 |
| 44 | 145 | `history.pushState` 与 `popstate` | `#out` exact path + count |
| 45 | 146 | `location.hash` 解析与监听 | `#out` exact route |
| 46 | 147 | `BroadcastChannel` 自回环消息 | `#out` exact echo |
| 47 | 148 | `Worker` 内联 Blob 计算 | `#out` exact sum |
| 48 | 149 | `MessageChannel` 端口通信 | `#out` exact reply |
| 49 | 150 | `ImageData` 像素处理 | canvas painted + exact pixel |
| 50 | 151 | `OffscreenCanvas` 支持检测与降级 | `#out` exact mode |
| 51 | 152 | `Canvas` 文本测量与居中 | measured width > 0 exact bucket |
| 52 | 153 | `Path2D` 复用路径 | canvas painted + log |
| 53 | 154 | `SVG` 动态创建与属性 | SVG circle `r` exact |
| 54 | 155 | `DragEvent` DataTransfer 本地拖放 | `#out` exact dropped text |
| 55 | 156 | `PointerEvent` 统一鼠标/触摸 | `#out` exact coordinates |
| 56 | 157 | `composition`/`input` 组合输入处理 | `#out` exact composed text |
| 57 | 158 | `input type=range` 实时值绑定 | `#out` exact slider value |
| 58 | 159 | `form` 原生校验 `checkValidity` | `#out` exact validity |
| 59 | 160 | `Intl.Segmenter` 分词（不可用降级截断） | `#out` exact segment count |
| 60 | 161 | 汇总：离线特性检测报告页 | `#out` exact supported-count format |

Every lesson also prints at least one exact console line, so `CONSOLE`-style
checks stay meaningful, and every lesson exposes its result in an `#out`
element (or a concrete DOM property) that the oracle can assert exactly.

## 4. Oracle contract

```js
export const COVERED_IDS = ['js-example-102', /* … */ 'js-example-161'];
export async function assertExpansionExample(page, example, addCheck) -> boolean
```

- Returns `true` only when `example.id` is owned by this module and assertions
  ran; `false` for any other id so the caller can fall through to the legacy
  `assertJs` oracle or the markup oracle.
- `addCheck(name, ok, detail = '')` receives one entry per assertion; the number
  of checks per id is ≥ 2 and every id has at least one exact-equality check.
- The module owns its own interaction driving (typed text, clicks, range input,
  drag events, `requestAnimationFrame` settling) and never depends on the
  runner's generic stimulus.
- No id in `COVERED_IDS` may appear twice, and the set must equal the ids the
  authoring module can produce (`102…161`).

## 5. Verification performed by this worker

A throwaway harness outside the repository (never committed) loads
`JS_EXTRA`, renders each document exactly the way `emit_content.example_document`
does (marker injection), serves it from a loopback `http` server with a
non-loopback request blocker, runs it in Playwright Chromium, applies
`assertExpansionExample`, and reports per-id failures. It also proves document
uniqueness and offline purity by static scan. Results and hashes are appended to
this file under "Verification results".

## 6. Integration notes for root

1. Add `js_expansion` to the `curriculum` imports and append `js_expansion.JS_EXTRA`
   to `LANGUAGES["javascript"]` in `scripts/emit_content.py` (JS total → 161).
2. Regenerate aggregates: `python -X utf8 scripts/emit_content.py`.
3. In `scripts/run_examples.mjs`, load `js_expansion_assertions.mjs` and call
   `assertExpansionExample(page, ex, addCheck)` before the legacy `js.assertJs`
   path when it returns `true`; do not double-run both oracles for one id.
4. Keep the historical 10-15 report untouched (the runner now honours
   `--report`).

## Verification results

Run 2026-10-22 by this worker with a throwaway harness kept outside the
repository (`%TEMP%/js_export.py` + `%TEMP%/js_expansion_verify.mjs`, never
committed). The harness intentionally reproduces the production runner: the
emitter's `example_document()` marker injection, one fresh browser context per
entry, loopback-only serving with a non-loopback request blocker, same-origin
resource-failure accounting, pageerror accounting, and the runner's generic
interaction stimulus applied **before** the per-id oracle.

Module hashes (content-addressed for root's review):

| file | sha256 (first 16) |
| --- | --- |
| `scripts/curriculum/js_expansion.py` | `5bcb69333fce2590` |
| `scripts/js_expansion_assertions.mjs` | `c7520fb1cb682df0` |

Result: **60/60 entries pass, 0 failures**, reproduced on three consecutive
runs (no timing flake). Static checks:

- 60 lessons, positional ids `js-example-102 … js-example-161`, 60 unique
  titles and 60 unique document bodies.
- Appending `JS_EXTRA` to the existing 101 lessons yields 161 unique bodies and
  161 unique titles (no collision with the shipped baseline).
- Every lesson has the full schema (`t/level/obj/pre/con/explain/code/out/pit/ex`),
  three or more pitfalls, at least one complete exercise triple, an `#out`
  element, inline `<style>` + `<script>`, and no `webforge-check` marker of its
  own (the emitter injects it).
- Offline purity scan found zero `<img src>`, `<script src>`, `<link href>`,
  `fetch(`, `XMLHttpRequest`, `@import`, dynamic `import(` or `sendBeacon`. The
  only URL literals are the loopback base in `js-example-140`
  (`http://127.0.0.1:8080`, a value only, never requested) and the mandatory SVG
  namespace in `js-example-154` (`http://www.w3.org/2000/svg`). No network
  request is issued by any entry (the harness request blocker recorded zero
  blocked requests for all 60).
- Each entry produced 6–9 checks: marker, oracle-handled, at least one exact
  value assertion, offline guard, internal-resource guard, page-error guard.
  No entry relies on the marker for semantic evidence.

### Real defects found and fixed during verification

These were genuine authoring/tooling mismatches, not assertion weakening — each
was fixed at the source so the document and its stated result now agree:

1. `js-example-107`: `toReversed()` of `[3,1,2]` is `213`, not `321` (the lesson
   text was corrected, behaviour and oracle now both assert `123|213|312|392`).
2. `js-example-111`: `String.raw` of `A\tB\nC` is 7 characters, not 8; lesson
   output and oracle corrected to `…|15|5|7`.
3. `js-example-115`: `Intl.Collator` base-sensitivity keeps the input order of
   equal keys, so the sorted result is `AabBc` (document, table and oracle
   corrected).
4. `js-example-126`: the first implementation created a fresh 5s timer after
   aborting, so the page later flipped from「已取消」to「完成」and hid the
   cancellation. Reimplemented as a start/cancel toggle; the oracle now clicks
   until the observable state is cancelled and re-checks it after a delay.
5. `js-example-127`: Chromium's `IdleDeadline` exposes `timeRemaining()`, not
   `timeLeft`; the lesson, the pitfall list and the oracle now assert
   `idle-run native=true remaining=true`.
6. `js-example-139`: the document contained a literal `</body>` inside a JS
   string, which made `emit_content.example_document()` (it replaces the first
   `</body>` occurrence) inject the marker into the script source and broke the
   page with a SyntaxError. The parsed source no longer contains that tag, so
   marker injection lands on the real document end.
7. `js-example-158`: `getComputedStyle().width` resolves percentages to pixels,
   so the oracle asserts the authored inline `style.width === '80%'` instead.

Point 6 is worth flagging to root: `example_document()` uses
`str.replace("</body>", ...)` with a first-occurrence match. Any future lesson
whose code contains a literal `</body>` (for example a "parse this HTML"
lesson) will be corrupted. A `rpartition`/`rsplit` fix in the emitter, or a
guard in the content audit, would prevent the whole class. This worker did not
touch the emitter (ownership boundary).

### Per-entry oracle summary

The oracle drives its own interactions (clicks, typed text, range input, drag
events, `history.back`, scrolling, animation completion) and then asserts exact
values. Representative exact assertions:

| id | assertion |
| --- | --- |
| 102 | `#out` === `WebForge/2 clone/3 2026-01-02T03:04:05.000Z true` |
| 103 | `#out` === grouped JSON `{"web":["HTML","CSS"],"tool":["Terminal"]}` |
| 109 | named capture groups JSON incl. `byIndex` |
| 111 | `String.raw` path + three exact lengths |
| 114 | `3\|前天/3小时后/HTML、CSS和JavaScript` |
| 115 | collator vs default sort order |
| 120 | awaits async generator, then exact `1>2>3` |
| 124 | microtask/macrotask order string |
| 126 | cancelled state, re-checked after 400 ms |
| 130 | `#list.innerHTML` exact markup for both cloned rows |
| 131 | dialog `open === true`, then `returnValue === 'confirmed'` |
| 136 | observer driven by real scroll, final `fired=N ratio=1` |
| 137 | resize observer at 120px then 160px, final `count=N w=160` |
| 145 | `history` URL step + exact `popstate` state object |
| 150/152/153 | opaque canvas pixels + exact text/pixel values |
| 154 | SVG `r`/`fill` attributes exact |
| 156 | real pointer click at (+40,+20) → `x=40 y=20 type=mouse` |
| 159 | native validity matrix for valid and underflow values |

### Handover to root

1. Import `js_expansion` in `scripts/emit_content.py` and append
   `js_expansion.JS_EXTRA` to `LANGUAGES["javascript"]` (total JS → 161, ids
   102..161). Regenerate aggregates and re-run the real runner.
2. In `scripts/run_examples.mjs`, for `js-example-*` ids call
   `assertExpansionExample(page, ex, addCheck)` first; only when it returns
   `false` fall through to `js.assertJs`. Never run both for one id.
3. `COVERED_IDS` (60 ids) is exported for the runner's coverage gate; the
   `assertExpansionExample` signature matches the markup oracle convention
   `(page, example, addCheck) -> boolean`.

Nothing outside the two owned files was modified by this worker.
