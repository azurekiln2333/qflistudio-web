"""Authored JavaScript expansion curriculum: 60 new offline topics.

Boundary contract (see .trellis/tasks/10-22-standalone-offline-ide/research/
js-expansion.md):

* This module is the single owner of `JS_EXTRA`. It is NOT imported by
  `scripts/emit_content.py` yet; root appends it to `LANGUAGES["javascript"]`.
* IDs are positional: index 0 -> `js-example-102` ... 59 -> `js-example-161`,
  because the shipped JavaScript baseline already occupies 001..101.
* Every entry is a complete, standalone, offline HTML5 document with inline
  CSS and inline JavaScript. No network, no companion fixtures, no assets.
* Assertions for these ids live in `scripts/js_expansion_assertions.mjs` and are
  exact (DOM text, console line, computed value or interaction result).
"""

from __future__ import annotations

import textwrap

FIRST_ID = 102
LAST_ID = 161


def _doc(source: str) -> str:
    """Strip the authoring indentation off a lesson document."""
    return textwrap.dedent(source).strip()


JS_EXTRA = [
    {
        "t": "structuredClone 深拷贝内置类型",
        "level": "advanced",
        "obj": "用 structuredClone 一次复制嵌套对象、Date 与 Set，并验证克隆与原始互不影响。",
        "pre": ["对象与数组基础", "引用类型与浅拷贝"],
        "con": ["structuredClone", "深拷贝", "Date/Set 复制", "引用独立"],
        "explain": "`structuredClone(value)` 是浏览器内置的结构化克隆：它按值递归复制对象，能处理 Date、Map、Set、ArrayBuffer 等结构化类型，也自动处理循环引用。与 `JSON.parse(JSON.stringify(x))` 相比，它不会把 Date 变成字符串、不会丢掉 Set，也不会因为循环引用而抛错。克隆出来的对象与原对象完全独立，修改副本不会影响原件。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>structuredClone 深拷贝</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #eef3ff; }
            </style>
            </head>
            <body>
              <h1>structuredClone 深拷贝内置类型</h1>
              <p>克隆后分别修改 name 与 tags，观察原始对象保持不变。</p>
              <output id="out"></output>
              <script>
                const source = {
                  name: 'WebForge',
                  when: new Date('2026-01-02T03:04:05Z'),
                  tags: new Set(['html', 'css']),
                };
                const copy = structuredClone(source);
                copy.tags.add('js');
                copy.name = 'clone';
                const text = [
                  source.name + '/' + source.tags.size,
                  copy.name + '/' + copy.tags.size,
                  copy.when.toISOString(),
                  copy.when !== source.when,
                ].join(' ');
                document.getElementById('out').textContent = text;
                console.log('clone', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `WebForge/2 clone/3 2026-01-02T03:04:05.000Z true`：原始对象仍是 2 个标签，副本有 3 个；日期被真正复制而不是共享引用。",
        "pit": [
            "structuredClone 不能复制函数、DOM 节点和原型链上的方法，遇到会抛 DataCloneError。",
            "它复制的是值语义，类实例会退化成普通对象，需要自行恢复原型。",
            "JSON 深拷贝会把 Date 变成字符串、丢掉 Set/Map，不能当作等价替代。",
        ],
        "ex": [
            [
                "把 source 改成包含循环引用的对象，验证 structuredClone 仍然成功。",
                "让 source.self = source 再克隆。",
                "const a = { name: 'x' }; a.self = a; const b = structuredClone(a); b.self === b 为 true。",
            ],
        ],
    },
    {
        "t": "Object.groupBy 分组聚合",
        "level": "intermediate",
        "obj": "用 Object.groupBy 按字段把数组分成若干组，并输出每组名称。",
        "pre": ["数组 map/filter", "对象键值"],
        "con": ["Object.groupBy", "分组", "回调返回值作键", "null 原型对象"],
        "explain": "`Object.groupBy(items, callback)` 遍历数组，把 `callback` 的返回值当作分组键，返回一个「键 → 元素数组」的对象。它等价于手写 `reduce` 里不断 push 的写法，但语义更直接、不会漏掉空组处理逻辑。返回对象使用 null 原型，因此可以安全地使用 `__proto__` 之类的键。分组结果是新数组，不会修改原始数据。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>Object.groupBy 分组</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #eef7ee; }
            </style>
            </head>
            <body>
              <h1>Object.groupBy 分组聚合</h1>
              <p>三个条目按部门分成两组。</p>
              <output id="out"></output>
              <script>
                const rows = [
                  { dept: 'web', name: 'HTML' },
                  { dept: 'web', name: 'CSS' },
                  { dept: 'tool', name: 'Terminal' },
                ];
                const grouped = Object.groupBy(rows, (row) => row.dept);
                const summary = JSON.stringify({
                  web: grouped.web.map((row) => row.name),
                  tool: grouped.tool.map((row) => row.name),
                });
                document.getElementById('out').textContent = summary;
                console.log('groupBy', summary);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `{\"web\":[\"HTML\",\"CSS\"],\"tool\":[\"Terminal\"]}`，两个分组各自保留原有顺序。",
        "pit": [
            "返回对象没有原型，直接调用 grouped.hasOwnProperty 会报错。",
            "键会被转换成字符串，用对象当键会得到 '[object Object]'。",
            "分组不排序，组的出现顺序取决于元素首次出现的顺序。",
        ],
        "ex": [
            [
                "按 level 把示例按 beginner/advanced 分组，并统计每组的条目数。",
                "分组后用 Object.entries 遍历。",
                "Object.entries(Object.groupBy(list, (x) => x.level)).map(([k, v]) => k + ':' + v.length)",
            ],
        ],
    },
    {
        "t": "Array.prototype.at 负索引取值",
        "level": "beginner",
        "obj": "用 at 支持负索引，正序、倒数同时取值且不修改原数组。",
        "pre": ["数组下标访问", "数组长度"],
        "con": ["at", "负索引", "越界返回 undefined", "可读性"],
        "explain": "`arr.at(index)` 与 `arr[index]` 的区别只有负索引：`at(-1)` 表示最后一个元素，`at(-2)` 表示倒数第二个。手写下标时必须写 `arr[arr.length - 1]`，既长又容易漏括号。`at` 越界时返回 `undefined`，不会抛错，因此可以配合可选链安全读取。它对字符串同样可用。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>at 负索引</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #fff4e5; }
            </style>
            </head>
            <body>
              <h1>Array.prototype.at 负索引取值</h1>
              <p>同一个数组用正索引和负索引各取三次。</p>
              <output id="out"></output>
              <script>
                const letters = ['甲', '乙', '丙', '丁', '戊'];
                const picked = [
                  letters.at(0),
                  letters.at(-1),
                  letters.at(-3),
                  letters[letters.length - 1],
                ];
                const text = picked.join('|') + ' 长度=' + letters.length;
                document.getElementById('out').textContent = text;
                console.log('at', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `甲|戊|丙|戊 长度=5`：`at(-1)` 与 `arr[arr.length-1]` 结果一致，而 `at(-3)` 取到正中间的「丙」。",
        "pit": [
            "at 返回元素本身，不能用于写入；赋值仍需用下标。",
            "负索引超出范围时返回 undefined，静默失败容易埋下 bug。",
            "at 不改变原数组，也不返回新数组，链式操作时要注意类型。",
        ],
        "ex": [
            [
                "用 at 取出字符串 'WebForge' 的首尾字符。",
                "字符串同样有 at 方法。",
                "'WebForge'.at(0) + 'WebForge'.at(-1) 得到 'We'。",
            ],
        ],
    },
    {
        "t": "Array.prototype.flatMap 映射并展平",
        "level": "intermediate",
        "obj": "用 flatMap 一步完成「映射 + 展平一层」，把嵌套条目变成扁平静态列表。",
        "pre": ["数组 map", "嵌套数组"],
        "con": ["flatMap", "展平一层", "空数组贡献 0 项", "链式处理"],
        "explain": "`flatMap` 等价于先 `map` 再 `flat(1)`：回调返回数组时会被摊平一层，返回空数组就等于跳过该项，非常适合「一个元素展开成多个」的场景，比如菜单分组展开成条目。它只展平一层，深层嵌套仍需再调用 `flat`；回调里的返回长度可以不同，这是它比 `map` 更适合做过滤+展开的原因。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>flatMap 映射展平</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #eef0ff; }
            </style>
            </head>
            <body>
              <h1>Array.prototype.flatMap 映射并展平</h1>
              <p>三个分组展开成三条带分组前缀的条目。</p>
              <output id="out"></output>
              <script>
                const menus = [
                  { group: '基础', items: ['变量', '函数'] },
                  { group: '进阶', items: ['闭包'] },
                  { group: '空', items: [] },
                ];
                const names = menus.flatMap((menu) =>
                  menu.items.map((item) => menu.group + ':' + item),
                );
                const text = names.join(',') + ' 共' + names.length + '项';
                document.getElementById('out').textContent = text;
                console.log('flatMap', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `基础:变量,基础:函数,进阶:闭包 共3项`：空分组自动贡献 0 项，不需要额外判断。",
        "pit": [
            "flatMap 只展平一层，返回 [[1],[2]] 仍会留下内层数组。",
            "回调必须返回可迭代值；返回 null/undefined 会被当作空数组处理，容易漏数据。",
            "它会跳过稀疏数组的空位，与 map 后再 flat 的细节略有不同。",
        ],
        "ex": [
            [
                "把「一个关键词对应多个同义词」的映射表展开成同义词列表。",
                "回调返回 synonyms 数组。",
                "dict.flatMap((entry) => entry.synonyms)",
            ],
        ],
    },
    {
        "t": "findLast 与 findLastIndex 从后查找",
        "level": "intermediate",
        "obj": "用 findLast/findLastIndex 从数组尾部查找满足条件的元素与下标。",
        "pre": ["数组 find/findIndex", "回调谓词"],
        "con": ["findLast", "findLastIndex", "从后遍历", "未命中返回 undefined/-1"],
        "explain": "`find` 从头找第一个匹配项，`findLast` 从尾部找最后一个匹配项，`findLastIndex` 则返回它的下标。它们在「取最近一次记录」「取最后一个可用版本」这类需求里比 `filter().pop()` 更省内存，也不会创建中间数组。未命中时分别返回 `undefined` 与 `-1`。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>findLast 从后查找</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #fdeef0; }
            </style>
            </head>
            <body>
              <h1>findLast 与 findLastIndex 从后查找</h1>
              <p>在 [3, 8, 12, 5, 20, 7] 中找最后一个偶数。</p>
              <output id="out"></output>
              <script>
                const numbers = [3, 8, 12, 5, 20, 7];
                const lastEven = numbers.findLast((n) => n % 2 === 0);
                const lastEvenIndex = numbers.findLastIndex((n) => n % 2 === 0);
                const missing = numbers.findLast((n) => n > 100);
                const text =
                  lastEven + '@' + lastEvenIndex + ' 缺失=' + String(missing);
                document.getElementById('out').textContent = text;
                console.log('findLast', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `20@4 缺失=undefined`：最后一个偶数是下标 4 的 20，找不到时返回 undefined。",
        "pit": [
            "findLastIndex 未命中返回 -1，直接拿来当数组下标会取到最后一个元素。",
            "回调里不要依赖遍历顺序做副作用，从后遍历的顺序与 for 循环相反。",
            "空数组调用不会抛错，只是立刻返回 undefined/-1。",
        ],
        "ex": [
            [
                "在提交记录里找最后一次失败的下标。",
                "用 findLastIndex 配合 status === 'failed'。",
                "commits.findLastIndex((c) => c.status === 'failed')",
            ],
        ],
    },
    {
        "t": "toSorted 与 toReversed 不可变排序",
        "level": "intermediate",
        "obj": "用 toSorted/toReversed/toSpliced 得到新数组，验证原数组保持不变。",
        "pre": ["数组 sort/reverse/splice", "不可变更新"],
        "con": ["toSorted", "toReversed", "toSpliced", "原数组不变"],
        "explain": "`sort`、`reverse`、`splice` 都会原地修改数组，在 React 之类的状态管理里容易引发「数据没变但引用没换」的 bug。`toSorted`、`toReversed`、`toSpliced` 是它们的不可变版本：返回新数组，原数组完全不动。这样既能拿到排序结果，又能保留原始顺序用于对比或回滚。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>不可变排序</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #eafaf5; }
            </style>
            </head>
            <body>
              <h1>toSorted 与 toReversed 不可变排序</h1>
              <p>依次展示：升序结果、倒序结果、原始数组、替换下标 1 后的结果。</p>
              <output id="out"></output>
              <script>
                const origin = [3, 1, 2];
                const sorted = origin.toSorted((a, b) => a - b);
                const reversed = origin.toReversed();
                const spliced = origin.toSpliced(1, 1, 9);
                const text = [
                  sorted.join(''),
                  reversed.join(''),
                  origin.join(''),
                  spliced.join(''),
                ].join('|');
                document.getElementById('out').textContent = text;
                console.log('immutable', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `123|213|312|392`：升序 123、倒序 213（原数组是 3,1,2）、原始数组仍是 312、替换下标 1 后为 392 —— 四个结果互不影响。",
        "pit": [
            "toSorted 默认按字符串比较，数字必须显式传 (a, b) => a - b。",
            "这些方法只做浅拷贝，元素是对象时对象本身仍共享。",
            "旧环境可能没有这些方法，需要先检测或用展开 + sort 兜底。",
        ],
        "ex": [
            [
                "用 toSpliced 删除下标 0 的元素并插入两个新元素。",
                "第二个参数是删除个数。",
                "origin.toSpliced(0, 1, 7, 8) 得到 [7, 8, 1, 2]。",
            ],
        ],
    },
    {
        "t": "replaceAll 结合回调批量替换",
        "level": "intermediate",
        "obj": "用 replaceAll 配合回调，把模板中的占位符一次性替换成真实数据。",
        "pre": ["字符串 replace", "正则表达式基础"],
        "con": ["replaceAll", "回调参数", "全局正则", "模板填充"],
        "explain": "`replaceAll(searchValue, replacement)` 会替换所有匹配位置，避免 `replace` 只换第一个的坑。当 `searchValue` 是带 `g` 的正则时，`replacement` 可以是函数，收到（匹配文本, 捕获组…）并返回替换值；这样就能用一个字典把 `{name}`、`{day}` 这类占位符整体映射成数据，比自己手写循环拼接更清晰。",
        "code": _doc(
            r"""
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>replaceAll 模板填充</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #f0f4ff; }
            </style>
            </head>
            <body>
              <h1>replaceAll 结合回调批量替换</h1>
              <p>模板里的 name 与 day 占位符被字典值替换。</p>
              <output id="out"></output>
              <script>
                const template = 'Hello {name}, today is {day}.';
                const values = { name: '小明', day: '周五' };
                const text = template.replaceAll(/\{(\w+)\}/g, (whole, key) =>
                  Object.prototype.hasOwnProperty.call(values, key) ? values[key] : whole,
                );
                document.getElementById('out').textContent = text;
                console.log('rendered', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `Hello 小明, today is 周五.`：两个占位符全部被替换，标点与空格保留。",
        "pit": [
            "replaceAll 的第一个参数是字符串时，不会处理特殊字符；要匹配模式必须传带 g 的正则。",
            "回调返回 undefined 会被当成字符串 'undefined' 插入，未命中时应返回原文本。",
            "用户数据直接回填到 HTML 时需要先转义，否则会引入 XSS。",
        ],
        "ex": [
            [
                "给字典增加一个 {city} 占位符并让模板填充它。",
                "在模板字符串里加入 {city}，并在 values 里补上键。",
                "values.city = '杭州'，模板改成 '... in {city}' 即可自动替换。",
            ],
        ],
    },
    {
        "t": "正则命名捕获组",
        "level": "intermediate",
        "obj": "用 (?<name>…) 命名捕获组，从日期字符串里取出年、月、日。",
        "pre": ["正则基本语法", "exec 返回值"],
        "con": ["命名捕获组", "m.groups", "可读性", "解构取值"],
        "explain": "普通捕获组只能靠位置访问（`m[1]`、`m[2]`），组一多就难以对应。命名捕获组写成 `(?<year>\\d{4})`，匹配结果会多出一个 `groups` 对象，用名字直接取值，并且可以用解构一次性取出所有字段。位置的数字下标仍然保留，因此可以向后兼容旧代码。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>命名捕获组</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #f5f0ff; }
            </style>
            </head>
            <body>
              <h1>正则命名捕获组</h1>
              <p>从 2026-10-22 中抽出年、月、日。</p>
              <output id="out"></output>
              <script>
                const pattern = /(?<year>\\d{4})-(?<month>\\d{2})-(?<day>\\d{2})/;
                const match = pattern.exec('发布于 2026-10-22 上午');
                const { year, month, day } = match.groups;
                const text = JSON.stringify({ year, month, day, byIndex: match[1] });
                document.getElementById('out').textContent = text;
                console.log('groups', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `{\"year\":\"2026\",\"month\":\"10\",\"day\":\"22\",\"byIndex\":\"2026\"}`：名字与位置下标同时可用。",
        "pit": [
            "命名不能重复，同一个正则里两个同名组会直接 SyntaxError。",
            "未参与匹配的可选组在 groups 里值是 undefined，不是空字符串。",
            "exec 在无 g 标志时不重置 lastIndex，多组匹配要自己循环。",
        ],
        "ex": [
            [
                "把日期格式改成 YYYY/MM/DD 也能匹配。",
                "把分隔符写成一个字符类。",
                "/(?<year>\\d{4})[-/](?<month>\\d{2})[-/](?<day>\\d{2})/",
            ],
        ],
    },
    {
        "t": "后行断言提取数值",
        "level": "advanced",
        "obj": "用 (?<=…) 后行断言只提取标记后面的数字，不把标记带进结果。",
        "pre": ["正则断言", "matchAll"],
        "con": ["后行断言", "matchAll", "零宽断言", "数值抽取"],
        "explain": "后行断言 `(?<=¥)` 要求前面是 ¥ 但自身不消耗字符，所以匹配结果里只有数字本身，不需要再写捕获组或 `slice` 去掉前缀。配合 `matchAll` 可以拿到所有出现位置，再统一转成数字做统计。反向写法 `(?<!…)` 是「前面不是」，可用来排除干扰项。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>后行断言</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #fffbe6; }
            </style>
            </head>
            <body>
              <h1>后行断言提取数值</h1>
              <p>从一句账单里抽出所有 ¥ 后面的金额并求和。</p>
              <output id="out"></output>
              <script>
                const bill = '价格 ¥120，折扣 ¥30，运费 ¥0';
                const prices = [...bill.matchAll(/(?<=¥)\\d+/g)].map((m) => Number(m[0]));
                const total = prices.reduce((sum, n) => sum + n, 0);
                const text = prices.join('+') + '=' + total;
                document.getElementById('out').textContent = text;
                console.log('prices', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `120+30+0=150`：三个金额都被无前缀地提取出来，合计 150。",
        "pit": [
            "后行断言要求固定宽度时性能最好，变长写法在部分引擎里会抛错。",
            "旧版 Safari 不支持后行断言，需要考虑先捕获再切片。",
            "matchAll 的正则必须带 g 标志，否则会抛 TypeError。",
        ],
        "ex": [
            [
                "用 (?<!\\d)\\d+ 只匹配不是紧跟在数字后面的数字。",
                "在 120 里它只会匹配到 1。",
                "'120'.match(/(?<!\\d)\\d+/g) 得到 ['1']。",
            ],
        ],
    },
    {
        "t": "String.raw 保留反斜杠",
        "level": "beginner",
        "obj": "用 String.raw 标签模板保留 Windows 路径里的反斜杠，并与普通模板对比长度。",
        "pre": ["模板字符串", "转义字符"],
        "con": ["String.raw", "标签模板", "转义序列", "路径拼接"],
        "explain": "普通模板字符串里 `\\t`、`\\n`、`\\f` 会被当作转义序列，写路径时极易出错。`String.raw` 是模板标签，它读取字符串的原始字符（raw），不做转义处理，因此反斜杠原样保留。对比普通模板的长度就能看出差异：普通版本里 `\\t` 变成了一个制表符，长度更短。",
        "code": _doc(
            r"""
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>String.raw</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #eef6ff; white-space: pre; }
            </style>
            </head>
            <body>
              <h1>String.raw 保留反斜杠</h1>
              <p>同一个路径用两种模板写法，长度不同。</p>
              <output id="out"></output>
              <script>
                const raw = String.raw`C:\html\new\tab`;
                const escaped = 'A\tB\nC';
                const rawEscaped = String.raw`A\tB\nC`;
                const text =
                  raw + '|' + raw.length + '|' + escaped.length + '|' + rawEscaped.length;
                document.getElementById('out').textContent = text;
                console.log('raw', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `C:\\html\\new\\tab|15|5|7`：raw 路径保留 3 个反斜杠共 15 个字符；'A\\tB\\nC' 里的转义序列只算 5 个字符，而 String.raw 版本里的反斜杠被原样保留，算 7 个字符。",
        "pit": [
            "String.raw 不能写成 String.raw(...)，它是标签，必须紧跟模板字面量。",
            "raw 中的 ${} 插值仍然生效，不是完全的字面量。",
            "路径太长时注意 Windows 的 MAX_PATH 限制，与转义无关。",
        ],
        "ex": [
            [
                "用 String.raw 生成一条正则源码字符串，再传给 new RegExp。",
                "反斜杠在字符串里只需写一次。",
                r"new RegExp(String.raw`\d{2}`).test('42') 为 true。",
            ],
        ],
    },
    {
        "t": "Intl.NumberFormat 百分比与单位",
        "level": "intermediate",
        "obj": "用 Intl.NumberFormat 的 percent 与 unit 样式输出本地化数值。",
        "pre": ["数字格式化", "Intl 基础"],
        "con": ["Intl.NumberFormat", "percent", "unit", "maximumFractionDigits"],
        "explain": "`Intl.NumberFormat` 不只能加千分位：`style: 'percent'` 会把 0.256 输出为 25.6%，`style: 'unit'` 会自动拼上单位名称并处理空格。配合 `maximumFractionDigits` 可以统一小数位，避免自己写 `toFixed` 后还得手动拼单位符号。注意单位是数据而不是字符串，多语言输出由 Intl 负责。",
        "code": _doc(
            r"""
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>Intl.NumberFormat</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #f0fff4; }
            </style>
            </head>
            <body>
              <h1>Intl.NumberFormat 百分比与单位</h1>
              <p>把 0.256 格式化为百分比，把 42 格式化为时速单位。</p>
              <output id="out"></output>
              <script>
                const percent = new Intl.NumberFormat('en-US', {
                  style: 'percent',
                  maximumFractionDigits: 1,
                }).format(0.256);
                const speed = new Intl.NumberFormat('en-US', {
                  style: 'unit',
                  unit: 'kilometer-per-hour',
                  unitDisplay: 'short',
                  maximumFractionDigits: 0,
                }).format(42);
                const text = percent + '|' + speed;
                document.getElementById('out').textContent = text;
                console.log('format', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `25.6%|42 km/h`：百分比自带符号，单位自动拼接且不与数字粘连。",
        "pit": [
            "percent 样式接收的是小数（0.256），直接传 25.6 会变成 2560%。",
            "unit 的取值必须是合法的 CLDR 单位标识，随便写会在构造时抛 RangeError。",
            "每次 new 一个格式器开销不小，循环里应复用同一个实例。",
        ],
        "ex": [
            [
                "把时速改成「公里每小时」的中文短单位。",
                "将 locale 改成 zh-CN，保留 unit。",
                "new Intl.NumberFormat('zh-CN', { style: 'unit', unit: 'kilometer-per-hour', unitDisplay: 'short' }).format(42)",
            ],
        ],
    },
    {
        "t": "Intl.DateTimeFormat 固定时区格式化",
        "level": "intermediate",
        "obj": "用 formatToParts 按 UTC 固定时区拆分日期时间各部分，保证输出稳定。",
        "pre": ["Date 基础", "toISOString"],
        "con": ["Intl.DateTimeFormat", "timeZone", "formatToParts", "稳定输出"],
        "explain": "`Intl.DateTimeFormat` 默认使用运行环境的本地时区，同一份代码在不同机器上输出可能不同。显式传入 `timeZone: 'UTC'` 后结果就固定了。`formatToParts` 返回结构化的片段数组，过滤掉 separator 后拼起来，既不会受地区标点影响，也便于把年、月、日、小时单独取出来做后续处理。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>固定时区格式化</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #fff5f5; }
            </style>
            </head>
            <body>
              <h1>Intl.DateTimeFormat 固定时区格式化</h1>
              <p>把同一个时间点按 UTC 拆成年月日时分。</p>
              <output id="out"></output>
              <script>
                const moment = new Date('2026-10-22T08:30:00Z');
                const formatter = new Intl.DateTimeFormat('en-CA', {
                  timeZone: 'UTC',
                  year: 'numeric',
                  month: '2-digit',
                  day: '2-digit',
                  hour: '2-digit',
                  minute: '2-digit',
                  hour12: false,
                });
                const digits = formatter
                  .formatToParts(moment)
                  .filter((part) => part.type !== 'literal')
                  .map((part) => part.value)
                  .join('');
                const text = digits + '|' + moment.toISOString();
                document.getElementById('out').textContent = text;
                console.log('datetime', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `202610220830|2026-10-22T08:30:00.000Z`：无论运行机器在哪个时区，拆分结果都一致。",
        "pit": [
            "忘记写 timeZone 时会跟着系统时区走，测试在不同机器上会不一样。",
            "hour12 未关闭时小时会变成 12 小时制，拆分结果会多出 AM/PM 片段。",
            "format() 的标点依赖 locale，想拼固定格式应使用 formatToParts。",
        ],
        "ex": [
            [
                "额外取出 weekday 片段。",
                "在选项里加 weekday: 'short'。",
                "formatToParts 会多出 type 为 weekday 的片段。",
            ],
        ],
    },
    {
        "t": "Intl.ListFormat 与 RelativeTimeFormat",
        "level": "intermediate",
        "obj": "用 ListFormat 输出并列列表，用 RelativeTimeFormat 输出相对时间。",
        "pre": ["Intl 基础", "模板字符串"],
        "con": ["Intl.ListFormat", "Intl.RelativeTimeFormat", "formatToParts", "多语言拼接"],
        "explain": "不同语言连接并列词的符号不同：中文用「、」与「和」，英文用逗号与 and。`Intl.ListFormat` 负责这个细节，`formatToParts` 还能把元素个数单独数出来。`Intl.RelativeTimeFormat` 则把「-2 天」这类偏移量变成「前天」「2 days ago」，`numeric: 'auto'` 会优先使用语言里已有的说法。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>Intl.ListFormat</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #f6f9ff; }
            </style>
            </head>
            <body>
              <h1>Intl.ListFormat 与 RelativeTimeFormat</h1>
              <p>先数出列表中元素个数，再拼接两个相对时间。</p>
              <output id="out"></output>
              <script>
                const list = new Intl.ListFormat('zh-CN', {
                  type: 'conjunction',
                  style: 'short',
                });
                const relative = new Intl.RelativeTimeFormat('zh-CN', { numeric: 'auto' });
                const elements = list
                  .formatToParts(['HTML', 'CSS', 'JavaScript'])
                  .filter((part) => part.type === 'element').length;
                const text =
                  elements +
                  '|' +
                  relative.format(-2, 'day') +
                  '/' +
                  relative.format(3, 'hour') +
                  '/' +
                  list.format(['HTML', 'CSS', 'JavaScript']);
                document.getElementById('out').textContent = text;
                console.log('intl-list', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `3|前天/3小时后/HTML、CSS和JavaScript`：列表元素数为 3，相对时间使用语言内的自然说法。",
        "pit": [
            "format 结果的标点依赖实现，做断言时应使用 formatToParts。",
            "RelativeTimeFormat 的数值必须带单位，units 写成 'days' 会抛 RangeError。",
            "type: 'unit' 与 type: 'conjunction' 的拼接结果差别很大，不要混用。",
        ],
        "ex": [
            [
                "把 type 改成 'disjunction' 观察「或」与「和」的区别。",
                "改构造参数即可。",
                "new Intl.ListFormat('zh-CN', { type: 'disjunction' }).format(['A', 'B'])",
            ],
        ],
    },
    {
        "t": "Intl.Collator 语言感知排序",
        "level": "intermediate",
        "obj": "用 Intl.Collator 控制大小写敏感度的排序行为。",
        "pre": ["数组 sort", "比较函数"],
        "con": ["Intl.Collator", "sensitivity", "稳定排序", "语言排序规则"],
        "explain": "默认的 `sort()` 把元素当字符串按 UTF-16 码位比较，大写字母全部排在小写前面，也不符合任何语言的字典序。`Intl.Collator(locale, options)` 提供一个符合语言习惯的比较函数；`sensitivity: 'base'` 忽略大小写与重音，大小写字母被视为相等，此时浏览器稳定排序会保留它们在原数组中的相对顺序。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>Intl.Collator</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #fdf6ec; }
            </style>
            </head>
            <body>
              <h1>Intl.Collator 语言感知排序</h1>
              <p>忽略大小写排序后，结果与默认排序不同。</p>
              <output id="out"></output>
              <script>
                const words = ['b', 'A', 'c', 'B', 'a'];
                const collator = new Intl.Collator('en', { sensitivity: 'base' });
                const sorted = [...words].sort(collator.compare);
                const defaulted = [...words].sort();
                const text = sorted.join('') + '|' + defaulted.join('');
                document.getElementById('out').textContent = text;
                console.log('collator', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `AabBc|ABabc`：Collator 把大小写视为相等，相等项保留输入顺序，所以 A 在 a 前；默认 sort 则把大写全排在前面。",
        "pit": [
            "sort(collator.compare) 必须传已绑定 compare，不能传 collator 对象本身。",
            "sensitivity 越高区分越细，'variant' 会把大小写和重音都视为不同。",
            "比较函数每次调用都重新创建 Collator 实例会造成性能问题。",
        ],
        "ex": [
            [
                "把 sensitivity 改成 'case' 观察结果变化。",
                "改构造参数后重新排序。",
                "'case' 下大小写字母会分开排序，结果不再是 'AabBc'。",
            ],
        ],
    },
    {
        "t": "toFixed 与 Intl 舍入差异",
        "level": "intermediate",
        "obj": "对比 toFixed 与 Intl.NumberFormat 在二进制浮点上的舍入表现。",
        "pre": ["浮点数精度", "数字格式化"],
        "con": ["toFixed", "maximumFractionDigits", "halfExpand", "二进制精度"],
        "explain": "`toFixed` 与 `Intl.NumberFormat` 都按「四舍五入（远离零）」处理边界值，但都建立在 IEEE-754 二进制浮点之上：`0.1 + 0.2` 实际是 `0.30000000000000004`，`1.005` 实际略小于 1.005，所以 `(1.005).toFixed(2)` 得到 `1.00`。理解这一点就能避开「显示金额对不上」的经典 bug：先按整数分计算，最后再格式化。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>舍入差异</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #f2f7ff; letter-spacing: 1px; }
            </style>
            </head>
            <body>
              <h1>toFixed 与 Intl 舍入差异</h1>
              <p>依次输出：整数舍入、Intl 同样舍入、0.1+0.2、1.005 保留两位。</p>
              <output id="out"></output>
              <script>
                const integer = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 });
                const text = [
                  (2.5).toFixed(0),
                  integer.format(2.5),
                  (0.1 + 0.2).toFixed(2),
                  (1.005).toFixed(2),
                ].join('|');
                document.getElementById('out').textContent = text;
                console.log('rounding', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `3|3|0.30|1.00`：可见 0.30 是真正的 0.3000000000004 舍入而来，而 1.005 因二进制误差被舍成 1.00。",
        "pit": [
            "toFixed 返回字符串，直接参与数学运算会被隐式转换。",
            "大数（超过 1e21）的 toFixed 会退化成科学计数法字符串。",
            "金额计算应用整数分存储，只在展示时格式化。",
        ],
        "ex": [
            [
                "用 Math.round((x + Number.EPSILON) * 100) / 100 修正 1.005。",
                "先加极小的 epsilon 消除误差。",
                "Math.round((1.005 + Number.EPSILON) * 100) / 100 得到 1.01。",
            ],
        ],
    },
    {
        "t": "BigInt 大整数精确运算",
        "level": "intermediate",
        "obj": "用 BigInt 计算超出 Number 安全整数范围的精确值。",
        "pre": ["数字类型", "Number.MAX_SAFE_INTEGER"],
        "con": ["BigInt", "n 后缀", "精确整数", "typeof bigint"],
        "explain": "`Number` 只能精确表示 2^53 - 1 以内的整数，再大就会丢精度。`BigInt` 用末尾的 `n` 字面量或 `BigInt()` 声明，支持任意精度整数运算，`typeof` 得到 `'bigint'`。它与 `Number` 不能隐式混算，必须显式转换；也正因为没有小数部分，适合哈希、雪花 ID、大额计数这类场景。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>BigInt 大整数</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #f0fff7; font-family: monospace; }
            </style>
            </head>
            <body>
              <h1>BigInt 大整数精确运算</h1>
              <p>2 的 64 次方减一，再加一，全靠 BigInt 完成。</p>
              <output id="out"></output>
              <script>
                const max = 2n ** 64n - 1n;
                const next = max + 1n;
                const unsafe = Number(max) === Number(max) + 1;
                const text = max + '|' + next + '|' + typeof next + '|' + unsafe;
                document.getElementById('out').textContent = text;
                console.log('bigint', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `18446744073709551615|18446744073709551616|bigint|true`：换成 Number 后 max 与 max+1 已经无法区分，BigInt 却精确。",
        "pit": [
            "BigInt 与 Number 相加会抛 TypeError，必须 BigInt(x) 或 Number(y) 显式转换。",
            "BigInt 不支持 Math 工具函数，也不参与 JSON.stringify，需要自定义序列化。",
            "除法会直接截断小数，需要小数精度时不要用 BigInt。",
        ],
        "ex": [
            [
                "用 BigInt 计算 100 的阶乘并输出位数。",
                "用 for 循环累乘，再用 String(x).length。",
                "let r = 1n; for (let i = 2n; i <= 100n; i++) r *= i; String(r).length 为 158。",
            ],
        ],
    },
    {
        "t": "Symbol.iterator 自定义可迭代对象",
        "level": "advanced",
        "obj": "给普通对象实现 Symbol.iterator，让它能直接被展开运算符和 Array.from 使用。",
        "pre": ["Symbol 基础", "迭代器协议"],
        "con": ["Symbol.iterator", "迭代器协议", "展开运算符", "Array.from"],
        "explain": "`for...of`、展开运算符、`Array.from` 都只认一个协议：对象上有 `Symbol.iterator` 方法，调用后返回带 `next()` 的迭代器，`next()` 返回 `{ value, done }`。自己实现这个协议，就能让任意自定义结构（区间、树、分页器等）享受内建的所有迭代能力，而不需要额外写一个 toArray 方法。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>自定义迭代器</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #eef4ff; }
            </style>
            </head>
            <body>
              <h1>Symbol.iterator 自定义可迭代对象</h1>
              <p>一个普通对象实现了迭代协议后，就能被展开与 Array.from 使用。</p>
              <output id="out"></output>
              <script>
                const range = {
                  from: 1,
                  to: 4,
                  [Symbol.iterator]() {
                    let current = this.from;
                    const last = this.to;
                    return {
                      next: () =>
                        current <= last
                          ? { value: current++, done: false }
                          : { value: undefined, done: true },
                    };
                  },
                };
                const spread = [...range];
                const total = [...range].reduce((sum, n) => sum + n, 0);
                const text =
                  spread.join(',') + '|' + Array.from(range).length + '|' + total;
                document.getElementById('out').textContent = text;
                console.log('iterable', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `1,2,3,4|4|10`：同一个对象不仅能展开，还能重复迭代并求和（每次迭代都新建迭代器）。",
        "pit": [
            "迭代器必须每次返回新对象，否则第二次展开会得到空数组。",
            "对象同时也需要 length 时，要写成类数组或额外处理，不能只靠迭代器。",
            "无限迭代器配合展开运算符会直接卡死页面，慎用。",
        ],
        "ex": [
            [
                "把 range 改成支持 step 递增。",
                "在 next 里用 current += this.step。",
                "step 为 2 时展开得到 1,3。",
            ],
        ],
    },
    {
        "t": "生成器委托 yield 与返回值",
        "level": "advanced",
        "obj": "用 yield* 在一个生成器里委托另一个生成器，并把子生成器的 return 值接住。",
        "pre": ["生成器函数", "yield"],
        "con": ["yield*", "生成器委托", "return 值", "惰性求值"],
        "explain": "`yield*` 把一个可迭代对象的每个值逐个向外 yield，行为相当于内联了一个 `for...of` 加 `yield`。关键细节是：生成器函数最终的 `return` 值不会被 `for...of`/展开取到，但会被 `yield*` 表达式当作普通表达式的值传回调用方。因此可以用它实现「子任务完成后把结果交回父任务」的流程。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>生成器委托</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #fff7f0; }
            </style>
            </head>
            <body>
              <h1>生成器委托 yield*</h1>
              <p>子生成器先产出两项，再把 return 值交回父生成器继续产出。</p>
              <output id="out"></output>
              <script>
                function* inner() {
                  yield 'a';
                  yield 'b';
                  return 'inner-done';
                }
                function* outer() {
                  const result = yield* inner();
                  yield result;
                  yield 'c';
                }
                const text = [...outer()].join(',');
                document.getElementById('out').textContent = text;
                console.log('delegate', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `a,b,inner-done,c`：inner 的 return 值被 yield* 接住，成为 outer 产出的第三项。",
        "pit": [
            "直接 for...of 遍历 inner() 拿不到 return 值，这是最容易踩的坑。",
            "yield* 后面必须跟可迭代对象，传普通值会抛 TypeError。",
            "生成器的 throw/return 也会传递给被委托的生成器，记得写 finally 清理资源。",
        ],
        "ex": [
            [
                "让 inner 接受参数并以参数为前缀产出。",
                "inner 加形参，yield* inner('x')。",
                "yield* inner('x') 会产出 xa、xb。",
            ],
        ],
    },
    {
        "t": "异步生成器与 for await...of",
        "level": "advanced",
        "obj": "用 async 生成器按顺序产出异步结果，并用 for await...of 逐个消费。",
        "pre": ["生成器函数", "Promise 与 async/await"],
        "con": ["async 生成器", "for await...of", "背压", "顺序消费"],
        "explain": "`async function*` 产生的对象在 `next()` 时返回 Promise，每次 `yield` 都可以是普通值或 Promise，引擎会自动等待。消费侧用 `for await...of` 逐个拿到已解析的值，循环体本身也是异步的，因此在循环里可以安全地 await。它最适合「边拉边处理」的分页或流式场景：只有上一项处理完，才会去取下一项。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>异步生成器</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #f0f8ff; }
            </style>
            </head>
            <body>
              <h1>异步生成器与 for await...of</h1>
              <p>三个带延迟的值被按顺序消费。</p>
              <output id="out">等待中</output>
              <script>
                const wait = (value, ms) => new Promise((resolve) => setTimeout(() => resolve(value), ms));
                async function* ticks() {
                  for (const value of [1, 2, 3]) {
                    yield wait(value, 10);
                  }
                }
                (async () => {
                  const got = [];
                  for await (const value of ticks()) {
                    got.push(value);
                  }
                  const text = got.join('>');
                  document.getElementById('out').textContent = text;
                  console.log('async-iter', text);
                })();
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `1>2>3`：三个值严格按产出顺序被消费，即使中间存在 setTimeout 延迟。",
        "pit": [
            "for await 只能在 async 函数内使用，顶层使用时需包一层 IIFE。",
            "异步生成器不能被普通展开运算符直接展开。",
            "忘记 await 内部 Promise 会让消费顺序错乱。",
        ],
        "ex": [
            [
                "让生成器在值大于 2 时提前 return。",
                "在循环里加 if (value > 2) return。",
                "输出会停在 1>2。",
            ],
        ],
    },
    {
        "t": "Promise.any 与 Promise.race",
        "level": "advanced",
        "obj": "对比 Promise.any（第一个成功）与 Promise.race（第一个完成）的聚合语义。",
        "pre": ["Promise 基础", "异步并发"],
        "con": ["Promise.any", "Promise.race", "AggregateError", "最先完成"],
        "explain": "`Promise.race` 看的是「谁先定稿」，不区分成功与失败；`Promise.any` 只关心第一个**成功**的结果，只有全部失败时才以 `AggregateError` 拒绝。多源镜像取最快成功、多候选请求容错都应该用 `any`，而超时控制这种「失败也要立即返回」的场景才适合 `race`。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>Promise.any</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #fff8e6; }
            </style>
            </head>
            <body>
              <h1>Promise.any 与 Promise.race</h1>
              <p>any 取最先成功的结果，race 取最先完成的结果。</p>
              <output id="out">计算中</output>
              <script>
                const later = (value, ms) =>
                  new Promise((resolve) => setTimeout(() => resolve(value), ms));
                (async () => {
                  const firstOk = await Promise.any([later('A', 30), later('B', 5)]);
                  const firstDone = await Promise.race([later('X', 40), later('Y', 10)]);
                  const allFailed = await Promise.any([
                    Promise.reject(new Error('e1')),
                    Promise.reject(new Error('e2')),
                  ]).catch((error) => error.constructor.name);
                  const text = firstOk + '|' + firstDone + '|' + allFailed;
                  document.getElementById('out').textContent = text;
                  console.log('any-race', text);
                })();
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `B|Y|AggregateError`：any 选了更快的 B，race 选了更快的 Y，全部失败时得到 AggregateError。",
        "pit": [
            "race 中一个 Promise 拒绝就会让整个 race 拒绝，不会等其他候选。",
            "any 全部失败才拒绝，失败前会等所有 Promise 完成。",
            "未处理的 rejected Promise 会触发全局 unhandledrejection 警告。",
        ],
        "ex": [
            [
                "给 any 增加一个立即拒绝的候选，验证结果仍是 B。",
                "插入 Promise.reject(new Error('fail'))。",
                "any 会跳过拒绝的候选，仍返回 B。",
            ],
        ],
    },
    {
        "t": "Promise.allSettled 结果映射",
        "level": "advanced",
        "obj": "用 allSettled 并行执行并区分成功与失败，不会因单个失败而中断。",
        "pre": ["Promise.all", "错误处理"],
        "con": ["Promise.allSettled", "status", "fulfilled/rejected", "批量容错"],
        "explain": "`Promise.all` 只要有一个失败就整体失败，适合同步依赖一致性的批量任务；`Promise.allSettled` 则等所有任务都定稿，返回 `{ status, value | reason }` 列表，适合「尽可能完成任务并汇总报告」的场景。根据 `status` 分支就能把成功值与失败原因分开处理，不需要在 each 上挂 catch。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>allSettled</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #f4fff4; }
            </style>
            </head>
            <body>
              <h1>Promise.allSettled 结果映射</h1>
              <p>三个任务中有一个失败，其余两个仍然完成。</p>
              <output id="out">执行中</output>
              <script>
                (async () => {
                  const results = await Promise.allSettled([
                    Promise.resolve('样式表已加载'),
                    Promise.reject(new Error('脚本缺失')),
                    Promise.resolve('字体已就绪'),
                  ]);
                  const text = results
                    .map((item) =>
                      item.status === 'fulfilled'
                        ? 'ok:' + item.value
                        : 'bad:' + item.reason.message,
                    )
                    .join(',');
                  document.getElementById('out').textContent = text;
                  console.log('settled', text);
                })();
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `ok:样式表已加载,bad:脚本缺失,ok:字体已就绪`：失败项不影响其余结果，顺序与输入一致。",
        "pit": [
            "allSettled 永远不会因为单个失败而拒绝，因此不需要 try/catch。",
            "rejected 项没有 value 属性，直接取会得到 undefined。",
            "结果顺序与输入一致，不是完成先后顺序。",
        ],
        "ex": [
            [
                "统计成功与失败的个数。",
                "用 filter 分别按 status 计数。",
                "results.filter((r) => r.status === 'fulfilled').length",
            ],
        ],
    },
    {
        "t": "手动实现 Promise.withResolvers 模式",
        "level": "advanced",
        "obj": "把 resolve/reject 抽到外部，实现「先交出 Promise，稍后再定稿」的延迟模式。",
        "pre": ["Promise 构造器", "手写工具函数"],
        "con": ["Promise.withResolvers", "延迟握持", "兼容降级", "外部 resolve"],
        "explain": "原生写法里 `resolve` 只能写在 `new Promise` 的执行器内部，外部想主动完成这个 Promise 得很别扭。`Promise.withResolvers()`（新标准）或手写的等价函数把三者一起返回：`{ promise, resolve, reject }`，于是可以先把 `promise` 交给等待方，把 `resolve` 存在变量里，等真实事件发生再定稿。这是实现弹窗回传、请求队列等“挂起”结构的常用手法。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>withResolvers 模式</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #f3f0ff; }
            </style>
            </head>
            <body>
              <h1>手动实现 Promise.withResolvers 模式</h1>
              <p>先把 Promise 交出去，再通过按钮外部定稿。</p>
              <button id="finish">完成初始化</button>
              <output id="out">等待中</output>
              <script>
                const makeDeferred = () => {
                  if (typeof Promise.withResolvers === 'function') {
                    return Promise.withResolvers();
                  }
                  let resolve;
                  let reject;
                  const promise = new Promise((res, rej) => {
                    resolve = res;
                    reject = rej;
                  });
                  return { promise, resolve, reject };
                };
                const deferred = makeDeferred();
                document.getElementById('finish').addEventListener('click', () => {
                  deferred.resolve('ready');
                });
                deferred.promise.then((value) => {
                  const text = 'value=' + value;
                  document.getElementById('out').textContent = text;
                  console.log('deferred', text);
                });
              </script>
            </body>
            </html>
            """
        ),
        "out": "点击按钮后输出 `value=ready`：Promise 在创建时就已交付，定稿却发生在点击回调里。",
        "pit": [
            "同一个 Promise 重复 resolve 会被忽略，只有第一次生效。",
            "忘记 catch 会让延迟拒绝变成未处理异常。",
            "原生 Promise.withResolvers 在不支持的运行环境会抛 TypeError，需要降级。",
        ],
        "ex": [
            [
                "增加一个「失败」按钮，调用 deferred.reject(new Error('取消'))。",
                "在 then 后面链 catch。",
                "catch 到错误后输出 取消。",
            ],
        ],
    },
    {
        "t": "微任务与宏任务的执行顺序",
        "level": "advanced",
        "obj": "用日志数组观察同步代码、queueMicrotask、Promise.then 与 setTimeout 的执行顺序。",
        "pre": ["事件循环基础", "Promise.then"],
        "con": ["事件循环", "微任务队列", "宏任务", "执行顺序"],
        "explain": "一段脚本先同步执行到底，再清空微任务队列（Promise.then、queueMicrotask、MutationObserver），然后才处理一个宏任务（setTimeout）。因此同步日志总在前面，微任务按入队顺序执行，定时器永远最后。理解这个顺序才能解释「为什么 setState 之后立刻读取 DOM 还没变」这类现象。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>任务顺序</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #eefaf1; font-family: monospace; }
            </style>
            </head>
            <body>
              <h1>微任务与宏任务的执行顺序</h1>
              <p>观察同步、微任务、定时器的实际完成次序。</p>
              <output id="out">排队中</output>
              <script>
                const order = [];
                order.push('sync-start');
                setTimeout(() => {
                  order.push('timeout');
                  const text = order.join('>');
                  document.getElementById('out').textContent = text;
                  console.log('order', text);
                }, 0);
                queueMicrotask(() => order.push('microtask'));
                Promise.resolve().then(() => order.push('promise'));
                order.push('sync-end');
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `sync-start>sync-end>microtask>promise>timeout`：同步代码先跑完，再跑两个微任务（按入队顺序），最后才是定时器。",
        "pit": [
            "setTimeout(fn, 0) 不是立即执行，最小延迟受浏览器限制。",
            "在微任务里无限入队新微任务会锁死渲染，定时器根本轮不上。",
            "queueMicrotask 与 Promise.then 同属微任务队列，顺序取决于入队先后。",
        ],
        "ex": [
            [
                "在两个微任务之间再插入一个 Promise.then，预测输出顺序。",
                "注意 Promise.resolve().then 的入队时机。",
                "结果依然是同步在前、微任务按入队顺序、定时器最后。",
            ],
        ],
    },
    {
        "t": "queueMicrotask 与绘制时机",
        "level": "advanced",
        "obj": "用 queueMicrotask 与 requestAnimationFrame 观察任务和绘制的先后关系。",
        "pre": ["事件循环", "requestAnimationFrame"],
        "con": ["queueMicrotask", "requestAnimationFrame", "渲染时机", "顺序日志"],
        "explain": "点击事件处理函数里修改 DOM 后，浏览器会先清空微任务队列，再在下一帧统一重排重绘；`requestAnimationFrame` 的回调正好排在重绘之前。用一个日志数组依次记录 click、microtask、frame，就能看清「同一轮事件里微任务先于帧回调」的固定次序，这也是批量更新必须放在微任务里的原因。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>微任务与帧</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #f5f7ff; font-family: monospace; }
            </style>
            </head>
            <body>
              <h1>queueMicrotask 与绘制时机</h1>
              <p>点击后依次记录 click、microtask、frame。</p>
              <button id="run">触发一帧</button>
              <output id="out">idle</output>
              <script>
                const trace = [];
                document.getElementById('run').addEventListener('click', () => {
                  trace.length = 0;
                  trace.push('click');
                  document.getElementById('out').textContent = '同步阶段';
                  queueMicrotask(() => trace.push('microtask'));
                  requestAnimationFrame(() => {
                    trace.push('frame');
                    const text = trace.join('>');
                    document.getElementById('out').textContent = text;
                    console.log('frame-order', text);
                  });
                });
              </script>
            </body>
            </html>
            """
        ),
        "out": "点击后输出 `同步阶段`，紧接着变为 `click>microtask>frame`，证明帧回调晚于微任务。",
        "pit": [
            "页面处于后台标签页时 requestAnimationFrame 可能长时间不触发。",
            "在帧回调里再改 DOM 不会立即生效，要等下一帧。",
            "用 setTimeout 代替 rAF 做动画会掉帧且不可预测。",
        ],
        "ex": [
            [
                "在微任务里修改页面标题，验证它在帧回调之前生效。",
                "在 queueMicrotask 回调里设置 document.title。",
                "帧回调里读取 document.title 已是新值。",
            ],
        ],
    },
    {
        "t": "AbortController 取消异步操作",
        "level": "advanced",
        "obj": "用 AbortController 的 signal 取消已经启动的定时任务，并区分取消与完成。",
        "pre": ["事件监听", "定时器", "Promise"],
        "con": ["AbortController", "AbortSignal", "取消监听", "清理副作用"],
        "explain": "`AbortController` 提供一把「取消开关」：`controller.abort()` 会把 `controller.signal` 置为 aborted 状态，并触发它的 `abort` 事件。`setTimeout`、`fetch`、`addEventListener` 都可以接收这个 signal，在取消时自动清理。正确做法是在新任务开始前 abort 上一个控制器，否则旧定时器会和新任务同时生效。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>AbortController</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #fff1f1; }
            </style>
            </head>
            <body>
              <h1>AbortController 取消异步操作</h1>
              <p>连续点击两次「开始」：第一次的定时器会被第二次取消。</p>              <button id="start">开始计时</button>
              <output id="out">尚未开始</output>
              <script>
                let controller = null;
                let timer = null;
                const out = document.getElementById('out');
                document.getElementById('start').addEventListener('click', () => {
                  if (controller && !controller.signal.aborted) {
                    controller.abort();
                    return;
                  }
                  controller = new AbortController();
                  out.textContent = '等待中';
                  timer = setTimeout(() => {
                    out.textContent = '完成';
                    console.log('timer-done');
                  }, 5000);
                  controller.signal.addEventListener('abort', () => {
                    clearTimeout(timer);
                    out.textContent = '已取消';
                    console.log('aborted');
                  });
                });
              </script>
            </body>
            </html>
            """
        ),
        "out": "第一次点击显示「等待中」，再次点击立即变为「已取消」且不会回到「完成」。控制台只会出现 aborted，不会出现 timer-done。",
        "pit": [
            "signal 一旦 abort 就永久失效，下一次任务必须新建 controller。",
            "abort 之后仍要自己 clearTimeout，除非你把 signal 传给了支持它的 API。",
            "在 abort 回调里再创建控制器会造成递归，需先置空。",
        ],
        "ex": [
            [
                "把定时器换成带 signal 的 fetch 请求，观察取消后的错误名。",
                "fetch(url, { signal: controller.signal }) 取消时抛 AbortError。",
                "catch 里判断 error.name === 'AbortError' 即可区分取消。",
            ],
        ],
    },
    {
        "t": "requestIdleCallback 空闲调度与降级",
        "level": "advanced",
        "obj": "把低优先级任务推迟到浏览器空闲时执行，并封装不支持时的降级方案。",
        "pre": ["事件循环", "回调调度"],
        "con": ["requestIdleCallback", "deadline", "降级封装", "低优先级任务"],
        "explain": "`requestIdleCallback(callback, { timeout })` 只会在浏览器一帧结束、还有剩余时间时调用回调，回调参数 `deadline` 提供 `timeRemaining()` 方法与 `didTimeout` 标志（Chromium 里剩余时间的方法名是 timeRemaining，不是 timeLeft），适合统计上报、预计算这类不影响首屏的任务。`timeout` 保证再忙也会在超时后强制执行。并非所有环境都支持，因此通常封装成「支持就 idle，不支持就 setTimeout」的统一接口。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>requestIdleCallback</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #f2fff9; }
            </style>
            </head>
            <body>
              <h1>requestIdleCallback 空闲调度与降级</h1>
              <p>通过降级封装把任务交给空闲槽执行。</p>
              <output id="out">排队中</output>
              <script>
                const scheduleIdle = (callback) => {
                  if (typeof window.requestIdleCallback === 'function') {
                    return window.requestIdleCallback(callback, { timeout: 500 });
                  }
                  return setTimeout(() => callback({ didTimeout: true }), 0);
                };
                scheduleIdle((deadline) => {
                  const hasRemaining = typeof deadline.timeRemaining === 'function';
                  const native = typeof window.requestIdleCallback === 'function';
                  const text =
                    'idle-run native=' + native + ' remaining=' + hasRemaining;
                  document.getElementById('out').textContent = text;
                  console.log('idle', text);
                });
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `idle-run native=true remaining=true`：原生空闲回调存在，且 deadline 上真的有 timeRemaining 方法可用于判断还能干多少活。",
        "pit": [
            "空闲回调可能长时间不被调用，对实时性有要求的任务不要用它。",
            "回调里执行太久会被浏览器强制结束，应用 timeRemaining() 判断剩余时间并拆分长任务。",
            "降级路径拿不到真实 deadline，只能用 didTimeout 标记。",
        ],
        "ex": [
            [
                "在空闲回调里把一批数字排序，验证不影响首屏。",
                "把 sort 放进 scheduleIdle 的回调。",
                "排序结果写入 #out 即可。",
            ],
        ],
    },
    {
        "t": "matches 与 closest 元素定位",
        "level": "intermediate",
        "obj": "用 matches 判断元素是否命中选择器，用 closest 向上找到最近的祖先。",
        "pre": ["DOM 查询", "选择器语法"],
        "con": ["matches", "closest", "dataset", "祖先查找"],
        "explain": "`element.matches(selector)` 返回布尔值，用来判断当前元素是否符合某个选择器；`element.closest(selector)` 从自身开始向上查找，返回首个匹配的祖先（包含自己）。两者结合就是事件委托的标准写法：在容器上监听点击，用 `event.target.closest('li')` 定位被点的行，避免给每一行都绑监听。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>matches 与 closest</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              li { margin: 4px 0; }
              #out { display: block; padding: 10px; background: #fff6e8; }
            </style>
            </head>
            <body>
              <h1>matches 与 closest 元素定位</h1>
              <ul id="tree">
                <li data-id="a"><span>甲</span></li>
                <li data-id="b"><span id="target">乙</span></li>
              </ul>
              <output id="out"></output>
              <script>
                const target = document.getElementById('target');
                const row = target.closest('li');
                const text = [
                  target.matches('span'),
                  target.matches('li'),
                  row.dataset.id,
                  target.closest('ul').id,
                ].join('|');
                document.getElementById('out').textContent = text;
                console.log('closest', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `true|false|b|tree`：span 命中 span 但不命中 li，最近的 li 携带 data-id=b。",
        "pit": [
            "closest 包含自身，因此传入的选择器可能直接返回当前元素。",
            "matches 对无效选择器会抛 SyntaxError，动态拼接时需先校验。",
            "closest 只向上找祖先，不会进入兄弟或后代子树。",
        ],
        "ex": [
            [
                "在 ul 上做事件委托，点击任意 li 输出它的 data-id。",
                "用 event.target.closest('li').dataset.id。",
                "给 ul 绑定一个 click 监听即可覆盖所有行。",
            ],
        ],
    },
    {
        "t": "dataset 与 data-* 属性同步",
        "level": "intermediate",
        "obj": "用 dataset 读写自定义属性，验证它和 HTML 属性的双向映射关系。",
        "pre": ["DOM 属性操作", "对象属性"],
        "con": ["dataset", "data-*", "camelCase 转换", "delete 删除属性"],
        "explain": "`element.dataset` 是 `data-*` 属性的活对象：驼峰键 `dataItemId` 对应 `data-item-id`，赋值会直接写回 HTML 属性，`delete` 则移除属性。它适合挂业务数据而不污染标准属性。注意值永远是字符串，存数字需要自己转换；展开 `{...dataset}` 能得到一个普通快照对象。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>dataset 同步</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #card { padding: 12px; background: #eef; }
              #out { display: block; padding: 10px; background: #f4f4ff; }
            </style>
            </head>
            <body>
              <h1>dataset 与 data-* 属性同步</h1>
              <div id="card" data-role="admin" data-level="3">卡片</div>
              <output id="out"></output>
              <script>
                const card = document.getElementById('card');
                card.dataset.level = '7';
                card.dataset.cardTitle = '设置页';
                delete card.dataset.role;
                const text = [
                  JSON.stringify({ ...card.dataset }),
                  card.getAttribute('data-level'),
                  card.getAttribute('data-card-title'),
                  card.hasAttribute('data-role'),
                ].join('|');
                document.getElementById('out').textContent = text;
                console.log('dataset', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `{\"level\":\"7\",\"cardTitle\":\"设置页\"}|7|设置页|false`：驼峰键自动转换成短横线属性，删除后属性也不存在。",
        "pit": [
            "dataset 的值都是字符串，'0' 在判断里是真值。",
            "存 JSON 需要自己序列化，直接赋对象会被转成 [object Object]。",
            "数据集 API 与属性名的大小写转换只针对短横线，其他符号会被忽略。",
        ],
        "ex": [
            [
                "把 dataset 里的数字安全地转成 Number。",
                "用 Number(card.dataset.level)。",
                "Number('7') 得到数字 7，可直接参与运算。",
            ],
        ],
    },
    {
        "t": "template 元素与内容克隆",
        "level": "intermediate",
        "obj": "用 template 的 content 片段克隆多行结构，避免重复拼接 HTML 字符串。",
        "pre": ["DOM 创建元素", "模板字符串"],
        "con": ["template", "content", "cloneNode", "DocumentFragment"],
        "explain": "`<template>` 里的内容不会渲染、不会执行脚本，只在 `template.content` 里以 DocumentFragment 形式存在。用 `content.cloneNode(true)` 得到一份深拷贝，填入数据后 append 到文档，就能安全地根据数据生成多行结构，而不必担心 HTML 字符串拼接带来的转义与 XSS 问题。每次克隆都是独立节点，修改一份不影响其他。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>template 克隆</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              .item { padding: 6px 0; }
              #out { display: block; padding: 10px; background: #f1f8f1; }
            </style>
            </head>
            <body>
              <h1>template 元素与内容克隆</h1>
              <template id="row"><li class="item"><b></b><span></span></li></template>
              <ul id="list"></ul>
              <output id="out"></output>
              <script>
                const template = document.getElementById('row');
                const list = document.getElementById('list');
                const rows = [
                  ['HTML', '结构'],
                  ['CSS', '样式'],
                ];
                for (const [name, desc] of rows) {
                  const node = template.content.cloneNode(true);
                  node.querySelector('b').textContent = name;
                  node.querySelector('span').textContent = desc;
                  list.append(node);
                }
                const text =
                  list.children.length +
                  '|' +
                  (template.childElementCount === 0) +
                  '|' +
                  list.querySelector('span').textContent;
                document.getElementById('out').textContent = text;
                console.log('template', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `2|true|结构`：克隆出两层 li，模板本身的内容仍未被消耗，首个描述为「结构」。",
        "pit": [
            "cloneNode 的 true 不能省，否则拿不到内部子节点。",
            "直接 append(template.content) 会把模板内容搬走，下次就没得克隆了。",
            "模板里的 script 不会执行，不要想用它做初始化逻辑。",
        ],
        "ex": [
            [
                "给模板加一个按钮并在克隆后绑定不同的事件处理。",
                "克隆后 querySelector('button') 再 addEventListener。",
                "每次克隆都是新节点，监听不会互相覆盖。",
            ],
        ],
    },
    {
        "t": "dialog 元素的模态与返回值",
        "level": "intermediate",
        "obj": "用 showModal/close 控制原生对话框，并读取 returnValue 判断用户选择。",
        "pre": ["DOM 事件", "表单基础"],
        "con": ["dialog", "showModal", "returnValue", "close 事件"],
        "explain": "`<dialog>` 是原生对话框：`showModal()` 以模态方式打开并自带遮罩层、焦点捕获和 Esc 关闭，`close(value)` 关闭时把字符串写入 `returnValue` 并触发 `close` 事件。因此不需要自己写遮罩与键盘处理，也能保证无障碍语义。注意对已打开的 dialog 再次 `showModal()` 会抛 InvalidStateError。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>dialog 对话框</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              dialog { border: 1px solid #ccd; border-radius: 8px; }
              #out { display: block; padding: 10px; background: #f6f6ff; }
            </style>
            </head>
            <body>
              <h1>dialog 元素的模态与返回值</h1>
              <p>打开对话框并确认，关闭时能读到用户的选择。</p>
              <button id="open">打开确认框</button>
              <dialog id="dlg">
                <p>确认删除这个文件？</p>
                <button id="ok" value="confirmed">确定</button>
              </dialog>
              <output id="out">closed</output>
              <script>
                const dialog = document.getElementById('dlg');
                const out = document.getElementById('out');
                document.getElementById('open').addEventListener('click', () => {
                  if (!dialog.open) dialog.showModal();
                  out.textContent = 'open=' + dialog.open;
                });
                document.getElementById('ok').addEventListener('click', () => {
                  dialog.close('confirmed');
                });
                dialog.addEventListener('close', () => {
                  out.textContent = 'closed result=' + dialog.returnValue;
                  console.log('dialog', dialog.returnValue);
                });
              </script>
            </body>
            </html>
            """
        ),
        "out": "打开后显示 `open=true`，点击确定后变为 `closed result=confirmed`，控制台输出 confirmed。",
        "pit": [
            "dialog 必须调用 showModal 或 show，仅设置 open 属性没有模态行为。",
            "Esc 关闭时 returnValue 保留上一次的值，不会自动清空。",
            "模态期间外部元素不可交互，自动化测试需要先关闭对话框。",
        ],
        "ex": [
            [
                "增加一个取消按钮，把 returnValue 设为 cancel。",
                "再用 close('cancel') 关闭。",
                "close 事件里能读到字符串 cancel。",
            ],
        ],
    },
    {
        "t": "自定义元素与生命周期回调",
        "level": "advanced",
        "obj": "用 customElements.define 注册自定义元素，观察 connected/attributeChanged/disconnected 回调。",
        "pre": ["类与继承", "DOM 节点"],
        "con": ["customElements.define", "connectedCallback", "observedAttributes", "元素升级"],
        "explain": "自定义元素的本质是「让浏览器在遇到某个标签名时创建你的类实例」。注册前已存在的标签会被「升级」，依次触发构造函数、`attributeChangedCallback`、`connectedCallback`。`observedAttributes` 声明关注的属性，只有列表内的属性变化才会回调；从文档中移除元素时触发 `disconnectedCallback`，适合在这里释放定时器与监听。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>自定义元素</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              status-badge { display: inline-block; padding: 4px 10px; background: #e6f7ec; }
              #out { display: block; padding: 10px; background: #f2fbf4; }
            </style>
            </head>
            <body>
              <h1>自定义元素与生命周期回调</h1>
              <status-badge state="idle"></status-badge>
              <output id="out"></output>
              <script>
                const log = [];
                class StatusBadge extends HTMLElement {
                  static get observedAttributes() {
                    return ['state'];
                  }
                  connectedCallback() {
                    log.push('connected');
                    this.textContent = '在线';
                  }
                  attributeChangedCallback(name, oldValue, newValue) {
                    log.push('attr:' + name + '=' + newValue);
                  }
                  disconnectedCallback() {
                    log.push('disconnected');
                  }
                }
                customElements.define('status-badge', StatusBadge);
                const badge = document.querySelector('status-badge');
                badge.setAttribute('state', 'busy');
                badge.setAttribute('title', '忽略');
                badge.remove();
                const text =
                  log.join(',') +
                  '|' +
                  (customElements.get('status-badge') === StatusBadge);
                document.getElementById('out').textContent = text;
                console.log('custom-element', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `attr:state=idle,connected,attr:state=busy,disconnected|true`：元素升级时先按已存在的属性回调一次，再触发 connected；未观察的 title 属性不产生回调，移除元素时回调 disconnected。",
        "pit": [
            "标签名必须包含短横线，否则 define 抛 SyntaxError。",
            "同一个标签名重复 define 会抛 NotSupportedError。",
            "构造函数里不能读属性或添加子节点，应放到 connectedCallback。",
        ],
        "ex": [
            [
                "在 disconnectedCallback 里清除一个 setInterval。",
                "在 connectedCallback 里保存 interval 句柄。",
                "remove() 后控制台不再输出计时日志。",
            ],
        ],
    },
    {
        "t": "影子 DOM 的样式隔离",
        "level": "advanced",
        "obj": "用 attachShadow 创建影子根，验证内部样式不受外部样式影响。",
        "pre": ["DOM 结构", "CSS 选择器优先级"],
        "con": ["attachShadow", "shadowRoot", "样式隔离", "mode open"],
        "explain": "影子 DOM 给组件一个独立的 DOM 子树，外部 CSS 选择器默认无法穿过边界，内部样式也不会泄漏到外部，这就是 Web 组件的样式隔离基础。`mode: 'open'` 允许通过 `host.shadowRoot` 访问内部，`'closed'` 则返回 null。注意内部元素的 `getComputedStyle` 仍然可用，这是验证隔离是否生效的直接手段。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>影子 DOM</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              p { color: rgb(200, 0, 0); }
              #out { display: block; padding: 10px; background: #fdf2ff; }
            </style>
            </head>
            <body>
              <h1>影子 DOM 的样式隔离</h1>
              <my-card id="host"></my-card>
              <p>外部段落是红色</p>
              <output id="out"></output>
              <script>
                const host = document.getElementById('host');
                const root = host.attachShadow({ mode: 'open' });
                root.innerHTML =
                  '<style>p { color: rgb(0, 0, 255); }</style><p>影子内文字</p>';
                const inner = root.querySelector('p');
                const outer = document.querySelector('body > p');
                const text = [
                  inner.textContent,
                  getComputedStyle(inner).color,
                  getComputedStyle(outer).color,
                  host.shadowRoot.mode,
                ].join('|');
                document.getElementById('out').textContent = text;
                console.log('shadow', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `影子内文字|rgb(0, 0, 255)|rgb(200, 0, 0)|open`：内部段落是蓝色，外部段落仍是红色，两边互不影响。",
        "pit": [
            "document.querySelector 查不到影子内部节点，必须从 shadowRoot 取。",
            "mode 只能在 attachShadow 时指定，创建后不可更改。",
            ":host 选择器才能从内部为宿主元素写样式。",
        ],
        "ex": [
            [
                "在影子内部用 :host 给宿主加边框。",
                "在内部 style 里加 :host { border: 2px solid; }。",
                "宿主元素会显示边框且不影响外部元素。",
            ],
        ],
    },
    {
        "t": "Web Animations 播放与完成",
        "level": "advanced",
        "obj": "用 Element.animate 创建动画，读取 playState 并在 finished 后检查最终样式。",
        "pre": ["CSS transform", "Promise"],
        "con": ["Element.animate", "playState", "finished", "fill forwards"],
        "explain": "`element.animate(keyframes, options)` 返回 Animation 对象，不用写 CSS keyframes 就能用 JS 驱动动画，并能随时 `pause`、`cancel`、改变 `playbackRate`。`animation.finished` 是一个 Promise，在动画结束（或取消）时定稿，适合串联多段动画。`fill: 'forwards'` 让动画结束后保留最后一帧的样式，否则元素会回到原位。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>Web Animations</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #box { width: 40px; height: 40px; background: #1a73e8; }
              #out { display: block; padding: 10px; background: #f1f4ff; }
            </style>
            </head>
            <body>
              <h1>Web Animations 播放与完成</h1>
              <p>点击按钮让色块向右移动 120px，结束后保留位置。</p>
              <button id="go">播放动画</button>
              <div id="box"></div>
              <output id="out">ready</output>
              <script>
                const box = document.getElementById('box');
                const out = document.getElementById('out');
                document.getElementById('go').addEventListener('click', () => {
                  const animation = box.animate(
                    [{ transform: 'translateX(0px)' }, { transform: 'translateX(120px)' }],
                    { duration: 150, fill: 'forwards' },
                  );
                  out.textContent = 'state=' + animation.playState;
                  animation.finished.then(() => {
                    const transform = getComputedStyle(box).transform;
                    out.textContent = 'done ' + transform;
                    console.log('anim-done', transform);
                  });
                });
              </script>
            </body>
            </html>
            """
        ),
        "out": "点击后先显示 `state=running`，动画结束后变为 `done matrix(1, 0, 0, 1, 120, 0)`。",
        "pit": [
            "没有 fill: 'forwards' 时动画结束会回退到初始样式。",
            "cancel 也会让 finished 定稿，需要用 animation.playState 区分结束与取消。",
            "动画属性需要能插值，display 之类的离散属性不会产生过渡。",
        ],
        "ex": [
            [
                "把动画改成无限循环并添加暂停按钮。",
                "options 里设置 iterations: Infinity，按钮里调用 animation.pause()。",
                "播放状态会在 running 与 paused 之间切换。",
            ],
        ],
    },
    {
        "t": "CSS 自定义属性读取与设置",
        "level": "intermediate",
        "obj": "用 getComputedStyle 读取计算后的自定义属性，并通过 setProperty 修改它。",
        "pre": ["CSS 变量", "getComputedStyle"],
        "con": ["setProperty", "getComputedStyle", "var()", "级联继承"],
        "explain": "CSS 自定义属性（变量）可以被 JS 读写：`element.style.setProperty('--gap', '12px')` 设置，`getComputedStyle(element).getPropertyValue('--gap')` 读取经过级联和 `var()` 解析后的值。读取时必须拿计算样式，直接读 `style` 只能拿到内联声明的部分。`CSS.registerProperty` 还能声明类型与默认值，让变量参与动画与语法校验。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>CSS 自定义属性</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              :root { --gap: 8px; }
              #box { padding: var(--gap); background: #eef; }
              #out { display: block; padding: 10px; background: #f7f7ff; }
            </style>
            </head>
            <body>
              <h1>CSS 自定义属性读取与设置</h1>
              <p>先读默认的内边距，再通过变量把它改成 12px。</p>
              <div id="box">内容</div>
              <output id="out"></output>
              <script>
                const box = document.getElementById('box');
                const before = getComputedStyle(box).paddingTop;
                box.style.setProperty('--gap', '12px');
                const after = getComputedStyle(box).paddingTop;
                const inline = box.style.getPropertyValue('--gap');
                const registered =
                  typeof CSS !== 'undefined' && typeof CSS.registerProperty === 'function';
                const text = [before, after, inline, registered].join('|');
                document.getElementById('out').textContent = text;
                console.log('custom-prop', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `8px|12px|12px|true`：变量修改后计算内边距真的变了，且当前环境支持 registerProperty。",
        "pit": [
            "getPropertyValue 返回字符串且可能带前导空格，比较前要 trim。",
            "修改 :root 上的变量会影响所有后代，注意作用域。",
            "未注册的变量不参与过渡动画，需要 registerProperty 声明类型。",
        ],
        "ex": [
            [
                "用 CSS.registerProperty 声明 --gap 为 <length> 类型并设置初始值。",
                "注意名字需以 -- 开头。",
                "CSS.registerProperty({ name: '--gap', syntax: '<length>', inherits: false, initialValue: '4px' })",
            ],
        ],
    },
    {
        "t": "IntersectionObserver 阈值与可见比例",
        "level": "advanced",
        "obj": "用 IntersectionObserver 的多阈值回调统计目标元素进入视口的可见比例。",
        "pre": ["DOM 事件", "滚动"],
        "con": ["IntersectionObserver", "threshold", "intersectionRatio", "懒加载"],
        "explain": "`IntersectionObserver` 异步观察目标与视口的交叉状态，不会像 scroll 事件那样每帧触发。`threshold` 声明关心的比例节点，进入或离开这些比例时回调；`entry.intersectionRatio` 给出实际可见比例，`isIntersecting` 表示是否至少有一部分可见。它也是图片懒加载与无限滚动的标准实现基础。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>IntersectionObserver</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #spacer { height: 1200px; background: #f5f5f5; }
              #target { height: 60px; background: #cfe3ff; }
              #out { display: block; padding: 10px; background: #eef4ff; }
            </style>
            </head>
            <body>
              <h1>IntersectionObserver 阈值与可见比例</h1>
              <p>目标元素在首屏下方，滚动进入视口后比例变为 1。</p>
              <div id="spacer">上方留白</div>
              <div id="target">被观察的目标</div>
              <output id="out">fired=0 ratio=0</output>
              <script>
                let fired = 0;
                const observer = new IntersectionObserver(
                  (entries) => {
                    for (const entry of entries) {
                      fired += 1;
                      const ratio = Math.round(entry.intersectionRatio * 100) / 100;
                      const text = 'fired=' + fired + ' ratio=' + ratio;
                      document.getElementById('out').textContent = text;
                      console.log('io', text);
                    }
                  },
                  { threshold: [0, 0.5, 1] },
                );
                observer.observe(document.getElementById('target'));
              </script>
            </body>
            </html>
            """
        ),
        "out": "初始输出类似 `fired=1 ratio=0`；把目标滚动到视口中央后，最终变为 `fired=N ratio=1`。",
        "pit": [
            "回调是异步的，观察后不能立即读到结果。",
            "threshold 为 0 时仍然会在完全不可见的首次观察时回调一次。",
            "元素被 display: none 时永远不会相交。",
        ],
        "ex": [
            [
                "用 unobserve 在首次可见后停止观察。",
                "在回调里判断 isIntersecting 再 unobserve(target)。",
                "后续滚动不再产生新的回调日志。",
            ],
        ],
    },
    {
        "t": "ResizeObserver 尺寸监听",
        "level": "advanced",
        "obj": "用 ResizeObserver 监听元素内容区尺寸变化，并在回调用 contentRect 输出宽度。",
        "pre": ["元素尺寸", "事件监听"],
        "con": ["ResizeObserver", "contentRect", "尺寸变化", "响应式组件"],
        "explain": "窗口 `resize` 事件只能告诉你视口变了，无法得知某个元素自身尺寸变化。`ResizeObserver` 观察具体元素，元素因布局、字体、容器变化而改变尺寸时都会回调，`entry.contentRect` 给出不含内边距的内容区宽高。它常用于图表重绘、虚拟列表重算，比轮询 `offsetWidth` 更准确也更省性能。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>ResizeObserver</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #box { width: 100px; height: 40px; background: #9cc9ff; }
              #out { display: block; padding: 10px; background: #f0f8ff; }
            </style>
            </head>
            <body>
              <h1>ResizeObserver 尺寸监听</h1>
              <p>点击按钮在 100px 与 160px 之间切换宽度。</p>
              <button id="grow">切换宽度</button>
              <div id="box"></div>
              <output id="out">count=0 w=0</output>
              <script>
                let count = 0;
                const box = document.getElementById('box');
                const observer = new ResizeObserver((entries) => {
                  count += 1;
                  const width = Math.round(entries[0].contentRect.width);
                  const text = 'count=' + count + ' w=' + width;
                  document.getElementById('out').textContent = text;
                  console.log('ro', width);
                });
                observer.observe(box);
                document.getElementById('grow').addEventListener('click', () => {
                  box.style.width = box.style.width === '160px' ? '100px' : '160px';
                });
              </script>
            </body>
            </html>
            """
        ),
        "out": "点击一次后宽度变为 160，输出类似 `count=2 w=160`；再点一次回到 100。",
        "pit": [
            "回调里修改被观察元素自身的尺寸可能造成循环触发。",
            "contentRect 不含 padding 与 border，需要总尺寸时用 borderBoxSize。",
            "观察不存在的元素会直接抛错，需先判空。",
        ],
        "ex": [
            [
                "在回调里按宽度切换 class，实现容器查询效果。",
                "判断 contentRect.width < 120 时加 compact 类。",
                "宽度变化时样式自动跟随。",
            ],
        ],
    },
    {
        "t": "Range 与 Selection 精确选区",
        "level": "advanced",
        "obj": "用 Range 指定文本范围并交给 Selection，读出选中的字符串。",
        "pre": ["DOM 节点结构", "文本节点"],
        "con": ["document.createRange", "setStart/setEnd", "getSelection", "rangeCount"],
        "explain": "Selection 是用户看到的选区，Range 是对 DOM 中一段区间的描述。用 `createRange()` 的 `setStart/setEnd` 指定起止点（父节点 + 字符偏移），再用 `selection.addRange(range)` 把它设为当前选区，就能用代码实现「选中某段文字」。`range.toString()` 与 `selection.toString()` 返回这段文字内容，`rangeCount` 表示当前选区内 Range 的个数。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>Range 与 Selection</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #para { padding: 10px; background: #eef6ff; }
              #out { display: block; padding: 10px; background: #f5fbff; }
            </style>
            </head>
            <body>
              <h1>Range 与 Selection 精确选区</h1>
              <p id="para">离线编辑器支持精确选区。</p>
              <output id="out"></output>
              <script>
                const para = document.getElementById('para');
                const range = document.createRange();
                range.setStart(para.firstChild, 0);
                range.setEnd(para.firstChild, 2);
                const selection = window.getSelection();
                selection.removeAllRanges();
                selection.addRange(range);
                const text = [
                  selection.toString(),
                  range.toString(),
                  selection.rangeCount,
                  range.collapsed,
                ].join('|');
                document.getElementById('out').textContent = text;
                console.log('selection', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `离线|离线|1|false`：前两个字被选中，Selection 与 Range 的内容一致，选区非空。",
        "pit": [
            "setStart 的偏移量是字符位置，不是字节或像素。",
            "修改选区前要先 removeAllRanges，否则可能叠加多个 Range。",
            "页面上已有用户选区时，代码设置会直接替换它。",
        ],
        "ex": [
            [
                "改成选中最后两个字「选区」。",
                "把偏移改成 text.length - 2 到 text.length。",
                "selection.toString() 会得到「选区」。",
            ],
        ],
    },
    {
        "t": "DOMParser 解析 HTML 字符串",
        "level": "advanced",
        "obj": "用 DOMParser 把一段 HTML 字符串解析成独立文档，并从中取标题与段落。",
        "pre": ["DOM 树结构", "文档结构"],
        "con": ["DOMParser", "parseFromString", "惰性文档", "不执行脚本"],
        "explain": "`new DOMParser().parseFromString(html, 'text/html')` 返回一个完整的、与当前页面无关的文档对象，可以像操作普通文档一样 `querySelector`、`getElementById`。解析过程不会执行脚本、不会加载资源，因此适合处理模板片段或不可信 HTML（先解析再按需取用元素）。注意它创建的是惰性文档，节点需要 `importNode` 才能插入当前页面。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>DOMParser</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #fff7ed; }
            </style>
            </head>
            <body>
              <h1>DOMParser 解析 HTML 字符串</h1>
              <p>解析一段带标题与两个段落的片段。</p>
              <output id="out"></output>
              <script>
                const source =
                  '<!doctype html><title>片段标题</title>' +
                  '<p id="p1">第一段</p><p>第二段</p>';
                const parsed = new DOMParser().parseFromString(source, 'text/html');
                const text = [
                  parsed.title,
                  parsed.querySelectorAll('p').length,
                  parsed.getElementById('p1').textContent,
                  parsed.body.parentElement === parsed.documentElement,
                ].join('|');
                document.getElementById('out').textContent = text;
                console.log('parsed', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `片段标题|2|第一段|true`：解析出的文档结构完整（body 由解析器自动补全），标题与段落都能直接查询。",
        "pit": [
            "解析出的节点不能直接 append，需要使用 document.importNode 深拷贝。",
            "text/html 解析会补全 html/head/body，与 XML 模式行为不同。",
            "DOMParser 不执行脚本，想要执行应使用 iframe。",
        ],
        "ex": [
            [
                "把解析出的段落插入当前页面。",
                "用 document.importNode(node, true)。",
                "document.body.append(document.importNode(parsed.getElementById('p1'), true))",
            ],
        ],
    },
    {
        "t": "URL 与 URLSearchParams 解析改写",
        "level": "intermediate",
        "obj": "用 URL 对象拆解地址，再用 URLSearchParams 增删查询参数。",
        "pre": ["字符串操作", "location 对象"],
        "con": ["URL", "URLSearchParams", "searchParams", "pathname/hash"],
        "explain": "`new URL(path, base)` 把字符串拆成 protocol、host、pathname、search、hash 等结构化部分，并根据需要自动编码。`url.searchParams` 是 URLSearchParams 视图，`append`、`delete`、`set`、`get`、`keys` 都能直接操作查询串，修改会同步回 URL。它比手写 split('&') 更安全，自动处理重复键与百分号编码。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>URL 解析</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #f0fdfa; word-break: break-all; }
            </style>
            </head>
            <body>
              <h1>URL 与 URLSearchParams 解析改写</h1>
              <p>在本机示例地址上增删参数，再拼回完整地址。</p>
              <output id="out"></output>
              <script>
                const url = new URL('/lesson/page.html?b=2&a=1#top', 'http://127.0.0.1:8080');
                url.searchParams.append('c', '3');
                url.searchParams.delete('b');
                url.pathname = '/offline/index.html';
                const text = [
                  url.pathname + url.search + url.hash,
                  [...url.searchParams.keys()].join(','),
                  url.searchParams.get('a'),
                  url.host,
                ].join('|');
                document.getElementById('out').textContent = text;
                console.log('url', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `/offline/index.html?a=1&c=3#top|a,c|1|127.0.0.1:8080`：删除与新增参数后顺序正确，'1' 仍是字符串。",
        "pit": [
            "URL 构造器需要绝对地址或 base 参数，直接传 '/a' 会抛 TypeError。",
            "searchParams 的值永远是字符串，数字比较要自己转换。",
            "search 包含开头的问号，拼接路径时不要重复加 ?。",
        ],
        "ex": [
            [
                "用 set 而不是 append 修改已有参数，观察重复键的区别。",
                "append 会保留旧值，set 会覆盖。",
                "连续两次 append('a','2') 后 getAll('a') 得到两个值。",
            ],
        ],
    },
    {
        "t": "TextEncoder 与 TextDecoder 字节转换",
        "level": "advanced",
        "obj": "用 TextEncoder 把中文字符串编码为 UTF-8 字节，再用 TextDecoder 还原。",
        "pre": ["字符串基础", "TypedArray"],
        "con": ["TextEncoder", "TextDecoder", "Uint8Array", "UTF-8"],
        "explain": "JS 字符串是 UTF-16 码元序列，而文件、网络、Blob 都是字节流。`new TextEncoder().encode(str)` 返回 UTF-8 的 `Uint8Array`，中文一个字符通常占 3 个字节；`new TextDecoder().decode(bytes)` 反向还原。处理二进制数据、计算字节长度、写文件前都耍经过这一步，不能直接用 `str.length`（它数的是 UTF-16 码元）。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>TextEncoder</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #f7f7f7; font-family: monospace; }
            </style>
            </head>
            <body>
              <h1>TextEncoder 与 TextDecoder 字节转换</h1>
              <p>统计「中文A」的 UTF-8 字节长度与前三个字节值。</p>
              <output id="out"></output>
              <script>
                const source = '中文A';
                const bytes = new TextEncoder().encode(source);
                const restored = new TextDecoder().decode(bytes);
                const text = [
                  bytes.length,
                  [...bytes].slice(0, 3).join(','),
                  restored,
                  source.length,
                ].join('|');
                document.getElementById('out').textContent = text;
                console.log('utf8', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `7|228,184,173|中文A|3`：UTF-8 下共 7 个字节，而 str.length 只数到 3 个字符。",
        "pit": [
            "str.length 与字节长度不等，限制上传大小时要用 encode 后的 length。",
            "TextDecoder 默认不忽略 BOM，utf-8 解码时要注意开头的 BOM 字符。",
            "解码非 UTF-8 字节时会出现替换字符 �，需指定正确的编码名。",
        ],
        "ex": [
            [
                "用 Latin-1 编码名解码同一字节数组，观察差异。",
                "new TextDecoder('latin1').decode(bytes)。",
                "结果会变成乱码，因为字节不合法于单字节编码。",
            ],
        ],
    },
    {
        "t": "Blob 与对象 URL 读取",
        "level": "advanced",
        "obj": "用 Blob 包装文本，读取大小与类型，并用 object URL 与 Response 两次读取内容。",
        "pre": ["Promise", "URL 对象"],
        "con": ["Blob", "createObjectURL", "arrayBuffer", "Response.text"],
        "explain": "`new Blob(parts, { type })` 把字符串或字节片段打包成一个不可变的二进制对象，`size` 是字节数，`type` 是 MIME。它可以直接交给 `Response` 读成文本/数组，也可以用 `URL.createObjectURL` 生成一个 `blob:` 地址，供 `<img>`、`<a download>` 使用。用完必须 `revokeObjectURL` 释放，否则整页生命周期内都会占着内存。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>Blob 对象</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #f2f6ff; }
            </style>
            </head>
            <body>
              <h1>Blob 与对象 URL 读取</h1>
              <p>把一段文本包成 Blob，再分别用 arrayBuffer 与 Response 读取。</p>
              <output id="out">读取中</output>
              <script>
                (async () => {
                  const blob = new Blob(['WebForge'], { type: 'text/plain' });
                  const buffer = await blob.arrayBuffer();
                  const objectUrl = URL.createObjectURL(blob);
                  const text = await new Response(blob).text();
                  const summary = [
                    blob.size,
                    blob.type,
                    buffer.byteLength,
                    objectUrl.startsWith('blob:'),
                    text,
                  ].join('|');
                  document.getElementById('out').textContent = summary;
                  console.log('blob', summary);
                  URL.revokeObjectURL(objectUrl);
                })();
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `8|text/plain|8|true|WebForge`：8 个 ASCII 字节，类型保留，对象 URL 以 blob: 开头。",
        "pit": [
            "Blob 内容不可变，要修改只能新建一个。",
            "中文内容的 size 是 UTF-8 字节数，不等于字符数。",
            "忘记 revokeObjectURL 会导致内存泄漏，尤其在大文件循环场景。",
        ],
        "ex": [
            [
                "用 blob.slice 截取前三个字节并读取。",
                "slice(start, end) 返回新 Blob。",
                "await new Blob(['WebForge']).slice(0, 3).text() 得到 'Web'。",
            ],
        ],
    },
    {
        "t": "base64 编解码与中文安全封装",
        "level": "advanced",
        "obj": "封装 UTF-8 安全的 base64 编码，并验证 atob 直接处理中文会报错。",
        "pre": ["TextEncoder", "异常捕获"],
        "con": ["btoa", "atob", "InvalidCharacterError", "UTF-8 安全"],
        "explain": "`btoa` 只能处理码位在 0–255 的「二进制字符串」，直接传中文会抛 InvalidCharacterError；`atob` 同理，只能解出单字节。安全做法是先用 TextEncoder 把字符串变成 UTF-8 字节，再逐字节拼成字符串交给 btoa；解码时先用 atob 拿回字节，再用 TextDecoder 还原。这样中文与 emoji 都不会丢。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>base64 中文安全</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #b64 { display: block; padding: 8px; background: #eee; font-family: monospace; word-break: break-all; }
              #out { display: block; padding: 10px; background: #fdf6ff; }
            </style>
            </head>
            <body>
              <h1>base64 编解码与中文安全封装</h1>
              <p>下面第一行是编码结果，第二行是解码与错误验证。</p>
              <output id="b64"></output>
              <output id="out"></output>
              <script>
                const encode = (value) =>
                  btoa(String.fromCharCode(...new TextEncoder().encode(value)));
                const decode = (value) =>
                  new TextDecoder().decode(
                    Uint8Array.from(atob(value), (ch) => ch.charCodeAt(0)),
                  );
                const source = '离线 WebForge';
                const encoded = encode(source);
                let directError;
                try {
                  atob(source);
                  directError = 'no-error';
                } catch (error) {
                  directError = error.name;
                }
                document.getElementById('b64').textContent = encoded;
                const text = decode(encoded) + '|' + directError;
                document.getElementById('out').textContent = text;
                console.log('base64', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "第一行是 base64 字符串；第二行输出 `离线 WebForge|InvalidCharacterError`，说明直接 atob 中文会失败。",
        "pit": [
            "btoa/atob 已在部分新标准中标记为遗留 API，但浏览器仍广泛支持。",
            "逐字节拼字符串时用 apply 可能因参数过多而栈溢出，大文件应分块。",
            "base64 不是加密，不能用来隐藏敏感信息。",
        ],
        "ex": [
            [
                "用分块循环代替展开运算符处理长文本。",
                "每 0x8000 字节拼一次。",
                "循环累加 String.fromCharCode.apply(null, chunk) 可避开参数上限。",
            ],
        ],
    },
    {
        "t": "crypto.randomUUID 与安全随机数",
        "level": "intermediate",
        "obj": "用 crypto.randomUUID 生成 v4 UUID，并用 getRandomValues 生成随机字节。",
        "pre": ["Math.random", "正则验证"],
        "con": ["crypto.randomUUID", "getRandomValues", "UUID v4", "安全上下文"],
        "explain": "`Math.random()` 不适合生成 ID，它既不可预测也可能重复。`crypto.randomUUID()` 生成符合 RFC 4122 v4 的 UUID（第 13 位固定为 4，第 17 位为 8/9/a/b），`crypto.getRandomValues(Uint8Array)` 则提供密码学强度的随机字节。两者都需要安全上下文（https 或 localhost）。ID 生成后建议用正则自检格式，而不是只信它。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>crypto.randomUUID</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #f4f8f4; font-family: monospace; }
            </style>
            </head>
            <body>
              <h1>crypto.randomUUID 与安全随机数</h1>
              <p>生成一个 UUID 与 4 个随机字节，并校验格式。</p>
              <output id="out"></output>
              <script>
                const version4 =
                  /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
                const id = crypto.randomUUID();
                const bytes = crypto.getRandomValues(new Uint8Array(4));
                const text = [
                  'uuid=' + version4.test(id),
                  'bytes=' + bytes.length,
                  'inrange=' + bytes.every((n) => n >= 0 && n <= 255),
                  'secure=' + window.isSecureContext,
                ].join(' ');
                document.getElementById('out').textContent = text;
                console.log('crypto', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `uuid=true bytes=4 inrange=true secure=true`：UUID 符合 v4 格式，随机字节在 0–255 内，且处于安全上下文。",
        "pit": [
            "非安全上下文下 crypto.randomUUID 为 undefined，需要先检测或降级。",
            "getRandomValues 的数组长度有上限（通常 65536 字节）。",
            "UUID 唯一不意味着有序，不要拿它当自增主键排序。",
        ],
        "ex": [
            [
                "生成一个短 ID，把随机字节转成十六进制。",
                "用 Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('')。",
                "四个字节会得到 8 个十六进制字符。",
            ],
        ],
    },
    {
        "t": "history.pushState 与 popstate",
        "level": "advanced",
        "obj": "用 pushState 添加历史记录，并在 popstate 里恢复携带的状态对象。",
        "pre": ["location 对象", "事件监听"],
        "con": ["history.pushState", "popstate", "state 对象", "history.back"],
        "explain": "`history.pushState(state, '', url)` 在不刷新页面的前提下新增一条历史记录，并把任意可结构化克隆的数据挂在这条记录上；用户后退时触发 `popstate`，`event.state` 就是当时传入的对象。这是单页路由的基本原理。注意 `replaceState` 不新增记录，`pushState` 也不会触发 `popstate`（它只是「进入」新记录）。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>pushState</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #f0f6ff; }
            </style>
            </head>
            <body>
              <h1>history.pushState 与 popstate</h1>
              <p>每次点击新增一步历史，后退时读取对应的 state。</p>
              <button id="push">进入下一步</button>
              <output id="out">path=</output>
              <script>
                let step = 0;
                const out = document.getElementById('out');
                document.getElementById('push').addEventListener('click', () => {
                  step += 1;
                  history.pushState({ step }, '', '?step=' + step);
                  out.textContent = 'path=' + location.search;
                });
                window.addEventListener('popstate', (event) => {
                  out.textContent = 'pop=' + JSON.stringify(event.state);
                });
              </script>
            </body>
            </html>
            """
        ),
        "out": "点击两次后地址变成 `?step=2`，后退一步时输出 `pop={\"step\":1}`，即上一条记录携带的状态。",
        "pit": [
            "pushState 不会触发 popstate，不要指望用它做路由渲染回调。",
            "跳转的 URL 必须同源，否则会抛 SecurityError。",
            "直接刷新页面后 event.state 会丢，持久化仍需自己处理。",
        ],
        "ex": [
            [
                "把 pushState 改成 replaceState，观察点击时地址是否还增长。",
                "改方法名即可。",
                "replaceState 仍会改变地址，但后退会直接离开当前页。",
            ],
        ],
    },
    {
        "t": "hash 路由与 hashchange",
        "level": "intermediate",
        "obj": "用 location.hash 与 hashchange 实现最简路由，并处理默认跳转。",
        "pre": ["location 对象", "事件监听"],
        "con": ["hashchange", "location.hash", "preventDefault", "路由映射"],
        "explain": "`location.hash` 是地址中 `#` 后面的部分，修改它不会刷新页面；浏览器随后派发 `hashchange` 事件，两者是纯前端路由最轻的基座。因为修改 hash 也会触发浏览器对锚点的默认滚动，所以链接监听里通常调用 `event.preventDefault()` 再由代码主动设 hash，保证行为可控。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>hash 路由</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              a { margin-right: 12px; }
              #out { display: block; padding: 10px; background: #fffaf0; }
            </style>
            </head>
            <body>
              <h1>hash 路由与 hashchange</h1>
              <p>点击「关于」后路由切换为 about。</p>
              <nav>
                <a href="#home" id="l-home">首页</a>
                <a href="#about" id="l-about">关于</a>
              </nav>
              <output id="out">route=</output>
              <script>
                const out = document.getElementById('out');
                const render = () => {
                  const route = location.hash.replace('#', '') || 'home';
                  out.textContent = 'route=' + route;
                  console.log('route-change', route);
                };
                window.addEventListener('hashchange', render);
                document.getElementById('l-about').addEventListener('click', (event) => {
                  event.preventDefault();
                  location.hash = 'about';
                });
                render();
              </script>
            </body>
            </html>
            """
        ),
        "out": "初始显示 `route=home`（hash 为空时的默认值），点击「关于」后变为 `route=about`。",
        "pit": [
            "hash 为空时 replace 后得到空串，此时应给默认路由。",
            "hashchange 不会在首次加载时触发，需要在初始化时手动渲染一次。",
            "hash 里带中文时需要 encodeURIComponent 避免乱码。",
        ],
        "ex": [
            [
                "增加一个 #settings 路由并在页面上展示不同标题。",
                "在 render 里用 switch 分发。",
                "switch(route) 分支里设置 document.title 即可。",
            ],
        ],
    },
    {
        "t": "BroadcastChannel 本地消息广播",
        "level": "advanced",
        "obj": "用 BroadcastChannel 在同一页面的两个通道对象间传递消息。",
        "pre": ["异步消息", "事件监听"],
        "con": ["BroadcastChannel", "postMessage", "onmessage", "同源广播"],
        "explain": "`BroadcastChannel` 提供同源标签页（包括 iframe）之间的广播：`postMessage(value)` 会把值结构化克隆后发给所有同名的其他通道对象，但发送者自身不收到。因此它可用于「多标签页同步登录状态/主题」；完全离线、不涉及网络。关闭页面时调用 `close()` 释放通道。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>BroadcastChannel</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #f4f0ff; }
            </style>
            </head>
            <body>
              <h1>BroadcastChannel 本地消息广播</h1>
              <p>发送端与接收端是两个独立通道对象，消息只送到另一个。</p>
              <button id="send">广播主题变更</button>
              <output id="out">等待消息</output>
              <script>
                const sender = new BroadcastChannel('webforge-theme');
                const receiver = new BroadcastChannel('webforge-theme');
                receiver.onmessage = (event) => {
                  const text = 'recv=' + event.data.theme + '#' + event.data.id;
                  document.getElementById('out').textContent = text;
                  console.log('bc-recv', event.data.theme);
                };
                document.getElementById('send').addEventListener('click', () => {
                  sender.postMessage({ theme: 'dark', id: 1 });
                });
              </script>
            </body>
            </html>
            """
        ),
        "out": "点击后输出 `recv=dark#1`，控制台打印 bc-recv dark。",
        "pit": [
            "同一个通道对象不会收到自己 postMessage 的消息。",
            "频道名必须完全一致，区分大小写。",
            "跨源标签页不会互通，也不会报错，容易误以为没发出去。",
        ],
        "ex": [
            [
                "在 onmessage 里再回一条确认消息，形成双向对话。",
                "注意不要在接收端无限回传。",
                "回传前判断 event.data.type 避免循环。",
            ],
        ],
    },
    {
        "t": "Worker 内联脚本并行计算",
        "level": "advanced",
        "obj": "用 Blob URL 创建内联 Worker，在不阻塞主线程的情况下求和。",
        "pre": ["Blob", "异步消息"],
        "con": ["Worker", "Blob URL", "postMessage", "主线程不阻塞"],
        "explain": "Worker 在独立线程运行，不会阻塞界面。正常情况下需要单独的 .js 文件，但用 `URL.createObjectURL(new Blob([源码]))` 就能把内联源码变成一个可加载的地址（完全离线）。主线程用 `postMessage` 发数据，Worker 用 `self.onmessage` 接收、算完后回发，主线程再在 `onmessage` 里更新 UI。两边数据是结构化克隆的副本，不共享内存。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>Worker</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #eefaf6; }
            </style>
            </head>
            <body>
              <h1>Worker 内联脚本并行计算</h1>
              <p>把数组交给 Worker 求和，结果通过消息回传。</p>
              <button id="calc">开始计算</button>
              <output id="out">未计算</output>
              <script>
                const source =
                  "self.onmessage = (event) => {" +
                  "  const total = event.data.reduce((sum, n) => sum + n, 0);" +
                  "  self.postMessage({ total });" +
                  '};';
                const url = URL.createObjectURL(new Blob([source], { type: 'text/javascript' }));
                const worker = new Worker(url);
                worker.onmessage = (event) => {
                  const text = 'sum=' + event.data.total;
                  document.getElementById('out').textContent = text;
                  console.log('worker', text);
                };
                document.getElementById('calc').addEventListener('click', () => {
                  worker.postMessage([1, 2, 3, 4, 5]);
                });
              </script>
            </body>
            </html>
            """
        ),
        "out": "点击后输出 `sum=15`：Worker 算完 1+2+3+4+5，主线程只负责展示。",
        "pit": [
            "Worker 里没有 window 与 document，只能通过消息与主线程通信。",
            "blob: 地址创建的 Worker 必须同源，且需要 revoke 释放。",
            "传递大对象会走结构化克隆，开销不小，可考虑 Transferable。",
        ],
        "ex": [
            [
                "把数组改成 10 万个随机数，观察页面是否仍然可以点击。",
                "用 Array.from 生成数据再 postMessage。",
                "主线程不会被阻塞，按钮仍可响应。",
            ],
        ],
    },
    {
        "t": "MessageChannel 双向端口通信",
        "level": "advanced",
        "obj": "用 MessageChannel 的两个端口建立一对双向通道，完成一次请求与应答。",
        "pre": ["异步消息", "事件监听"],
        "con": ["MessageChannel", "port1/port2", "postMessage", "请求应答"],
        "explain": "`new MessageChannel()` 创建一对互相连接的端口：发给 port1 的消息会从 port2 收到，反之亦然。它不需要标签页或 Worker，常用来在库内部建立异步通信通道，或把端口通过 `postMessage` 转交给 Worker/iframe（可转移，不复制）。两个端口都需要在不再使用时 `close()`，否则会阻止页面卸载回收。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>MessageChannel</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #f0f0ff; }
            </style>
            </head>
            <body>
              <h1>MessageChannel 双向端口通信</h1>
              <p>发送 ping 后收到大写回包。</p>
              <button id="ping">发送 ping</button>
              <output id="out">空闲</output>
              <script>
                const channel = new MessageChannel();
                channel.port1.onmessage = (event) => {
                  const text = 'reply=' + event.data;
                  document.getElementById('out').textContent = text;
                  console.log('port-reply', event.data);
                };
                channel.port2.onmessage = (event) => {
                  channel.port2.postMessage(String(event.data).toUpperCase());
                };
                document.getElementById('ping').addEventListener('click', () => {
                  channel.port1.postMessage('hello');
                });
              </script>
            </body>
            </html>
            """
        ),
        "out": "点击后输出 `reply=HELLO`：port1 发出 hello，port2 收到并回大写值。",
        "pit": [
            "端口消息是异步的，发送后不能立即读取结果。",
            "start() 只在另一侧通过 postMessage 传递端口后才需要调用。",
            "忘记 close 端口会导致与页面生命周期一起泄漏。",
        ],
        "ex": [
            [
                "让 port2 返回对象 { text, length }，验证结构化克隆。",
                "注意字符串 length 也算进去。",
                "收到的对象可以直接读 event.data.length。",
            ],
        ],
    },
    {
        "t": "ImageData 像素读取",
        "level": "advanced",
        "obj": "用 getImageData 读取画布像素的 RGBA 值，验证填充色真的写进了像素。",
        "pre": ["Canvas 基础", "颜色表示"],
        "con": ["getImageData", "ImageData", "RGBA", "像素级处理"],
        "explain": "Canvas 不是只能画图：`ctx.getImageData(x, y, w, h)` 把指定区域的像素读成 `Uint8ClampedArray`（每像素 4 个值，依次为 R、G、B、A），修改后可以用 `putImageData` 写回，从而实现滤镜、马赛克、亮度调整等像素级效果。颜色 `#1a73e8` 对应十进制 26、115、232，A 通道为 255。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>ImageData 像素</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              canvas { border: 1px solid #ccd; image-rendering: pixelated; }
              #out { display: block; padding: 10px; background: #eef4ff; font-family: monospace; }
            </style>
            </head>
            <body>
              <h1>ImageData 像素读取</h1>
              <p>先填一个 20×20 的蓝色矩形，再读左上角像素的 RGBA。</p>
              <canvas id="panel" width="20" height="20"></canvas>
              <output id="out"></output>
              <script>
                const canvas = document.getElementById('panel');
                const ctx = canvas.getContext('2d');
                ctx.fillStyle = '#1a73e8';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                const pixel = ctx.getImageData(0, 0, 1, 1);
                const [red, green, blue, alpha] = pixel.data;
                const text = [red, green, blue, alpha].join(',') + '|' + pixel.width + 'x' + pixel.height;
                document.getElementById('out').textContent = text;
                console.log('pixel', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `26,115,232,255|1x1`：蓝色被准确换算成十进制通道值，不透明度为 255。",
        "pit": [
            "getImageData 受同源限制，跨域图片会污染画布并抛 SecurityError。",
            "data 是 Uint8ClampedArray，赋值会自动截断到 0–255。",
            "读像素开销较大，循环里应一次读大区域而不是逐像素调用。",
        ],
        "ex": [
            [
                "把整张图变灰：每个像素取三个通道的平均值。",
                "遍历 data，步长为 4。",
                "let g = (r + gr + b) / 3; data[i] = data[i+1] = data[i+2] = g;",
            ],
        ],
    },
    {
        "t": "OffscreenCanvas 能力检测",
        "level": "advanced",
        "obj": "检测 OffscreenCanvas 支持情况，并在支持时主线程外绘制并读取像素。",
        "pre": ["Canvas 基础", "特性检测"],
        "con": ["OffscreenCanvas", "能力检测", "降级", "Worker 绘制"],
        "explain": "`OffscreenCanvas` 是可以在 Worker 里使用的画布，主线程与渲染线程分离，适合大尺寸图像处理。它不一定在所有运行环境都存在，因此正确的写法是先检测 `typeof OffscreenCanvas === 'function'`，再决定走离屏路径还是降级到普通 canvas。上面的例子在离屏画布上绘制并 `getImageData` 读回像素，证明它真的能画而不只是个构造器。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>OffscreenCanvas</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #f4fff8; font-family: monospace; }
            </style>
            </head>
            <body>
              <h1>OffscreenCanvas 能力检测</h1>
              <p>支持时在离屏画布上画红色并读回像素，否则降级。</p>
              <output id="out"></output>
              <script>
                const supported = typeof OffscreenCanvas === 'function';
                let mode = 'fallback';
                if (supported) {
                  const offscreen = new OffscreenCanvas(10, 10);
                  const ctx = offscreen.getContext('2d');
                  ctx.fillStyle = '#ff0000';
                  ctx.fillRect(0, 0, 10, 10);
                  const pixel = ctx.getImageData(0, 0, 1, 1).data;
                  mode = 'offscreen:' + pixel[0] + ',' + pixel[3];
                }
                document.getElementById('out').textContent = mode;
                console.log('offscreen', mode);
              </script>
            </body>
            </html>
            """
        ),
        "out": "在 Chromium 中输出 `offscreen:255,255`：离屏画布真实绘制成功，红通道与 alpha 都是 255。",
        "pit": [
            "OffscreenCanvas 不能直接插入 DOM，需要转成 bitmap 或绘制到可见画布。",
            "transferControlToOffscreen 只能调用一次。",
            "不能假设存在，未做降级会在不支持的浏览器上直接报错。",
        ],
        "ex": [
            [
                "用 convertToBlob 把离屏画布转成 Blob 并读取大小。",
                "await offscreen.convertToBlob({ type: 'image/png' })。",
                "返回的 blob.size 会大于 0。",
            ],
        ],
    },
    {
        "t": "Canvas 文本测量与居中",
        "level": "intermediate",
        "obj": "用 measureText 量出文本宽度，再用 textAlign/textBaseline 精确居中。",
        "pre": ["Canvas 基础", "字体设置"],
        "con": ["measureText", "textAlign", "textBaseline", "居中绘制"],
        "explain": "Canvas 里的文字不会自动居中：要先用 `ctx.measureText(text).width` 量出宽度，再自己计算坐标，或者把 `textAlign` 设为 `center`、`textBaseline` 设为 `middle` 后直接传入画布中心点。`measureText` 的结果依赖 `ctx.font` 当前值，所以必须先设字体再量。这些数值也是自动换行、行高计算的基础。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>Canvas 文本</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              canvas { border: 1px solid #ccd; }
              #out { display: block; padding: 10px; background: #fff8f0; font-family: monospace; }
            </style>
            </head>
            <body>
              <h1>Canvas 文本测量与居中</h1>
              <p>量出文本宽度后，以画布中心为锚点绘制。</p>
              <canvas id="board" width="240" height="60"></canvas>
              <output id="out"></output>
              <script>
                const canvas = document.getElementById('board');
                const ctx = canvas.getContext('2d');
                ctx.font = '16px sans-serif';
                const label = 'WebForge 离线';
                const width = ctx.measureText(label).width;
                ctx.fillStyle = '#1a1a1a';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(label, canvas.width / 2, canvas.height / 2);
                const text = [
                  width > 0,
                  Math.round(canvas.width / 2),
                  ctx.textAlign,
                  Math.round(canvas.height / 2),
                ].join('|');
                document.getElementById('out').textContent = text;
                console.log('measure', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `true|120|center|30`：文本宽度为正，锚点位于 240×60 画布的中心 (120, 30)。",
        "pit": [
            "不设置 ctx.font 就用 measureText，会拿到默认 10px 字体的宽度。",
            "中文字符宽度不等宽，不能假设「字数 × 字号」就是宽度。",
            "高分屏下需要按 devicePixelRatio 放大画布并 scale，否则文字发虚。",
        ],
        "ex": [
            [
                "给每行文字加上背景矩形，宽度直接用 measureText 的结果。",
                "测量后用 fillRect(0, y, width, lineHeight)。",
                "矩形能刚好包住文字。",
            ],
        ],
    },
    {
        "t": "Path2D 复用路径",
        "level": "advanced",
        "obj": "把图形描述集中存到 Path2D 对象，并在同一画布上重复填充与描边。",
        "pre": ["Canvas 基础", "路径绘制"],
        "con": ["Path2D", "复用路径", "fill/stroke", "可缓存图形"],
        "explain": "把一段路径（moveTo、lineTo、rect、arc…）先存进 `Path2D`，之后 `ctx.fill(path)` / `ctx.stroke(path)` 可以重复使用，不必每次重写坐标。在需要反复绘制同一图形的场景（游戏、图表、动画）里，它既能避免重建路径的开销，也让坐标定义集中在一处、便于复用。Path2D 还可以用 `addPath` 合并。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>Path2D</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              canvas { border: 1px solid #ccd; }
              #out { display: block; padding: 10px; background: #f2f6f2; }
            </style>
            </head>
            <body>
              <h1>Path2D 复用路径</h1>
              <p>同一个路径对象先填充后描边，再次平移重复绘制。</p>
              <canvas id="board" width="200" height="100"></canvas>
              <output id="out"></output>
              <script>
                const canvas = document.getElementById('board');
                const ctx = canvas.getContext('2d');
                const shape = new Path2D();
                shape.rect(5, 5, 60, 40);
                shape.moveTo(0, 0);
                shape.lineTo(60, 40);
                ctx.fillStyle = '#8fd3a8';
                ctx.fill(shape);
                ctx.strokeStyle = '#155724';
                ctx.lineWidth = 2;
                ctx.stroke(shape);
                ctx.translate(70, 0);
                ctx.stroke(shape);
                const text = 'path-drawn|' + (shape instanceof Path2D);
                document.getElementById('out').textContent = text;
                console.log('path2d', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `path-drawn|true`：矩形与对角线同时被填充和描边，平移后同一路径可以再次描边。",
        "pit": [
            "Path2D 记录的是路径指令，不包含样式，颜色仍需由 ctx 决定。",
            "ctx.translate 会一直叠加，重复绘制前要 save/restore。",
            "SVG 路径字符串可以传给 Path2D 构造器，但需要合法的 d 写法。",
        ],
        "ex": [
            [
                "用 Path2D('M10 10 L50 10 L30 40 Z') 画一个三角形。",
                "直接把 SVG d 字符串传给构造器。",
                "fill 后可以看到三角形。",
            ],
        ],
    },
    {
        "t": "SVG 动态创建与命名空间",
        "level": "advanced",
        "obj": "用 createElementNS 在 SVG 命名空间下创建圆并设置属性。",
        "pre": ["DOM 创建元素", "SVG 基础"],
        "con": ["createElementNS", "SVG 命名空间", "setAttribute", "矢量图形"],
        "explain": "SVG 元素与 HTML 元素属于不同命名空间，`document.createElement('circle')` 创建出来的只是未知 HTML 元素，浏览器不会渲染它。必须使用 `createElementNS('http://www.w3.org/2000/svg', 'circle')`，再用 `setAttribute` 设置 `cx/cy/r/fill` 等属性。检查 `element.namespaceURI` 是验证「真的创建了 SVG 元素」的最直接方式。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>SVG 动态创建</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              svg { border: 1px solid #dde; background: #fbfdff; }
              #out { display: block; padding: 10px; background: #f0f4ff; }
            </style>
            </head>
            <body>
              <h1>SVG 动态创建与命名空间</h1>
              <p>用脚本创建一个半径 20 的蓝色圆。</p>
              <svg id="board" width="120" height="120" viewBox="0 0 120 120"></svg>
              <output id="out"></output>
              <script>
                const NS = 'http://www.w3.org/2000/svg';
                const board = document.getElementById('board');
                const circle = document.createElementNS(NS, 'circle');
                circle.setAttribute('cx', '60');
                circle.setAttribute('cy', '60');
                circle.setAttribute('r', '20');
                circle.setAttribute('fill', '#1a73e8');
                board.append(circle);
                const text = [
                  circle.namespaceURI === NS,
                  circle.getAttribute('r'),
                  circle.parentElement.id,
                  board.querySelectorAll('circle').length,
                ].join('|');
                document.getElementById('out').textContent = text;
                console.log('svg', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `true|20|board|1`：圆确实处于 SVG 命名空间，半径与层级都正确。",
        "pit": [
            "用 createElement 创建的 circle 不会渲染，也不会报错，非常难排查。",
            "SVG 的 width/height 与 viewBox 是两回事，缩放要靠 viewBox。",
            "CSS 里给 SVG 属性写样式时，fill 与 stroke 优先于属性值。",
        ],
        "ex": [
            [
                "用动画把 r 从 20 逐渐改到 60。",
                "用 requestAnimationFrame 每帧 setAttribute。",
                "半径变大会看到圆逐渐放大。",
            ],
        ],
    },
    {
        "t": "DataTransfer 本地拖放",
        "level": "advanced",
        "obj": "监听 dragover 与 drop，从 dataTransfer 读取拖入的文本。",
        "pre": ["事件监听", "preventDefault"],
        "con": ["dragover", "drop", "DataTransfer", "getData"],
        "explain": "拖放必须成对处理：`dragover` 里调用 `preventDefault()` 才能把元素声明为可放置区域，否则 `drop` 永远不会触发。`drop` 回调里用 `event.dataTransfer.getData('text/plain')` 读取文本，或用 `files` 读文件。两者都要 `preventDefault()`，避免浏览器默认打开拖入内容。整个过程本地完成，不发生任何网络请求。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>拖放</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #zone { padding: 24px; border: 2px dashed #9ab; background: #f6fbff; }
              #zone.over { border-color: #1a73e8; background: #e8f2ff; }
              #out { display: block; padding: 10px; background: #f4f8ff; }
            </style>
            </head>
            <body>
              <h1>DataTransfer 本地拖放</h1>
              <p>把一段文字拖到虚线框内。</p>
              <div id="zone">拖放到这里</div>
              <output id="out">empty</output>
              <script>
                const zone = document.getElementById('zone');
                const out = document.getElementById('out');
                zone.addEventListener('dragover', (event) => {
                  event.preventDefault();
                  zone.classList.add('over');
                });
                zone.addEventListener('dragleave', () => zone.classList.remove('over'));
                zone.addEventListener('drop', (event) => {
                  event.preventDefault();
                  zone.classList.remove('over');
                  const text = event.dataTransfer.getData('text/plain');
                  out.textContent = 'dropped=' + text;
                  console.log('drop', text);
                });
              </script>
            </body>
            </html>
            """
        ),
        "out": "拖入「离线拖放」后输出 `dropped=离线拖放`，控制台同步打印。",
        "pit": [
            "缺少 dragover 的 preventDefault 是最常见的「drop 不触发」原因。",
            "getData 在 dragenter/dragover 阶段是空的，只能在 drop 里读。",
            "文件需要通过 event.dataTransfer.files 获取，不能用 getData。",
        ],
        "ex": [
            [
                "在 drop 时读取拖入文件的名称与大小。",
                "用 Array.from(event.dataTransfer.files)。",
                "files[0].name 与 files[0].size 可用。",
            ],
        ],
    },
    {
        "t": "PointerEvent 统一鼠标与触摸",
        "level": "advanced",
        "obj": "用 pointerdown 读取相对坐标与 pointerType，一套代码兼容鼠标、触摸、手写笔。",
        "pre": ["事件对象", "坐标系统"],
        "con": ["PointerEvent", "pointerType", "clientX/Y", "统一输入"],
        "explain": "鼠标事件（mouse＊）与触摸事件（touch＊）需要两套监听，PointerEvent 把它们统一成一个模型：`pointerdown/move/up` 同时覆盖鼠标、手指、触控笔，`pointerType` 告诉你当前是 'mouse'、'touch' 还是 'pen'。计算元素内坐标时用 `clientX - rect.left`，不依赖 pageYOffset，窗口滚动后依然准确。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>PointerEvent</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #pad { width: 200px; height: 100px; background: #e8eefc; border: 1px solid #c3d0f0; }
              #out { display: block; padding: 10px; background: #f2f5ff; font-family: monospace; }
            </style>
            </head>
            <body>
              <h1>PointerEvent 统一鼠标与触摸</h1>
              <p>在左侧区域内点击，输出相对坐标与指针类型。</p>
              <div id="pad">点击区域</div>
              <output id="out">none</output>
              <script>
                const pad = document.getElementById('pad');
                const out = document.getElementById('out');
                pad.addEventListener('pointerdown', (event) => {
                  const rect = pad.getBoundingClientRect();
                  const x = Math.round(event.clientX - rect.left);
                  const y = Math.round(event.clientY - rect.top);
                  const text = 'x=' + x + ' y=' + y + ' type=' + event.pointerType;
                  out.textContent = text;
                  console.log('pointer', event.pointerType, x, y);
                });
              </script>
            </body>
            </html>
            """
        ),
        "out": "鼠标在距离区域左 40px、上 20px 处点击时输出 `x=40 y=20 type=mouse`。",
        "pit": [
            "用 offsetX/offsetY 会受子元素影响，取外层容器坐标应用 clientX - rect.left。",
            "触摸时不要忘记 CSS 的 touch-action，否则会触发页面滚动。",
            "pointerdown 后不捕获指针，移出元素就收不到 pointerup。",
        ],
        "ex": [
            [
                "在 pointerdown 后调用 setPointerCapture，保证拖出区域也能收到 pointerup。",
                "pad.setPointerCapture(event.pointerId)。",
                "快速拖出区域时 pointerup 仍能触发。",
            ],
        ],
    },
    {
        "t": "组合输入与 input 事件处理",
        "level": "advanced",
        "obj": "监听 compositionstart/compositionend 与 input，区分候选输入与已确认文本。",
        "pre": ["表单事件", "输入框基础"],
        "con": ["compositionstart", "compositionend", "input", "中文输入"],
        "explain": "中文、日文输入法在敲拼音时并没有真正写入文本，此时是「组合中」（composition）状态，会在输入框上触发 `compositionstart`，选完字并确认后触发 `compositionend`，同时共用一个 `input` 事件序列。如果你在 input 里直接做实时搜索，拼音字母也会被当成关键词，因此需要用一个 `composing` 标志跳过组合中的输入。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>组合输入</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              input { padding: 6px 10px; width: 220px; }
              #out { display: block; padding: 10px; background: #fdf7ff; }
            </style>
            </head>
            <body>
              <h1>组合输入与 input 事件处理</h1>
              <p>在输入框里输入中文，观察 composing 状态与最终文本。</p>
              <input id="field" placeholder="请输入关键词">
              <output id="out">composing=false text=</output>
              <script>
                const field = document.getElementById('field');
                const out = document.getElementById('out');
                let composing = false;
                field.addEventListener('compositionstart', () => {
                  composing = true;
                });
                field.addEventListener('compositionend', (event) => {
                  composing = false;
                  out.textContent = 'compositionend=' + event.data;
                });
                field.addEventListener('input', (event) => {
                  out.textContent =
                    'composing=' + composing + ' text=' + event.target.value;
                });
              </script>
            </body>
            </html>
            """
        ),
        "out": "输入「你好」后输出 `composing=false text=你好`；使用输入法敲拼音的过程中 composing 会短暂为 true。",
        "pit": [
            "用键盘事件监听文本输入会漏掉粘贴与输入法，应该用 input。",
            "compositionend 后还会补发 input，注意不要重复触发。",
            "composing 标志必须写在实例上，不能每次事件重新声明。",
        ],
        "ex": [
            [
                "在组合中输入时把提示文字改为「输入中…」。",
                "在 input 里先判断 composing。",
                "composing 为 true 时只改提示，不更新结果。",
            ],
        ],
    },
    {
        "t": "range 滑块实时值绑定",
        "level": "beginner",
        "obj": "监听 range 输入的 input 事件，把数值同步到文本与进度条宽度。",
        "pre": ["表单元素", "事件监听"],
        "con": ["input type=range", "input 事件", "实时绑定", "百分比"],
        "explain": "`<input type=range>` 的 `change` 事件只在松手后触发，想在拖动过程中实时反馈就必须监听 `input`。滑块的值永远是字符串，参与计算前要 `Number()`。把 `(value - min) / (max - min)` 乘 100 就得到百分比，可直接用于设置进度条宽度，这也是音量、亮度、字体大小等控件的标准实现。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>range 滑块</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #bar { height: 8px; background: #dde3ee; border-radius: 4px; overflow: hidden; }
              #fill { height: 100%; width: 50%; background: #1a73e8; }
              #out { display: block; padding: 10px; background: #eef2fb; }
            </style>
            </head>
            <body>
              <h1>range 滑块实时值绑定</h1>
              <p>拖动滑块，同时更新数值与进度条宽度。</p>
              <label>音量 <input id="range" type="range" min="0" max="10" value="5"></label>
              <div id="bar"><div id="fill"></div></div>
              <output id="out">v=5</output>
              <script>
                const range = document.getElementById('range');
                const fill = document.getElementById('fill');
                const out = document.getElementById('out');
                range.addEventListener('input', () => {
                  const value = Number(range.value);
                  out.textContent = 'v=' + value;
                  fill.style.width = value * 10 + '%';
                  console.log('range', value);
                });
              </script>
            </body>
            </html>
            """
        ),
        "out": "把滑块拖到 8 时输出 `v=8`，进度条宽度变为 80%；拖到 0 时宽度为 0%。",
        "pit": [
            "只监听 change 会要求松手才更新，体验上很硬。",
            "range 的 value 是字符串，'10' 直接参与运算会变成字符串拼接。",
            "步长 step 未设置时默认 1，需要小数时要显式设置。",
        ],
        "ex": [
            [
                "把音量映射到页面文字的大小时，用 value 直接拼成 px。",
                "设置 document.body.style.fontSize。",
                "拖动时文字大小实时变化。",
            ],
        ],
    },
    {
        "t": "表单原生校验 checkValidity",
        "level": "intermediate",
        "obj": "用 checkValidity 与 validity 对象读取邮箱、数字范围的原生校验结果。",
        "pre": ["表单基础", "input 类型"],
        "con": ["checkValidity", "validity", "typeMismatch", "rangeUnderflow"],
        "explain": "HTML 表单自带校验：`type=email` 检查格式，`min/max` 检查范围，`required` 检查非空。`form.checkValidity()` 返回整体是否通过，`input.validity` 给出具体原因（`typeMismatch`、`rangeUnderflow`、`valueMissing`…）。把 `novalidate` 加在 form 上可以关掉自动弹窗，完全由 JS 决定提示时机与样式，这也是自定义校验界面的起点。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>表单校验</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              input { display: block; margin: 6px 0; padding: 6px 10px; width: 200px; }
              #out { display: block; padding: 10px; background: #fff9ee; }
            </style>
            </head>
            <body>
              <h1>表单原生校验 checkValidity</h1>
              <p>先填合法数据，再把年龄改成 10 触发范围下溢。</p>
              <form id="form" novalidate>
                <input id="email" name="email" type="email" required placeholder="邮箱">
                <input id="age" name="age" type="number" min="18" max="99" placeholder="年龄">
              </form>
              <output id="out">-</output>
              <script>
                const form = document.getElementById('form');
                const email = document.getElementById('email');
                const age = document.getElementById('age');
                const out = document.getElementById('out');
                form.addEventListener('submit', (event) => event.preventDefault());
                form.addEventListener('input', () => {
                  const text = [
                    form.checkValidity(),
                    email.validity.typeMismatch,
                    age.validity.rangeUnderflow,
                    email.validity.valueMissing,
                  ].join('|');
                  out.textContent = text;
                  console.log('valid', text);
                });
              </script>
            </body>
            </html>
            """
        ),
        "out": "邮箱输入 `a@b.com`、年龄 `20` 时输出 `true|false|false|false`；年龄改成 `10` 后变为 `false|false|true|false`。",
        "pit": [
            "novalidate 只关闭自动提示，不关闭 checkValidity 的计算。",
            "type=number 输入非法字符时 value 为空串，可能被误判为缺失。",
            "validity 对象每次读取都是实时的，不要把它缓存成快照。",
        ],
        "ex": [
            [
                "用 setCustomValidity 给年龄加一条自定义错误。",
                "先清空其他错误再接自定义消息。",
                "age.setCustomValidity('年龄必须为偶数') 会让 checkValidity 返回 false。",
            ],
        ],
    },
    {
        "t": "Intl.Segmenter 分词与粒度",
        "level": "advanced",
        "obj": "用 Intl.Segmenter 按词切分文本，并区分词与非词片段。",
        "pre": ["字符串处理", "Intl 基础"],
        "con": ["Intl.Segmenter", "granularity", "isWordLike", "词数统计"],
        "explain": "按空格 `split` 对英文尚可，对中文、日文基本无效。`Intl.Segmenter` 使用语言字典做分词，`granularity: 'word'` 按词、`'sentence'` 按句、`'grapheme'` 按字素（连 emoji 组合都不会拆坏）。遍历结果的 `isWordLike` 可过滤掉空格与标点，非常适合字数统计与关键词提取。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>Intl.Segmenter</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              #out { display: block; padding: 10px; background: #f3fff7; font-family: monospace; }
            </style>
            </head>
            <body>
              <h1>Intl.Segmenter 分词与粒度</h1>
              <p>按词切分一句英文术语，只统计词片段。</p>
              <output id="out"></output>
              <script>
                const source = 'WebForge IDE 2026';
                const mode = typeof Intl.Segmenter === 'function' ? 'segmenter' : 'fallback';
                let words;
                if (mode === 'segmenter') {
                  const segmenter = new Intl.Segmenter('en', { granularity: 'word' });
                  words = [...segmenter.segment(source)]
                    .filter((part) => part.isWordLike)
                    .map((part) => part.segment);
                } else {
                  words = source.split(' ');
                }
                const text = mode + '|' + words.length + '|' + words.join('/');
                document.getElementById('out').textContent = text;
                console.log('segmenter', text);
              </script>
            </body>
            </html>
            """
        ),
        "out": "输出 `segmenter|3|WebForge/IDE/2026`：三个词片段被准确识别，空格不计入。",
        "pit": [
            "旧环境没有 Intl.Segmenter，需要先检测再降级。",
            "中文分词依赖词典，不同引擎版本结果可能略有差异。",
            "segment 返回的是惰性迭代器，不能直接用 length 取值。",
        ],
        "ex": [
            [
                "用 granularity: 'grapheme' 数出含 emoji 字符串的可见字符数。",
                "注意 emoji 组合序列。",
                "[...segmenter.segment('🙂👍')].length 为 2。",
            ],
        ],
    },
    {
        "t": "离线特性检测报告",
        "level": "intermediate",
        "obj": "汇总多个现代 API 的支持情况，生成一份离线可用性报告列表。",
        "pre": ["特性检测", "DOM 渲染"],
        "con": ["特性检测", "in 运算符", "typeof", "渐进增强"],
        "explain": "直接调用可能不存在的新 API 会让整个脚本报错并中断后续逻辑。稳妥的做法是先做特性检测：全局构造函数用 `typeof x === 'function'`，挂载在 window 上的接口用 `'x' in window`。把结果收集成一个报告，就能在不支持的环境里有针对性地降级，而不是整页白屏。这也是离线应用兼容旧 WebView 的基本功。",
        "code": _doc(
            """
            <!doctype html>
            <html lang="zh-CN">
            <head>
            <meta charset="utf-8">
            <title>特性检测报告</title>
            <style>
              body { font-family: system-ui, sans-serif; padding: 16px; }
              li { padding: 2px 0; font-family: monospace; }
              li.no { color: #b3261e; }
              #out { display: block; padding: 10px; background: #f4f6ff; }
            </style>
            </head>
            <body>
              <h1>离线特性检测报告</h1>
              <p>逐项检测并生成列表。</p>
              <output id="out"></output>
              <ul id="list"></ul>
              <script>
                const checks = [
                  ['structuredClone', typeof structuredClone === 'function'],
                  ['IntersectionObserver', 'IntersectionObserver' in window],
                  ['OffscreenCanvas', typeof OffscreenCanvas === 'function'],
                  ['Intl.Segmenter', typeof Intl.Segmenter === 'function'],
                  ['requestIdleCallback', 'requestIdleCallback' in window],
                ];
                const supported = checks.filter(([, ok]) => ok);
                const out = document.getElementById('out');
                out.textContent = 'supported=' + supported.length + '/' + checks.length;
                document.getElementById('list').innerHTML = checks
                  .map(
                    ([name, ok]) =>
                      '<li class="' + (ok ? 'yes' : 'no') + '">' +
                      name + ':' + (ok ? '支持' : '不可用') +
                      '</li>',
                  )
                  .join('');
                console.log('report', out.textContent);
              </script>
            </body>
            </html>
            """
        ),
        "out": "当前 Chromium 输出 `supported=5/5`，五个 li 全是支持状态；旧环境则会显示不可用项的数量。",
        "pit": [
            "只检测不降级没有意义，每个分支都要有可用的退路。",
            "用 typeof 检测全局对象在未声明时会抛 ReferenceError，应写 typeof window.x。",
            "特性检测结果不要在页面加载后缓存太久，热更新环境会变。",
        ],
        "ex": [
            [
                "增加一项检测 canvas 的 getContext 是否可用。",
                "用 document.createElement('canvas').getContext 判断。",
                "返回对象则支持，返回 null 则不支持。",
            ],
        ],
    },
    # <<<APPEND>>>
]
