# Relay 窗口包装器独立静态复核

日期 2026-10-26。方式为纯静态读取，未运行任何脚本。

## 结论

该文件可留档为禁用研究源码。不能申请窗口。不能称运行就绪。运行路径已关闭，无参数可解锁。

## 固定哈希

本报告只依据下表文件的最新读取。

| 对象 | SHA256 |
| --- | --- |
| `run-web-relay-window.py` | `b4e4c13d20049041c29557ae6fad7341d945aa162588d8153c241748f735c84d` |
| `web-relay-window-handoff-20261026.md` | `680757098fc8fb3ac328276478d82bc8949f76a03f0d1d1188896300c58d10f3` |
| `web-relay-window-design-20261026.md` | `fabfe13da874e5a0842c2abadc6a12212c4b0c522ec673c8ffd3c3991beb50ca` |
| `web-relay-window-incident-20261026.md` | `84c0d26ebbefc2d82a1b058fdb6d2cb24df13b669146c5da78eeef33985a3a8f` |
| `build/web-relay-disabled-pure-controls-20261026.log` | `d8c7234f52061826e3cf39a5f5a845782dc2952757e27b6356d8f36065dc7914` |

包装器大小 41360 字节，末次改动 03:46:02。三份文档随后更新，时间落在 03:56 至 04:02。

## 已核实的禁用事实

- `EXECUTION_STATE = "SOURCE_ONLY_DISABLED"`（49 行）。
- `RUN_ENABLED = False`（48 行）。
- `run()` 首条语句即拒绝（368 至 369 行）。它先于任何副作用。
- `main()` 收到任一 grant、run-name、next-owner、authorization 时不调用 `run()`。它打印拒绝 JSON 并返回 3。
- 参数无法解锁。源码注释明写 no grant of any shape unlocks this revision。
- `self_test()` 体不含 `load_frozen`、`importlib`、`execute` 调用。它不导入冻结模块，不建 Job。
- `self_test()` 内 `run(None)` 期望 `PermissionError`。该用例验证先拒绝再碰参数。
- 无参快照只打印并返回。它不启动进程。

## 文档现状

三份文档都已更新，并自述 SOURCE_ONLY_DISABLED。它们与禁用状态一致。

- handoff 顶部记 99 项纯控通过，`execution=false`、`processStarted=false`，未建 Job。
- design 顶部记 `RUN_ENABLED=False`、`main()` 退出 3、`run()` 先于读参即拒绝。它把余下章节标为历史设计。
- incident 记 `C607-NEG` 未授权运行。它附完整命令行与证据目录。
- 纯控日志记录 99 项 PASS，含 reject placeholder NEG。

## dead run 现存问题

下列问题只存在于已禁用的 `run()` 路径。它们绑定 `b4e4c13d`。留档备将来授权设计。

1. `verdict()` 无时钟参数（279 行）。`status` 可为 `RELAYED`，而 `total_clock_exhausted` 为真。退出码仍为 1，字段本身不诚实。
2. `releaseClaimed` 只由 `status` 与 `cleanup_confirmed` 决定（531 行）。它不含 gate。gate 为 FAIL 时它仍可为真。
3. `run()` 路径从未在禁用版上跑过。它的计时、日志与清理行为均为纸面。
4. `load_authorization` 与实际授权证据路径未在真实运行中验证。
5. HOLD 保持（`while True`，552 行）已写入，但未在真实 Job 上验证。
6. `compose_accept` 仍写这是时钟起点。时钟实起于 wrapper 进程入口，早于 ACCEPT 投递。措辞不准。

## 本轮修正确认

以下四项在 `b4e4c13d` 已闭合。

| 项 | 位置 | 状态 |
| --- | --- | --- |
| 强制清理计入 relay 阶段 | 493 至 494 行 | 已计入 `relay_phase` 与 `cleanup_state["stopped"]` |
| report 写失败不得成功 | 533 至 555 行 | 返回条件含 `persisted`、`not report["errors"]`、`not total_clock_exhausted` |
| 清理未确认不得退出 | 551 至 552 行 | `while True` 保留句柄 |
| 双目录不复用 | `paths_for` | wrapper 用 `-relay` 后缀，child 由冻结 runner 自建 |

## 未授权运行

`C607-NEG` 曾触发一次真实 app 窗口。incident 文档记有完整命令行。证据目录如下。

| 目录 | 内容 |
| --- | --- |
| `web-app-c606-20261026-relay-relay/` | `wrapper.json`、`accept.txt`、`relay.txt`、三段日志 |
| `web-app-c606-20261026-relay/` | 冻结 runner 的 `job.json` 与四段阶段日志 |

该次 `wrapper.json` 记 `grant: "C607-NEG"`、`status: "RELAYED"`、`gate: "FAIL"`、`releaseClaimed: true`。它证明两点。其一，形状校验不授权。其二，`status` 与 `releaseClaimed` 会与 gate 脱节。这正是本轮改为默认禁用的直接理由。

## 交付判定

- 可留档：是。文件、handoff、design 与 incident 都自述禁用。
- 可申请窗口：否。授权证据路径未实现，且未复核。
- 可称运行就绪：否。嵌套 Job 与共享时钟均无实测。
- 解除禁用前必须先落地并复核独立授权证据路径。

## 边界

本轮未启动 Job、SDK、浏览器、Flutter、native 或设备。未运行包装器、`--self-test` 或任何带 grant 的 CLI。仅做静态读取与哈希读取，并定位禁用路径的行号。