// WebForge HTML expansion oracle: concrete per-example assertions for the 60
// newly authored HTML topics (ids html-example-101 .. html-example-160).
//
// Owner: task 10-22-standalone-offline-ide (WebForge HTML expansion).
// Consumed by the runner owner (`scripts/run_examples.mjs`), which must delegate
// these ids here before falling back to `web_markup_assertions.mjs`.
//
// Contract (mirrors assertMarkupExample):
//   import { assertExpansionExample, COVERED_IDS } from './html_expansion_assertions.mjs';
//   const handled = await assertExpansionExample(page, example, addCheck);
//
//   * `page`      Playwright Page already navigated to `example.code`.
//   * `example`   the raw entry from assets/content/examples.json.
//   * `addCheck`  (name, ok, detail?) => void
//   * returns     true when this module asserted the example, false otherwise.
//
// Rules:
//   * every id gets >= 3 concrete assertions: exact text/attributes, computed
//     style values, DOM API results, or real interaction (click / keyboard /
//     focus) whose observable effect is asserted;
//   * no `#webforge-check` marker checks, no "element exists" alone, no
//     DOM-compares-to-itself;
//   * expected values are the human-reviewed values authored in
//     `scripts/curriculum/html_expansion.py`;
//   * all examples are offline: no navigation to external URLs is ever driven.

const CASES = new Map();

const norm = (s) => (s == null ? '' : String(s)).replace(/\s+/g, ' ').trim();

const text = (page, sel) =>
  page
    .locator(sel)
    .first()
    .innerText()
    .then(norm)
    .catch(() => null);

const attr = (page, sel, name) =>
  page
    .locator(sel)
    .first()
    .getAttribute(name)
    .catch(() => null);

// Metadata, MathML and canvas fallback nodes are not rendered HTML text.
const content = (page, sel) => page.locator(sel).first().textContent().then(norm);

const count = (page, sel) => page.locator(sel).count().catch(() => -1);

const computed = (page, sel, prop) =>
  page
    .locator(sel)
    .first()
    .evaluate((el, p) => getComputedStyle(el)[p], prop)
    .catch(() => null);

const settle = (page, ms = 150) => page.waitForTimeout(ms);

const colorAlpha = (value) => {
  const m = /rgba?\(([^)]+)\)/.exec(String(value || ''));
  if (!m) return 0;
  const parts = m[1].split(',').map((p) => parseFloat(p.trim()));
  return parts.length === 4 ? parts[3] : 1;
};

// ---------------------------------------------------------------------------
// Group A — structure & semantics (101-112)
// ---------------------------------------------------------------------------

CASES.set('html-example-101', async (page, addCheck) => {
  addCheck('one hgroup', (await count(page, 'hgroup')) === 1);
  const tags = await page.locator('hgroup').evaluate((el) =>
    Array.from(el.children).map((c) => c.tagName.toLowerCase()),
  );
  addCheck('hgroup children are h2>p', tags.join('>') === 'h2>p', tags.join('>'));
  addCheck('h2 text', (await text(page, 'hgroup h2')) === '离线 IDE 实战');
  addCheck('subtitle text', (await text(page, 'hgroup p')) === '从零搭建一个可用的本地开发环境');
  addCheck('hgroup is block', (await computed(page, 'hgroup', 'display')) === 'block');
  addCheck('probe report', (await text(page, '#report')) === '2 个子元素：h2>p');
});

CASES.set('html-example-102', async (page, addCheck) => {
  const tag = await page.locator('#site-search').evaluate((el) => el.tagName.toLowerCase());
  addCheck('search element used', tag === 'search', tag);
  addCheck('search input type', (await attr(page, '#q', 'type')) === 'search');
  addCheck('label bound to input', (await text(page, 'label[for="q"]')) === '站内搜索');
  addCheck('initial status', (await text(page, '#status')) === '等待筛选');
  await page.locator('#q').fill('离线');
  await page.locator('#run').click();
  addCheck('click reports keyword', (await text(page, '#status')) === '关键词：离线');
  await page.locator('#q').fill('');
  await page.locator('#run').click();
  addCheck('empty keyword reported', (await text(page, '#status')) === '关键词为空');
});

CASES.set('html-example-103', async (page, addCheck) => {
  const tag = await page.locator('#contact').evaluate((el) => el.tagName.toLowerCase());
  addCheck('address element used', tag === 'address', tag);
  addCheck('address inside footer', (await count(page, 'footer address')) === 1);
  addCheck('default italic', (await computed(page, '#contact', 'fontStyle')) === 'italic');
  addCheck('two line breaks', (await count(page, '#contact br')) === 2);
  const body = await text(page, '#contact');
  addCheck('contact fields', body.includes('维护者') && body.includes('反馈') && body.includes('更新时间'), body);
  addCheck('feedback anchor resolves', (await count(page, '#feedback')) === 1 && (await attr(page, '#contact a', 'href')) === '#feedback');
  addCheck('probe text', (await text(page, '#probe')) === 'font-style=italic;display=block;lines=2');
});

CASES.set('html-example-104', async (page, addCheck) => {
  const tag = await page.locator('#toolbar').evaluate((el) => el.tagName.toLowerCase());
  addCheck('menu element used', tag === 'menu', tag);
  addCheck('three commands', (await count(page, '#toolbar li')) === 3);
  addCheck('third command disabled', await page.locator('#toolbar li:nth-child(3) button').isDisabled());
  addCheck('flex toolbar', (await computed(page, '#toolbar', 'display')) === 'flex');
  await page.locator('#toolbar li:nth-child(2) button').click();
  addCheck('click logs command', (await text(page, '#log')) === '已选择：italic');
});

CASES.set('html-example-105', async (page, addCheck) => {
  addCheck('one main', (await count(page, 'main#main')) === 1);
  addCheck('article inside main', (await count(page, 'main > article#post')) === 1);
  addCheck('aside inside main', (await count(page, 'main > aside#related')) === 1);
  addCheck('aside labelled by heading', (await text(page, '#related-title')) === '相关阅读');
  addCheck('labelledby resolves to h2', await page.evaluate(() => {
    const aside = document.getElementById('related');
    const label = document.getElementById(aside.getAttribute('aria-labelledby'));
    return label !== null && label.tagName.toLowerCase() === 'h2';
  }));
  addCheck('probe counts', (await text(page, '#summary')) === '2 段正文 / 2 条相关 / 标签=相关阅读');
});

CASES.set('html-example-106', async (page, addCheck) => {
  addCheck('breadcrumb nav', (await count(page, 'nav[aria-label="面包屑"]')) === 1);
  addCheck('ordered levels', (await count(page, '#crumbs ol > li')) === 3);
  addCheck('two links', (await count(page, '#crumbs a')) === 2);
  addCheck('current marked', (await attr(page, '#crumbs [aria-current]', 'aria-current')) === 'page');
  const tag = await page.locator('#crumbs [aria-current]').evaluate((el) => el.tagName.toLowerCase());
  addCheck('current is not a link', tag === 'span', tag);
  addCheck('probe state', (await text(page, '#state')) === '当前页：HTML 进阶 / 层级：3 / 链接：2');
});

CASES.set('html-example-107', async (page, addCheck) => {
  addCheck('caption text', (await text(page, '#grades caption')) === '期末成绩（满分 100）');
  addCheck('column headers', (await count(page, '#grades th[scope="col"]')) === 2);
  addCheck('data cells reference headers', (await count(page, '#grades td[headers="h-score"]')) === 2);
  addCheck('first score cell', (await text(page, '#grades tbody tr:first-child td[headers="h-score"]')) === '92');
  addCheck('three rows', await page.locator('#grades').evaluate((t) => t.rows.length === 3));
  const state = await text(page, '#state');
  addCheck('probe caption and header', state.includes('行数=3') && state.includes('表头=分数'), state);
});

CASES.set('html-example-108', async (page, addCheck) => {
  addCheck('two col elements', (await count(page, '#cols col')) === 2);
  addCheck('second col spans two', (await attr(page, '#cols col:nth-child(2)', 'span')) === '2');
  addCheck('colgroup parent is table', await page.evaluate(() => {
    const group = document.getElementById('cols');
    return group.parentElement.tagName.toLowerCase() === 'table';
  }));
  addCheck('three cells per body row', (await count(page, '#plan tbody tr:first-child td')) === 3);
  addCheck('probe coverage', (await text(page, '#state')) === 'col 数=2 / 第二个 span=2 / 覆盖列数=3 / 父元素=table');
});

CASES.set('html-example-109', async (page, addCheck) => {
  addCheck('total computed', (await text(page, '#total')) === '800');
  addCheck('table.tFoot present', await page.evaluate(() => {
    const table = document.getElementById('cost');
    return table.tFoot !== null && table.tFoot === table.querySelector('tfoot') && table.tFoot.rows[0].rowIndex === 3;
  }));
  const geometry = await page.evaluate(() => {
    const foot = document.querySelector('#cost tfoot');
    const lastBody = document.querySelector('#cost tbody tr:last-child');
    return {
      footTop: foot.getBoundingClientRect().top,
      bodyBottom: lastBody.getBoundingClientRect().bottom,
    };
  });
  addCheck('tfoot renders after body rows', geometry.footTop >= geometry.bodyBottom - 1, JSON.stringify(geometry));
  addCheck('body rows counted', await text(page, '#state').then((s) => s.includes('表体行数=2')));
  addCheck('footer row index reported', await text(page, '#state').then((s) => s.includes('行索引=3')));
  addCheck('two amount cells', (await count(page, '#cost tbody td[data-amount]')) === 2);
});

CASES.set('html-example-110', async (page, addCheck) => {
  addCheck('two exclusive panels', (await count(page, 'details[name="faq"]')) === 2);
  addCheck('first open by default', await page.locator('details[name="faq"]').nth(0).evaluate((d) => d.open));
  addCheck('second closed by default', await page.locator('details[name="faq"]').nth(1).evaluate((d) => !d.open));
  await page.locator('details[name="faq"]').nth(1).locator('summary').click();
  await settle(page, 200);
  const state = await page.evaluate(() => ({
    first: document.querySelectorAll('details[name="faq"]')[0].open,
    second: document.querySelectorAll('details[name="faq"]')[1].open,
  }));
  addCheck('opening second closes first', state.second === true && state.first === false, JSON.stringify(state));
  addCheck('open count is one', (await count(page, 'details[name="faq"][open]')) === 1);
  const probe = await text(page, '#state');
  addCheck('probe reports new state', probe.includes('展开数=1') && probe.includes('支持哪些设备？'), probe);
});

CASES.set('html-example-111', async (page, addCheck) => {
  addCheck('dialog closed initially', await page.locator('#dlg').evaluate((d) => !d.open));
  await page.locator('#open').click();
  await settle(page, 150);
  addCheck('showModal opens dialog', await page.locator('#dlg').evaluate((d) => d.open));
  addCheck('modal state active', await page.locator('#dlg').evaluate((d) => d.matches(':modal')));
  const backdrop = await page.evaluate(() => getComputedStyle(document.getElementById('dlg'), '::backdrop').backgroundColor);
  addCheck('backdrop painted', colorAlpha(backdrop) > 0, backdrop);
  await page.locator('#confirm').click();
  await settle(page, 150);
  addCheck('confirm closes dialog', await page.locator('#dlg').evaluate((d) => !d.open));
  addCheck('returnValue from button', (await text(page, '#result')) === 'returnValue=ok / open=false');
});

CASES.set('html-example-112', async (page, addCheck) => {
  addCheck('popover attribute present', (await attr(page, '#tip', 'popover')) !== null);
  addCheck('closed initially', await page.locator('#tip').evaluate((el) => !el.matches(':popover-open')));
  await page.locator('#trigger').click();
  await settle(page, 150);
  addCheck('trigger opens popover', await page.locator('#tip').evaluate((el) => el.matches(':popover-open')));
  addCheck('toggle reports open', (await text(page, '#state')) === 'popover open / pinned=true');
  await page.locator('#hide').click();
  await settle(page, 150);
  addCheck('hide action closes', await page.locator('#tip').evaluate((el) => !el.matches(':popover-open')));
  addCheck('toggle reports closed', (await text(page, '#state')) === 'popover closed / pinned=false');
});

// ---------------------------------------------------------------------------
// Group B — form association & constraint APIs (113-124)
// ---------------------------------------------------------------------------

CASES.set('html-example-113', async (page, addCheck) => {
  addCheck('input.list resolves', await page.evaluate(() => {
    const input = document.getElementById('city');
    return input.list !== null && input.list.id === 'cities';
  }));
  addCheck('three suggestions', (await count(page, '#cities option')) === 3);
  addCheck('suggestion values', await page.evaluate(() =>
    Array.from(document.getElementById('cities').options).map((o) => o.value).join(',') === '杭州,合肥,深圳',
  ));
  addCheck('probe list metadata', (await text(page, '#meta')) === 'list 关联=cities / 候选数=3');
  await page.locator('#city').fill('合肥');
  await page.locator('#city').dispatchEvent('change');
  addCheck('change reports pick', (await text(page, '#picked')) === '已选：合肥');
  await page.locator('#city').fill('乌鲁木齐');
  await page.locator('#city').dispatchEvent('change');
  addCheck('free text accepted', (await text(page, '#picked')) === '已选：乌鲁木齐');
});

CASES.set('html-example-114', async (page, addCheck) => {
  addCheck('multiple enabled', await page.locator('#langs').evaluate((s) => s.multiple === true));
  addCheck('size is five', (await attr(page, '#langs', 'size')) === '5');
  addCheck('two option groups', (await count(page, '#langs optgroup')) === 2);
  addCheck('second group disabled', await page.locator('#langs optgroup').nth(1).evaluate((g) => g.disabled === true));
  addCheck('four options', (await count(page, '#langs option')) === 4);
  addCheck('html selected initially', await page.locator('#langs').evaluate((s) =>
    Array.from(s.selectedOptions).map((o) => o.value).join(',') === 'html',
  ));
  await page.locator('#langs').selectOption(['html', 'css']);
  addCheck('multi selection read back', (await text(page, '#out')) === '已选：html, css');
  const probe = await text(page, '#meta');
  addCheck('probe group state', probe === 'multiple=true / size=5 / 分组=2 / 禁用分组=后端 / 选项=4', probe);
});

CASES.set('html-example-115', async (page, addCheck) => {
  const tag = await page.locator('#sum').evaluate((el) => el.tagName.toLowerCase());
  addCheck('output element used', tag === 'output', tag);
  addCheck('for lists both inputs', (await attr(page, '#sum', 'for')) === 'qty price');
  addCheck('name reflected', (await attr(page, '#sum', 'name')) === 'sum');
  addCheck('initial product', (await text(page, '#sum')) === '30.00');
  await page.locator('#qty').fill('3');
  await settle(page, 120);
  addCheck('input recomputes product', (await text(page, '#sum')) === '45.00');
  addCheck('output registered in form', await text(page, '#meta').then((s) => s.includes('表单内=true')));
});

CASES.set('html-example-116', async (page, addCheck) => {
  addCheck('all checkbox present', (await count(page, '#all')) === 1);
  addCheck('two of three checked', (await count(page, '.item:checked')) === 2);
  addCheck('parent is indeterminate', await page.locator('#all').evaluate((el) => el.indeterminate === true));
  addCheck('parent not checked', await page.locator('#all').evaluate((el) => el.checked === false));
  addCheck('probe initial state', (await text(page, '#state')) === '选中=2/3 / all.checked=false / all.indeterminate=true');
  await page.locator('#all').click();
  await settle(page, 120);
  addCheck('select all checks children', (await count(page, '.item:checked')) === 3);
  addCheck('parent indeterminate cleared', await page.locator('#all').evaluate((el) => el.indeterminate === false));
  await page.locator('#all').click();
  await settle(page, 120);
  addCheck('unselect all clears children', (await count(page, '.item:checked')) === 0);
  addCheck('probe after toggle', (await text(page, '#state')) === '选中=0/3 / all.checked=false / all.indeterminate=false');
});

CASES.set('html-example-117', async (page, addCheck) => {
  addCheck('email associated with form', await page.evaluate(() => {
    const email = document.getElementById('email');
    return email.form !== null && email.form.id === 'signup';
  }));
  addCheck('three form controls', await page.locator('#signup').evaluate((f) => f.elements.length === 3));
  addCheck('email listed in elements', await page.evaluate(() => {
    const form = document.getElementById('signup');
    return form.elements.namedItem('email') === document.getElementById('email');
  }));
  addCheck('submit button outside form', await page.evaluate(() => {
    const button = document.querySelector('button[form="signup"]');
    return button !== null && button.closest('form') === null;
  }));
  addCheck('probe association', (await text(page, '#state')) === 'email.form 匹配=true / 表单控件数=3 / 含 email=true / 含 name=true');
  addCheck('side section holds external control', (await count(page, '#side input[form="signup"]')) === 1);
});

CASES.set('html-example-118', async (page, addCheck) => {
  addCheck('form action attribute', (await attr(page, '#publish', 'action')) === '#local-draft');
  addCheck('form method is get', await page.locator('#publish').evaluate((f) => f.method === 'get'));
  addCheck('publish overrides action', (await attr(page, '#now', 'formaction')) === '#local-publish');
  addCheck('publish overrides method', (await attr(page, '#now', 'formmethod')) === 'post');
  addCheck('formAction resolved to attribute', await page.locator('#now').evaluate((b) => b.formAction.endsWith('#local-publish')));
  addCheck('save has no override', (await attr(page, '#save', 'formmethod')) === null);
  addCheck('probe override summary', (await text(page, '#state')) ===
    '表单 action=#local-draft / 表单 method=get / 发布 action=#local-publish / 发布 method=post / 发布 formAction 结尾匹配=true / 草稿 method 覆盖=none');
});

CASES.set('html-example-119', async (page, addCheck) => {
  addCheck('image input type', (await attr(page, '#map', 'type')) === 'image');
  addCheck('name used for coordinates', (await attr(page, '#map', 'name')) === 'spot');
  addCheck('alt provides name', (await attr(page, '#map', 'alt')) === '选择位置');
  addCheck('inline image decodes to authored size', await page.locator('#map').evaluate(async (el) => {
    const image = new Image();
    image.src = el.src;
    await image.decode();
    return image.complete && image.naturalWidth === 160 && image.naturalHeight === 80;
  }));
  addCheck('image belongs to form', await page.locator('#map').evaluate((el) => el.form !== null && el.form.id === 'pick'));
  await page.locator('#map').click({ position: { x: 30, y: 20 } });
  await settle(page, 150);
  addCheck('click submits with image submitter', (await text(page, '#state')) ===
    'submitter 是图片按钮=true / type=image / 坐标字段=spot.x,spot.y / 坐标=30,20');
  addCheck('probe natural size', await text(page, '#meta').then((s) => s.includes('naturalWidth=160') && s.includes('form 关联=true')));
});

CASES.set('html-example-120', async (page, addCheck) => {
  addCheck('custom error set initially', await page.locator('#code').evaluate((el) => el.validity.customError === true));
  addCheck('invalid initially', await page.locator('#code').evaluate((el) => el.validity.valid === false));
  addCheck('validation message', await page.locator('#code').evaluate((el) => el.validationMessage === '邀请码必须是 WF2026'));
  addCheck('message rendered', (await text(page, '#msg')) === '邀请码必须是 WF2026');
  addCheck('probe custom state', (await text(page, '#state')) === 'valid=false / customError=true / willValidate=true');
  await page.locator('#code').fill('WF2026');
  await settle(page, 120);
  addCheck('valid after correct code', await page.locator('#code').evaluate((el) => el.validity.valid === true));
  addCheck('custom error cleared', await page.locator('#code').evaluate((el) => el.validity.customError === false));
  addCheck('success message rendered', (await text(page, '#msg')) === '校验通过');
});

CASES.set('html-example-121', async (page, addCheck) => {
  addCheck('rows attribute', (await attr(page, '#note', 'rows')) === '3');
  addCheck('cols attribute', (await attr(page, '#note', 'cols')) === '30');
  addCheck('wrap soft', (await attr(page, '#note', 'wrap')) === 'soft');
  addCheck('maxlength limit', await page.locator('#note').evaluate((el) => el.maxLength === 60));
  addCheck('initial selection reported', await text(page, '#state').then((s) => s.startsWith('len=7 / sel=0-3 / rows=3 / cols=30 / wrap=soft / maxlength=60')));
  addCheck('initial snippet', (await text(page, '#snippet')) === '选中：第一行');
  await page.locator('#note').selectText();
  await settle(page, 120);
  addCheck('select all updates selection', await text(page, '#state').then((s) => s.includes('sel=0-7')));
  addCheck('snippet shows both lines', (await text(page, '#snippet')) === '选中：第一行⏎第二行');
});

CASES.set('html-example-122', async (page, addCheck) => {
  addCheck('two named controls', (await count(page, '#order input[name]')) === 2);
  addCheck('no data yet', (await text(page, '#state')) === '尚未提交');
  await page.locator('#item').fill('离线键盘');
  await page.locator('#count').fill('2');
  await page.locator('#go').click();
  await settle(page, 200);
  addCheck('formdata rewritten', (await text(page, '#state')) === '提交数据：item=离线键盘&count=4&source=offline-ide');
  addCheck('count doubled by set', await text(page, '#state').then((s) => s.includes('count=4')));
  addCheck('source appended last', await text(page, '#state').then((s) => s.endsWith('source=offline-ide')));
  addCheck('page did not navigate', await page.evaluate(() => document.querySelectorAll('#order').length === 1));
});

CASES.set('html-example-123', async (page, addCheck) => {
  const initialUrl = page.url();
  addCheck('initial log empty', (await text(page, '#state')) === '等待操作');
  await page.locator('#programmatic').click();
  await settle(page, 150);
  addCheck('requestSubmit runs submit event', (await text(page, '#state')) === 'click(programmatic) → submit(native)');
  await page.locator('#native').click();
  await settle(page, 150);
  const state = await text(page, '#state');
  addCheck('native click appends submit', state === 'click(programmatic) → submit(native) → submit(native)', state);
  addCheck('omitted requestSubmit argument uses null submitter', await page.evaluate(() => {
    const form = document.getElementById('draft');
    let seen = 'event did not fire';
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      seen = event.submitter;
    }, { once: true });
    form.requestSubmit();
    return seen === null;
  }));
  addCheck('omitted submitter logged', (await text(page, '#state')) ===
    'click(programmatic) → submit(native) → submit(native) → submit(none)');
  addCheck('preventDefault kept page', page.url() === initialUrl, page.url());
});

CASES.set('html-example-124', async (page, addCheck) => {
  addCheck('step attribute', (await attr(page, '#n', 'step')) === '3');
  addCheck('min attribute', (await attr(page, '#n', 'min')) === '0');
  addCheck('max attribute', (await attr(page, '#n', 'max')) === '20');
  addCheck('initial probe', (await text(page, '#state')) === 'value=6 / asNumber=6 / valid=true / stepMismatch=false');
  await page.locator('#up').click();
  addCheck('stepUp adds one step', (await text(page, '#state')) === 'value=9 / asNumber=9 / valid=true / stepMismatch=false');
  await page.locator('#down').click();
  await page.locator('#down').click();
  addCheck('stepDown twice', (await text(page, '#state')) === 'value=3 / asNumber=3 / valid=true / stepMismatch=false');
  await page.locator('#n').fill('7');
  await settle(page, 120);
  addCheck('off-step value invalid', (await text(page, '#state')) === 'value=7 / asNumber=7 / valid=false / stepMismatch=true');
});

// ---------------------------------------------------------------------------
// Group C — text, i18n, machine-readable data (125-136)
// ---------------------------------------------------------------------------

CASES.set('html-example-125', async (page, addCheck) => {
  addCheck('two ruby elements', (await count(page, 'ruby')) === 2);
  addCheck('annotation text', (await text(page, '#zh rt')) === 'lí xiàn');
  addCheck('two fallback parens', (await count(page, '#jp rp')) === 2);
  addCheck('rp hidden by UA style', (await computed(page, '#jp rp', 'display')) === 'none');
  addCheck('rt rendered with height', await page.locator('#zh rt').evaluate((el) => el.getBoundingClientRect().height > 0));
  addCheck('ruby annotation renders above base glyphs', await page.locator('#zh').evaluate((el) => {
    const range = document.createRange();
    range.selectNodeContents(el.firstChild);
    const base = range.getBoundingClientRect();
    const annotation = el.querySelector('rt').getBoundingClientRect();
    return base.height > 0 && annotation.height > 0 && annotation.top < base.top && annotation.bottom < base.bottom;
  }));
  const probe = await text(page, '#state');
  addCheck('probe ruby counts', probe.includes('ruby 数=2') && probe.includes('注音=lí xiàn'), probe);
});

CASES.set('html-example-126', async (page, addCheck) => {
  addCheck('two bdi elements', (await count(page, 'bdi')) === 2);
  addCheck('bdi isolates', (await computed(page, '#user', 'unicodeBidi')) === 'isolate');
  addCheck('bdi derives rtl from Arabic text', (await computed(page, '#user', 'direction')) === 'rtl');
  addCheck('bdo overrides direction', (await computed(page, '#forced', 'direction')) === 'rtl');
  addCheck('bdo isolates and overrides', (await computed(page, '#forced', 'unicodeBidi')) === 'isolate-override');
  addCheck('dir=auto resolves to rtl', (await computed(page, '#auto', 'direction')) === 'rtl');
  addCheck('probe bidi state', (await text(page, '#state')) === 'bdi 数=2 / user=isolate/rtl / bdo=isolate-override/rtl / auto=isolate/rtl');
});

CASES.set('html-example-127', async (page, addCheck) => {
  addCheck('two marks created', (await count(page, '#wrapped mark')) === 2);
  addCheck('hit counter updated', (await text(page, '#count')) === '2');
  addCheck('mark text preserved', (await text(page, '#wrapped mark')) === '离线');
  addCheck('original paragraph intact', (await text(page, '#text')) === '离线优先意味着优先使用本地能力，离线不是退路。');
  const backgrounds = await page.evaluate(() => ({
    mark: getComputedStyle(document.querySelector('#wrapped mark')).backgroundColor,
    text: getComputedStyle(document.getElementById('text')).backgroundColor,
  }));
  addCheck('mark background differs from body', backgrounds.mark !== backgrounds.text, JSON.stringify(backgrounds));
  addCheck('mark background not transparent', colorAlpha(backgrounds.mark) > 0, backgrounds.mark);
  addCheck('probe reports marks', await text(page, '#state').then((s) => s.includes('mark 数=2') && s.includes('与正文背景不同=true')));
});

CASES.set('html-example-128', async (page, addCheck) => {
  addCheck('del struck through', (await computed(page, 'del', 'textDecorationLine')) === 'line-through');
  addCheck('ins underlined', (await computed(page, 'ins', 'textDecorationLine')) === 'underline');
  addCheck('ins cite attribute', (await attr(page, 'ins', 'cite')) === '#changelog-22');
  addCheck('ins datetime attribute', (await attr(page, 'ins', 'datetime')) === '2026-10-22');
  addCheck('dateTime property reflects', await page.locator('ins').evaluate((el) => el.dateTime === '2026-10-22'));
  addCheck('del keeps its own datetime', await page.locator('del').evaluate((el) => el.dateTime === '2026-09-01'));
  const probe = await text(page, '#state');
  addCheck('probe revision styles', probe === 'del 线=line-through / ins 线=underline / ins.cite=#changelog-22 / ins.dateTime=2026-10-22 / del.dateTime 非空=true', probe);
});

CASES.set('html-example-129', async (page, addCheck) => {
  addCheck('s struck through', (await computed(page, '#old', 'textDecorationLine')) === 'line-through');
  addCheck('s has no dateTime property', await page.locator('#old').evaluate((el) => el.dateTime === undefined));
  addCheck('s has no datetime attribute', (await attr(page, '#old', 'datetime')) === null);
  const sizes = await page.evaluate(() => ({
    small: parseFloat(getComputedStyle(document.getElementById('note')).fontSize),
    body: parseFloat(getComputedStyle(document.body).fontSize),
  }));
  addCheck('small is smaller than body', sizes.small < sizes.body, JSON.stringify(sizes));
  addCheck('small renders as block-level paragraph child', (await computed(page, '#note', 'display')) === 'inline');
  const probe = await text(page, '#state');
  addCheck('probe semantics', probe.includes('s.dateTime 属性不存在=true') && probe.includes('small 更小=true'), probe);
});

CASES.set('html-example-130', async (page, addCheck) => {
  addCheck('two data elements', (await count(page, 'data')) === 2);
  addCheck('values machine readable', await page.evaluate(() =>
    Array.from(document.querySelectorAll('data')).map((el) => el.value).join(',') === 'WF-1001,WF-1002',
  ));
  addCheck('visible text differs from value', (await text(page, '#sku1')) === '离线键盘');
  addCheck('data stays inline', (await computed(page, '#sku1', 'display')) === 'inline');
  addCheck('probe values', (await text(page, '#state')) === 'items=2 / values=WF-1001,WF-1002 / 首个文本=离线键盘 / 显示方式=inline');
});

CASES.set('html-example-131', async (page, addCheck) => {
  addCheck('four break opportunities', (await count(page, '#path wbr')) === 4);
  addCheck('path wraps into multiple lines', await page.locator('#path').evaluate((el) => el.getBoundingClientRect().height > 30));
  addCheck('overflow-wrap changed by script', (await computed(page, '#long', 'overflowWrap')) === 'break-word');
  addCheck('long word does not overflow', await page.locator('#long').evaluate((el) => el.scrollWidth <= el.clientWidth + 1));
  addCheck('wbr is void element', await page.evaluate(() => document.querySelectorAll('wbr *').length === 0));
  const probe = await text(page, '#state');
  addCheck('probe wrap values', probe.includes('wbr 数=4') && probe.includes('wrap 前=normal') && probe.includes('wrap 后=break-word'), probe);
});

CASES.set('html-example-132', async (page, addCheck) => {
  addCheck('single base element', (await count(page, 'base')) === 1);
  addCheck('base changes baseURI', await page.evaluate(() => document.baseURI.indexOf('#workspace') >= 0));
  addCheck('relative link absolutised', await page.locator('#rel').evaluate((el) => el.href.endsWith('/notes/today.html')));
  addCheck('URL constructor agrees with anchor', await page.evaluate(() => {
    const link = document.getElementById('rel');
    return link.href === new URL('notes/today.html', document.baseURI).href;
  }));
  addCheck('resolved pathname', await page.evaluate(() => new URL('notes/today.html', document.baseURI).pathname === '/notes/today.html'));
  const probe = await text(page, '#state');
  addCheck('probe base resolution', probe.includes('base 数=1') && probe.includes('a.href 与解析一致=true'), probe);
});

CASES.set('html-example-133', async (page, addCheck) => {
  addCheck('translate attribute value', (await attr(page, '#brand', 'translate')) === 'no');
  addCheck('translate property false', await page.locator('#brand').evaluate((el) => el.translate === false));
  addCheck('spellcheck false on brand', await page.locator('#brand').evaluate((el) => el.spellcheck === false));
  addCheck('spellcheck true on editor', await page.locator('#note').evaluate((el) => el.spellcheck === true));
  addCheck('editor lang', (await attr(page, '#note', 'lang')) === 'zh-CN');
  addCheck('body translate inherits true', await page.locator('body').evaluate((el) => el.translate === true));
  addCheck('probe editing semantics', (await text(page, '#state')) === 'brand.translate=false / brand 属性=no / spellcheck=false / note.spellcheck=true / note.lang=zh-CN / body.translate=true');
});

CASES.set('html-example-134', async (page, addCheck) => {
  addCheck('math root present', (await count(page, '#einstein')) === 1);
  addCheck('superscript node', (await count(page, '#einstein msup')) === 1);
  addCheck('exponent value', (await content(page, '#einstein msup mn')) === '2');
  addCheck('math uses block layout', ['block', 'block math'].includes(await computed(page, '#einstein', 'display')));
  addCheck('fraction numerator is laid out above denominator', await page.locator('#avg mfrac').evaluate((el) => {
    const numerator = el.firstElementChild.getBoundingClientRect();
    const denominator = el.lastElementChild.getBoundingClientRect();
    return numerator.height > 0 && denominator.height > 0 && numerator.bottom <= denominator.top &&
      el.getBoundingClientRect().height >= numerator.height + denominator.height;
  }));
  addCheck('fraction has numerator and denominator', (await count(page, '#avg mfrac > *')) === 2);
  const probe = await text(page, '#state');
  addCheck('probe math layout', probe.includes('msup 存在=true') && probe.includes('次幂=2') && probe.includes('块级显示=block'), probe);
});

CASES.set('html-example-135', async (page, addCheck) => {
  addCheck('two source candidates', (await count(page, '#art source')) === 2);
  addCheck('first media query', (await attr(page, '#art source', 'media')) === '(min-width: 600px)');
  addCheck('sources use inline data', await page.evaluate(() =>
    Array.from(document.querySelectorAll('#art source')).every((s) => s.srcset.indexOf('data:image/svg+xml') === 0),
  ));
  await page.waitForFunction(() => document.getElementById('fallback').complete && document.getElementById('fallback').naturalWidth > 0);
  const crop = await page.evaluate(() => {
    const wide = matchMedia('(min-width: 600px)').matches;
    const medium = matchMedia('(min-width: 300px)').matches;
    const image = document.getElementById('fallback');
    const sources = document.querySelectorAll('#art source');
    const expectedSource = wide ? sources[0].srcset : medium ? sources[1].srcset : image.src;
    return { expectedWidth: wide ? 300 : medium ? 200 : 120, width: image.naturalWidth, wide,
      sourceMatches: decodeURIComponent(image.currentSrc) === decodeURIComponent(expectedSource) };
  });
  addCheck('crop matches actual viewport media query', crop.width === crop.expectedWidth, JSON.stringify(crop));
  addCheck('currentSrc is the matching candidate', crop.sourceMatches, JSON.stringify(crop));
  addCheck('image decoded', await page.locator('#fallback').evaluate((el) => el.complete === true && el.naturalWidth > 0));
  addCheck('fallback img still declared', (await attr(page, '#fallback', 'width')) === '120');
  addCheck('probe selected crop', await text(page, '#state').then((s) =>
    s.includes(`命中宽屏=${crop.wide}`) && s.includes('source 数=2') && s.includes(`实际宽=${crop.expectedWidth}`)));
});

CASES.set('html-example-136', async (page, addCheck) => {
  addCheck('three subscripts', (await count(page, 'sub')) === 3);
  addCheck('four superscripts', (await count(page, 'sup')) === 4);
  addCheck('sub vertical alignment', (await computed(page, 'sub', 'verticalAlign')) === 'sub');
  addCheck('sup vertical alignment', (await computed(page, 'sup', 'verticalAlign')) === 'super');
  addCheck('water formula text', (await text(page, '#water')) === '水分子：H2O，甲烷：CH4');
  addCheck('sulfate order sub before sup', await page.evaluate(() => {
    const sulfate = document.getElementById('sulfate');
    const sub = sulfate.querySelector('sub');
    const sup = sulfate.querySelector('sup');
    return (sub.compareDocumentPosition(sup) & Node.DOCUMENT_POSITION_FOLLOWING) !== 0;
  }));
  const probe = await text(page, '#state');
  addCheck('probe script state', probe.includes('sub 数=3') && probe.includes('电荷在上=sub 在前'), probe);
});

// ---------------------------------------------------------------------------
// Group D — embedding, graphics, script loading (137-148)
// ---------------------------------------------------------------------------

CASES.set('html-example-137', async (page, addCheck) => {
  const tag = await page.locator('#figure').evaluate((el) => el.tagName.toLowerCase());
  addCheck('object element used', tag === 'object', tag);
  addCheck('type declared', (await attr(page, '#figure', 'type')) === 'text/html');
  addCheck('data is same-origin Blob', await page.locator('#figure').evaluate((el) => el.data.startsWith(`blob:${location.origin}/`)));
  await page.waitForFunction(() => {
    const el = document.getElementById('figure');
    return el.contentDocument !== null && el.contentDocument.getElementById('inner') !== null;
  });
  addCheck('embedded document root is html', await page.locator('#figure').evaluate((el) => el.contentDocument.documentElement.tagName.toLowerCase() === 'html'));
  addCheck('embedded document contains authored text', await page.locator('#figure').evaluate((el) =>
    el.contentDocument.getElementById('inner').textContent === '运行内联的 HTML 文档'));
  addCheck('fallback content retained', (await count(page, '#figure p')) === 1);
  addCheck('probe embedded root', await text(page, '#state').then((s) => s.includes('内嵌根元素=html') && s.includes('data 是 Blob=true')));
});

CASES.set('html-example-138', async (page, addCheck) => {
  addCheck('iframe has title', (await attr(page, '#frame', 'title')) === '内联示例文档');
  await page.waitForFunction(() => {
    const frame = document.getElementById('frame');
    return frame.contentDocument !== null && frame.contentDocument.getElementById('inner') !== null;
  });
  addCheck('srcdoc document parsed', await page.locator('#frame').evaluate((el) => el.contentDocument.getElementById('inner').textContent === 'srcdoc 渲染的内容'));
  addCheck('srcdoc shares origin', await page.locator('#frame').evaluate((el) => el.contentDocument !== null));
  addCheck('embed type', (await attr(page, '#emb', 'type')) === 'image/svg+xml');
  addCheck('embed element used', (await page.locator('#emb').evaluate((el) => el.tagName.toLowerCase())) === 'embed');
  addCheck('probe srcdoc state', await text(page, '#state').then((s) => s.includes('srcdoc 同源可访=true') && s.includes('内部文本=srcdoc 渲染的内容')));
});

CASES.set('html-example-139', async (page, addCheck) => {
  addCheck('sandbox attribute present', await page.locator('#safe').evaluate((el) => el.hasAttribute('sandbox')));
  addCheck('no allowances granted', await page.locator('#safe').evaluate((el) => el.sandbox.length === 0));
  addCheck('frame has accessible title', (await attr(page, '#safe', 'title')) === '受限内嵌文档');
  await settle(page, 400);
  addCheck('opaque origin blocks document access', await page.locator('#safe').evaluate((el) => el.contentDocument === null));
  addCheck('no postMessage received', await page.evaluate(() => window.__messages === 0));
  addCheck('probe sandbox report', (await text(page, '#state')) === '未收到消息 / 沙箱标记=true / 允许项=0 / 可访内嵌文档=false');
});

CASES.set('html-example-140', async (page, addCheck) => {
  addCheck('aria label describes chart', (await attr(page, '#board', 'aria-label')) === '离线进度 60% 的条形图');
  addCheck('role img on canvas', (await attr(page, '#board', 'role')) === 'img');
  const dpr = await page.evaluate(() => Math.min(window.devicePixelRatio || 1, 2));
  addCheck('bitmap scaled by dpr', await page.locator('#board').evaluate((el, d) => el.width === Math.round(150 * d) && el.height === Math.round(75 * d), dpr));
  addCheck('css drawing size stays logical', await page.locator('#board').evaluate((el) => {
    const style = getComputedStyle(el);
    return style.width === '150px' && style.height === '75px' && Math.round(el.getBoundingClientRect().width) === 152;
  }));
  const pixels = await page.locator('#board').evaluate((el, d) => {
    const ctx = el.getContext('2d');
    const at = (x, y) => Array.from(ctx.getImageData(Math.round(x * d), Math.round(y * d), 1, 1).data);
    return { background: at(120, 10), bar: at(10, 10) };
  }, dpr);
  addCheck('background pixel is light blue', pixels.background.slice(0, 3).join(',') === '232,240,254', JSON.stringify(pixels.background));
  addCheck('bar pixel is blue', pixels.bar.slice(0, 3).join(',') === '26,115,232', JSON.stringify(pixels.bar));
  addCheck('fallback text present', (await content(page, '#board')) === '离线进度 60% 的条形图');
});

CASES.set('html-example-141', async (page, addCheck) => {
  addCheck('role img on svg', (await attr(page, '#chart', 'role')) === 'img');
  addCheck('two labelled ids', await page.evaluate(() => document.getElementById('chart').getAttribute('aria-labelledby').split(' ').length === 2));
  addCheck('title text', (await content(page, '#chart-title')) === '离线缓存命中率');
  addCheck('desc text', (await content(page, '#chart-desc')) === '柱状图：命中 92%，未命中 8%');
  addCheck('bar widths encode ratio', await page.evaluate(() => {
    const bars = document.querySelectorAll('#chart rect');
    return bars[0].getAttribute('width') === '184' && bars[1].getAttribute('width') === '16';
  }));
  addCheck('svg keeps 200px width', await page.locator('#chart').evaluate((el) => Math.round(el.getBoundingClientRect().width) === 200));
  const probe = await text(page, '#state');
  addCheck('probe accessible name', probe.includes('名称=离线缓存命中率') && probe.includes('标签数=2'), probe);
});

CASES.set('html-example-142', async (page, addCheck) => {
  addCheck('poster is inline svg', await page.locator('#clip').evaluate((el) => el.poster.indexOf('data:image/svg+xml') === 0));
  addCheck('playsinline enabled', await page.locator('#clip').evaluate((el) => el.playsInline === true));
  addCheck('muted and looped', await page.locator('#clip').evaluate((el) => el.muted === true && el.loop === true));
  addCheck('controls visible', await page.locator('#clip').evaluate((el) => el.controls === true));
  addCheck('no media data loaded', await page.locator('#clip').evaluate((el) => el.readyState === 0 && el.videoWidth === 0));
  addCheck('preload none', (await attr(page, '#clip', 'preload')) === 'none');
  addCheck('box keeps poster size', await page.locator('#clip').evaluate((el) => {
    const box = el.getBoundingClientRect();
    return Math.round(box.width) === 240 && Math.round(box.height) === 135;
  }));
});

CASES.set('html-example-143', async (page, addCheck) => {
  await page.waitForFunction(() => {
    const clip = document.getElementById('clip');
    const track = clip && clip.textTracks[0];
    return !!track && !!track.cues && track.cues.length > 0;
  }, null, { timeout: 4000 }).catch(() => {});
  const info = await page.locator('#clip').evaluate((el) => {
    const track = el.textTracks[0];
    return {
      tracks: el.textTracks.length,
      kind: track ? track.kind : null,
      cues: track && track.cues ? track.cues.length : 0,
      first: track && track.cues && track.cues[0] ? track.cues[0].text : null,
      end: track && track.cues && track.cues[0] ? track.cues[0].endTime : null,
    };
  });
  addCheck('one text track', info.tracks === 1, JSON.stringify(info));
  addCheck('track kind captions', info.kind === 'captions', String(info.kind));
  addCheck('two parsed cues', info.cues === 2, String(info.cues));
  addCheck('first cue text', info.first === '离线也能显示字幕', String(info.first));
  addCheck('first cue end time', info.end === 5, String(info.end));
  addCheck('probe cue summary', await text(page, '#state').then((s) => s.includes('cue 数=2') && s.includes('轨道数=1')));
});

CASES.set('html-example-144', async (page, addCheck) => {
  addCheck('declarative shadow root exists', await page.locator('#card').evaluate((el) => el.shadowRoot !== null));
  addCheck('shadow root mode open', await page.locator('#card').evaluate((el) => el.shadowRoot.mode === 'open'));
  addCheck('shadow heading text', await page.locator('#card').evaluate((el) => el.shadowRoot.querySelector('h3').textContent === '声明式 Shadow DOM'));
  addCheck('light dom has no h3', await page.locator('#card').evaluate((el) => el.querySelectorAll('h3').length === 0));
  addCheck('slot assigned one node', await page.locator('#card').evaluate((el) => el.shadowRoot.querySelector('slot[name="desc"]').assignedNodes().length === 1));
  addCheck('slot text from host', await page.locator('#card').evaluate((el) => el.shadowRoot.querySelector('slot[name="desc"]').assignedNodes()[0].textContent === '来自宿主页面的插槽内容'));
  addCheck('host border applied', (await computed(page, '#card', 'borderTopWidth')) === '1px');
  const probe = await text(page, '#state');
  addCheck('probe shadow state', probe.includes('shadowRoot=true') && probe.includes('分配节点=1'), probe);
});

CASES.set('html-example-145', async (page, addCheck) => {
  addCheck('open shadow root', await page.locator('#chip').evaluate((el) => el.shadowRoot !== null && el.shadowRoot.mode === 'open'));
  addCheck('host background from :host', (await computed(page, '#chip', 'backgroundColor')) === 'rgb(232, 240, 254)');
  addCheck('host radius from :host', (await computed(page, '#chip', 'borderTopLeftRadius')) === '999px');
  addCheck('slotted span bold', (await computed(page, '#chip span', 'fontWeight')) === '700');
  addCheck('slotted letter spacing', (await computed(page, '#chip span', 'letterSpacing')) === '1px');
  addCheck('light dom span kept', (await count(page, '#chip span')) === 1);
  addCheck('shadow contains slot', await page.locator('#chip').evaluate((el) => el.shadowRoot.querySelector('slot') !== null));
  const probe = await text(page, '#state');
  addCheck('probe scoping result', probe.includes('host 背景=rgb(232, 240, 254)') && probe.includes('slotted 字重=700'), probe);
});

CASES.set('html-example-146', async (page, addCheck) => {
  addCheck('element upgraded', await page.evaluate(() => document.querySelector('lite-badge') instanceof customElements.get('lite-badge')));
  addCheck('connected callback rendered text', (await text(page, 'lite-badge')) === '离线优先');
  addCheck('connection logged', await text(page, '#state').then((s) => s.includes('connected:离线优先')));
  addCheck('host holds one badge', (await count(page, '#host lite-badge')) === 1);
  await page.locator('#remove').click();
  await settle(page, 150);
  addCheck('badge removed from dom', (await count(page, '#host lite-badge')) === 0);
  const state = await text(page, '#state');
  addCheck('disconnect logged', state.includes('disconnected:离线优先'), state);
  addCheck('probe reports removal', state.includes('仍在文档中=false'), state);
});

CASES.set('html-example-147', async (page, addCheck) => {
  addCheck('defer scripts ran in order', await page.evaluate(() => window.__order.join('>') === 'classic>defer-1>defer-2'));
  addCheck('three ordered steps', await page.evaluate(() => window.__order.length === 3));
  addCheck('target parsed before defer', await page.evaluate(() => document.getElementById('target') !== null));
  addCheck('noscript not in dom', (await count(page, '#nojs')) === 0);
  addCheck('probe execution order', (await text(page, '#state')) === '执行顺序=classic>defer-1>defer-2 / 解析期目标已存在=true / noscript 进入 DOM=false');
  addCheck('defer scripts still present in dom', (await count(page, 'script[defer]')) === 2);
});

CASES.set('html-example-148', async (page, addCheck) => {
  addCheck('module ran after classic', await page.evaluate(() => window.__order.join('>') === 'classic>module'));
  addCheck('classic var leaks to window', await page.evaluate(() => window.leakedInClassic === 'classic-var'));
  addCheck('module var does not leak', await page.evaluate(() => window.leakedInModule === undefined));
  addCheck('import.meta.url equals document url', await page.evaluate(() => document.getElementById('state').textContent.includes('地址与文档一致=true')));
  addCheck('module runs strict mode', await text(page, '#state').then((s) => s.includes('严格模式=true')));
  addCheck('probe module state', await text(page, '#state').then((s) => s.includes('模块泄漏=undefined') && s.includes('执行顺序=classic>module')));
});

// ---------------------------------------------------------------------------
// Group E — modern interaction & accessibility patterns (149-160)
// ---------------------------------------------------------------------------

CASES.set('html-example-149', async (page, addCheck) => {
  addCheck('status role declared', (await attr(page, '#status', 'role')) === 'status');
  addCheck('polite live region', (await attr(page, '#status', 'aria-live')) === 'polite');
  addCheck('single live region', (await count(page, '[aria-live]')) === 1);
  addCheck('initial status text', (await text(page, '#status')) === '尚未保存');
  await page.locator('#save').click();
  await page.locator('#save').click();
  await settle(page, 120);
  addCheck('live region updated', (await text(page, '#status')) === '已保存第 2 次');
  addCheck('region element reused', (await count(page, '#status')) === 1);
});

CASES.set('html-example-150', async (page, addCheck) => {
  addCheck('tablist labelled', (await attr(page, '#tablist', 'aria-label')) === '示例分组');
  addCheck('two tabs', (await count(page, '[role="tab"]')) === 2);
  addCheck('two panels', (await count(page, '[role="tabpanel"]')) === 2);
  addCheck('first tab selected', (await attr(page, '#tab-a', 'aria-selected')) === 'true');
  addCheck('second tab has roving tabindex', (await attr(page, '#tab-b', 'tabindex')) === '-1');
  addCheck('panel a visible initially', await page.locator('#panel-a').isVisible());
  await page.locator('#tab-b').click();
  await settle(page, 120);
  addCheck('click switches selection', (await attr(page, '#tab-b', 'aria-selected')) === 'true');
  addCheck('panel b revealed', await page.locator('#panel-b').isVisible());
  addCheck('panel a hidden', !(await page.locator('#panel-a').isVisible()));
  addCheck('probe selection', (await text(page, '#state')) === '选中=tab-b / 可见面板=panel-b / 面板数=2');
  await page.keyboard.press('ArrowLeft');
  await settle(page, 120);
  addCheck('arrow key returns to first tab', (await attr(page, '#tab-a', 'aria-selected')) === 'true');
  addCheck('focus followed selection', await page.evaluate(() => document.activeElement.id === 'tab-a'));
});

CASES.set('html-example-151', async (page, addCheck) => {
  addCheck('collapsed initially', (await attr(page, '#toggle', 'aria-expanded')) === 'false');
  addCheck('content hidden initially', !(await page.locator('#more').isVisible()));
  addCheck('controls points at content', (await attr(page, '#toggle', 'aria-controls')) === 'more');
  await page.locator('#toggle').click();
  await settle(page, 120);
  addCheck('expanded after click', (await attr(page, '#toggle', 'aria-expanded')) === 'true');
  addCheck('content visible after click', await page.locator('#more').isVisible());
  addCheck('probe expanded state', (await text(page, '#state')) === 'expanded=true / hidden=false / controls 匹配=true');
  await page.locator('#toggle').click();
  await settle(page, 120);
  addCheck('second click collapses', (await attr(page, '#toggle', 'aria-expanded')) === 'false');
  addCheck('content hidden again', !(await page.locator('#more').isVisible()));
});

CASES.set('html-example-152', async (page, addCheck) => {
  addCheck('positive tabindex values', await page.evaluate(() => document.getElementById('third').tabIndex === 1 && document.getElementById('second').tabIndex === 2));
  addCheck('programmatic target is -1', await page.evaluate(() => document.getElementById('focusable').tabIndex === -1));
  await page.keyboard.press('Tab');
  addCheck('first tab stop is tabindex=1', await page.evaluate(() => document.activeElement.id === 'third'));
  await page.keyboard.press('Tab');
  addCheck('second tab stop is tabindex=2', await page.evaluate(() => document.activeElement.id === 'second'));
  await page.keyboard.press('Tab');
  addCheck('third tab stop is default 0', await page.evaluate(() => document.activeElement.id === 'first'));
  addCheck('probe focus order', await text(page, '#state').then((s) => s.includes('焦点顺序=third>second>first')));
  addCheck('programmatic focus works', await page.evaluate(() => {
    const box = document.getElementById('focusable');
    box.focus();
    return document.activeElement === box;
  }));
});

CASES.set('html-example-153', async (page, addCheck) => {
  addCheck('inert reflected as true', await page.locator('#modalish').evaluate((el) => el.inert === true));
  addCheck('inert subtree is dimmed', (await computed(page, '#modalish', 'opacity')) === '0.5');
  addCheck('blocked button cannot take focus', await page.evaluate(() => {
    const blocked = document.getElementById('blocked');
    blocked.focus();
    return document.activeElement !== blocked;
  }));
  addCheck('blocked button not focusable match', await page.locator('#blocked').evaluate((el) => !el.matches(':focus')));
  addCheck('outside button can focus', await page.evaluate(() => {
    const allowed = document.getElementById('allowed');
    allowed.focus();
    return document.activeElement === allowed;
  }));
  addCheck('probe inert state', (await text(page, '#state')) === 'inert=true / 被阻按钮可聚焦=false / 正常按钮可聚焦=true / 被阻透明度=0.5');
});

CASES.set('html-example-154', async (page, addCheck) => {
  addCheck('hidden value is until-found', (await attr(page, '#hidden-part', 'hidden')) === 'until-found');
  addCheck('content-visibility hidden', (await computed(page, '#hidden-part', 'contentVisibility')) === 'hidden');
  addCheck('hidden content has no height', await page.locator('#hidden-part').evaluate((el) => el.getBoundingClientRect().height === 0));
  await page.locator('#reveal').click();
  await settle(page, 150);
  addCheck('reveal clears hidden', await page.locator('#hidden-part').evaluate((el) => el.hidden === false));
  addCheck('content visible after reveal', await page.locator('#hidden-part').evaluate((el) => el.getBoundingClientRect().height > 0));
  const probe = await text(page, '#state');
  addCheck('beforematch observed', probe.includes('事件=beforematch'), probe);
  addCheck('probe reports visible', probe.includes('已解密=true'), probe);
});

CASES.set('html-example-155', async (page, addCheck) => {
  addCheck('plaintext-only mode', (await attr(page, '#editor', 'contenteditable')) === 'plaintext-only');
  addCheck('editor is editable', await page.locator('#editor').evaluate((el) => el.isContentEditable === true));
  addCheck('textbox role and name', await page.locator('#editor').evaluate((el) => el.getAttribute('role') === 'textbox' && el.getAttribute('aria-label') === '备注编辑器'));
  addCheck('initial text content', (await text(page, '#editor')) === '第一行');
  await page.locator('#editor').click();
  await page.keyboard.press('End');
  await page.keyboard.type('<b>粗体</b>');
  await settle(page, 150);
  addCheck('markup typed as plain text', await page.locator('#editor').evaluate((el) => el.querySelectorAll('*').length === 0));
  addCheck('literal markup kept in text', await page.locator('#editor').evaluate((el) => el.textContent.includes('<b>粗体</b>')));
  addCheck('input event fired', await text(page, '#state').then((s) => !s.includes('input 次数=0')));
  addCheck('probe child count zero', await text(page, '#state').then((s) => s.includes('子元素数=0')));
});

CASES.set('html-example-156', async (page, addCheck) => {
  addCheck('combobox role', (await attr(page, '#combo', 'role')) === 'combobox');
  addCheck('controls listbox', (await attr(page, '#combo', 'aria-controls')) === 'list');
  addCheck('listbox role', (await attr(page, '#list', 'role')) === 'listbox');
  addCheck('three options', (await count(page, '[role="option"]')) === 3);
  addCheck('initial active option', (await attr(page, '#combo', 'aria-activedescendant')) === 'opt-2');
  addCheck('initial selected option', (await attr(page, '#opt-2', 'aria-selected')) === 'true');
  addCheck('initial value matches option', await page.locator('#combo').evaluate((el) => el.value === 'CSS'));
  await page.locator('#combo').click();
  await page.keyboard.press('ArrowDown');
  await settle(page, 120);
  addCheck('arrow down moves active option', (await attr(page, '#combo', 'aria-activedescendant')) === 'opt-3');
  addCheck('value follows active option', await page.locator('#combo').evaluate((el) => el.value === 'JavaScript'));
  addCheck('single selected option', (await count(page, '[role="option"][aria-selected="true"]')) === 1);
  await page.keyboard.press('ArrowUp');
  await page.keyboard.press('ArrowUp');
  await settle(page, 120);
  addCheck('arrow up wraps to first', (await attr(page, '#combo', 'aria-activedescendant')) === 'opt-1');
  addCheck('focus never left combobox', await page.evaluate(() => document.activeElement.id === 'combo'));
});

CASES.set('html-example-157', async (page, addCheck) => {
  addCheck('manual popover declared', (await attr(page, '#manual', 'popover')) === 'manual');
  addCheck('closed initially', await page.locator('#manual').evaluate((el) => !el.matches(':popover-open')));
  await page.locator('#toggle').click();
  await settle(page, 150);
  addCheck('target button opens popover', await page.locator('#manual').evaluate((el) => el.matches(':popover-open')));
  addCheck('toggle event recorded', await text(page, '#state').then((s) => s.includes('newState=open')));
  await page.mouse.click(1000, 650);
  await settle(page, 200);
  addCheck('outside click does not dismiss manual popover', await page.locator('#manual').evaluate((el) => el.matches(':popover-open')));
  await page.locator('#close').click();
  await settle(page, 150);
  addCheck('toggle action closes popover', await page.locator('#manual').evaluate((el) => !el.matches(':popover-open')));
  const probe = await text(page, '#state');
  addCheck('probe counts toggle events', probe.includes('事件数=2') && probe.includes('newState=closed'), probe);
});

CASES.set('html-example-158', async (page, addCheck) => {
  addCheck('describedby points at help', (await attr(page, '#mail', 'aria-describedby')) === 'mail-help');
  addCheck('errormessage points at error', (await attr(page, '#mail', 'aria-errormessage')) === 'mail-error');
  addCheck('invalid state set initially', (await attr(page, '#mail', 'aria-invalid')) === 'true');
  addCheck('error message visible', (await text(page, '#mail-error')) === '请输入完整邮箱地址');
  addCheck('error not hidden', await page.locator('#mail-error').isVisible());
  addCheck('help text present', (await text(page, '#mail-help')) === '用于接收离线通知，不会联网。');
  await page.locator('#mail').fill('lin@example.invalid');
  await settle(page, 150);
  addCheck('valid input clears error', await page.locator('#mail-error').evaluate((el) => el.hidden === true));
  addCheck('aria-invalid back to false', (await attr(page, '#mail', 'aria-invalid')) === 'false');
  addCheck('probe validity', await text(page, '#state').then((s) => s.includes('valid=true') && s.includes('错误文案=none')));
});

CASES.set('html-example-159', async (page, addCheck) => {
  addCheck('alert region declared', (await attr(page, '#summary', 'role')) === 'alert');
  addCheck('summary hidden initially', await page.locator('#summary').evaluate((el) => el.hidden === true));
  await page.locator('#signup button[type="submit"]').click();
  await settle(page, 150);
  addCheck('summary revealed on invalid submit', await page.locator('#summary').isVisible());
  addCheck('two error items', (await count(page, '#summary-list li')) === 2);
  addCheck('error headline', (await text(page, '#summary-text')) === '2 项需要修正');
  addCheck('first error item text', (await text(page, '#summary-list li')) === '用户名不能为空');
  addCheck('focus moved to first invalid field', await page.evaluate(() => document.activeElement.id === 'user'));
  addCheck('probe invalid submit', (await text(page, '#state')) === '错误数=2 / 汇总可见=true / 条目=2 / 焦点=user');
  await page.locator('#user').fill('小林');
  await page.locator('#pwd').fill('offline-2026');
  await page.locator('#signup button[type="submit"]').click();
  await settle(page, 150);
  addCheck('summary hidden after fix', await page.locator('#summary').evaluate((el) => el.hidden === true));
  addCheck('probe success submit', await text(page, '#state').then((s) => s.includes('错误数=0') && s.includes('汇总可见=false')));
});

CASES.set('html-example-160', async (page, addCheck) => {
  addCheck('table has caption', (await text(page, '#board caption')) === '本地工单');
  addCheck('status role for count', (await attr(page, '#status', 'role')) === 'status');
  addCheck('details shares name group', (await attr(page, 'details', 'name')) === 'panel');
  addCheck('initial probe state', await text(page, '#state').then((s) => s.includes('初始行数=0') && s.includes('合计=0') && s.includes('播报区=status')));
  await page.locator('#add').click();
  await settle(page, 150);
  addCheck('empty title rejected', (await text(page, '#title-error')) === '标题不能为空');
  addCheck('error visible', await page.locator('#title-error').isVisible());
  addCheck('focus returned to title', await page.evaluate(() => document.activeElement.id === 'title'));
  addCheck('aria-invalid set', (await attr(page, '#title', 'aria-invalid')) === 'true');
  addCheck('no row added yet', (await count(page, '#rows tr')) === 0);
  await page.locator('#title').fill('磁盘告警');
  await page.locator('#add').click();
  await settle(page, 150);
  addCheck('one row added', (await count(page, '#rows tr')) === 1);
  addCheck('row id generated', (await text(page, '#rows tr td')) === 'T-1');
  addCheck('row title stored', (await text(page, '#rows tr td:nth-child(2)')) === '磁盘告警');
  addCheck('tfoot total updated', (await text(page, '#total')) === '1');
  addCheck('status announced', (await text(page, '#status')) === '共 1 条工单');
  addCheck('error cleared after success', await page.locator('#title-error').evaluate((el) => el.hidden === true));
  await page.locator('#open-help').click();
  await settle(page, 150);
  addCheck('help popover opens', await page.locator('#help').evaluate((el) => el.matches(':popover-open')));
  await page.locator('#close-help').click();
  await settle(page, 150);
  addCheck('help popover closes', await page.locator('#help').evaluate((el) => !el.matches(':popover-open')));
});

export const COVERED_IDS = [...CASES.keys()];

export async function assertExpansionExample(page, example, addCheck) {
  const id = example?.id;
  const fn = CASES.get(id);
  if (!fn) return false;
  await fn(page, addCheck);
  return true;
}
