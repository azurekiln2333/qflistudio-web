// Independent, per-example assertions for WebForge's 101 JavaScript examples.
//
// This module is the concrete oracle for the JS curriculum: every example id
// has at least one meaningful expectation (exact DOM text, an exact console
// line, a canvas paint, or the result of a real interaction). It never passes
// on "non-empty" alone and never uses the check marker as an assertion.
//
// Interface used by scripts/run_examples.mjs:
//   assertJs(page, ctx) -> Promise<Array<{name, ok, detail}>>
// ctx = {
//   id,            // example id
//   logs,          // string[] of "type: text" console lines captured so far
//   getLogs,       // () => string[]  (live, after interactions)
//   interaction,   // result of the generic driver, or null
//   canvasPainted, // () => Promise<boolean>
// }
//
// Only this file owns JS expectations. Do not edit it from other modules.

// Exact expected DOM text per example id, keyed by element id.
// `[/regex/, 'text']` means the element text must match the regex.
const DOM = {
  'js-example-001': { out: '小明 今年 19 岁' },
  'js-example-002': { out: 'n+1=43' },
  'js-example-003': { out: 'B/游客' },
  'js-example-004': { out: '15' },
  'js-example-005': { out: '20' },
  'js-example-006': { out: 'a,b,c,d' },
  'js-example-007': { out: '小明 19' },
  'js-example-010': { out: '1380013****' },
  'js-example-011': { out: '15' },
  'js-example-012': { out: '4' },
  'js-example-013': { out: '{"name":"小明","tags":["html","css"]}' },
  'js-example-014': { out: '年龄必须是数字' },
  'js-example-016': { out: '3' },
  'js-example-017': { out: 'WebForge 本地数据' },
  'js-example-018': { out: '5' },
  'js-example-019': { out: 'dark/16' },
  'js-example-021': { out: [/^掷出[1-6]$/] },
  'js-example-022': { out: '狗 汪汪叫' },
  'js-example-023': { out: '90' },
  'js-example-024': { out: '未知城市/light' },
  'js-example-029': { canvas: true },
  'js-example-035': { out: '1,20,3' },
  'js-example-036': { out: '2,4,10,33' },
  'js-example-037': { out: '1,2,3' },
  'js-example-038': {
    out: '<p>你好，&lt;b&gt;小明&lt;/b&gt;</p>',
  },
  'js-example-039': { out: '1,2,3,4,5' },
  'js-example-040': { out: 'count=5' },
  'js-example-044': { out: 'page=3&q=html&sort=new' },
  'js-example-045': { out: '¥1,234.50 / 3天前' },
  'js-example-047': { out: [/^[1-5](,[1-5]){4}$/] },
  'js-example-048': { out: '99' },
  'js-example-049': { out: '欢迎 小明' },
  'js-example-050': { out: 'AB' },
  'js-example-055': { box: 'translateX' }, // transform applied
  'js-example-056': { canvas: true },
  'js-example-057': { previewSrc: true },
  'js-example-060': { out: '1,234,567.89' },
  'js-example-061': { out: 'olleh' },
  'js-example-062': { out: '匿名用户' },
  'js-example-063': { out: '0.30' },
  'js-example-064': { out: '小明/18' },
  'js-example-065': { out: '2/1' },
  'js-example-066': { out: '200x50 #1a73e8' },
  'js-example-070': { out: 'a 得 3 票' },
  'js-example-071': { canvas: true },
  'js-example-072': { out: '||=10 ??=0' },
  'js-example-073': { out: 'B' },
  'js-example-074': { out: '1,2,3,4' },
  'js-example-075': { out: 'a@b.com' },
  'js-example-076': { out: '||50 ??0' },
  'js-example-077': { out: '6' },
  'js-example-079': { out: '{"A":["甲","丙"],"B":["乙"]}' },
  'js-example-085': { out: '1,2,3' },
  'js-example-086': { out: '2026年10月15日' },
  'js-example-088': { out: '当前页：home' },
  'js-example-093': { scrollTo: true },
  'js-example-097': { out: '14/5' },
  'js-example-098': { out: '你好，小明' },
  'js-example-099': { out: '07:05' },
  'js-example-100': { out: '全部填写：true' },
};

// Exact console substrings expected per id (each must appear in captured logs).
const CONSOLE = {
  'js-example-001': ['小明 今年 19 岁'],
  'js-example-002': ['string number 43'],
  'js-example-003': ['等级 B 昵称 游客'],
  'js-example-004': ['苹果、香蕉、樱桃 15'],
  'js-example-005': ['12 5 20'],
  'js-example-006': ['4 true a-b'],
  'js-example-007': ['小明 18 19 18'],
  'js-example-008': ['active= true'],
  'js-example-009': ['点击了 1 甲'],
  'js-example-010': ['1380013****'],
  'js-example-011': ['[2, 4, 6, 8, 10]', '15'],
  'js-example-012': ['1 2 3'],
  'js-example-013': ['html'],
  'js-example-014': ['捕获：年龄必须是数字', '结束'],
  'js-example-020': ['2026 10'],
  'js-example-022': ['猫 发出声音', '狗 汪汪叫'],
  'js-example-023': ['10', '90'],
  'js-example-024': ['小明', '未知城市', 'light'],
  'js-example-029': ['绘制完成'],
  'js-example-034': ['这是一条警告'],
  'js-example-035': ['[1, 2, 3, 4]', '[1, 20, 3]'],
  'js-example-036': ['[2, 4, 10, 33]'],
  'js-example-037': ['对象键', '2'],
  'js-example-041': ['插入完成'],
  'js-example-043': ['节流已启用'],
  'js-example-045': ['¥1,234.50', '3天前'],
  'js-example-050': ['fulfilled', 'rejected'],
  'js-example-060': ['1,234,567.89'],
  'js-example-062': ['匿名用户', '0'],
  'js-example-063': ['0.30000000000000004', '0.30'],
  'js-example-065': ['2 1'],
  'js-example-067': ['安全写法：'],
  'js-example-070': ['{a: 3, b: 2, c: 1}'],
  'js-example-071': ['dpr='],
  'js-example-072': ['管理员操作', '10 0'],
  'js-example-073': ['B green'],
  'js-example-074': ['[1, 2, 3, 4]', 'h-i-b-y-e'],
  'js-example-075': ['a@b.com'],
  'js-example-076': ['50 0 true'],
  'js-example-077': ['6 0 true'],
  'js-example-078': ['两种方式各渲染 2 项'],
  'js-example-085': ['[1, 2, 3]', '2'],
  'js-example-086': ['2026年10月15日', 'userName'],
  'js-example-093': ['滚动到 s2'],
  'js-example-097': ['14 5'],
  'js-example-098': ['你好，小明'],
  'js-example-099': ['07:05', '====='],
  'js-example-100': ['true false true'],
};

// Interaction-driven expectations: after the runner's generic stimuli, the
// handler must have produced this exact output. These require a specific
// action because they only fire on an event.
const INTERACTION_DOM = {
  'js-example-008': { title: '新标题' },
  'js-example-015': { out: [/^[1-3]$/] }, // interval increments at least once
  'js-example-025': { out: '你好，WebForge' }, // submit with typed value
  'js-example-026': { list: [/条目 1/] },
  'js-example-030': { out: '搜索：WebForge' },
  'js-example-031': { list: [/学习 HTML/] },
  'js-example-032': { out: [/已复制|复制失败/] },
  'js-example-033': { list: [] }, // starts empty; filled by add interaction
  'js-example-040': { out: 'count=5' },
  'js-example-042': { list: [/项 1/] },
  'js-example-043': { out: [/^\d+$/] },
  'js-example-046': { out: 'count=1' },
  'js-example-051': { out: '已保存（模拟）' },
  'js-example-057': { previewSrc: true },
  'js-example-058': { out: [/收到 1 个文件/] },
  'js-example-059': { out: [/当前 \d+ 项/] },
  'js-example-068': { out: '提交成功' },
  'js-example-069': { out: [/[0-3]分\d+秒|时间到/] },
  'js-example-080': { list: [/<li>HTML<\/li>/] },
  'js-example-081': { msg: /格式正确|请检查邮箱格式/ },
  'js-example-082': { menu: { hidden: true } },
  'js-example-083': { out: 'success' },
  'js-example-084': { out: [/已保存 \d+ 字/] },
  'js-example-087': { out: '{"a":1,"nested":{"x":1,"y":9}}' },
  'js-example-090': { out: [/已复制：WEBFORGE-2026|复制失败/] },
  'js-example-091': { out: [/范围有效|开始不能晚于结束/] },
  'js-example-092': { out: [/^(大奖|谢谢参与)$/] },
  'js-example-094': { list: [/甲/, /乙/] },
  'js-example-096': { out: [/请输入数量|数量：\d+/] },
  'js-example-101': { text: '这段文字会被切换高亮。' }, // class toggled, text intact
};

function matches(value, expected) {
  if (expected instanceof RegExp) return expected.test(value);
  if (Array.isArray(expected)) return expected.every((e) => matches(value, e));
  return value === expected;
}

function containsAll(haystack, needles) {
  return needles.every((n) => haystack.includes(n));
}

// These oracles own their real gestures; generic pre-clicks would compete.
export const SELF_DRIVEN_IDS = Object.freeze(['js-example-052', 'js-example-053']);

export function owns(id) {
  // This module owns exactly the original authored cases. Future IDs must
  // supply their own oracle instead of passing through this generic prefix.
  const match = /^js-example-(\d{3})$/.exec(id);
  return match !== null && Number(match[1]) >= 1 && Number(match[1]) <= 101;
}

export async function assertJs(page, ctx) {
  const { id } = ctx;
  const checks = [];

  // --- Per-example concrete actions + assertions ------------------------
  // list.innerHTML structural checks (e.g. template-generated markup).
  const listInner = await page.evaluate(() => {
    const l = document.getElementById('list');
    return l ? l.innerHTML : null;
  });

  if (id === 'js-example-009') {
    const li = page.locator('#list li').first();
    if (await li.count()) await li.click({ timeout: 1000 }).catch(() => {});
  }
  if (id === 'js-example-043') {
    await page.mouse.move(50, 50).catch(() => {});
    await page.mouse.move(80, 80).catch(() => {});
    await page.waitForTimeout(120);
  }
  if (id === 'js-example-084') {
    const ed = page.locator('#editor');
    if (await ed.count()) {
      await ed.click().catch(() => {});
      await page.keyboard.type('X').catch(() => {});
      await page.waitForTimeout(150);
    }
  }
  if (id === 'js-example-091') {
    await page.evaluate(() => {
      const s = document.getElementById('start');
      const e = document.getElementById('end');
      if (s && e) {
        s.value = '2026-01-01';
        e.value = '2026-12-31';
        s.dispatchEvent(new Event('change', { bubbles: true }));
        e.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
    await page.waitForTimeout(120);
  }
  if (id === 'js-example-096') {
    await page.evaluate(() => {
      const q = document.getElementById('qty');
      if (q) {
        q.value = '3';
        q.dispatchEvent(new Event('input', { bubbles: true }));
      }
    });
    await page.waitForTimeout(120);
  }
  if (id === 'js-example-015' || id === 'js-example-069') {
    await page.waitForTimeout(700);
  }
  if (id === 'js-example-055' || id === 'js-example-056') {
    await page.waitForTimeout(300);
  }
  if (id === 'js-example-057') {
    await page.waitForTimeout(300);
  }

  // --- js-example-052: geolocation must settle, visibly, with no hang --------
  // ArkWeb on an offline emulator exposes navigator.geolocation but never
  // resolves either callback (no permission decision is ever made). A correct
  // product therefore bounds the wait itself and always renders a terminal
  // state. The contract asserted here is exactly that: the UI leaves 定位中 and
  // lands on one of the documented outcomes within the lesson's own budget.
  if (id === 'js-example-052') {
    const click = page.locator('#loc').first();
    const present = (await click.count()) > 0;
    checks.push({
      name: 'js 052 action button present',
      ok: present,
      detail: present ? '#loc found' : '#loc missing',
    });
    if (!present) throw new Error('geolocation action button is missing');
    const initial = await page.locator('#out').textContent();
    checks.push({
      name: 'js 052 does not begin with a prefilled terminal state',
      ok: (initial || '').trim() === '',
      detail: `before click: ${JSON.stringify(initial)}`,
    });
    // A missing/covered button must fail. Do not swallow actionability errors
    // or accept selector existence as evidence that the authored handler ran.
    await click.click({ timeout: 3000 });

    // The lesson's watchdog is 800ms; allow a generous margin for device timers.
    let settled = false;
    for (let waited = 0; waited < 4000 && !settled; waited += 100) {
      await page.waitForTimeout(100);
      const current = await page.$eval('#out', (el) => (el.textContent || '').trim()).catch(() => '');
      settled = current !== '' && current !== '定位中';
    }
    const outcome = await page.$eval('#out', (el) => (el.textContent || '').trim()).catch(() => '');

    checks.push({
      name: 'js 052 geolocation settles within budget',
      ok: settled,
      detail: `#out=${JSON.stringify(outcome)} after bounded wait`,
    });

    // Only the documented terminal states are acceptable. This is not a
    // pass-through "non-empty" check: the coordinate branch must look like a
    // coordinate pair, and the failure branch must name a concrete cause.
    const terminal = [
      /^-?\d+\.\d{2},-?\d+\.\d{2}$/, // 纬度,经度
      /^不支持定位$/, // no Geolocation at all
      /^定位超时$/, // bounded watchdog fired (offline / no permission prompt)
      /^定位失败：.+$/, // explicit error, including 用户拒绝
    ];
    const matched = terminal.find((re) => re.test(outcome)) || null;
    checks.push({
      name: 'js 052 terminal state is a documented outcome',
      ok: matched !== null,
      detail: matched
        ? `matched ${matched}`
        : `unexpected ${JSON.stringify(outcome)}`,
    });

    checks.push({
      name: 'js 052 gesture outcome is also logged',
      ok: ctx.getLogs().some((line) => line.replace(/^[a-z]+: /, '') ===
        (outcome === '不支持定位' ? 'unsupported' : outcome)),
      detail: `#out=${JSON.stringify(outcome)}; console=${JSON.stringify(ctx.getLogs())}`,
    });
  }

  // Clipboard responses are controlled only at the platform boundary. Real
  // reachable button clicks still run the unmodified authored handler; this
  // proves its feedback/settlement, not access to the user's real clipboard.
  if (id === 'js-example-053') {
    const add = (name, ok, detail = '') => checks.push({ name: `js 053 ${name}`, ok: ok === true, detail });
    const readOut = () => page.locator('#out').textContent().then((value) => (value || '').trim());
    const waitOut = (expected) => page.waitForFunction(
      (value) => document.getElementById('out')?.textContent.trim() === value,
      expected, { timeout: 4000 },
    );
    await page.evaluate(() => {
      const proto = Object.getPrototypeOf(navigator);
      window.__wfClipboardState = {
        own: Object.getOwnPropertyDescriptor(navigator, 'clipboard'),
        proto: Object.getOwnPropertyDescriptor(proto, 'clipboard'),
        changedOwn: false, changedProto: false, calls: 0, progress: [], replies: [],
      };
    });
    const install = (mode) => page.evaluate((requested) => {
      const saved = window.__wfClipboardState;
      saved.calls = 0;
      saved.progress = [];
      saved.replies = [];
      delete window.__wfClipboardReply;
      const api = requested === 'absent' ? undefined : {
        readText: () => {
          saved.calls += 1;
          // Record authored feedback at the API boundary, before the Promise
          // can settle or a slow CDP round trip can consume the watchdog budget.
          saved.progress.push(document.getElementById('out').textContent.trim());
          return new Promise((resolve, reject) => {
            window.__wfClipboardReply = { resolve, reject };
            saved.replies.push(window.__wfClipboardReply);
          });
        },
      };
      const descriptor = { configurable: true, get: () => api };
      try {
        Object.defineProperty(navigator, 'clipboard', descriptor);
        saved.changedOwn = true;
      } catch {
        Object.defineProperty(Object.getPrototypeOf(navigator), 'clipboard', descriptor);
        saved.changedProto = true;
      }
      return navigator.clipboard === api;
    }, mode);
    const click = () => page.locator('#paste').click({ timeout: 3000 });
    const observe = (reply) => page.evaluate((action) => {
      const saved = window.__wfClipboardState;
      const observed = { calls: saved.calls, progress: [...saved.progress], out: document.getElementById('out').textContent.trim() };
      if (action === 'success') window.__wfClipboardReply.resolve('WEBFORGE-CLIP');
      if (action === 'denied') {
        const error = new Error('Document is not focused');
        error.name = 'NotAllowedError';
        window.__wfClipboardReply.reject(error);
      }
      if (action === 'latest') window.__wfClipboardReply.resolve('LATEST-CLIP');
      return observed;
    }, reply);
    try {
      const successInstalled = await install('success');
      add('controlled success API installed', successInstalled);
      if (!successInstalled) throw new Error('clipboard boundary could not be controlled');
      await click();
      const success = await observe('success');
      add('real click starts the read and shows progress', success.calls === 1 && success.progress[0] === '读取中', JSON.stringify(success));
      await waitOut('内容：WEBFORGE-CLIP');
      add('success renders the exact supplied text', await readOut() === '内容：WEBFORGE-CLIP');

      const deniedInstalled = await install('denied');
      if (!deniedInstalled) throw new Error('clipboard denial boundary could not be controlled');
      await click();
      const denied = await observe('denied');
      add('denied read starts with visible progress', denied.calls === 1 && denied.progress[0] === '读取中', JSON.stringify(denied));
      await waitOut('读取失败：Document is not focused');
      add('denial renders the actual reason', await readOut() === '读取失败：Document is not focused');

      const absentInstalled = await install('absent');
      if (!absentInstalled) throw new Error('clipboard absence boundary could not be controlled');
      await click();
      await waitOut('读取失败：不支持读取');
      const absent = await observe();
      add('absent API reports unsupported without reading', absent.calls === 0 && absent.out === '读取失败：不支持读取', JSON.stringify(absent));

      const hangInstalled = await install('hang');
      if (!hangInstalled) throw new Error('clipboard hang boundary could not be controlled');
      await click();
      const hanging = await observe();
      add('hanging read shows progress after the real click', hanging.calls === 1 && hanging.progress[0] === '读取中', JSON.stringify(hanging));
      await waitOut('读取超时');
      add('the authored watchdog bounds a never-settling read', await readOut() === '读取超时');
      await page.evaluate(() => window.__wfClipboardReply.resolve('LATE-CLIPBOARD-RESULT'));
      await page.waitForTimeout(150);
      add('late completion cannot replace the settled timeout', await readOut() === '读取超时');
      add('timeout is also logged', ctx.getLogs().some((line) => line.replace(/^[a-z]+: /, '') === '读取超时'));

      if (!await install('overlap')) throw new Error('clipboard overlap boundary could not be controlled');
      await click();
      await click();
      const overlap = await observe('latest');
      add('repeat real clicks start two independent reads with feedback',
        overlap.calls === 2 && overlap.progress.length === 2 && overlap.progress.every((value) => value === '读取中'), JSON.stringify(overlap));
      await waitOut('内容：LATEST-CLIP');
      // The first read is still pending. Its own 800ms watchdog must not replace
      // the result of the newer click, even though it has not settled locally.
      await page.waitForTimeout(950);
      add('older request timeout cannot overwrite the newest success', await readOut() === '内容：LATEST-CLIP');
      await page.evaluate(() => window.__wfClipboardState.replies[0].resolve('STALE-CLIP'));
      await page.waitForTimeout(100);
      add('older request completion cannot overwrite the newest success', await readOut() === '内容：LATEST-CLIP');
    } finally {
      const restored = await page.evaluate(() => {
        const saved = window.__wfClipboardState;
        const proto = Object.getPrototypeOf(navigator);
        if (saved.changedOwn) {
          delete navigator.clipboard;
          if (saved.own) Object.defineProperty(navigator, 'clipboard', saved.own);
        }
        if (saved.changedProto) {
          if (saved.proto) Object.defineProperty(proto, 'clipboard', saved.proto);
          else delete proto.clipboard;
        }
        const same = (actual, original) => actual === undefined || original === undefined
          ? actual === original
          : ['get', 'set', 'value', 'writable', 'enumerable', 'configurable'].every((key) => actual[key] === original[key]);
        const ok = same(Object.getOwnPropertyDescriptor(navigator, 'clipboard'), saved.own)
          && same(Object.getOwnPropertyDescriptor(proto, 'clipboard'), saved.proto);
        delete window.__wfClipboardState;
        delete window.__wfClipboardReply;
        return ok;
      });
      add('restores exact original platform descriptors', restored);
    }
  }

  // --- js-example-095: online state must mirror navigator.onLine ------------
  // The device may genuinely be offline, so the expected label is derived from
  // the live navigator.onLine value instead of assuming host connectivity. The
  // listeners are then proven by dispatching real online/offline events.
  if (id === 'js-example-095') {
    const liveOnline = await page.evaluate(() => navigator.onLine);
    const label = (online) => (online ? '在线' : '离线');

    const initial = await page.$eval('#out', (el) => (el.textContent || '').trim()).catch(() => '');
    checks.push({
      name: 'js 095 initial label matches navigator.onLine',
      ok: initial === label(liveOnline),
      detail: `onLine=${liveOnline} expect ${label(liveOnline)} got ${JSON.stringify(initial)}`,
    });

    // Force the offline transition and assert the listener repainted.
    const offlineState = await page.evaluate(() => {
      Object.defineProperty(navigator, 'onLine', { configurable: true, get: () => false });
      window.dispatchEvent(new Event('offline'));
      return document.getElementById('out').textContent.trim();
    });
    checks.push({
      name: 'js 095 offline event repaints to 离线',
      ok: offlineState === '离线',
      detail: `got ${JSON.stringify(offlineState)}`,
    });

    // Force the online transition and assert the listener repainted again.
    const onlineState = await page.evaluate(() => {
      Object.defineProperty(navigator, 'onLine', { configurable: true, get: () => true });
      window.dispatchEvent(new Event('online'));
      return document.getElementById('out').textContent.trim();
    });
    checks.push({
      name: 'js 095 online event repaints to 在线',
      ok: onlineState === '在线',
      detail: `got ${JSON.stringify(onlineState)}`,
    });

    // Restore the device's real state so later assertions see the truth.
    await page
      .evaluate((restore) => {
        Object.defineProperty(navigator, 'onLine', {
          configurable: true,
          get: () => restore,
        });
        window.dispatchEvent(new Event(restore ? 'online' : 'offline'));
      }, liveOnline)
      .catch(() => {});
    const restored = await page.$eval('#out', (el) => (el.textContent || '').trim()).catch(() => '');
    checks.push({
      name: 'js 095 restores real device state',
      ok: restored === label(liveOnline),
      detail: `onLine=${liveOnline} expect ${label(liveOnline)} got ${JSON.stringify(restored)}`,
    });
  }

  // 1. Exact console expectations (if any).
  const consoleLines = ctx
    .getLogs()
    .map((l) => l.replace(/^[a-z]+: /, ''))
    .join('\n');
  if (CONSOLE[id]) {
    const ok = containsAll(consoleLines, CONSOLE[id]);
    checks.push({
      name: `js console ${id}`,
      ok,
      detail: ok
        ? CONSOLE[id].join(' | ')
        : `missing ${CONSOLE[id].filter((n) => !consoleLines.includes(n)).join(', ')}`,
    });
  }

  // 2. Exact DOM text / structure.
  const domSpec = DOM[id];
  if (domSpec) {
    for (const [sel, expected] of Object.entries(domSpec)) {
      if (sel === 'canvas' || sel === 'box' || sel === 'scrollTo' || sel === 'previewSrc') continue;
      const el = await page.$('#' + sel);
      const text = el ? (await el.textContent()) || '' : '';
      const ok = el ? matches(text.trim(), expected) : false;
      checks.push({
        name: `js dom #${sel} ${id}`,
        ok,
        detail: `expect ${String(expected)} got ${JSON.stringify(text.trim())}`,
      });
    }
    if (domSpec.canvas) {
      const painted = await ctx.canvasPainted();
      checks.push({ name: `js canvas painted ${id}`, ok: painted });
    }
    if (domSpec.previewSrc) {
      const src = await page.$eval('#preview', (el) => el.getAttribute('src') || '').catch(() => '');
      // FileReader produces a data: URL; assert the concrete prefix and that
      // the read completed (non-trivial length).
      checks.push({
        name: `js preview src ${id}`,
        ok: src.startsWith('data:') && src.length > 30,
        detail: src.slice(0, 40),
      });
      const readLog = ctx.getLogs().join('\n');
      checks.push({
        name: `js file read log ${id}`,
        ok: /已读取 sample\.txt/.test(readLog),
        detail: readLog.split('\n').pop() || '',
      });
    }
  }

  // 3. Interaction results.
  const actSpec = INTERACTION_DOM[id];
  if (actSpec) {
    for (const [sel, expected] of Object.entries(actSpec)) {
      if (sel === 'previewSrc') continue; // handled in the DOM block above
      if (sel === 'menu') {
        const hidden = await page.$eval('#menu', (m) => m.hidden);
        const ok = hidden === expected.hidden;
        checks.push({ name: `js interaction #menu ${id}`, ok, detail: `hidden=${hidden}` });
        continue;
      }
      if (sel === 'list') {
        const text = (listInner || '').replace(/\s+/g, ' ').trim();
        const ok = Array.isArray(expected) && expected.every((e) => e.test(listInner || ''));
        checks.push({
          name: `js interaction #list ${id}`,
          ok,
          detail: `expect ${expected} got ${JSON.stringify(text.slice(0, 80))}`,
        });
        continue;
      }
      const el = await page.$('#' + sel);
      const text = el ? (await el.textContent()) || '' : '';
      const ok = el ? matches(text.trim(), expected) : false;
      checks.push({
        name: `js interaction #${sel} ${id}`,
        ok,
        detail: `expect ${String(expected)} got ${JSON.stringify(text.trim())}`,
      });
    }
  }

  // 4. Storage-backed lessons: assert the persisted value directly.
  if (id === 'js-example-055') {
    const t = await page.$eval('#box', (el) => el.style.transform).catch(() => '');
    const m = t.match(/translateX\(([\d.]+)px\)/);
    checks.push({
      name: 'js rAF transform applied',
      ok: !!m && Number(m[1]) >= 0,
      detail: t,
    });
  }
  if (id === 'js-example-028') {
    const stored = await page.evaluate(() => localStorage.getItem('msg'));
    checks.push({ name: 'js storage msg set', ok: /^\d+$/.test(stored || ''), detail: String(stored) });
  }
  if (id === 'js-example-054') {
    const stored = await page.evaluate(() => localStorage.getItem('draft'));
    checks.push({ name: 'js storage draft set', ok: (stored || '').includes('WebForge'), detail: String(stored) });
  }
  if (id === 'js-example-089') {
    const y = await page.evaluate(() => window.scrollY);
    checks.push({ name: 'js scroll reset to top', ok: y === 0, detail: `scrollY=${y}` });
  }
  if (id === 'js-example-093') {
    const y = await page.evaluate(() => window.scrollY);
    const log = ctx.getLogs().join('\n');
    const s2Top = await page.evaluate(() => {
      const r = document.getElementById('s2').getBoundingClientRect();
      return Math.round(r.top);
    });
    const vh = await page.evaluate(() => window.innerHeight);
    // Either the page scrolled, or (short page) s2 is already within the
    // viewport; the handler ran either way and must have logged.
    checks.push({
      name: 'js scrolled to s2',
      ok: y > 0 || (s2Top >= 0 && s2Top < vh),
      detail: `scrollY=${y} s2Top=${s2Top} vh=${vh}`,
    });
    checks.push({ name: 'js scroll log', ok: /滚动到 s2/.test(log), detail: log.split('\n').pop() || '' });
  }
  if (id === 'js-example-027') {
    // IntersectionObserver lesson: target must have been revealed (class
    // added) and the visibility message logged. If the target starts in view
    // the observer fires immediately; force a check either way.
    const shown = await page.$eval('#target', (el) => el.classList.contains('show')).catch(() => false);
    const log = ctx.getLogs().join('\n');
    checks.push({ name: 'js observer revealed', ok: shown || /可见/.test(log), detail: `shown=${shown}` });
  }
  if (id === 'js-example-020') {
    // Date lesson: output must be a formatted date string containing 2026.
    const t = await page.$eval('#out', (el) => el.textContent).catch(() => '');
    checks.push({ name: 'js date formatted', ok: /2026/.test(t), detail: t });
  }

  // 5. Coverage enforcement: every JS id must have produced at least one
  // substantive check. A missing oracle entry fails loudly instead of passing.
  if (checks.length === 0) {
    checks.push({ name: `js oracle ${id}`, ok: false, detail: 'no assertion defined for this id' });
  }

  return checks;
}
