# HTML expansion browser verification

Documents: 60. Assertions: 629. Passed: 31. Failed: 29.

| id | topic | result | checks | first failure |
| --- | --- | --- | --- | --- |
| html-example-101 | hgroup 标题组与副标题绑定 | pass | 10 |  |
| html-example-102 | search 搜索地标与表单语义 | FAIL | 10 | click reports keyword:  |
| html-example-103 | address 联系信息语义与默认样式 | pass | 11 |  |
| html-example-104 | menu 工具条与命令按钮组 | pass | 9 |  |
| html-example-105 | article 与 aside 的正文和相关内容关系 | pass | 10 |  |
| html-example-106 | nav 面包屑与 aria-current 当前项 | pass | 10 |  |
| html-example-107 | 表格 caption 与 headers 显式关联 | pass | 10 |  |
| html-example-108 | colgroup 与 col 列分组 | pass | 9 |  |
| html-example-109 | tfoot 合计行与表格渲染顺序 | FAIL | 8 | table.tFoot present:  |
| html-example-110 | details name 互斥手风琴 | pass | 10 |  |
| html-example-111 | dialog 模态对话框与 ::backdrop | pass | 10 |  |
| html-example-112 | popover 轻量浮层与 toggle 事件 | pass | 10 |  |
| html-example-113 | datalist 输入建议与 list 关联 | pass | 10 |  |
| html-example-114 | optgroup 与 select multiple 多选 | pass | 12 |  |
| html-example-115 | output 元素与 for 关联计算结果 | FAIL | 10 | page load/setup: TypeError: (intermediate value).then is not a function |
| html-example-116 | 复选框 indeterminate 三态语义 | pass | 13 |  |
| html-example-117 | form 属性把外部控件关联进表单 | pass | 10 |  |
| html-example-118 | button formaction 与 formmethod 提交覆盖 | pass | 11 |  |
| html-example-119 | input type=image 提交坐标与 submitter | FAIL | 11 | pageerror: TypeError: Cannot set properties of null (setting 'textContent') |
| html-example-120 | setCustomValidity 自定义校验消息 | pass | 12 |  |
| html-example-121 | textarea 尺寸、换行与选区 API | FAIL | 9 | page load/setup: TypeError: (intermediate value).then is not a function |
| html-example-122 | formdata 事件与 FormData 迭代 | FAIL | 8 | formdata rewritten:  |
| html-example-123 | requestSubmit 与提交事件取消 | pass | 9 |  |
| html-example-124 | input type=number 步进与 valueAsNumber | pass | 11 |  |
| html-example-125 | ruby 注音标注与 rp 回退 | FAIL | 11 | ruby box grows for annotation:  |
| html-example-126 | bdi 与 bdo 的双向文本隔离 | FAIL | 11 | bdi stays ltr:  |
| html-example-127 | mark 高亮与检索命中 | FAIL | 11 | page load/setup: TypeError: (intermediate value).then is not a function |
| html-example-128 | del 与 ins 的修订记录语义 | pass | 11 |  |
| html-example-129 | s 与 small 的语义边界 | pass | 10 |  |
| html-example-130 | data value 机器可读取值 | pass | 9 |  |
| html-example-131 | wbr 长词断行与 overflow-wrap | pass | 10 |  |
| html-example-132 | base 与相对 URL 解析 | pass | 10 |  |
| html-example-133 | translate 与 spellcheck 编辑语义 | pass | 11 |  |
| html-example-134 | MathML 公式排版基础 | FAIL | 11 | exponent value:  |
| html-example-135 | picture 与 source media 艺术指导 | FAIL | 11 | wide crop selected at 1280px:  |
| html-example-136 | sup 与 sub 的表达式组合 | FAIL | 11 | four subscripts:  |
| html-example-137 | object 嵌入 SVG 与回退内容 | FAIL | 8 | page load/setup: TimeoutError: page.waitForFunction: Timeout 4000ms exceeded. |
| html-example-138 | embed 与 iframe srcdoc 内联文档 | FAIL | 10 | page load/setup: TypeError: (intermediate value).then is not a function |
| html-example-139 | iframe sandbox 的脚本与同源隔离 | FAIL | 10 | console: Blocked script execution in 'about:srcdoc' because the document's frame is sandboxed and the 'allow-scripts' permission is not set. |
| html-example-140 | canvas 高 DPI 像素适配与可访问回退 | FAIL | 11 | css size stays logical:  |
| html-example-141 | 内联 SVG 的可访问名称与描述 | FAIL | 11 | title text:  |
| html-example-142 | video poster 与 playsinline 首帧策略 | pass | 11 |  |
| html-example-143 | track 字幕轨与 VTTCue | FAIL | 10 | page load/setup: TypeError: (intermediate value).then is not a function |
| html-example-144 | 声明式 Shadow DOM 与插槽 | FAIL | 12 | light dom has no h3:  |
| html-example-145 | attachShadow 的作用域样式 ::slotted | FAIL | 11 | pageerror: SyntaxError: Unexpected identifier 'label' |
| html-example-146 | 自定义元素生命周期回调 | FAIL | 7 | page load/setup: TypeError: (intermediate value).then is not a function |
| html-example-147 | defer、async 与 noscript 加载时序 | pass | 10 |  |
| html-example-148 | script type=module 的作用域与 import.meta | FAIL | 9 | page load/setup: TypeError: (intermediate value).then is not a function |
| html-example-149 | aria-live 状态区域的播报 | FAIL | 10 | pageerror: TypeError: status.getAttribute is not a function |
| html-example-150 | role=tablist 标签页模式与键盘切换 | pass | 16 |  |
| html-example-151 | aria-expanded 披露按钮与 aria-controls | pass | 12 |  |
| html-example-152 | tabindex 焦点顺序与可编程聚焦 | FAIL | 10 | page load/setup: TypeError: (intermediate value).then is not a function |
| html-example-153 | inert 阻止焦点与交互 | pass | 10 |  |
| html-example-154 | hidden=until-found 与 beforematch | pass | 11 |  |
| html-example-155 | contenteditable plaintext-only 编辑区 | FAIL | 11 | page load/setup: TypeError: (intermediate value).then is not a function |
| html-example-156 | combobox 与 aria-activedescendant | pass | 16 |  |
| html-example-157 | popover=manual 与显式关闭动作 | FAIL | 8 | page load/setup: TypeError: (intermediate value).then is not a function |
| html-example-158 | aria-describedby 与 aria-errormessage 关联 | FAIL | 13 | page load/setup: TypeError: (intermediate value).then is not a function |
| html-example-159 | role=alert 错误汇总与焦点移动 | FAIL | 14 | page load/setup: TypeError: (intermediate value).then is not a function |
| html-example-160 | 综合实战：离线工单面板 | FAIL | 8 | pageerror: SyntaxError: missing ) after argument list |

## Failures

### html-example-102 — search 搜索地标与表单语义

- click reports keyword (ok=false) 
- empty keyword reported (ok=false) 

### html-example-109 — tfoot 合计行与表格渲染顺序

- table.tFoot present (ok=false) 
- page load/setup (ok=false) TypeError: (intermediate value).then is not a function

### html-example-115 — output 元素与 for 关联计算结果

- page load/setup (ok=false) TypeError: (intermediate value).then is not a function

### html-example-119 — input type=image 提交坐标与 submitter

- inline image loaded (ok=false) 
- page load/setup (ok=false) TypeError: (intermediate value).then is not a function
- error: pageerror: TypeError: Cannot set properties of null (setting 'textContent')

### html-example-121 — textarea 尺寸、换行与选区 API

- page load/setup (ok=false) TypeError: (intermediate value).then is not a function

### html-example-122 — formdata 事件与 FormData 迭代

- formdata rewritten (ok=false) 
- page load/setup (ok=false) TypeError: (intermediate value).then is not a function

### html-example-125 — ruby 注音标注与 rp 回退

- ruby box grows for annotation (ok=false) 

### html-example-126 — bdi 与 bdo 的双向文本隔离

- bdi stays ltr (ok=false) 
- bdo uses bidi-override (ok=false) 
- probe bidi state (ok=false) 

### html-example-127 — mark 高亮与检索命中

- page load/setup (ok=false) TypeError: (intermediate value).then is not a function

### html-example-134 — MathML 公式排版基础

- exponent value (ok=false) 
- math display block (ok=false) 
- fraction laid out taller than a line (ok=false) 

### html-example-135 — picture 与 source media 艺术指导

- wide crop selected at 1280px (ok=false) 
- page load/setup (ok=false) TypeError: (intermediate value).then is not a function

### html-example-136 — sup 与 sub 的表达式组合

- four subscripts (ok=false) 
- probe script state (ok=false) sub 数=3 / sup 数=4 / sub 对齐=sub / sup 对齐=super / 硫酸根=硫酸根离子：SO42− / 电荷在上=sup 在前

### html-example-137 — object 嵌入 SVG 与回退内容

- page load/setup (ok=false) TimeoutError: page.waitForFunction: Timeout 4000ms exceeded.

### html-example-138 — embed 与 iframe srcdoc 内联文档

- page load/setup (ok=false) TypeError: (intermediate value).then is not a function

### html-example-139 — iframe sandbox 的脚本与同源隔离

- error: console: Blocked script execution in 'about:srcdoc' because the document's frame is sandboxed and the 'allow-scripts' permission is not set.

### html-example-140 — canvas 高 DPI 像素适配与可访问回退

- css size stays logical (ok=false) 
- fallback text present (ok=false) 

### html-example-141 — 内联 SVG 的可访问名称与描述

- title text (ok=false) 
- desc text (ok=false) 

### html-example-143 — track 字幕轨与 VTTCue

- page load/setup (ok=false) TypeError: (intermediate value).then is not a function

### html-example-144 — 声明式 Shadow DOM 与插槽

- light dom has no h3 (ok=false) 

### html-example-145 — attachShadow 的作用域样式 ::slotted

- open shadow root (ok=false) 
- host background from :host (ok=false) 
- host radius from :host (ok=false) 
- slotted span bold (ok=false) 
- slotted letter spacing (ok=false) 
- page load/setup (ok=false) Error: locator.evaluate: TypeError: Cannot read properties of null (reading 'querySelector')
- error: pageerror: SyntaxError: Unexpected identifier 'label'

### html-example-146 — 自定义元素生命周期回调

- page load/setup (ok=false) TypeError: (intermediate value).then is not a function

### html-example-148 — script type=module 的作用域与 import.meta

- page load/setup (ok=false) TypeError: (intermediate value).then is not a function

### html-example-149 — aria-live 状态区域的播报

- live region updated (ok=false) 
- error: pageerror: TypeError: status.getAttribute is not a function

### html-example-152 — tabindex 焦点顺序与可编程聚焦

- page load/setup (ok=false) TypeError: (intermediate value).then is not a function

### html-example-155 — contenteditable plaintext-only 编辑区

- page load/setup (ok=false) TypeError: (intermediate value).then is not a function

### html-example-157 — popover=manual 与显式关闭动作

- page load/setup (ok=false) TypeError: (intermediate value).then is not a function

### html-example-158 — aria-describedby 与 aria-errormessage 关联

- page load/setup (ok=false) TypeError: (intermediate value).then is not a function

### html-example-159 — role=alert 错误汇总与焦点移动

- page load/setup (ok=false) TypeError: (intermediate value).then is not a function

### html-example-160 — 综合实战：离线工单面板

- page load/setup (ok=false) TypeError: (intermediate value).then is not a function
- error: pageerror: SyntaxError: missing ) after argument list

