# C864 独立核心核查（pi4，2026-10-26）

只读核查。未运行 SDK、测试、Job、授权或频道。未改产品或核心代码。
只读取文件。只写入本文件。

核查对象有三项。

1. 核心仓库 HEAD 是否为 `5b3c48c7d1c1822d0ee348b68eb6b33f3bba54d0`。
2. 相对原始冻结，是否只有 supervisor 一个文件变化。
3. Pi3 的 C864 输入清单是否与磁盘一致。

## 1. 结论

三项全部通过。清单可以独立复现。

| 项 | 结果 |
| --- | --- |
| 核心 HEAD | `5b3c48c7d1c1822d0ee348b68eb6b33f3bba54d0` |
| supervisor 哈希 | `095de8c17c66dc206fe170b3f99b7447d8660f183085ecb338f97484ff0e5bfc` |
| terminal 哈希 | `7bf7d36524eb4db8b4d57d10aace5227446769f95622879af80ac7216d6beffd` |
| 核心差集 | 225 个文件中恰好 1 个变化 |
| 清单 `filesSha256` | 独立复现一致 |
| 就绪输入 `wipRollupSha256` | 独立复现一致 |

## 2. 核心 HEAD 与工作树身份

命令 `git -C core rev-parse HEAD` 返回 `5b3c48c7d1c1822d0ee348b68eb6b33f3bba54d0`。
分支为 `main`。
`git -C core log --oneline -5` 的 HEAD 标题是
`fix(process): terminate Windows tree before waiting for input`。

HEAD 提交 `5b3c48c` 改动的文件如下。

| 路径 | 说明 |
| --- | --- |
| `.trellis/spec/frontend/offline-debugger.md` | 规范 |
| `.trellis/tasks/10-22-offline-editor-analysis/research/supervisor-blocked-input-20261026/**` | 证据目录 |
| `lib/services/process_supervisor.dart` | 产品源码 |
| `test/process_supervisor_test.dart` | 测试 |

工作树的 supervisor 与 HEAD 提交内容完全相同。两条命令给出同一对象。

- `git rev-parse HEAD:lib/services/process_supervisor.dart` = `3fe02954786b2a324bab12a4f15241c44f2a46a8`
- `git hash-object lib/services/process_supervisor.dart` = `3fe02954786b2a324bab12a4f15241c44f2a46a8`

所以 `095de8c1…` 就是 HEAD 已提交的内容。它不是未提交的改动。

`git status --porcelain -- lib/services/process_supervisor.dart lib/editor/terminal_pane.dart`
无输出。这两个文件相对 HEAD 干净。

## 3. 精确差集：只有 supervisor

我把冻结的核心清单与当前工作树逐文件比对。
冻结清单取自 `web-app-c843-20261026/source-after.json`。
它含 225 条核心记录。

比对结果如下。

| 路径 | 冻结 | 当前 | 判定 |
| --- | --- | --- | --- |
| `lib/services/process_supervisor.dart` | `25ba430c…` 21248 B | `095de8c1…` 21796 B | 变化 |
| `lib/editor/terminal_pane.dart` | `7bf7d365…` 82279 B | `7bf7d365…` 82279 B | 未变 |

225 条记录中差异数为 1。

`terminal_pane.dart` 的哈希在 `web-app-c843-20261026/source-before.json` 与
`source-after.json` 中都是 `7bf7d365…`。当前也是。所以第 4 节的「terminal 不变」成立。

`25ba430c…` 上溯可见于 C606、C782、C843 记录与 `web-source-ready-20261024.json`。
所以它是原始冻结谱系的核心值。

## 4. 清单级增量

我另比对了 C864 前一份清单与 C864 清单。
前者在 `web-relay-input-20261026/app-full-inputs.json`。
后者在 `web-relay-input-c864-20261026/app-full-inputs.json`。

两份都是 332 条记录。路径集合相同。改动行数为 2。

| 路径 | 前 | 后 | 仓库 |
| --- | --- | --- | --- |
| `../qfli_studio_core/lib/services/process_supervisor.dart` | `25ba430ce7c0…` 21248 B | `095de8c17c66…` 21796 B | 核心 |
| `test/owned_preview_resource_broker_test.dart` | `6f41b71218ca…` 19454 B | `ffb4e6ec0bbb…` 19030 B | 产品 |

第二条是上一轮的 broker 测试夹具修复。它的 `ffb4e6ec…` 19030 B 与我上轮记录一致。

核心仓库的改动行数为 1。这与第 3 节独立得出的结论一致。

## 5. 独立复现 `app-full-inputs.json`

我按冻结 `snapshot()` 的定义重建文件集。
定义来自 `run-web-app-window.py:86-135`。

规则如下。

- 加入 `run-web-app-window.py`、`run-web-app-worker.ps1`、`run-web-owned-window.py`。
- 加入产品与核心的 `lib`、`test`、`integration_test`、`tool` 下的 `*.dart`。
- 加入产品与核心的指定 glob，例如 `assets/content/**/*.json` 与 `scripts/*.py`。
- 加入运行期路径中的 native 文件。
- 按绝对路径 `casefold()` 排序。
- 每行记录 `path`、`bytes`、`sha256`。

复现结果如下。

| 项 | 值 |
| --- | --- |
| 我重建的文件数 | 332 |
| 清单文件数 | 332 |
| 路径集合相同 | 是，仅清单独有 0，仅重建独有 0 |
| 行顺序相同 | 是 |
| 行哈希与字节差异 | 0 |
| 我复算的 `filesSha256` | `7B87BB2676D7E90892536BCAB0158132064A19660972D93B0B08450A3937F7B5` |
| 清单记录的 `filesSha256` | `7B87BB2676D7E90892536BCAB0158132064A19660972D93B0B08450A3937F7B5` |

我也核了清单自身的内部一致性。
`sha256(json.dumps(files, sort_keys=True, separators=(",",":")))` 的上界值与记录值相同。
`filesCount` 332 与 `len(files)` 332 相同。

关键行点名如下。

| 路径 | 哈希前 16 位 | 字节 |
| --- | --- | --- |
| `../qfli_studio_core/lib/services/process_supervisor.dart` | `095de8c17c66dc20` | 21796 |
| `../qfli_studio_core/lib/editor/terminal_pane.dart` | `7bf7d36524eb4db8` | 82279 |
| `scripts/ste-lint-zh.py` | `4571e2c4c1c8d790` | 20114 |

`scripts/ste-lint-zh.py` 以展开后的文件路径出现。
它没有以整目录 `scripts/` 形式出现。
这避开了「整目录条目」与「引号路径」两类错误。

## 6. 独立复现 `readiness-input.json`

`readiness-input.json` 记录核心 WIP 42 条，并对它们做聚合哈希。
聚合定义来自 `build-readiness-input.py:166-174`。

我在 `main` 上重跑同一定义。

- `wipRollupSha256` 记录值 `8BC8E2F34EFF374971EEBD1103F21F715A41674683963E776C9440356DB599F6`
- 我复算值 `8BC8E2F34EFF374971EEBD1103F21F715A41674683963E776C9440356DB599F6`

结果一致。行数 42 对 42。行差异 0。

核心 WIP 的采集方式字段是
`git status --porcelain --untracked-files=all`。
这一方式把未跟踪目录展开为文件。
所以 `scripts/` 变成 `scripts/ste-lint-zh.py`。

其他字段核查如下。

| 字段 | 记录值 | 我的结果 |
| --- | --- | --- |
| `core.head` | `5b3c48c7…` | 一致 |
| `core.statusEntries` | 42 | 42 |
| `core.wipFilesHashed` | 42 | 42 |
| `core.wipDirectoryEntries` | 空 | 空 |
| `core.malformedStatusLines` | 空 | 空 |
| `core.completeWipFiles` | `true` | `true` |

## 7. 冻结 pin 与文件哈希

`frozenPins` 共 7 条。全部 `match=true`。`frozenMatch` 为 `true`。

| 角色 | 哈希前 16 位 |
| --- | --- |
| observer | `D1943BD1E622FC3…` |
| test | `81D61C8B0F639222…` |
| wrapper | `401F61D44495DD0A…` |
| authorization | `84445442FED9B938…` |
| runner | `D80C46E1B1CF2ABE…` |
| worker | `074AC02216BAB95E…` |
| helper | `9DF7A94399AAE389…` |

这些值与我已知的冻结值一致。

清单文件哈希核查如下。

| 文件 | 字节 | 声明值 | 实测值 |
| --- | --- | --- | --- |
| c864 `app-full-inputs.json` | 64409 | `F8D2AB9E…` | 一致 |
| c864 `readiness-input.json` | 19305 | `DC495523…` | 一致 |
| 父 `app-full-inputs.json` | 64381 | `2DDB7E38…` | 一致 |

`permittedChanges` 如下。

- `parentFiles` 332，`currentFiles` 332。
- `added` 空，`removed` 空。
- `changed` 两项：核心 supervisor 与产品 broker 测试。
- `unexpectedChanges` 空。
- `permittedOnly` 为 `true`。

这与我第 4 节的独立结论相同。

`product.head` 为 `d863397122f2a3f0e3f6df5cbe066873f959d902`。
我核过 `git -C web rev-parse HEAD`，值相同。
HEAD 提交改动 4 个文件。其中 3 个是 README。所以 `researchOnly` 为 `false`。

## 8. 发现（全部非阻断）

### F1 `allowed` 含一条死路径

`permittedChanges.allowed` 三项如下。

| 条目 | web 根存在 | 核心存在 |
| --- | --- | --- |
| `../qfli_studio_core/lib/services/process_supervisor.dart` | 是 | 是 |
| `lib/services/process_supervisor.dart` | 否 | 是 |
| `test/owned_preview_resource_broker_test.dart` | 是 | 否 |

第二条在 web 根下不存在。它在核心下存在。
它与第一条指向同一文件，只是少了 `../qfli_studio_core/` 前缀。
它是一条冗余别名。它不改变 `permittedOnly` 的结论，因为白名单仍含真实路径。
但它会让读者以为存在第二个获准的产品文件。
建议删掉该别名，或把它标为别名。

### F2 清单的核心覆盖范围窄于核心工作树

清单的文件集来自冻结 `snapshot()`。
核心侧它只扫描 `lib`、`test`（仅核心 `lib`）、`assets/content`、
`pubspec.yaml`、`analysis_options.yaml`、`vendor/**/pubspec.yaml`。
核心清单条目按根分布如下。

| 根 | 条数 |
| --- | --- |
| `lib` | 161 |
| `vendor` | 60 |
| `assets` | 2 |
| `pubspec.yaml` | 1 |
| `analysis_options.yaml` | 1 |

核心 WIP 共 42 条。其中只有 12 条在这个范围内。

界外 30 条包括核心的 `test`、`tool`、`assets/tutorials`、
`.trellis`、`AGENTS.md` 与 `scripts`。

一个具体例子：`test/process_supervisor_test.dart` 不在清单内。
HEAD 提交 `5b3c48c` 恰好改了它，增加 139 行。

这一范围来自冻结 `snapshot()` 的既有定义。Pi3 没有引入它。
Pi3 在就绪输入层用完整 42 行 rollup 补上了核心 WIP。
但清单本身没有写它的范围。
只绑定清单的读者会以为核心全覆盖。
建议在 `capture` 块补一句范围说明。

### F3 逐文件哈希大小写不一致

两份产物的哈希大小写不同。

| 产物 | 行哈希大小写 |
| --- | --- |
| `app-full-inputs.json` | 小写 |
| `readiness-input.json` 的 `wip` 行 | 大写 |

清单行来自冻结 `file_hash`，它是小写。
就绪输入行来自 `sha256_file`，它是大写。

Pi3 已披露这一约定。`perFileHashCase` 字段写了
`lowercase hexdigest from the frozen snapshot`。

我第一遍比对没有归一化大小写。它报出 332 处「差异」。
归一化后差异为 0。
这是一条操作陷阱，不是缺陷。建议比对时先归一化大小写。

## 9. 未证明项

以下各条我不声称。

- 我未运行任何测试。
- 我未运行 frozen 模块。我按源码定义重写了采集规则。
- 我未运行 gater 阶段、formatter、analysis 或内容核查。
- 我未核 C864 的授权、READY 或频道。
- 我未核产品侧 332 条以外的改动。
- 我未验证就绪输入中 `repairStatus` 的 UNRUN 结论之外的行为。
- 我未核实 `notProven` 7 条的正确性。我只记录 Pi3 写下了它们。

Pi3 的 `notProven` 含两条值得保留。

1. 「The historical 164 freeze is not a 164-hash match today.」
2. 「The current fixture and broker repair stay UNRUN and unvalidated.」

这两条与我此前的记录一致。它们诚实。

## 10. 边界

- 未改产品代码。
- 未改核心代码。
- 未改 Pi3 的目录内容。
- 未运行 SDK、测试、Job、授权或网络请求。
- 我只运行了本地只读计算。它们读取文件并算 sha256。
- 本文件为本轮唯一写入。

## 11. 措辞修正后的最终复核

Pi3 对 `readiness-input.json` 做了一次证据措辞修正。本节记录修正后的终态。

### 11.1 最终哈希

| 产物 | 字节 | SHA256 |
| --- | --- | --- |
| `readiness-input.json` | 19773 | `6A7BF3B96F221D4C4732F95A44C503225F205128CCDC1894E613B9B8234C3C79` |

修正前是 `DC495523ADF36799…` 19305 字节。字节增 468。

最终判定：**PASS**。

### 11.2 只改措辞

全部权威字段与不变量未变。我逐项复核。

| 字段 | 值 | 与修正前 |
| --- | --- | --- |
| `core.head` | `5b3c48c7…` | 同 |
| `core.statusEntries` | 42 | 同 |
| `core.wipFilesHashed` | 42 | 同 |
| `core.wipRollupSha256` | `8BC8E2F3…` | 同，且我复算一致 |
| `core.completeWipFiles` | `true` | 同 |
| `frozenMatch` | `true` | 同 |
| pin 命中 | 7 / 7 | 同 |
| `fullInputs.sha256` | `F8D2AB9E…` | 同 |
| `fullInputs.filesSha256` | `7B87BB26…` | 同，且我复算一致 |
| `formatterPaths` | 5 | 同 |
| `repairFiles` | 4 | 同 |
| `permittedChanges.changed` | 2 项 | 同 |
| `unexpectedChanges` | 空 | 同 |
| `permittedOnly` | `true` | 同 |
| `product.head` | `d863397…` | 同 |
| `sourceOnly` / `execution` | `true` / `false` | 同 |
| 顶层键数 | 17 | 同 |

文件集未变。`app-full-inputs.json` 仍为 `F8D2AB9E…` 64409 字节。
`capture-app-full-inputs.py` 仍为 `ADF0FBD8…` 6013 字节。
所以没有重新采集。

### 11.3 修正内容

`notProven` 从 7 条变为 8 条。旧第 6 条拆为两条。

| 序号 | 文本要点 |
| --- | --- |
| 6 | 合并候选（生产字节加夹具清理）未运行 |
| 7 | broker 生产字节已在 C843 运行，且该门禁失败：320 PASS、1 FAIL |
| 8 | 历史 164 冻结不是今日的 164 哈希匹配 |

`repairStatus` 由 1 个键扩为 3 个键。
它们分别描述合并候选、夹具清理与 broker 生产字节。

### 11.4 修正语义准确

我独立核实了第 7 条的三个说法。

第一，broker 生产字节在 C843 运行过。
`web-c843-validation-20261026.md` 写 `Full tests | FAIL, 320 passed and 1 failed`。
它写唯一失败测试是 `owned_preview_resource_broker_test.dart` 的
`deadline aborts the owned request and releases in-flight accounting`。

第二，那些生产字节与现在相同。
`lib/services/owned_preview_resource_broker.dart` 在三处都是 `56fd917c…` 11793 字节。
三处是 C843 前清单行、C864 清单行与当前磁盘。

第三，合并候选未运行。
夹具修复发生在 C843 之后。它尚未运行。
我这个结论与我上轮的静态复核一致。

所以第 7 条准确。旧文本把「夹具与 broker 修复」一起标为未运行，对生产字节不准确。
修正后不再混淆两者。

### 11.5 两个辅助文件也变了

| 文件 | 修正前 | 修正后 | 字节差 |
| --- | --- | --- | --- |
| `build-readiness-input.py` | `42FF4152…` 16085 | `5B56F184…` 16692 | +607 |
| `refreeze-report.md` | `86B95CC4…` 4339 | `028EC18C…` 4604 | +265 |

构建器变是必然的。`notProven` 与 `repairStatus` 的文本是构建器里的字面量。
改文本就要改构建器。

我核了构建器的哈希原语未变。
`sha256_file` 在 `:109`。`canonical_sha256` 在 `:117`。
`rollup` 在 `:166`。`wipRollupSha256` 在 `:175`。
新增内容只是 `:321-327` 与 `:340-341` 的文本。
所以计算逻辑未变，我复算的值仍一致。

### 11.6 164 冻结：163 加 1 覆盖

父冻结文件在第三个仓库 `qfli_c`。
路径是 `.trellis/tasks/10-22-offline-standalone-ide/research/terminal-recovery-20261026/core-lib-config-freeze.json`。

| 项 | 值 |
| --- | --- |
| 文件 SHA256 | `863F97CEB34FCB491780F1BA4AC38DADF472E1BA28C0CF0F7A522F89BA4E04D0` |
| 与声明比对 | 一致 |
| 字节 | 18626 |
| 绑定文件数 | 164 |
| 未变 | 163 |
| 变化 | 1 |
| 缺失 | 0 |

唯一变化是 `lib/services/process_supervisor.dart`，从 `25ba430c…` 到 `095de8c1…`。

terminal 在冻结内绑定为 `7bf7d365…`。
它在当前磁盘也是 `7bf7d365…`。所以它未变。

该冻结自带的 `productionTerminalSha256` 也是 `7bf7d365…`。
所以 terminal 在 164 冻结时已是这个值，此后不变。

我独立算得 163 加 1 的分解成立。

### 11.7 未变项

- 我未运行任何测试或 gater。
- 我未核 `readiness-input.json` 之外的新一轮声明。
- 我未核 `refreeze-report.md` 全文的新措辞。
- `permittedChanges.allowed` 仍含 F1 的冗余别名。它是白名单，不影响判定。
- F2 的范围披露缺口仍在。

### 11.8 边界

- 未改产品、核心或 `qfli_c` 的任何文件。
- 未改 Pi3 的目录内容。
- 未运行 SDK、测试、Job、授权或频道。
- 只运行本地只读计算。它们读文件并算 sha256。