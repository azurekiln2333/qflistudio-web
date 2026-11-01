# Relay 窗口最终授权复核

日期 2026-10-26。只读复核。未运行带 grant 的 CLI。未起 SDK、Job 或浏览器。

## 固定哈希

| 对象 | SHA256 | 字节 |
| --- | --- | --- |
| `run-web-relay-window.py` | `aafaa64435d551c65b05858d46bb06449a03d6d3a9293033575c3b6a47f2d5d9` | 59058 |
| `web_relay_authorization.py` | `ee4d251a494772ec607c990a35abca538c07a3b7801863c23ad7dd3e320915e9` | 29293 |

两值与本轮指定值一致。

## 一、原始事件独立 pin

绑定成立，但只是管线独立，不是信任独立。

- `--reviewed-raw-sha256` 是独立命令行参数（1121 行）。
- 入口强制它非空（1145 至 1146 行）。
- 入口校验形状为 64 位小写十六进制（154 至 155 行）。
- 该 pin 同时进入 `validate_receipt`（177 行）与 `decide_execution`（185 行）。
- 模块比对 pin 与 `digest_of(rawEvent)`（397 至 398 行）。不符即拒。

限制：wrapper 不加载独立的原始事件文件。pin 只表达 root 的断言。任何能拼命令的人都能按收据算出同一个 pin。模块自身声明不做密码学认证。该 pin 证明一致，不证明真实。

## 二、实际 fresh grant

进程内成立。持久性有缺口。

- 新鲜度只由标记文件承载。
- 标记目录写死为 `RESEARCH / ".web-relay-consumed"`（184 行）。命令行不能改道。
- 标记按协调者与 grant 命名。
- 模块用 `O_CREAT|O_EXCL` 独占创建（259 行）。第二次即重放。
- 校验失败不落标记。消费只在真实运行路径触发。

缺口：模块建目录时用 `mkdir(parents=True, exist_ok=True)`。删掉 `.web-relay-consumed/` 即恢复可重放。该目录无校验。它无防篡改。它无镜像。wrapper 也不校验它是否原在。

## 三、marker 先于任何 Job

成立。

| 行 | 动作 |
| --- | --- |
| 534 | 消费标记，`consume=True` |
| 538 | 载入冻结模块 |
| 539 | 载入 helper |
| 540 | 读取 wrapper 身份 |
| 541 | 建 wrapper 目录 |
| 587 | 第一个 Job，ACCEPT 发布 |
| 607 | 格式化 Job |
| 625 | supervisor Job |
| 661 | relay Job |

消费早于全部 `frozen.execute`。载入与建目录都不建 Job。

代价属有意 fail-closed：534 行之后任一步抛错，grant 已烧且无运行。

## 四、跨 run-name 防重放

成立。

- 模块 `MARKER_FIELDS = ("author", "grant")`（68 行）。
- `marker_binding` 只取这两项（229 行）。
- `marker_id` 与 run-name、seq、哈希、过期都无关（232 至 241 行）。
- wrapper 只传 `marker_dir` 与收据。它不把 run-name 带进标记。

同一 grant 换 run-name 仍落同一标记。第二次报 `already consumed`。

## 残余问题

1. 标记目录可删。一次性属性依赖仓库内一个普通目录。建议记录其摘要，并加只读保护。
2. pin 须由 root 从真实原始事件算出。若有人按收据算 pin，绑定仍会通过。该项只靠流程约束。
3. `event.successor` 与命令 successor 的交叉校验缺失。此项已修，见追加复核。
4. 收据绑定 wrapper 当前字节。收据必须在 wrapper 定稿后创建。

## 边界

未运行带 grant 的 CLI。未探测真实授权。未起 SDK、Job、浏览器、Flutter 或设备。未改任何代码与报告以外文件。

---

# 追加复核：successor 缺口已修

日期 2026-10-26。只读复核。本次只看 successor 修复与 pin 更新。

## 新哈希

| 对象 | SHA256 | 字节 |
| --- | --- | --- |
| `run-web-relay-window.py` | `338d31ce67b8decb08bc9eff2af6ac20548bb372b822c24288f00b717974db7e` | 60227 |
| `web_relay_authorization.py` | `84445442fed9b9382555e02b8812c6321cbd7c7ec5026ff13904c5f5897a1de4` | 30119 |
| `test_web_relay_authorization.py` | `95ee470e83c355953a56f2f6fa5f847f15723d05816402bbaaa9d59c8a569a0f` | 31765 |

两值与指派值一致。

## 差异一：successor 交叉校验

模块 339 至 340 行新增一条。

```python
    if not isinstance(event, dict) or event.get("successor") != successor:
        problems.append("Receipt successor is not the coordinator event successor")
```

原有两条查收据对命令（337 至 338 行）。grant 本来就走传递绑定。successor 不走。补上第三条后，三者闭合：收据对命令，收据对事件，故命令对事件。

## 差异二：回归用例

`test_web_relay_authorization.py` 655 至 662 行新增 `SuccessorBindingRegressionTests`。

用例把收据与命令的 successor 同时改成 `different-owner`。事件仍为 `c-coordinator`。旧代码会放行。新代码报 `Receipt successor is not the coordinator event successor`。这正是我报告的缺口形状，用例形状正确。

## 差异三：wrapper pin

60 行为 `AUTHORIZATION_SHA256 = "84445442…"`，等于新模块哈希。

限制：两个文件都未纳入 git（`git status` 记为 `??`）。磁盘上没有旧副本。因此当时无法逐字节证实「仅更新 pin」。该限制已在追加复核二解除。

可证实三点。pin 值已换。五处 guard 锚点语义未变，即 154 行原始 pin 形状、177 与 185 行 pin 双传、184 行标记目录写死。wrapper 体积从 59058 增到 60258，增加 1169 字节。该增量由换行风格解释，见追加复核二。

## 复核结果

- 模块单元 79 项通过。模块自测 17 项通过。
- 未运行带 grant 的 CLI。未跑 wrapper self-test。未起 runner、SDK 或 Job。
- 你报的 4 入口与 144 控制我未独立复算。wrapper 内 `case(` 计数为 145，即 1 个定义加 144 个用例。数字与 144 控制相符。

## 边界维持

marker 目录可删与 pin 信任属已披露的本机流程边界。本轮不扩成防恶意管理员机制。残余第 1、2 条维持原状。残余第 3 条已修。

---

# 追加复核二：机械复算成立

日期 2026-10-26。只读。未改源码。只在内存内读取与哈希。

## 目标断言

从当前 wrapper 文本反向替换两处，按 LF 编码，应得 `aafaa644…`。

## 复算结果

| 量 | 实测 |
| --- | --- |
| 当前原始字节 | 60258 |
| 当前 SHA256 | `401f61d44495dd0a8b681a25746263e589203a9555f30c49106eca791db0fdb3` |
| CRLF 对数 | 1169 |
| 裸 LF | 0 |
| LF 归一字节 | 59089 |
| 反向替换后字节 | 59058 |
| 反向替换后 SHA256 | `aafaa64435d551c65b05858d46bb06449a03d6d3a9293033575c3b6a47f2d5d9` |
| 与目标比对 | 相同 |

两处替换各命中 1 次。模块 pin 替换为等长。快照键名替换缩短 31 字节。故 59089 减 31 得 59058。

## 换行解释成立

全文 1169 个 CRLF，0 个裸 LF。LF 与 CRLF 之差正好 1169 字节，等于行数。

59058 加 31 加 1169 得 60258。逐项闭合，无余额。

## 结论

上节两条限制解除。

1. wrapper 与 `aafaa644` 的差异确为两处。一处是模块 pin。一处是快照键名。
2. 1169 字节增量全部来自换行风格。它不涉逻辑。

## 键名改动的语义

`"runReachable": False` 改为 `"runReachableWithReviewedAuthorization": RUN_ENABLED`。

旧值写死为假。新值随 `RUN_ENABLED` 取值。当前 `RUN_ENABLED` 为真。故快照现在报可运行，键名还点明前提是已审授权。

旧版本在 root 放开运行路径后仍报假。那是陈旧断言。此项属纠正，不属放宽。

## 边界

未改源码。未运行带 grant 的 CLI。未起 runner、SDK 或 Job。