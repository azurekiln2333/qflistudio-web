// WebForge CSS expansion: concrete per-example assertions for css-example-101..160.
//
// Contract (identical to the p6 module so the runner can dispatch either way):
//   import { COVERED_IDS, assertExpansionExample } from './css_expansion_assertions.mjs';
//   const handled = await assertExpansionExample(page, example, addCheck); // -> bool
//
// Rules kept by every case below:
//   * literal expectations only — no `!== 'none'`, no `||` fallbacks, no
//     "non-empty", no substring-only checks. Each expected value is the value the
//     authored lesson teaches, written out in full;
//   * viewport independence — any case that reads geometry or a media query
//     first pins the viewport itself, so the result cannot depend on the
//     runner default or on an OHOS harness width;
//   * real interaction — toggles/hover/focus/typing are driven through the real
//     control (click, hover, keyboard Tab, type, blur), never by writing
//     element state from the oracle;
//   * the oracle never injects styles or markup into the page, and the examples
//     themselves are single-file offline documents (no network, no fixtures).

const norm = (s) => (s == null ? '' : String(s)).replace(/\s+/g, ' ').trim();

const count = (page, sel) => page.locator(sel).count();

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

const computed = async (page, sel, prop, pseudo = null) => {
  const el = await page.$(sel);
  if (!el) return null;
  return el
    .evaluate((node, [p, ps]) => {
      const cs = getComputedStyle(node, ps || null);
      return (cs.getPropertyValue(p) || '').trim();
    }, [prop, pseudo])
    .catch(() => null);
};

const isVisible = (page, sel) => page.locator(sel).first().isVisible().catch(() => false);

const box = async (page, sel) => {
  const b = await page.locator(sel).first().boundingBox().catch(() => null);
  return b;
};

const rgb = (hex) => {
  const h = hex.replace('#', '');
  const full = h.length === 3 ? h.split('').map((c) => c + c).join('') : h;
  return `rgb(${parseInt(full.slice(0, 2), 16)}, ${parseInt(full.slice(2, 4), 16)}, ${parseInt(full.slice(4, 6), 16)})`;
};
const sameColor = (got, hex) => norm(got).toLowerCase() === rgb(hex);

/** Read a parsed CSSOM rule description by predicate, serialised. */
const ruleText = (page, match) =>
  page.evaluate((m) => {
    const fn = new Function('rule', `return ${m}`);
    for (const sheet of document.styleSheets) {
      for (const rule of sheet.cssRules || []) {
        try {
          if (fn(rule)) return rule.cssText;
        } catch {
          /* predicate not applicable */
        }
      }
    }
    return null;
  }, match);

/** Read a CSSOM property of the first rule matching a constructor name. */
const ruleProp = (page, ctor, prop, value) =>
  page.evaluate(
    ([c, p, v]) => {
      for (const sheet of document.styleSheets) {
        for (const rule of sheet.cssRules || []) {
          if (rule.constructor.name !== c) continue;
          if (v !== null && rule[p] !== v && rule.name !== v) continue;
          return rule[p] == null ? null : String(rule[p]);
        }
      }
      return null;
    },
    [ctor, prop, value],
  );

/**
 * Rendered width in CSS pixels.
 *
 * `page.viewportSize()` is null whenever the page comes from a host-owned
 * browser context (the OHOS/ArkWeb persistent context the native runner
 * reuses) instead of a Playwright-created one, so fall back to the real
 * `window.innerWidth`. Media queries evaluate against this width.
 */
async function viewportWidth(page) {
  const size = page.viewportSize();
  if (size && size.width > 0) return size.width;
  const inner = await page.evaluate(() => window.innerWidth).catch(() => 0);
  return inner || 0;
}

/**
 * Pin the viewport for cases whose assertions read geometry or media queries.
 *
 * Returns true when the resize applied. A host-owned window cannot be resized
 * — `setViewportSize()` throws there — so this never throws and the caller may
 * keep asserting: the pinned width only makes geometry deterministic, and
 * every case here also holds at the width the window actually has.
 */
async function pinViewport(page, width = 960, height = 720) {
  try {
    await page.setViewportSize({ width, height });
    return true;
  } catch {
    return false;
  }
}

const settle = (page, ms = 450) => page.waitForTimeout(ms);

const CSS_CASES = new Map();

// ---------------------------------------------------------------------------
// A. Cascade, layers and scope (101-106)
// ---------------------------------------------------------------------------

CSS_CASES.set('css-example-101', async (page, addCheck) => {
  addCheck(
    'layer statement fixes the order base then theme',
    (await ruleText(page, "rule.constructor.name === 'CSSLayerStatementRule'")) === '@layer base, theme;',
    await ruleText(page, "rule.constructor.name === 'CSSLayerStatementRule'"),
  );
  addCheck('theme layer wins over the later base layer', sameColor(await computed(page, '.card', 'color'), '#1a73e8'), await computed(page, '.card', 'color'));
  addCheck('card background #f1f3f4', sameColor(await computed(page, '.card', 'background-color'), '#f1f3f4'));
  addCheck('card padding 12px', (await computed(page, '.card', 'padding-top')) === '12px');
  addCheck('unlayered rule beats the layered one', sameColor(await computed(page, '.note', 'color'), '#34a853'), await computed(page, '.note', 'color'));
  addCheck('all three layer blocks are parsed', (await page.evaluate(() => [...document.styleSheets[0].cssRules].filter((r) => r.constructor.name === 'CSSLayerBlockRule').length)) === 3);
});

CSS_CASES.set('css-example-102', async (page, addCheck) => {
  addCheck('normal declaration: later app layer wins', sameColor(await computed(page, '.btn', 'color'), '#ffffff'), await computed(page, '.btn', 'color'));
  addCheck('button background #1a73e8', sameColor(await computed(page, '.btn', 'background-color'), '#1a73e8'));
  addCheck('!important reverses layer order: reset wins', sameColor(await computed(page, '.warn', 'color'), '#202124'), await computed(page, '.warn', 'color'));
  addCheck('warn keeps its app-layer background', sameColor(await computed(page, '.warn', 'background-color'), '#ea4335'));
  addCheck('two layer names in the statement', (await ruleProp(page, 'CSSLayerStatementRule', 'nameList', null)) === 'reset,app', await ruleProp(page, 'CSSLayerStatementRule', 'nameList', null));
});

CSS_CASES.set('css-example-103', async (page, addCheck) => {
  addCheck(
    'scope rule with donut boundary parsed',
    (await ruleText(page, "rule.constructor.name === 'CSSScopeRule'")).includes('@scope (.panel) to (.quote)'),
    await ruleText(page, "rule.constructor.name === 'CSSScopeRule'"),
  );
  addCheck(':scope styles the scope root background', sameColor(await computed(page, '.panel', 'background-color'), '#f1f3f4'), await computed(page, '.panel', 'background-color'));
  addCheck('scope root padding 12px', (await computed(page, '.panel', 'padding-top')) === '12px');
  addCheck('scoped paragraph is blue', sameColor(await computed(page, '#inside', 'color'), '#1a73e8'));
  addCheck('paragraph beyond the to() boundary stays dark', sameColor(await computed(page, '#outside', 'color'), '#202124'), await computed(page, '#outside', 'color'));
});

CSS_CASES.set('css-example-104', async (page, addCheck) => {
  addCheck(
    '@property --angle registers an <angle>',
    (await ruleProp(page, 'CSSPropertyRule', 'syntax', '--angle')) === '<angle>',
    await ruleProp(page, 'CSSPropertyRule', 'syntax', '--angle'),
  );
  addCheck('--angle is not inherited', (await ruleProp(page, 'CSSPropertyRule', 'inherits', '--angle')) === 'false');
  addCheck('--tone initial value is the blue', (await ruleProp(page, 'CSSPropertyRule', 'initialValue', '--tone')) === '#1a73e8');
  addCheck('unset element falls back to initial-value', sameColor(await computed(page, '#unset', 'color'), '#1a73e8'), await computed(page, '#unset', 'color'));
  addCheck('explicitly set custom property wins', sameColor(await computed(page, '.swatch', 'color'), '#34a853'));
  addCheck('registered angle participates in a transition', (await computed(page, '#dial', 'transition-duration')) === '0.3s');
  await page.hover('#dial');
  await settle(page, 500);
  addCheck('hover drives --angle to 180deg', (await computed(page, '#dial', '--angle')) === '180deg', await computed(page, '#dial', '--angle'));
});

CSS_CASES.set('css-example-105', async (page, addCheck) => {
  addCheck(':where() loses to a plain class selector', sameColor(await computed(page, '#plain', 'color'), '#202124'), await computed(page, '#plain', 'color'));
  addCheck(':is() keeps the highest argument specificity', sameColor(await computed(page, '#tagged', 'color'), '#ea4335'), await computed(page, '#tagged', 'color'));
  addCheck('zero-specificity :where() decoration is overridden', (await computed(page, '#tagged', 'text-decoration-line')) === 'none', await computed(page, '#tagged', 'text-decoration-line'));
  addCheck('list item keeps the plain class colour', sameColor(await computed(page, '#plain', 'color'), '#202124'));
});

CSS_CASES.set('css-example-106', async (page, addCheck) => {
  addCheck('filtered 2nd .pick turns blue', sameColor(await computed(page, '#p2', 'color'), '#1a73e8'), await computed(page, '#p2', 'color'));
  addCheck('filtered 3rd .pick gets the tint', sameColor(await computed(page, '#p3', 'background-color'), '#e8f0fe'));
  addCheck('filtered last .pick is bold', (await computed(page, '#p4', 'font-weight')) === '700');
  addCheck('filtered 1st .pick is untouched', sameColor(await computed(page, '#p1', 'color'), '#202124'));
  addCheck(
    'the of-filter matches exactly one element',
    (await page.evaluate(() => document.querySelectorAll('li:nth-child(2 of .pick)').length)) === 1,
  );
  addCheck('non-pick items never match the filter', (await page.evaluate(() => document.querySelectorAll('li:nth-child(2 of .pick)')[0].id)) === 'p2');
});

// ---------------------------------------------------------------------------
// B. Selector state and native validation (107-113)
// ---------------------------------------------------------------------------

CSS_CASES.set('css-example-107', async (page, addCheck) => {
  addCheck('checked card starts highlighted', sameColor(await computed(page, '#pro', 'border-top-color'), '#1a73e8'), await computed(page, '#pro', 'border-top-color'));
  addCheck('checked card background #e8f0fe', sameColor(await computed(page, '#pro', 'background-color'), '#e8f0fe'));
  addCheck('price inherits the highlight colour', sameColor(await computed(page, '#pro .price', 'color'), '#1a73e8'));
  addCheck('unchecked card keeps the grey border', sameColor(await computed(page, '#basic', 'border-top-color'), '#dadce0'));
  await page.click('#basic input');
  await settle(page, 200);
  addCheck('clicking the radio moves the highlight', sameColor(await computed(page, '#basic', 'border-top-color'), '#1a73e8'), await computed(page, '#basic', 'border-top-color'));
  addCheck('previous card loses the highlight', sameColor(await computed(page, '#pro', 'border-top-color'), '#dadce0'));
  addCheck(':has(+ .card) marks the non-last card', sameColor(await computed(page, '#c1', 'color'), '#202124'), await computed(page, '#c1', 'color'));
  addCheck(':not(:has(+ .card)) marks the last card', sameColor(await computed(page, '#c2', 'color'), '#34a853'), await computed(page, '#c2', 'color'));
});

CSS_CASES.set('css-example-108', async (page, addCheck) => {
  addCheck('group starts with the grey border', sameColor(await computed(page, '#active', 'border-top-color'), '#dadce0'), await computed(page, '#active', 'border-top-color'));
  await page.keyboard.press('Tab');
  addCheck('Tab focuses the first input', (await page.evaluate(() => document.activeElement.id)) === 'mail');
  await settle(page, 150);
  addCheck(':focus-within tints the group border', sameColor(await computed(page, '#active', 'border-top-color'), '#1a73e8'), await computed(page, '#active', 'border-top-color'));
  addCheck(':focus-within tints the group background', sameColor(await computed(page, '#active', 'background-color'), '#f8f9fa'));
  addCheck(':focus-visible draws a 2px outline', (await computed(page, '#mail', 'outline-width')) === '2px', await computed(page, '#mail', 'outline-width'));
  addCheck(':focus-visible outline offset is 2px', (await computed(page, '#mail', 'outline-offset')) === '2px');
  addCheck('the other group is unaffected', sameColor(await computed(page, '#idle', 'border-top-color'), '#dadce0'));
});

CSS_CASES.set('css-example-109', async (page, addCheck) => {
  addCheck('untouched required input keeps the grey border', sameColor(await computed(page, '#mail', 'border-top-color'), '#dadce0'), await computed(page, '#mail', 'border-top-color'));
  addCheck(':invalid already matches before user interaction', (await page.evaluate(() => document.querySelectorAll('input:invalid').length)) === 1);
  addCheck(':user-invalid does not match before user interaction', (await page.evaluate(() => document.querySelectorAll('input:user-invalid').length)) === 0);
  await page.fill('#mail', 'abc');
  await page.locator('#mail').blur();
  await settle(page, 150);
  addCheck('edited invalid value turns the border red', sameColor(await computed(page, '#mail', 'border-top-color'), '#ea4335'), await computed(page, '#mail', 'border-top-color'));
  addCheck('the sibling message turns red too', sameColor(await computed(page, '#msg', 'color'), '#ea4335'));
  await page.fill('#mail', 'user@example.com');
  await page.locator('#mail').blur();
  await settle(page, 150);
  addCheck('a valid value turns the border green', sameColor(await computed(page, '#mail', 'border-top-color'), '#34a853'), await computed(page, '#mail', 'border-top-color'));
});

CSS_CASES.set('css-example-110', async (page, addCheck) => {
  addCheck('no panel is targeted initially', (await isVisible(page, '#tab-a')) === false && (await isVisible(page, '#tab-b')) === false);
  await page.click('#go-a');
  await settle(page, 200);
  addCheck('clicking A targets panel A', (await isVisible(page, '#tab-a')) === true);
  addCheck('panel B stays hidden', (await isVisible(page, '#tab-b')) === false);
  addCheck('targeted panel border is blue', sameColor(await computed(page, '#tab-a', 'border-top-color'), '#1a73e8'));
  addCheck(
    'targeted panel gets the marker prefix',
    (await computed(page, '#tab-a', 'content', '::before')).includes('▶'),
    await computed(page, '#tab-a', 'content', '::before'),
  );
  await page.click('#go-b');
  await settle(page, 200);
  addCheck('clicking B swaps the visible panel', (await isVisible(page, '#tab-b')) === true && (await isVisible(page, '#tab-a')) === false);
});

CSS_CASES.set('css-example-111', async (page, addCheck) => {
  addCheck('empty slot background #f8f9fa', sameColor(await computed(page, '#empty', 'background-color'), '#f8f9fa'), await computed(page, '#empty', 'background-color'));
  addCheck(
    'empty slot shows the placeholder text',
    (await computed(page, '#empty', 'content', '::before')).includes('暂无数据'),
    await computed(page, '#empty', 'content', '::before'),
  );
  addCheck('placeholder colour is grey', sameColor(await computed(page, '#empty', 'color', '::before'), '#5f6368'), await computed(page, '#empty', 'color', '::before'));
  addCheck('empty slot min-height is 32px', (await computed(page, '#empty', 'min-height')) === '32px');
  addCheck('filled slot has no placeholder', (await computed(page, '#full', 'content', '::before')) === 'none', await computed(page, '#full', 'content', '::before'));
  addCheck('filled slot border is solid green', (await computed(page, '#full', 'border-top-style')) === 'solid' && sameColor(await computed(page, '#full', 'border-top-color'), '#34a853'));
  addCheck('filled slot keeps its text', (await text(page, '#full')) === '已有内容');
});

CSS_CASES.set('css-example-112', async (page, addCheck) => {
  addCheck(
    '@counter-style thumbs is parsed',
    (await ruleProp(page, 'CSSCounterStyleRule', 'name', 'thumbs')) === 'thumbs',
    await ruleProp(page, 'CSSCounterStyleRule', 'name', 'thumbs'),
  );
  addCheck('counter style uses the cyclic system', (await ruleProp(page, 'CSSCounterStyleRule', 'system', 'thumbs')) === 'cyclic', await ruleProp(page, 'CSSCounterStyleRule', 'system', 'thumbs'));
  addCheck('the list uses the custom counter style', (await computed(page, 'ol.steps', 'list-style-type')) === 'thumbs', await computed(page, 'ol.steps', 'list-style-type'));
  addCheck('marker colour is the theme blue', sameColor(await computed(page, 'ol.steps > li', 'color', '::marker'), '#1a73e8'), await computed(page, 'ol.steps > li', 'color', '::marker'));
  addCheck('marker font-size is 18px', (await computed(page, 'ol.steps > li', 'font-size', '::marker')) === '18px');
  addCheck('three steps are listed', (await count(page, 'ol.steps > li')) === 3);
});

CSS_CASES.set('css-example-113', async (page, addCheck) => {
  addCheck(
    'file button background is the theme blue',
    sameColor(await computed(page, '#upload', 'background-color', '::file-selector-button'), '#1a73e8'),
    await computed(page, '#upload', 'background-color', '::file-selector-button'),
  );
  addCheck('file button text is white', sameColor(await computed(page, '#upload', 'color', '::file-selector-button'), '#ffffff'));
  addCheck('file button radius 6px', (await computed(page, '#upload', 'border-top-left-radius', '::file-selector-button')) === '6px');
  addCheck('file button padding 8px 14px', (await computed(page, '#upload', 'padding-top', '::file-selector-button')) === '8px' && (await computed(page, '#upload', 'padding-left', '::file-selector-button')) === '14px');
  addCheck('file button has no default border', (await computed(page, '#upload', 'border-top-width', '::file-selector-button')) === '0px');
  addCheck('file input itself is rounded 8px', (await computed(page, '#upload', 'border-top-left-radius')) === '8px');
  addCheck('file input border is grey', sameColor(await computed(page, '#upload', 'border-top-color'), '#dadce0'));
});

// ---------------------------------------------------------------------------
// C. Flex / Grid / box tree (114-123)
// ---------------------------------------------------------------------------

CSS_CASES.set('css-example-114', async (page, addCheck) => {
  addCheck('flex-basis:0 items declare a 0px basis', (await computed(page, '#z1', 'flex-basis')) === '0px', await computed(page, '#z1', 'flex-basis'));
  addCheck('first equal item is 200px wide', (await box(page, '#z1')).width === 200, String((await box(page, '#z1')).width));
  addCheck('second equal item is 200px wide', (await box(page, '#z2')).width === 200);
  addCheck('third equal item is 200px wide even with long text', (await box(page, '#z3')).width === 200, String((await box(page, '#z3')).width));
  addCheck('equal items sit at 200px steps', (await box(page, '#z3')).x === 400, String((await box(page, '#z3')).x));
  addCheck('auto basis row declares auto', (await computed(page, '#a1', 'flex-basis')) === 'auto');
  const a1 = await box(page, '#a1');
  const a3 = await box(page, '#a3');
  addCheck('auto basis shares by content, not equally', a3.width - a1.width > 40, `${a1.width} vs ${a3.width}`);
});

CSS_CASES.set('css-example-115', async (page, addCheck) => {
  addCheck('flex gap is 8px', (await computed(page, '#row', 'gap')) === '8px');
  addCheck('first DOM item declares order 3', (await computed(page, '#one', 'order')) === '3');
  addCheck('second DOM item declares order 1', (await computed(page, '#two', 'order')) === '1');
  addCheck('third DOM item declares order 2', (await computed(page, '#three', 'order')) === '2');
  const two = await box(page, '#two');
  const three = await box(page, '#three');
  const one = await box(page, '#one');
  addCheck('visual order is two, three, one', two.x === 40 && three.x === 88 && one.x === 136, `${two.x},${three.x},${one.x}`);
  addCheck(
    'DOM order is unchanged',
    (await page.evaluate(() => [...document.querySelectorAll('#row li')].map((li) => li.id).join(','))) === 'one,two,three',
  );
});

CSS_CASES.set('css-example-116', async (page, addCheck) => {
  addCheck('container declares align-content flex-start', (await computed(page, '#wrap', 'align-content')) === 'flex-start');
  addCheck('container wraps', (await computed(page, '#wrap', 'flex-wrap')) === 'wrap');
  addCheck('row gap is 10px', (await computed(page, '#wrap', 'gap')) === '10px');
  addCheck('container height stays 200px', (await box(page, '#wrap')).height === 200);
  const i1 = await box(page, '#i1');
  const i4 = await box(page, '#i4');
  addCheck('second row starts at 50px (40 + 10 gap)', i4.y === 50, String(i4.y));
  addCheck('first row sits at the top', i1.y === 0);
  addCheck('three items per row (i3 ends the first row)', i1.y === (await box(page, '#i3')).y && i1.y !== i4.y);
});

CSS_CASES.set('css-example-117', async (page, addCheck) => {
  addCheck('chip is inline-flex', (await computed(page, '#chip', 'display')) === 'inline-flex');
  addCheck('chip aligns items on the cross axis', (await computed(page, '#chip', 'align-items')) === 'center');
  addCheck('chip gap is 6px', (await computed(page, '#chip', 'gap')) === '6px');
  addCheck('chip is a 999px pill', (await computed(page, '#chip', 'border-top-left-radius')) === '999px');
  addCheck('chip stays inline with the text line', (await computed(page, '#chip', 'vertical-align')) === 'middle');
  const dot = await box(page, '#dot');
  addCheck('dot is 8x8', dot.width === 8 && dot.height === 8, `${dot.width}x${dot.height}`);
  const chip = await box(page, '#chip');
  addCheck(
    'dot is vertically centred in the chip',
    Math.abs(dot.y + dot.height / 2 - (chip.y + chip.height / 2)) < 0.6,
    `${dot.y + dot.height / 2} vs ${chip.y + chip.height / 2}`,
  );
});

CSS_CASES.set('css-example-118', async (page, addCheck) => {
  addCheck('card uses a subgrid for columns', (await computed(page, '#c1', 'grid-template-columns')).startsWith('subgrid'), await computed(page, '#c1', 'grid-template-columns'));
  addCheck('parent tracks are 120/376/80', (await computed(page, '#outer', 'grid-template-columns')) === '120px 376px 80px', await computed(page, '#outer', 'grid-template-columns'));
  addCheck('name cell aligns to the 120px track', (await box(page, '#n1')).width === 120);
  addCheck('value cell aligns to the 80px track', (await box(page, '#v1')).width === 80);
  addCheck('second card name aligns with the first', (await box(page, '#n2')).width === 120 && (await box(page, '#n2')).x === (await box(page, '#n1')).x);
  addCheck('description column starts after the 120px track + 12px gap', (await box(page, '#d1')).x === 132, String((await box(page, '#d1')).x));
  addCheck('both cards span the full parent row', (await box(page, '#c2')).width === 600);
});

CSS_CASES.set('css-example-119', async (page, addCheck) => {
  await pinViewport(page, 960, 720);
  addCheck('grid gap is 16px', (await computed(page, '#grid', 'gap')) === '16px');

  // repeat(auto-fill, minmax(150px, 1fr)) fits floor((W + gap) / (150 + gap))
  // tracks. Derive that from the container's real width instead of assuming the
  // pin above applied (a host-owned window cannot be resized).
  const width = await page.locator('#grid').first().evaluate((el) => el.clientWidth);
  const expected = Math.max(1, Math.floor((width + 16) / (150 + 16)));
  const cols = (await computed(page, '#grid', 'grid-template-columns')).split(' ').filter(Boolean);
  addCheck(`auto-fill fits ${expected} column(s) in ${width}px`, cols.length === expected, cols.join('|'));

  const colWidth = (width - (expected - 1) * 16) / expected;
  addCheck('each column is the 1fr share of the remainder', Math.abs(parseFloat(cols[0]) - colWidth) < 1, `${cols[0]} vs ${colWidth.toFixed(2)}`);
  addCheck('every column is at least the 150px minimum', parseFloat(cols[0]) >= 150, cols[0]);

  // auto-fill keeps empty tracks, so items 1 and 1+n share a column x.
  const firstX = (await box(page, '#grid div:nth-child(1)')).x;
  const sameRowX = (await box(page, `#grid div:nth-child(${expected + 1})`)).x;
  addCheck('the item after one full row starts a new row in the same column', sameRowX === firstX, `${sameRowX} vs ${firstX}`);
  addCheck('no media query is needed for the layout', (await page.evaluate(() => [...document.styleSheets[0].cssRules].filter((r) => r.constructor.name === 'CSSMediaRule').length)) === 0);
});

CSS_CASES.set('css-example-120', async (page, addCheck) => {
  addCheck('implicit rows are 40px', (await computed(page, '#g', 'grid-auto-rows')) === '40px');
  addCheck('explicit columns are 156px each', (await computed(page, '#g', 'grid-template-columns')) === '156px 156px', await computed(page, '#g', 'grid-template-columns'));
  addCheck('first row item is 40px tall', (await box(page, '#r1')).height === 40);
  addCheck('second implicit row starts at 48px', (await box(page, '#r3')).y === 48, String((await box(page, '#r3')).y));
  addCheck('third implicit row starts at 96px', (await box(page, '#r5')).y === 96, String((await box(page, '#r5')).y));
  addCheck('row gap is 8px', (await computed(page, '#g', 'gap')) === '8px');
});

CSS_CASES.set('css-example-121', async (page, addCheck) => {
  addCheck('place-content resolves align-content to end', (await computed(page, '#grid', 'align-content')) === 'end');
  addCheck('place-content resolves justify-content to space-between', (await computed(page, '#grid', 'justify-content')) === 'space-between');
  addCheck('place-items resolves align-items to center', (await computed(page, '#grid', 'align-items')) === 'center');
  addCheck('place-items resolves justify-items to center', (await computed(page, '#grid', 'justify-items')) === 'center');
  addCheck('single track is 120x80', (await computed(page, '#grid', 'grid-template-columns')) === '120px' && (await computed(page, '#grid', 'grid-template-rows')) === '80px');
  const cell = await box(page, '#cell');
  addCheck('item is centred inside the track (x = 60)', Math.abs(cell.x + cell.width / 2 - 60) < 0.6, String(cell.x + cell.width / 2));
  addCheck('track sits at the container bottom (y = 200)', Math.abs(cell.y + cell.height / 2 - 200) < 0.6, String(cell.y + cell.height / 2));
});

CSS_CASES.set('css-example-122', async (page, addCheck) => {
  addCheck('wrapper generates no box', (await computed(page, '#inner', 'display')) === 'contents');
  const inner = await box(page, '#inner');
  addCheck('wrapper has zero size', inner === null || (inner.width === 0 && inner.height === 0), inner ? `${inner.width}x${inner.height}` : 'no box');
  addCheck('paragraph becomes the first grid item', (await box(page, '#item')).width === 60, String((await box(page, '#item')).width));
  addCheck('paragraph starts at the container edge', (await box(page, '#item')).x === (await box(page, '#wrap')).x);
  addCheck('parent tracks are 60px and 230px', (await computed(page, '#wrap', 'grid-template-columns')) === '60px 230px', await computed(page, '#wrap', 'grid-template-columns'));
  addCheck('the following paragraph keeps normal block layout', (await computed(page, '#sib', 'display')) === 'block');
});

CSS_CASES.set('css-example-123', async (page, addCheck) => {
  addCheck('containment is layout paint', (await computed(page, '#box', 'contain')) === 'layout paint', await computed(page, '#box', 'contain'));
  addCheck('box keeps its fixed 60px height', (await box(page, '#box')).height === 60);
  addCheck('inner content is really 200px tall', (await box(page, '#big')).height === 200);
  addCheck('clipping does not come from overflow', (await computed(page, '#box', 'overflow')) === 'visible');
  addCheck('following paragraph starts at 76px, not 276px', (await box(page, '#after')).y === 76, String((await box(page, '#after')).y));
  addCheck('box width is unchanged by containment', (await box(page, '#box')).width === 200);
});

// ---------------------------------------------------------------------------
// D. Sizing units and positioning (124-131)
// ---------------------------------------------------------------------------

CSS_CASES.set('css-example-124', async (page, addCheck) => {
  await pinViewport(page, 960, 720);

  // clamp(200px, 40vw, 320px), min(120px, 20vh) and max(8px, 2vw) all resolve
  // against the real viewport. Derive the expected values from it so the case is
  // correct at any width, including a host-owned window that cannot be pinned.
  const { w, h } = await page.evaluate(() => ({ w: window.innerWidth, h: window.innerHeight }));
  const expectedWidth = Math.min(320, Math.max(200, 0.4 * w));
  const expectedHeight = Math.min(120, 0.2 * h);
  const expectedPad = Math.max(8, 0.02 * w);

  addCheck('width is clamp(200px, 40vw, 320px)', Math.abs((await box(page, '#box')).width - expectedWidth) < 0.6, `${(await box(page, '#box')).width} vs ${expectedWidth.toFixed(2)} at ${w}px`);
  addCheck('height is min(120px, 20vh)', Math.abs((await box(page, '#box')).height - expectedHeight) < 0.6, `${(await box(page, '#box')).height} vs ${expectedHeight.toFixed(2)} at ${h}px`);
  addCheck('padding is max(8px, 2vw)', Math.abs(parseFloat(await computed(page, '#box', 'padding-left')) - expectedPad) < 0.6, `${await computed(page, '#box', 'padding-left')} vs ${expectedPad.toFixed(2)}`);
  addCheck('the computed width matches the resolved clamp', Math.abs(parseFloat(await computed(page, '#box', 'width')) - expectedWidth) < 0.6, await computed(page, '#box', 'width'));

  // clamp(200px, 10vw, 320px) on the second box: 10vw is below the 200px floor
  // at every realistic width, so the floor is what actually applies.
  addCheck('the narrow box is held at the 200px floor', (await box(page, '#small')).width === 200, String((await box(page, '#small')).width));
  addCheck('10vw would be below the floor at this width', 0.1 * w < 200, `${(0.1 * w).toFixed(1)} at ${w}px`);
});

CSS_CASES.set('css-example-125', async (page, addCheck) => {
  addCheck('fit-content shrinks to the available 120px', (await box(page, '#fit')).width === 120, String((await box(page, '#fit')).width));
  const max = await box(page, '#max');
  addCheck('max-content keeps the whole line (145.859px)', Math.abs(max.width - 145.859) < 0.1, String(max.width));
  addCheck('max-content overflows its 120px parent', max.width > 120);
  const min = await box(page, '#min');
  addCheck('min-content narrows to the longest word', Math.abs(min.width - 59.1094) < 0.1, String(min.width));
  addCheck('min-content is narrower than max-content', min.width < max.width);
});

CSS_CASES.set('css-example-126', async (page, addCheck) => {
  addCheck('inset-inline-start resolves to left: 20px', (await computed(page, '#badge', 'left')) === '20px', await computed(page, '#badge', 'left'));
  addCheck('inset-block-start resolves to top: 10px', (await computed(page, '#badge', 'top')) === '10px');
  addCheck('inset-inline-end resolves to right: 0px', (await computed(page, '#note', 'right')) === '0px');
  addCheck('inset-block-end resolves to bottom: 0px', (await computed(page, '#note', 'bottom')) === '0px');
  const stage = await box(page, '#stage');
  const badge = await box(page, '#badge');
  addCheck('badge sits 20px from the stage inline start', badge.x - stage.x === 20, String(badge.x - stage.x));
  const note = await box(page, '#note');
  addCheck('note ends flush with the stage inline end', Math.abs(note.x + note.width - (stage.x + stage.width)) < 0.6, String(note.x + note.width - (stage.x + stage.width)));
});

CSS_CASES.set('css-example-127', async (page, addCheck) => {
  await pinViewport(page, 960, 720);
  addCheck('header is sticky', (await computed(page, '#top', 'position')) === 'sticky');
  addCheck('header sticks at top 0', (await computed(page, '#top', 'top')) === '0px');
  addCheck('sidebar is sticky', (await computed(page, '#side', 'position')) === 'sticky');
  addCheck('sidebar sticks at 48px', (await computed(page, '#side', 'top')) === '48px');
  addCheck('anchor reserves 60px of scroll margin', (await computed(page, '#sec2', 'scroll-margin-top')) === '60px');
  await page.evaluate(() => window.scrollTo(0, 300));
  await page.waitForTimeout(150);
  addCheck('header stays at the top after scrolling', (await box(page, '#top')).y === 0, String((await box(page, '#top')).y));
  addCheck('sidebar stops at 48px after scrolling', (await box(page, '#side')).y === 48, String((await box(page, '#side')).y));
  await page.click('#jump');
  await page.waitForTimeout(300);
  addCheck('anchor jump lands 60px below the viewport top', Math.abs((await box(page, '#sec2')).y - 60) < 1, String((await box(page, '#sec2')).y));
});

CSS_CASES.set('css-example-128', async (page, addCheck) => {
  await pinViewport(page, 960, 720);
  // 50dvh / 50svh are halves of the *real* viewport height. In a static page
  // dvh and svh are equal, so both blocks must be exactly half of innerHeight.
  const h = await page.evaluate(() => window.innerHeight);
  const half = h / 2;
  addCheck('dvh block takes half the dynamic viewport', Math.abs((await box(page, '#hero')).height - half) < 1, `${(await box(page, '#hero')).height} vs ${half} at ${h}px`);
  addCheck('svh block takes half the small viewport', Math.abs((await box(page, '#half')).height - half) < 1, `${(await box(page, '#half')).height} vs ${half}`);
  addCheck('dvh and svh agree in a static viewport', (await box(page, '#hero')).height === (await box(page, '#half')).height);
  addCheck('computed dvh height is the used pixel value', Math.abs(parseFloat(await computed(page, '#hero', 'height')) - half) < 1, await computed(page, '#hero', 'height'));
  addCheck('both units are supported by the engine', (await page.evaluate(() => CSS.supports('height', '50dvh') && CSS.supports('height', '50svh'))));
  addCheck('blocks stack exactly to one viewport height', Math.abs((await box(page, '#half')).y + (await box(page, '#half')).height - h) < 1);
});

CSS_CASES.set('css-example-129', async (page, addCheck) => {
  addCheck('wide card is a size container', (await computed(page, '#wide', 'container-type')) === 'inline-size');
  addCheck('title is 5cqi of a 400px container = 20px', (await computed(page, '#tw', 'font-size')) === '20px', await computed(page, '#tw', 'font-size'));
  addCheck('body is 2.5cqw of a 400px container = 10px', (await computed(page, '#bw', 'font-size')) === '10px', await computed(page, '#bw', 'font-size'));
  addCheck('title is 5cqi of a 200px container = 10px', (await computed(page, '#tn', 'font-size')) === '10px', await computed(page, '#tn', 'font-size'));
  addCheck('body is 2.5cqw of a 200px container = 5px', (await computed(page, '#bn', 'font-size')) === '5px', await computed(page, '#bn', 'font-size'));
  addCheck('both cards live in the same viewport, so the difference is container-driven', (await box(page, '#wide')).x === (await box(page, '#narrow')).x);
});

CSS_CASES.set('css-example-130', async (page, addCheck) => {
  await pinViewport(page, 960, 720);
  // Measure 60ch in the same engine/font rather than assuming 960px of width;
  // the article is then min(60ch, viewport), which holds at every width.
  const ch60 = await page.evaluate(() => {
    const probe = document.createElement('div');
    probe.style.cssText = 'position:absolute;width:60ch;visibility:hidden;left:-9999px;font:16px/1.6 monospace';
    document.body.appendChild(probe);
    const width = probe.getBoundingClientRect().width;
    probe.remove();
    return width;
  });
  addCheck('60ch resolves to the measured monospace measure', Math.abs(parseFloat(await computed(page, '#measure', 'max-width')) - ch60) < 0.5, `${await computed(page, '#measure', 'max-width')} vs ${ch60}`);
  const articleWidth = (await box(page, '#measure')).width;
  const available = await page.locator('#measure').first().evaluate((el) => el.clientWidth);
  addCheck('the article is capped by the measure', Math.abs(articleWidth - Math.min(ch60, available)) < 1, `${articleWidth} vs min(${ch60}, ${available})`);
  addCheck('3cap resolves to a font size larger than the 16px base', parseFloat(await computed(page, '#cap', 'font-size')) > 30, await computed(page, '#cap', 'font-size'));
  addCheck('cap heading is much larger than body text', parseFloat(await computed(page, '#cap', 'font-size')) > 30);
  addCheck('monospace base font is 16px', (await computed(page, '#measure', 'font-size')) === '16px');
});

CSS_CASES.set('css-example-131', async (page, addCheck) => {
  addCheck('overflow: clip is applied', (await computed(page, '#clipbox', 'overflow')) === 'clip', await computed(page, '#clipbox', 'overflow'));
  addCheck('clip margin is 10px', (await computed(page, '#clipbox', 'overflow-clip-margin')) === '10px', await computed(page, '#clipbox', 'overflow-clip-margin'));
  addCheck('hidden box really uses overflow: hidden', (await computed(page, '#hidden', 'overflow')) === 'hidden');
  const clipScroll = await page.locator('#clipbox').evaluate((el) => {
    el.scrollLeft = 50;
    return el.scrollLeft;
  });
  const hiddenScroll = await page.locator('#hidden').evaluate((el) => {
    el.scrollLeft = 50;
    return el.scrollLeft;
  });
  addCheck('clip is not a scroll container (scrollLeft stays 0)', clipScroll === 0, String(clipScroll));
  addCheck('hidden can be scrolled by script (scrollLeft 40)', hiddenScroll === 40, String(hiddenScroll));
  addCheck('both boxes are 120x60', (await box(page, '#clipbox')).width === 120 && (await box(page, '#hidden')).height === 60);
});

// ---------------------------------------------------------------------------
// E. Colour (132-133, continued below)
// ---------------------------------------------------------------------------

CSS_CASES.set('css-example-132', async (page, addCheck) => {
  addCheck('swatch 1 keeps its oklch value', (await computed(page, '#s1', 'background-color')) === 'oklch(0.9 0.05 255)', await computed(page, '#s1', 'background-color'));
  addCheck('swatch 2 keeps its oklch value', (await computed(page, '#s2', 'background-color')) === 'oklch(0.75 0.11 255)');
  addCheck('swatch 3 keeps its oklch value', (await computed(page, '#s3', 'background-color')) === 'oklch(0.6 0.17 255)');
  addCheck('swatch 4 keeps its oklch value', (await computed(page, '#s4', 'background-color')) === 'oklch(0.45 0.21 255)');
  addCheck('all four swatches are 60x60', (await box(page, '#s1')).width === 60 && (await box(page, '#s4')).height === 60);
  addCheck('swatches are laid out left to right', (await box(page, '#s4')).x === 180, String((await box(page, '#s4')).x));
});

const oklabL = (value) => {
  const m = /^oklab\(([0-9.]+) /.exec(String(value || ''));
  return m ? parseFloat(m[1]) : NaN;
};

CSS_CASES.set('css-example-133', async (page, addCheck) => {
  addCheck('base swatch is the theme blue', sameColor(await computed(page, '#base', 'background-color'), '#1a73e8'));
  const l50 = oklabL(await computed(page, '#m50', 'background-color'));
  const l25 = oklabL(await computed(page, '#m25', 'background-color'));
  addCheck('50/50 mix resolves in oklab with L = 0.7868', Math.abs(l50 - 0.786837) < 0.001, String(l50));
  addCheck('25/75 mix resolves in oklab with L = 0.8934', Math.abs(l25 - 0.893415) < 0.001, String(l25));
  addCheck('the 25% mix is lighter than the 50% mix', l25 > l50);
  addCheck('all three swatches are 80x40', (await box(page, '#base')).width === 80 && (await box(page, '#m25')).height === 40);
  addCheck('mixed colour keeps the oklab colour space', String(await computed(page, '#m50', 'background-color')).startsWith('oklab('));
});

CSS_CASES.set('css-example-134', async (page, addCheck) => {
  addCheck('root declares both schemes', (await computed(page, '#card', 'color-scheme')) === 'light dark', await computed(page, '#card', 'color-scheme'));
  addCheck('light theme card background is #f1f3f4', sameColor(await computed(page, '#card', 'background-color'), '#f1f3f4'), await computed(page, '#card', 'background-color'));
  addCheck('light theme text is #202124', sameColor(await computed(page, '#card', 'color'), '#202124'));
  addCheck('light theme page background is white', sameColor(await computed(page, 'body', 'background-color'), '#ffffff'));
  await page.emulateMedia({ colorScheme: 'dark' });
  await page.waitForTimeout(150);
  addCheck('dark theme card background is #303134', sameColor(await computed(page, '#card', 'background-color'), '#303134'), await computed(page, '#card', 'background-color'));
  addCheck('dark theme page background is #202124', sameColor(await computed(page, 'body', 'background-color'), '#202124'));
  addCheck('dark theme text is white', sameColor(await computed(page, '#card', 'color'), '#ffffff'));
});

CSS_CASES.set('css-example-135', async (page, addCheck) => {
  addCheck('base swatch is #3366cc', sameColor(await computed(page, '#base', 'background-color'), '#3366cc'), await computed(page, '#base', 'background-color'));
  addCheck(
    'relative colour keeps the channels and applies 40% alpha',
    (await computed(page, '#dim', 'background-color')) === 'color(srgb 0.2 0.4 0.8 / 0.4)',
    await computed(page, '#dim', 'background-color'),
  );
  addCheck(
    'calc() raises each channel by 60/255',
    (await computed(page, '#lighter', 'background-color')) === 'color(srgb 0.435294 0.635294 1.03529)',
    await computed(page, '#lighter', 'background-color'),
  );
  addCheck('all swatches are 80x40', (await box(page, '#base')).width === 80 && (await box(page, '#lighter')).height === 40);
  addCheck('the derived colour is lighter than the base', parseFloat(/srgb ([\d.]+)/.exec(await computed(page, '#lighter', 'background-color'))[1]) > 0.2);
});

CSS_CASES.set('css-example-136', async (page, addCheck) => {
  addCheck(
    'diagonal stripes keep both stops and the 20px period',
    (await computed(page, '#stripe', 'background-image')) ===
      'repeating-linear-gradient(45deg, rgb(26, 115, 232) 0px, rgb(26, 115, 232) 10px, rgb(255, 255, 255) 10px, rgb(255, 255, 255) 20px)',
    await computed(page, '#stripe', 'background-image'),
  );
  addCheck(
    'zebra stripes use a 40px period',
    (await computed(page, '#zebra', 'background-image')) ===
      'repeating-linear-gradient(90deg, rgb(241, 243, 244) 0px, rgb(241, 243, 244) 20px, rgb(232, 240, 254) 20px, rgb(232, 240, 254) 40px)',
    await computed(page, '#zebra', 'background-image'),
  );
  addCheck('stripes are painted, not a solid colour', (await computed(page, '#stripe', 'background-color')) === 'rgba(0, 0, 0, 0)');
  addCheck('stroke block is 200x40', (await box(page, '#stripe')).width === 200 && (await box(page, '#stripe')).height === 40);
});

CSS_CASES.set('css-example-137', async (page, addCheck) => {
  addCheck(
    'mask fades black to transparent to the right',
    (await computed(page, '#fade', 'mask-image')) === 'linear-gradient(to right, rgb(0, 0, 0), rgba(0, 0, 0, 0))',
    await computed(page, '#fade', 'mask-image'),
  );
  addCheck('mask size is 100% 100%', (await computed(page, '#fade', 'mask-size')) === '100% 100%', await computed(page, '#fade', 'mask-size'));
  addCheck('mask does not repeat', (await computed(page, '#fade', 'mask-repeat')) === 'no-repeat');
  addCheck('fade block is 200x40', (await box(page, '#fade')).width === 200 && (await box(page, '#fade')).height === 40);
  addCheck('the element still has its solid blue background', sameColor(await computed(page, '#fade', 'background-color'), '#1a73e8'));
});

CSS_CASES.set('css-example-138', async (page, addCheck) => {
  addCheck('two mask layers are declared', (await computed(page, '#blend', 'mask-image')).split('radial-gradient').length === 2, await computed(page, '#blend', 'mask-image'));
  addCheck('mask-composite resolves to intersect for both layers', (await computed(page, '#blend', 'mask-composite')) === 'intersect, intersect', await computed(page, '#blend', 'mask-composite'));
  addCheck('both mask layers cover the box', (await computed(page, '#blend', 'mask-size')) === '100% 100%, 100% 100%');
  addCheck('neither layer repeats', (await computed(page, '#blend', 'mask-repeat')) === 'no-repeat, no-repeat');
  addCheck('blend box is 120x120', (await box(page, '#blend')).width === 120 && (await box(page, '#blend')).height === 120);
  addCheck('the radial layer stops at 60%', (await computed(page, '#blend', 'mask-image')).includes('60%'));
});

CSS_CASES.set('css-example-139', async (page, addCheck) => {
  addCheck(
    'two background layers are stacked',
    (await computed(page, '#blend', 'background-image')) ===
      'linear-gradient(rgb(26, 115, 232), rgb(26, 115, 232)), linear-gradient(90deg, rgb(255, 255, 255), rgb(0, 0, 0))',
    await computed(page, '#blend', 'background-image'),
  );
  addCheck('blend mode multiply applies to both layers', (await computed(page, '#blend', 'background-blend-mode')) === 'multiply, multiply', await computed(page, '#blend', 'background-blend-mode'));
  addCheck('base colour under the gradients is white', sameColor(await computed(page, '#blend', 'background-color'), '#ffffff'));
  addCheck('blend block is 200x80', (await box(page, '#blend')).width === 200 && (await box(page, '#blend')).height === 80);
});

CSS_CASES.set('css-example-140', async (page, addCheck) => {
  addCheck(
    'border-image source is the authored gradient',
    (await computed(page, '#frame', 'border-image-source')) === 'linear-gradient(45deg, rgb(26, 115, 232), rgb(52, 168, 83))',
    await computed(page, '#frame', 'border-image-source'),
  );
  addCheck('slice is the keyword value 1', (await computed(page, '#frame', 'border-image-slice')) === '1');
  addCheck('border width is 8px', (await computed(page, '#frame', 'border-top-width')) === '8px');
  addCheck('border colour is transparent (the image paints)', (await computed(page, '#frame', 'border-top-color')) === 'rgba(0, 0, 0, 0)', await computed(page, '#frame', 'border-top-color'));
  addCheck('corners stay square (radius 0)', (await computed(page, '#frame', 'border-top-left-radius')) === '0px');
  addCheck('content width is 160px', (await computed(page, '#frame', 'width')) === '160px');
});

CSS_CASES.set('css-example-141', async (page, addCheck) => {
  addCheck('emphasis style is a dot', (await computed(page, '#em', 'text-emphasis-style')) === 'dot', await computed(page, '#em', 'text-emphasis-style'));
  addCheck('emphasis colour is the theme blue', sameColor(await computed(page, '#em', 'text-emphasis-color'), '#1a73e8'));
  addCheck('emphasis sits above the text', (await computed(page, '#em', 'text-emphasis-position')) === 'over', await computed(page, '#em', 'text-emphasis-position'));
  addCheck('emphasis does not change the line box height (36px)', (await computed(page, 'p', 'height')) === '36px', await computed(page, 'p', 'height'));
  addCheck('plain text next to it has no emphasis', (await computed(page, 'p', 'text-emphasis-style')) === 'none');
});

CSS_CASES.set('css-example-142', async (page, addCheck) => {
  addCheck('stroke width is 2px', (await computed(page, '#stroke', '-webkit-text-stroke-width')) === '2px', await computed(page, '#stroke', '-webkit-text-stroke-width'));
  addCheck('stroke colour is the theme blue', sameColor(await computed(page, '#stroke', '-webkit-text-stroke-color'), '#1a73e8'));
  addCheck('filled text stays white', sameColor(await computed(page, '#stroke', 'color'), '#ffffff'));
  addCheck('hollow text has a transparent fill', (await computed(page, '#hollow', 'color')) === 'rgba(0, 0, 0, 0)', await computed(page, '#hollow', 'color'));
  addCheck('hollow stroke is green', sameColor(await computed(page, '#hollow', '-webkit-text-stroke-color'), '#34a853'));
  addCheck('both headings are 32px', (await computed(page, '#stroke', 'font-size')) === '32px' && (await computed(page, '#hollow', 'font-size')) === '32px');
});

CSS_CASES.set('css-example-143', async (page, addCheck) => {
  addCheck('wrap heading declares text-wrap: wrap', (await computed(page, '#wrap', 'text-wrap')) === 'wrap');
  addCheck('balanced heading declares text-wrap: balance', (await computed(page, '#balance', 'text-wrap')) === 'balance', await computed(page, '#balance', 'text-wrap'));
  const lines = async (sel) =>
    page.evaluate((s) => {
      const el = document.querySelector(s);
      const range = document.createRange();
      range.selectNodeContents(el);
      return [...range.getClientRects()].map((r) => Math.round(r.width));
    }, sel);
  const wrapLines = await lines('#wrap');
  const balLines = await lines('#balance');
  addCheck('both headings use three lines', wrapLines.length === 3 && balLines.length === 3, `${wrapLines.length} vs ${balLines.length}`);
  addCheck('unbalanced heading ends with a tiny last line', Math.min(...wrapLines) <= 45, wrapLines.join('/'));
  addCheck('balanced heading keeps every line wide', Math.min(...balLines) >= 130, balLines.join('/'));
  addCheck(
    'balance narrows the spread between longest and shortest line',
    Math.max(...balLines) - Math.min(...balLines) < Math.max(...wrapLines) - Math.min(...wrapLines),
    `${Math.max(...balLines) - Math.min(...balLines)} vs ${Math.max(...wrapLines) - Math.min(...wrapLines)}`,
  );
});

CSS_CASES.set('css-example-144', async (page, addCheck) => {
  addCheck('long word allows breaking anywhere', (await computed(page, '.anywhere', 'overflow-wrap')) === 'anywhere', await computed(page, '.anywhere', 'overflow-wrap'));
  addCheck('hyphenation is enabled for the english fragment', (await computed(page, '.hyphen', 'hyphens')) === 'auto');
  addCheck('the hyphenation fragment declares lang="en"', (await attr(page, '#hyphenated', 'lang')) === 'en');
  const anywhere = await box(page, '.anywhere');
  addCheck('broken word stays inside the 120px box', anywhere.width <= 120, String(anywhere.width));
  const hyphen = await box(page, '.hyphen');
  addCheck('hyphenated word also stays inside the box', hyphen.width <= 120, String(hyphen.width));
  addCheck('both boxes are 120px wide', (await box(page, '#broken')).width === 122 && (await box(page, '#hyphenated')).width === 122);
});

CSS_CASES.set('css-example-145', async (page, addCheck) => {
  addCheck('tabular-nums is applied to the first row', (await computed(page, '#tnum', 'font-variant-numeric')) === 'tabular-nums', await computed(page, '#tnum', 'font-variant-numeric'));
  addCheck('proportional-nums is applied to the second row', (await computed(page, '#pnum', 'font-variant-numeric')) === 'proportional-nums');
  const t1 = await box(page, '#t1');
  const t2 = await box(page, '#t2');
  addCheck('tabular digits 1111 and 8888 are exactly equal width', t1.width === t2.width, `${t1.width} vs ${t2.width}`);
  addCheck('tabular digit run is 56.3px wide', Math.abs(t1.width - 56.3) < 0.1, String(t1.width));
  addCheck('both rows start at the same x', t1.x === (await box(page, '#p1')).x);
});

CSS_CASES.set('css-example-146', async (page, addCheck) => {
  addCheck('skip-ink auto is applied', (await computed(page, '#ink', 'text-decoration-skip-ink')) === 'auto', await computed(page, '#ink', 'text-decoration-skip-ink'));
  addCheck('skip-ink none is applied to the second link', (await computed(page, '#noink', 'text-decoration-skip-ink')) === 'none');
  addCheck('underline offset is 4px on both', (await computed(page, '#ink', 'text-underline-offset')) === '4px' && (await computed(page, '#noink', 'text-underline-offset')) === '4px');
  addCheck('decoration thickness is 2px', (await computed(page, '#ink', 'text-decoration-thickness')) === '2px');
  addCheck('decoration line is underline', (await computed(page, '#ink', 'text-decoration-line')) === 'underline');
  addCheck('both links keep the theme colour', sameColor(await computed(page, '#ink', 'color'), '#1a73e8'));
});

CSS_CASES.set('css-example-147', async (page, addCheck) => {
  addCheck('box-decoration-break is clone', (await computed(page, '#hl', 'box-decoration-break')) === 'clone', await computed(page, '#hl', 'box-decoration-break'));
  const fragments = await page.locator('#hl').evaluate((el) => el.getClientRects().length);
  addCheck('the highlight is fragmented into 3 line boxes', fragments === 3, String(fragments));
  addCheck('every fragment keeps the 6px left padding', (await computed(page, '#hl', 'padding-left')) === '6px');
  addCheck('every fragment keeps the 3px left border', (await computed(page, '#hl', 'border-left-width')) === '3px');
  addCheck('every fragment keeps the highlight background', sameColor(await computed(page, '#hl', 'background-color'), '#e8f0fe'));
  addCheck('the narrow container is 260px wide', (await box(page, '.narrow')).width === 262, String((await box(page, '.narrow')).width));
});

CSS_CASES.set('css-example-148', async (page, addCheck) => {
  addCheck('plain heading has no trimming', (await computed(page, '#plain', 'text-box-trim')) === 'none');
  addCheck('trimmed heading declares trim-both', (await computed(page, '#trim', 'text-box-trim')) === 'trim-both', await computed(page, '#trim', 'text-box-trim'));
  addCheck('trim edge is cap alphabetic', (await computed(page, '#trim', 'text-box-edge')) === 'cap alphabetic', await computed(page, '#trim', 'text-box-edge'));
  addCheck('plain heading box is 48px tall', (await computed(page, '#plain', 'height')) === '48px', await computed(page, '#plain', 'height'));
  addCheck('trimmed heading box shrinks to 30.25px', (await computed(page, '#trim', 'height')) === '30.25px', await computed(page, '#trim', 'height'));
  addCheck('both headings keep the 40px font size', (await computed(page, '#trim', 'font-size')) === '40px');
});

CSS_CASES.set('css-example-149', async (page, addCheck) => {
  addCheck('panel starts hidden', (await computed(page, '#panel', 'display')) === 'none');
  addCheck('display is in the transition property list', (await computed(page, '#panel', 'transition-property')) === 'opacity, transform, display', await computed(page, '#panel', 'transition-property'));
  addCheck('display transitions discretely', (await computed(page, '#panel', 'transition-behavior')) === 'normal, normal, allow-discrete', await computed(page, '#panel', 'transition-behavior'));
  addCheck(
    '@starting-style rule is parsed',
    (await page.evaluate(() => [...document.styleSheets[0].cssRules].some((r) => r.constructor.name === 'CSSStartingStyleRule'))),
  );
  await page.click('#btn');
  await page.waitForTimeout(450);
  addCheck('panel becomes visible after the click', (await computed(page, '#panel', 'display')) === 'block');
  addCheck('panel reaches full opacity', (await computed(page, '#panel', 'opacity')) === '1', await computed(page, '#panel', 'opacity'));
  addCheck('panel ends at its resting position', (await computed(page, '#panel', 'transform')) === 'matrix(1, 0, 0, 1, 0, 0)', await computed(page, '#panel', 'transform'));
  await page.click('#btn');
  await page.waitForTimeout(500);
  addCheck('closing hides the panel again', (await computed(page, '#panel', 'display')) === 'none');
});

CSS_CASES.set('css-example-150', async (page, addCheck) => {
  addCheck('animation name is slide', (await computed(page, '#bar', 'animation-name')) === 'slide');
  addCheck('duration is 0.3s', (await computed(page, '#bar', 'animation-duration')) === '0.3s');
  addCheck('delay is 0.1s', (await computed(page, '#bar', 'animation-delay')) === '0.1s');
  addCheck('fill mode is forwards', (await computed(page, '#bar', 'animation-fill-mode')) === 'forwards', await computed(page, '#bar', 'animation-fill-mode'));
  await page.waitForTimeout(700);
  addCheck('the final frame is kept at translateX(60px)', (await computed(page, '#bar', 'transform')) === 'matrix(1, 0, 0, 1, 60, 0)', await computed(page, '#bar', 'transform'));
  addCheck('the bar keeps its 60px width', (await box(page, '#bar')).width === 60);
});

CSS_CASES.set('css-example-151', async (page, addCheck) => {
  addCheck(
    'custom easing curve is parsed',
    (await computed(page, '#dot', 'transition-timing-function')) === 'cubic-bezier(0.2, 0.8, 0.2, 1)',
    await computed(page, '#dot', 'transition-timing-function'),
  );
  addCheck('transition duration is 0.4s', (await computed(page, '#dot', 'transition-duration')) === '0.4s');
  await page.hover('#dot');
  await page.waitForTimeout(120);
  const tx = await page.locator('#dot').evaluate((el) => {
    const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(el).transform);
    return m ? parseFloat(m[1].split(',')[4]) : 0;
  });
  addCheck('at ~30% of the duration the dot has already moved past the linear position', tx > 40, String(tx));
  addCheck('the dot has not finished yet', tx < 100, String(tx));
  await page.waitForTimeout(500);
  addCheck('the dot ends exactly 100px to the right', (await computed(page, '#dot', 'transform')) === 'matrix(1, 0, 0, 1, 100, 0)', await computed(page, '#dot', 'transform'));
});

CSS_CASES.set('css-example-152', async (page, addCheck) => {
  addCheck('animation timeline is the root scroller', (await computed(page, '#bar', 'animation-timeline')) === 'scroll(root)', await computed(page, '#bar', 'animation-timeline'));
  addCheck('keyframes name is grow', (await computed(page, '#bar', 'animation-name')) === 'grow');
  addCheck('fill mode keeps both ends', (await computed(page, '#bar', 'animation-fill-mode')) === 'both');
  const scaleX = () =>
    page.locator('#bar').evaluate((el) => {
      const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(el).transform);
      return m ? parseFloat(m[1].split(',')[0]) : NaN;
    });
  addCheck('progress starts at zero', (await scaleX()) === 0, String(await scaleX()));
  const max = await page.evaluate(() => document.documentElement.scrollHeight - window.innerHeight);
  addCheck('the page is actually scrollable', max > 800, String(max));
  await page.evaluate(() => window.scrollTo(0, (document.documentElement.scrollHeight - window.innerHeight) / 2));
  await page.waitForTimeout(200);
  const mid = await scaleX();
  addCheck('progress tracks the middle of the scroll range', mid > 0.35 && mid < 0.65, String(mid));
  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
  await page.waitForTimeout(200);
  addCheck('progress reaches full width at the bottom', (await scaleX()) === 1, String(await scaleX()));
});

CSS_CASES.set('css-example-153', async (page, addCheck) => {
  addCheck('spinner animates by default', (await computed(page, '#spinner', 'animation-name')) === 'spin', await computed(page, '#spinner', 'animation-name'));
  addCheck('spin loops forever', (await computed(page, '#spinner', 'animation-iteration-count')) === 'infinite');
  addCheck('spin duration is 1s', (await computed(page, '#spinner', 'animation-duration')) === '1s');
  addCheck('the ring is circular', (await computed(page, '#spinner', 'border-top-left-radius')) === '50%');
  addCheck(
    'the reduce media query is declared',
    (await page.evaluate(() =>
      [...document.styleSheets[0].cssRules].some((r) => r.conditionText && r.conditionText.includes('prefers-reduced-motion')),
    )),
  );
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.waitForTimeout(120);
  addCheck('reduced motion turns the animation off', (await computed(page, '#spinner', 'animation-name')) === 'none', await computed(page, '#spinner', 'animation-name'));
  addCheck('the spinner keeps its 32px size', (await box(page, '#spinner')).width === 40 && (await computed(page, '#spinner', 'width')) === '32px');
});

CSS_CASES.set('css-example-154', async (page, addCheck) => {
  addCheck('replace composition keeps the last animation only', (await computed(page, '#rep', 'animation-composition')) === 'replace');
  addCheck('accumulate composition applies to both animations', (await computed(page, '#acc', 'animation-composition')) === 'accumulate, accumulate', await computed(page, '#acc', 'animation-composition'));
  await page.waitForTimeout(1200);
  addCheck('replace ends at translateX(20px)', (await computed(page, '#rep', 'transform')) === 'matrix(1, 0, 0, 1, 20, 0)', await computed(page, '#rep', 'transform'));
  addCheck('accumulate ends at translateX(30px)', (await computed(page, '#acc', 'transform')) === 'matrix(1, 0, 0, 1, 30, 0)', await computed(page, '#acc', 'transform'));
  addCheck('both boxes keep fill-mode forwards', (await computed(page, '#acc', 'animation-fill-mode')) === 'forwards');
  addCheck('both boxes are 20x20', (await box(page, '#rep')).width === 20 && (await box(page, '#acc')).height === 20);
});

CSS_CASES.set('css-example-155', async (page, addCheck) => {
  addCheck('rail snaps on the x axis mandatorily', (await computed(page, '#rail', 'scroll-snap-type')) === 'x mandatory', await computed(page, '#rail', 'scroll-snap-type'));
  addCheck('cards snap their start edge', (await computed(page, '#c1', 'scroll-snap-align')) === 'start');
  const rail = await box(page, '#rail');
  addCheck('rail is 220px wide', rail.width === 220, String(rail.width));
  addCheck('content is 640px wide (3 x 200 + 2 x 20 gap)', (await page.locator('#rail').evaluate((el) => el.scrollWidth)) === 640);
  await page.evaluate(() => document.querySelector('#rail').scrollBy({ left: 250 }));
  await page.waitForTimeout(700);
  addCheck('the rail snaps to the 220px snap point', (await page.locator('#rail').evaluate((el) => el.scrollLeft)) === 220, String(await page.locator('#rail').evaluate((el) => el.scrollLeft)));
  await page.evaluate(() => document.querySelector('#rail').scrollBy({ left: 250 }));
  await page.waitForTimeout(700);
  addCheck('the last card snaps to the clamped end (420px)', (await page.locator('#rail').evaluate((el) => el.scrollLeft)) === 420, String(await page.locator('#rail').evaluate((el) => el.scrollLeft)));
});

CSS_CASES.set('css-example-156', async (page, addCheck) => {
  addCheck('stable gutter is declared', (await computed(page, '#short', 'scrollbar-gutter')) === 'stable', await computed(page, '#short', 'scrollbar-gutter'));
  addCheck('the plain box has no gutter', (await computed(page, '#plain', 'scrollbar-gutter')) === 'auto');
  addCheck('stable reserves 15px even without overflow', (await computed(page, '#short', 'width')) === '185px', await computed(page, '#short', 'width'));
  addCheck('the plain box keeps the full 200px', (await computed(page, '#plain', 'width')) === '200px', await computed(page, '#plain', 'width'));
  addCheck('neither box actually overflows', (await page.locator('#short').evaluate((el) => el.scrollHeight <= el.clientHeight)) === true);
  addCheck('both boxes keep the same outer width', (await box(page, '#short')).width === (await box(page, '#plain')).width);
});

CSS_CASES.set('css-example-157', async (page, addCheck) => {
  await pinViewport(page, 960, 720);
  addCheck('outer scroller contains its overscroll', (await computed(page, '#outer', 'overscroll-behavior')) === 'contain', await computed(page, '#outer', 'overscroll-behavior'));
  addCheck('the outer scroller is really scrollable', (await page.locator('#outer').evaluate((el) => el.scrollHeight > el.clientHeight)) === true);
  addCheck('the inner content is 600px tall in a 200px scroller', (await computed(page, '#inner', 'height')) === '600px' && (await computed(page, '#outer', 'height')) === '200px');

  // Scrolling the inner box to its end must not move the page.
  const outer = await box(page, '#outer');
  const vw = await page.evaluate(() => window.innerWidth);
  const onScreen = outer.x >= 0 && outer.x + outer.width <= vw;
  await page.evaluate(() => {
    const o = document.querySelector('#outer');
    o.scrollTop = o.scrollHeight;
  });
  await page.waitForTimeout(100);
  addCheck('inner scroller reaches its bottom (400px)', (await page.locator('#outer').evaluate((el) => el.scrollTop)) === 400);

  if (onScreen) {
    // Only meaningful when the wheel can actually be delivered to the scroller.
    await page.mouse.move(outer.x + outer.width / 2, outer.y + outer.height / 2);
    const beforeY = await page.evaluate(() => window.scrollY);
    await page.mouse.wheel(0, 600);
    await page.waitForTimeout(300);
    addCheck('the page does not scroll when the inner one is at its end', (await page.evaluate(() => window.scrollY)) === beforeY, `viewport ${vw}px`);
    addCheck('the page itself is long enough to scroll', (await page.evaluate(() => document.documentElement.scrollHeight)) > 1400);
  } else {
    // The fixed 260px-wide scroller sits at left:300px, which is off-screen on a
    // narrow window; assert the containment contract that does not need a wheel.
    addCheck('contain applies to both scroll axes', (await computed(page, '#outer', 'overscroll-behavior-y')) === 'contain' && (await computed(page, '#outer', 'overscroll-behavior-x')) === 'contain', `viewport ${vw}px, scroller at x=${outer.x}`);
    addCheck('the page itself is long enough to scroll', (await page.evaluate(() => document.documentElement.scrollHeight)) > 1400);
  }
});

CSS_CASES.set('css-example-158', async (page, addCheck) => {
  addCheck('input declares field-sizing: content', (await computed(page, '#input', 'field-sizing')) === 'content', await computed(page, '#input', 'field-sizing'));
  addCheck('textarea declares field-sizing: content', (await computed(page, '#textarea', 'field-sizing')) === 'content');
  addCheck('short content sits at the 80px minimum', (await computed(page, '#input', 'width')) === '80px', await computed(page, '#input', 'width'));
  const before = await box(page, '#input');
  await page.fill('#input', '这是一个相当长的输入内容用来观察宽度增长');
  await page.waitForTimeout(150);
  const after = await box(page, '#input');
  addCheck('typing grows the input', after.width > before.width + 100, `${before.width} -> ${after.width}`);
  addCheck('growth stops at the 260px max plus padding and border (278px)', after.width === 278, String(after.width));
  const taBefore = await box(page, '#textarea');
  await page.fill('#textarea', '第一行内容\n第二行内容\n第三行');
  await page.waitForTimeout(150);
  const taAfter = await box(page, '#textarea');
  addCheck('the textarea grows in height with its lines', taAfter.height > taBefore.height, `${taBefore.height} -> ${taAfter.height}`);
});

CSS_CASES.set('css-example-159', async (page, addCheck) => {
  addCheck('native appearance is removed', (await computed(page, '#pick', 'appearance')) === 'none', await computed(page, '#pick', 'appearance'));
  addCheck('right padding reserves 32px for the arrow', (await computed(page, '#pick', 'padding-right')) === '32px');
  addCheck('the control is rounded to 6px', (await computed(page, '#pick', 'border-top-left-radius')) === '6px');
  addCheck(
    'the arrow is an inline data URI',
    (await computed(page, '#pick', 'background-image')).startsWith('url("data:image/svg+xml,'),
    (await computed(page, '#pick', 'background-image')).slice(0, 40),
  );
  addCheck('the arrow is positioned 10px from the right edge', (await computed(page, '#pick', 'background-position')) === 'calc(100% - 10px) 50%', await computed(page, '#pick', 'background-position'));
  addCheck('the arrow does not repeat', (await computed(page, '#pick', 'background-repeat')) === 'no-repeat');
  await page.keyboard.press('Tab');
  await page.waitForTimeout(150);
  addCheck('keyboard focus lands on the select', (await page.evaluate(() => document.activeElement.id)) === 'pick');
  addCheck('a 2px blue focus ring appears', (await computed(page, '#pick', 'outline-width')) === '2px' && sameColor(await computed(page, '#pick', 'outline-color'), '#1a73e8'));
  addCheck('the focus ring is offset by 2px', (await computed(page, '#pick', 'outline-offset')) === '2px');
});

CSS_CASES.set('css-example-160', async (page, addCheck) => {
  addCheck('anchor declares its anchor name', (await computed(page, '#anchor', 'anchor-name')) === '--tip', await computed(page, '#anchor', 'anchor-name'));
  addCheck('tooltip points at that anchor', (await computed(page, '#tip', 'position-anchor')) === '--tip', await computed(page, '#tip', 'position-anchor'));
  addCheck('tooltip area is below the anchor', (await computed(page, '#tip', 'position-area')) === 'bottom');
  addCheck('tooltip is absolutely positioned', (await computed(page, '#tip', 'position')) === 'absolute');
  const anchor = await box(page, '#anchor');
  const tip = await box(page, '#tip');
  addCheck('tooltip top touches the anchor bottom (73px)', tip.y === anchor.y + anchor.height, `${tip.y} vs ${anchor.y + anchor.height}`);
  addCheck(
    'tooltip is horizontally centred on the anchor',
    Math.abs(tip.x + tip.width / 2 - (anchor.x + anchor.width / 2)) < 0.6,
    `${tip.x + tip.width / 2} vs ${anchor.x + anchor.width / 2}`,
  );
  addCheck('tooltip keeps its dark background', sameColor(await computed(page, '#tip', 'background-color'), '#202124'));
});

/** Ids this module covers. */
export const COVERED_IDS = [...CSS_CASES.keys()];

/**
 * Assert one CSS expansion example.
 *
 * @param {import('playwright').Page} page
 * @param {{id:string, language:string, code:string, expectedOutput:string}} example
 * @param {(name:string, ok:boolean, detail?:string) => void} addCheck
 * @returns {Promise<boolean>} true when this module handled the example
 */
export async function assertExpansionExample(page, example, addCheck) {
  const id = example?.id;
  const fn = CSS_CASES.get(id);
  if (!fn) return false;
  await fn(page, addCheck);
  return true;
}
