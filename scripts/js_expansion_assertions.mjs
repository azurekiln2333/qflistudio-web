// Independent, per-example oracles for WebForge's authored JavaScript
// expansion (js-example-102 … js-example-161).
//
// Contract with scripts/run_examples.mjs (root wires it):
//   COVERED_IDS                       -> ids this module owns
//   assertExpansionExample(page, example, addCheck) -> boolean
//
// Semantics:
//   * returns `false` for any id this module does not own, so the caller can
//     fall through to the legacy `js_example_assertions.mjs` oracle;
//   * returns `true` after running the assertions for an owned id;
//   * `addCheck(name, ok, detail)` records one assertion result each time it is
//     called.
//
// Every owned id asserts exact values (exact DOM text, exact attribute/computed
// style, or the exact result of an interaction this module drives itself). No
// assertion passes merely because a value is non-empty, and the
// `webforge-check` marker injected by the emitter is never used as evidence.
//
// The runner has already applied its generic stimulus before this module runs,
// so handlers never assume untouched initial state: they set the values they
// depend on, then observe the outcome. Console capture starts when the module
// is entered, therefore console assertions cover interaction-driven logs only;
// load-time logging is still verified through the exact DOM result.

const FIRST_ID = 102;
const LAST_ID = 161;

export const COVERED_IDS = Array.from(
  { length: LAST_ID - FIRST_ID + 1 },
  (_, i) => `js-example-${String(FIRST_ID + i).padStart(3, '0')}`,
);

const OWNED = new Set(COVERED_IDS);

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------

async function textOf(page, selector) {
  const value = await page
    .$eval(selector, (el) => el.textContent || '')
    .catch(() => null);
  return value === null ? null : value.trim();
}

async function attrOf(page, selector, name) {
  return page
    .$eval(selector, (el, attrName) => el.getAttribute(attrName), name)
    .catch(() => null);
}

async function styleOf(page, selector, property) {
  return page
    .$eval(
      selector,
      (el, prop) =>
        prop.startsWith('--')
          ? getComputedStyle(el).getPropertyValue(prop).trim()
          : getComputedStyle(el)[prop],
      property,
    )
    .catch(() => null);
}

async function waitForText(page, selector, matcher, timeout = 5000) {
  const source = matcher instanceof RegExp ? matcher.source : matcher;
  const flags = matcher instanceof RegExp ? matcher.flags : '';
  try {
    await page.waitForFunction(
      ({ sel, src, fl }) => {
        const el = document.querySelector(sel);
        if (!el) return false;
        const value = (el.textContent || '').trim();
        return new RegExp(src, fl).test(value);
      },
      { sel: selector, src: source, fl: flags },
      { timeout },
    );
    return true;
  } catch {
    return false;
  }
}

async function canvasPainted(page, selector = 'canvas') {
  return page.evaluate((sel) => {
    const canvas = document.querySelector(sel);
    if (!canvas || !canvas.getContext) return false;
    const ctx = canvas.getContext('2d');
    if (!ctx) return false;
    const { width, height } = canvas;
    if (!width || !height) return false;
    try {
      const { data } = ctx.getImageData(0, 0, width, height);
      for (let i = 3; i < data.length; i += 4) {
        if (data[i] !== 0) return true;
      }
    } catch {
      return false;
    }
    return false;
  }, selector).catch(() => false);
}

async function clickIfPresent(page, selector) {
  const locator = page.locator(selector).first();
  if ((await locator.count()) === 0) return false;
  try {
    await locator.click({ timeout: 2500 });
    return true;
  } catch {
    return false;
  }
}

/**
 * Assert exact DOM text.
 * `expected` may be a string (exact equality) or a RegExp (full match).
 */
async function expectText(page, addCheck, id, selector, expected, label = '') {
  const actual = await textOf(page, selector);
  const ok =
    actual !== null &&
    (expected instanceof RegExp
      ? expected.test(actual)
      : actual === expected);
  addCheck(
    `${id} ${label || selector} exact`,
    ok,
    ok ? `= ${JSON.stringify(actual)}` : `expect ${String(expected)} got ${JSON.stringify(actual)}`,
  );
  return ok;
}

/** Assert exact attribute value. */
async function expectAttr(page, addCheck, id, selector, name, expected) {
  const actual = await attrOf(page, selector, name);
  const ok = actual === expected;
  addCheck(
    `${id} ${selector}@${name} exact`,
    ok,
    ok ? `= ${JSON.stringify(actual)}` : `expect ${JSON.stringify(expected)} got ${JSON.stringify(actual)}`,
  );
  return ok;
}

/** Assert exact computed style value. */
async function expectStyle(page, addCheck, id, selector, property, expected) {
  const actual = await styleOf(page, selector, property);
  const ok = actual === expected;
  addCheck(
    `${id} ${selector} ${property} computed`,
    ok,
    ok ? `= ${JSON.stringify(actual)}` : `expect ${JSON.stringify(expected)} got ${JSON.stringify(actual)}`,
  );
  return ok;
}

const HANDLERS = Object.create(null);

function register(id, handler) {
  HANDLERS[id] = handler;
}

// --- 102..120 ---------------------------------------------------------------

register('js-example-102', async (page, add) => {
  const id = 'js-example-102';
  await expectText(
    page,
    add,
    id,
    '#out',
    'WebForge/2 clone/3 2026-01-02T03:04:05.000Z true',
  );
});

register('js-example-103', async (page, add) => {
  const id = 'js-example-103';
  await expectText(
    page,
    add,
    id,
    '#out',
    '{"web":["HTML","CSS"],"tool":["Terminal"]}',
  );
});

register('js-example-104', async (page, add) => {
  const id = 'js-example-104';
  await expectText(page, add, id, '#out', '甲|戊|丙|戊 长度=5');
});

register('js-example-105', async (page, add) => {
  const id = 'js-example-105';
  await expectText(page, add, id, '#out', '基础:变量,基础:函数,进阶:闭包 共3项');
});

register('js-example-106', async (page, add) => {
  const id = 'js-example-106';
  await expectText(page, add, id, '#out', '20@4 缺失=undefined');
});

register('js-example-107', async (page, add) => {
  const id = 'js-example-107';
  await expectText(page, add, id, '#out', '123|213|312|392');
});

register('js-example-108', async (page, add) => {
  const id = 'js-example-108';
  await expectText(page, add, id, '#out', 'Hello 小明, today is 周五.');
});

register('js-example-109', async (page, add) => {
  const id = 'js-example-109';
  await expectText(
    page,
    add,
    id,
    '#out',
    '{"year":"2026","month":"10","day":"22","byIndex":"2026"}',
  );
});

register('js-example-110', async (page, add) => {
  const id = 'js-example-110';
  await expectText(page, add, id, '#out', '120+30+0=150');
});

register('js-example-111', async (page, add) => {
  const id = 'js-example-111';
  // The document prints its own raw path, lengths and escaped form.
  await expectText(page, add, id, '#out', String.raw`C:\html\new\tab|15|5|7`);
});

register('js-example-112', async (page, add) => {
  const id = 'js-example-112';
  await expectText(page, add, id, '#out', '25.6%|42 km/h');
});

register('js-example-113', async (page, add) => {
  const id = 'js-example-113';
  await expectText(
    page,
    add,
    id,
    '#out',
    '202610220830|2026-10-22T08:30:00.000Z',
  );
});

register('js-example-114', async (page, add) => {
  const id = 'js-example-114';
  await expectText(
    page,
    add,
    id,
    '#out',
    '3|前天/3小时后/HTML、CSS和JavaScript',
  );
});

register('js-example-115', async (page, add) => {
  const id = 'js-example-115';
  await expectText(page, add, id, '#out', 'AabBc|ABabc');
});

register('js-example-116', async (page, add) => {
  const id = 'js-example-116';
  await expectText(page, add, id, '#out', '3|3|0.30|1.00');
});

register('js-example-117', async (page, add) => {
  const id = 'js-example-117';
  await expectText(
    page,
    add,
    id,
    '#out',
    '18446744073709551615|18446744073709551616|bigint|true',
  );
});

register('js-example-118', async (page, add) => {
  const id = 'js-example-118';
  await expectText(page, add, id, '#out', '1,2,3,4|4|10');
});

register('js-example-119', async (page, add) => {
  const id = 'js-example-119';
  await expectText(page, add, id, '#out', 'a,b,inner-done,c');
});

register('js-example-120', async (page, add) => {
  const id = 'js-example-120';
  const settled = await waitForText(page, '#out', /^1>2>3$/);
  add('js-example-120 async iteration settled', settled, 'expect 1>2>3');
  await expectText(page, add, id, '#out', '1>2>3');
});

// --- 121..140 ---------------------------------------------------------------

register('js-example-121', async (page, add) => {
  const id = 'js-example-121';
  await waitForText(page, '#out', /^B\|Y\|AggregateError$/);
  await expectText(page, add, id, '#out', 'B|Y|AggregateError');
});

register('js-example-122', async (page, add) => {
  const id = 'js-example-122';
  const expected = 'ok:样式表已加载,bad:脚本缺失,ok:字体已就绪';
  await waitForText(page, '#out', expected);
  await expectText(page, add, id, '#out', expected);
});

register('js-example-123', async (page, add) => {
  const id = 'js-example-123';
  const clicked = await clickIfPresent(page, '#finish');
  add('js-example-123 button clicked', clicked, clicked ? '#finish' : 'missing');
  await waitForText(page, '#out', 'value=ready');
  await expectText(page, add, id, '#out', 'value=ready');
});

register('js-example-124', async (page, add) => {
  const id = 'js-example-124';
  const expected = 'sync-start>sync-end>microtask>promise>timeout';
  await waitForText(page, '#out', expected);
  await expectText(page, add, id, '#out', expected);
});

register('js-example-125', async (page, add) => {
  const id = 'js-example-125';
  const clicked = await clickIfPresent(page, '#run');
  add('js-example-125 button clicked', clicked, clicked ? '#run' : 'missing');
  await waitForText(page, '#out', 'click>microtask>frame');
  await expectText(page, add, id, '#out', 'click>microtask>frame');
});

register('js-example-126', async (page, add) => {
  const id = 'js-example-126';
  // The button toggles start/cancel, and the generic stimulus may already have
  // started the timer, so click until the observable state is "cancelled".
  let state = null;
  let clicks = 0;
  for (let i = 0; i < 3; i += 1) {
    if (!(await clickIfPresent(page, '#start'))) break;
    clicks += 1;
    await page.waitForTimeout(80);
    state = await textOf(page, '#out');
    if (state === '已取消') break;
  }
  add(`${id} cancellation reached`, state === '已取消', `after ${clicks} clicks: ${state}`);
  await expectText(page, add, id, '#out', '已取消');
  await page.waitForTimeout(400);
  await expectText(page, add, id, '#out', '已取消', 'still cancelled');
});

register('js-example-127', async (page, add) => {
  const id = 'js-example-127';
  await waitForText(page, '#out', /^idle-run native=true remaining=true$/);
  await expectText(
    page,
    add,
    id,
    '#out',
    /^idle-run native=true remaining=true$/,
  );
});

register('js-example-128', async (page, add) => {
  const id = 'js-example-128';
  await expectText(page, add, id, '#out', 'true|false|b|tree');
});

register('js-example-129', async (page, add) => {
  const id = 'js-example-129';
  await expectText(
    page,
    add,
    id,
    '#out',
    '{"level":"7","cardTitle":"设置页"}|7|设置页|false',
  );
});

register('js-example-130', async (page, add) => {
  const id = 'js-example-130';
  await expectText(page, add, id, '#out', '2|true|结构');
  const inner = await page
    .$eval('#list', (el) => el.innerHTML)
    .catch(() => null);
  const expected = [
    '<li class="item"><b>HTML</b><span>结构</span></li>',
    '<li class="item"><b>CSS</b><span>样式</span></li>',
  ].join('');
  add(
    `${id} #list innerHTML exact`,
    inner === expected,
    `got ${JSON.stringify(inner)}`,
  );
});

register('js-example-131', async (page, add) => {
  const id = 'js-example-131';
  // A modal dialog blocks pointer input outside itself; normalise first.
  await page
    .evaluate(() => {
      const dialog = document.getElementById('dlg');
      if (dialog && dialog.open) dialog.close();
    })
    .catch(() => {});
  await clickIfPresent(page, '#open');
  await waitForText(page, '#out', 'open=true');
  await expectText(page, add, id, '#out', 'open=true');
  const open = await page
    .$eval('#dlg', (el) => el.open)
    .catch(() => null);
  add(`${id} dialog open state`, open === true, `open=${open}`);
  await clickIfPresent(page, '#ok');
  await waitForText(page, '#out', 'closed result=confirmed');
  await expectText(page, add, id, '#out', 'closed result=confirmed');
  const returnValue = await page
    .$eval('#dlg', (el) => el.returnValue)
    .catch(() => null);
  add(
    `${id} dialog returnValue exact`,
    returnValue === 'confirmed',
    `returnValue=${JSON.stringify(returnValue)}`,
  );
});

register('js-example-132', async (page, add) => {
  const id = 'js-example-132';
  await expectText(
    page,
    add,
    id,
    '#out',
    'attr:state=idle,connected,attr:state=busy,disconnected|true',
  );
  const remaining = await page
    .evaluate(() => document.querySelectorAll('status-badge').length)
    .catch(() => -1);
  add(`${id} custom element removed`, remaining === 0, `count=${remaining}`);
});

register('js-example-133', async (page, add) => {
  const id = 'js-example-133';
  await expectText(
    page,
    add,
    id,
    '#out',
    '影子内文字|rgb(0, 0, 255)|rgb(200, 0, 0)|open',
  );
});

register('js-example-134', async (page, add) => {
  const id = 'js-example-134';
  await clickIfPresent(page, '#go');
  const done = await waitForText(page, '#out', /^done matrix/);
  add(`${id} animation finished`, done, 'waiting for done matrix');
  await expectText(
    page,
    add,
    id,
    '#out',
    /^done matrix\(1, 0, 0, 1, 120, 0\)$/,
  );
});

register('js-example-135', async (page, add) => {
  const id = 'js-example-135';
  await expectText(page, add, id, '#out', '8px|12px|12px|true');
  await expectStyle(page, add, id, '#box', 'paddingTop', '12px');
});

register('js-example-136', async (page, add) => {
  const id = 'js-example-136';
  await page
    .evaluate(() => {
      const target = document.getElementById('target');
      if (target) target.scrollIntoView({ block: 'center' });
    })
    .catch(() => {});
  const reached = await waitForText(page, '#out', /ratio=1$/);
  add(`${id} observer reached ratio 1`, reached, 'waiting for ratio=1');
  await expectText(page, add, id, '#out', /^fired=\d+ ratio=1$/);
});

register('js-example-137', async (page, add) => {
  const id = 'js-example-137';
  await page
    .evaluate(() => {
      const box = document.getElementById('box');
      if (box) box.style.width = '120px';
    })
    .catch(() => {});
  const mid = await waitForText(page, '#out', /w=120$/);
  add(`${id} observer saw 120px`, mid, 'waiting for w=120');
  await page
    .evaluate(() => {
      const box = document.getElementById('box');
      if (box) box.style.width = '160px';
    })
    .catch(() => {});
  const wide = await waitForText(page, '#out', /w=160$/);
  add(`${id} observer saw 160px`, wide, 'waiting for w=160');
  await expectText(page, add, id, '#out', /^count=\d+ w=160$/);
});

register('js-example-138', async (page, add) => {
  const id = 'js-example-138';
  await expectText(page, add, id, '#out', '离线|离线|1|false');
});

register('js-example-139', async (page, add) => {
  const id = 'js-example-139';
  await expectText(page, add, id, '#out', '片段标题|2|第一段|true');
});

register('js-example-140', async (page, add) => {
  const id = 'js-example-140';
  await expectText(
    page,
    add,
    id,
    '#out',
    '/offline/index.html?a=1&c=3#top|a,c|1|127.0.0.1:8080',
  );
});

// --- 141..161 ---------------------------------------------------------------

register('js-example-141', async (page, add) => {
  const id = 'js-example-141';
  await expectText(page, add, id, '#out', '7|228,184,173|中文A|3');
});

register('js-example-142', async (page, add) => {
  const id = 'js-example-142';
  await waitForText(page, '#out', '8|text/plain|8|true|WebForge');
  await expectText(page, add, id, '#out', '8|text/plain|8|true|WebForge');
});

register('js-example-143', async (page, add) => {
  const id = 'js-example-143';
  const encoded = await textOf(page, '#b64');
  const isBase64 = !!encoded && /^[A-Za-z0-9+/]+={0,2}$/.test(encoded);
  add(
    `${id} base64 alphabet only`,
    isBase64,
    `got ${JSON.stringify(encoded)}`,
  );
  await expectText(
    page,
    add,
    id,
    '#out',
    '离线 WebForge|InvalidCharacterError',
  );
});

register('js-example-144', async (page, add) => {
  const id = 'js-example-144';
  await expectText(
    page,
    add,
    id,
    '#out',
    'uuid=true bytes=4 inrange=true secure=true',
  );
});

register('js-example-145', async (page, add) => {
  const id = 'js-example-145';
  await clickIfPresent(page, '#push');
  await clickIfPresent(page, '#push');
  const search = await page.evaluate(() => location.search);
  const match = /^\?step=(\d+)$/.exec(search);
  add(
    `${id} pushState wrote url`,
    !!match,
    `location.search=${JSON.stringify(search)}`,
  );
  await expectText(page, add, id, '#out', /^path=\?step=\d+$/);
  if (!match) return;
  const step = Number(match[1]);
  await page.evaluate(() => history.back());
  const expected = 'pop=' + JSON.stringify({ step: step - 1 });
  await waitForText(page, '#out', expected);
  await expectText(page, add, id, '#out', expected, 'popstate state');
});

register('js-example-146', async (page, add) => {
  const id = 'js-example-146';
  await expectText(page, add, id, '#out', 'route=home', 'initial route');
  await clickIfPresent(page, '#l-about');
  const changed = await waitForText(page, '#out', 'route=about');
  add(`${id} hashchange rendered`, changed, 'waiting for route=about');
  await expectText(page, add, id, '#out', 'route=about');
  const hash = await page.evaluate(() => location.hash);
  add(`${id} location.hash exact`, hash === '#about', `hash=${hash}`);
});

register('js-example-147', async (page, add) => {
  const id = 'js-example-147';
  await clickIfPresent(page, '#send');
  const received = await waitForText(page, '#out', 'recv=dark#1');
  add(`${id} broadcast received`, received, 'waiting for recv=dark#1');
  await expectText(page, add, id, '#out', 'recv=dark#1');
});

register('js-example-148', async (page, add) => {
  const id = 'js-example-148';
  await clickIfPresent(page, '#calc');
  const summed = await waitForText(page, '#out', 'sum=15');
  add(`${id} worker replied`, summed, 'waiting for sum=15');
  await expectText(page, add, id, '#out', 'sum=15');
});

register('js-example-149', async (page, add) => {
  const id = 'js-example-149';
  await clickIfPresent(page, '#ping');
  const replied = await waitForText(page, '#out', 'reply=HELLO');
  add(`${id} port replied`, replied, 'waiting for reply=HELLO');
  await expectText(page, add, id, '#out', 'reply=HELLO');
});

register('js-example-150', async (page, add) => {
  const id = 'js-example-150';
  await expectText(page, add, id, '#out', '26,115,232,255|1x1');
  const painted = await canvasPainted(page, '#panel');
  add(`${id} canvas painted`, painted, 'canvas has opaque pixels');
});

register('js-example-151', async (page, add) => {
  const id = 'js-example-151';
  await expectText(page, add, id, '#out', /^(offscreen:255,255|fallback)$/);
});

register('js-example-152', async (page, add) => {
  const id = 'js-example-152';
  await expectText(page, add, id, '#out', 'true|120|center|30');
  const painted = await canvasPainted(page, '#board');
  add(`${id} text painted`, painted, 'canvas has opaque pixels');
});

register('js-example-153', async (page, add) => {
  const id = 'js-example-153';
  await expectText(page, add, id, '#out', 'path-drawn|true');
  const painted = await canvasPainted(page, '#board');
  add(`${id} path painted`, painted, 'canvas has opaque pixels');
});

register('js-example-154', async (page, add) => {
  const id = 'js-example-154';
  await expectText(page, add, id, '#out', 'true|20|board|1');
  await expectAttr(page, add, id, '#board circle', 'r', '20');
  await expectAttr(page, add, id, '#board circle', 'fill', '#1a73e8');
});

register('js-example-155', async (page, add) => {
  const id = 'js-example-155';
  const dropped = await page
    .evaluate(() => {
      const zone = document.getElementById('zone');
      if (!zone) return false;
      const dataTransfer = new DataTransfer();
      dataTransfer.setData('text/plain', '离线拖放');
      zone.dispatchEvent(
        new DragEvent('dragover', { bubbles: true, cancelable: true, dataTransfer }),
      );
      zone.dispatchEvent(
        new DragEvent('drop', { bubbles: true, cancelable: true, dataTransfer }),
      );
      return true;
    })
    .catch(() => false);
  add(`${id} drop dispatched`, dropped, 'synthetic DataTransfer');
  await waitForText(page, '#out', 'dropped=离线拖放');
  await expectText(page, add, id, '#out', 'dropped=离线拖放');
  await expectStyle(page, add, id, '#zone', 'borderTopStyle', 'dashed');
});

register('js-example-156', async (page, add) => {
  const id = 'js-example-156';
  const box = await page.locator('#pad').boundingBox().catch(() => null);
  add(`${id} pad measurable`, !!box, box ? `w=${box.width}` : 'no box');
  if (!box) return;
  await page.mouse.click(box.x + 40, box.y + 20);
  await waitForText(page, '#out', /^x=40 y=20 type=mouse$/);
  await expectText(page, add, id, '#out', 'x=40 y=20 type=mouse');
});

register('js-example-157', async (page, add) => {
  const id = 'js-example-157';
  await page.fill('#field', '你好').catch(() => {});
  await waitForText(page, '#out', 'composing=false text=你好');
  await expectText(page, add, id, '#out', 'composing=false text=你好');
  const value = await page.$eval('#field', (el) => el.value).catch(() => null);
  add(`${id} field value exact`, value === '你好', `value=${value}`);
});

register('js-example-158', async (page, add) => {
  const id = 'js-example-158';
  await page
    .evaluate(() => {
      const range = document.getElementById('range');
      range.value = '8';
      range.dispatchEvent(new Event('input', { bubbles: true }));
    })
    .catch(() => {});
  await waitForText(page, '#out', 'v=8');
  await expectText(page, add, id, '#out', 'v=8');
  // Percentage widths are resolved to px by getComputedStyle, so assert the
  // authored inline width instead.
  const inline = await page
    .$eval('#fill', (el) => el.style.width)
    .catch(() => null);
  add(
    `${id} #fill inline width exact`,
    inline === '80%',
    `expect "80%" got ${JSON.stringify(inline)}`,
  );
});

register('js-example-159', async (page, add) => {
  const id = 'js-example-159';
  const setValues = (email, age) =>
    page.evaluate(
      ({ emailValue, ageValue }) => {
        const form = document.getElementById('form');
        const emailInput = document.getElementById('email');
        const ageInput = document.getElementById('age');
        emailInput.value = emailValue;
        ageInput.value = ageValue;
        form.dispatchEvent(new Event('input', { bubbles: true }));
      },
      { emailValue: email, ageValue: age },
    );
  await setValues('a@b.com', '20').catch(() => {});
  await waitForText(page, '#out', 'true|false|false|false');
  await expectText(page, add, id, '#out', 'true|false|false|false', 'valid state');
  await setValues('a@b.com', '10').catch(() => {});
  await waitForText(page, '#out', 'false|false|true|false');
  await expectText(
    page,
    add,
    id,
    '#out',
    'false|false|true|false',
    'underflow state',
  );
});

register('js-example-160', async (page, add) => {
  const id = 'js-example-160';
  await expectText(page, add, id, '#out', 'segmenter|3|WebForge/IDE/2026');
});

register('js-example-161', async (page, add) => {
  const id = 'js-example-161';
  await expectText(page, add, id, '#out', 'supported=5/5');
  const counts = await page
    .evaluate(() => ({
      items: document.querySelectorAll('#list li').length,
      supported: document.querySelectorAll('#list li.yes').length,
    }))
    .catch(() => ({ items: -1, supported: -1 }));
  add(
    `${id} report lists every check`,
    counts.items === 5,
    `items=${counts.items}`,
  );
  add(
    `${id} report marks every check supported`,
    counts.supported === 5,
    `supported=${counts.supported}`,
  );
});

// ---------------------------------------------------------------------------
// public entry point
// ---------------------------------------------------------------------------

export async function assertExpansionExample(page, example, addCheck) {
  const id = example && example.id;
  if (!OWNED.has(id)) return false;
  const handler = HANDLERS[id];
  if (!handler) {
    addCheck(`${id} oracle`, false, 'no handler registered');
    return true;
  }
  await handler(page, addCheck);
  return true;
}
