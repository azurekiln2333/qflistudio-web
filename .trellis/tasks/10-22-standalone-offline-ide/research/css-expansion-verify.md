# CSS expansion — module self-verification

Generated: 2026-10-22T05:16:19.033Z

Reproduces `emit_content.py` output for `curriculum/css_expansion.py` (marker injection
included) and executes every generated example against
`scripts/css_expansion_assertions.mjs`, at a pinned 960x720 viewport and again at
1280x900 to prove the oracle is not host-width dependent.

## Schema / policy

- entries: 60
- distinct code bodies: 60
- shortest explain: 181 chars; shortest document: 355 chars
- issues: 0

## Execution

Examples: 60. Passed (pinned): 60. Passed (alt viewport): 60. Assertions: 547.

| id | title | checks | pinned | alt viewport | first failure |
| --- | --- | --- | --- | --- | --- |
| css-example-101 | @layer 级联层：用层顺序取代书写顺序 | 9 | pass | pass |  |
| css-example-102 | @layer 与 !important 的层顺序反转 | 8 | pass | pass |  |
| css-example-103 | @scope：给样式划定作用域与边界 | 8 | pass | pass |  |
| css-example-104 | @property：给自定义属性加上类型 | 10 | pass | pass |  |
| css-example-105 | :where() 的零权重与 :is() 的继承权重 | 7 | pass | pass |  |
| css-example-106 | :nth-child(An+B of S) 过滤后计数 | 9 | pass | pass |  |
| css-example-107 | :has() 让父级跟随子级状态变化 | 11 | pass | pass |  |
| css-example-108 | :focus-within 让整个表单组进入聚焦态 | 10 | pass | pass |  |
| css-example-109 | :user-invalid 只在用户操作后才报错 | 9 | pass | pass |  |
| css-example-110 | :target 实现纯 CSS 标签页 | 9 | pass | pass |  |
| css-example-111 | :empty 空状态占位与空白陷阱 | 10 | pass | pass |  |
| css-example-112 | @counter-style 自定义序号标记 | 9 | pass | pass |  |
| css-example-113 | ::file-selector-button 自定义文件选择按钮 | 10 | pass | pass |  |
| css-example-114 | flex 简写与 flex-basis: 0 和 auto 的差别 | 10 | pass | pass |  |
| css-example-115 | flex order 改变视觉顺序而不改 DOM | 9 | pass | pass |  |
| css-example-116 | flex-wrap 与 align-content 的多行对齐 | 10 | pass | pass |  |
| css-example-117 | inline-flex 与基线对齐的芯片 | 10 | pass | pass |  |
| css-example-118 | subgrid：子网格继承父网格轨道 | 10 | pass | pass |  |
| css-example-119 | repeat(auto-fill) 与 minmax 的自适应列 | 9 | pass | pass |  |
| css-example-120 | grid-auto-rows 控制隐式行高 | 9 | pass | pass |  |
| css-example-121 | place-items 与 place-content 的分工 | 10 | pass | pass |  |
| css-example-122 | display: contents 展开盒树 | 9 | pass | pass |  |
| css-example-123 | contain: layout paint 隔离渲染 | 9 | pass | pass |  |
| css-example-124 | min()、max() 与 clamp() 的组合运算 | 9 | pass | pass |  |
| css-example-125 | fit-content、max-content 与 min-content 的取舍 | 8 | pass | pass |  |
| css-example-126 | 逻辑属性 inset-inline 与 inset-block | 9 | pass | pass |  |
| css-example-127 | 粘性页头、粘性侧栏与 scroll-margin-top | 11 | pass | pass |  |
| css-example-128 | dvh 与 svh：移动端视口高度单位 | 9 | pass | pass |  |
| css-example-129 | cqi 与 cqw：容器查询单位 | 9 | pass | pass |  |
| css-example-130 | ch 与 cap 排版单位控制行宽与字高 | 8 | pass | pass |  |
| css-example-131 | overflow: clip 与 overflow-clip-margin | 9 | pass | pass |  |
| css-example-132 | oklch 感知均匀色阶 | 9 | pass | pass |  |
| css-example-133 | color-mix() 就地混色 | 9 | pass | pass |  |
| css-example-134 | light-dark() 与 color-scheme 双主题 | 10 | pass | pass |  |
| css-example-135 | 相对颜色 rgb(from …) 的通道运算 | 8 | pass | pass |  |
| css-example-136 | repeating-linear-gradient 条纹背景 | 7 | pass | pass |  |
| css-example-137 | mask-image 渐隐遮罩 | 8 | pass | pass |  |
| css-example-138 | mask-composite 多层遮罩合成 | 9 | pass | pass |  |
| css-example-139 | background-blend-mode 双色叠加 | 7 | pass | pass |  |
| css-example-140 | border-image 渐变边框 | 9 | pass | pass |  |
| css-example-141 | text-emphasis 重点符号 | 8 | pass | pass |  |
| css-example-142 | -webkit-text-stroke 描边字 | 9 | pass | pass |  |
| css-example-143 | text-wrap: balance 平衡折行标题 | 9 | pass | pass |  |
| css-example-144 | hyphens 与 overflow-wrap 的长词处理 | 9 | pass | pass |  |
| css-example-145 | font-variant-numeric 等宽数字对齐 | 8 | pass | pass |  |
| css-example-146 | text-decoration-skip-ink 下划线避让 | 9 | pass | pass |  |
| css-example-147 | box-decoration-break 跨行装饰 | 9 | pass | pass |  |
| css-example-148 | text-box-trim 去掉行首多余空隙 | 9 | pass | pass |  |
| css-example-149 | @starting-style 让离散过渡有入场动画 | 11 | pass | pass |  |
| css-example-150 | animation-fill-mode 与延迟序列 | 9 | pass | pass |  |
| css-example-151 | cubic-bezier 自定义缓动曲线 | 8 | pass | pass |  |
| css-example-152 | 滚动驱动动画 animation-timeline: scroll() | 10 | pass | pass |  |
| css-example-153 | prefers-reduced-motion 动效降级 | 10 | pass | pass |  |
| css-example-154 | animation-composition 叠加动画效果 | 9 | pass | pass |  |
| css-example-155 | scroll-snap 纯 CSS 横向卡片吸附 | 9 | pass | pass |  |
| css-example-156 | scrollbar-gutter 预留滚动条空间 | 9 | pass | pass |  |
| css-example-157 | overscroll-behavior 阻断滚动链 | 9 | pass | pass |  |
| css-example-158 | field-sizing 让输入框随内容变宽 | 9 | pass | pass |  |
| css-example-159 | appearance: none 自定义 select 外观 | 12 | pass | pass |  |
| css-example-160 | CSS 锚点定位 position-anchor | 10 | pass | pass |  |

