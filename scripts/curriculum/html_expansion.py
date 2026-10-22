"""HTML expansion: 60 additional authored HTML lessons (ids 101-160).

These lessons extend the baseline 100 HTML topics (html_data*.py, supplement.py)
without duplicating them. Each new topic covers an HTML surface area the baseline
does not: modern structural elements, form-association and constraint APIs,
bidirectional text and machine-readable data, embedding/sandboxing, script
loading, declarative shadow DOM, and ARIA interaction patterns.

Every document is complete, standalone and offline:
  * no external URL in any fetched position;
  * no preconnect / dns-prefetch / preload hints;
  * all media inline `data:` or generated at runtime through Blob URLs;
  * links are same-document fragments only.

Schema matches the baseline modules exactly:
    t / level / obj / pre / con / explain / code / out / pit / ex

`code` is the complete document; scripts/emit_content.py appends the
`webforge-check` marker when emitting examples and tutorials.

Owned by task 10-22-standalone-offline-ide (WebForge HTML expansion).
"""

HTML_EXTRA = [
    {
        "t": "hgroup 标题组与副标题绑定",
        "level": "intermediate",
        "obj": "用 hgroup 把主标题与副标题组合成一个语义整体。",
        "pre": ["HTML 大纲与标题顺序", "语义化标签汇总与选择"],
        "con": ["hgroup", "副标题", "大纲层级", "段落与标题分组"],
        "explain": "`<hgroup>` 用来把标题和紧随其后的副标题、标语包成一个整体，表示“这是一组标题”，而副标题本身并不单独占用大纲层级。它只能包含 `<h1>`–`<h6>` 与 `<p>`。浏览器默认把它渲染成块级元素，样式仍由 CSS 控制。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>hgroup 标题组</title></head>
<body>
  <article>
    <hgroup id="head-group">
      <h2>离线 IDE 实战</h2>
      <p>从零搭建一个可用的本地开发环境</p>
    </hgroup>
    <p>正文：hgroup 让主标题和副标题在语义上不可分割。</p>
  </article>
  <p id="report">等待探测</p>
  <script>
    var group = document.getElementById('head-group');
    var tags = Array.prototype.map.call(group.children, function (el) {
      return el.tagName.toLowerCase();
    });
    document.getElementById('report').textContent =
      group.children.length + ' 个子元素：' + tags.join('>');
  </script>
</body>
</html>''',
        "out": "页面显示一个二级标题“离线 IDE 实战”，下面是灰色副标题“从零搭建一个可用的本地开发环境”，再下面是正文；探测行输出“2 个子元素：h2>p”。",
        "pit": [
            "在 hgroup 里放 img 或 div 是无效内容模型，浏览器不会报错但语义丢失。",
            "副标题用 p 而不是 h3，否则它会成为大纲里的独立条目。",
            "hgroup 只解决分组，不负责字号；不要指望它自动让副标题变小。",
        ],
        "ex": [("把副标题改成“配套 60 个示例”。", "只改 hgroup 内 p 的文本。", "<p>配套 60 个示例</p>")],
    },
    {
        "t": "search 搜索地标与表单语义",
        "level": "intermediate",
        "obj": "用 search 元素包围站内搜索控件并获得搜索地标语义。",
        "pre": ["语义化结构：header、nav、main、footer", "表单基础：form、input 与 label"],
        "con": ["search", "地标", "role=search", "input type=search", "label 关联"],
        "explain": "`<search>` 是 HTML 的搜索地标元素，用来包裹搜索或筛选控件组，它自带与 `role=\"search\"` 等价的地标语义，屏幕阅读器的地标列表里会出现“搜索”。它只是地标，不提供搜索能力，真正的过滤仍由脚本或服务端完成。地标内部仍应使用 `<form>` 与 `<label>`。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>search 地标</title></head>
<body>
  <header><h1>我的文档库</h1></header>
  <search id="site-search">
    <form action="#results">
      <label for="q">站内搜索</label>
      <input id="q" name="q" type="search" value="离线" autocomplete="off">
      <button type="button" id="run">筛选</button>
    </form>
  </search>
  <p id="status">等待筛选</p>
  <p id="results">离线优先 · 离线缓存 · 离线包</p>
  <script>
    var input = document.getElementById('q');
    var statusEl = document.getElementById('status');
    document.getElementById('run').addEventListener('click', function () {
      statusEl.textContent = input.value ? '关键词：' + input.value : '关键词为空';
    });
  </script>
</body>
</html>''',
        "out": "页面顶部是文档库标题，下面一行“站内搜索”标签 + 搜索框 + 筛选按钮。点击“筛选”后状态行变成“关键词：离线”；清空输入再点则显示“关键词为空”。",
        "pit": [
            "search 不能单独完成过滤，别把它当成功能组件。",
            "一个页面通常只放一个 search 地标，多个搜索框应合并到一个地标里。",
            "搜索框要用 label 关联或 aria-label，占位符不能替代可访问名称。",
        ],
        "ex": [("在地标里再加一个“仅离线”复选框。", "把 input 放进 label 里自动关联。", "<label><input type=\"checkbox\"> 仅离线</label>")],
    },
    {
        "t": "address 联系信息语义与默认样式",
        "level": "intermediate",
        "obj": "用 address 表达文档或文章作者的联系方式。",
        "pre": ["语义化结构：header、nav、main、footer", "HTML 全局属性总览"],
        "con": ["address", "联系信息", "默认斜体", "footer 组合", "br 用法"],
        "explain": "`<address>` 表示最近的 `article` 或 `body` 的作者、维护者的联系方式，而不是任意地址。浏览器默认把它渲染成斜体，并且是块级元素。它常放在 `<footer>` 中，内部用 `<br>` 分行；如果需要强调，可以用 `<a>` 给出联系方式入口。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>address 联系信息</title></head>
<body>
  <article>
    <h1>离线缓存的三条经验</h1>
    <p>正文内容……</p>
    <footer>
      <address id="contact">
        维护者：WebForge 文档组<br>
        反馈：<a href="#feedback">问题登记表</a><br>
        更新时间：<time datetime="2026-10-22">2026 年 10 月 22 日</time>
      </address>
      <p id="feedback">问题登记表位于离线工作区根目录。</p>
    </footer>
  </article>
  <p id="probe">等待探测</p>
  <script>
    var box = document.getElementById('contact');
    var style = getComputedStyle(box);
    document.getElementById('probe').textContent =
      'font-style=' + style.fontStyle + ';display=' + style.display +
      ';lines=' + box.querySelectorAll('br').length;
  </script>
</body>
</html>''',
        "out": "文章末尾出现联系信息块，文字为斜体并分三行显示；探测行输出“font-style=italic;display=block;lines=2”。",
        "pit": [
            "把办公室邮寄地址写进 address 只有在它确实是作者联系方式时才正确。",
            "address 内部不要再嵌套 address。",
            "斜体是浏览器默认样式，若设计需要正体应在 CSS 里显式改回。",
        ],
        "ex": [("在联系信息里补一行“版本：1.4”。", "用 br 换行，不要用两个 p。", "版本：1.4<br>")],
    },
    {
        "t": "menu 工具条与命令按钮组",
        "level": "intermediate",
        "obj": "用 menu 表达一组可执行的命令而不是导航链接。",
        "pre": ["列表：有序、无序与描述列表", "表单按钮与提交：button 类型与进入点"],
        "con": ["menu", "li", "命令语义", "事件委托", "dataset"],
        "explain": "`<menu>` 是 `<ul>` 的语义变体，表示一组*命令*（工具条、上下文操作），而不是普通条目列表。它同样用 `<li>` 作为子元素。命令通常由 `<button type=\"button\">` 承载，避免无意提交表单；一次点击可以用事件委托统一处理，靠 `data-*` 传命令名。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>menu 工具条</title>
  <style>
    menu { display: flex; gap: 8px; padding: 0; margin: 0 0 12px; }
    button { padding: 6px 12px; }
  </style>
</head>
<body>
  <menu id="toolbar">
    <li><button type="button" data-cmd="bold">加粗</button></li>
    <li><button type="button" data-cmd="italic">斜体</button></li>
    <li><button type="button" data-cmd="clear" disabled>清除</button></li>
  </menu>
  <p id="log">尚未选择命令</p>
  <script>
    var log = document.getElementById('log');
    document.getElementById('toolbar').addEventListener('click', function (event) {
      var button = event.target.closest('button');
      if (!button || button.disabled) return;
      log.textContent = '已选择：' + button.dataset.cmd;
    });
  </script>
</body>
</html>''',
        "out": "页面上是一条横向工具条，三个按钮依次为“加粗”“斜体”“清除”，其中“清除”置灰不可点。点击“斜体”后下方文字变成“已选择：italic”。",
        "pit": [
            "menu 里的按钮忘记写 type=\"button\" 时，在表单中会触发提交。",
            "被禁用的按钮不会触发 click，事件委托里要再判断一次 disabled。",
            "menu 不是导航菜单的正确选择，页面跳转请用 nav + ul。",
        ],
        "ex": [("再加一个“下划线”命令。", "复制一个 li，命令名用 underline。", "<li><button type=\"button\" data-cmd=\"underline\">下划线</button></li>")],
    },
    {
        "t": "article 与 aside 的正文和相关内容关系",
        "level": "intermediate",
        "obj": "用 main、article、aside 区分正文主体与旁支内容。",
        "pre": ["语义化标签汇总与选择", "HTML 综合实战：文章详情页"],
        "con": ["article", "aside", "main", "aria-labelledby", "内容独立性"],
        "explain": "`<article>` 表示可独立分发或复用的完整内容（一篇博客、一条工单）。`<aside>` 表示与正文相关但可脱离的旁支内容（相关阅读、术语提示）。两者可以并列放在 `<main>` 里；旁支内容建议用 `aria-labelledby` 指向自己的标题，这样屏幕阅读器在跳转时能读出这一块叫什么。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>article 与 aside</title></head>
<body>
  <main id="main">
    <article id="post">
      <h1>离线优先的设计取舍</h1>
      <p>正文第一段：先把本地能力做扎实。</p>
      <p>正文第二段：再考虑可选的同步。</p>
    </article>
    <aside id="related" aria-labelledby="related-title">
      <h2 id="related-title">相关阅读</h2>
      <ul>
        <li>本地存储配额</li>
        <li>离线资源打包</li>
      </ul>
    </aside>
  </main>
  <p id="summary">等待统计</p>
  <script>
    var post = document.getElementById('post');
    var aside = document.getElementById('related');
    var label = document.getElementById(aside.getAttribute('aria-labelledby'));
    document.getElementById('summary').textContent =
      post.querySelectorAll('p').length + ' 段正文 / ' +
      aside.querySelectorAll('li').length + ' 条相关 / 标签=' + label.textContent;
  </script>
</body>
</html>''',
        "out": "主区域左侧是文章标题和两段正文，右侧是带“相关阅读”标题的两条列表；统计行输出“2 段正文 / 2 条相关 / 标签=相关阅读”。",
        "pit": [
            "把整页导航塞进 aside 会削弱它的“旁支内容”语义。",
            "aria-labelledby 的值是元素的 id，不是文本，写错会得到空标签。",
            "一个页面里 main 只能有一个且不能嵌套在 article 内部。",
        ],
        "ex": [("给 aside 再加一条相关阅读。", "在 ul 末尾追加 li。", "<li>离线调试面板</li>")],
    },
    {
        "t": "nav 面包屑与 aria-current 当前项",
        "level": "intermediate",
        "obj": "用 nav + ol 构建面包屑，并标注当前页面。",
        "pre": ["语义化结构：header、nav、main、footer", "链接与锚点：a 标签的 href 家族"],
        "con": ["nav", "aria-label", "ol", "aria-current", "aria-disabled"],
        "explain": "面包屑是导航，所以外层用 `<nav>`，并给它 `aria-label=\"面包屑\"` 与其他导航区分。层级用 `<ol>` 表达。最后一项代表当前页面，用 `aria-current=\"page\"` 标注，通常渲染成不可点的文本；中间层级用链接。屏幕阅读器会把 current 读成“当前页”。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>面包屑导航</title></head>
<body>
  <nav id="crumbs" aria-label="面包屑">
    <ol>
      <li><a href="#home">首页</a></li>
      <li><a href="#docs">教程</a></li>
      <li><span aria-current="page">HTML 进阶</span></li>
    </ol>
  </nav>
  <p id="state">等待探测</p>
  <script>
    var nav = document.getElementById('crumbs');
    var current = nav.querySelector('[aria-current="page"]');
    document.getElementById('state').textContent =
      '当前页：' + current.textContent +
      ' / 层级：' + nav.querySelectorAll('li').length +
      ' / 链接：' + nav.querySelectorAll('a').length;
  </script>
</body>
</html>''',
        "out": "页面上出现“首页 › 教程 › HTML 进阶”的层级导航，前两项可点击跳转锚点，最后一项是纯文本；探测行输出“当前页：HTML 进阶 / 层级：3 / 链接：2”。",
        "pit": [
            "给当前项也加 href 会让用户误以为还能前进。",
            "aria-current 的值要与语境匹配，步骤流程应使用 step 而不是 page。",
            "面包屑只反映层级路径，不要拿它当主站导航。",
        ],
        "ex": [("在“教程”和当前页之间插入“语义化”层级。", "新增一个 li 放在倒数第二项。", "<li><a href=\"#semantic\">语义化</a></li>")],
    },
    {
        "t": "表格 caption 与 headers 显式关联",
        "level": "advanced",
        "obj": "用 caption 命名表格，并用 headers 显式绑定数据单元格与表头。",
        "pre": ["表格：table、thead、tbody 与合并单元格", "无障碍基础：ARIA 与键盘导航"],
        "con": ["caption", "headers", "scope", "数据表格语义", "屏幕阅读器"],
        "explain": "`<caption>` 是表格的标题，必须紧跟 `<table>` 开始标签。表头用 `scope=\"col\"`/`scope=\"row\"` 声明作用范围；对复杂表格，还可以用 `headers` 属性在数据单元格上列出它对应的表头 id，提供比 scope 更精确的关联。简单表格不必同时写两套，复杂表格才需要 `headers`。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>表格标题与表头关联</title></head>
<body>
  <table id="grades">
    <caption>期末成绩（满分 100）</caption>
    <thead>
      <tr><th id="h-name" scope="col">姓名</th><th id="h-score" scope="col">分数</th></tr>
    </thead>
    <tbody>
      <tr><td headers="h-name">小林</td><td headers="h-score">92</td></tr>
      <tr><td headers="h-name">小周</td><td headers="h-score">88</td></tr>
    </tbody>
  </table>
  <p id="state">等待探测</p>
  <script>
    var table = document.getElementById('grades');
    var firstScore = table.querySelector('tbody tr td[headers="h-score"]');
    var header = document.getElementById(firstScore.getAttribute('headers'));
    document.getElementById('state').textContent =
      'caption=' + table.caption.textContent.trim() +
      ' / 行数=' + table.rows.length +
      ' / 首个分数=' + firstScore.textContent +
      ' / 表头=' + header.textContent;
  </script>
</body>
</html>''',
        "out": "表格上方显示标题“期末成绩（满分 100）”，表头两列“姓名”“分数”，两行数据；探测行输出“caption=期末成绩（满分 100） / 行数=3 / 首个分数=92 / 表头=分数”。",
        "pit": [
            "caption 写在 thead 之后会失效。",
            "headers 里的 id 必须存在且唯一，写错等于没有关联。",
            "把布局表格也加 scope 会产生错误语义，布局应改用 CSS。",
        ],
        "ex": [("增加第三名学生“小陈 / 79”。", "复制一行 tr 并改 id 关联不变。", "<tr><td headers=\"h-name\">小陈</td><td headers=\"h-score\">79</td></tr>")],
    },
    {
        "t": "colgroup 与 col 列分组",
        "level": "advanced",
        "obj": "用 colgroup/col 为整列声明语义分组与列级样式。",
        "pre": ["表格：table、thead、tbody 与合并单元格", "表格 caption 与 headers 显式关联"],
        "con": ["colgroup", "col", "span", "列级样式", "DOM 结构"],
        "explain": "`<colgroup>` 是一组 `<col>`，每个 `<col>` 通过 `span` 覆盖若干列，用来给整列挂样式或标注意义。`colgroup` 必须出现在 `caption` 之后、`thead`/`tbody` 之前。列级背景色会绘制在单元格背景之下，所以单元格自身有背景色时会遮住列样式。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>列分组</title>
  <style>
    table { border-collapse: collapse; }
    th, td { border: 1px solid #c8cdd4; padding: 6px 10px; }
    .col-name { background: #eef4ff; }
    .col-num { background: #f6fbf2; }
  </style>
</head>
<body>
  <table id="plan">
    <caption>季度计划（单位：小时）</caption>
    <colgroup id="cols">
      <col span="1" class="col-name">
      <col span="2" class="col-num">
    </colgroup>
    <thead>
      <tr><th scope="col">项目</th><th scope="col">Q1</th><th scope="col">Q2</th></tr>
    </thead>
    <tbody>
      <tr><td>离线缓存</td><td>40</td><td>60</td></tr>
      <tr><td>示例验证</td><td>25</td><td>15</td></tr>
    </tbody>
  </table>
  <p id="state">等待探测</p>
  <script>
    var cols = document.querySelectorAll('#cols col');
    var owner = document.getElementById('cols').parentElement;
    document.getElementById('state').textContent =
      'col 数=' + cols.length +
      ' / 第二个 span=' + cols[1].span +
      ' / 覆盖列数=' + Array.prototype.reduce.call(cols, function (n, c) {
        return n + Number(c.span || 1);
      }, 0) +
      ' / 父元素=' + owner.tagName.toLowerCase();
  </script>
</body>
</html>''',
        "out": "表格第一列“项目”为浅蓝底，后两列数字为浅绿底；探测行输出“col 数=2 / 第二个 span=2 / 覆盖列数=3 / 父元素=table”。",
        "pit": [
            "colgroup 放在 thead 之后会被浏览器挪动或忽略，位置必须严格正确。",
            "单元格自己设置了背景色时，col 的背景色就看不到了。",
            "col 是空元素，不能包含 th/td，也不要写闭合标签。",
        ],
        "ex": [("让第一个 col 覆盖两列。", "把 span 改成 2 并调整 class。", "<col span=\"2\" class=\"col-name\">")],
    },
    {
        "t": "tfoot 合计行与表格渲染顺序",
        "level": "advanced",
        "obj": "用 tfoot 承载合计行，并理解它按渲染顺序出现在表体之后。",
        "pre": ["表格：table、thead、tbody 与合并单元格", "进度与度量：progress 与 meter"],
        "con": ["tfoot", "tableFoot", "渲染顺序", "数据汇总", "data-*"],
        "explain": "`<tfoot>` 表示表格的行列汇总。它的 DOM 位置可以写在 `<tbody>` 之前（历史写法），但浏览器一定会把它渲染在表体之后，因此不能靠 DOM 顺序或行号判断视觉顺序，应比较元素位置或使用 `table.tFoot`。脚本汇总数据时，只遍历 `tbody` 里的数据单元，避免把合计行重复计入。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>tfoot 合计行</title>
  <style>
    table { border-collapse: collapse; }
    th, td { border: 1px solid #c8cdd4; padding: 6px 10px; }
    tfoot th, tfoot td { background: #f2f4f7; font-weight: 600; }
  </style>
</head>
<body>
  <table id="cost">
    <caption>差旅费用（元）</caption>
    <thead><tr><th scope="col">项目</th><th scope="col">金额</th></tr></thead>
    <tfoot><tr><th scope="row">合计</th><td id="total">0</td></tr></tfoot>
    <tbody>
      <tr><td>车票</td><td data-amount="320">320</td></tr>
      <tr><td>住宿</td><td data-amount="480">480</td></tr>
    </tbody>
  </table>
  <p id="state">等待探测</p>
  <script>
    var table = document.getElementById('cost');
    var sum = Array.prototype.reduce.call(
      table.querySelectorAll('tbody td[data-amount]'),
      function (total, cell) { return total + Number(cell.dataset.amount); },
      0,
    );
    document.getElementById('total').textContent = sum;
    var foot = table.querySelector('tfoot');
    var lastBody = table.querySelector('tbody tr:last-child');
    document.getElementById('state').textContent =
      '合计=' + sum +
      ' / table.tFoot 匹配=' + (table.tFoot === foot) +
      ' / 行索引=' + foot.rows[0].rowIndex +
      ' / 表体行数=' + table.tBodies[0].rows.length;
  </script>
</body>
</html>''',
        "out": "表格按“项目 / 金额”“车票 320”“住宿 480”“合计 800”从上到下渲染（合计行取自 DOM 中靠前的 tfoot）；探测行输出“合计=800 / table.tFoot 匹配=true / 行索引=3 / 表体行数=2”。rowIndex 读取的是合计行 tr，表头占索引 0。",
        "pit": [
            "遍历整张表求和会把合计行也算进去，结果翻倍。",
            "tfoot 写在 tbody 前面不代表视觉上靠前，浏览器按固定规则渲染。",
            "合计单元格用 td 还是 th 要看语义：行标题用 th scope=row，数值结果用 td。",
        ],
        "ex": [("再加一行“餐饮 120”。", "新增 tbody 行，合计会自动更新。", "<tr><td>餐饮</td><td data-amount=\"120\">120</td></tr>")],
    },
    {
        "t": "details name 互斥手风琴",
        "level": "intermediate",
        "obj": "用 details 的 name 属性让同组折叠面板同一时间只展开一个。",
        "pre": ["内容分组：figure 与 details", "HTML 详情组与无障碍说明"],
        "con": ["details", "summary", "name 属性", "toggle 事件", "互斥展开"],
        "explain": "多个 `<details>` 使用相同的 `name` 时形成互斥组：展开其中一个会自动收起同组其他面板，浏览器原生实现，不需要脚本。`<summary>` 是面板的标题行，必须作为第一个子元素。`toggle` 事件在展开状态变化后触发，事件对象上的 `newState` 是 `\"open\"` 或 `\"closed\"`。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>互斥手风琴</title></head>
<body>
  <details name="faq" open>
    <summary>离线包怎么更新？</summary>
    <p>导入新的内容包后重启本地运行时即可。</p>
  </details>
  <details name="faq">
    <summary>支持哪些设备？</summary>
    <p>支持桌面浏览器与 OHOS 设备上的本地运行时。</p>
  </details>
  <p id="state">当前展开：离线包怎么更新？</p>
  <script>
    var panels = document.querySelectorAll('details[name="faq"]');
    Array.prototype.forEach.call(panels, function (panel) {
      panel.addEventListener('toggle', function (event) {
        var open = document.querySelectorAll('details[name="faq"][open]');
        document.getElementById('state').textContent =
          '最新事件=' + event.newState +
          ' / 展开数=' + open.length +
          ' / 展开项=' + Array.prototype.map.call(open, function (item) {
            return item.querySelector('summary').textContent;
          }).join('、');
      });
    });
  </script>
</body>
</html>''',
        "out": "页面有两个可折叠面板，初始只展开第一个。点击第二个面板的标题后，第一个自动收起，状态行显示“最新事件=open / 展开数=1 / 展开项=支持哪些设备？”。",
        "pit": [
            "name 相同的 details 才会互斥；漏写 name 就各自独立展开。",
            "summary 必须是第一个子元素，放到后面浏览器不会把它当标题。",
            "toggle 事件是异步派发的，点击后立刻读事件结果可能还没更新，应在回调里读。",
        ],
        "ex": [("再加第三个同组面板“如何导出日志？”。", "保持 name=\"faq\"。", "<details name=\"faq\"><summary>如何导出日志？</summary><p>从终端面板导出。</p></details>")],
    },
    {
        "t": "dialog 模态对话框与 ::backdrop",
        "level": "advanced",
        "obj": "用 showModal 打开模态对话框，并读取 ::backdrop 与 returnValue。",
        "pre": ["表单按钮与提交：button 类型与进入点", "无障碍基础：ARIA 与键盘导航"],
        "con": ["dialog", "showModal", ":modal", "::backdrop", "form method=dialog", "returnValue"],
        "explain": "`<dialog>` 默认是隐藏的，调用 `showModal()` 会以模态方式打开：页面其余内容不可交互，焦点被限制在对话框内，并绘制 `::backdrop` 遮罩。对话框内的 `<form method=\"dialog\">` 提交时会关闭对话框，并把被点按钮的 `value` 写进 `dialog.returnValue`。关闭时触发 `close` 事件。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>dialog 模态</title>
  <style>
    dialog { border: 1px solid #c8cdd4; border-radius: 8px; padding: 16px 20px; }
    dialog::backdrop { background: rgba(15, 23, 42, 0.45); }
  </style>
</head>
<body>
  <button type="button" id="open">打开对话框</button>
  <p id="result">未操作</p>
  <dialog id="dlg" aria-labelledby="dlg-title">
    <h2 id="dlg-title">确认删除</h2>
    <p>删除后无法恢复。</p>
    <form method="dialog">
      <button value="cancel">取消</button>
      <button value="ok" id="confirm">删除</button>
    </form>
  </dialog>
  <script>
    var dlg = document.getElementById('dlg');
    document.getElementById('open').addEventListener('click', function () {
      dlg.showModal();
    });
    dlg.addEventListener('close', function () {
      document.getElementById('result').textContent =
        'returnValue=' + dlg.returnValue + ' / open=' + dlg.open;
    });
  </script>
</body>
</html>''',
        "out": "点击“打开对话框”后弹出带半透明遮罩的模态框；点“删除”后对话框关闭，状态行显示“returnValue=ok / open=false”。",
        "pit": [
            "用 open 属性或 show() 打开不是模态，遮罩与焦点限制都不会出现。",
            "button 不写 value 时 returnValue 是空字符串，无法区分取消与确认。",
            "改 ::backdrop 样式要写在 dialog::backdrop 选择器上，普通背景色不生效。",
        ],
        "ex": [("把取消按钮的返回值改成 cancel-close。", "只改 value。", "<button value=\"cancel-close\">取消</button>")],
    },
    {
        "t": "popover 轻量浮层与 toggle 事件",
        "level": "advanced",
        "obj": "用 popovertarget 声明式打开浮层，并观察 toggle 事件的状态。",
        "pre": ["dialog 模态对话框与 ::backdrop", "HTML5 数据属性：data-* 与前端钩子"],
        "con": ["popover", "popovertarget", "popovertargetaction", ":popover-open", "toggle 事件"],
        "explain": "任何元素加上 `popover` 属性就变成浮层，默认处于隐藏状态。按钮用 `popovertarget=\"浮层id\"` 就能打开它，不需要脚本；`popovertargetaction=\"hide\"` 可以再关掉。打开时元素匹配 `:popover-open`，同时派发 `toggle` 事件，`newState` 为 `\"open\"` 或 `\"closed\"`。`auto` 浮层点击外部会自动关闭，`manual` 则不会。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>popover 浮层</title>
  <style>
    [popover] { border: 1px solid #c8cdd4; border-radius: 8px; padding: 12px 16px; }
  </style>
</head>
<body>
  <button type="button" id="trigger" popovertarget="tip">显示提示</button>
  <div id="tip" popover>
    <p>这是一个声明式 popover 浮层。</p>
    <button type="button" id="hide" popovertarget="tip" popovertargetaction="hide">关闭</button>
  </div>
  <p id="state">popover closed</p>
  <script>
    var tip = document.getElementById('tip');
    tip.addEventListener('toggle', function (event) {
      document.getElementById('state').textContent =
        'popover ' + event.newState + ' / pinned=' + tip.matches(':popover-open');
    });
  </script>
</body>
</html>''',
        "out": "点击“显示提示”后浮层出现在按钮附近，状态行变为“popover open / pinned=true”；点击浮层里的“关闭”后浮层消失，状态行变为“popover closed / pinned=false”。",
        "pit": [
            "popover 元素默认 display:none，想调位置要用定位样式而不是靠外边距。",
            "popovertarget 的值是目标元素的 id，不是 CSS 选择器，别加 #。",
            "auto 浮层点击外部会关闭，如果希望常驻要显式写 popover=\"manual\"。",
        ],
        "ex": [("给浮层加一条说明文字的第二个段落。", "在 p 后追加 p。", "<p>再次点击按钮即可切换。</p>")],
    },
    {
        "t": "datalist 输入建议与 list 关联",
        "level": "intermediate",
        "obj": "用 datalist 为文本输入提供可选建议而不限制自由输入。",
        "pre": ["表单基础：form、input 与 label", "表单控件进阶：select、textarea、range"],
        "con": ["datalist", "list 属性", "option value", "input.list", "change 事件"],
        "explain": "`<datalist>` 给输入框提供建议列表，通过 `input` 的 `list` 属性按 id 关联。它与 `<select>` 的关键区别是：建议不是强制选项，用户仍可以输入列表外的值。脚本里可以用 `input.list` 直接拿到关联的 datalist 元素，用 `option.value` 读取候选项。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>datalist 建议</title></head>
<body>
  <label for="city">城市</label>
  <input id="city" list="cities" placeholder="输入或选择" autocomplete="off">
  <datalist id="cities">
    <option value="杭州"></option>
    <option value="合肥"></option>
    <option value="深圳"></option>
  </datalist>
  <p id="picked">未选择</p>
  <p id="meta">等待探测</p>
  <script>
    var input = document.getElementById('city');
    input.addEventListener('change', function () {
      document.getElementById('picked').textContent =
        input.value ? '已选：' + input.value : '未选择';
    });
    document.getElementById('meta').textContent =
      'list 关联=' + (input.list ? input.list.id : 'none') +
      ' / 候选数=' + (input.list ? input.list.options.length : 0);
  </script>
</body>
</html>''',
        "out": "输入框右侧出现下拉箭头，展开可见杭州、合肥、深圳三个建议；探测行输出“list 关联=cities / 候选数=3”。选择或输入合肥并失焦后，状态行显示“已选：合肥”。",
        "pit": [
            "datalist 的 option 不需要闭合，写成 </option> 也不算错但容易与 select 混淆。",
            "list 属性的值是 id 而不是选择器，写成 #cities 会失效。",
            "datalist 不提供校验，需要限定取值时要在提交时自行判断。",
        ],
        "ex": [("再加一个候选“成都”。", "在 datalist 末尾追加 option。", "<option value=\"成都\"></option>")],
    },
    {
        "t": "optgroup 与 select multiple 多选",
        "level": "intermediate",
        "obj": "用 optgroup 分组选项，并用 multiple 实现多选与 selectedOptions 读取。",
        "pre": ["表单控件进阶：select、textarea、range", "表单分组与禁用状态"],
        "con": ["select", "multiple", "size", "optgroup", "selectedOptions"],
        "explain": "`<optgroup label=\"…\">` 给 `<select>` 的选项分组，分组本身不可选，也可以整体 `disabled`。加 `multiple` 后用户可以多选，用 `select.selectedOptions` 得到一个实时的选项集合，直接 `map` 出 value 即可。`size` 控制可见行数，多选列表至少要能看见两三行才好操作。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>多选与分组</title></head>
<body>
  <label for="langs">熟悉语言（可多选）</label>
  <select id="langs" multiple size="5">
    <optgroup label="前端">
      <option value="html" selected>HTML</option>
      <option value="css">CSS</option>
    </optgroup>
    <optgroup label="后端" disabled>
      <option value="go">Go</option>
      <option value="rust">Rust</option>
    </optgroup>
  </select>
  <p id="out">已选：html</p>
  <p id="meta">等待探测</p>
  <script>
    var select = document.getElementById('langs');
    select.addEventListener('change', function () {
      var picked = Array.prototype.map.call(select.selectedOptions, function (option) {
        return option.value;
      });
      document.getElementById('out').textContent = '已选：' + (picked.join(', ') || '无');
    });
    var groups = select.querySelectorAll('optgroup');
    document.getElementById('meta').textContent =
      'multiple=' + select.multiple +
      ' / size=' + select.size +
      ' / 分组=' + groups.length +
      ' / 禁用分组=' + (groups[1].disabled ? groups[1].label : '无') +
      ' / 选项=' + select.options.length;
  </script>
</body>
</html>''',
        "out": "页面出现五行高的多选列表，“前端”组里的 HTML 默认选中，“后端”组整体置灰不可选；探测行输出“multiple=true / size=5 / 分组=2 / 禁用分组=后端 / 选项=4”。",
        "pit": [
            "不加 multiple 时 selectedOptions 只会有一个，别指望多选。",
            "optgroup 不能嵌套，也不要给 optgroup 写 value。",
            "给 selectedOptions 排序要用 Array.from 后再排序，它本身没有 sort 方法。",
        ],
        "ex": [("让 CSS 也默认选中。", "在 css 的 option 上加 selected。", "<option value=\"css\" selected>CSS</option>")],
    },
    {
        "t": "output 元素与 for 关联计算结果",
        "level": "intermediate",
        "obj": "用 output 展示表单计算结果，并用 for 声明结果来源控件。",
        "pre": ["表单基础：form、input 与 label", "表单数字与范围约束"],
        "con": ["output", "for 属性", "name 属性", "input 事件", "实时计算"],
        "explain": "`<output>` 表示计算或用户操作产生的结果，语义上不同于普通段落。`for` 属性列出参与计算的控件 id（空格分隔），`name` 让它像其他控件一样出现在表单数据里。结果由脚本在 `input` 事件里更新，这样输入过程中的每一次变化都能反映出来。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>output 计算</title></head>
<body>
  <form id="calc">
    <p><label for="qty">数量</label><input id="qty" name="qty" type="number" value="2" min="0" step="1"></p>
    <p><label for="price">单价</label><input id="price" name="price" type="number" value="15" min="0" step="0.5"></p>
    <p>合计：<output id="sum" name="sum" for="qty price">30.00</output> 元</p>
  </form>
  <p id="meta">等待探测</p>
  <script>
    var form = document.getElementById('calc');
    var qty = document.getElementById('qty');
    var price = document.getElementById('price');
    var sum = document.getElementById('sum');
    function refresh() {
      var total = Number(qty.value || 0) * Number(price.value || 0);
      sum.textContent = total.toFixed(2);
    }
    form.addEventListener('input', refresh);
    refresh();
    document.getElementById('meta').textContent =
      'for=' + sum.getAttribute('for') +
      ' / name=' + sum.name +
      ' / 初值=' + sum.value +
      ' / 表单内=' + (form.elements.namedItem('sum') === sum);
  </script>
</body>
</html>''',
        "out": "表单显示数量 2、单价 15，合计行初始为 30.00 元；把数量改成 3 后合计立刻变成 45.00；探测行输出“for=qty price / name=sum / 初值=30.00 / 表单内=true”。",
        "pit": [
            "output 的 value 就是它的文本内容，不要另外写 value 属性。",
            "只在 change 事件里更新会导致拖动数字框时不刷新，应监听 input。",
            "for 里写的是 id 列表，写成选择器或逗号分隔都不符合规范。",
        ],
        "ex": [("把合计结果保留一位小数。", "把 toFixed(2) 改成 toFixed(1)。", "sum.textContent = total.toFixed(1);")],
    },
    {
        "t": "复选框 indeterminate 三态语义",
        "level": "advanced",
        "obj": "用 indeterminate 表现“部分选中”，并让父复选框驱动子项。",
        "pre": ["表单基础：form、input 与 label", "HTML 表单与后端交互的结构"],
        "con": ["indeterminate", "checked", "全选", "input 事件", "状态同步"],
        "explain": "复选框的 `indeterminate` 是脚本属性而不是 HTML 属性，表示“既非全选也非全不选”的第三态，常见于全选控制。它只影响外观与读屏语义，不会改变 `checked`，也不会随点击自动清除，需要在事件里自己维护。点击父复选框时按逻辑把子项全部设为选中或全部取消。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>三态复选框</title></head>
<body>
  <form id="picker">
    <p><label><input type="checkbox" id="all"> 全选</label></p>
    <ul id="items">
      <li><label><input type="checkbox" class="item" value="html" checked> HTML</label></li>
      <li><label><input type="checkbox" class="item" value="css" checked> CSS</label></li>
      <li><label><input type="checkbox" class="item" value="js"> JavaScript</label></li>
    </ul>
  </form>
  <p id="state">等待探测</p>
  <script>
    var all = document.getElementById('all');
    var items = Array.prototype.slice.call(document.querySelectorAll('.item'));
    function syncAll() {
      var checked = items.filter(function (item) { return item.checked; }).length;
      all.checked = checked === items.length;
      all.indeterminate = checked > 0 && checked < items.length;
      document.getElementById('state').textContent =
        '选中=' + checked + '/' + items.length +
        ' / all.checked=' + all.checked +
        ' / all.indeterminate=' + all.indeterminate;
    }
    all.addEventListener('change', function () {
      items.forEach(function (item) { item.checked = all.checked; });
      syncAll();
    });
    items.forEach(function (item) { item.addEventListener('change', syncAll); });
    syncAll();
  </script>
</body>
</html>''',
        "out": "初始勾选 HTML 与 CSS 两项，父级“全选”呈横线三态；探测行输出“选中=2/3 / all.checked=false / all.indeterminate=true”。勾上 JavaScript 后父级变为已选，取消全选后三个子项全部取消。",
        "pit": [
            "只设 indeterminate 不会取消 checked，两个状态需要分别维护。",
            "没有 HTML 属性可以声明三态，必须用脚本在元素上赋值。",
            "点击父项时若只改 indeterminate 而不改子项，数据仍不一致。",
        ],
        "ex": [("删除 CSS 子项后观察三态是否仍正确。", "删掉一个 li，脚本会自动按 2 项计算。", "（删除后父级只在 1/2 时三态）")],
    },
    {
        "t": "form 属性把外部控件关联进表单",
        "level": "advanced",
        "obj": "用 form 属性让表单外的控件参与提交与校验。",
        "pre": ["表单基础：form、input 与 label", "表单提交方法：GET 与 POST"],
        "con": ["form 属性", "form.elements", "关联控件", "formAction", "布局自由"],
        "explain": "控件不必是 `<form>` 的后代，只要 `form=\"表单id\"` 就能被关联进那个表单：它会出现在 `form.elements` 里，参与校验与提交，而页面结构可以把它放在别处（例如侧栏或卡片）。这种关联让你既能保持视觉布局，又不牺牲表单语义。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>form 属性关联</title></head>
<body>
  <form id="signup" action="#done">
    <p><label for="name">昵称</label><input id="name" name="name" value="小林"></p>
  </form>
  <section id="side">
    <h2>在表单外</h2>
    <p><label for="email">邮箱</label><input id="email" name="email" type="email" form="signup" value="lin@example.invalid"></p>
    <p><button type="submit" form="signup">提交</button></p>
  </section>
  <p id="state">等待探测</p>
  <script>
    var form = document.getElementById('signup');
    var email = document.getElementById('email');
    document.getElementById('state').textContent =
      'email.form 匹配=' + (email.form === form) +
      ' / 表单控件数=' + form.elements.length +
      ' / 含 email=' + (form.elements.namedItem('email') === email) +
      ' / 含 name=' + (form.elements.namedItem('name') !== null);
  </script>
</body>
</html>''',
        "out": "昵称输入框在表单里，邮箱输入框和提交按钮在表单外的侧栏里，但它们属于同一个表单；探测行输出“email.form 匹配=true / 表单控件数=3 / 含 email=true / 含 name=true”。",
        "pit": [
            "form 属性的值是表单 id，写错时控件成为脱离表单的孤立控件，既不校验也不提交。",
            "外部控件仍要写 name，否则不会出现在表单数据里。",
            "同一个 id 被两个表单引用会报错，关联关系必须唯一。",
        ],
        "ex": [("在外部区域再加一个必填的“手机号”输入框。", "加 form=\"signup\" 与 required。", "<input id=\"phone\" name=\"phone\" required form=\"signup\">")],
    },
    {
        "t": "button formaction 与 formmethod 提交覆盖",
        "level": "advanced",
        "obj": "用按钮级的 formaction/formmethod 让同一个表单提交到不同目标。",
        "pre": ["表单按钮与提交：button 类型与进入点", "表单提交方法：GET 与 POST"],
        "con": ["formaction", "formmethod", "form.submitter", "提交按钮覆盖", "多动作表单"],
        "explain": "提交按钮可以为本次提交覆盖表单的 `action` 与 `method`：保存草稿和正式发布可以共用一个表单，却走不同的地址与方法。属性名在 HTML 里是 `formaction`/`formmethod`，脚本里读 `button.formAction`（绝对化后的 URL）与 `button.formMethod`。只有作为提交者的按钮才会生效。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>按钮级提交覆盖</title></head>
<body>
  <form id="publish" action="#local-draft" method="get">
    <p><label for="title">标题</label><input id="title" name="title" value="离线周报"></p>
    <button type="submit" id="save">保存草稿</button>
    <button type="submit" id="now" formaction="#local-publish" formmethod="post">立即发布</button>
  </form>
  <p id="state">等待探测</p>
  <script>
    var form = document.getElementById('publish');
    var save = document.getElementById('save');
    var now = document.getElementById('now');
    document.getElementById('state').textContent =
      '表单 action=' + form.getAttribute('action') +
      ' / 表单 method=' + form.method +
      ' / 发布 action=' + now.getAttribute('formaction') +
      ' / 发布 method=' + now.getAttribute('formmethod') +
      ' / 发布 formAction 结尾匹配=' + now.formAction.endsWith('#local-publish') +
      ' / 草稿 method 覆盖=' + (save.getAttribute('formmethod') || 'none');
  </script>
</body>
</html>''',
        "out": "表单显示一个标题输入框和“保存草稿”“立即发布”两个提交按钮；探测行输出“表单 action=#local-draft / 表单 method=get / 发布 action=#local-publish / 发布 method=post / 发布 formAction 结尾匹配=true / 草稿 method 覆盖=none”。",
        "pit": [
            "formaction 只在提交按钮上有效，普通 button 或 disabled 按钮不会覆盖。",
            "脚本读 button.formMethod 时未设置属性得到空字符串，别当成继承表单方法。",
            "覆盖只能改变地址与方法，不能改变 enctype 之外的请求体格式。",
        ],
        "ex": [("给“保存草稿”按钮加上 formmethod=\"post\"。", "与发布按钮写法一致。", "<button type=\"submit\" id=\"save\" formmethod=\"post\">保存草稿</button>")],
    },
    {
        "t": "input type=image 提交坐标与 submitter",
        "level": "advanced",
        "obj": "用图片提交按钮把点击坐标提交，并识别提交来源按钮。",
        "pre": ["表单按钮与提交：button 类型与进入点", "图片与替代文本：img 的正确用法"],
        "con": ["input type=image", "submitter", "SubmitEvent", "坐标提交", "alt 可访问名"],
        "explain": "`<input type=\"image\">` 是图片形式的提交按钮：用户点击的位置会以 `name.x`、`name.y` 的形式进入表单数据，浏览器还会把被点按钮作为 `SubmitEvent.submitter`。它必须有 `alt`，否则屏幕阅读器读不出按钮名。图片本身与 `<img>` 一样是外部资源，本示例使用内联 SVG 保证离线。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>图片提交按钮</title></head>
<body>
  <form id="pick" action="#hit">
    <p>点击下图不同位置提交，坐标会写进表单数据。</p>
    <input type="image" id="map" name="spot" alt="选择位置" width="160" height="80"
      src="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%27160%27 height=%2780%27%3E%3Crect width=%27160%27 height=%2780%27 fill=%27%23e8f0fe%27/%3E%3Ccircle cx=%2780%27 cy=%2740%27 r=%2724%27 fill=%27%231a73e8%27/%3E%3C/svg%3E">
  </form>
  <p id="state">尚未提交</p>
  <p id="meta">等待探测</p>
  <script>
    var form = document.getElementById('pick');
    var map = document.getElementById('map');
    var image = new Image();
    form.addEventListener('submit', function (event) {
      event.preventDefault();
      var data = new FormData(form, event.submitter);
      document.getElementById('state').textContent =
        'submitter 是图片按钮=' + (event.submitter === map) +
        ' / type=' + map.type +
        ' / 坐标字段=' + map.name + '.x,' + map.name + '.y' +
        ' / 坐标=' + data.get(map.name + '.x') + ',' + data.get(map.name + '.y');
    });
    function reportImage() {
      document.getElementById('meta').textContent =
        'naturalWidth=' + image.naturalWidth + ' / complete=' + image.complete +
        ' / form 关联=' + (map.form === form);
    }
    image.addEventListener('load', reportImage);
    image.src = map.src;
    if (image.complete) reportImage();
  </script>
</body>
</html>''',
        "out": "页面显示一个 160×80 的浅蓝底蓝色圆点图作为提交按钮；点击后状态行显示真实的 spot.x、spot.y 坐标，例如点击 (30,20) 输出“submitter 是图片按钮=true / type=image / 坐标字段=spot.x,spot.y / 坐标=30,20”。探测行通过独立的 Image 解码确认图片宽 160、已加载且按钮关联表单。",
        "pit": [
            "图片按钮缺 alt 时读屏只能读成“按钮”，无法说明用途。",
            "坐标字段名依赖 name，没写 name 就只有 x/y 前缀残缺。",
            "用 input type=image 承载纯视觉装饰会误导键盘用户，键盘回车也会提交。",
            "图片提交控件是 HTMLInputElement，没有 naturalWidth/complete；读取图片原始尺寸需要用 Image 解码它的 src。",
        ],
        "ex": [("把按钮名从 spot 改成 point。", "同步修改 name 与探测文本里的前缀。", "name=\"point\"")],
    },
    {
        "t": "setCustomValidity 自定义校验消息",
        "level": "advanced",
        "obj": "用 setCustomValidity 写入业务级错误，并读取 validity 状态。",
        "pre": ["表单验证：required、pattern 与 constraint API", "表单错误提示的展示"],
        "con": ["setCustomValidity", "validity.customError", "validationMessage", "willValidate", "实时校验"],
        "explain": "约束校验只能表达格式类规则，业务规则要靠 `setCustomValidity(message)`。传非空字符串会把控件置为 `customError` 无效状态，`validationMessage` 随之变成这句话；传空字符串清除。清除后浏览器仍会继续检查 `required`/`pattern` 等原生约束，所以自定义消息必须每次重新判断，不能只在初始化时设一次。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>自定义校验</title></head>
<body>
  <form id="reg">
    <p><label for="code">邀请码</label>
      <input id="code" name="code" value="AB" required autocomplete="off"></p>
    <p id="msg" aria-live="polite"></p>
    <p><button type="submit">注册</button></p>
  </form>
  <p id="state">等待探测</p>
  <script>
    var code = document.getElementById('code');
    var msg = document.getElementById('msg');
    function validate() {
      code.setCustomValidity('');
      if (code.value !== 'WF2026') {
        code.setCustomValidity('邀请码必须是 WF2026');
      }
      msg.textContent = code.validationMessage || '校验通过';
      document.getElementById('state').textContent =
        'valid=' + code.validity.valid +
        ' / customError=' + code.validity.customError +
        ' / willValidate=' + code.willValidate;
    }
    code.addEventListener('input', validate);
    validate();
  </script>
</body>
</html>''',
        "out": "初始值为 AB，提示行显示“邀请码必须是 WF2026”，探测行显示 valid=false / customError=true；把输入改成 WF2026 后提示变成“校验通过”，探测行变成 valid=true / customError=false。",
        "pit": [
            "设置自定义消息后忘记清除，即使输入已经正确也永远不会通过。",
            "自定义消息不会自动显示在页面上，需要自己渲染到 aria-live 区域。",
            "对 readonly 或 disabled 控件设置自定义消息不会参与校验。",
        ],
        "ex": [("把合法邀请码改成 WF-2026。", "同时修改比较字符串与提示文字。", "code.setCustomValidity('邀请码必须是 WF-2026');")],
    },
    {
        "t": "textarea 尺寸、换行与选区 API",
        "level": "intermediate",
        "obj": "控制多行文本的行列与换行方式，并用 selectionStart/End 读取选区。",
        "pre": ["表单控件进阶：select、textarea、range", "表单字符计数与实时反馈"],
        "con": ["textarea", "rows/cols", "wrap", "maxlength", "setSelectionRange"],
        "explain": "`rows`/`cols` 决定可见行数与字符宽度，`wrap=\"soft\"` 只在显示时折行、提交的文本不带额外换行，`hard` 才会插入换行符。`maxlength` 限制的是字符数而不是字节数。选区用 `selectionStart`/`selectionEnd` 读取，也可以用 `setSelectionRange` 主动设置，常用于插入模板或高亮错误片段。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>textarea 选区</title></head>
<body>
  <p><label for="note">备注</label></p>
  <textarea id="note" rows="3" cols="30" wrap="soft" maxlength="60">第一行
第二行</textarea>
  <p id="snippet">选中：第一行</p>
  <p id="state">等待探测</p>
  <script>
    var note = document.getElementById('note');
    function report() {
      var picked = note.value.slice(note.selectionStart, note.selectionEnd).split('\\n').join('⏎');
      document.getElementById('snippet').textContent = '选中：' + picked;
      document.getElementById('state').textContent =
        'len=' + note.value.length +
        ' / sel=' + note.selectionStart + '-' + note.selectionEnd +
        ' / rows=' + note.rows + ' / cols=' + note.cols +
        ' / wrap=' + note.wrap + ' / maxlength=' + note.maxLength;
    }
    note.addEventListener('select', report);
    note.addEventListener('input', report);
    note.focus();
    note.setSelectionRange(0, 3);
    report();
  </script>
</body>
</html>''',
        "out": "页面显示三行高、30 字符宽的备注框，内容为两行文字；初始高亮“第一行”，状态行为“len=7 / sel=0-3 / rows=3 / cols=30 / wrap=soft / maxlength=60”。全选后状态变为 sel=0-7，选中提示变成“选中：第一行⏎第二行”。",
        "pit": [
            "rows/cols 只是建议尺寸，CSS 的 width/height 会覆盖它们。",
            "soft 换行不会把折行写进提交值，需要原文换行时不要依赖它。",
            "maxlength 按 UTF-16 码元计数，emoji 可能算两个字符。",
        ],
        "ex": [("把备注框改成 5 行。", "只改 rows。", "<textarea id=\"note\" rows=\"5\" cols=\"30\">")],
    },
    {
        "t": "formdata 事件与 FormData 迭代",
        "level": "advanced",
        "obj": "在 formdata 事件里增删提交数据，并遍历结果。",
        "pre": ["表单与后端交互的结构", "表单提交方法：GET 与 POST"],
        "con": ["formdata 事件", "FormData", "append/set", "forEach", "离线提交"],
        "explain": "提交时浏览器会先构造一份 `FormData`，并在表单上派发 `formdata` 事件。监听它可以追加字段（如来源标记）或改写已有值，适合在离线运行时补上本地生成的元数据。`FormData.forEach` 按插入顺序遍历键值，`set` 会替换同名字段但保持它的位置。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>formdata 事件</title></head>
<body>
  <form id="order" action="#done">
    <p><label for="item">商品</label><input id="item" name="item" value="离线键盘"></p>
    <p><label for="count">数量</label><input id="count" name="count" type="number" value="2"></p>
    <p><button type="submit" id="go">提交</button></p>
  </form>
  <p id="state">尚未提交</p>
  <script>
    var form = document.getElementById('order');
    form.addEventListener('submit', function (event) {
      event.preventDefault();
      new FormData(form);
    });
    form.addEventListener('formdata', function (event) {
      var data = event.formData;
      data.append('source', 'offline-ide');
      data.set('count', String(Number(data.get('count')) * 2));
      var pairs = [];
      data.forEach(function (value, key) { pairs.push(key + '=' + value); });
      document.getElementById('state').textContent = '提交数据：' + pairs.join('&');
    });
  </script>
</body>
</html>''',
        "out": "表单显示商品“离线键盘”和数量 2；点击“提交”后状态行显示“提交数据：item=离线键盘&count=4&source=offline-ide”，说明脚本把数量翻倍并追加了来源字段。",
        "pit": [
            "submit 被 preventDefault 取消后不会继续构造数据；离线演示中显式 new FormData(form) 仍会派发 formdata 事件。",
            "append 会追加重复键，想覆盖必须用 set。",
            "在事件外修改 FormData 实例不会影响提交内容。",
        ],
        "ex": [("再追加一个 channel=local 字段。", "在 append source 之后添加。", "data.append('channel', 'local');")],
    },
    {
        "t": "requestSubmit 与提交事件取消",
        "level": "advanced",
        "obj": "用 requestSubmit 触发真实提交流程，并区分 submitter。",
        "pre": ["表单按钮与提交：button 类型与进入点", "表单提交方法：GET 与 POST"],
        "con": ["form.requestSubmit", "SubmitEvent.submitter", "preventDefault", "校验参与", "submit 事件"],
        "explain": "`form.submit()` 直接提交、跳过校验与 `submit` 事件；`form.requestSubmit()` 则走完整流程：执行约束校验、派发可取消的 `submit` 事件，并可传入一个提交按钮作为 `submitter`。在离线运行时里，通常用 `requestSubmit` 接管提交以做本地校验，再用 `preventDefault` 阻止真正的页面跳转。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>requestSubmit</title></head>
<body>
  <form id="draft" action="#saved">
    <p><label for="text">内容</label><input id="text" name="text" value="草稿内容"></p>
    <button type="submit" id="native">原生提交</button>
  </form>
  <p><button type="button" id="programmatic">脚本提交</button></p>
  <p id="state">等待操作</p>
  <script>
    var form = document.getElementById('draft');
    var native = document.getElementById('native');
    var log = [];
    function render() {
      document.getElementById('state').textContent = log.join(' → ');
    }
    form.addEventListener('submit', function (event) {
      event.preventDefault();
      log.push('submit(' + (event.submitter ? event.submitter.id : 'none') + ')');
      render();
    });
    document.getElementById('programmatic').addEventListener('click', function () {
      log.push('click(programmatic)');
      form.requestSubmit(native);
    });
  </script>
</body>
</html>''',
        "out": "点击“脚本提交”后状态行显示“click(programmatic) → submit(native)”；再点“原生提交”后追加一段“submit(native)”，说明两次都走了同一套 submit 事件和 submitter 信息。",
        "pit": [
            "form.submit() 不会触发 submit 事件，用它代替 requestSubmit 会跳过拦截逻辑。",
            "requestSubmit 里的按钮必须是该表单内的提交按钮，否则抛错。",
            "忘记 preventDefault 时页面会真的导航到 action 地址。",
        ],
        "ex": [("再触发一次不带按钮的 requestSubmit。", "在脚本末尾加 setTimeout 调用 form.requestSubmit()。", "setTimeout(function () { form.requestSubmit(); }, 0);")],
    },
    {
        "t": "input type=number 步进与 valueAsNumber",
        "level": "intermediate",
        "obj": "用 stepUp/stepDown 与 valueAsNumber 处理数值输入。",
        "pre": ["表单数字与范围约束", "表单验证：required、pattern 与 constraint API"],
        "con": ["valueAsNumber", "stepUp", "stepDown", "stepMismatch", "min/max"],
        "explain": "数字输入框的字符串值要用 `valueAsNumber` 转成数字，空值或非法输入时它是 `NaN`。`stepUp()`/`stepDown()` 按 `step` 调整到相邻的合法步进值，并遵守 `min`/`max`。手写不符合步进的值会得到 `validity.stepMismatch`，浏览器不会自动帮你四舍五入。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>数字步进</title></head>
<body>
  <form id="st">
    <p><label for="n">数量（步进 3，范围 0-20）</label></p>
    <p><input id="n" name="n" type="number" value="6" min="0" max="20" step="3"></p>
    <p><button type="button" id="up">+3</button> <button type="button" id="down">-3</button></p>
  </form>
  <p id="state">等待探测</p>
  <script>
    var n = document.getElementById('n');
    function report() {
      document.getElementById('state').textContent =
        'value=' + n.value +
        ' / asNumber=' + n.valueAsNumber +
        ' / valid=' + n.validity.valid +
        ' / stepMismatch=' + n.validity.stepMismatch;
    }
    document.getElementById('up').addEventListener('click', function () { n.stepUp(); report(); });
    document.getElementById('down').addEventListener('click', function () { n.stepDown(); report(); });
    n.addEventListener('input', report);
    report();
  </script>
</body>
</html>''',
        "out": "输入框初始显示 6，状态行为“value=6 / asNumber=6 / valid=true / stepMismatch=false”；点“+3”变成 9，点两次“-3”变成 3；手动输入 7 后状态变为 valid=false / stepMismatch=true。",
        "pit": [
            "空输入框的 valueAsNumber 是 NaN，直接参与运算会得到 NaN。",
            "stepUp 从非法值开始时会先对齐到最近的合法步进值，结果可能与“加一个 step”不同。",
            "type=number 不能阻止用户输入字母，服务端仍要再校验。",
        ],
        "ex": [("把步进改成 5，并让按钮显示 +5/-5。", "同步修改 step 与按钮文字。", "step=\"5\"")],
    },
    {
        "t": "ruby 注音标注与 rp 回退",
        "level": "intermediate",
        "obj": "用 ruby/rt 给汉字加注音，并理解 rp 的回退作用。",
        "pre": ["文本强调：strong、em、br 与 hr 语义", "语言与方向：lang 与 dir"],
        "con": ["ruby", "rt", "rp", "注音", "东亚排版"],
        "explain": "`<ruby>` 把一个或多个字符与其注音绑定，注音写在 `<rt>` 里。`<rp>` 是给不支持 ruby 的浏览器准备的括号回退，支持 ruby 的浏览器会用 UA 样式把它隐藏。注音是排版信息而非正文，读屏默认只读基字，因此基字本身要写完整。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>ruby 注音</title></head>
<body>
  <p>日语：<ruby id="jp">漢字<rp>(</rp><rt>かんじ</rt><rp>)</rp></ruby></p>
  <p>中文：<ruby id="zh">离线<rt>lí xiàn</rt></ruby></p>
  <p id="state">等待探测</p>
  <script>
    var zh = document.getElementById('zh');
    var rts = zh.querySelectorAll('rt');
    var rps = document.getElementById('jp').querySelectorAll('rp');
    document.getElementById('state').textContent =
      'ruby 数=' + document.querySelectorAll('ruby').length +
      ' / rt 数=' + rts.length +
      ' / 注音=' + rts[0].textContent +
      ' / rp 数=' + rps.length +
      ' / rp 显示=' + getComputedStyle(rps[0]).display +
      ' / rt 显示=' + getComputedStyle(rts[0]).display;
  </script>
</body>
</html>''',
        "out": "“漢字”上方显示“かんじ”，“离线”上方显示“lí xiàn”；探测行输出“ruby 数=2 / rt 数=1 / 注音=lí xiàn / rp 数=2 / rp 显示=none / rt 显示=ruby-text”。",
        "pit": [
            "rt 里再嵌 span 会被当成注音内容的一部分，某些引擎排版会错位。",
            "只有一个字的注音也用 ruby，不要用上标 sup 冒充注音。",
            "rp 的括号必须成对且紧贴 rt，否则回退文本会重复。",
        ],
        "ex": [("给“注音”二字加 ruby 与 zhù yīn。", "照抄第二行结构。", "<ruby>注音<rt>zhù yīn</rt></ruby>")],
    },
    {
        "t": "bdi 与 bdo 的双向文本隔离",
        "level": "advanced",
        "obj": "用 bdi 隔离未知方向的用户名，用 bdo 强制指定方向。",
        "pre": ["语言与方向：lang 与 dir", "HTML 全局属性总览"],
        "con": ["bdi", "bdo", "unicode-bidi", "dir=auto", "双向文本"],
        "explain": "混排阿拉伯语、希伯来语与拉丁字母时，文本方向会影响标点位置。`<bdi>` 会把内容与周围文本隔离（`unicode-bidi: isolate`），并根据内容自动判断方向，适合插入用户昵称这类方向未知的片段。`<bdo dir=\"rtl\">` 则强制覆盖方向（computed 值为 `isolate-override`，即隔离后再反转），常用于演示或特殊排版。`dir=\"auto\"` 让浏览器按第一个强方向字符决定方向。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>双向文本</title></head>
<body dir="ltr">
  <p>登录用户：<bdi id="user">أحمد</bdi> 已上线</p>
  <p>昵称：<bdi id="nick">@offline</bdi> 说：你好</p>
  <p>强制反向：<bdo dir="rtl" id="forced">abc 123</bdo></p>
  <p>自动方向：<span dir="auto" id="auto">שלום</span></p>
  <p id="state">等待探测</p>
  <script>
    function style(el) {
      var cs = getComputedStyle(el);
      return cs.unicodeBidi + '/' + cs.direction;
    }
    document.getElementById('state').textContent =
      'bdi 数=' + document.querySelectorAll('bdi').length +
      ' / user=' + style(document.getElementById('user')) +
      ' / bdo=' + style(document.getElementById('forced')) +
      ' / auto=' + style(document.getElementById('auto'));
  </script>
</body>
</html>''',
        "out": "第一行阿拉伯语用户名独立成段，标点不会跑到句子另一侧；探测行输出“bdi 数=2 / user=isolate/rtl / bdo=isolate-override/rtl / auto=isolate/rtl”。",
        "pit": [
            "直接把用户昵称拼进句子而不包 bdi，会让整句标点位置跳变。",
            "bdi 的 computed direction 会根据内容自动变成 rtl，隔离靠的是 unicode-bidi，不是 direction。",
            "bdo 在浏览器里的 computed unicode-bidi 是 isolate-override（不是 bidi-override），会强行反转内容，不要用于普通正文。",
        ],
        "ex": [("给昵称换成希伯来语并保留 bdi。", "把 id=\"nick\" 的文本替换即可。", "<bdi id=\"nick\">דנה</bdi>")],
    },
    {
        "t": "mark 高亮与检索命中",
        "level": "intermediate",
        "obj": "用 mark 标注检索命中的文本，并区分语义高亮与装饰性背景。",
        "pre": ["文本强调：strong、em、br 与 hr 语义", "HTML 与 CSS/JS 的引入方式"],
        "con": ["mark", "检索高亮", "innerHTML 安全", "默认背景", "命中计数"],
        "explain": "`<mark>` 表示因为*上下文相关*而需要突出的文本，最典型的场景是搜索命中。它与 `<em>`（强调语气）、`<strong>`（重要性）语义不同，浏览器默认给它黄色背景。渲染命中时先把纯文本按关键词切开再拼接元素，比直接拼 innerHTML 更安全，也方便统计命中次数。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>mark 高亮</title></head>
<body>
  <p id="text">离线优先意味着优先使用本地能力，离线不是退路。</p>
  <p>命中 <mark id="hit">离线</mark> 共 <span id="count">0</span> 处</p>
  <p id="wrapped"></p>
  <p id="state">等待探测</p>
  <script>
    var text = document.getElementById('text');
    var keyword = '离线';
    var parts = text.textContent.split(keyword);
    var target = document.getElementById('wrapped');
    parts.forEach(function (part, index) {
      target.appendChild(document.createTextNode(part));
      if (index < parts.length - 1) {
        var mark = document.createElement('mark');
        mark.textContent = keyword;
        target.appendChild(mark);
      }
    });
    var marks = target.querySelectorAll('mark');
    document.getElementById('count').textContent = marks.length;
    var markStyle = getComputedStyle(marks[0]);
    document.getElementById('state').textContent =
      'mark 数=' + marks.length +
      ' / 背景=' + markStyle.backgroundColor +
      ' / 与正文背景不同=' + (markStyle.backgroundColor !== getComputedStyle(text).backgroundColor);
  </script>
</body>
</html>''',
        "out": "第三行重复显示同一句话，但两处“离线”被黄色背景高亮；命中计数显示 2；探测行输出“mark 数=2 / 背景=rgb(255, 255, 0) / 与正文背景不同=true”。",
        "pit": [
            "用 mark 做纯装饰背景会污染语义，装饰请用 span + CSS。",
            "拼字符串 innerHTML 会把用户输入当标签解析，可能注入脚本。",
            "关键词出现在标签属性里时纯文本替换会破坏 HTML，应只处理文本节点。",
        ],
        "ex": [("把关键词换成“本地”并观察命中数。", "只改 keyword 变量。", "var keyword = '本地';")],
    },
    {
        "t": "del 与 ins 的修订记录语义",
        "level": "intermediate",
        "obj": "用 del/ins 表示被删除与被插入的内容，并给出修改出处与时间。",
        "pre": ["引用与出处：blockquote 与 cite", "时间与机器可读数据：time"],
        "con": ["del", "ins", "cite", "datetime", "HTMLModElement"],
        "explain": "`<del>` 表示已删除的内容，`<ins>` 表示新增的内容，两者都支持 `cite`（说明修改依据的地址）与 `datetime`（修改时间）。它们属于 `HTMLModElement`，脚本里可以读 `element.dateTime`。浏览器默认给 del 删除线、给 ins 下划线，但这只是视觉提示，真正的语义在元素本身。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>修订记录</title></head>
<body>
  <p id="doc">
    版本 2.2：<del cite="#changelog-21" datetime="2026-09-01">每 30 分钟自动联网同步</del>
    <ins cite="#changelog-22" datetime="2026-10-22">每 30 分钟检查本地缓存</ins>
  </p>
  <p id="state">等待探测</p>
  <script>
    var del = document.querySelector('del');
    var ins = document.querySelector('ins');
    document.getElementById('state').textContent =
      'del 线=' + getComputedStyle(del).textDecorationLine +
      ' / ins 线=' + getComputedStyle(ins).textDecorationLine +
      ' / ins.cite=' + ins.getAttribute('cite') +
      ' / ins.dateTime=' + ins.dateTime +
      ' / del.dateTime 非空=' + (del.dateTime !== '');
  </script>
</body>
</html>''',
        "out": "页面上“每 30 分钟自动联网同步”带删除线，“每 30 分钟检查本地缓存”带下划线；探测行输出“del 线=line-through / ins 线=underline / ins.cite=#changelog-22 / ins.dateTime=2026-10-22 / del.dateTime 非空=true”。",
        "pit": [
            "del/ins 表示修订，不是“旧价格”这类非文本修改场景，价格划掉要用 s。",
            "datetime 必须写合法的日期时间字符串，否则脚本读到的是原样字符串而无意义。",
            "嵌套使用 del 包 ins 会让差异无法阅读，修订应逐句标注。",
        ],
        "ex": [("把新增内容的修改日期改到 2026-11-01。", "只改 ins 的 datetime。", "<ins cite=\"#changelog-23\" datetime=\"2026-11-01\">")],
    },
    {
        "t": "s 与 small 的语义边界",
        "level": "intermediate",
        "obj": "区分 s（不再准确）与 small（细则说明）与 del（删除）。",
        "pre": ["del 与 ins 的修订记录语义", "上标与下标：sup 与 sub"],
        "con": ["s", "small", "不再准确", "细则文本", "日期属性归属"],
        "explain": "`<s>` 表示内容在当下已不准确（如原价、售罄），但不代表被删除，所以它*没有* `datetime`/`cite` 属性——那是 del/ins 的。`<small>` 表示旁注与细则（免责声明、版权），浏览器默认把它渲染成更小的字号。很多开发者把 s 与 del 混用，导致修订语义与价格语义纠缠。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>s 与 small</title></head>
<body>
  <p>原价 <s id="old">¥199</s> 现价 ¥129</p>
  <p><small id="note">价格仅在离线工作区内有效，不含税费。</small></p>
  <p id="state">等待探测</p>
  <script>
    var old = document.getElementById('old');
    var note = document.getElementById('note');
    var bodySize = parseFloat(getComputedStyle(document.body).fontSize);
    var noteSize = parseFloat(getComputedStyle(note).fontSize);
    document.getElementById('state').textContent =
      's 线=' + getComputedStyle(old).textDecorationLine +
      ' / s.dateTime 属性不存在=' + (old.dateTime === undefined) +
      ' / small 更小=' + (noteSize < bodySize) +
      ' / 字号=' + noteSize.toFixed(2) + '<' + bodySize.toFixed(2);
  </script>
</body>
</html>''',
        "out": "页面上“¥199”带删除线，“¥129”正常显示，下面一行细则以更小字号呈现；探测行输出“s 线=line-through / s.dateTime 属性不存在=true / small 更小=true / 字号=13.33<16.00”。",
        "pit": [
            "给 s 加 datetime 属性无效，s 元素不实现 HTMLModElement。",
            "把正文整段放进 small 会让全站字号失控，small 只用于旁注。",
            "用 s 表达“已删除”会在读屏里读成“不再准确”，语义不符。",
        ],
        "ex": [("把细则改成版权声明。", "替换 small 内文本。", "<small id=\"note\">© 2026 WebForge 文档组</small>")],
    },
    {
        "t": "data value 机器可读取值",
        "level": "intermediate",
        "obj": "用 data 元素为展示文本绑定机器可读的值。",
        "pre": ["时间与机器可读数据：time", "HTML5 数据属性：data-* 与前端钩子"],
        "con": ["data", "value 属性", "机器可读", "与 time 的区别", "商品编码"],
        "explain": "`<data value=\"…\">` 让可见文本与机器可读的值分开：页面上显示“离线键盘”，脚本与爬虫读到 `WF-1001`。它适合商品编码、分类 ID 这类场景；日期时间请用 `<time datetime>`，那个有专门的时间语义。`data.value` 属性直接反射 `value`。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>data 元素</title></head>
<body>
  <ul id="catalog">
    <li><data id="sku1" value="WF-1001">离线键盘</data></li>
    <li><data id="sku2" value="WF-1002">离线鼠标</data></li>
  </ul>
  <p id="state">等待探测</p>
  <script>
    var items = document.querySelectorAll('data');
    var values = Array.prototype.map.call(items, function (el) { return el.value; });
    document.getElementById('state').textContent =
      'items=' + items.length +
      ' / values=' + values.join(',') +
      ' / 首个文本=' + items[0].textContent +
      ' / 显示方式=' + getComputedStyle(items[0]).display;
  </script>
</body>
</html>''',
        "out": "列表显示“离线键盘”“离线鼠标”两项；探测行输出“items=2 / values=WF-1001,WF-1002 / 首个文本=离线键盘 / 显示方式=inline”。",
        "pit": [
            "data 的显示文本不受 value 影响，两者需要自己保持一致。",
            "日期/时间不要用 data 冒充，time 才有时间语义与可解析的 datetime。",
            "value 缺失时 data.value 返回空字符串，容易在编码映射里得到空 id。",
        ],
        "ex": [("再加一个配件“离线支架 / WF-2001”。", "复制 li 并改 id、value 与文本。", "<data id=\"sku3\" value=\"WF-2001\">离线支架</data>")],
    },
    {
        "t": "wbr 长词断行与 overflow-wrap",
        "level": "advanced",
        "obj": "用 wbr 给出可选换行点，并配合 overflow-wrap 处理超长串。",
        "pre": ["HTML 中的空白与格式化", "HTML 视口单位与全屏区块"],
        "con": ["wbr", "可选换行", "overflow-wrap", "长路径", "容器宽度"],
        "explain": "`<wbr>` 表示浏览器*可以*在此处换行，但不是强制换行（那才是 `<br>`）。它适合长路径、UUID、URL 片段：容器窄时在标记处断开，宽时保持一整行。对没有标记点的超长单词，还需要 CSS 的 `overflow-wrap: break-word` 或 `anywhere` 才能避免溢出。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>wbr 断行</title>
  <style>
    #path { width: 150px; border: 1px solid #c8cdd4; }
    #long { width: 150px; border: 1px solid #c8cdd4; }
  </style>
</head>
<body>
  <p id="path">offline/<wbr>workspace/<wbr>assets/<wbr>content/<wbr>examples.json</p>
  <p id="long">SupercalifragilisticexpialidociousSupercalifragilisticexpialidocious</p>
  <p id="state">等待探测</p>
  <script>
    var path = document.getElementById('path');
    var long = document.getElementById('long');
    var before = getComputedStyle(long).overflowWrap;
    long.style.overflowWrap = 'break-word';
    var after = getComputedStyle(long).overflowWrap;
    document.getElementById('state').textContent =
      'wbr 数=' + path.querySelectorAll('wbr').length +
      ' / 路径高=' + Math.round(path.getBoundingClientRect().height) +
      ' / wrap 前=' + before + ' / wrap 后=' + after;
  </script>
</body>
</html>''',
        "out": "150px 宽的框里，长路径在斜杠处折成多行（高度明显超过一行）；超长单词在加上 overflow-wrap 后也能折行，不会横向溢出；探测行输出“wbr 数=4 / 路径高=… / wrap 前=normal / wrap 后=break-word”。",
        "pit": [
            "把 wbr 当 br 用会在宽屏里也断行，破坏可读性。",
            "wbr 不能闭合，写成 </wbr> 是无效标签。",
            "没有 wbr 也没有 overflow-wrap 时，长串会把容器撑破并出现横向滚动条。",
        ],
        "ex": [("在 examples.json 之后再加一个可选断点。", "在末尾追加 wbr 与剩余文本。", "examples.json<wbr>.bak")],
    },
    {
        "t": "base 与相对 URL 解析",
        "level": "advanced",
        "obj": "用 base 改变文档基准地址，并理解相对链接如何解析。",
        "pre": ["链接与锚点：a 标签的 href 家族", "meta 标签与页面 SEO"],
        "con": ["base", "document.baseURI", "相对 URL", "URL 构造器", "单实例限制"],
        "explain": "`<base href>` 设置文档的基准地址，所有相对 URL（链接、图片、表单 action、脚本里的 `new URL(相对, document.baseURI)`）都以它为基准解析。一个文档只应有一个 base，且它必须出现在第一个使用 URL 的元素之前。它影响的是解析结果，不会自动发起请求。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>base 与相对 URL</title>
  <base id="base" href="#workspace/">
</head>
<body>
  <p><a id="rel" href="notes/today.html">今天的笔记</a></p>
  <p id="state">等待探测</p>
  <script>
    var link = document.getElementById('rel');
    var resolved = new URL('notes/today.html', document.baseURI);
    document.getElementById('state').textContent =
      'base 数=' + document.querySelectorAll('base').length +
      ' / baseURI 含锚点=' + (document.baseURI.indexOf('#workspace') >= 0) +
      ' / 解析 pathname=' + resolved.pathname +
      ' / a.href 已绝对化=' + link.href.endsWith('/notes/today.html') +
      ' / a.href 与解析一致=' + (link.href === resolved.href);
  </script>
</body>
</html>''',
        "out": "页面上“今天的笔记”链接指向同源的 `notes/today.html`；探测行输出“base 数=1 / baseURI 含锚点=true / 解析 pathname=/notes/today.html / a.href 已绝对化=true / a.href 与解析一致=true”。",
        "pit": [
            "多个 base 时只有第一个生效，第二个会被忽略且不会报错。",
            "base 写在要使用它的元素之后，那些元素仍按文档默认地址解析。",
            "把 base 指向外部地址会把所有相对资源变成外链，破坏离线约束。",
        ],
        "ex": [("把 base 改成 #docs/ 并观察解析结果。", "只改 href，注意探测仍成立。", "<base id=\"base\" href=\"#docs/\">")],
    },
    {
        "t": "translate 与 spellcheck 编辑语义",
        "level": "advanced",
        "obj": "用 translate 与 spellcheck 声明内容是否可翻译、是否做拼写检查。",
        "pre": ["语言与方向：lang 与 dir", "HTML 全局属性总览"],
        "con": ["translate", "spellcheck", "布尔属性反射", "品牌名保护", "编辑区"],
        "explain": "`translate=\"no\"` 告诉翻译工具不要翻译该元素的内容，适合品牌名、代码与命令。`spellcheck` 控制浏览器是否对可编辑内容做拼写检查，默认继承父元素。两者都是全局属性，脚本里读的是布尔属性 `element.translate` 与 `element.spellcheck`，写 `\"no\"` 在脚本里会变成 `false`。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>translate 与 spellcheck</title></head>
<body>
  <p id="brand" translate="no" spellcheck="false">WebForge 离线 IDE</p>
  <p id="code" translate="no"><code>webforge serve --offline</code></p>
  <p><label for="note">中文备注（不需要英文拼写检查）</label></p>
  <textarea id="note" spellcheck="true" lang="zh-CN" rows="2" cols="40">离线编辑器的拼写检查</textarea>
  <p id="state">等待探测</p>
  <script>
    var brand = document.getElementById('brand');
    var note = document.getElementById('note');
    document.getElementById('state').textContent =
      'brand.translate=' + brand.translate +
      ' / brand 属性=' + brand.getAttribute('translate') +
      ' / spellcheck=' + brand.spellcheck +
      ' / note.spellcheck=' + note.spellcheck +
      ' / note.lang=' + note.lang +
      ' / body.translate=' + document.body.translate;
  </script>
</body>
</html>''',
        "out": "品牌名与命令行保持原样不被翻译；探测行输出“brand.translate=false / brand 属性=no / spellcheck=false / note.spellcheck=true / note.lang=zh-CN / body.translate=true”。",
        "pit": [
            "translate 只对翻译工具有约束，不会阻止用户手动复制修改。",
            "spellcheck=\"false\" 写在不可编辑元素上没有实际效果。",
            "布尔属性写成 translate=\"false\" 仍然表示“不要翻译”，布尔语义只看属性存在与否。",
        ],
        "ex": [("让代码块也禁止拼写检查。", "在 code 的父元素上加 spellcheck=\"false\"。", "<p id=\"code\" translate=\"no\" spellcheck=\"false\">")],
    },
    {
        "t": "MathML 公式排版基础",
        "level": "advanced",
        "obj": "用 math/mrow/msup/mfrac 在 HTML 中直接排版数学公式。",
        "pre": ["上标与下标：sup 与 sub", "内联 SVG 图标系统"],
        "con": ["math", "mrow", "msup", "mfrac", "display=block"],
        "explain": "HTML 支持内嵌 MathML：`<math>` 是根元素，`<mi>` 是标识符、`<mn>` 是数字、`<mo>` 是运算符，`<mrow>` 把子项组合成一行，`<msup>` 生成上标，`<mfrac>` 生成分式。`display=\"block\"` 让公式独立成块并居中渲染，现代浏览器的 computed display 为 `block math`。验证分式排版应检查分子在分母上方；内联数学会缩小分子、分母，整个分式未必高于普通文本行。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>MathML 公式</title></head>
<body>
  <math id="einstein" display="block">
    <mrow>
      <mi>E</mi><mo>=</mo><mi>m</mi><msup><mi>c</mi><mn>2</mn></msup>
    </mrow>
  </math>
  <p>平均值：<math id="avg"><mfrac><mrow><mn>1</mn></mrow><mi>n</mi></mfrac></math> 求和</p>
  <p id="state">等待探测</p>
  <script>
    var block = document.getElementById('einstein');
    var sup = block.querySelector('msup');
    var avg = document.getElementById('avg');
    var frac = avg.querySelector('mfrac');
    document.getElementById('state').textContent =
      'msup 存在=' + (sup !== null) +
      ' / 次幂=' + sup.querySelector('mn').textContent +
      ' / 块级显示=' + getComputedStyle(block).display +
      ' / 分式高=' + Math.round(frac.getBoundingClientRect().height) +
      ' / 公式宽=' + Math.round(block.getBoundingClientRect().width);
  </script>
</body>
</html>''',
        "out": "页面上出现居中的 E=mc² 公式（c 带 2 次幂），下面一行里有一个 1/n 的分式，分子 1 位于分母 n 上方；探测行输出“msup 存在=true / 次幂=2 / 块级显示=block math / 分式高=… / 公式宽=…”。",
        "pit": [
            "用 sup 手排分式只能得到一行的伪公式，真实分式要用 mfrac。",
            "msup 的第二个子元素才是指数，第一个是底数，顺序写反公式就错。",
            "MathML 元素不能混写 HTML 的 div 布局，结构只能用 mrow 等数学容器。",
        ],
        "ex": [("把分式分子改成 a+b。", "用 mrow 包住 mi、mo、mi。", "<mfrac><mrow><mi>a</mi><mo>+</mo><mi>b</mi></mrow><mi>n</mi></mfrac>")],
    },
    {
        "t": "picture 与 source media 艺术指导",
        "level": "advanced",
        "obj": "用 picture 按视口条件切换不同裁剪的图片。",
        "pre": ["响应式图片：srcset 与 sizes", "图片格式选择：webp 与 avif"],
        "con": ["picture", "source media", "艺术指导", "currentSrc", "naturalWidth"],
        "explain": "`<picture>` 里的 `<source media=\"…\">` 按媒体查询选择图片，这叫艺术指导：不同宽度用不同裁剪比例，而不只是分辨率不同。浏览器按顺序取第一个命中的 source，都不命中时回退到内部 `<img>`。`<img>` 是必需的：它提供 `src`、`alt` 与尺寸，`picture` 本身不显示任何内容。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>picture 艺术指导</title></head>
<body>
  <picture id="art">
    <source media="(min-width: 600px)"
      srcset="data:image/svg+xml,%3Csvg%20xmlns=%27http://www.w3.org/2000/svg%27%20width=%27300%27%20height=%2760%27%3E%3Crect%20width=%27300%27%20height=%2760%27%20fill=%27%231a73e8%27/%3E%3Ctext%20x=%27150%27%20y=%2737%27%20font-size=%2718%27%20text-anchor=%27middle%27%20fill=%27%23fff%27%3E宽屏裁剪%3C/text%3E%3C/svg%3E">
    <source media="(min-width: 300px)"
      srcset="data:image/svg+xml,%3Csvg%20xmlns=%27http://www.w3.org/2000/svg%27%20width=%27200%27%20height=%2760%27%3E%3Crect%20width=%27200%27%20height=%2760%27%20fill=%27%238ab4f8%27/%3E%3Ctext%20x=%27100%27%20y=%2737%27%20font-size=%2716%27%20text-anchor=%27middle%27%20fill=%27%23113%27%3E窄屏裁剪%3C/text%3E%3C/svg%3E">
    <img id="fallback" width="120" height="60" alt="响应式示意图"
      src="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%27120%27 height=%2760%27%3E%3Crect width=%27120%27 height=%2760%27 fill=%27%23c8cdd4%27/%3E%3C/svg%3E">
  </picture>
  <p id="state">等待探测</p>
  <script>
    var img = document.getElementById('fallback');
    function report() {
      var sources = document.querySelectorAll('#art source');
      document.getElementById('state').textContent =
        'source 数=' + sources.length +
        ' / 首个 media=' + sources[0].media +
        ' / 实际宽=' + img.naturalWidth +
        ' / 命中宽屏=' + (img.naturalWidth === 300) +
        ' / 已加载=' + (img.complete && img.naturalWidth > 0);
    }
    if (img.complete) report();
    img.addEventListener('load', report);
  </script>
</body>
</html>''',
        "out": "宽视口下显示蓝色“宽屏裁剪”横图，缩小到 600px 以下换成浅蓝“窄屏裁剪”；探测行输出“source 数=2 / 首个 media=(min-width: 600px) / 实际宽=300 / 命中宽屏=true / 已加载=true”。",
        "pit": [
            "source 顺序即优先级；若把 min-width:300px 放在 min-width:600px 之前，宽屏也会先命中窄屏裁剪。",
            "picture 里必须有一个 img，否则什么都不会显示。",
            "source 的 srcset 也需要 data: 或同源地址，指向外部会破坏离线要求。",
        ],
        "ex": [("把窄屏裁剪的最小宽度改成 400px。", "只改第二个 source 的 media。", "media=\"(min-width: 400px)\"")],
    },
    {
        "t": "sup 与 sub 的表达式组合",
        "level": "intermediate",
        "obj": "在化学式与幂表达式中正确组合上标与下标。",
        "pre": ["上标与下标：sup 与 sub", "MathML 公式排版基础"],
        "con": ["sup", "sub", "vertical-align", "化学式", "离子电荷"],
        "explain": "`<sup>` 与 `<sub>` 用 UA 样式 `vertical-align: super` / `sub` 把内容抬升或下沉，并自动缩小字号，适合短表达式（H₂O、a²）。硫酸根这类同时带下标与电荷的写法要按“先原子下标、后电荷上标”的顺序书写。表达式较长、需要真实分式或根式时，应该改用 MathML。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>上下标组合</title></head>
<body>
  <p id="water">水分子：H<sub>2</sub>O，甲烷：CH<sub>4</sub></p>
  <p id="pythagoras">勾股定理：a<sup>2</sup> + b<sup>2</sup> = c<sup>2</sup></p>
  <p id="sulfate">硫酸根离子：SO<sub>4</sub><sup>2−</sup></p>
  <p id="state">等待探测</p>
  <script>
    var subs = document.querySelectorAll('sub');
    var sups = document.querySelectorAll('sup');
    var sulfate = document.getElementById('sulfate');
    document.getElementById('state').textContent =
      'sub 数=' + subs.length +
      ' / sup 数=' + sups.length +
      ' / sub 对齐=' + getComputedStyle(subs[0]).verticalAlign +
      ' / sup 对齐=' + getComputedStyle(sups[0]).verticalAlign +
      ' / 硫酸根=' + sulfate.textContent.split(/\\s+/).join('') +
      ' / 电荷在上=' + (sulfate.querySelector('sub').compareDocumentPosition(sulfate.querySelector('sup')) & Node.DOCUMENT_POSITION_FOLLOWING ? 'sub 在前' : 'sup 在前');
  </script>
</body>
</html>''',
        "out": "三行公式分别显示 H₂O、a²+b²=c² 与 SO₄²⁻；探测行输出“sub 数=3 / sup 数=4 / sub 对齐=sub / sup 对齐=super / 硫酸根=硫酸根离子：SO42− / 电荷在上=sub 在前”。",
        "pit": [
            "在 sup 里用 CSS 改字号会与 UA 缩小叠加，字号可能过小。",
            "离子电荷的减号要用字符 − 或 &minus;，用连字符视觉上偏小。",
            "长公式全靠 sup/sub 拼装会失去语义与无障碍朗读，应使用 MathML。",
        ],
        "ex": [("补一个碳酸根 CO₃²⁻。", "照抄硫酸根结构。", "<p>碳酸根：CO<sub>3</sub><sup>2−</sup></p>")],
    },
    {
        "t": "object 嵌入文档与回退内容",
        "level": "advanced",
        "obj": "用 object 嵌入一份文档，并用 contentDocument 验证内嵌结果。",
        "pre": ["内联 SVG 图标系统", "内联框架与嵌入内容：iframe"],
        "con": ["object", "data/type", "contentDocument", "回退内容", "不透明源"],
        "explain": "`<object>` 可以嵌入另一份文档或资源，`data` 指向资源地址，`type` 声明 MIME 类型。与 `<img>` 不同，`object` 内的子元素是它的*回退内容*：外层资源无法加载时才会显示，也可以作为无障碍说明。只有同源资源才能通过 `contentDocument` 读到内嵌文档的 DOM；`data:` 地址是不透明源，读不到，所以下面用运行时生成的 `Blob` 地址（继承当前页面的源）来演示。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>object 嵌入文档</title></head>
<body>
  <object id="figure" type="text/html" width="240" height="80">
    <p>当前环境无法显示内嵌文档，请阅读文字说明。</p>
  </object>
  <p id="state">等待探测</p>
  <script>
    var figure = document.getElementById('figure');
    var innerDoc = '<!doctype html><html><body><p id="inner">运行内联的 HTML 文档</p></body></html>';
    var url = URL.createObjectURL(new Blob([innerDoc], { type: 'text/html' }));
    function report() {
      var inner = figure.contentDocument;
      var note = inner ? inner.getElementById('inner') : null;
      document.getElementById('state').textContent =
        'type=' + figure.type +
        ' / data 是 Blob=' + (figure.data.indexOf('blob:') === 0) +
        ' / 内嵌根元素=' + (inner && inner.documentElement ? inner.documentElement.tagName.toLowerCase() : 'none') +
        ' / 内嵌文本=' + (note ? note.textContent : 'none') +
        ' / 回退段数=' + figure.querySelectorAll('p').length;
    }
    figure.addEventListener('load', report);
    figure.data = url;
  </script>
</body>
</html>''',
        "out": "页面上出现一个 240×80 的内嵌文档，里面显示“运行内联的 HTML 文档”；探测行输出“type=text/html / data 是 Blob=true / 内嵌根元素=html / 内嵌文本=运行内联的 HTML 文档 / 回退段数=1”。",
        "pit": [
            "object 的回退内容只在资源加载失败时显示，不能拿来当正常提示文字。",
            "data: 地址是不透明源，contentDocument 为 null；要读内嵌 DOM 必须同源（如 Blob）。",
            "把 object 当 img 用会失去图片的 alt 语义，纯图片优先用 img。",
        ],
        "ex": [("把内嵌文档的文本改成“内联文档已就绪”。", "修改 innerDoc 里的 p 文本。", "'<p id=\"inner\">内联文档已就绪</p>'")],
    },
    {
        "t": "embed 与 iframe srcdoc 内联文档",
        "level": "advanced",
        "obj": "用 srcdoc 内联一份完整文档，并与 embed 的插件式嵌入区分。",
        "pre": ["内联框架与嵌入内容：iframe", "object 嵌入 SVG 与回退内容"],
        "con": ["iframe srcdoc", "contentDocument", "embed", "同源内联", "title 属性"],
        "explain": "`<iframe srcdoc=\"…\">` 把一段 HTML 字符串直接当文档渲染，不需要任何外部文件，因此非常适合离线教学与隔离预览；它与父页面同源，脚本可以访问 `contentDocument`。`<embed>` 则是非 HTML 资源的插件式嵌入（如 SVG、PDF），没有文档 DOM 可操作，也不支持回退内容。`iframe` 必须有 `title` 以提供可访问名称。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>srcdoc 与 embed</title></head>
<body>
  <iframe id="frame" title="内联示例文档" width="260" height="70"
    srcdoc="<p id='inner'>srcdoc 渲染的内容</p>"></iframe>
  <embed id="emb" type="image/svg+xml" width="80" height="40" title="内联图标"
    src="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%2780%27 height=%2740%27%3E%3Ccircle cx=%2720%27 cy=%2720%27 r=%2716%27 fill=%27%231a73e8%27/%3E%3C/svg%3E">
  <p id="state">等待探测</p>
  <script>
    var frame = document.getElementById('frame');
    function report() {
      var doc = frame.contentDocument;
      var inner = doc && doc.getElementById('inner');
      document.getElementById('state').textContent =
        'srcdoc 同源可访=' + (doc !== null) +
        ' / 内部文本=' + (inner ? inner.textContent : 'none') +
        ' / frame.title=' + frame.title +
        ' / embed.type=' + document.getElementById('emb').type +
        ' / embed 标签=' + document.getElementById('emb').tagName.toLowerCase();
    }
    frame.addEventListener('load', report);
    setTimeout(report, 200);
  </script>
</body>
</html>''',
        "out": "上方是一个 260×70 的内嵌框，里面显示“srcdoc 渲染的内容”，右侧是一个 80×40 的蓝色圆点图标；探测行输出“srcdoc 同源可访=true / 内部文本=srcdoc 渲染的内容 / frame.title=内联示例文档 / embed.type=image/svg+xml / embed 标签=embed”。",
        "pit": [
            "srcdoc 的属性值里再写未转义的引号会截断属性，属性值内引号应改用单引号。",
            "embed 无法拿回退内容与 DOM，需要交互的嵌入请用 iframe。",
            "iframe 不写 title 时读屏只会读成“框架”，多个内嵌文档无法区分。",
        ],
        "ex": [("把 srcdoc 里的文本文改成“内联文档已加载”。", "只改 p 里的文字。", "srcdoc=\"<p id='inner'>内联文档已加载</p>\"")],
    },
    {
        "t": "iframe sandbox 的脚本与同源隔离",
        "level": "advanced",
        "obj": "用 sandbox 属性验证脚本被阻止与同源隔离。",
        "pre": ["embed 与 iframe srcdoc 内联文档", "安全基础：内容安全策略与 noopener"],
        "con": ["sandbox", "allow-scripts", "allow-same-origin", "不透明源", "contentDocument 为 null"],
        "explain": "`<iframe sandbox>` 不写任何允许项时，内嵌文档得到一个*不透明源*：不能读父页面的 DOM、不能执行脚本、也不能提交表单。父页面访问它的 `contentDocument` 会得到 `null`（因为跨源）。需要脚本时加 `allow-scripts`，但*不要同时*加 `allow-same-origin`，否则沙箱几乎失效。这个示例只演示“全部禁止”的最安全形态。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>sandbox 隔离</title></head>
<body>
  <iframe id="safe" title="受限内嵌文档" width="280" height="70" sandbox
    srcdoc="<p id='note'>沙箱内容不会执行脚本</p><script>parent.postMessage('脚本已运行', '*');</script>"></iframe>
  <p id="state">尚未收到任何消息</p>
  <script>
    window.__messages = 0;
    window.addEventListener('message', function (event) {
      window.__messages++;
      document.getElementById('state').textContent = '收到消息：' + event.data;
    });
    var frame = document.getElementById('safe');
    setTimeout(function () {
      if (window.__messages === 0) {
        document.getElementById('state').textContent =
          '未收到消息 / 沙箱标记=' + frame.hasAttribute('sandbox') +
          ' / 允许项=' + frame.sandbox.length +
          ' / 可访内嵌文档=' + (frame.contentDocument !== null);
      }
    }, 250);
  </script>
</body>
</html>''',
        "out": "上方是一个内嵌文档，里面只显示出文字；内嵌脚本没有执行，所以父页面收不到消息；状态行变成“未收到消息 / 沙箱标记=true / 允许项=0 / 可访内嵌文档=false”。",
        "pit": [
            "同时写 allow-scripts 与 allow-same-origin 会让沙箱内的脚本能操作父页面，等于没隔离。",
            "sandbox 属性的值是空字符串，不要写成 sandbox=\"true\"（那会被当成未知的允许项）。",
            "sandbox 后 contentDocument 为 null 是预期行为，不是加载失败。",
        ],
        "ex": [("给沙箱加上 allow-scripts 并重新观察状态行。", "只加这个允许项，不要加 same-origin。", "<iframe id=\"safe\" sandbox=\"allow-scripts\" ...>")],
    },
    {
        "t": "canvas 高 DPI 像素适配与可访问回退",
        "level": "advanced",
        "obj": "按设备像素比设置 canvas 位图尺寸，并保留可访问名称。",
        "pre": ["多媒体：audio 与 video", "内联 SVG 图标系统"],
        "con": ["canvas", "devicePixelRatio", "位图尺寸 vs CSS 尺寸", "role=img", "getImageData"],
        "explain": "`canvas` 的 `width`/`height` 属性是*位图*尺寸，CSS 宽高是显示尺寸。把位图尺寸设为 CSS 尺寸 × `devicePixelRatio`，再用 `ctx.scale(dpr, dpr)` 按逻辑坐标绘制，才能在高分屏上不模糊。`canvas` 元素内可以放回退文本，并提供 `role=\"img\"` + `aria-label` 让屏幕阅读器得到描述。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>canvas 高 DPI</title>
  <style>#board { width: 150px; height: 75px; border: 1px solid #c8cdd4; }</style>
</head>
<body>
  <canvas id="board" width="150" height="75" role="img" aria-label="离线进度 60% 的条形图">离线进度 60% 的条形图</canvas>
  <p id="state">等待探测</p>
  <script>
    var board = document.getElementById('board');
    var cssW = 150;
    var cssH = 75;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    board.width = Math.round(cssW * dpr);
    board.height = Math.round(cssH * dpr);
    var ctx = board.getContext('2d');
    ctx.scale(dpr, dpr);
    ctx.fillStyle = '#e8f0fe';
    ctx.fillRect(0, 0, cssW, cssH);
    ctx.fillStyle = '#1a73e8';
    ctx.fillRect(0, 0, Math.round(cssW * 0.6), cssH);
    function report() {
      document.getElementById('state').textContent =
        'dpr=' + dpr +
        ' / 位图=' + board.width + 'x' + board.height +
        ' / 显示=' + Math.round(board.getBoundingClientRect().width) + 'x' + Math.round(board.getBoundingClientRect().height) +
        ' / 可访问名=' + board.getAttribute('aria-label');
    }
    report();
  </script>
</body>
</html>''',
        "out": "页面上出现 150×75 的条形图，左侧 60% 是深蓝、右侧是浅蓝；探测行输出 dpr、位图尺寸是显示尺寸乘以 dpr、显示尺寸 150×75 与可访问名称。",
        "pit": [
            "只改 CSS 宽高而不改 width/height 属性，图形会被拉伸变形。",
            "设置了位图尺寸后没有 ctx.scale，绘制坐标会按物理像素解释导致图形缩小。",
            "canvas 内容对读屏不可见，必须提供 aria-label 或回退文本。",
        ],
        "ex": [("把进度从 60% 改成 80%。", "修改 fillRect 的宽度比例。", "ctx.fillRect(0, 0, Math.round(cssW * 0.8), cssH);")],
    },
    {
        "t": "内联 SVG 的可访问名称与描述",
        "level": "advanced",
        "obj": "用 title/desc 与 aria-labelledby 为内联图表提供可访问名称。",
        "pre": ["内联 SVG 图标系统", "无障碍图片与图标按钮"],
        "con": ["svg title", "svg desc", "aria-labelledby", "role=img", "viewBox"],
        "explain": "内联 `<svg>` 默认被读屏当作图形容器，但它需要名称与描述才有意义：`<title>` 提供名称，`<desc>` 提供展开说明，两者都必须是 svg 的前两个子元素。也可以用 `aria-labelledby` 同时指向 title 与 desc 的 id。当 svg 作为整体图片（而不是可交互图标）时，加 `role=\"img\"` 把它合并为一个图形对象。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>SVG 可访问名</title></head>
<body>
  <svg id="chart" role="img" aria-labelledby="chart-title chart-desc"
    width="200" height="100" viewBox="0 0 200 100">
    <title id="chart-title">离线缓存命中率</title>
    <desc id="chart-desc">柱状图：命中 92%，未命中 8%</desc>
    <rect x="0" y="10" width="184" height="20" fill="#1a73e8"></rect>
    <rect x="0" y="40" width="16" height="20" fill="#c8cdd4"></rect>
    <text x="0" y="85" font-size="12" fill="#3c4043">命中 / 未命中</text>
  </svg>
  <p id="state">等待探测</p>
  <script>
    var chart = document.getElementById('chart');
    var ids = chart.getAttribute('aria-labelledby').split(' ');
    var texts = ids.map(function (id) { return document.getElementById(id).textContent; });
    var bars = chart.querySelectorAll('rect');
    document.getElementById('state').textContent =
      '标签数=' + ids.length +
      ' / 名称=' + texts[0] +
      ' / 描述=' + texts[1] +
      ' / 柱宽=' + bars[0].getAttribute('width') + ',' + bars[1].getAttribute('width') +
      ' / 显示宽=' + Math.round(chart.getBoundingClientRect().width);
  </script>
</body>
</html>''',
        "out": "页面上显示两根横向柱：蓝色长柱与灰色短柱，下方有一行小字说明；探测行输出“标签数=2 / 名称=离线缓存命中率 / 描述=柱状图：命中 92%，未命中 8% / 柱宽=184,16 / 显示宽=200”。",
        "pit": [
            "title/desc 必须写在 svg 开头，写在图形之后部分工具无法建立名称。",
            "多个 svg 都用 id=\"title\" 会造成 aria-labelledby 指向错误元素。",
            "给装饰性 svg 加 role=img 并保留空名会让读屏读出“图片”而无线索，装饰图形应 aria-hidden=true。",
        ],
        "ex": [("把未命中柱改成 32 宽。", "只改第二个 rect 的 width。", "<rect x=\"0\" y=\"40\" width=\"32\" height=\"20\">")],
    },
    {
        "t": "video poster 与 playsinline 首帧策略",
        "level": "advanced",
        "obj": "用 poster 提供离线封面，用 playsinline 控制在页面内播放。",
        "pre": ["多媒体：audio 与 video", "资源提示与懒加载"],
        "con": ["video", "poster", "playsinline", "preload=none", "readyState"],
        "explain": "`poster` 指定视频加载前的封面图，`playsinline` 让移动浏览器在页面内播放而不是强制全屏，`preload=\"none\"` 告诉浏览器不要预先下载视频数据。在离线示例里没有真实视频源，因此 `readyState` 是 0、`videoWidth` 是 0，但封面、尺寸与属性仍然可以被验证——这也说明“看着像视频播放器”不代表媒体真的可播。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>video 封面</title></head>
<body>
  <video id="clip" width="240" height="135" playsinline muted loop controls preload="none"
    poster="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%27240%27 height=%27135%27%3E%3Crect width=%27240%27 height=%27135%27 fill=%27%231a73e8%27/%3E%3Ctext x=%27120%27 y=%2772%27 font-size=%2718%27 text-anchor=%27middle%27 fill=%27%23fff%27%3E离线封面%3C/text%3E%3C/svg%3E"></video>
  <p id="state">等待探测</p>
  <script>
    var clip = document.getElementById('clip');
    document.getElementById('state').textContent =
      'poster 内联=' + (clip.poster.indexOf('data:image/svg+xml') === 0) +
      ' / playsInline=' + clip.playsInline +
      ' / muted=' + clip.muted +
      ' / controls=' + clip.controls +
      ' / readyState=' + clip.readyState +
      ' / videoWidth=' + clip.videoWidth +
      ' / 显示=' + Math.round(clip.getBoundingClientRect().width) + 'x' + Math.round(clip.getBoundingClientRect().height);
  </script>
</body>
</html>''',
        "out": "页面显示一个 240×135 的蓝色封面，写着“离线封面”，下方是播放控件；探测行输出“poster 内联=true / playsInline=true / muted=true / controls=true / readyState=0 / videoWidth=0 / 显示=240x135”。",
        "pit": [
            "poster 指向外部地址会破坏离线要求，应使用 data: 内联图。",
            "没有 playsinline 时移动端会自动全屏，控制条与页面其它内容被遮挡。",
            "readyState=0 说明没有任何媒体数据，排障时先查这个而不是查样式。",
        ],
        "ex": [("把封面文字改成“离线教程视频”。", "修改 poster 里文本的百分号编码内容。", "%3Ctext x=%27120%27 y=%2772%27 font-size=%2718%27 text-anchor=%27middle%27 fill=%27%23fff%27%3E离线教程视频%3C/text%3E")],
    },
    {
        "t": "track 字幕轨与 VTTCue",
        "level": "advanced",
        "obj": "用运行时生成的 Blob 字幕轨验证 textTracks 与 cue 解析。",
        "pre": ["多媒体：audio 与 video", "video poster 与 playsinline 首帧策略"],
        "con": ["track", "WebVTT", "textTracks", "VTTCue", "Blob URL"],
        "explain": "`<track kind=\"captions\" srclang=\"zh\" default>` 给媒体添加字幕轨，内容是 WebVTT 文本。为了保持离线自包含，示例用 Blob 生成 VTT 再挂到 track 上，这样也能看到它加载后跑的文字。加载完成后 `video.textTracks[0].cues` 会是真正解析出的 cue 列表，可验证时间轴与文本是否被正确解析。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>字幕轨</title></head>
<body>
  <video id="clip" width="240" height="135" muted controls></video>
  <p id="state">等待字幕加载</p>
  <script>
    var nl = String.fromCharCode(10);
    var vtt = ['WEBVTT', '', '1', '00:00:00.000 --> 00:00:05.000', '离线也能显示字幕', '', '2', '00:00:05.000 --> 00:00:10.000', '第二条字幕', ''].join(nl);
    var url = URL.createObjectURL(new Blob([vtt], { type: 'text/vtt' }));
    var clip = document.getElementById('clip');
    var track = document.createElement('track');
    track.kind = 'captions';
    track.label = '中文';
    track.srclang = 'zh';
    track.default = true;
    track.src = url;
    clip.appendChild(track);
    function report() {
      var list = clip.textTracks;
      var trackObj = list[0];
      var cues = trackObj && trackObj.cues ? trackObj.cues.length : 0;
      document.getElementById('state').textContent =
        '轨道数=' + list.length +
        ' / kind=' + (trackObj ? trackObj.kind : 'none') +
        ' / cue 数=' + cues +
        ' / 首条=' + (cues ? trackObj.cues[0].text : '') +
        ' / 结束时间=' + (cues ? trackObj.cues[0].endTime : 0);
    }
    track.addEventListener('load', report);
    track.addEventListener('error', function () {
      document.getElementById('state').textContent = '字幕加载失败';
    });
    setTimeout(report, 400);
  </script>
</body>
</html>''',
        "out": "页面显示一个 240×135 的黑框播放器区域；字幕解析成功后状态行显示“轨道数=1 / kind=captions / cue 数=2 / 首条=离线也能显示字幕 / 结束时间=5”。",
        "pit": [
            "VTT 首行必须是 WEBVTT，且每个 cue 之间要有空行，否则解析出 0 条 cue。",
            "textTracks 的 mode 默认可能是 disabled，读取 cues 前要确认轨道已加载。",
            "用 blob: 地址时要在不使用时 revokeObjectURL，否则内存不释放。",
        ],
        "ex": [("把第一条字幕的结束时间改成 00:00:03.000。", "只改第一段的时间行。", "'00:00:00.000 --> 00:00:03.000',")],
    },
    {
        "t": "声明式 Shadow DOM 与插槽",
        "level": "advanced",
        "obj": "用 template shadowrootmode 直接声明 shadow root 与插槽，无需脚本挂载。",
        "pre": ["自定义数据与模板：template 与 slot", "自定义元素入门"],
        "con": ["template shadowrootmode", "shadowRoot", "slot name", "assignedNodes", ":host"],
        "explain": "在自定义元素内部放一个 `<template shadowrootmode=\"open\">`，浏览器解析时就直接把它的内容变成元素的 shadow root（即声明式 Shadow DOM），不需要再写 `attachShadow` 的脚本。Shadow 内部用 `<slot name=\"desc\">` 接收宿主页面里 `slot=\"desc\"` 的子元素（light DOM 不会被挪走）。`:host` 选择器可用于给宿主元素样式。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>声明式 Shadow DOM</title></head>
<body>
  <user-card id="card">
    <template shadowrootmode="open">
      <style>
        :host { display: block; border: 1px solid #c8cdd4; padding: 8px; }
        h3 { color: #1a73e8; margin: 0 0 4px; }
      </style>
      <h3>声明式 Shadow DOM</h3>
      <p><slot name="desc">默认描述</slot></p>
    </template>
    <span slot="desc">来自宿主页面的插槽内容</span>
  </user-card>
  <p id="state">等待探测</p>
  <script>
    var card = document.getElementById('card');
    var root = card.shadowRoot;
    var slot = root.querySelector('slot[name="desc"]');
    var assigned = slot.assignedNodes();
    document.getElementById('state').textContent =
      'shadowRoot=' + (root !== null) +
      ' / 内部 h3=' + root.querySelector('h3').textContent +
      ' / 外部 h3 数=' + card.querySelectorAll('h3').length +
      ' / 分配节点=' + assigned.length +
      ' / 插槽文本=' + (assigned[0] ? assigned[0].textContent : 'none') +
      ' / host 边框=' + getComputedStyle(card).borderTopWidth;
  </script>
</body>
</html>''',
        "out": "页面上出现一个带边框的卡片，标题蓝色“声明式 Shadow DOM”，下面一行显示外部传入的插槽文本；探测行输出“shadowRoot=true / 内部 h3=声明式 Shadow DOM / 外部 h3 数=0 / 分配节点=1 / 插槽文本=来自宿主页面的插槽内容 / host 边框=1px”。",
        "pit": [
            "shadowrootmode 模板必须是宿主元素的直接子元素，放深了一层就不会生效。",
            "light DOM 里的 h3 不会被 shadow 选择器影响，两边的样式相互隔离。",
            "宿主元素自身如果没有 display 声明，:host 的边框仍会应用到元素本身，但布局行为要显式写成 block。",
        ],
        "ex": [("把默认插槽文本改成“未提供描述”。", "只改 slot 内的文字。", "<slot name=\"desc\">未提供描述</slot>")],
    },
    {
        "t": "attachShadow 的作用域样式 ::slotted",
        "level": "advanced",
        "obj": "用 attachShadow 创建开放 shadow root，并用 ::slotted 给插槽内容加样式。",
        "pre": ["声明式 Shadow DOM 与插槽", "HTML class 与 id 的取舍"],
        "con": ["attachShadow", "mode: open", "::slotted", ":host", "样式隔离"],
        "explain": "`element.attachShadow({ mode: \"open\" })` 在运行时创建 shadow root，`mode: \"open\"` 让外部能通过 `element.shadowRoot` 访问它。shadow 内的 `<style>` 只影响 shadow 树；要影响*投影进来*的 light DOM 元素，必须用 `::slotted(选择器)`。反过来，外部页面的样式无法穿透进来，只能改宿主元素自身的样式。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>attachShadow 样式作用域</title>
  <style>badge-chip span { color: red; }</style>
</head>
<body>
  <badge-chip id="chip"><span slot="label">离线</span></badge-chip>
  <p id="state">等待探测</p>
  <script>
    var chip = document.getElementById('chip');
    var root = chip.attachShadow({ mode: "open" });
    root.innerHTML = "<style>" +
      ":host { display: inline-block; border-radius: 999px; padding: 2px 10px; background: #e8f0fe; }" +
      "::slotted(span) { font-weight: 700; letter-spacing: 1px; }" +
      "</style><slot name='label'></slot>";
    var slotted = chip.querySelector('span');
    var hostStyle = getComputedStyle(chip);
    var slotStyle = getComputedStyle(slotted);
    document.getElementById('state').textContent =
      'mode=' + root.mode +
      ' / host 背景=' + hostStyle.backgroundColor +
      ' / host 圆角=' + hostStyle.borderTopLeftRadius +
      ' / slotted 字重=' + slotStyle.fontWeight +
      ' / 外部红色样式是否穿透=' + (slotStyle.color === 'rgb(255, 0, 0)') +
      ' / light DOM 保留=' + (chip.querySelectorAll('span').length === 1);
  </script>
</body>
</html>''',
        "out": "页面上出现一个浅蓝胶囊标签“离线”，字重加粗、字距略宽；探测行输出“mode=open / host 背景=rgb(232, 240, 254) / host 圆角=999px / slotted 字重=700 / 外部红色样式是否穿透=true / light DOM 保留=true”。",
        "pit": [
            "对同一个元素重复调用 attachShadow 会抛错，一个元素只能有一个 shadow root。",
            "外部样式会作用于 light DOM 元素本体，所以“穿透=false”这样的预期往往是错的。",
            "::slotted 只能选直接投影的顶层元素，不能选中它们内部的子孙元素。",
        ],
        "ex": [("把 ::slotted 的字距改成 2px。", "只改 letter-spacing。", "::slotted(span) { font-weight: 700; letter-spacing: 2px; }")],
    },
    {
        "t": "自定义元素生命周期回调",
        "level": "advanced",
        "obj": "验证 connectedCallback 与 disconnectedCallback 的触发时机。",
        "pre": ["自定义元素入门", "attachShadow 的作用域样式 ::slotted"],
        "con": ["customElements.define", "connectedCallback", "disconnectedCallback", "元素升级", "生命周期日志"],
        "explain": "自定义元素在*进入*文档时调用 `connectedCallback`，在*离开*文档时调用 `disconnectedCallback`，两者可以多次触发（元素被反复插入时）。定义之前已经存在于 DOM 的元素会在定义时被“升级”，同样会触发连接回调。用日志数组记录这两类事件是排查组件行为最直接的方式。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>元素生命周期</title></head>
<body>
  <div id="host"></div>
  <p><button type="button" id="remove">移除徽标</button></p>
  <p id="state">等待探测</p>
  <script>
    var log = [];
    class LiteBadge extends HTMLElement {
      connectedCallback() {
        log.push('connected:' + this.getAttribute('label'));
        this.textContent = this.getAttribute('label');
      }
      disconnectedCallback() {
        log.push('disconnected:' + this.getAttribute('label'));
      }
    }
    customElements.define('lite-badge', LiteBadge);
    var badge = document.createElement('lite-badge');
    badge.setAttribute('label', '离线优先');
    document.getElementById('host').appendChild(badge);
    var state = document.getElementById('state');
    function render(extra) {
      state.textContent = '日志=' + log.join(' / ') + (extra ? ' / ' + extra : '');
    }
    render('升级=' + (badge instanceof LiteBadge) + ' / 文本=' + badge.textContent);
    document.getElementById('remove').addEventListener('click', function () {
      badge.remove();
      render('仍在文档中=' + document.contains(badge));
    });
  </script>
</body>
</html>''',
        "out": "页面上出现一个写着“离线优先”的徽标；探测行显示“日志=connected:离线优先 / 升级=true / 文本=离线优先”。点击“移除徽标”后徽标消失，状态行追加“disconnected:离线优先 / 仍在文档中=false”。",
        "pit": [
            "在 constructor 里读写属性或子节点会被规范禁止，元素行为应写在 connectedCallback。",
            "移除后再插入会再次触发 connectedCallback，计数类逻辑不能假设只执行一次。",
            "自定义元素名必须包含连字符，camelCase 名字会导致 define 抛错。",
        ],
        "ex": [("把徽标标签文本改成“本地优先”。", "只改 setAttribute 的 label 值。", "badge.setAttribute('label', '本地优先');")],
    },
    {
        "t": "defer、async 与 noscript 加载时序",
        "level": "advanced",
        "obj": "用执行顺序验证 defer 与内联脚本的时序，并观察 noscript 的行为。",
        "pre": ["HTML 与 CSS/JS 的引入方式", "资源提示与懒加载"],
        "con": ["defer", "async", "DOMContentLoaded", "noscript", "执行顺序"],
        "explain": "普通内联脚本在解析到它时就执行；`defer` 脚本在文档解析完成后、按文档顺序执行，并在 `DOMContentLoaded` 之前；`async` 脚本一旦下载完就立即执行，顺序不确定。`<noscript>` 的内容在启用脚本时*不会*进入 DOM，所以用脚本查它是查不到的，它只服务于禁用脚本的场景。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>脚本时序</title></head>
<body>
  <script>window.__order = ['classic'];</script>
  <script defer>window.__order.push('defer-1');</script>
  <p id="target">目标段落</p>
  <noscript><p id="nojs">需要启用 JavaScript 才能看到交互</p></noscript>
  <script defer>
    window.__order.push('defer-2');
    document.addEventListener('DOMContentLoaded', function () {
      document.getElementById('state').textContent =
        '执行顺序=' + window.__order.join('>') +
        ' / 解析期目标已存在=' + (document.getElementById('target') !== null) +
        ' / noscript 进入 DOM=' + (document.getElementById('nojs') !== null);
    });
  </script>
  <p id="state">等待探测</p>
</body>
</html>''',
        "out": "DOMContentLoaded 之后状态行显示“执行顺序=classic>defer-1>defer-2 / 解析期目标已存在=true / noscript 进入 DOM=false”，说明 defer 脚本按顺序在解析完成后执行，而 noscript 内容在启用脚本时不进入 DOM。",
        "pit": [
            "defer 只对外部脚本与内联脚本生效，但内联 defer 不能依赖下载时机，顺序仍按文档。",
            "async 脚本可能在 DOM 未就绪时执行，访问元素前要先判断存在性。",
            "依赖 noscript 提供关键信息会让启用脚本的用户完全看不到这些内容。",
        ],
        "ex": [("再加一个 async 脚本并记录它的名字。", "注意 async 顺序不确定，只用于日志。", "<script async>window.__order.push('async');</script>")],
    },
    {
        "t": "script type=module 的作用域与 import.meta",
        "level": "advanced",
        "obj": "验证模块脚本的独立作用域、延迟执行与 import.meta.url。",
        "pre": ["defer、async 与 noscript 加载时序", "全局属性总览与脚本作用域"],
        "con": ["type=module", "模块作用域", "import.meta", "延迟执行", "不泄漏全局"],
        "explain": "`<script type=\"module\">` 默认带 defer 语义：解析完成后才执行，且严格模式。它有自己的作用域，顶层 `var`/`function` 不会挂到 `window` 上，这正是模块与经典脚本最大的区别。`import.meta.url` 给出模块自身的地址，内联模块就是文档地址，可用于推导相对资源位置。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>模块作用域</title></head>
<body>
  <script>window.__order = ['classic']; window.leakedInClassic = 'classic-var';</script>
  <script type="module">
    var leakedInModule = 'module-var';
    window.__order.push('module');
    document.getElementById('state').textContent =
      '执行顺序=' + window.__order.join('>') +
      ' / 经典脚本泄漏=' + window.leakedInClassic +
      ' / 模块泄漏=' + String(window.leakedInModule) +
      ' / import.meta 存在=' + (typeof import.meta === 'object') +
      ' / 地址与文档一致=' + (import.meta.url === document.URL) +
      ' / 严格模式=' + (function () { try { undeclaredProbe = 1; return false; } catch (e) { return true; } })();
  </script>
  <p id="state">等待探测</p>
</body>
</html>''',
        "out": "状态行显示“执行顺序=classic>module / 经典脚本泄漏=classic-var / 模块泄漏=undefined / import.meta 存在=true / 地址与文档一致=true / 严格模式=true”，说明模块在经典脚本之后执行且不向 window 泄漏变量。",
        "pit": [
            "模块脚本里的顶层 var 不是全局变量，事件绑定不能用内联 onclick 访问它。",
            "直接打开 file:// 页面时模块会被 CORS 限制，离线预览也应通过本地 HTTP 服务。",
            "模块脚本的 import 路径需要真实文件，离线时可以用 data: 或 blob: 地址承载小模块。",
        ],
        "ex": [("在模块里再声明一个 const 并尝试从 window 读取。", "用 window.xxx 读取，结果应为 undefined。", "window.readConst 应为 undefined")],
    },
    {
        "t": "aria-live 状态区域的播报",
        "level": "advanced",
        "obj": "用 aria-live/role=status 让动态状态变化被读屏播报。",
        "pre": ["无障碍基础：ARIA 与键盘导航", "表单错误提示的展示"],
        "con": ["aria-live", "role=status", "polite", "动态区域", "不能抢焦点"],
        "explain": "`aria-live=\"polite\"` 的区域内容变化后，读屏会在当前朗读结束后播报新内容；`assertive` 会立即打断。`role=\"status\"` 本身就隐含 `aria-live=\"polite\"`，常用于“已保存”“共 N 条”这类状态行。关键约束是：区域要在变化*之前*就存在，只改文本内容，不要新建整个元素，否则辅助技术可能捕捉不到。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>aria-live 状态</title></head>
<body>
  <p><button type="button" id="save">保存</button></p>
  <p id="status" role="status" aria-live="polite">尚未保存</p>
  <p id="state">等待探测</p>
  <script>
    var statusEl = document.getElementById('status');
    var times = 0;
    document.getElementById('save').addEventListener('click', function () {
      times++;
      statusEl.textContent = '已保存第 ' + times + ' 次';
    });
    document.getElementById('state').textContent =
      'role=' + statusEl.getAttribute('role') +
      ' / aria-live=' + statusEl.getAttribute('aria-live') +
      ' / 动态区域数=' + document.querySelectorAll('[aria-live]').length +
      ' / 初始文本=' + statusEl.textContent;
  </script>
</body>
</html>''',
        "out": "页面上有一个“保存”按钮与状态行“尚未保存”；点击两次后状态行变成“已保存第 2 次”，读屏会播报这句变化；探测行输出“role=status / aria-live=polite / 动态区域数=1 / 初始文本=尚未保存”。",
        "pit": [
            "每次都重建整个状态元素会让播报丢失，应只改已有元素的文本。",
            "aria-live 区域在页面加载时就有内容会被整体读一遍，初始内容应尽量简短。",
            "用 assertive 播报频繁变化的值会不断打断读屏，普通状态用 polite。",
        ],
        "ex": [("把状态行改成 assertive 并在注释里说明原因。", "仅当错误必须立即告知时使用 assertive。", "aria-live=\"assertive\"")],
    },
    {
        "t": "role=tablist 标签页模式与键盘切换",
        "level": "advanced",
        "obj": "用 tablist/tab/tabpanel 实现可键盘操作的标签页。",
        "pre": ["无障碍基础：ARIA 与键盘导航", "语义区块与 ARIA 地标"],
        "con": ["role=tablist", "role=tab", "aria-selected", "aria-controls", "roving tabindex"],
        "explain": "标签页是 ARIA 复合模式：`role=\"tablist\"` 包住多个 `role=\"tab\"`，每个 tab 用 `aria-controls` 指向自己的 `role=\"tabpanel\"`，用 `aria-selected` 表示选中。键盘上只让选中的 tab 进入 Tab 序列（roving tabindex：选中项 `tabindex=0`，其余 `-1`），左右方向键在 tab 之间切换。面板用 `hidden` 切换显隐。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>标签页模式</title></head>
<body>
  <div role="tablist" id="tablist" aria-label="示例分组">
    <button type="button" role="tab" id="tab-a" aria-selected="true" aria-controls="panel-a" tabindex="0">HTML</button>
    <button type="button" role="tab" id="tab-b" aria-selected="false" aria-controls="panel-b" tabindex="-1">CSS</button>
  </div>
  <div role="tabpanel" id="panel-a" aria-labelledby="tab-a">HTML 面板内容</div>
  <div role="tabpanel" id="panel-b" aria-labelledby="tab-b" hidden>CSS 面板内容</div>
  <p id="state">等待探测</p>
  <script>
    var tabs = Array.prototype.slice.call(document.querySelectorAll('[role="tab"]'));
    var panels = Array.prototype.slice.call(document.querySelectorAll('[role="tabpanel"]'));
    function select(tab) {
      tabs.forEach(function (item) {
        var on = item === tab;
        item.setAttribute('aria-selected', String(on));
        item.tabIndex = on ? 0 : -1;
        document.getElementById(item.getAttribute('aria-controls')).hidden = !on;
      });
      var visible = panels.filter(function (panel) { return !panel.hidden; });
      document.getElementById('state').textContent =
        '选中=' + tab.id +
        ' / 可见面板=' + visible.map(function (p) { return p.id; }).join(',') +
        ' / 面板数=' + panels.length;
    }
    tabs.forEach(function (tab) {
      tab.addEventListener('click', function () { select(tab); });
      tab.addEventListener('keydown', function (event) {
        if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft') return;
        event.preventDefault();
        var index = tabs.indexOf(tab);
        var next = tabs[(index + (event.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length];
        next.focus();
        select(next);
      });
    });
  </script>
</body>
</html>''',
        "out": "页面上有两个标签“HTML”“CSS”，初始显示 HTML 面板；点击 CSS 后切换到 CSS 面板，状态行显示“选中=tab-b / 可见面板=panel-b / 面板数=2”；在 CSS 标签上按左方向键切回 HTML。",
        "pit": [
            "没有 roving tabindex 时所有 tab 都能被 Tab 键选中，不符合 ARIA 模式。",
            "面板隐藏用 hidden 而不是 CSS 高度 0，否则仍会被读屏与搜索到。",
            "aria-controls 指向 id 而不是选择器，写错时监听关系断裂。",
        ],
        "ex": [("再加入一个 JavaScript 标签与对应面板。", "复制一组 tab/panel 并保持 id 一致。", "<button role=\"tab\" id=\"tab-c\" aria-selected=\"false\" aria-controls=\"panel-c\" tabindex=\"-1\">JavaScript</button>")],
    },
    {
        "t": "aria-expanded 披露按钮与 aria-controls",
        "level": "intermediate",
        "obj": "用 aria-expanded 维护展开状态，并让按钮与目标区域建立关联。",
        "pre": ["无障碍基础：ARIA 与键盘导航", "内容分组：figure 与 details"],
        "con": ["aria-expanded", "aria-controls", "hidden", "披露模式", "状态同步"],
        "explain": "自定义折叠区不能只用 `hidden` 切显隐，还要把按钮的展开状态暴露给读屏：`aria-expanded=\"true|false\"`，并用 `aria-controls` 指向受控元素的 id。按钮依然用原生 `<button>` 以保留光标、回车与空格的默认行为，脚本只负责切状态。状态与可见性必须同步更新，只改一个就会出现“说已展开但看不到内容”。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>aria-expanded 披露</title></head>
<body>
  <button type="button" id="toggle" aria-expanded="false" aria-controls="more">更多信息</button>
  <div id="more" hidden>这里是展开后的补充内容。</div>
  <p id="state">等待探测</p>
  <script>
    var toggle = document.getElementById('toggle');
    var more = document.getElementById('more');
    function report() {
      document.getElementById('state').textContent =
        'expanded=' + toggle.getAttribute('aria-expanded') +
        ' / hidden=' + more.hidden +
        ' / controls 匹配=' + (document.getElementById(toggle.getAttribute('aria-controls')) === more);
    }
    toggle.addEventListener('click', function () {
      var open = toggle.getAttribute('aria-expanded') !== 'true';
      toggle.setAttribute('aria-expanded', String(open));
      more.hidden = !open;
      report();
    });
    report();
  </script>
</body>
</html>''',
        "out": "页面上有一个“更多信息”按钮和隐藏的内容；点击后内容出现，状态行从“expanded=false / hidden=true / controls 匹配=true”变成“expanded=true / hidden=false / controls 匹配=true”。",
        "pit": [
            "只改 hidden 不改 aria-expanded，读屏会说“已折叠”但内容已显示。",
            "按钮内放 div 或用 span 模拟按钮会丢失键盘激活能力。",
            "aria-controls 指向不存在的 id 时不会报错，只是关联静默失效。",
        ],
        "ex": [("再加一个“重置”按钮把展开状态收回。", "点击后设回 expanded=false。", "toggle.setAttribute('aria-expanded', 'false'); more.hidden = true;")],
    },
    {
        "t": "tabindex 焦点顺序与可编程聚焦",
        "level": "advanced",
        "obj": "用正负 tabindex 控制 Tab 顺序与可编程聚焦目标。",
        "pre": ["无障碍地标与跳转链接", "HTML 全局属性总览"],
        "con": ["tabindex", "正数顺序", "tabindex=-1", "activeElement", "焦点管理"],
        "explain": "`tabindex=\"0\"` 让元素按 DOM 顺序进入 Tab 序列，`tabindex=\"-1\"` 让它只能用脚本 `focus()` 聚焦（不进入 Tab 序列），正整数值会把元素插到 Tab 序列前端并按数值排序——这几乎总是坏事，因为它会脱离版面顺序并让键盘用户迷失。下面用三个按钮验证“数值小的先被 Tab 到”。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>tabindex 焦点顺序</title></head>
<body>
  <button type="button" id="first">第一</button>
  <button type="button" id="second" tabindex="2">第二（tabindex=2）</button>
  <button type="button" id="third" tabindex="1">第三（tabindex=1）</button>
  <div id="focusable" tabindex="-1">可编程聚焦区域</div>
  <p id="state">等待探测</p>
  <script>
    var log = [];
    document.addEventListener('focusin', function (event) {
      log.push(event.target.id);
      document.getElementById('state').textContent =
        '焦点顺序=' + log.join('>') +
        ' / tabIndex 值=' + ['first', 'second', 'third'].map(function (id) {
          return id + ':' + document.getElementById(id).tabIndex;
        }).join(',') +
        ' / 程序聚焦区域 tabIndex=' + document.getElementById('focusable').tabIndex;
    });
  </script>
</body>
</html>''',
        "out": "连续按 Tab 时焦点顺序是“第三 → 第二 → 第一”（因 tabindex=1/2 优先于默认 0）；状态行同时列出每个元素的 tabIndex 值与可编程聚焦区域的 -1。",
        "pit": [
            "正数 tabindex 会让 Tab 顺序与视觉顺序不一致，维护时应全部用 0 与 -1。",
            "tabindex=-1 的元素仍需自身可聚焦语义，给 div 加后应配合 role 与 aria-label。",
            "移除焦点所在元素后焦点会回到 body，应在移除前把焦点移到合理位置。",
        ],
        "ex": [("把第三按钮的 tabindex 改成 3，重新按 Tab 验证顺序变化。", "只改数值，注意先前的 1 变最小就不会再排第一。", "tabindex=\"3\"")],
    },
    {
        "t": "inert 阻止焦点与交互",
        "level": "advanced",
        "obj": "用 inert 属性整体禁用一块子树的焦点、点击与读屏访问。",
        "pre": ["tabindex 焦点顺序与可编程聚焦", "无障碍基础：ARIA 与键盘导航"],
        "con": ["inert", "焦点阻止", "可交互性", "弹层背景", "伪类"],
        "explain": "`inert` 是 HTML 的全局布尔属性：被标记的子树里的控件无法聚焦、无法点击，也不会被读屏或页内查找访问。它比逐个 `disabled` 或 `tabindex=-1` 更彻底，常用于模态弹层打开时把背景内容整体隔离。脚本里读 `element.inert`，并可结合 `:has()` 做样式提示。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>inert 隔离</title>
  <style>#modalish[inert] { opacity: 0.5; }</style>
</head>
<body>
  <div id="modalish" inert>
    <p>弹层打开时应被隔离的背景区</p>
    <button type="button" id="blocked">不可聚焦按钮</button>
  </div>
  <button type="button" id="allowed">可聚焦按钮</button>
  <p id="state">等待探测</p>
  <script>
    var box = document.getElementById('modalish');
    var blocked = document.getElementById('blocked');
    var allowed = document.getElementById('allowed');
    blocked.focus();
    var afterBlocked = document.activeElement;
    allowed.focus();
    var afterAllowed = document.activeElement;
    document.getElementById('state').textContent =
      'inert=' + box.inert +
      ' / 被阻按钮可聚焦=' + (afterBlocked === blocked) +
      ' / 正常按钮可聚焦=' + (afterAllowed === allowed) +
      ' / 被阻透明度=' + getComputedStyle(box).opacity;
  </script>
</body>
</html>''',
        "out": "背景区以半透明显示，其中的按钮无法获得焦点，点击也无反应；下面的“可聚焦按钮”可正常聚焦；探测行输出“inert=true / 被阻按钮可聚焦=false / 正常按钮可聚焦=true / 被阻透明度=0.5”。",
        "pit": [
            "inert 是布尔属性，写成 inert=\"false\" 依然是禁用状态。",
            "inert 不会改变视觉样式，需要自己加 CSS 提示。",
            "在 inert 容器外放弹层，否则弹层自己也会被禁用。",
        ],
        "ex": [("点击前把背景区的 inert 移除并观察焦点。", "用 box.inert = false 后再调用 focus。", "box.inert = false; blocked.focus();")],
    },
    {
        "t": "hidden=until-found 与 beforematch",
        "level": "advanced",
        "obj": "用 hidden=until-found 实现可被页内查找命中的折叠内容。",
        "pre": ["内容分组：figure 与 details", "aria-expanded 披露按钮与 aria-controls"],
        "con": ["hidden=until-found", "content-visibility", "beforematch", "页内查找", "按需渲染"],
        "explain": "`hidden=\"until-found\"` 让内容在未被查找命中前隐藏，且不参与渲染成本；浏览器页内查找命中时，会先派发 `beforematch` 事件（可在此时展开祖先的折叠区域），再把内容显示并滚动到命中位置。它比普通 `hidden` 多了“可被搜索”这个能力，适合长文档里的折叠章节。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>hidden until-found</title></head>
<body>
  <p><button type="button" id="reveal">模拟查找命中</button></p>
  <div id="hidden-part" hidden="until-found">
    <h2>隐藏章节</h2>
    <p>搜索“离线缓存”会命中这一段。</p>
  </div>
  <p id="state">等待探测</p>
  <script>
    var part = document.getElementById('hidden-part');
    var log = [];
    part.addEventListener('beforematch', function () { log.push('beforematch'); });
    function report() {
      var style = getComputedStyle(part);
      document.getElementById('state').textContent =
        'hidden 值=' + (part.getAttribute('hidden') === null ? 'none' : part.getAttribute('hidden')) +
        ' / content-visibility=' + style.contentVisibility +
        ' / 已解密=' + (part.hidden === false) +
        ' / 事件=' + (log.join(',') || 'none') +
        ' / 高度=' + Math.round(part.getBoundingClientRect().height);
    }
    document.getElementById('reveal').addEventListener('click', function () {
      part.dispatchEvent(new Event('beforematch'));
      part.hidden = false;
      report();
    });
    report();
  </script>
</body>
</html>''',
        "out": "初始时隐藏章节不可见但能被页内查找命中（`content-visibility: hidden`）；点击“模拟查找命中”后先触发 beforematch，再把内容展开，状态行输出 hidden 值与高度。",
        "pit": [
            "until-found 的隐藏区域仍会被搜索引擎与页内查找索引，不适合放敏感数据。",
            "在 beforematch 里同步修改 DOM 会报错，展开操作要放到微任务里执行。",
            "不支持该值的旧浏览器会把它当成普通 hidden，需要准备降级交互。",
        ],
        "ex": [("把隐藏原因改成“暂时隐藏，不参与查找”。", "改用普通 hidden 属性并比较 content-visibility。", "<div id=\"hidden-part\" hidden>")],
    },
    {
        "t": "contenteditable plaintext-only 编辑区",
        "level": "advanced",
        "obj": "用 contenteditable 创建纯文本编辑区，并验证粘贴/输入不产生标签。",
        "pre": ["textarea 尺寸、换行与选区 API", "无障碍基础：ARIA 与键盘导航"],
        "con": ["contenteditable", "plaintext-only", "input 事件", "role=textbox", "标签防流失"],
        "explain": "`contenteditable=\"plaintext-only\"` 让元素可编辑但只接受纯文本：输入或粘贴富文本时浏览器会剥掉标签，不会把 HTML 塞进 DOM。普通 `contenteditable=\"true\"` 会保留格式，在需要“只存文本”的场景里很难清洗。可编辑区域不自动拥有输入框语义，应补 `role=\"textbox\"`、`aria-multiline` 与名称。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>contenteditable 纯文本</title>
  <style>#editor { border: 1px solid #c8cdd4; min-height: 40px; padding: 6px 8px; }</style>
</head>
<body>
  <div id="editor" contenteditable="plaintext-only" role="textbox" aria-multiline="true"
    aria-label="备注编辑器">第一行</div>
  <p id="state">等待探测</p>
  <script>
    var editor = document.getElementById('editor');
    var events = 0;
    function report(extra) {
      document.getElementById('state').textContent =
        'contenteditable=' + editor.getAttribute('contenteditable') +
        ' / isContentEditable=' + editor.isContentEditable +
        ' / input 次数=' + events +
        ' / 子元素数=' + editor.querySelectorAll('*').length +
        ' / 文本=' + editor.textContent + (extra ? ' / ' + extra : '');
    }
    editor.addEventListener('input', function () { events++; report(); });
    report();
  </script>
</body>
</html>''',
        "out": "页面上出现一个可编辑的纯文本区域，初始内容是“第一行”；在里面输入 `<b>粗</b>` 这样的文字后，子元素数仍为 0、文本原样保留尖括号，说明标签被当作文本对待。",
        "pit": [
            "contenteditable 区域不参与表单提交，需要自己读取 textContent 组装数据。",
            "plaintext-only 在某些旧内核不支持，会退化成完全可编辑的富文本。",
            "不写 aria-label 时读屏只会说“可编辑文本”，用户不知道要填什么。",
        ],
        "ex": [("把区域改成多行并验证回车不会产生 div。", "保留 plaintext-only，输入回车观察子元素数。", "aria-multiline=\"true\" 保持不变")],
    },
    {
        "t": "combobox 与 aria-activedescendant",
        "level": "advanced",
        "obj": "用 combobox + listbox + aria-activedescendant 实现不经焦点转移的选项导航。",
        "pre": ["datalist 输入建议与 list 关联", "role=tablist 标签页模式与键盘切换"],
        "con": ["role=combobox", "role=listbox", "aria-activedescendant", "aria-selected", "键盘导航"],
        "explain": "自定义下拉框的标准 ARIA 写法是：输入框 `role=\"combobox\"`，用 `aria-controls` 与 `aria-expanded` 关联列表，列表 `role=\"listbox\"` 包多个 `role=\"option\"`。焦点始终留在输入框，用 `aria-activedescendant` 指向当前活动选项的 id，这样读屏会跟随播报但不会真的把焦点移走。方向键只改活动选项与选中状态。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>组合框</title></head>
<body>
  <label for="combo" id="combo-label">选择语言</label>
  <input id="combo" role="combobox" aria-expanded="true" aria-controls="list" aria-autocomplete="list" aria-activedescendant="opt-2" value="CSS">
  <ul id="list" role="listbox" aria-labelledby="combo-label">
    <li id="opt-1" role="option" aria-selected="false">HTML</li>
    <li id="opt-2" role="option" aria-selected="true">CSS</li>
    <li id="opt-3" role="option" aria-selected="false">JavaScript</li>
  </ul>
  <p id="state">等待探测</p>
  <script>
    var combo = document.getElementById('combo');
    var options = Array.prototype.slice.call(document.querySelectorAll('[role="option"]'));
    var index = 1;
    function activate(next) {
      index = next;
      options.forEach(function (option, i) {
        option.setAttribute('aria-selected', String(i === index));
      });
      combo.setAttribute('aria-activedescendant', options[index].id);
      combo.value = options[index].textContent;
      document.getElementById('state').textContent =
        '活动选项=' + options[index].id +
        ' / 值=' + combo.value +
        ' / 选中项数=' + options.filter(function (o) { return o.getAttribute('aria-selected') === 'true'; }).length +
        ' / 焦点在输入框=' + (document.activeElement === combo);
    }
    combo.addEventListener('keydown', function (event) {
      if (event.key === 'ArrowDown') {
        event.preventDefault();
        activate((index + 1) % options.length);
      }
      if (event.key === 'ArrowUp') {
        event.preventDefault();
        activate((index + options.length - 1) % options.length);
      }
    });
    combo.addEventListener('focus', function () { activate(index); });
    activate(1);
  </script>
</body>
</html>''',
        "out": "输入框显示“CSS”，下方列表里 CSS 被标记为选中；聚焦输入框后按一下方向下键，活动选项变为 JavaScript 且输入框值同步；再按方向下键循环回到 HTML，焦点始终留在输入框。",
        "pit": [
            "把焦点真的移到 li 上会破坏组合框模式，应使用 aria-activedescendant。",
            "aria-expanded 与列表可见性不同步时读屏状态会与实际界面矛盾。",
            "option 用 tabindex 会让 Tab 键进入每个选项，键盘体验反而变差。",
        ],
        "ex": [("把列表改成默认收起。", "同步把 aria-expanded 设为 false。", "aria-expanded=\"false\" 并在聚焦时展开")],
    },
    {
        "t": "popover=manual 与显式关闭动作",
        "level": "advanced",
        "obj": "对比 manual 浮层与 auto 浮层的关闭行为差异。",
        "pre": ["popover 轻量浮层与 toggle 事件", "dialog 模态对话框与 ::backdrop"],
        "con": ["popover=manual", "light dismiss", "popovertargetaction=toggle", "toggle 事件", ":popover-open"],
        "explain": "`popover=\"auto\"`（默认值）在点击外部或按 Esc 时会自动关闭（light dismiss），`popover=\"manual\"` 则只能靠脚本或显式的 `popovertarget` 按钮关闭，可用于需要用户确认的常驻面板。`popovertargetaction=\"toggle\"` 在自己身上反复切换，`hide` 只能关。`toggle` 事件在每次状态变化后派发，可以用于统计或同步其它 UI。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>manual 浮层</title>
  <style>[popover] { border: 1px solid #c8cdd4; border-radius: 8px; padding: 10px 14px; }</style>
</head>
<body>
  <button type="button" id="toggle" popovertarget="manual">打开手动浮层</button>
  <div id="manual" popover="manual">
    <p>manual 浮层不会因为点击外部而关闭。</p>
    <button type="button" id="close" popovertarget="manual" popovertargetaction="toggle">切换</button>
  </div>
  <p id="state">等待探测</p>
  <script>
    var tip = document.getElementById('manual');
    var changes = 0;
    tip.addEventListener('toggle', function (event) {
      changes++;
      document.getElementById('state').textContent =
        'newState=' + event.newState +
        ' / 事件数=' + changes +
        ' / popover 值=' + tip.getAttribute('popover') +
        ' / 打开=' + tip.matches(':popover-open');
    });
    document.getElementById('state').textContent =
      'popover 值=' + tip.getAttribute('popover') + ' / 初始打开=' + tip.matches(':popover-open');
  </script>
</body>
</html>''',
        "out": "点击“打开手动浮层”后浮层出现；在页面空白处点击或按 Esc（不使用 light dismiss 的 manual 类型），浮层依然存在；再点浮层内的“切换”才关闭，状态行记录每次 newState 与事件数。",
        "pit": [
            "manual 浮层没有 light dismiss，忘记提供关闭按钮会让用户卡在浮层里。",
            "多个 auto 浮层互相排他，manual 浮层则不会被自动关闭。",
            "浮层内容若包含表单，关闭时不会自动提交或重置，需要自己处理收起逻辑。",
        ],
        "ex": [("把该浮层改成 auto 类型并验证点击外部会关闭。", "只改属性值。", "<div id=\"manual\" popover=\"auto\">")],
    },
    {
        "t": "aria-describedby 与 aria-errormessage 关联",
        "level": "advanced",
        "obj": "用 aria-describedby 提供帮助文本，用 aria-errormessage 关联错误消息。",
        "pre": ["表单输入提示与错误关联", "无障碍基础：ARIA 与键盘导航"],
        "con": ["aria-describedby", "aria-errormessage", "aria-invalid", "validity", "错误可见性"],
        "explain": "`aria-describedby` 指向帮助说明，读屏会在读到控件时附上这段提示；`aria-errormessage` 指向错误文案，只有在 `aria-invalid=\"true\"` 时才会被朗读。两者都用 id 引用而不是内嵌字符串，这样既能复用样式，也能把错误节点隐藏/显示而不必反复重建元素。错误文案要与 `validity` 真实状态同步。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>错误消息关联</title></head>
<body>
  <label for="mail">邮箱</label>
  <input id="mail" name="mail" type="email" value="lin@"
    aria-describedby="mail-help" aria-errormessage="mail-error">
  <p id="mail-help">用于接收离线通知，不会联网。</p>
  <p id="mail-error" hidden></p>
  <p id="state">等待探测</p>
  <script>
    var mail = document.getElementById('mail');
    var error = document.getElementById('mail-error');
    var help = document.getElementById('mail-help');
    function check() {
      var invalid = !(mail.value && mail.validity.valid);
      error.textContent = invalid ? '请输入完整邮箱地址' : '';
      error.hidden = !invalid;
      mail.setAttribute('aria-invalid', String(invalid));
      document.getElementById('state').textContent =
        'valid=' + mail.validity.valid +
        ' / aria-invalid=' + mail.getAttribute('aria-invalid') +
        ' / 错误可见=' + (!error.hidden) +
        ' / 关联帮助=' + (document.getElementById(mail.getAttribute('aria-describedby')) === help) +
        ' / 错误文案=' + (error.textContent || 'none');
    }
    mail.addEventListener('input', check);
    check();
  </script>
</body>
</html>''',
        "out": "初始值 `lin@` 不合法，邮箱框下方出现红色提示“请输入完整邮箱地址”，探测行显示 valid=false / aria-invalid=true；补全为 `lin@example.invalid` 后提示消失，aria-invalid 变回 false。",
        "pit": [
            "aria-errormessage 必须搭配 aria-invalid=true，否则读屏不会朗读错误。",
            "把错误文案写成 placeholder 会在输入后消失，用户看不到问题所在。",
            "aria-describedby 指向隐藏元素时，某些读屏仍会朗读，应按需切换。",
        ],
        "ex": [("把帮助文本改成“仅用于离线提醒”。", "只改 mail-help 的文本。", "<p id=\"mail-help\">仅用于离线提醒。</p>")],
    },
    {
        "t": "role=alert 错误汇总与焦点移动",
        "level": "advanced",
        "obj": "用 role=alert 汇总表单错误，并把焦点移到第一个出错字段。",
        "pre": ["表单错误提示的展示", "aria-live 状态区域的播报"],
        "con": ["role=alert", "错误汇总", "焦点管理", "novalidate", "可定位错误"],
        "explain": "提交失败时，最佳实践是把所有错误汇总到一个 `role=\"alert\"` 区域（隐式 `aria-live=\"assertive\"`，会被立即播报），并把焦点移到第一个出错的字段，让键盘与读屏用户不必自己寻找问题。表单加 `novalidate` 是为了接管校验流程，从而统一走自己的汇总逻辑，而不是让浏览器弹出气泡后消失。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>错误汇总</title></head>
<body>
  <form id="signup" novalidate>
    <p><label for="user">用户名</label><input id="user" name="user" required value=""></p>
    <p><label for="pwd">密码</label><input id="pwd" name="pwd" type="password" required value=""></p>
    <p><button type="submit">注册</button></p>
  </form>
  <div id="summary" role="alert" aria-live="assertive" hidden>
    <p id="summary-text"></p>
    <ul id="summary-list"></ul>
  </div>
  <p id="state">等待探测</p>
  <script>
    var form = document.getElementById('signup');
    var summary = document.getElementById('summary');
    var list = document.getElementById('summary-list');
    var labels = { user: '用户名', pwd: '密码' };
    form.addEventListener('submit', function (event) {
      event.preventDefault();
      var fields = [document.getElementById('user'), document.getElementById('pwd')];
      var missing = fields.filter(function (field) { return !field.value; });
      while (list.firstChild) list.removeChild(list.firstChild);
      missing.forEach(function (field) {
        var item = document.createElement('li');
        item.textContent = labels[field.id] + '不能为空';
        list.appendChild(item);
      });
      summary.hidden = missing.length === 0;
      document.getElementById('summary-text').textContent =
        missing.length ? missing.length + ' 项需要修正' : '表单已通过校验';
      if (missing.length) missing[0].focus();
      document.getElementById('state').textContent =
        '错误数=' + missing.length +
        ' / 汇总可见=' + (!summary.hidden) +
        ' / 条目=' + list.children.length +
        ' / 焦点=' + document.activeElement.id;
    });
  </script>
</body>
</html>''',
        "out": "直接点“注册”时，汇总区出现“2 项需要修正”与两条“不能为空”，焦点自动跳到用户名字段；填好两项再提交后汇总隐藏，状态行显示错误数=0 与汇总可见=false。",
        "pit": [
            "少了 novalidate，浏览器原生气泡会先弹出，自定义汇总可能根本不会执行。",
            "汇总区域默认隐藏后才发现内容，部分读屏会错过第一次播报，应保留容器。",
            "焦点移到错误字段后没有提示文案关联，读屏用户仍不知道具体原因。",
        ],
        "ex": [("把错误提示改成“请填写用户名”。", "修改 labels 与文案拼接。", "item.textContent = labels[field.id] + '未填写';")],
    },
    {
        "t": "综合实战：离线工单面板",
        "level": "advanced",
        "obj": "把表单校验、表格、状态播报、折叠面板与浮层组合成一个可用的面板。",
        "pre": ["表单错误提示的展示", "表格 caption 与 headers 显式关联"],
        "con": ["组合模式", "form novalidate", "tfoot 合计", "role=status", "popover 帮助"],
        "explain": "真实页面很少只用一种元素。这个面板把已验证的独立模式拼在一起：`form` + 自定义校验、`table` + `caption`/`tfoot` 合计、`role=\"status\"` 播报总数、`details name` 折叠说明与 `popover` 帮助浮层。所有数据都留在页面内存中，不访问任何网络，新增与校验逻辑都可在离线环境中完整验证。",
        "code": '''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>离线工单面板</title>
  <style>
    body { font-family: sans-serif; }
    table { border-collapse: collapse; }
    th, td { border: 1px solid #c8cdd4; padding: 4px 8px; text-align: left; }
    #title-error { color: #d93025; }
    [popover] { border: 1px solid #c8cdd4; border-radius: 8px; padding: 10px 14px; }
  </style>
</head>
<body>
  <main>
    <h1>离线工单面板</h1>
    <form id="ticket" novalidate>
      <p>
        <label for="title">工单标题</label>
        <input id="title" name="title" required aria-describedby="title-help" aria-errormessage="title-error">
      </p>
      <p id="title-help">标题会保存到本地工单表。</p>
      <p id="title-error" hidden></p>
      <p><button type="submit" id="add">添加工单</button></p>
    </form>
    <p id="status" role="status" aria-live="polite">共 0 条工单</p>
    <table id="board">
      <caption>本地工单</caption>
      <thead><tr><th scope="col">编号</th><th scope="col">标题</th><th scope="col">状态</th></tr></thead>
      <tbody id="rows"></tbody>
      <tfoot><tr><th scope="row">合计</th><td id="total" colspan="2">0</td></tr></tfoot>
    </table>
    <details name="panel" open>
      <summary>如何离线保存？</summary>
      <p>数据只写入本地存储，不会访问网络。</p>
    </details>
    <p><button type="button" id="open-help" popovertarget="help">查看帮助</button></p>
    <div id="help" popover>
      <p>离线工单面板不会发送任何网络请求。</p>
      <button type="button" id="close-help" popovertarget="help" popovertargetaction="hide">关闭</button>
    </div>
    <p id="state">等待探测</p>
  </main>
  <script>
    var form = document.getElementById('ticket');
    var title = document.getElementById('title');
    var error = document.getElementById('title-error');
    var rows = document.getElementById('rows');
    var total = document.getElementById('total');
    var statusEl = document.getElementById('status');
    var count = 0;
    form.addEventListener('submit', function (event) {
      event.preventDefault();
      var invalid = title.value.trim() === '';
      title.setAttribute('aria-invalid', String(invalid));
      error.hidden = !invalid;
      error.textContent = invalid ? '标题不能为空' : '';
      if (invalid) {
        title.focus();
        document.getElementById('state').textContent = '校验失败，焦点=' + document.activeElement.id;
        return;
      }
      count++;
      var row = document.createElement('tr');
      var idCell = document.createElement('td');
      idCell.textContent = 'T-' + count;
      var titleCell = document.createElement('td');
      titleCell.textContent = title.value.trim();
      var stateCell = document.createElement('td');
      stateCell.textContent = '待处理';
      row.appendChild(idCell);
      row.appendChild(titleCell);
      row.appendChild(stateCell);
      rows.appendChild(row);
      total.textContent = String(count);
      statusEl.textContent = '共 ' + count + ' 条工单';
      title.value = '';
      document.getElementById('state').textContent = '已添加 / 行数=' + rows.children.length + ' / 合计=' + total.textContent;
    });
    document.getElementById('state').textContent =
      '初始行数=' + rows.children.length + ' / 合计=' + total.textContent +
      ' / 播报区=' + statusEl.getAttribute('role') +
      ' / 折叠组=' + document.querySelector('details').getAttribute('name');
  </script>
</body>
</html>''',
        "out": "面板初始显示空工单表（合计 0）、展开的说明与帮助按钮；空标题提交时出现红色“标题不能为空”并把焦点移回输入框；填入“磁盘告警”后新增一行 T-1，合计变 1，状态行播报“共 1 条工单”。",
        "pit": [
            "每次提交都重建整个 tbody 会让读屏与焦点丢失，应只追加新行。",
            "校验通过后忘记把 aria-invalid 改回 false，会一直保持错误态。",
            "帮助浮层里的按钮不写 popovertargetaction 时行为是 toggle，反复点击会开关交替。",
        ],
        "ex": [("给新增的工单行加一个“标记完成”按钮并更新状态列。", "在 stateCell 里放 button，点击后改文本为已完成。", "stateCell.appendChild(document.createElement('button'))")],
    },
]
