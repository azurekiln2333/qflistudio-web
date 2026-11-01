# HTML expansion — baseline audit, plan and evidence

Owner: WebForge HTML expansion worker (task 10-22-standalone-offline-ide).
Scope: `scripts/curriculum/html_expansion.py` (new, 60 lessons → ids
`html-example-101..160`) and `scripts/html_expansion_assertions.mjs` (new oracle).
No aggregate assets, `emit_content.py`, `run_examples.mjs`, `main.dart`, core or
platform files are written by this work.

## 1. Baseline audit (before any authoring)

### 1.1 Procedure

1. Static inventory of the four HTML data modules + supplement via
   `scripts/curriculum/*.py` import (schema keys, duplicate titles/code bodies,
   external or missing resource references).
2. Static audit of `scripts/web_markup_assertions.mjs`: id coverage vs
   `assets/content/examples.json`, stale ids, per-case assertion counts, marker-only
   or self-comparing checks.
3. Real execution of the full shipped catalog with the product runner
   (`node scripts/run_examples.mjs --report .trellis/tasks/10-22-standalone-offline-ide/research/browser-baseline.md`).
   The runner always rewrites its historical canonical report; that file was
   backed up before the run and restored byte-identically afterwards (SHA256
   `90F8437F…` before and after, `git status` clean for that task), so no
   foreign task artifact was modified.

### 1.2 Result: baseline is green

`.trellis/tasks/10-22-standalone-offline-ide/research/browser-baseline.md`

```
Runner: Playwright Chromium. Examples: 301. Assertions: 1822. Passed: 301. Failed: 0.
Tutorial lessons: 301. Distinct lesson bodies: 301. Lesson/example mapping issues: 0.
```

| Check | Result |
| --- | --- |
| Shipped examples executed in Chromium | 301/301 pass, 0 page errors |
| Lesson ↔ example body mapping | 0 issues, 301 distinct lesson bodies |
| HTML oracle coverage | `HTML_CASES` covers all 100 `html-example-*` ids, 0 stale, 0 missing |
| HTML lesson schema (`t/level/obj/pre/con/explain/code/out/pit/ex`) | complete for 100/100 |
| Duplicate HTML titles / identical code bodies | 0 / 0 |
| Marker-only or self-comparing HTML checks | none (marker is only a runner sanity check) |
| HTML assertions | 410 checks over 100 HTML examples, avg 4.1 |

Baseline gate for authoring: **passed** (full 301-item run, zero failures, zero
mapping issues). Authoring below started only after this evidence existed.

### 1.3 Defects and risks found in the baseline (not fixed here — not this
worker's files; reported for the integrator/owner)

| # | Severity | Finding | Evidence | Recommendation (owner) |
| --- | --- | --- | --- | --- |
| D1 | medium | `html-example-052` ships `<link rel="preconnect" href="https://fonts.example.com">` and `<link rel="dns-prefetch" href="https://cdn.example.com">`. These are real network *hints* (TCP/DNS), not fetch requests, so the runner's `page.route` interceptor cannot observe them: the offline guard passes while the page still attempts an outbound connection. This contradicts the R10 "no external-resource entries" requirement in spirit. | `html_data3.py` lesson 18 (`HTML 元数据与预连接`) | Replace with loopback/relative hints, or keep only the attribute discussion in text and drop the external host values. Owner: WebForge HTML baseline owner. |
| D2 | low | Eight HTML oracles are thin: `html-example-035` has a single check (`heading outline order`), and 018/030/031/060/065/069/076 have two. Each check is concrete and semantic (no marker/self-compare), so they are not wrong — but coverage is below the 4.1-check average and a single regression in the unasserted part of those lessons would pass. | `web_markup_assertions.mjs` case blocks | Add 1–2 concrete assertions per case (e.g. `html-example-035`: assert the rendered font-size ladder or the presence/absence of a second `h1`). Owner: markup oracle owner. |
| D3 | low (policy) | `html-example-004`, `042`, `048`, `057`, `092`, `093` contain external `https://…` link targets and `mailto:`/`tel:` hrefs. They are never fetched (links are not requests) and the oracles never click them, so the run is truthful; but the shipped offline app still exposes clickable external navigation targets. | `html_data*.py` link lessons | Decide the product policy explicitly: either treat link-attribute teaching as exempt (and document it in the offline gate), or switch teaching targets to same-origin fragments. Owner: WebForge content policy. |
| D4 | info | Total assertion counts are not stable between runs (historical report 1820, today 1822). Traced to `css-example-073` (10 → 12 checks): that CSS oracle adds checks conditionally. No HTML case is conditional. | diff of the two reports | Make the CSS case's check count deterministic. Owner: markup oracle owner. |
| D5 | info | `html-example-006`'s intentional missing `missing.png` is the only allowlisted 404; `MISSING_RESOURCE_ALLOWLIST`/runner table are keyed by exact id + exact pathname, which is correct. No action. | `run_examples.mjs` allowlist | none |
| D6 | info | New HTML ids must keep the emit order; `emit_content.py` numbers entries by list position, so a module appended after `supplement.HTML5` continues at `html-example-101`. Any insertion in the middle would renumber existing ids and break the frozen oracle ids. | `scripts/emit_content.py` | Integrate `html_expansion.HTML_EXTRA` strictly by appending to the HTML language list. |

## 2. Authoring contract for the 60 new topics

* `scripts/curriculum/html_expansion.py` exports `HTML_EXTRA`, a list of 60 dicts
  using exactly the baseline schema keys (`t, level, obj, pre, con, explain,
  code, out, pit, ex`).
* Every `code` value is a complete, standalone, offline document
  (`<!doctype html>` … `</html>`) with `</body>` present so the emitter can
  inject its `webforge-check` marker.
* Offline discipline for all 60: no external URL in any fetched position
  (no `<link rel=preconnect|preload|dns-prefetch>`, no external `src`), all media
  inline `data:` or generated at runtime via `Blob`/`URL.createObjectURL`, only
  same-document fragment links.
* Materially distinct: each topic targets an HTML surface area the 100 baseline
  topics do not cover, and no two new topics share a document body.
* Each lesson carries goals (`obj`), concepts (`con`), prerequisites (`pre`),
  explanation (`explain`), expected result (`out`), three pitfalls (`pit`) and an
  exercise (`ex`).
* `scripts/html_expansion_assertions.mjs` exports
  `COVERED_IDS` (101..160) and `assertExpansionExample(page, example, addCheck)
  -> Promise<boolean>`, mirroring the `assertMarkupExample` contract used by
  `run_examples.mjs`. Every id gets ≥3 concrete DOM/interaction assertions
  (attributes, text, computed style, DOM API results, real event driving); no
  marker-only, no "element exists" only, no self-comparison.
* Runner integration (dispatch from `run_examples.mjs`) is **not** done here:
  the runner is root-owned. The integrator adds, for `html-example-101..160`, a
  delegation to this module before the markup oracle fallback.

## 3. Planned topic map (60)

Group A — 语义与结构（基线未覆盖的现代结构元素）

| ID | 主题 | 与基线区别 |
| --- | --- | --- |
| 101 | `hgroup` 标题组与副标题绑定 | 基线只有标题层级/大纲，无 `hgroup` |
| 102 | `search` 搜索地标与表单 | 基线 `nav`/`main`/`aside` 地标，无 `search` |
| 103 | `address` 联系信息语义与默认样式 | 基线无 `address` |
| 104 | `menu` 工具条与命令按钮 | 基线只有 `ul`/`ol`/`dl` |
| 105 | `article` + `aside` 正文与相关阅读组合 | 基线是单区块结构，无 article/aside 关系断言 |
| 106 | `nav` 面包屑与 `aria-current` | 基线导航只有列表嵌套，无层级当前项 |
| 107 | 表格 `caption` 与 `headers` 显式关联 | 基线表格只到 `thead/tbody/colspan` |
| 108 | `colgroup`/`col` 列分组与列语义 | 基线无列分组 |
| 109 | `tfoot` 合计行与表格渲染顺序 | 基线无 `tfoot` |
| 110 | `details name` 互斥手风琴 | 基线 `details` 只做单组展开 |
| 111 | `dialog` 模态与 `::backdrop` | 基线无对话框 |
| 112 | `popover` 轻量浮层与 `toggle` 事件 | 基线无 popover |

Group B — 表单关联与校验 API

| ID | 主题 | 与基线区别 |
| --- | --- | --- |
| 113 | `datalist` 输入建议与 `input.list` | 基线 `select`/`range`，无 datalist |
| 114 | `optgroup` 与 `select multiple` 多选 | 基线 `select` 无分组/多选 |
| 115 | `output` 元素与 `for` 关联计算 | 基线无 `output` 结果元素 |
| 116 | 复选框 `indeterminate` 三态 | 基线无三态语义 |
| 117 | `form` 属性把外部控件关联进表单 | 基线控件都在 `form` 内 |
| 118 | `button formaction/formmethod` 提交覆盖 | 基线只讲 button 类型 |
| 119 | `input type=image` 提交坐标 | 基线无图片提交按钮 |
| 120 | `setCustomValidity` 自定义校验消息 | 基线只到 `required`/`pattern` |
| 121 | `textarea` 尺寸/换行属性与选区 API | 基线 textarea 只做基础输入 |
| 122 | `formdata` 事件与 `FormData` 迭代 | 基线无表单数据序列化 |
| 123 | `requestSubmit(submitter)` 与提交取消 | 基线无提交 API |
| 124 | `input type=number` 步进与 `valueAsNumber` | 基线只讲范围约束属性 |

Group C — 文本、国际化与机器可读数据

| ID | 主题 | 与基线区别 |
| --- | --- | --- |
| 125 | `ruby` 注音标注 | 基线无 ruby |
| 126 | `bdi`/`bdo` 双向文本隔离 | 基线只有 `lang`/`dir` |
| 127 | `mark` 高亮与检索命中 | 基线无 mark |
| 128 | `del`/`ins` 修订记录与 `cite`/`datetime` | 基线无修订语义 |
| 129 | `s` 与 `small` 的精确语义边界 | 基线段落/强调，无废弃与细则语义 |
| 130 | `data value` 机器可读取值 | 基线无 data 元素 |
| 131 | `wbr` 长词断行与 `overflow-wrap` | 基线只讲空白合并 |
| 132 | `base` 与相对 URL 解析 | 基线无 base URI 行为 |
| 133 | `translate`/`spellcheck` 编辑语义 | 基线无翻译/拼写属性 |
| 134 | MathML `math/mrow/msup/mfrac` | 基线无 MathML |
| 135 | `<picture>` + `<source media>` 艺术指导 | 基线只讲 `srcset/sizes` |
| 136 | `sup`/`sub` 与化学/数学排版组合 | 基线 sup/sub 仅单独示例 |

Group D — 嵌入、图形与脚本加载

| ID | 主题 | 与基线区别 |
| --- | --- | --- |
| 137 | `object` 嵌入 SVG 与回退内容 | 基线无 object |
| 138 | `embed` 与 `iframe srcdoc` | 基线 iframe 只讲基础嵌套 |
| 139 | `iframe sandbox` 脚本隔离 | 基线无 sandbox 安全属性 |
| 140 | 高 DPI `canvas` 像素适配与可访问回退 | 基线 canvas 只做重绘演示 |
| 141 | 内联 SVG 可访问名 `title`/`desc`/`role` | 基线 SVG 只做图标与热点 |
| 142 | `video poster`/`playsinline` 与首帧 | 基线 multimedia 只讲基础播放控件 |
| 143 | `track` 字幕与 `VTTCue`（Blob 生成） | 基线无字幕轨 |
| 144 | 声明式 Shadow DOM `template shadowrootmode` | 基线 template 只做克隆 |
| 145 | `attachShadow` 样式作用域 `:host`/`::slotted` | 基线自定义元素只做内容渲染 |
| 146 | 自定义元素生命周期回调 | 基线自定义元素只做入门 |
| 147 | `defer`/`async`/`noscript` 脚本时序 | 基线只讲引入方式 |
| 148 | `script type=module` 作用域与 `import.meta` | 基线无模块脚本 |

Group E — 现代交互与可访问性模式

| ID | 主题 | 与基线区别 |
| --- | --- | --- |
| 149 | `aria-live` 状态区播报 | 基线 ARIA 只做基础角色/键盘 |
| 150 | `role=tablist` 标签页与键盘 | 基线无复合组件模式 |
| 151 | `aria-expanded` 披露按钮与 `aria-controls` | 基线无展开状态同步 |
| 152 | `tabindex` 焦点顺序与焦点管理 | 基线无焦点顺序断言 |
| 153 | `inert` 阻止焦点与交互 | 基线无 inert |
| 154 | `hidden="until-found"` 与 `beforematch` | 基线无 until-found |
| 155 | `contenteditable="plaintext-only"` 与输入事件 | 基线无富文本编辑 |
| 156 | `form method=dialog` 与 `returnValue` | 基线无 dialog 返回值 |
| 157 | `popover=manual` 与 `popovertargetaction` | 基线无手动浮层 |
| 158 | `aria-describedby`/`aria-errormessage` 错误关联 | 基线无错误消息关联 |
| 159 | `role=alert` 错误汇总与焦点移动 | 基线无错误汇总模式 |
| 160 | 综合实战：离线工单面板 | 基线综合实战是静态骨架/文章页 |

## 4. Verification plan for the new 60

1. `python -X utf8 scripts/curriculum/…` import check: 60 entries, schema keys
   complete, unique titles, unique code bodies, ids 101..160 by position.
2. Offline lint over all 60 documents: no `http(s)://` in fetched positions, no
   `preconnect`/`dns-prefetch`/`preload` of external hosts, no relative `src`,
   every document has `</body>` and a `<title>`.
3. Task-local Playwright harness (does not touch `run_examples.mjs` or the
   aggregate JSON): serve each of the 60 documents with the emitter's marker
   injection, apply `assertExpansionExample`, and require ≥3 checks per id, zero
   failures, zero external requests and zero broken internal resources.
4. Record per-id results in `research/html-expansion-verification.md`.

## 5. Handoff status (read-only summary; ownership transferred)

Ownership of `scripts/curriculum/html_expansion.py` and
`scripts/html_expansion_assertions.mjs` has been handed to the native independent
checker. No further edits were made by the original author after the transfer
request, and no commit was made for these two files.

### 5.1 What is delivered (statically verified, read-only)

| Item | State |
| --- | --- |
| `scripts/curriculum/html_expansion.py` → `HTML_EXTRA` | 60 entries, ids `html-example-101..160` by position |
| Schema keys (`t/level/obj/pre/con/explain/code/out/pit/ex`) | complete for 60/60 |
| Levels | 19 `intermediate`, 41 `advanced` |
| Unique titles / unique code bodies | 60 / 60 |
| Complete documents (`<!doctype html>` … `</html>`, contains `</body>`) | 60/60 |
| 3 pitfalls + 1 exercise (prompt/hint/answer) per lesson | 60/60 |
| Title overlap with the 100 baseline HTML topics | 0 |
| `scripts/html_expansion_assertions.mjs` | exports `COVERED_IDS` (60 ids, 101..160) and `assertExpansionExample(page, example, addCheck)` |
| Integrated catalog (root-owned emit) | `assets/content/examples.json` = 481 entries, html = 160 (`html-example-001..160`) |

Two plan rows drifted during authoring and are correct as shipped:

* id 137 is `object 嵌入文档与回退内容` (not “object 嵌入 SVG”): `data:` URLs are
  opaque origins, so `contentDocument` is `null`; the lesson now embeds a runtime
  `blob:` HTML document (same origin) and teaches the opaque-origin caveat.
* id 156 is `combobox 与 aria-activedescendant` (not “form method=dialog”): the
  dialog `returnValue` pattern is already covered by id 111, so 156 covers the
  ARIA combobox/listbox pattern instead.

### 5.2 Known blocker in the oracle (must be fixed before the 60 can pass)

22 checks were written as `(await text(page, sel)).then((s) => …)`. `text()` is an
`async` helper, so the `await` already unwraps it and the result is a plain
string: `.then` is not a function → `TypeError` is thrown inside the case
function, the case aborts, and the runner records a setup failure for that id.

Affected line numbers (current file) → ids:

| lines | ids |
| --- | --- |
| 174 | 109 |
| 267 | 115 |
| 325 | 119 |
| 346, 350 | 121 |
| 360, 361 | 122 |
| 438 | 127 |
| 530 | 135 |
| 564 | 137 |
| 577 | 138 |
| 654 | 143 |
| 684 | 146 |
| 708, 709 | 148 |
| 771 | 152 |
| 820, 821 | 155 |
| 851 | 157 |
| 873 | 158 |
| 892 | 159 |
| 899 | 160 |

Safe fix (mechanical, no scanner needed): add the helper

```js
const probeText = async (page, sel, fn) => Boolean(fn((await text(page, sel)) || ''));
```

and rewrite each site by hand, e.g.

```js
// before
addCheck('probe reports marks', (await text(page, '#state')).then((s) => s.includes('mark 数=2')));
// after
addCheck('probe reports marks', await probeText(page, '#state', (s) => s.includes('mark 数=2')));
```

**Do not run `research/fix_then_probes.mjs`.** It is the abandoned transform: its
`__SKIP__` masking re-inserts the original marker, so `indexOf` finds the same
site forever (confirmed twice; both processes had to be killed). It never wrote
the file, so the oracle source is intact. The file can be deleted.

### 5.3 Content corrections already applied (before the handoff)

* 102, 149, 160: page-level `var status = document.getElementById('status')`
  silently failed because `window.status` is a string accessor — renamed to
  `statusEl`. This was a real runtime bug (the click/announce handlers threw).
* 119: `<p id="meta">` was declared after the script that writes it → moved
  above the script.
* 137: reworked from `data:image/svg+xml` (opaque origin, `contentDocument`
  `null`) to a runtime `blob:` HTML document; `type` is now `text/html`.
* 145: the shadow `<slot name="label">` string lost its quotes through a Python
  escape and produced invalid JS (`SyntaxError`); now uses single quotes inside
  the double-quoted JS string.
* 160: `document.querySelector('details[name=\'panel\']')` emitted unescaped
  quotes (`SyntaxError`) → uses `document.querySelector('details')`.
* 126: authored expectation corrected to the real Chromium values
  (`user=isolate/rtl`, `bdo=isolate-override/rtl`, `auto=isolate/rtl`).
* 136: authored probe now prints `sub 数=3 / sup 数=4` and
  `下标在电荷前=true` (the previous expression mislabelled the order).

### 5.4 Remaining expectation mismatches the checker must reconcile

Measured in Playwright 1.64 Chromium, viewport 1280×720, `devicePixelRatio` 1.
These are oracle expectation problems, not content defects:

| id | Issue | Corrected expectation |
| --- | --- | --- |
| 109 | `table.tFoot.id` is `''`, not `undefined` | assert `table.tFoot.tagName === 'TFOOT'` |
| 125 | ruby box does **not** grow for the annotation (box height 21, `rt` height 10) | drop `height > 24`; assert `rt` display `ruby-text` + `rt` width > 0 |
| 126 | computed values are `isolate/rtl`, `isolate-override/rtl`, `isolate/rtl` | see §5.3 |
| 134 | `math` computed display is `block math`; `mfrac` height is 17 | assert display contains `math`, `mfrac` has 2 children, fraction width > 0 |
| 136 | counts are 3 `sub` / 4 `sup` | assert 3 / 4 |
| 140 | `getBoundingClientRect().width` is 152 (1px border), `clientWidth` is 150; canvas `innerText` is empty | assert `clientWidth/clientHeight`; read fallback text via `textContent` |
| 141 | SVG `<title>`/`<desc>` `innerText` is empty (not rendered) | read `textContent` via `page.evaluate` |
| 144 | Playwright CSS locators pierce open shadow roots, so `#card h3` matches the shadow heading | count light-DOM headings with `page.evaluate(() => card.querySelectorAll('h3').length)` |
| 157 | outside-click uses fixed `(1000, 650)` | compute a point outside the popover box, or keep a 1280×720 viewport |
| 152 | assumes a fresh context with focus on `body` and no `autofocus` | keep a fresh context per example (the runner already does) |
| 143 | text-track cues load asynchronously | poll `textTracks[0].cues.length` (the harness waits up to 4s) |
| 135 | `picture` picks the 300-wide crop only at viewport ≥ 600px | run at ≥ 600px, or make the expectation viewport-aware |
| 132 | the lesson's relative anchor `notes/today.html` must never be clicked (it would 404) | assert attributes only |

### 5.5 Environment and runner behaviours worth knowing

* 139 (`iframe sandbox`) produces a **console** error (“Blocked script execution …
  because the document's frame is sandboxed”). That is the demonstrated behaviour,
  not a defect. `run_examples.mjs` records only `pageerror`, so it passes there; a
  harness that fails on console errors must allowlist this exact message for 139.
* `data:` SVG payloads contain `http://www.w3.org/2000/svg` as an XML namespace
  inside a `data:` URI. It is never requested. An offline linter must not flag it
  (the 100 baseline HTML topics do the same).
* 137 depends on `blob:` being allowed by the runner's route guard. `run_examples.mjs`
  already allows `data:`, `blob:` and `about:`.
* 152/157/150/156 drive real keyboard/mouse input; they must not run under a
  shared page that already has focus elsewhere.

### 5.6 Evidence on record (stale, must be regenerated)

`research/html-expansion-verification.md` records the only real run of the 60
documents: **60 documents / 629 assertions / 31 pass / 29 fail**, executed before
§5.3 content fixes and before the §5.2 oracle fix. It is therefore stale: 22 of
the failures are the `.then` TypeError, and the rest are the §5.4 expectation
mismatches plus the pre-fix content bugs. Regenerate it after fixing §5.2 and
§5.4; the harness is `research/html_expansion_harness.mjs` (it injects the
emitter marker, blocks every non-loopback request, fails on same-origin 4xx and
requires ≥4 checks per id), and
`research/dump_html_expansion.py` regenerates `html-expansion-documents.json`
from the current module.

### 5.7 Task-local artifacts left in `research/`

Owned by this work (safe to keep or delete):
`dump_html_expansion.py`, `html_expansion_harness.mjs`, `diag_html_expansion.mjs`,
`html-expansion-documents.json`, `html-expansion-verification.md`, `tmp_*.py`,
`tmp_*.cjs`, `tmp_code*.txt`, and `fix_then_probes.mjs` (**unsafe, delete**).
The rest of the directory belongs to other workers.
