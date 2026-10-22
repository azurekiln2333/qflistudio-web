"""CSS curriculum expansion, authored for task 10-22-standalone-offline-ide.

60 new complete offline lessons (module schema identical to css_data*.py /
supplement.py). `emit_content.py` appends this module LAST in the css chain, so
the entries here become `css-tutorial-101..160` / `css-example-101..160`.

Authoring rules (enforced by research/css-expansion-verify.mjs):
  * one complete, self-contained offline HTML document per lesson, inline
    <style> only, no external URL, no <script>, no `webforge-check` marker
    (emit_content injects that marker itself);
  * full Chinese explanation, 4-7 concepts, exactly 3 pitfalls, >=1 exercise;
  * every lesson is asserted by scripts/css_expansion_assertions.mjs with
    literal computed values, so the numbers below are the taught contract.
"""

CSS_EXTRA = []

# ---------------------------------------------------------------------------
# A. Cascade, layers and scope (101-106)
# ---------------------------------------------------------------------------

_B1 = [
    {
        "t": "@layer 级联层：用层顺序取代书写顺序",
        "level": "advanced",
        "obj": "用 @layer 显式声明层顺序，让同一优先级的选择器按层而不是书写先后决定胜负。",
        "pre": ["层叠、继承与优先级"],
        "con": ["@layer", "层顺序", "未分层样式", "层语句"],
        "explain": "`@layer` 把样式分成若干层，层与层之间的胜负由层的先后顺序决定，而不是规则出现的位置。先用 `@layer base, theme;` 声明顺序：靠后的层胜出，所以即使 base 的规则写在后面，theme 依然赢。没有放进任何层的普通规则始终赢过分层规则，因此“未分层”是最强的默认层。层的价值在于把“重置、基础、主题、组件”拆开：引入第三方样式时把它整体塞进一个层，自己的组件层就能稳定覆盖它，不再需要堆 !important 或加长选择器。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>级联层</title>
<style>
  @layer base, theme;
  @layer theme { .card { color: #1a73e8; } }
  @layer base  { .card { color: #202124; } }
  .card { background: #f1f3f4; padding: 12px; }
  @layer base { .note { color: #ea4335; } }
  .note { color: #34a853; }
</style>
</head>
<body>
  <p class="card">theme 层写在前面，却因为层顺序靠后而胜出。</p>
  <p class="note">未分层的规则总是赢过分层规则。</p>
</body>
</html>""",
        "out": "卡片文字是 theme 层的蓝色 #1a73e8（不是后面写的 base 黑色），背景 #f1f3f4；提示行是未分层的绿色 #34a853，而不是 base 层的红色。",
        "pit": [
            "只写 `@layer a { … } @layer b { … }` 而不写层语句时，层顺序按首次出现的顺序决定，后出现的层反而更强，容易和直觉相反。",
            "未分层规则赢过所有分层规则，把组件样式漏在层外会让主题层彻底失效。",
            "层只影响优先级比较，不改变选择器特异性：层内 0,0,1 仍然输给层内 0,1,0。",
        ],
        "ex": [
            (
                "把主题色从蓝色改成紫色 #7b1fa2，并让 base 层保持黑色。",
                "只改 theme 层里的 color。",
                "@layer theme { .card { color: #7b1fa2; } }",
            )
        ],
    },
    {
        "t": "@layer 与 !important 的层顺序反转",
        "level": "advanced",
        "obj": "理解 !important 声明在层之间是反向比较的，并用它设计可覆盖的重置层。",
        "pre": ["@layer 级联层：用层顺序取代书写顺序"],
        "con": ["!important", "层反转", "reset 层", "覆盖策略"],
        "explain": "普通声明里，靠后的层更强；但 `!important` 声明在层之间的比较方向是反的：越早的层越强。这条规则让“重置层”可以安全地使用 !important 保护关键声明，同时保证后写的主题层仍然能用普通声明覆盖其他属性。实际写法是把 `@layer reset, base, theme;` 放在最前面，reset 里只写真正需要强制的内容。理解这一点可以避免“加了 !important 反而被更早的层压住”的困惑：这不是 bug，而是层与 !important 共同定义的两套顺序。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>层与 important</title>
<style>
  @layer reset, app;
  @layer app   { .btn { color: #ffffff; background: #1a73e8; } }
  @layer reset { .btn { color: #ff0000; } }
  @layer app   { .warn { color: #ffffff; background: #ea4335; } }
  @layer reset { .warn { color: #202124 !important; } }
  @layer app   { .warn { color: #ffffff !important; } }
</style>
</head>
<body>
  <p class="btn">普通声明：靠后的 app 层胜出。</p>
  <p class="warn">两条 !important 相撞：更早的 reset 层胜出。</p>
</body>
</html>""",
        "out": "按钮白字蓝底；警告行是深灰字 #202124 配红底，说明 !important 让更早的 reset 层赢了 app 层。",
        "pit": [
            "以为 !important 一律最强：它只在同一层内最强，跨层时反而偏向更早的层。",
            "把 reset 层写在层语句之后才声明，层顺序会变成首次出现顺序，反转关系随之改变。",
            "用 !important 去修普通层冲突，会把问题升级成两层 !important 对抗，更难维护。",
        ],
        "ex": [
            (
                "让 app 层的警告文字改成白色并仍然胜过 reset 层。",
                "把 app 的声明放进比 reset 更早的层。",
                "@layer app, reset; 并保持 .warn 的 !important 在 app 层。",
            )
        ],
    },
    {
        "t": "@scope：给样式划定作用域与边界",
        "level": "advanced",
        "obj": "用 @scope 把选择器限制在根元素范围内，并用 to 语法排除嵌套区域。",
        "pre": ["层叠、继承与优先级"],
        "con": ["@scope", ":scope", "donut 边界", "选择器作用域"],
        "explain": "`@scope (.panel) { p { … } }` 表示只在 `.panel` 子树里匹配 `p`，作用相当于给每条规则加上 `.panel` 前缀，但不需要写出来，也不会把特异性抬高。`to (.quote)` 再划出一条下界：`.quote` 及其子树被排除在外，形成中间有洞的“甜甜圈”范围，这正是组件里“不要再深入嵌套子组件”的常见需求。`@scope` 内的 `:scope` 指作用域根元素本身，可以用来只给根加样式。它解决的是选择器污染，不改变层叠与优先级规则。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>作用域</title>
<style>
  @scope (.panel) to (.quote) {
    :scope { background: #f1f3f4; padding: 12px; }
    p { color: #1a73e8; }
  }
  .quote p { color: #202124; }
</style>
</head>
<body>
  <section class="panel">
    <p id="inside">作用域内的段落是蓝色。</p>
    <section class="quote">
      <p id="outside">被 to (.quote) 排除的段落保持深灰。</p>
    </section>
  </section>
</body>
</html>""",
        "out": "面板背景 #f1f3f4、内边距 12px；第一段蓝色 #1a73e8；嵌套引用块里的段落是深灰 #202124。",
        "pit": [
            "把 `to` 的目标写成作用域根自身，会把整个子树都排除，规则一条也不生效。",
            "以为 @scope 会降低特异性：它只是限定匹配范围，特异性仍按内部选择器计算。",
            "用 @scope 替代组件命名空间后忘记边界，深层嵌套组件的样式仍会被外层覆盖。",
        ],
        "ex": [
            (
                "让被排除的引用块段落变成斜体，而不影响作用域内段落。",
                "在作用域外单独写 .quote p 规则。",
                ".quote p { font-style: italic; }",
            )
        ],
    },
    {
        "t": "@property：给自定义属性加上类型",
        "level": "advanced",
        "obj": "用 @property 声明自定义属性的语法、继承性与初始值，让它可以被过渡和校验。",
        "pre": ["变量与主题：CSS 自定义属性"],
        "con": ["@property", "syntax", "inherits", "initial-value"],
        "explain": "普通自定义属性只是字符串，浏览器不知道它是什么，因此既不能做类型检查也不能平滑过渡。`@property` 用 `syntax: \"<angle>\"` 之类的描述符声明类型，用 `inherits: false` 控制是否向下继承，用 `initial-value` 给出未设置时的兜底值。声明之后，`--angle` 就真的按角度解析：可以参与 `transition`、`animation` 插值，写错单位会被丢弃并回退到初始值。它把“CSS 变量”从文本替换升级为有类型的属性，是动画和设计系统里最实用的一项现代能力。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>类型化属性</title>
<style>
  @property --angle {
    syntax: "<angle>";
    inherits: false;
    initial-value: 0deg;
  }
  @property --tone {
    syntax: "<color>";
    inherits: true;
    initial-value: #1a73e8;
  }
  .dial {
    width: 80px; height: 80px; border-radius: 50%;
    background: conic-gradient(from var(--angle), #1a73e8, #e8f0fe);
    transition: --angle 0.3s linear;
  }
  .dial:hover { --angle: 180deg; }
  .swatch { color: var(--tone); }
  .unset { color: var(--tone); }
</style>
</head>
<body>
  <div class="dial" id="dial"></div>
  <p class="swatch" style="--tone: #34a853">显式设置的自定义属性值。</p>
  <p class="unset" id="unset">没有设置时取 initial-value。</p>
</body>
</html>""",
        "out": "圆盘用蓝色锥形渐变，悬停时渐变起始角度过渡到 180deg；第一段绿色 #34a853；第二段使用初始值蓝色 #1a73e8。",
        "pit": [
            "syntax 写错（例如 `<length>` 却赋值 `10`）会让声明被丢弃，元素直接回退到 initial-value。",
            "忘记写 initial-value 时，注册属性在未设置处的计算值是无效值，transition 不会按预期运行。",
            "把 inherits 写成 true 又给子元素设置不同值，会让过渡在整棵子树上同时触发。",
        ],
        "ex": [
            (
                "把圆盘的过渡改成 1s 并使用 ease-in-out。",
                "改 .dial 的 transition 简写。",
                "transition: --angle 1s ease-in-out;",
            )
        ],
    },
    {
        "t": ":where() 的零权重与 :is() 的继承权重",
        "level": "advanced",
        "obj": "区分 :where() 的零特异性与 :is() 取参数最高特异性的行为，用它们写可覆盖的基础样式。",
        "pre": ["CSS 伪类进阶：:not、:is、:where"],
        "con": [":where()", ":is()", "特异性", "可覆盖基础样式"],
        "explain": "`:where()` 的特异性恒为 0，即使括号里写的是 id 选择器也一样；`:is()` 则取参数列表中特异性最高的那个。于是同一条基础样式，用 `:where(.list) li` 写成 0,0,1，任何 `.list li`（0,1,1）都能轻松覆盖它；换成 `:is(.tags) .tag` 就是 0,1,1，反而能压过单独的 `.tag`。写设计系统时常用 `:where()` 给默认值、把覆盖权留给使用者，用 `:is()` 合并重复选择器同时保留强度。两者都不改变层叠顺序，只改变权重。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>where 与 is</title>
<style>
  :where(.list) li { color: #1a73e8; }
  .list li { color: #202124; }
  :where(.tags) .tag { text-decoration-line: underline; }
  .tags .tag { text-decoration-line: none; }
  :is(.tags) .tag { color: #ea4335; }
  .tag { color: #34a853; }
</style>
</head>
<body>
  <ul class="list"><li id="plain">:where() 权重为 0，被普通类选择器覆盖。</li></ul>
  <div class="tags"><span class="tag" id="tagged">:is() 继承最高权重，压过单个类。</span></div>
</body>
</html>""",
        "out": "列表项是深灰 #202124（:where 版本被覆盖）；标签文字红色 #ea4335（:is 版本胜出），且没有下划线。",
        "pit": [
            "以为 :where() 只是简写：它的 0 权重会让“看起来更强”的规则失效。",
            "把 id 放进 :where() 仍得不到 id 的权重，覆盖关系与直觉相反。",
            "在 :is() 里混入 id 选择器，会意外抬高整条规则的权重。",
        ],
        "ex": [
            (
                "让标签重新带上下划线，同时保持红色。",
                "把下划线规则改成普通类选择器。",
                ".tags .tag { text-decoration-line: underline; }",
            )
        ],
    },
    {
        "t": ":nth-child(An+B of S) 过滤后计数",
        "level": "intermediate",
        "obj": "用 of 语法先按选择器过滤再计数，精确命中第 N 个匹配项。",
        "pre": ["CSS 选择第一个与最后一个"],
        "con": [":nth-child()", "of S 过滤", "An+B", ":nth-last-child()"],
        "explain": "`li:nth-child(2 of .pick)` 的意思是：先只保留带 `.pick` 的子元素，再取其中的第 2 个。没有 `of` 时计数包含所有同级元素，混排列表里就会数错位置；加上过滤后，序号只按目标子集计算。它还能和 `An+B` 组合成 `nth-child(2n of .pick)` 做隔行，用 `:nth-last-child(1 of .pick)` 取过滤后的最后一个。这是纯 CSS 实现“只给有效项编号”“跳过隐藏项”的关键工具。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>过滤计数</title>
<style>
  li { color: #202124; }
  li:nth-child(2 of .pick) { color: #1a73e8; }
  li:nth-child(3 of .pick) { background: #e8f0fe; }
  li:nth-last-child(1 of .pick) { font-weight: 700; }
</style>
</head>
<body>
  <ul>
    <li>第一项：不参与计数</li>
    <li class="pick" id="p1">第二项：pick 第 1 个</li>
    <li>第三项：不参与计数</li>
    <li class="pick" id="p2">第四项：pick 第 2 个，变蓝</li>
    <li class="pick" id="p3">第五项：pick 第 3 个，浅蓝底</li>
    <li class="pick" id="p4">第六项：pick 第 4 个，也是最后一个，加粗</li>
  </ul>
</body>
</html>""",
        "out": "只有 pick 第 2 项变蓝 #1a73e8，第 3 项有 #e8f0fe 背景，最后一项加粗；其余项保持默认。",
        "pit": [
            "把 `of` 写成后代选择器（如 `of .list .pick`），过滤集合会变成空集，规则完全不生效。",
            "以为 `of` 会改变计数起点：序号仍从 1 开始，只是集合变小。",
            "在动态列表里用 `nth-child` 而不加 `of`，插入或隐藏元素后序号会整体错位。",
        ],
        "ex": [
            (
                "让 pick 的第 1 项也变成蓝色。",
                "把 2 改成 1。",
                "li:nth-child(1 of .pick) { color: #1a73e8; }",
            )
        ],
    },
]

# ---------------------------------------------------------------------------
# B. Selector state and native validation (107-113)
# ---------------------------------------------------------------------------

_B2 = [
    {
        "t": ":has() 让父级跟随子级状态变化",
        "level": "intermediate",
        "obj": "用 :has() 依据子元素或相邻兄弟的状态给祖先与兄弟元素加样式。",
        "pre": ["CSS 伪类进阶：:not、:is、:where"],
        "con": [":has()", "关系选择器", "父级选择", "相邻兄弟"],
        "explain": "CSS 一直只能“向下”选择，`:has()` 补上了向上和横向的能力：`.plan:has(input:checked)` 在卡片内部有被选中的单选框时命中卡片本身，`.card:has(+ .card)` 则判断后面是否还跟着兄弟卡片。它支持相对选择器，所以 `:has(> img)` 只检查直接子元素。用它可以把“选中态”从 JS 的 class 切换改成纯 CSS：单选卡片高亮、表单出错时整组标红、列表项有图片时调整内边距。注意 `:has()` 的参数参与特异性计算，且不能嵌套在另一个 `:has()` 里。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>has 选择器</title>
<style>
  .plan {
    display: block; border: 2px solid #dadce0; padding: 12px; margin-bottom: 8px;
  }
  .plan:has(input:checked) { border-color: #1a73e8; background: #e8f0fe; }
  .plan:has(input:checked) .price { color: #1a73e8; }
  .plan input { margin-right: 6px; }
  .card { border-right: 1px dashed #dadce0; padding: 4px 8px; }
  .card:has(+ .card) { color: #202124; }
  .card:not(:has(+ .card)) { color: #34a853; }
</style>
</head>
<body>
  <label class="plan" id="basic"><input type="radio" name="plan" value="basic"> 基础版 <span class="price">￥0</span></label>
  <label class="plan" id="pro"><input type="radio" name="plan" value="pro" checked> 专业版 <span class="price">￥99</span></label>
  <p><span class="card" id="c1">第一张卡</span><span class="card" id="c2">最后一张卡</span></p>
</body>
</html>""",
        "out": "默认专业版卡片有蓝色边框 #1a73e8 与 #e8f0fe 背景、价格变蓝；点击基础版后高亮切换过去。第一张卡是深灰，最后一张卡因为后面没有兄弟而变绿 #34a853。",
        "pit": [
            "把 `:has()` 写在被检查元素的后面（如 `input:checked:has(.plan)`），方向写反后永远不匹配。",
            "`:has()` 里再嵌套 `:has()` 在规范中无效，整条规则会被丢弃。",
            "以为 `:has(+ .card)` 会匹配最后一项：相邻兄弟不存在时它不成立，需要 :not(:has(...)) 才取到最后一项。",
        ],
        "ex": [
            (
                "让未选中的卡片文字变浅灰 #5f6368。",
                "用 :not(:has(input:checked)) 选择未选中卡片。",
                ".plan:not(:has(input:checked)) { color: #5f6368; }",
            )
        ],
    },
    {
        "t": ":focus-within 让整个表单组进入聚焦态",
        "level": "intermediate",
        "obj": "用 :focus-within 给包含焦点的容器加样式，并用 :focus-visible 只对键盘焦点画环。",
        "pre": ["表单控件样式与自定义复选框"],
        "con": [":focus-within", ":focus-visible", "outline-offset", "键盘可达"],
        "explain": "`:focus-within` 在容器内任意后代获得焦点时命中容器，因此可以把边框、背景、阴影加在整组表单上，而不是逐个输入框。`:focus-visible` 只在浏览器判断“用户需要看到焦点”时命中，鼠标点击通常不触发、Tab 键触发，正好避免鼠标用户看到多余的外环。两者配合是表单可访问性的标准做法：容器给出整体反馈，输入框给出精确的键盘焦点环。注意 `outline: none` 会直接破坏键盘可达性，必须用 `:focus-visible` 补回来。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>聚焦组</title>
<style>
  .group { border: 2px solid #dadce0; padding: 12px; margin-bottom: 8px; }
  .group:focus-within { border-color: #1a73e8; background: #f8f9fa; }
  .group input { outline: none; border: 1px solid #dadce0; padding: 6px; }
  .group input:focus-visible { outline: 2px solid #1a73e8; outline-offset: 2px; }
  label { display: block; margin-bottom: 6px; }
</style>
</head>
<body>
  <div class="group" id="active">
    <label>邮箱 <input id="mail" type="email"></label>
    <label>昵称 <input id="nick" type="text"></label>
  </div>
  <div class="group" id="idle"><p>这一组没有焦点。</p></div>
</body>
</html>""",
        "out": "默认两组都是灰边框；用 Tab 聚焦邮箱后，第一组边框变蓝 #1a73e8、背景 #f8f9fa，输入框出现 2px 蓝色外环且偏移 2px；第二组保持不变。",
        "pit": [
            "只写 `input:focus` 而不处理容器，焦点反馈会碎在每个小控件上。",
            "用 `outline: none` 去掉默认环却不补 `:focus-visible`，键盘用户完全看不到焦点。",
            "把 `:focus-within` 加在 body 上，任何焦点都会让整页变色。",
        ],
        "ex": [
            (
                "让聚焦组的边框加粗到 3px。",
                "改 .group:focus-within 的 border。",
                ".group:focus-within { border: 3px solid #1a73e8; }",
            )
        ],
    },
    {
        "t": ":user-invalid 只在用户操作后才报错",
        "level": "advanced",
        "obj": "区分 :invalid 与 :user-invalid，做到“填错才提示，一进来不红”。",
        "pre": ["CSS 输入框错误状态"],
        "con": [":user-invalid", ":valid", ":invalid", "原生校验"],
        "explain": "`:invalid` 在页面加载时就会命中空且必填的输入框，于是用户还没动手就看到一片红色，体验很差。`:user-invalid` 只在用户编辑过该控件并且值仍然不合法时命中，正好对应“提交前/离开输入框后再提示”的期望。两者可以同时使用：`:invalid` 用于内部状态判断，`:user-invalid` 用于视觉提示。配合 `input:valid` 可以把合法状态也标成绿色，形成即时的正负反馈；再加上相邻兄弟选择器 `~ .msg` 就能让错误文案跟随输入框变色。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>用户无效态</title>
<style>
  input { border: 2px solid #dadce0; padding: 6px; }
  input:valid { border-color: #34a853; }
  input:user-invalid { border-color: #ea4335; }
  .msg { color: #5f6368; font-size: 13px; }
  input:user-invalid ~ .msg { color: #ea4335; }
  label { display: block; margin-bottom: 4px; }
</style>
</head>
<body>
  <label for="mail">邮箱</label>
  <input id="mail" type="email" required>
  <p class="msg" id="msg">输入内容并离开输入框后才会出现校验颜色。</p>
</body>
</html>""",
        "out": "刚打开时边框是灰色 #dadce0、提示文字灰色；输入 abc 后离开，边框与提示都变红 #ea4335；改成 user@example.com 后边框变绿 #34a853。",
        "pit": [
            "只用 `:invalid` 做视觉提示，空表单一加载就全红。",
            "以为 `:user-invalid` 需要 JS：它由浏览器的用户交互状态驱动，纯 CSS 即可。",
            "把 `required` 忘了，空值也算合法，`:valid` 会立刻变绿造成误导。",
        ],
        "ex": [
            (
                "让合法状态也显示一句绿色提示。",
                "用 input:valid ~ .msg 加一条规则。",
                "input:valid ~ .msg { color: #34a853; }",
            )
        ],
    },
    {
        "t": ":target 实现纯 CSS 标签页",
        "level": "advanced",
        "obj": "用 URL 片段与 :target 切换面板，不写一行脚本就做出标签页。",
        "pre": ["伪类与伪元素：:hover、::before"],
        "con": [":target", "URL 片段", "面板切换", "::before 标记"],
        "explain": "点击 `href=\"#tab-a\"` 只改变地址栏片段，不会重新加载页面；`:target` 会命中 id 与当前片段相同的元素。把面板默认设为 `display: none`，再用 `.panel:target { display: block }` 只显示被选中的那个，就得到标签页。加 `::before` 可以在激活面板前插入一个指示符。这种方案完全离线、可前进后退、可分享链接，适合文档、设置页和教程。代价是页面会跳转到锚点位置，需要配合 `scroll-margin-top` 或固定头部高度来避免遮挡。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>target 标签页</title>
<style>
  .panel { display: none; border: 2px solid #dadce0; padding: 12px; }
  .panel:target { display: block; border-color: #1a73e8; }
  .panel:target::before { content: "▶ "; color: #1a73e8; }
  nav a { margin-right: 12px; color: #1a73e8; }
</style>
</head>
<body>
  <nav><a id="go-a" href="#tab-a">面板 A</a><a id="go-b" href="#tab-b">面板 B</a></nav>
  <section class="panel" id="tab-a"><h2>A 的内容</h2><p>只有被 :target 命中的面板才显示。</p></section>
  <section class="panel" id="tab-b"><h2>B 的内容</h2><p>切换链接即可换面板。</p></section>
</body>
</html>""",
        "out": "初始两个面板都隐藏；点击“面板 A”后 A 显示、边框蓝色并带“▶ ”前缀；点击“面板 B”后 B 显示、A 隐藏。",
        "pit": [
            "忘记给面板写默认 `display: none`，所有面板会同时出现。",
            "把 id 写成中文或带空格，片段匹配会失败。",
            "固定页头覆盖锚点：需要 `scroll-margin-top` 给目标留出偏移。",
        ],
        "ex": [
            (
                "让激活面板的背景也变成浅蓝 #f8f9fa。",
                "在 .panel:target 里加 background。",
                ".panel:target { background: #f8f9fa; }",
            )
        ],
    },
    {
        "t": ":empty 空状态占位与空白陷阱",
        "level": "beginner",
        "obj": "用 :empty 识别真正没有子节点的元素并显示占位内容。",
        "pre": ["伪类与伪元素：:hover、::before"],
        "con": [":empty", "占位内容", "空白字符", "::before"],
        "explain": "`:empty` 只在元素没有任何子节点（包括文本节点）时命中。关键陷阱是空白：`<div> </div>` 里有一个空格文本节点，就不算空。所以模板里的空容器必须写成 `<div></div>`，中间不能有换行或空格。利用这一点可以在列表为空时显示占位文案：`.list:empty::before { content: \"暂无数据\" }`，不需要脚本判断长度。它适合静态站点和离线应用的骨架屏，但动态清空内容时要确保用 `textContent = ''` 而不是留一个空格。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>空状态</title>
<style>
  .slot { min-height: 32px; border: 1px dashed #dadce0; padding: 8px; }
  .slot:empty { background: #f8f9fa; }
  .slot:empty::before { content: "暂无数据"; color: #5f6368; }
  .slot.filled { border-style: solid; border-color: #34a853; }
</style>
</head>
<body>
  <div class="slot" id="empty"></div>
  <div class="slot filled" id="full">已有内容</div>
</body>
</html>""",
        "out": "第一个格子显示灰色“暂无数据”并有浅灰底；第二个格子显示“已有内容”，边框为绿色实线。",
        "pit": [
            "容器里有换行或空格时不再匹配 `:empty`，占位文案不出现。",
            "用 `:empty` 判断“没有可见内容”，但隐藏元素仍是子节点，判断会失效。",
            "把占位文案写进 HTML 再想用 :empty 覆盖，两者会同时显示。",
        ],
        "ex": [
            (
                "把占位文案改成“还没有项目”。",
                "改 ::before 的 content。",
                '.slot:empty::before { content: "还没有项目"; }',
            )
        ],
    },
    {
        "t": "@counter-style 自定义序号标记",
        "level": "advanced",
        "obj": "用 @counter-style 定义自己的编号体系，并让 ::marker 使用它。",
        "pre": ["CSS 计数器与序号"],
        "con": ["@counter-style", "system", "symbols", "::marker"],
        "explain": "`@counter-style` 定义一个命名的计数体系：`system` 决定递推方式（`cyclic` 循环、`numeric` 数字、`fixed` 固定序列等），`symbols` 给出符号表，`suffix` 控制序号后的分隔符。定义后用 `list-style-type: 名字` 或 `list-style-type: 名字` 让列表使用它，`::marker` 还能单独设置颜色和字号。相比 `::before { content: counter(...) }`，它的优势是序号是真正的列表标记，能参与 `list-style-position` 和可访问性树，也更容易复用。适合步骤条、章节编号和带图标的有序列表。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>自定义序号</title>
<style>
  @counter-style thumbs {
    system: cyclic;
    symbols: "①" "②" "③";
    suffix: " ";
  }
  ol.steps { list-style-type: thumbs; padding-left: 28px; }
  ol.steps li { margin-bottom: 6px; }
  ol.steps li::marker { color: #1a73e8; font-size: 18px; }
</style>
</head>
<body>
  <ol class="steps">
    <li>安装离线运行时</li>
    <li>打开本地预览</li>
    <li>导出静态站点</li>
  </ol>
</body>
</html>""",
        "out": "三个列表项前面分别显示蓝色 ① ② ③，序号字号 18px，序号与文字之间有一个空格。",
        "pit": [
            "`system: cyclic` 的符号用完后会从头循环，列表变长后序号重复。",
            "忘记写 `suffix`，序号会和文字紧贴在一起。",
            "把 @counter-style 写在样式表末尾、又被 @layer 包住时，作用域外可能引用不到。",
        ],
        "ex": [
            (
                "把符号换成 A、B、C 并保持循环。",
                "只改 symbols。",
                'symbols: "A" "B" "C";',
            )
        ],
    },
    {
        "t": "::file-selector-button 自定义文件选择按钮",
        "level": "intermediate",
        "obj": "用 ::file-selector-button 给原生上传控件的按钮单独设置样式。",
        "pre": ["CSS 表单外观统一"],
        "con": ["::file-selector-button", "appearance", "文件上传", "伪元素"],
        "explain": "`<input type=\"file\">` 的按钮部分是浏览器内部构件，普通选择器改不到。`::file-selector-button` 是专门暴露给它的伪元素，可以设置背景、圆角、内边距、字体和鼠标指针，让上传控件与设计系统统一。输入框本体仍用普通规则设置边框和内边距。要注意这个伪元素只能设置一部分属性（字体、颜色、背景、边框、内边距等），布局类属性大多无效；不同浏览器对默认值的处理也略有差异，因此显式写出关键属性更稳。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>上传按钮</title>
<style>
  input[type="file"] {
    border: 1px solid #dadce0; border-radius: 8px; padding: 6px; width: 320px;
  }
  input[type="file"]::file-selector-button {
    appearance: none;
    background: #1a73e8; color: #ffffff;
    border: none; border-radius: 6px;
    padding: 8px 14px; margin-right: 12px;
    font-size: 14px; cursor: pointer;
  }
</style>
</head>
<body>
  <input type="file" id="upload">
</body>
</html>""",
        "out": "上传控件外层是 8px 圆角灰边框，内部按钮为蓝底白字、6px 圆角、内边距 8px 14px。",
        "pit": [
            "用 `input[type=file] { background: … }` 想改按钮，结果只改了控件背景。",
            "在伪元素里写 `display: flex` 之类的布局属性，浏览器会忽略。",
            "漏写 `appearance: none`，部分平台仍会画出系统默认按钮外观。",
        ],
        "ex": [
            (
                "把按钮背景改成绿色 #34a853。",
                "改伪元素的 background。",
                "input[type=file]::file-selector-button { background: #34a853; }",
            )
        ],
    },
]

_B3 = [
    {
        "t": "flex 简写与 flex-basis: 0 和 auto 的差别",
        "level": "advanced",
        "obj": "用 flex 简写控制伸缩，并理解 flex-basis 取 0 与 auto 时分配结果的差异。",
        "pre": ["Flexbox 布局：主轴与交叉轴"],
        "con": ["flex 简写", "flex-basis", "flex-grow", "等分与按内容"],
        "explain": "`flex` 是 `flex-grow flex-shrink flex-basis` 的简写，默认值 `0 1 auto`。关键在 basis：写成 `flex: 1 1 0` 时基准尺寸为 0，所有剩余空间按 grow 平均分配，于是三项等宽，和内容长短无关；写成 `flex: 1 1 auto` 时基准是内容本身宽度，剩余空间再按 grow 叠加，内容长的项最后更宽。常见 bug 是“想等分却写了 flex: 1 1 auto”，内容一长就分不匀。要真正等分请用 `flex: 1`，它的完整含义就是 `1 1 0%`。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>flex 简写</title>
<style>
  * { box-sizing: border-box; }
  body { margin: 0; }
  .row { display: flex; width: 600px; margin-bottom: 12px; }
  .row > div { padding: 8px; border: 1px solid #dadce0; background: #e8f0fe; }
  .zero > div { flex: 1 1 0; }
  .auto > div { flex: 1 1 auto; }
</style>
</head>
<body>
  <div class="row zero" id="zero"><div id="z1">短</div><div id="z2">中等长度</div><div id="z3">很长很长很长很长很长很长的文本</div></div>
  <div class="row auto" id="auto"><div id="a1">短</div><div id="a2">中等长度</div><div id="a3">很长很长很长很长很长很长的文本</div></div>
</body>
</html>""",
        "out": "第一行三项各 200px 等宽；第二行按内容分配，第三项明显宽于第一项。两行的 flex-basis 分别是 0px 与 auto。",
        "pit": [
            "想等分却用 `flex: 1 1 auto`，内容长的子项会抢占更多空间。",
            "只写 `flex: 1` 以为等于 `flex: 1 1 auto`，实际是 `1 1 0%`。",
            "忘记 `min-width: 0`，内容不可断行的子项会被最小内容宽度撑住，等分失效。",
        ],
        "ex": [
            (
                "让第一行第一项占两份宽度，其余各占一份。",
                "给第一项单独的 flex-grow。",
                "#z1 { flex: 2 1 0; }",
            )
        ],
    },
    {
        "t": "flex order 改变视觉顺序而不改 DOM",
        "level": "intermediate",
        "obj": "用 order 调整视觉顺序，同时保留 DOM 顺序带来的阅读与键盘顺序。",
        "pre": ["Flexbox 布局：主轴与交叉轴"],
        "con": ["order", "视觉顺序", "DOM 顺序", "键盘顺顺"],
        "explain": "`order` 只在 flex 或 grid 容器内生效，数值小的排前面，默认 0。它可以不动物结构就把“置顶”“置底”做出来，视觉顺序和 DOM 顺序因此可以不一致。代价是可访问性：屏幕阅读器和键盘 Tab 仍然按 DOM 顺序走，视觉顺序被改得太多会造成焦点乱跳。所以 order 适合小范围重排（例如把侧栏移到前面），而不是整体重排页面。要真正改变阅读顺序，应该改 HTML 结构，而不是只改 order。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>order</title>
<style>
  body { margin: 0; }
  .row { display: flex; gap: 8px; width: 300px; }
  .row li { list-style: none; padding: 8px 12px; background: #e8f0fe; }
  .row li:nth-child(1) { order: 3; }
  .row li:nth-child(2) { order: 1; }
  .row li:nth-child(3) { order: 2; }
</style>
</head>
<body>
  <ul class="row" id="row"><li id="one">一</li><li id="two">二</li><li id="three">三</li></ul>
</body>
</html>""",
        "out": "屏幕上从左到右是“二、三、一”，但 DOM 里仍然是“一、二、三”，Tab 键也按一、二、三走。",
        "pit": [
            "给非 flex/grid 子项写 order，属性被忽略且没有任何提示。",
            "用 order 做大范围重排，键盘焦点顺序与视觉顺序错位。",
            "以为 order 会改变 DOM：打印、复制、读屏拿到的还是原顺序。",
        ],
        "ex": [
            (
                "把“一”放回最前面。",
                "把第一项的 order 改为 0。",
                ".row li:nth-child(1) { order: 0; }",
            )
        ],
    },
    {
        "t": "flex-wrap 与 align-content 的多行对齐",
        "level": "intermediate",
        "obj": "在换行的 flex 容器里用 align-content 控制行与行之间的分布。",
        "pre": ["Flexbox 布局：主轴与交叉轴"],
        "con": ["flex-wrap", "align-content", "gap", "多行"],
        "explain": "`flex-wrap: wrap` 让一行放不下时换行，但换行之后“行与行怎么排”由 `align-content` 决定，而不是 `align-items`：`align-items` 管的是每行内部、行与行在交叉轴上的整体分布交给 `align-content`。容器有固定高度时，`align-content: flex-start` 把两行都挤在顶部，`center` 让整块居中，`space-between` 把第一行顶到最上、最后一行压到最下。行距用 `gap` 控制，不要再用 margin 叠。忘记设置高度时容器高度由内容决定，align-content 看不出效果，这也是“设了没用”的常见原因。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>多行 flex</title>
<style>
  body { margin: 0; }
  .wrap {
    display: flex; flex-wrap: wrap; align-content: flex-start;
    gap: 10px; width: 300px; height: 200px; background: #f8f9fa;
  }
  .wrap div { width: 90px; height: 40px; background: #e8f0fe; }
</style>
</head>
<body>
  <div class="wrap" id="wrap">
    <div id="i1">1</div><div id="i2">2</div><div id="i3">3</div>
    <div id="i4">4</div><div id="i5">5</div><div id="i6">6</div>
  </div>
</body>
</html>""",
        "out": "六个格子排成两行、每行三个，两行都贴在容器顶部，行内与行间间距都是 10px；容器高 200px 的下方留空。",
        "pit": [
            "想用 align-items 控制行距：它只影响每行内部，多行分布要用 align-content。",
            "容器没有固定高度时 align-content 没有可用空间，看起来“没生效”。",
            "混用 margin 与 gap 做行距，间距会叠加成 20px。",
        ],
        "ex": [
            (
                "让两行在 200px 高度里垂直居中。",
                "改 align-content 的值。",
                "align-content: center;",
            )
        ],
    },
    {
        "t": "inline-flex 与基线对齐的芯片",
        "level": "intermediate",
        "obj": "用 inline-flex 让内联芯片内部居中，并与周围文字保持基线协调。",
        "pre": ["Flexbox 布局：主轴与交叉轴"],
        "con": ["inline-flex", "align-items", "vertical-align", "行内布局"],
        "explain": "`display: inline-flex` 同时具备“像文字一样排进行内”和“内部是 flex 容器”两种特性，是做徽标、芯片、带图标按钮的标准选择：外部用 `vertical-align: middle` 或基线对齐让它和正文对齐，内部用 `align-items: center` 把图标与文字在竖直方向居中。如果换成 `flex`，芯片会独占一行；换成 `inline-block`，内部又失去 flex 的居中能力，只能靠 line-height 硬凑。注意行内 flex 容器的基线由第一个 flex 项决定，图标过高时整行行高会被撑大。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>芯片</title>
<style>
  body { margin: 0; padding: 16px; font-size: 16px; }
  .chip {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 2px 8px; border-radius: 999px;
    background: #e8f0fe; vertical-align: middle;
  }
  .dot { width: 8px; height: 8px; border-radius: 50%; background: #1a73e8; }
</style>
</head>
<body>
  <p>状态：<span class="chip" id="chip"><span class="dot" id="dot"></span>已连接</span> 后续文字。</p>
</body>
</html>""",
        "out": "“已连接”芯片在行内显示，胶囊形浅蓝底，左侧 8px 蓝色圆点与文字垂直居中，芯片与前后文字在同一行。",
        "pit": [
            "用 display: flex 做芯片，芯片独占一行。",
            "只在芯片上设 line-height 而不设 align-items，图标偏高偏低。",
            "圆点尺寸过大时撑高行盒，正文行高被拉大。",
        ],
        "ex": [
            (
                "把芯片的间距从 6px 改成 10px。",
                "改 .chip 的 gap。",
                ".chip { gap: 10px; }",
            )
        ],
    },
    {
        "t": "subgrid：子网格继承父网格轨道",
        "level": "advanced",
        "obj": "用 subgrid 让卡片内部元素对齐到父网格的同一组列。",
        "pre": ["Grid 布局：行列与网格区域"],
        "con": ["subgrid", "grid-column", "轨道对齐", "嵌套网格"],
        "explain": "嵌套网格默认是独立的：子网格自己算列宽，于是并排卡片的标题和正文对不齐。`grid-template-columns: subgrid` 让子网格直接沿用父网格的轨道，父级的列宽因此贯穿到卡片内部。用法是父级定义轨道，卡片 `grid-column: 1 / -1` 横跨整行、再声明 `display: grid; grid-template-columns: subgrid`，子元素就分别落进父级的第 1、2、3 列。它解决的是“多卡片内部元素横向对齐”这类以前只能靠固定宽度或 JS 测量的问题。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>subgrid</title>
<style>
  body { margin: 0; }
  .outer { display: grid; grid-template-columns: 120px 1fr 80px; gap: 12px; width: 600px; }
  .card { display: grid; grid-column: 1 / -1; grid-template-columns: subgrid; background: #f1f3f4; }
  .card > span { padding: 4px; }
</style>
</head>
<body>
  <div class="outer" id="outer">
    <div class="card" id="c1"><span id="n1">名称</span><span id="d1">说明文字</span><span id="v1">1</span></div>
    <div class="card" id="c2"><span id="n2">更长的名称</span><span id="d2">说明</span><span id="v2">2</span></div>
  </div>
</body>
</html>""",
        "out": "两张卡片的名称列都宽 120px、数值列都宽 80px，说明列吃掉剩余宽度；两行卡片的元素左右边缘严格对齐。",
        "pit": [
            "卡片没有 `grid-column: 1 / -1`，subgrid 只覆盖一格，内部三列无处安放。",
            "父级用 `gap` 而子网格又加 margin，列宽对齐看起来偏了 12px。",
            "以为 subgrid 会继承行高：可以继承行轨道，但需要写 `grid-template-rows: subgrid`。",
        ],
        "ex": [
            (
                "让卡片也继承父级的行轨道。",
                "再加一条 grid-template-rows。",
                ".card { grid-template-rows: subgrid; }",
            )
        ],
    },
]

_B4 = [
    {
        "t": "repeat(auto-fill) 与 minmax 的自适应列",
        "level": "intermediate",
        "obj": "用 auto-fill 加 minmax 写出不写媒体查询也能自适应的卡片栅格。",
        "pre": ["CSS 网格模板区域与命名"],
        "con": ["auto-fill", "minmax()", "gap", "自适应列数"],
        "explain": "`repeat(auto-fill, minmax(150px, 1fr))` 的含义是：在容器宽度内尽量多放列，每列最小 150px，剩余空间按 1fr 均分。于是宽屏列多、窄屏列少，不需要任何媒体查询。`auto-fill` 会保留空轨道位置，`auto-fit` 则会把空轨道折叠，让现有项目变宽；单行项目用 auto-fit 更好看，需要稳定列数时用 auto-fill。列数由“可用宽度 + gap”与最小宽度共同决定，所以 gap 变大时列数可能突然少一列，这是调试时最常见的困惑点。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>自适应栅格</title>
<style>
  body { margin: 0; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 16px; }
  .grid div { background: #e8f0fe; padding: 12px; }
</style>
</head>
<body>
  <div class="grid" id="grid">
    <div>1</div><div>2</div><div>3</div><div>4</div>
    <div>5</div><div>6</div><div>7</div><div>8</div>
  </div>
</body>
</html>""",
        "out": "在 960px 宽下排成 5 列，每列 179.2px，列间距 16px；窗口变窄时列数自动减少，不需要媒体查询。",
        "pit": [
            "minmax 的最小值写成百分比，跟随容器变化时结果不可预测。",
            "同时设置固定 `grid-template-columns` 又写 auto-fill，后者被覆盖。",
            "把 gap 调大后忘了重新核对列数，最后一列被挤到下一行。",
        ],
        "ex": [
            (
                "把最小列宽改成 200px 并观察列数变化。",
                "只改 minmax 的第一个参数。",
                "repeat(auto-fill, minmax(200px, 1fr))",
            )
        ],
    },
    {
        "t": "grid-auto-rows 控制隐式行高",
        "level": "intermediate",
        "obj": "用 grid-auto-rows 统一隐式行的高度，避免内容多少导致行高参差。",
        "pre": ["Grid 布局：行列与网格区域"],
        "con": ["grid-auto-rows", "隐式行", "gap", "行轨道"],
        "explain": "只声明 `grid-template-columns` 时，多出来的项目会进入自动生成的“隐式行”，它们的高度默认由内容决定，于是某一行文字多就高、少就矮。`grid-auto-rows: 40px` 给所有隐式行统一高度，卡片栅格立刻整齐；也可以写成 `minmax(40px, auto)` 让行至少 40px、内容多时再长高。区分清楚：`grid-template-rows` 管显式声明的行，`grid-auto-rows` 管自动补出来的行，两者可以同时存在。想要内容垂直居中，再配合每项的 `align-items: center`。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>隐式行</title>
<style>
  body { margin: 0; }
  .g {
    display: grid; grid-template-columns: repeat(2, 1fr);
    grid-auto-rows: 40px; gap: 8px; width: 320px;
  }
  .g div { background: #e8f0fe; }
</style>
</head>
<body>
  <div class="g" id="g">
    <div id="r1">1</div><div id="r2">2</div>
    <div id="r3">3</div><div id="r4">4</div>
    <div id="r5">5</div>
  </div>
</body>
</html>""",
        "out": "三行的高度都是 40px，行间距 8px：第一行从 0 开始，第二行从 48px 开始，第三行从 96px 开始。",
        "pit": [
            "写了 grid-template-rows 却想控制自动补出的行，改错属性后完全无效。",
            "行高固定 40px 但内容更高时文字溢出，需要 minmax 或 overflow 处理。",
            "忘记 gap 也占高度，算总高时少算了行间距。",
        ],
        "ex": [
            (
                "让隐式行至少 60px 高，内容多时自动长高。",
                "把固定值换成 minmax。",
                "grid-auto-rows: minmax(60px, auto);",
            )
        ],
    },
    {
        "t": "place-items 与 place-content 的分工",
        "level": "intermediate",
        "obj": "分清 place-items（项目在格子里）与 place-content（轨道在容器里）两组对齐属性的作用对象。",
        "pre": ["Grid 布局：行列与网格区域"],
        "con": ["place-items", "place-content", "align-content", "justify-content"],
        "explain": "网格有两层对齐：`place-items` 是 `align-items` + `justify-items`，决定每个项目在自己格子内部怎么放；`place-content` 是 `align-content` + `justify-content`，决定整组轨道在容器剩余空间里怎么放。容器比轨道大时才会出现“剩余空间”，这时 place-content 才有可见效果；格子比项目大时 place-items 才有效。两者都写作“第一个值管块轴、第二个值管行内轴”，只写一个值时两个轴同时生效。搞混这两层是最常见的“设了没用”来源。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>两层对齐</title>
<style>
  body { margin: 0; }
  .grid {
    display: grid; width: 400px; height: 240px;
    grid-template-columns: 120px; grid-template-rows: 80px;
    place-items: center;
    place-content: end space-between;
    background: #f8f9fa;
  }
  .cell { background: #e8f0fe; padding: 4px; }
</style>
</head>
<body>
  <div class="grid" id="grid"><div class="cell" id="cell">格子</div></div>
</body>
</html>""",
        "out": "唯一的 120x80 轨道贴在容器底部，格子内容在轨道内水平垂直居中，因此格子中心位于 (60, 200)。",
        "pit": [
            "容器与轨道一样大时用 place-content，看不到任何变化。",
            "把 place-items 写成 place-content，项目不居中而整组轨道移动。",
            "只写一个值时以为只管水平轴，实际两个轴都被设置。",
        ],
        "ex": [
            (
                "让轨道回到容器左上角。",
                "把 place-content 改成 start。",
                "place-content: start;",
            )
        ],
    },
    {
        "t": "display: contents 展开盒树",
        "level": "advanced",
        "obj": "用 display: contents 去掉包装盒，让子元素直接参与父级布局。",
        "pre": ["Grid 布局：行列与网格区域"],
        "con": ["display: contents", "盒树", "网格项", "无障碍"],
        "explain": "`display: contents` 让元素本身不再生成盒子，它的子元素直接“上提”一层，成为父容器的布局项。典型用途是语义包装：`<div class=\"item\">` 只是为了分组，却破坏了 grid 的直接子元素关系，加上 contents 后语义还在、盒子消失。它也会把元素的背景、边框、内边距一并取消，所以在需要视觉外框时不能这么用。无障碍方面要谨慎：某些辅助技术会跳过 contents 元素，若它承载了 role 或可聚焦内容，可能丢失语义，因此只应用在纯包装层。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>contents</title>
<style>
  body { margin: 0; }
  .wrap { display: grid; grid-template-columns: 60px 1fr; gap: 10px; width: 300px; background: #e8f0fe; }
  .inner { display: contents; }
  .item { margin: 0; background: #34a853; color: #ffffff; }
  .sib { margin: 0; background: #f1f3f4; }
</style>
</head>
<body>
  <div class="wrap" id="wrap">
    <div class="inner" id="inner"><p class="item" id="item">内容</p></div>
  </div>
  <p class="sib" id="sib">普通段落</p>
</body>
</html>""",
        "out": "包装 div 不再产生盒子（尺寸为 0），段落直接成为网格第一列的项目，宽 60px 并贴着容器左边；下面的普通段落仍是块级元素。",
        "pit": [
            "在需要背景或边框的卡片上加 contents，装饰全部消失。",
            "包装层带 role 或 tabindex 时用 contents，可能破坏无障碍语义。",
            "以为 contents 会保留盒子的外边距，实际整个盒子都不生成。",
        ],
        "ex": [
            (
                "把段落改成横跨两列。",
                "给 .item 加 grid-column。",
                ".item { grid-column: 1 / -1; }",
            )
        ],
    },
    {
        "t": "contain: layout paint 隔离渲染",
        "level": "advanced",
        "obj": "用 contain 把子树隔离成独立的布局与绘制范围，防止内容溢出影响外部。",
        "pre": ["性能优化：will-change 与合成层"],
        "con": ["contain", "layout", "paint", "渲染隔离"],
        "explain": "`contain: layout paint` 告诉浏览器：这个元素的内部布局不会影响外部，内部绘制也不会画到盒子外面。于是浏览器可以跳过整棵子树的重排传播，长列表和复杂组件因此更快；同时 `paint` 会像 `overflow: hidden` 一样裁剪越界内容，但不会创建滚动容器、也不会改变 overflow 的计算值。注意它不改变元素自身尺寸：固定高度 60px 的盒子即使内部有 200px 高的内容，盒子仍是 60px，内容被裁掉。需要滚动时用 `overflow: auto` 而不是 contain。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>contain</title>
<style>
  body { margin: 0; }
  .box { contain: layout paint; width: 200px; height: 60px; background: #f1f3f4; }
  .big { height: 200px; background: #e8f0fe; }
</style>
</head>
<body>
  <div class="box" id="box"><div class="big" id="big">超出盒子的内容</div></div>
  <p id="after">下方文字不会被 200px 高的内容推下去。</p>
</body>
</html>""",
        "out": "盒子高度固定 60px，内部 200px 高的内容被裁掉，下方段落紧跟其后；盒子的 overflow 计算值仍是 visible。",
        "pit": [
            "用 contain: paint 当滚动容器，内容被裁掉且无法滚动。",
            "期望 contain 改变尺寸：它只隔离布局与绘制，不改变盒模型。",
            "在需要 sticky 子元素的容器上加 layout 包含，粘性定位可能失效。",
        ],
        "ex": [
            (
                "让盒子可以滚动查看被裁掉的内容。",
                "保留 contain，另加 overflow。",
                ".box { overflow: auto; }",
            )
        ],
    },
]

_B5 = [
    {
        "t": "min()、max() 与 clamp() 的组合运算",
        "level": "intermediate",
        "obj": "用三个比较函数把最小、最大与理想值写进一个长度，避免滥用媒体查询。",
        "pre": ["颜色与单位：px、rem、em、百分比"],
        "con": ["min()", "max()", "clamp()", "视口单位"],
        "explain": "`clamp(最小, 理想, 最大)` 等价于 `max(最小, min(理想, 最大))`，它把“不想要的值”直接截掉：视口很窄时取最小值，很宽时取最大值，中间段按理想值连续变化。`min()` 与 `max()` 可以单独用来做“不超过”“不小于”：`height: min(120px, 20vh)` 让面板在矮屏幕上自动变矮，`padding: max(8px, 2vw)` 保证最小呼吸空间。三个函数都参与正常长度计算，可以互相嵌套，比一串断点更好维护。注意里面混用百分比时，百分比相对的是包含块而不是视口。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>比较函数</title>
<style>
  body { margin: 0; }
  * { box-sizing: border-box; }
  .box { background: #e8f0fe; width: clamp(200px, 40vw, 320px); height: min(120px, 20vh); padding: max(8px, 2vw); }
  .small { background: #34a853; width: clamp(200px, 10vw, 320px); height: 20px; }
</style>
</head>
<body>
  <div class="box" id="box">宽高都随视口变化，但有上下限。</div>
  <div class="small" id="small">理想值太小时被最小值兜住。</div>
</body>
</html>""",
        "out": "在 960x720 下：大盒子宽 320px（命中上限）、高 120px、内边距 19.2px；小盒子宽 200px（命中下限）。",
        "pit": [
            "把 clamp 的三个参数顺序写反，浏览器直接丢弃整条声明。",
            "在 min/max 里混用百分比与视口单位，结果随包含块变化而不易预测。",
            "用 clamp 控制字号却没有设置根字号与行高，缩放时行距不跟随。",
        ],
        "ex": [
            (
                "把大盒子的最大宽改为 280px。",
                "改 clamp 第三个参数。",
                "width: clamp(200px, 40vw, 280px);",
            )
        ],
    },
    {
        "t": "fit-content、max-content 与 min-content 的取舍",
        "level": "advanced",
        "obj": "用三种内容尺寸关键字控制盒宽：按内容、按可用宽、还是按最长词。",
        "pre": ["CSS 网格内联尺寸：min-content 与 max-content"],
        "con": ["fit-content", "max-content", "min-content", "内容尺寸"],
        "explain": "`max-content` 表示“一行放下全部内容需要的宽度”，会直接被容器宽度限制并溢出；`min-content` 表示“尽量窄、但不拆开单词”需要的宽度，中文里通常是一个字；`fit-content` 取两者之间：内容短则按内容，内容长则封顶到可用宽度，相当于“自动收缩”。做标签、徽标、侧边栏自适应时，fit-content 最常用：不铺满整行，也不会把内容挤断。注意它们只对宽度等可自动计算的方向生效，父容器没有确定宽度时判断会变得模糊。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>内容尺寸</title>
<style>
  body { margin: 0; }
  .wrap { width: 120px; background: #f8f9fa; padding-bottom: 4px; }
  .box { background: #e8f0fe; margin: 4px 0; }
  .fit { width: fit-content; }
  .max { width: max-content; }
  .min { width: min-content; }
</style>
</head>
<body>
  <div class="wrap">
    <div class="box fit" id="fit">Offline IDE Preview</div>
    <div class="box max" id="max">Offline IDE Preview</div>
    <div class="box min" id="min">Offline IDE Preview</div>
  </div>
</body>
</html>""",
        "out": "fit-content 盒宽等于容器可用宽 120px；max-content 盒宽按整行文字撑开到 160px 以上并溢出容器；min-content 盒宽只相当于最长单词“Preview”的宽度。",
        "pit": [
            "把 fit-content 当成“居中”：它只控制宽度，居中还需要 margin: auto。",
            "在两个轴都自动的弹性上下文中用内容尺寸，结果随子项内容乱跳。",
            "用 min-content 处理不可断行的长网址，页面被撑破。",
        ],
        "ex": [
            (
                "让 min-content 盒子不再溢出，保持最窄。",
                "给文本加断词规则。",
                ".min { overflow-wrap: anywhere; }",
            )
        ],
    },
    {
        "t": "逻辑属性 inset-inline 与 inset-block",
        "level": "intermediate",
        "obj": "用逻辑方向代替 left/right 定位，让布局随书写方向自动翻转。",
        "pre": ["逻辑属性：margin-inline、padding-block"],
        "con": ["inset-inline", "inset-block", "逻辑方向", "绝对定位"],
        "explain": "`left`、`right` 是物理方向，换成阿拉伯文等从右到左的语言就会错位。`inset-inline-start` 表示“行内方向的起点”，在从左到右的页面里等于 `left`；`inset-block-end` 表示块方向的终点，等于 `bottom`。用逻辑属性写绝对定位，组件在 `direction: rtl` 或竖排文本下自动翻转，不需要另写一套规则。浏览器会把逻辑值解析成物理值，因此 `getComputedStyle` 读出来的仍是 left/top；写的时候统一用逻辑版更可维护。它与 `margin-inline`、`padding-block` 属同一体系。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>逻辑定位</title>
<style>
  body { margin: 0; }
  .stage { position: relative; width: 300px; height: 150px; background: #f8f9fa; }
  .badge { position: absolute; inset-inline-start: 20px; inset-block-start: 10px; background: #1a73e8; color: #ffffff; padding: 2px 6px; }
  .note { position: absolute; inset-inline-end: 0; inset-block-end: 0; background: #34a853; color: #ffffff; padding: 2px 6px; }
</style>
</head>
<body>
  <div class="stage" id="stage">
    <div class="badge" id="badge">角标</div>
    <div class="note" id="note">说明</div>
  </div>
</body>
</html>""",
        "out": "角标距离舞台左边 20px、上边 10px；说明块贴住舞台右下角。把页面改成 direction: rtl 后，角标自动跑到右边。",
        "pit": [
            "在同一元素上同时写 left 与 inset-inline-start，后者声明在前时会被覆盖。",
            "以为逻辑属性会自动改写 getComputedStyle 的属性名，实际读到的仍是物理值。",
            "父元素没有 position: relative，绝对定位元素跑去相对页面对位。",
        ],
        "ex": [
            (
                "把角标移到行内方向的终点。",
                "换成 inset-inline-end。",
                "inset-inline-start: auto; inset-inline-end: 20px;",
            )
        ],
    },
    {
        "t": "粘性页头、粘性侧栏与 scroll-margin-top",
        "level": "advanced",
        "obj": "用 position: sticky 实现滚动保持，并用 scroll-margin-top 修正锚点遮挡。",
        "pre": ["定位：static、relative、absolute、fixed"],
        "con": ["position: sticky", "scroll-margin-top", "锚点", "滚动偏移"],
        "explain": "`position: sticky` 是“滚动到阈值前像 relative、超过后像 fixed”：元素在它的滚动容器里移动，到达 top 偏移值后停住，但没有 fixed 的脱离文档流问题。页头和侧栏都用它。粘性元素的前提是滚动容器足够高、且没有被祖先的 `overflow: hidden` 截断。粘性页头会遮住跳转目标，此时给目标加 `scroll-margin-top: 页头高度`，浏览器滚动时会自动预留出这段距离；`scroll-padding-top` 是同一目的的容器侧写法。两者都不影响文档流。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>粘性</title>
<style>
  body { margin: 0; }
  .top { position: sticky; top: 0; height: 40px; background: #1a73e8; color: #ffffff; line-height: 40px; padding-left: 8px; }
  main { display: flex; gap: 12px; padding: 8px; }
  .side { position: sticky; top: 48px; width: 100px; height: 60px; background: #e8f0fe; }
  .sec { height: 400px; background: #f8f9fa; margin-bottom: 12px; flex: 1; }
  #sec2 { scroll-margin-top: 60px; }
</style>
</head>
<body>
  <header class="top" id="top">粘性页头</header>
  <p><a id="jump" href="#sec2">跳到第二节</a></p>
  <main>
    <nav class="side" id="side">粘性侧栏</nav>
    <div style="flex: 1">
      <section class="sec" id="sec1">第一节</section>
      <section class="sec" id="sec2">第二节</section>
      <section class="sec" id="sec3">第三节（为滚动留出空间）</section>
    </div>
  </main>
</body>
</html>""",
        "out": "向下滚动 300px 后页头仍贴在顶部、侧栏停在距顶部 48px 处；点击“跳到第二节”后第二节标题停在距顶部 60px，不被页头遮住。",
        "pit": [
            "父级设了 overflow: hidden 或 auto，粘性在父级高度内就“失效”。",
            "忘记给跳转目标加 scroll-margin-top，锚点内容被页头盖住。",
            "同时写 top: 0 与 bottom: 0，粘性元素在两端的收缩行为可能和预期相反。",
        ],
        "ex": [
            (
                "把页头高度改成 56px，并让锚点预留同样的高度。",
                "两处数值同步修改。",
                ".top { height: 56px; } #sec2 { scroll-margin-top: 56px; }",
            )
        ],
    },
    {
        "t": "dvh 与 svh：移动端视口高度单位",
        "level": "intermediate",
        "obj": "区分 vh、dvh、svh、lvh，用它们解决移动端地址栏伸缩导致的高度跳动。",
        "pre": ["响应式排版：clamp 与流体字号"],
        "con": ["dvh", "svh", "lvh", "视口单位"],
        "explain": "手机上浏览器地址栏会随滚动收起，`100vh` 在旧实现里按“最大视口”计算，于是首屏元素比实际可见区域更高，出现意外滚动。`dvh`（动态）、`svh`（最小）、`lvh`（最大）分别对应随地址栏变化的当前视口、地址栏展开时的最小视口、收起时的最大视口。做首屏 hero 常用 `min-height: 100svh` 保证内容不被裁，做全屏覆盖层则用 `100dvh` 跟随变化。它们都是长度单位，可以直接参与 `calc()` 与 `clamp()`，不需要 JS 测量。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>视口单位</title>
<style>
  body { margin: 0; }
  .hero { height: 50dvh; background: #1a73e8; color: #ffffff; }
  .half { height: 50svh; background: #e8f0fe; }
</style>
</head>
<body>
  <div class="hero" id="hero">50dvh 首屏</div>
  <div class="half" id="half">50svh 区块</div>
</body>
</html>""",
        "out": "在 720px 高的视口下，两个区块都是 360px 高（各占一半视口）；在手机上地址栏伸缩时，dvh 跟随变化而 svh 保持不变。",
        "pit": [
            "用 `100vh` 做首屏，手机上底部内容被地址栏遮住。",
            "在父容器里有 padding 时仍然用 100vh 取满，结果总高超过视口。",
            "在 iframe 或嵌入式预览里使用 dvh，量到的是 iframe 视口而不是整页。",
        ],
        "ex": [
            (
                "让 hero 始终占满整个动态视口。",
                "改高度为 100dvh。",
                ".hero { height: 100dvh; }",
            )
        ],
    },
]

_B6 = [
    {
        "t": "cqi 与 cqw：容器查询单位",
        "level": "advanced",
        "obj": "用容器单位让字号随容器宽度缩放，而不是随整个视口缩放。",
        "pre": ["容器查询：container queries"],
        "con": ["container-type", "cqi", "cqw", "容器单位"],
        "explain": "`vw` 参考视口宽度，组件放进侧栏或卡片后字号就不再合适；`cqi`/`cqw` 参考最近的查询容器宽度，于是同一个组件在宽卡里字大、在窄卡里字小，真正随自己的舞台变化。用法是先给外层声明 `container-type: inline-size`，内部再用 `5cqi`。`cqi` 是行向 `cqw` 的 1%，尺寸方向还有 `cqb`/`cqh`。它比媒体查询更适合组件库：改框架布局时不需要重算断点。注意容器必须显式声明 container-type，否则 cqi 会向上找不到容器而退化为视口的一个小默认值。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>容器单位</title>
<style>
  body { margin: 0; padding: 8px; }
  .card { container-type: inline-size; background: #e8f0fe; margin-bottom: 8px; }
  .wide { width: 400px; }
  .narrow { width: 200px; }
  .title { font-size: 5cqi; margin: 0; }
  .body { font-size: 2.5cqw; margin: 0; }
</style>
</head>
<body>
  <div class="card wide" id="wide"><h2 class="title" id="tw">宽卡片</h2><p class="body" id="bw">正文</p></div>
  <div class="card narrow" id="narrow"><h2 class="title" id="tn">窄卡片</h2><p class="body" id="bn">正文</p></div>
</body>
</html>""",
        "out": "宽卡片容器 400px：标题字号 20px、正文 10px；窄卡片容器 200px：标题 10px、正文 5px。两卡位于同一页面，证明字号跟着容器而不是视口走。",
        "pit": [
            "忘记给父级声明 container-type，cqi 找不到容器，尺寸不按预期。",
            "把 container-type 写在元素自身又用它算自身字号，形成循环而失效。",
            "在容器内部再用 cqw 设置容器自己的宽度，同样会陷入循环。",
        ],
        "ex": [
            (
                "把标题字号改为容器宽度的 8%。",
                "改 cqi 系数。",
                ".title { font-size: 8cqi; }",
            )
        ],
    },
    {
        "t": "ch 与 cap 排版单位控制行宽与字高",
        "level": "intermediate",
        "obj": "用字符相关单位限制行宽和字号，让排版随字体自然伸缩。",
        "pre": ["CSS 响应式字号与行宽"],
        "con": ["ch", "cap", "行宽", "字符单位"],
        "explain": "`ch` 是当前字体中“0”字符的宽度，等宽字体下它等于一个字符宽，因此 `max-width: 60ch` 能稳定得到“每行约六十个字符”的可读行宽，换字体时也不需要重调像素。`cap` 是大写字母高度，用 `font-size: 3cap` 可以让装饰性标题与正文大写字母高度成比例。两者都依赖当前 `font-size` 与字体本身，所以在字体回退时数值会变化。它们解决的是“文本量与容器无关”的排版问题，是布局像素单位之外的另一种思路。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>字符单位</title>
<style>
  body { margin: 0; }
  .measure { font: 16px/1.6 monospace; max-width: 60ch; background: #f8f9fa; }
  .cap { font-size: 3cap; margin: 0; background: #e8f0fe; }
</style>
</head>
<body>
  <article class="measure" id="measure">这段正文每行最多60个等宽字符，读起来不会太长。</article>
  <h2 class="cap" id="cap">大写高度驱动的标题</h2>
</body>
</html>""",
        "out": "正文块最大宽度等于 60 个等宽字符的宽度（本例约 576px）；标题字号按 3 倍大写高度计算，与字体本身成比例。",
        "pit": [
            "在比例字体里用 ch 当像素用，不同字体的 ch 宽度差异很大。",
            "只写 max-width 不居中，长行挤在左边依然难读。",
            "字体回退到缺少 metrics 的系统字体时，cap 计算结果会跳变。",
        ],
        "ex": [
            (
                "把行宽收紧到 45 个字符。",
                "改 max-width。",
                ".measure { max-width: 45ch; }",
            )
        ],
    },
    {
        "t": "overflow: clip 与 overflow-clip-margin",
        "level": "advanced",
        "obj": "用 clip 裁剪内容而不创建滚动容器，并用 overflow-clip-margin 控制允许的出血量。",
        "pre": ["CSS 溢出处理：overflow"],
        "con": ["overflow: clip", "overflow-clip-margin", "滚动容器", "裁剪"],
        "explain": "`overflow: hidden` 会创建滚动容器：内容被裁掉，但脚本仍能通过 `scrollLeft`/`scrollTop` 滚动它；`overflow: clip` 不创建滚动容器，越界内容被真正丢弃，脚本给它赋值 `scrollLeft` 之后仍然是 0，也不会参与滚动锚定，因此开销更小。`overflow-clip-margin` 是 clip 专属的“出血量”：设为 10px 时，盒子外 10px 范围内的内容仍会绘制，做阴影、徽标越界时很有用。需要用户自己滚动时用 auto，只是视觉截断时用 clip，两者语义不同。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>clip</title>
<style>
  body { margin: 0; }
  .clipbox { width: 120px; height: 60px; overflow: clip; overflow-clip-margin: 10px; background: #f1f3f4; }
  .hidden { width: 120px; height: 60px; overflow: hidden; background: #f1f3f4; margin-top: 8px; }
  .blob { width: 160px; height: 40px; margin-top: 10px; background: #1a73e8; }
</style>
</head>
<body>
  <div class="clipbox" id="clipbox"><div class="blob" id="blob1"></div></div>
  <div class="hidden" id="hidden"><div class="blob" id="blob2"></div></div>
</body>
</html>""",
        "out": "两个盒子都是 120x60，内部蓝块宽 160px 被裁掉；区别是脚本给 clip 盒设 scrollLeft 后仍为 0（它不是滚动容器），而 hidden 盒可以被滚到 40px。",
        "pit": [
            "用 clip 之后又想用脚本滚动内容，`scrollLeft` 永远是 0。",
            "把 overflow-clip-margin 写在 hidden 元素上，属性不生效。",
            "以为 clip 会像 hidden 一样保留可访问的溢出区域，结果内容真的不可达。",
        ],
        "ex": [
            (
                "把出血量改为 20px。",
                "改 overflow-clip-margin。",
                ".clipbox { overflow-clip-margin: 20px; }",
            )
        ],
    },
    {
        "t": "oklch 感知均匀色阶",
        "level": "advanced",
        "obj": "用 oklch 的亮度、彩度、色相生成视觉上等距的色阶。",
        "pre": ["CSS 主题色生成器（HSL 派生）"],
        "con": ["oklch()", "感知均匀", "色阶", "彩度"],
        "explain": "HSL 里“亮度加 10%”在人眼中并不等距，蓝色 50% 和黄色 50% 的观感差别很大；`oklch()` 基于感知均匀的色彩空间，把颜色拆成 L（亮度 0-1）、C（彩度）、h（色相角度），只改 L 就能得到一条看起来均匀的色阶，适合作设计系统的调色板。它还能表达 sRGB 之外更鲜艳的颜色，超出色域时浏览器会自动映射。写法是 `oklch(0.62 0.18 255)`，与 `color-mix()`、`light-dark()` 组合使用能覆盖现在主流应用的主题需求。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>oklch</title>
<style>
  body { margin: 0; display: flex; }
  .sw { width: 60px; height: 60px; }
  .s1 { background: oklch(0.9 0.05 255); }
  .s2 { background: oklch(0.75 0.11 255); }
  .s3 { background: oklch(0.6 0.17 255); }
  .s4 { background: oklch(0.45 0.21 255); }
</style>
</head>
<body>
  <div class="sw s1" id="s1"></div>
  <div class="sw s2" id="s2"></div>
  <div class="sw s3" id="s3"></div>
  <div class="sw s4" id="s4"></div>
</body>
</html>""",
        "out": "四个色块从很浅的蓝逐级变深，亮度差看起来均匀；每个色块宽高都是 60px。",
        "pit": [
            "把 L 写成百分比（oklch(90% 0.05 255)），部分写法会失效，应使用 0-1 的小数。",
            "彩度设得过高超出 sRGB 色域，屏幕颜色会被自动压低，与其他色块不再匹配。",
            "在旧内核上不支持 oklch，需要提供十六进制回退色。",
        ],
        "ex": [
            (
                "再加一档更亮的颜色。",
                "提高 L 到 0.97。",
                ".s5 { background: oklch(0.97 0.03 255); }",
            )
        ],
    },
    {
        "t": "color-mix() 就地混色",
        "level": "intermediate",
        "obj": "用 color-mix() 在样式表里混出中间色，避免手算十六进制。",
        "pre": ["变量与主题：CSS 自定义属性"],
        "con": ["color-mix()", "插值空间", "主题派生", "透明混合"],
        "explain": "`color-mix(in oklab, #1a73e8 50%, #ffffff)` 把两个颜色按比例混合。插值空间很重要：`in srgb` 简单但中间色发灰，`in oklab` 更接近人眼期望，`in oklch` 还能保持色相与彩度。百分比可以都不写（各 50%），也可以只写一个（另一个自动补足），还可以写成 `transparent` 做半透明色。它让主题只维护一个主色，悬停、禁用、边框、背景都由主色派生，改主题时不用再手动计算一堆十六进制值。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>混色</title>
<style>
  body { margin: 0; }
  .base { background: #1a73e8; }
  .m50 { background: color-mix(in oklab, #1a73e8 50%, #ffffff); }
  .m25 { background: color-mix(in oklab, #1a73e8 25%, #ffffff); }
  .sw { width: 80px; height: 40px; }
</style>
</head>
<body>
  <div class="sw base" id="base"></div>
  <div class="sw m50" id="m50"></div>
  <div class="sw m25" id="m25"></div>
</body>
</html>""",
        "out": "三块颜色从深蓝到浅蓝依次变浅：主色、与白色各半混合、只留四分之一主色；每个色块都是 80x40。",
        "pit": [
            "忘记写插值空间（in oklab）的写法细节，浏览器直接丢弃整个颜色。",
            "两个百分比加起来不等于 100%，缺失的一方自动补足，容易与预期不符。",
            "在 srgb 里混深色与浅色，中间色容易发脏。",
        ],
        "ex": [
            (
                "把中间一块改成主色与黑色对半混合。",
                "把白色换成黑色。",
                ".m50 { background: color-mix(in oklab, #1a73e8 50%, #000000); }",
            )
        ],
    },
]

_B7 = [
    {
        "t": "light-dark() 与 color-scheme 双主题",
        "level": "advanced",
        "obj": "用 color-scheme 声明主题能力，再用 light-dark() 在一个属性里给出明暗两套值。",
        "pre": ["暗色模式：prefers-color-scheme"],
        "con": ["light-dark()", "color-scheme", "双主题", "表单控件主题"],
        "explain": "旧写法要写两遍：一套默认值加一个 `@media (prefers-color-scheme: dark)` 块。`light-dark(亮值, 暗值)` 把两个值写在一处，由 `color-scheme` 属性决定取哪个：声明 `color-scheme: light dark` 表示“两套都支持，跟随系统”。它还能让浏览器自己的控件（滚动条、输入框默认色、拼写检查）跟着变，这是只改背景色做不到的。适合设计变量一一对应的主题：根上定色，组件里全部用 light-dark 成对写。注意它只能用于颜色属性，且两个参数都必须是颜色值。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>light-dark</title>
<style>
  :root { color-scheme: light dark; }
  body { margin: 0; background: light-dark(#ffffff, #202124); color: light-dark(#202124, #ffffff); }
  .card { background: light-dark(#f1f3f4, #303134); padding: 16px; }
</style>
</head>
<body>
  <div class="card" id="card">主题跟随系统设置。</div>
</body>
</html>""",
        "out": "亮色主题下：页面白底深灰字，卡片浅灰底；系统切到暗色后：页面深灰底白字，卡片 #303134。",
        "pit": [
            "只给组件写 light-dark 而根上没写 color-scheme，两个值都按浅色处理。",
            "把 color-scheme 写在 body 上，页面默认背景与滚动条仍可能不跟随。",
            "在元素上又写死一个 background 颜色，暗色下 light-dark 的结果被覆盖。",
        ],
        "ex": [
            (
                "把页面固定为暗色主题。",
                "改根元素的 color-scheme。",
                ":root { color-scheme: dark; }",
            )
        ],
    },
    {
        "t": "相对颜色 rgb(from …) 的通道运算",
        "level": "advanced",
        "obj": "用相对颜色语法从一个基准色派生色值，不手算十六进制。",
        "pre": ["CSS 主题色生成器（HSL 派生）"],
        "con": ["相对颜色", "rgb(from …)", "calc 通道", "透明度"],
        "explain": "`rgb(from #3366cc r g b / 50%)` 先取出基准色的通道，再用 `r`、`g`、`b`、`alpha` 这些变量重新组装颜色，通道里可以嵌 `calc()`。于是“同一个主色提亮 60、半透明、降饱和”这类派生都能写成一行，改主色时全部跟随。它比 `color-mix()` 更精细：混合是两色插值，相对颜色是直接改写通道。注意 `from` 后的颜色可以是任意颜色值，但不能省略 `from`；不支持时整条声明被丢弃，因此需要保留一个回退色。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>相对颜色</title>
<style>
  body { margin: 0; }
  .base { background: #3366cc; }
  .dim { background: rgb(from #3366cc r g b / 40%); }
  .lighter { background: rgb(from #3366cc calc(r + 60) calc(g + 60) calc(b + 60)); }
  .sw { width: 80px; height: 40px; }
</style>
</head>
<body>
  <div class="sw base" id="base"></div>
  <div class="sw dim" id="dim"></div>
  <div class="sw lighter" id="lighter"></div>
</body>
</html>""",
        "out": "第一块是基准蓝 #3366cc，第二块是同一颜色 40% 不透明，第三块把三个通道各加 60 得到更亮的蓝。",
        "pit": [
            "通道名写错（写成 red/green）导致整条声明无效，颜色回退为透明。",
            "在 calc 里把 r 与百分数直接相加，单位不匹配被丢弃。",
            "忘了给不支持的旧引擎提供回退色，颜色直接消失。",
        ],
        "ex": [
            (
                "让第三块降亮度而不是提亮。",
                "把 calc 里的加号改成减号。",
                "rgb(from #3366cc calc(r - 60) calc(g - 60) calc(b - 60))",
            )
        ],
    },
    {
        "t": "repeating-linear-gradient 条纹背景",
        "level": "intermediate",
        "obj": "用重复线性渐变画出斜条纹，并理解色标区间的含义。",
        "pre": ["背景：颜色、渐变与图片"],
        "con": ["repeating-linear-gradient", "色标区间", "斜纹", "无图背景"],
        "explain": "`repeating-linear-gradient(45deg, A 0 10px, B 10px 20px)` 的意思是：从 0 到 10px 是 A，10 到 20px 是 B，然后每 20px 重复一次，于是一整片斜条纹。关键在于每个色标要写“起点 终点”两个位置；只写一个位置时浏览器会平均分配，条纹宽度就不受控。条纹周期等于最后一个色标的位置，想要更密就把周期改小。它不需要任何图片资源，因此完全离线：进度条、警示带、斑马纹表格都可以这样画。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>条纹</title>
<style>
  body { margin: 0; }
  .stripe { width: 200px; height: 40px; background: repeating-linear-gradient(45deg, #1a73e8 0 10px, #ffffff 10px 20px); }
  .zebra { width: 200px; height: 40px; margin-top: 8px; background: repeating-linear-gradient(90deg, #f1f3f4 0 20px, #e8f0fe 20px 40px); }
</style>
</head>
<body>
  <div class="stripe" id="stripe"></div>
  <div class="zebra" id="zebra"></div>
</body>
</html>""",
        "out": "第一块是斜向蓝白条纹（每 20px 一个周期），第二块是竖向蓝灰方块交替；两块都不需要图片文件。",
        "pit": [
            "色标只写一个位置，条纹宽度随渐变自动分配而失去控制。",
            "用普通 linear-gradient 代替 repeating 版，条纹只出现一次。",
            "在度数与像素之间混算周期，换角度后条纹密度意外变化。",
        ],
        "ex": [
            (
                "把斜条纹周期缩到一半。",
                "改两个区间的终点。",
                "repeating-linear-gradient(45deg, #1a73e8 0 5px, #ffffff 5px 10px)",
            )
        ],
    },
    {
        "t": "mask-image 渐隐遮罩",
        "level": "advanced",
        "obj": "用渐变遮罩让元素在某个方向逐渐透明，而不是整体透明度变化。",
        "pre": ["渐变进阶：径向与多重背景"],
        "con": ["mask-image", "mask-size", "mask-repeat", "渐隐"],
        "explain": "`mask-image` 用一张图的亮度当作遮罩：白色区域完全可见，透明区域完全隐藏，中间就是部分透明。因此 `linear-gradient(to right, #000, transparent)` 会让元素右侧逐渐消失，常用于文本溢出提示、图片边缘消亡、滚动容器两端渐隐。配套要写 `mask-size: 100% 100%` 与 `mask-repeat: no-repeat`，否则默认的重复平铺与尺寸会让渐隐效果看起来不对。它作用于整个元素（包括背景与子元素），与 `opacity` 不同——后者是整体均匀透明。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>遮罩</title>
<style>
  body { margin: 0; padding: 8px; }
  .fade {
    width: 200px; height: 40px; background: #1a73e8;
    mask-image: linear-gradient(to right, #000000, transparent);
    mask-size: 100% 100%; mask-repeat: no-repeat;
  }
</style>
</head>
<body>
  <div class="fade" id="fade">右侧渐隐的蓝条</div>
</body>
</html>""",
        "out": "蓝条宽度 200px、高 40px，左边完全不透明、从左到右逐渐变成透明，右侧边界看不到硬边。",
        "pit": [
            "只写 mask-image 不写 mask-size，默认平铺后出现一条条块。",
            "以为 mask 只影响背景：它同样遮住文字与子元素。",
            "在需要打印的元素上用遮罩，打印稿里遮罩可能不生效。",
        ],
        "ex": [
            (
                "改成从下往上渐隐。",
                "把方向改成 to top。",
                "mask-image: linear-gradient(to top, #000000, transparent);",
            )
        ],
    },
    {
        "t": "mask-composite 多层遮罩合成",
        "level": "advanced",
        "obj": "用 mask-composite 控制多层遮罩是取交集还是取差集。",
        "pre": ["mask-image 渐隐遮罩"],
        "con": ["mask-composite", "多层遮罩", "intersect", "exclude"],
        "explain": "同时声明多层 `mask-image` 时，浏览器默认把上层盖在下层上（add），所以两块不透明遮罩合起来几乎是全开。`mask-composite` 改变合成方式：`intersect` 取交集（只有两层都亮的地方才可见，适合“只显示某个区域”），`exclude` 取差集（从下层减去上层，适合做环形、镂空）。配合 `mask-repeat: no-repeat` 与 `mask-size: 100% 100%` 使用，不然多层遮罩各自的平铺会互相干扰。理解它就能用纯 CSS 画出环形进度、图形镂空等效果。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>遮罩合成</title>
<style>
  body { margin: 0; padding: 8px; }
  .blend {
    width: 120px; height: 120px; background: #34a853;
    mask-image: linear-gradient(#000000 0 100%), radial-gradient(circle, #000000 0 60%, transparent 60%);
    mask-composite: intersect;
    mask-size: 100% 100%; mask-repeat: no-repeat;
  }
</style>
</head>
<body>
  <div class="blend" id="blend"></div>
</body>
</html>""",
        "out": "绿色方块只有中心圆形区域可见，四角被裁掉：两层遮罩取交集的结果。改成 exclude 后会变成中心镂空、四角保留。",
        "pit": [
            "只写 mask-composite 但只有一层 mask-image，合成无从谈起。",
            "忘了给多层遮罩写 mask-repeat: no-repeat，渐变被平铺后交集区域错位。",
            "把 intersect 期望成“相加”，可见区域比预期小很多。",
        ],
        "ex": [
            (
                "改成中心镂空、四角保留。",
                "把合成方式换成差集。",
                "mask-composite: exclude;",
            )
        ],
    },
]

_B8 = [
    {
        "t": "background-blend-mode 双色叠加",
        "level": "intermediate",
        "obj": "用 background-blend-mode 在两层背景之间混合，不增加额外元素。",
        "pre": ["CSS 多背景叠加"],
        "con": ["background-blend-mode", "多层背景", "混合模式", "背景混合"],
        "explain": "背景可以叠多层，默认是“上层盖住下层”；`background-blend-mode: multiply` 改成混合计算，于是主色加一层黑白渐变就能得到从浅到深的同色系效果，用不着额外元素或伪元素。它只混合同一个元素内的背景层，不影响页面其他内容；要跨元素混合用 `mix-blend-mode`。注意混合模式数组按层对应，层数不匹配时会循环取值，容易出现“第一层模式对了、第二层没变”的现象。性能上混合比普通绘制贵，大块背景上慎用。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>背景混合</title>
<style>
  body { margin: 0; }
  .blend {
    width: 200px; height: 80px; background-color: #ffffff;
    background-image: linear-gradient(#1a73e8, #1a73e8), linear-gradient(90deg, #ffffff, #000000);
    background-blend-mode: multiply;
  }
</style>
</head>
<body>
  <div class="blend" id="blend"></div>
</body>
</html>""",
        "out": "一块从左到右由亮变暗的蓝色渐变：两层背景相乘后左侧接近原蓝、右侧接近黑色。",
        "pit": [
            "把 mix-blend-mode 当成背景混合，结果整个元素与页面内容混合。",
            "层数与模式个数不匹配，后面几层默默使用默认模式。",
            "在大面积背景上堆多层混合，滚动时可能丢帧。",
        ],
        "ex": [
            (
                "把混合模式改成滤色（screen）。",
                "只改 background-blend-mode。",
                "background-blend-mode: screen;",
            )
        ],
    },
    {
        "t": "border-image 渐变边框",
        "level": "advanced",
        "obj": "用 border-image 把渐变画成边框，并知道它会让圆角失效。",
        "pre": ["CSS 阴影与层次感"],
        "con": ["border-image-source", "border-image-slice", "渐变边框", "圆角限制"],
        "explain": "`border-image` 把一张图（可以是渐变）切成九块，分别贴到边框的四条边与四个角，`slice` 控制切分位置，`1` 表示按边框宽度的比例切。它能让边框呈现渐变、纹理，而普通 `border-color` 只能单色。代价是：一旦用 border-image，`border-radius` 就不再生效，圆角会被切成直角；同时边框颜色变成透明，所有视觉都来自图片。需要圆角渐变边框时，改用双层背景或 padding 加背景裁剪的写法。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>渐变边框</title>
<style>
  body { margin: 0; padding: 8px; }
  .frame {
    border: 8px solid transparent;
    border-image: linear-gradient(45deg, #1a73e8, #34a853) 1;
    padding: 8px; width: 160px;
  }
</style>
</head>
<body>
  <div class="frame" id="frame">渐变边框不会产生圆角。</div>
</body>
</html>""",
        "out": "卡片四周是一条从蓝到绿的斜向渐变边框，宽 8px，四个角保持直角，即使写 border-radius 也不会变圆。",
        "pit": [
            "以为 border-radius 仍会裁出圆角：border-image 会覆盖圆角绘制。",
            "slice 写成 0，整张渐变被拉伸到边框里，看不出九宫格效果。",
            "只写 border-image 而 border-style 为 none，边框不绘制。",
        ],
        "ex": [
            (
                "把渐变方向改成水平。",
                "改 linear-gradient 的角度。",
                "border-image: linear-gradient(90deg, #1a73e8, #34a853) 1;",
            )
        ],
    },
    {
        "t": "text-emphasis 重点符号",
        "level": "intermediate",
        "obj": "用 text-emphasis 给文字加重点符号，替代下划线做强调。",
        "pre": ["CSS 文本装饰与链接样式"],
        "con": ["text-emphasis-style", "text-emphasis-color", "text-emphasis-position", "强调"],
        "explain": "在中文与日文排版里，强调常用点或小圆而不是下划线，`text-emphasis-style: dot` 就是为此准备的：它会在每个字旁边加一个点，颜色由 `text-emphasis-color` 控制，位置由 `text-emphasis-position` 调整（横排默认在字的上方，写成 `over right` 时行内偏移方向在浏览器里可能被简化为 `over`）。与下划线相比，它不会与文字基线重叠，也不改变布局尺寸。它只对字符生效，标点与其他非字符内容不加点。浏览器支持已很完整，是纯 CSS 的排版细节提升。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>重点符号</title>
<style>
  body { margin: 0; padding: 8px; }
  p { font-size: 20px; line-height: 1.8; margin: 0; }
  .em { text-emphasis-style: dot; text-emphasis-color: #1a73e8; text-emphasis-position: over right; }
</style>
</head>
<body>
  <p>普通句子，<span class="em" id="em">强调部分</span>后面继续。</p>
</body>
</html>""",
        "out": "“强调部分”四个字上方各有一个蓝点，位置在字符上方，行高不受影响，其他文字没有点。",
        "pit": [
            "把 text-emphasis 与 text-decoration 混用，两者同时出现显得脏乱。",
            "在行高很小的段落上加重点符号，点会与上一行文字重叠。",
            "以为重点符号会随字体颜色变化：它需要 text-emphasis-color 单独设置。",
        ],
        "ex": [
            (
                "把重点符号改成实心圆。",
                "改 text-emphasis-style。",
                ".em { text-emphasis-style: filled circle; }",
            )
        ],
    },
    {
        "t": "-webkit-text-stroke 描边字",
        "level": "intermediate",
        "obj": "给文字加描边，做出空心字或描边叠加效果。",
        "pre": ["字体与文本排版"],
        "con": ["-webkit-text-stroke", "描边", "空心字", "绘制顺序"],
        "explain": "`-webkit-text-stroke-width` 与 `-webkit-text-stroke-color` 给字形加一圈描边，虽然带厂商前缀但在主流内核都已支持。文字颜色仍然决定填充，所以把 `color` 设为 `transparent` 就得到空心描边字，与背景叠加可做海报式标题。绘制顺序是“先描边后填充”，所以描边会有一半被填充盖住；这意味着描边宽度实际可见部分只有一半，想要 2px 可见效果要写 4px。它不能单独改变描边与填充的层级，也不影响布局尺寸。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>描边字</title>
<style>
  body { margin: 0; padding: 8px; background: #ffffff; }
  .stroke { font-size: 32px; font-weight: 700; -webkit-text-stroke: 2px #1a73e8; color: #ffffff; }
  .hollow { font-size: 32px; font-weight: 700; -webkit-text-stroke: 2px #34a853; color: transparent; }
</style>
</head>
<body>
  <p class="stroke" id="stroke">描边标题</p>
  <p class="hollow" id="hollow">空心标题</p>
</body>
</html>""",
        "out": "第一行是白字配 2px 蓝描边，第二行没有填充只有 2px 绿描边（空心字）；字号都是 32px。",
        "pit": [
            "把可见描边宽度直接当声明值：实际可见只有一半。",
            "只写 color: transparent 而没写描边，文字完全不可见。",
            "在细体字上用过大描边，字形糊在一起难以辨认。",
        ],
        "ex": [
            (
                "让空心标题的描边变成 4px。",
                "改 .hollow 的 -webkit-text-stroke。",
                ".hollow { -webkit-text-stroke: 4px #34a853; }",
            )
        ],
    },
]

_B9 = [
    {
        "t": "text-wrap: balance 平衡折行标题",
        "level": "intermediate",
        "obj": "用 text-wrap: balance 让标题在折行时行宽更均匀，避免最后一行只剩一个字。",
        "pre": ["字体与文本排版"],
        "con": ["text-wrap", "balance", "pretty", "折行控制"],
        "explain": "浏览器默认的折行只保证“尽量塞满”，于是三段式标题常常第一行很满、最后一行只剩一两个字。`text-wrap: balance` 让浏览器在所有可行断点里挑一组行宽最接近的方案，标题看起来更稳；`text-wrap: pretty` 则优先避免孤字与孤行，适合正文段落。它们只对块级文本容器生效，且 balance 有行数上限（浏览器会为性能限制在少量行内）。用法上通常只给标题加 balance、给正文加 pretty，不要给长列表或超大容器加，否则会带来额外的排版计算成本。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>平衡折行</title>
<style>
  body { margin: 0; padding: 8px; }
  h2 { width: 200px; font-size: 20px; line-height: 1.4; margin: 0 0 12px; border: 1px solid #dadce0; }
  .balance { text-wrap: balance; }
  .wrap { text-wrap: wrap; }
</style>
</head>
<body>
  <h2 class="wrap" id="wrap">离线 IDE 帮助里常见的一行很长很长的标题文本</h2>
  <h2 class="balance" id="balance">离线 IDE 帮助里常见的一行很长很长的标题文本</h2>
</body>
</html>""",
        "out": "两个标题都被限制在 200px 宽；上面那个（wrap）行宽不均，下面那个（balance）两行长度更接近。",
        "pit": [
            "给超长正文加 balance，浏览器会忽略或只处理前几行。",
            "以为 balance 能改变容器宽度：它只调整断点位置。",
            "在窄容器上同时使用 balance 与 `word-break: anywhere`，断点过碎反而更差。",
        ],
        "ex": [
            (
                "让第二个标题优先避免孤字。",
                "把 balance 换成 pretty。",
                ".balance { text-wrap: pretty; }",
            )
        ],
    },
    {
        "t": "hyphens 与 overflow-wrap 的长词处理",
        "level": "intermediate",
        "obj": "用 hyphens 与 overflow-wrap 处理超长单词，避免横向溢出。",
        "pre": ["文本溢出与截断：ellipsis"],
        "con": ["hyphens", "overflow-wrap", "word-break", "断行策略"],
        "explain": "遇到长单词或长网址时，默认只在空格处断行，窄容器就会被撑破。`overflow-wrap: break-word` 允许在必要时把单词拆开；`overflow-wrap: anywhere` 更进一步，断点也参与最小内容宽度计算，因此弹性布局里也能真正收缩。`hyphens: auto` 走另一条路：按语言词典在正确位置插连字符，前提是元素（或其祖先）有 `lang` 属性且浏览器带该语言词典。两者可以叠加：先尝试按词典断词，实在不行再硬断。`word-break: break-all` 断得更粗暴，适合纯技术字符串。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>长词</title>
<style>
  body { margin: 0; padding: 8px; }
  .box { width: 120px; border: 1px solid #dadce0; margin-bottom: 12px; }
  .anywhere { overflow-wrap: anywhere; }
  .hyphen { hyphens: auto; }
</style>
</head>
<body>
  <div class="box" id="broken"><span class="anywhere">supercalifragilisticexpialidocious</span></div>
  <div class="box" id="hyphenated" lang="en"><span class="hyphen">supercalifragilisticexpialidocious</span></div>
</body>
</html>""",
        "out": "两个 120px 宽的盒子都没有被长单词撑破；第一个靠 anywhere 硬断，第二个在 lang=en 下尝试用连字符断词。",
        "pit": [
            "只写 `word-wrap: break-word`：老名字仍可用，但语义不如 overflow-wrap 清楚。",
            "忘了给元素加 `lang`，hyphens: auto 找不到词典而完全不生效。",
            "在弹性容器里用 break-word 之外的最小宽度假设，长词仍会撑开父级。",
        ],
        "ex": [
            (
                "让第一个盒子改用粗暴断行。",
                "换成 word-break。",
                ".anywhere { word-break: break-all; }",
            )
        ],
    },
    {
        "t": "font-variant-numeric 等宽数字对齐",
        "level": "beginner",
        "obj": "用 tabular-nums 让数字等宽，使表格与统计数字纵向对齐。",
        "pre": ["字体与文本排版"],
        "con": ["font-variant-numeric", "tabular-nums", "等宽数字", "数据排版"],
        "explain": "很多比例字体里的数字宽度不一（“1”比“8”窄），于是价格列表、计时器、表格数字会左右参差。`font-variant-numeric: tabular-nums` 请求等宽数字，每个数字占同样宽度，纵向就能对齐；相反 `proportional-nums` 强调紧凑。它比换等宽字体更轻：只改数字，字母仍是原字体，视觉不突兀。注意它依赖字体本身是否提供等宽数字表，缺表时浏览器只能回退；做关键数据展示时可以配合 `font-variant-numeric: tabular-nums slashed-zero` 区分 0 与 O。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>等宽数字</title>
<style>
  body { margin: 0; padding: 8px; font-size: 24px; }
  .row { margin-bottom: 6px; }
  .tnum { font-variant-numeric: tabular-nums; }
  .pnum { font-variant-numeric: proportional-nums; }
</style>
</head>
<body>
  <div class="row tnum" id="tnum"><span id="t1">1111</span> <span id="t2">8888</span></div>
  <div class="row pnum" id="pnum"><span id="p1">1111</span> <span id="p2">8888</span></div>
</body>
</html>""",
        "out": "第一行（tabular-nums）里“1111”和“8888”宽度完全相等，两列数字能上下对齐；第二行（proportional-nums）由字体决定宽度。",
        "pit": [
            "以为它与等宽字体等价：字母与标点仍是比例宽度。",
            "给整页加 tabular-nums，正文里的数字显得松散。",
            "字体没有等宽数字表时属性被静默忽略，需确认实际渲染。",
        ],
        "ex": [
            (
                "让第二行也用等宽数字。",
                "把 proportional-nums 换成 tabular-nums。",
                ".pnum { font-variant-numeric: tabular-nums; }",
            )
        ],
    },
    {
        "t": "text-decoration-skip-ink 下划线避让",
        "level": "intermediate",
        "obj": "控制下划线是否在字母的下伸部断开，并调整线与文字的间距与粗细。",
        "pre": ["CSS 文本装饰与链接样式"],
        "con": ["text-decoration-skip-ink", "text-underline-offset", "text-decoration-thickness", "下划线"],
        "explain": "现代浏览器默认开启 `text-decoration-skip-ink: auto`：下划线遇到 g、j、p、q 这类下伸部件时会断开，读起来更干净；改成 `none` 就得到一条贯穿到底的实线。配合 `text-underline-offset` 把线往下挪、`text-decoration-thickness` 加粗，可以做出接近设计稿的链接下划线，而不用画伪元素。注意偏移量过大会让线跑到下一行文字上；想要更精细的控制（比如渐变色下划线、只在悬停时出现）仍需伪元素方案。这三个属性都不会创建额外盒子，也不影响行高。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>下划线</title>
<style>
  body { margin: 0; padding: 8px; font-size: 20px; }
  a { display: block; margin-bottom: 8px; color: #1a73e8; }
  .ink { text-decoration-line: underline; text-decoration-skip-ink: auto; text-underline-offset: 4px; text-decoration-thickness: 2px; }
  .noink { text-decoration-line: underline; text-decoration-skip-ink: none; text-underline-offset: 4px; text-decoration-thickness: 2px; }
</style>
</head>
<body>
  <a class="ink" id="ink" href="#ink">jgpq 有避让</a>
  <a class="noink" id="noink" href="#noink">jgpq 无避让</a>
</body>
</html>""",
        "out": "两条链接都是 2px 粗、距基线 4px 的下划线；第一行在 j、g、p、q 的下伸处断开，第二行是连续实线。",
        "pit": [
            "把 offset 设得过大，线压到下一行文字上。",
            "用 border-bottom 代替下划线，导致无法避让字形且影响盒模型。",
            "在粗体大字号上仍用 1px 线，视觉上显得虚。",
        ],
        "ex": [
            (
                "让第二条也启用避让。",
                "把 noink 的值改成 auto。",
                ".noink { text-decoration-skip-ink: auto; }",
            )
        ],
    },
    {
        "t": "box-decoration-break 跨行装饰",
        "level": "advanced",
        "obj": "让行内元素换行时每一行都保有完整的背景、内边距与边框。",
        "pre": ["背景：颜色、渐变与图片"],
        "con": ["box-decoration-break", "clone", "行内片段", "跨行高亮"],
        "explain": "行内元素折行后会被切成多个片段。默认 `slice` 把装饰当作一整块切开：只有第一段有左内边距、最后一段有右内边距，边框也不会在行尾闭合。改成 `clone` 后，每个片段都重新绘制背景、内边距与边框，于是跨行高亮、带边框的链接在换行处依然是完整的小色块。它常用于文章里的高亮标记、代码片段内联样式。代价是片段间的间距会让文字略微松散；需要严格等宽排版时慎用。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>跨行装饰</title>
<style>
  body { margin: 0; padding: 8px; font-size: 18px; line-height: 1.8; }
  .narrow { width: 260px; border: 1px dashed #dadce0; }
  .hl { background: #e8f0fe; border-left: 3px solid #1a73e8; padding: 2px 6px; box-decoration-break: clone; }
</style>
</head>
<body>
  <div class="narrow"><p>普通文字开头，<span class="hl" id="hl">这里是一段故意写得足够长、长到必须在窄容器里折行的高亮文字</span>，后面继续。</p></div>
</body>
</html>""",
        "out": "高亮文字折成两行以上，每一行都有浅蓝背景、左侧 3px 蓝边和 6px 内边距，像是在每一行都重新画了一遍。",
        "pit": [
            "以为它作用于块级元素：块级元素不会被切成多个片段。",
            "在需要精确对齐的表格文字上用 clone，片段内边距让列变宽。",
            "忘记加行高，片段背景与上下行贴得过紧。",
        ],
        "ex": [
            (
                "改回默认的切片行为并观察差异。",
                "把值改成 slice。",
                ".hl { box-decoration-break: slice; }",
            )
        ],
    },
]

_B10 = [
    {
        "t": "text-box-trim 去掉行首多余空隙",
        "level": "advanced",
        "obj": "用 text-box-trim 与 text-box-edge 裁掉文字上下的字体留白，让视觉边距精确。",
        "pre": ["CSS 响应式字号与行宽"],
        "con": ["text-box-trim", "text-box-edge", "字体留白", "精确对齐"],
        "explain": "每一行文字的高度都包含字体自带的上下留白（ascent/descent），所以大标题看起来总比设计稿“多了一点空”。`text-box-trim: trim-both` 配合 `text-box-edge: cap alphabetic` 把盒子上缘裁到大写字母顶部、下缘裁到基线，于是标题的视觉边缘与盒边缘对齐，卡片内边距看起来才准确。它只影响块级容器的首行与末行，不改字号也不改行高。做营销页、卡片标题这类对像素敏感的场景很实用；对内边距本来就宽松的正文可以不用。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>裁掉留白</title>
<style>
  body { margin: 0; padding: 8px; }
  .title { font-size: 40px; line-height: 1.2; margin: 0; background: #e8f0fe; }
  .trim { text-box-trim: trim-both; text-box-edge: cap alphabetic; }
</style>
</head>
<body>
  <h1 class="title" id="plain">未裁剪标题</h1>
  <h1 class="title trim" id="trim">裁剪后标题</h1>
</body>
</html>""",
        "out": "两个标题字号都是 40px、背景浅蓝；下面的那个盒子明显更矮，上缘贴着大写字母顶部、下缘贴着基线。",
        "pit": [
            "以为它会改变字号或行高：它只裁掉盒子边缘的字体留白。",
            "对多行段落首行裁剪后，上下行看起来更挤。",
            "不同字体的 metrics 不同，裁剪后的高度不再是整数像素，写死高度会出错。",
        ],
        "ex": [
            (
                "只裁剪上缘。",
                "改 text-box-trim 的值。",
                ".trim { text-box-trim: trim-start; }",
            )
        ],
    },
    {
        "t": "@starting-style 让离散过渡有入场动画",
        "level": "advanced",
        "obj": "用 @starting-style 给“刚出现”的元素一个起始状态，并用 allow-discrete 过渡 display。",
        "pre": ["过渡与变换：transition 和 transform"],
        "con": ["@starting-style", "transition-behavior", "allow-discrete", "display 过渡"],
        "explain": "元素从 `display: none` 变成可见时，浏览器找不到“上一个值”，所以 opacity 过渡不会触发——这是最常见的“淡入没生效”。`@starting-style` 显式给出元素首次渲染时的起始状态，过渡于是有了起点；`transition-behavior: allow-discrete` 则让 `display` 这类离散属性也能参与过渡（延迟到动画结束时才切换）。两者合作就是纯 CSS 的进入/退出动画：展开时淡入下滑，收起时淡出上收。注意起始状态只对“第一次出现”生效，元素常驻时修改类名不会重放。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>入场动画</title>
<style>
  body { margin: 0; padding: 8px; }
  label { display: inline-block; padding: 6px 12px; background: #1a73e8; color: #ffffff; cursor: pointer; }
  .panel {
    display: none; opacity: 0; transform: translateY(8px);
    margin-top: 8px; padding: 12px; background: #e8f0fe;
    transition: opacity 0.3s ease, transform 0.3s ease, display 0.3s allow-discrete;
  }
  #toggle:checked ~ .panel { display: block; opacity: 1; transform: translateY(0); }
  @starting-style {
    #toggle:checked ~ .panel { opacity: 0; transform: translateY(8px); }
  }
</style>
</head>
<body>
  <input type="checkbox" id="toggle" hidden>
  <label for="toggle" id="btn">展开面板</label>
  <div class="panel" id="panel">面板内容</div>
</body>
</html>""",
        "out": "点击按钮前面板不可见；点击后面板淡入并从上往下移动 8px 到位，再点一次会淡出后消失。",
        "pit": [
            "只写过渡不写 @starting-style，从 display: none 出现时看不到动画。",
            "没有 allow-discrete，display 会瞬间切换，退出动画直接消失。",
            "把起始状态写成最终状态，动画看上去完全没动。",
        ],
        "ex": [
            (
                "让位移距离变成 16px。",
                "同时改最终状态与起始状态里的 translateY 起点。",
                "@starting-style { #toggle:checked ~ .panel { transform: translateY(16px); } }",
            )
        ],
    },
    {
        "t": "animation-fill-mode 与延迟序列",
        "level": "intermediate",
        "obj": "用 fill-mode 与 delay 控制动画结束后是否保持最终状态、以及何时开始。",
        "pre": ["动画：@keyframes 与 animation"],
        "con": ["animation-fill-mode", "animation-delay", "forwards", "关键帧"],
        "explain": "动画默认在结束后把元素还原成初始样式，于是“滑到位置又跳回去”。`animation-fill-mode: forwards` 让最后一帧的状态保持下来，`both` 则同时把第一帧也应用到延迟时间段上。`animation-delay` 控制开始前的等待，配合 fill-mode: backwards/both 才能在等待期就看到起始状态，否则元素会先闪一下原样。它们常与缩写 `animation: 名称 时长 缓动 延迟 次数 方向 填充` 一起写。注意 forwards 只是“视觉保持”，元素的计算样式仍是动画最后一帧，不代表属性被真正改写。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>填充模式</title>
<style>
  body { margin: 0; padding: 8px; }
  .bar { width: 60px; height: 24px; background: #1a73e8; }
  .run { animation: slide 0.3s ease 0.1s forwards; }
  @keyframes slide { to { transform: translateX(60px); } }
</style>
</head>
<body>
  <div class="bar run" id="bar"></div>
</body>
</html>""",
        "out": "蓝色方块在 0.1s 后开始右移，0.3s 后停在右移 60px 的位置并保持不再跳动。",
        "pit": [
            "只写 animation 不写 forwards，动画结束瞬间弹回原位。",
            "有延迟却不写 backwards/both，延迟期间元素先显示最终样式再跳回起点。",
            "以为 fill-mode 会持久修改属性：用 getComputedStyle 读到的仍是关键帧结果，不是内联值。",
        ],
        "ex": [
            (
                "让动画结束后回到原位。",
                "把 forwards 去掉。",
                ".run { animation: slide 0.3s ease 0.1s; }",
            )
        ],
    },
    {
        "t": "cubic-bezier 自定义缓动曲线",
        "level": "advanced",
        "obj": "用 cubic-bezier 描述非线性的速度曲线，做出先快后慢的动效手感。",
        "pre": ["过渡与变换：transition 和 transform"],
        "con": ["cubic-bezier", "缓动", "速度曲线", "动效手感"],
        "explain": "`ease` 之类的关键字背后都是三次贝塞尔曲线：`cubic-bezier(x1, y1, x2, y2)` 用两个控制点描述进度随时间变化的曲线。y 值可以超过 1 或小于 0，于是能做“回弹”和“冲出再回来”；x 必须保持在 0 到 1 之间，否则整条声明无效。`cubic-bezier(.2,.8,.2,1)` 是常见的“快起慢收”手感，适合卡片、抽屉；`linear` 则适合进度条这类需要匀速的场合。想要分段速度用 `steps()`，想要参数化的分段曲线可以用 `linear()` 函数。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>缓动曲线</title>
<style>
  body { margin: 0; padding: 8px; }
  .dot { width: 24px; height: 24px; background: #1a73e8; transition: transform 0.4s cubic-bezier(0.2, 0.8, 0.2, 1); }
  .dot:hover { transform: translateX(100px); }
</style>
</head>
<body>
  <div class="dot" id="dot"></div>
</body>
</html>""",
        "out": "鼠标移入时圆点用“快起慢收”的曲线右移 100px：开头快、接近终点明显减速，与匀速右移的手感完全不同。",
        "pit": [
            "把 x 写成超出 0 到 1 的值，整条 transition 声明被丢弃。",
            "四个参数顺序记反，得到意想不到的加速曲线。",
            "把缓动加在频繁触发的滚动监听动画上，反而显得延迟。",
        ],
        "ex": [
            (
                "做一个轻微回弹的曲线。",
                "让 y2 大于 1。",
                "transition: transform 0.4s cubic-bezier(0.2, 0.8, 0.2, 1.4);",
            )
        ],
    },
    {
        "t": "滚动驱动动画 animation-timeline: scroll()",
        "level": "advanced",
        "obj": "用滚动时间线让动画进度直接绑定滚动位置，无需脚本监听 scroll。",
        "pre": ["滚动行为与位置：scroll-behavior"],
        "con": ["animation-timeline", "scroll()", "滚动驱动", "进度条"],
        "explain": "`animation-timeline: scroll(root)` 把动画的进度来源从时间换成滚动位置：滚到顶部是 0%，滚到底部是 100%，中间线性插值。配合 `animation-range` 还能指定参与映射的区间，例如只在元素进入视口时播放。这样做的页面滚动进度条完全不依赖脚本，滚动时不会掉帧，也不需要在 scroll 事件里读布局。写法上先声明普通的 `animation: 名称 linear both`，再用 animation-timeline 覆盖时间来源；元素必须处在可滚动容器里，否则进度恒为 0。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>滚动动画</title>
<style>
  body { margin: 0; }
  .bar {
    position: fixed; top: 0; left: 0; width: 100%; height: 6px;
    background: #1a73e8; transform-origin: 0 50%; transform: scaleX(0);
    animation: grow linear both; animation-timeline: scroll(root);
  }
  .content { height: 2000px; padding: 24px 8px; background: #f8f9fa; }
  @keyframes grow { from { transform: scaleX(0); } to { transform: scaleX(1); } }
</style>
</head>
<body>
  <div class="bar" id="bar"></div>
  <div class="content">向下滚动，顶部进度条会跟随滚动位置增长。</div>
</body>
</html>""",
        "out": "页面停在顶部时进度条宽度为 0，滚到中间约一半，滚到底部时铺满整行；全程没有脚本参与。",
        "pit": [
            "只写 animation-timeline，又忘了保留 animation 名称与填充，进度不播放。",
            "把滚动驱动动画放在不可滚动的容器上，进度永远为 0。",
            "同时用脚本改同一属性，两者互相覆盖导致抖动。",
        ],
        "ex": [
            (
                "让进度条从下往上长（用缩放方向控制）。",
                "把 transform-origin 改成底部。",
                "transform-origin: 0 100%;",
            )
        ],
    },
]

_B11 = [
    {
        "t": "prefers-reduced-motion 动效降级",
        "level": "intermediate",
        "obj": "用媒体查询在系统要求减少动效时关闭动画，兼顾眩晕敏感用户。",
        "pre": ["动画：@keyframes 与 animation"],
        "con": ["prefers-reduced-motion", "可访问性", "动画降级", "媒体查询"],
        "explain": "部分用户会因为前庭功能敏感而关闭系统动效，`@media (prefers-reduced-motion: reduce)` 就是这件事的信号。正确做法不是把所有过渡删掉，而是去掉大幅位移、旋转、视差这类容易引起不适的效果，保留淡入淡出这类温和反馈。通常会写一个 `reduce` 分支把 animation 关掉、把 transition-duration 压到极短，同时保证界面结构不变。它属于“默认保留、必要时降级”的模式：先写完整动效，再用媒体查询覆盖。测试时可以在浏览器里模拟该偏好，无需改系统设置。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>减少动效</title>
<style>
  body { margin: 0; padding: 16px; }
  .spinner {
    width: 32px; height: 32px; border: 4px solid #dadce0; border-top-color: #1a73e8;
    border-radius: 50%; animation: spin 1s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  @media (prefers-reduced-motion: reduce) {
    .spinner { animation: none; }
  }
</style>
</head>
<body>
  <div class="spinner" id="spinner"></div>
</body>
</html>""",
        "out": "默认环境下圆环持续旋转（1s 一圈、无限循环）；系统开启“减少动效”后圆环静止，但样式与尺寸不变。",
        "pit": [
            "把 reduce 分支写成清空整个样式表，界面结构也随之丢失。",
            "只关注动画，忘了过渡与平滑滚动同样会引起不适。",
            "用 JS 判断一次偏好后写死，用户中途改系统设置不会跟随。",
        ],
        "ex": [
            (
                "在减少动效时也把旋转改成 0.01s 而不是完全移除。",
                "用 animation-duration 覆盖。",
                "@media (prefers-reduced-motion: reduce) { .spinner { animation-duration: 0.01s; } }",
            )
        ],
    },
    {
        "t": "animation-composition 叠加动画效果",
        "level": "advanced",
        "obj": "用 animation-composition 让多条动画在同一属性上相加，而不是互相覆盖。",
        "pre": ["动画：@keyframes 与 animation"],
        "con": ["animation-composition", "accumulate", "replace", "动画叠加"],
        "explain": "同一元素上有多条动画作用于同一属性时，默认 `replace` 让后出现的那条完全覆盖前面的值；`add` 把两条的数值相加，`accumulate` 则在同类型值上做累积合成。于是“基础位移 + 呼吸浮动”这类组合可以拆成两条独立动画，分别调整时长与缓动，而不用手写一条复合关键帧。多条动画名用逗号分隔，`animation-composition` 同样按列表一一对应，个数不足时循环取值。注意它只影响合成阶段，不改变每条动画自身的时间线。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>动画叠加</title>
<style>
  body { margin: 0; padding: 8px; }
  .box { width: 20px; height: 20px; background: #1a73e8; margin-bottom: 8px; }
  .box { animation-duration: 1s; animation-fill-mode: forwards; animation-timing-function: linear; }
  .rep { animation-name: base10, add20; animation-composition: replace; }
  .acc { animation-name: base10, add20; animation-composition: accumulate, accumulate; }
  @keyframes base10 { from { transform: translateX(10px); } to { transform: translateX(10px); } }
  @keyframes add20 { from { transform: translateX(20px); } to { transform: translateX(20px); } }
</style>
</head>
<body>
  <div class="box rep" id="rep"></div>
  <div class="box acc" id="acc"></div>
</body>
</html>""",
        "out": "两条动画都结束后，第一个方块停在 translateX(20px)，第二个方块停在 translateX(30px)：accumulate 把 10px 与 20px 相加了。",
        "pit": [
            "以为默认会叠加：默认 replace 只保留最后一条动画的值。",
            "动画没写 fill-mode: forwards，动画结束后两者都回到原位，看不出差异。",
            "把 accumulate 用在颜色上期望数值相加，结果按颜色规则合成，观感与预期不同。",
        ],
        "ex": [
            (
                "把第一个方块也改成叠加。",
                "改 rep 的合成方式。",
                ".rep { animation-composition: accumulate, accumulate; }",
            )
        ],
    },
    {
        "t": "scroll-snap 纯 CSS 横向卡片吸附",
        "level": "intermediate",
        "obj": "用 scroll-snap-type 与 scroll-snap-align 做出滑动后自动对齐的卡片轨道。",
        "pre": ["滚动行为与位置：scroll-behavior"],
        "con": ["scroll-snap-type", "scroll-snap-align", "scroll-padding", "横向轨道"],
        "explain": "横向卡片列表滚到手感松散，是因为停止位置完全随机。给容器加 `scroll-snap-type: x mandatory` 后，滚动结束时浏览器会把最近的吸附点对齐到容器边缘；子项加 `scroll-snap-align: start` 决定用它自己的哪条边对齐。`mandatory` 严格吸附，`proximity` 只在接近时吸附（更柔和）。容器两侧想留呼吸空间用 `scroll-padding-inline`，子项想留距离用 `scroll-margin`。注意 mandatory 在某些内容长度不一致的场景会让用户“滚不到想看的位置”，可以改用 proximity。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>吸附</title>
<style>
  body { margin: 0; padding: 8px; }
  .rail { display: flex; gap: 20px; width: 220px; overflow-x: auto; scroll-snap-type: x mandatory; }
  .card { flex: 0 0 200px; height: 80px; background: #e8f0fe; scroll-snap-align: start; }
</style>
</head>
<body>
  <div class="rail" id="rail">
    <div class="card" id="c1">1</div>
    <div class="card" id="c2">2</div>
    <div class="card" id="c3">3</div>
  </div>
</body>
</html>""",
        "out": "轨道宽 220px、卡片各 200px；向右滑动后卡片会自动吸附到左边缘，不会停在半张卡片的位置（本例第二张吸附在 220px 处）。",
        "pit": [
            "把 scroll-snap-type 写成只有 `x`，缺少 mandatory/proximity，吸附不生效。",
            "容器上写 scroll-snap-align 而不是容器下的子项写。",
            "卡片用百分比宽度加 gap，吸附点与容器宽度不整除时对不齐。",
        ],
        "ex": [
            (
                "改成柔和吸附。",
                "把 mandatory 换成 proximity。",
                ".rail { scroll-snap-type: x proximity; }",
            )
        ],
    },
    {
        "t": "scrollbar-gutter 预留滚动条空间",
        "level": "advanced",
        "obj": "用 scrollbar-gutter: stable 让滚动条出现或消失时内容不左右跳动。",
        "pre": ["CSS 卡片悬浮抬升效果"],
        "con": ["scrollbar-gutter", "布局跳动", "滚动条", "稳定布局"],
        "explain": "页面从短变长、滚动条突然出现时，可用宽度减少，所有居中内容会横向跳一下。`scrollbar-gutter: stable` 让浏览器始终为滚动条预留那条空间，无论当前是否真的需要滚动；`stable both-edges` 还会在两侧各留一半，保持居中不变。它比 `overflow-y: scroll` 更好：后者会让“不需要滚动”的容器也画出禁用状态的滚动条。注意它在使用覆盖式滚动条的系统（如部分移动端）上没有可见差别，因为覆盖式滚动条不占布局宽度。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>滚动条槽</title>
<style>
  body { margin: 0; padding: 8px; }
  .short { width: 200px; height: 60px; overflow-y: auto; scrollbar-gutter: stable; background: #e8f0fe; }
  .plain { width: 200px; height: 60px; overflow-y: auto; background: #f1f3f4; }
</style>
</head>
<body>
  <div class="short" id="short">内容很短，不会出现滚动条。</div>
  <div class="plain" id="plain">内容很短，也不会出现滚动条。</div>
</body>
</html>""",
        "out": "两个盒子高 60px；上面那个声明了 stable，即使没有滚动条也预留了滚动条宽度，内容区因此更窄，而下面的盒子铺满 200px。",
        "pit": [
            "以为 stable 会画出滚动条：它只预留空间，不绘制。",
            "在覆盖式滚动条系统上期待宽度变化，结果没有变化。",
            "给每个小组件都加 stable，窄容器可用宽度变得更小。",
        ],
        "ex": [
            (
                "两侧都预留空间。",
                "改 scrollbar-gutter 的值。",
                ".short { scrollbar-gutter: stable both-edges; }",
            )
        ],
    },
    {
        "t": "overscroll-behavior 阻断滚动链",
        "level": "intermediate",
        "obj": "用 overscroll-behavior: contain 让内层滚动到边界后不再带动外层页面。",
        "pre": ["滚动行为与位置：scroll-behavior"],
        "con": ["overscroll-behavior", "滚动链", "contain", "嵌套滚动"],
        "explain": "内层可滚动区域到达顶部或底部后，继续滚动会“传递”给外层页面，这就是滚动链；弹窗、侧边抽屉、地图容器被页面带着滚是最常见的投诉。`overscroll-behavior: contain` 断开这条链，但内容滚到底时仍会显示边缘的回弹提示；`none` 连回弹效果一起去掉。它还可以单独设置 `overscroll-behavior-y` 或 `-x`，只在某个方向生效。配合 `touch-action` 可以进一步约束手势，但要注意不要因此禁用用户必要的手势操作。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>滚动链</title>
<style>
  body { margin: 0; padding: 8px; }
  .tall { height: 1600px; background: #f8f9fa; }
  .outer { height: 200px; width: 260px; overflow-y: auto; overscroll-behavior: contain; background: #e8f0fe; position: fixed; top: 40px; left: 300px; }
  .inner { height: 600px; }
</style>
</head>
<body>
  <div class="outer" id="outer"><div class="inner" id="inner">内层内容（可滚动）</div></div>
  <div class="tall" id="tall">页面内容足够长，可以验证滚动链。</div>
</body>
</html>""",
        "out": "鼠标在内层区域继续向下滚动时，只会把内层滚到底，页面本身纹丝不动；把 contain 去掉后同样的手势会让页面跟着滚动。",
        "pit": [
            "只给内层写 overflow: auto，忘了断链，页面仍会被带动。",
            "把 overscroll-behavior 写在 body 上，内层容器的链并未断开。",
            "在需要触底反弹提示的场景用 none，用户会以为手势失效。",
        ],
        "ex": [
            (
                "同时禁用横向滚动链。",
                "改 overscroll-behavior 为 none。",
                ".outer { overscroll-behavior: none; }",
            )
        ],
    },
    {
        "t": "field-sizing 让输入框随内容变宽",
        "level": "advanced",
        "obj": "用 field-sizing: content 让输入框与文本域按内容自动伸缩，并配合最小最大宽度兜底。",
        "pre": ["CSS 表单外观统一"],
        "con": ["field-sizing", "自适应宽度", "min-width", "max-width"],
        "explain": "输入框默认是固定宽度，短内容浪费空间、长内容被截断。`field-sizing: content` 让控件宽度跟随内容，类似行内编辑器的体验；再配合 `min-width` 与 `max-width` 保证不会太窄或无限变宽。它对 `<input>` 与 `<textarea>` 都有效，文本域还能随内容增行。注意它依赖内容宽度计算，若父容器是 flex 且未设 `min-width: 0`，可能被压缩规则覆盖；同时不要与显式 width 混用，后者优先级更高会让效果失效。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>自适应输入</title>
<style>
  body { margin: 0; padding: 8px; }
  .grow {
    field-sizing: content; min-width: 80px; max-width: 260px;
    border: 1px solid #dadce0; border-radius: 6px; padding: 6px 8px; font-size: 16px;
  }
</style>
</head>
<body>
  <input class="grow" id="input" value="短">
  <p><textarea class="grow" id="textarea" rows="1">短</textarea></p>
</body>
</html>""",
        "out": "两个控件初始都很窄；输入更多文字时宽度随内容增长，超过 260px 后停止增长，内容被限制在最大宽度内。",
        "pit": [
            "同时写了 width: 200px，field-sizing 被固定宽度覆盖。",
            "不设 max-width，长文本把布局撑到出屏。",
            "在 flex 子项上使用却没写 min-width: 0，被压缩后看不出自适应。",
        ],
        "ex": [
            (
                "让控件最大宽度变成 400px。",
                "改 max-width。",
                ".grow { max-width: 400px; }",
            )
        ],
    },
    {
        "t": "appearance: none 自定义 select 外观",
        "level": "intermediate",
        "obj": "用 appearance: none 去掉系统控件外观，再用内联 SVG 背景画出下拉箭头。",
        "pre": ["表单控件样式与自定义复选框"],
        "con": ["appearance", "自定义箭头", "主题色", "focus-visible"],
        "explain": "`<select>` 的外观由系统绘制，圆角、内边距常常不听话。`appearance: none` 把系统绘制关掉，于是边框、背景、内边距全部由 CSS 决定；代价是默认的下拉箭头也没了，需要用 `background-image` 画一个内联 SVG（data URI，完全离线），并用 `background-position` 放到右侧。右侧要留出箭头宽度，所以 `padding-right` 要比左边大。别忘了补 `:focus-visible` 的焦点环，去掉系统外观后键盘用户就靠它来定位焦点。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>自定义下拉</title>
<style>
  body { margin: 0; padding: 8px; }
  .pick {
    appearance: none;
    border: 1px solid #dadce0; border-radius: 6px;
    padding: 8px 32px 8px 12px; font-size: 16px; background-color: #ffffff;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8'%3E%3Cpath d='M1 1l5 5 5-5' fill='none' stroke='%231a73e8' stroke-width='2'/%3E%3C/svg%3E");
    background-repeat: no-repeat; background-position: right 10px center;
  }
  .pick:focus-visible { outline: 2px solid #1a73e8; outline-offset: 2px; }
</style>
</head>
<body>
  <select class="pick" id="pick">
    <option>离线运行时</option>
    <option>本地预览</option>
    <option>导出静态站点</option>
  </select>
</body>
</html>""",
        "out": "下拉框是 6px 圆角、右侧留出 32px 空间并显示一个蓝色小箭头；用键盘 Tab 聚焦时出现 2px 蓝色焦点环。",
        "pit": [
            "只关外观不补箭头，用户看不出这是可展开的下拉。",
            "箭头用外部图片地址，离线环境下加载失败。",
            "padding-right 留得太小，箭头压在选项文字上。",
        ],
        "ex": [
            (
                "把箭头换成绿色。",
                "改内联 SVG 里的 stroke 颜色。",
                "stroke='%2334a853'",
            )
        ],
    },
    {
        "t": "CSS 锚点定位 position-anchor",
        "level": "advanced",
        "obj": "用 anchor-name、position-anchor 与 position-area 让浮层自动对齐到锚点元素。",
        "pre": ["定位：static、relative、absolute、fixed"],
        "con": ["anchor-name", "position-anchor", "position-area", "浮层定位"],
        "explain": "传统做法要用 JS 量出按钮坐标再设置浮层位置。CSS 锚点定位把这层关系写进样式：给锚点元素声明 `anchor-name: --tip`，给浮层写 `position-anchor: --tip` 与 `position-area: bottom`，浏览器就会把浮层放在锚点下方并自动居中；`anchor()` 函数还能在 `top`、`left` 里做精确偏移。浮层超出视口时浏览器会自动翻转到另一侧，这是手写绝对定位做不到的。它适合提示气泡、下拉菜单、角标，但这些功能通常仍需脚本控制显隐，CSS 只负责“贴在哪里”。",
        "code": """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>锚点定位</title>
<style>
  body { margin: 0; padding: 40px; }
  .anchor { anchor-name: --tip; display: inline-block; padding: 6px 12px; background: #1a73e8; color: #ffffff; }
  .tip {
    position: absolute; position-anchor: --tip; position-area: bottom;
    background: #202124; color: #ffffff; padding: 4px 8px; border-radius: 4px;
  }
</style>
</head>
<body>
  <span class="anchor" id="anchor">锚点按钮</span>
  <div class="tip" id="tip">提示气泡</div>
</body>
</html>""",
        "out": "提示气泡自动出现在按钮正下方并水平居中，顶部紧贴按钮底部；把 position-area 改成 top 就翻到按钮上方。",
        "pit": [
            "浮层忘了写 position: absolute，锚点定位没有可定位的盒子。",
            "anchor-name 与 position-anchor 的名字不一致（包括前缀的 --）。",
            "锚点与浮层不在同一个包含块里，定位会相对错误的祖先。",
        ],
        "ex": [
            (
                "把气泡翻到锚点上方。",
                "改 position-area。",
                ".tip { position-area: top; }",
            )
        ],
    },
]

CSS_EXTRA = _B1 + _B2 + _B3 + _B4 + _B5 + _B6 + _B7 + _B8 + _B9 + _B10 + _B11
