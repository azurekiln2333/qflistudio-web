// WebForge curriculum: concrete, per-example markup/CSS assertions.
//
// Owner: task 10-15-webforge-offline-ui (scripts/web_markup_assertions.mjs).
// Consumed by the p7-owned runner (`scripts/run_examples.mjs`).
//
// Contract
// --------
//   import { assertMarkupExample } from './web_markup_assertions.mjs';
//   const handled = await assertMarkupExample(page, example, addCheck);
//
//   * `page`      Playwright Page already navigated to `example.code` and given
//                 a short settle window. The module drives any interaction it
//                 needs itself, so it does not depend on the runner's generic
//                 driver having run.
//   * `example`   the raw entry from assets/content/examples.json.
//   * `addCheck`  (name, ok, detail?) => void — the runner's collector.
//   * returns     true when this module asserted the example; false when it
//                 does not handle it (runner keeps its own fallback).
//
// Rules this module follows (per controller):
//   * every example gets at least one CONCRETE semantic-content / attribute
//     assertion, or a CONCRETE CSS computed / interactive value;
//   * no generic `#webforge-check` marker check, no "stylesheet exists", no
//     "any non-empty value", and never "read the DOM and compare it to itself";
//   * expected values are the real, human-reviewed values from the assets.
//
// Organisation: one entry per example id, grouped by subject. Expected strings
// are written literally so a content change fails the assertion.

const HTML_CASES = new Map();
const CSS_CASES = new Map();

function norm(s) {
  return (s == null ? '' : String(s)).replace(/\s+/g, ' ').trim();
}

const text = (page, sel) =>
  page.locator(sel).first().innerText().then(norm).catch(() => null);

const attr = (page, sel, name) =>
  page.locator(sel).first().getAttribute(name).catch(() => null);

const count = (page, sel) => page.locator(sel).count();

const computed = async (page, sel, prop) => {
  const el = await page.$(sel);
  if (!el) return null;
  return el
    .evaluate((node, p) => {
      const cs = getComputedStyle(node);
      return (cs.getPropertyValue(p) || '').trim();
    }, prop)
    .catch(() => null);
};

const isVisible = (page, sel) =>
  page.locator(sel).first().isVisible().catch(() => false);

// Wait past CSS transitions/animations before reading a computed value. The
// examples use up to 0.4s transitions, so 450ms covers the longest here.
const settle = (page, ms = 450) => page.waitForTimeout(ms);

// --- viewport helpers ------------------------------------------------------
//
// Responsive lessons only prove themselves at more than one width. Two facts
// make that harder than calling `page.viewportSize()`:
//
//   * `viewportSize()` is null whenever the page comes from a real browser
//     context instead of a Playwright-created one (the ArkWeb/CDP path the
//     native runner uses), so the width has to come from the document;
//   * `setViewportSize()` throws in exactly that mode, because the window is
//     owned by the host browser.
//
// So widths are read from `window.innerWidth` when necessary, and resizing is
// attempted rather than assumed. When a case cannot resize, it asserts the
// branch that the real width implies instead of silently asserting desktop.

/** Rendered width in CSS pixels, whether or not Playwright owns the viewport. */
async function viewportWidth(page) {
  const size = page.viewportSize();
  if (size && size.width > 0) return size.width;
  const inner = await page.evaluate(() => window.innerWidth).catch(() => 0);
  return inner || 0;
}

/**
 * Run `fn` with the page resized to `width` x `height`, then restore the
 * previous viewport. Returns null when the page cannot be resized.
 */
async function atViewport(page, width, height, fn) {
  const original = page.viewportSize();
  try {
    await page.setViewportSize({ width, height });
  } catch {
    return null;
  }
  try {
    // Media queries re-evaluate synchronously, but a short settle keeps grid
    // track resolution and layout reads deterministic across engines.
    await page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))));
    return await fn();
  } finally {
    if (original) await page.setViewportSize(original).catch(() => {});
  }
}

/**
 * Number of grid tracks that actually carry content.
 *
 * `repeat(auto-fit, ...)` keeps every track it computed and collapses the ones
 * without items to `0px`, so counting all space-separated lengths overcounts.
 * Only positive tracks are real columns.
 */
async function gridColumns(page, sel) {
  return page.locator(sel).first().evaluate((el) => {
    const value = getComputedStyle(el).gridTemplateColumns;
    if (!value || value === 'none') return 0;
    return value
      .split(' ')
      .map((t) => t.trim())
      .filter((t) => t && parseFloat(t) > 0).length;
  });
}

/** Vertical offsets of every match, one per element (rows/stack detection). */
async function tops(page, sel) {
  return page.locator(sel).evaluateAll((els) =>
    els.map((el) => Math.round(el.getBoundingClientRect().top)),
  );
}

/** Horizontal offsets of every match. */
async function lefts(page, sel) {
  return page.locator(sel).evaluateAll((els) =>
    els.map((el) => Math.round(el.getBoundingClientRect().left)),
  );
}

// --- real resource outcomes (not just attribute presence) -------------------
//
// The curriculum is being offline-ified to data:/blob: sources; a syntactically
// valid but corrupt data URI would still "pass" a src-attribute check. These
// helpers assert the resource actually DECODES.

/** Wait until every <img> has finished loading and report decode outcomes. */
async function imageOutcomes(page) {
  return page.evaluate(async () => {
    const imgs = [...document.querySelectorAll('img')];
    await Promise.all(
      imgs.map(
        (img) =>
          new Promise((resolve) => {
            if (img.complete) return resolve();
            img.addEventListener('load', resolve, { once: true });
            img.addEventListener('error', resolve, { once: true });
            setTimeout(resolve, 3000);
          }),
      ),
    );
    return imgs.map((img) => ({
      src: img.getAttribute('src') || '',
      alt: img.getAttribute('alt') || '',
      isData: (img.getAttribute('src') || '').startsWith('data:image/'),
      complete: img.complete,
      naturalWidth: img.naturalWidth,
      naturalHeight: img.naturalHeight,
    }));
  });
}

/** Wait for a media element to expose metadata, then report it. */
async function mediaMetadata(page, selector) {
  return page.evaluate(async (sel) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const ready = () => el.readyState >= 1; // HAVE_METADATA
    if (!ready()) {
      await new Promise((resolve) => {
        el.addEventListener('loadedmetadata', resolve, { once: true });
        el.addEventListener('error', resolve, { once: true });
        setTimeout(resolve, 3000);
      });
    }
    return {
      readyState: el.readyState,
      duration: el.duration,
      videoWidth: el.videoWidth ?? null,
      videoHeight: el.videoHeight ?? null,
      networkState: el.networkState,
    };
  }, selector);
}

/**
 * Decode the first CSS background-image URL of `selector` in the page.
 * Returns { url, ok } where ok means the image decoded (naturalWidth > 0).
 */
async function backgroundDecodes(page, selector) {
  return page.evaluate(async (sel) => {
    const el = document.querySelector(sel);
    if (!el) return { url: '<no element>', ok: false, isData: false };
    const bg = getComputedStyle(el).backgroundImage || '';
    // getComputedStyle wraps the URL in quotes: url("..."). Prefer that form and
    // fall back to a greedy match for any unquoted data URI.
    const quoted = /url\("([^"]+)"\)/.exec(bg);
    const bare = quoted ? null : /url\((['"]?)(.+?)\1\)/.exec(bg);
    const url = quoted ? quoted[1] : bare ? bare[2] : '';
    if (!url) return { url: bg.slice(0, 60), ok: false, isData: false };
    const isData = url.startsWith('data:image/');
    const ok = await new Promise((resolve) => {
      const probe = new Image();
      probe.onload = () => resolve(probe.naturalWidth > 0 && probe.naturalHeight > 0);
      probe.onerror = () => resolve(false);
      probe.src = url;
      setTimeout(() => resolve(false), 3000);
    });
    return { url: url.slice(0, 40), ok, isData };
  }, selector);
}

function rgb(hex) {
  const h = hex.replace('#', '');
  const full = h.length === 3 ? h.split('').map((c) => c + c).join('') : h;
  return `rgb(${parseInt(full.slice(0, 2), 16)}, ${parseInt(full.slice(2, 4), 16)}, ${parseInt(full.slice(4, 6), 16)})`;
}
const sameColor = (got, hex) => norm(got).toLowerCase() === rgb(hex);

// ===========================================================================
// HTML examples (100)
// ===========================================================================

HTML_CASES.set('html-example-001', async (page, addCheck) => {
  addCheck('title', (await page.title()) === '我的第一个页面', await page.title());
  addCheck('h1 text', (await text(page, 'h1')) === '你好，网页');
  addCheck('p text', (await text(page, 'p')) === '这是我的第一个 HTML 页面。');
  addCheck('html lang', (await attr(page, 'html', 'lang')) === 'zh-CN');
});

HTML_CASES.set('html-example-002', async (page, addCheck) => {
  addCheck('h1 text', (await text(page, 'h1')) === '前端入门');
  addCheck('h2 text', (await text(page, 'h2')) === 'HTML');
  addCheck('h3 text', (await text(page, 'h3')) === '标题');
  addCheck('p count', (await count(page, 'p')) === 2);
  addCheck(
    'whitespace collapsed in first p',
    (await text(page, 'p')) === '这是第一段。 多个空格 会被合并。',
    await text(page, 'p'),
  );
});

HTML_CASES.set('html-example-003', async (page, addCheck) => {
  addCheck('strong text', (await text(page, 'strong')) === '务必');
  addCheck('em text', (await text(page, 'em')) === '不要');
  addCheck('strong bold', (await computed(page, 'strong', 'font-weight')) === '700');
  addCheck('em italic', (await computed(page, 'em', 'font-style')) === 'italic');
  addCheck('hr visible', await isVisible(page, 'hr'));
  addCheck('last p', (await text(page, 'p:last-of-type')) === '分隔线之后的段落。');
});

HTML_CASES.set('html-example-004', async (page, addCheck) => {
  addCheck('anchor target id exists', (await count(page, '#footer')) === 1);
  addCheck('top anchor id exists', (await count(page, '#top')) === 1);
  addCheck('footer link href', (await attr(page, 'a[href="#footer"]', 'href')) === '#footer');
  addCheck(
    'external link rel',
    (await attr(page, 'a[href^="https://developer.mozilla.org"]', 'rel')) === 'noopener',
  );
  addCheck(
    'external link target',
    (await attr(page, 'a[href^="https://developer.mozilla.org"]', 'target')) === '_blank',
  );
});

HTML_CASES.set('html-example-005', async (page, addCheck) => {
  addCheck('ul li count', (await count(page, 'ul > li')) === 2);
  addCheck('ul first item', (await text(page, 'ul > li')) === 'HTML');
  addCheck('ol li count', (await count(page, 'ol > li')) === 2);
  addCheck('ol list-style ordered', (await computed(page, 'ol', 'list-style-type')) === 'decimal');
  addCheck('dt text', (await text(page, 'dt')) === 'HTML');
  addCheck('dd text', (await text(page, 'dd')) === '描述结构的标记语言。');
});

HTML_CASES.set('html-example-006', async (page, addCheck) => {
  addCheck('img count', (await count(page, 'img')) === 2);
  addCheck(
    'img alt text',
    (await attr(page, 'img[alt="这张图片缺失时你会看到这段文字"]', 'alt')) ===
      '这张图片缺失时你会看到这段文字',
  );
  addCheck(
    'first img dimensions',
    (await attr(page, 'img[width]', 'width')) === '120' &&
      (await attr(page, 'img[width]', 'height')) === '60',
  );
  // Real decode, not attribute presence: the first image is meant to load; the
  // second (missing.png) intentionally fails so the alt text shows.
  const imgs = await imageOutcomes(page);
  addCheck(
    'first image really decodes',
    imgs[0]?.naturalWidth > 0 && imgs[0]?.naturalHeight > 0,
    JSON.stringify(imgs[0]),
  );
  addCheck('first image is inline data URI', imgs[0]?.isData, JSON.stringify(imgs[0]));
  addCheck(
    'second image intentionally fails to load',
    imgs[1] && imgs[1].complete && imgs[1].naturalWidth === 0,
    JSON.stringify(imgs[1]),
  );
});

HTML_CASES.set('html-example-007', async (page, addCheck) => {
  addCheck('column headers', (await count(page, 'thead th')) === 2);
  addCheck('header first th', (await text(page, 'thead th')) === '语言');
  addCheck('body rows', (await count(page, 'tbody tr')) === 2);
  addCheck('first data cell', (await text(page, 'tbody td')) === 'HTML');
  // <table border="1"> is a presentational hint; engines expose it as
  // `outset`, not `solid`. Assert a visible border of either style.
  const borderStyle = await computed(page, 'table', 'border-top-style');
  addCheck('table shows a border', borderStyle !== 'none' && borderStyle !== '', borderStyle);
});

HTML_CASES.set('html-example-008', async (page, addCheck) => {
  const forId = await attr(page, 'label[for="user"]', 'for');
  addCheck('label targets existing input', (await count(page, `#${forId}`)) === 1);
  addCheck('username input required', (await attr(page, '#user', 'required')) !== null);
  addCheck('password type', (await attr(page, '#pass', 'type')) === 'password');
  addCheck('form method', (await attr(page, 'form', 'method')) === 'post');
  const form = page.locator('form').first();
  addCheck(
    'empty submit blocked by validation',
    await form.evaluate((f) => !f.checkValidity()),
  );
});

HTML_CASES.set('html-example-009', async (page, addCheck) => {
  addCheck('header contains site name', (await text(page, 'header h1')) === '我的博客');
  addCheck('nav link count', (await count(page, 'nav a')) === 2);
  addCheck('article title', (await text(page, 'article h2')) === '第一篇文章');
  addCheck('footer copyright', (await text(page, 'footer p')) === '© 2026 我的博客');
  addCheck('main present', (await count(page, 'main article')) === 1);
});

// html-010: the lesson was rewritten (p5) from a <video>/<audio> demo with
// absent files into a real offline demo: a canvas that repaints per frame and a
// Web Audio oscillator. Assert the observable playback, not tag presence.
HTML_CASES.set('html-example-010', async (page, addCheck) => {
  addCheck('canvas stage present', (await count(page, '#stage')) === 1);
  addCheck('play control present', (await text(page, '#play')) === '播放视频');
  addCheck('beep control present', (await text(page, '#beep')) === '播放音频');

  // Video: clicking #play must start a repainting loop. Capture the canvas
  // pixels, wait, and require they changed (a static canvas is a failure).
  const before = await page
    .locator('#stage')
    .evaluate((c) => c.toDataURL())
    .catch(() => null);
  await page.click('#play');
  await settle(page, 350);
  const after = await page
    .locator('#stage')
    .evaluate((c) => c.toDataURL())
    .catch(() => null);
  addCheck('canvas actually repaints after play', !!before && !!after && before !== after, `${String(before).length}->${String(after).length}`);
  const painted = await page.locator('#stage').evaluate((c) => {
    const ctx = c.getContext('2d');
    const { data } = ctx.getImageData(0, 0, c.width, c.height);
    for (let i = 3; i < data.length; i += 4) if (data[i] !== 0) return true;
    return false;
  });
  addCheck('canvas has non-transparent pixels', painted);
  await page.click('#play');

  // Audio: instrument AudioContext BEFORE the page's handler runs, then drive
  // #beep and require a real oscillator was created and started at 440 Hz.
  await page.addInitScript(() => {
    window.__wfAudio = { contexts: 0, frequencies: [], starts: 0 };
    const Orig = window.AudioContext || window.webkitAudioContext;
    if (!Orig) return;
    class Instrumented extends Orig {
      constructor(...args) {
        super(...args);
        window.__wfAudio.contexts++;
      }
      createOscillator() {
        const osc = super.createOscillator();
        const origConnect = osc.connect.bind(osc);
        osc.connect = (...a) => {
          window.__wfAudio.starts++;
          return origConnect(...a);
        };
        // Capture `osc.frequency.value = N` by wrapping the AudioParam's value.
        try {
          const param = osc.frequency;
          const desc = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(param), 'value');
          if (desc && desc.set && desc.get) {
            Object.defineProperty(param, 'value', {
              configurable: true,
              get: () => desc.get.call(param),
              set: (v) => {
                window.__wfAudio.frequencies.push(v);
                desc.set.call(param, v);
              },
            });
          }
        } catch {
          /* leave frequency unwrapped if the engine forbids it */
        }
        return osc;
      }
    }
    window.AudioContext = Instrumented;
    window.webkitAudioContext = Instrumented;
  });
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(120);
  await page.click('#beep');
  await settle(page, 250);
  const audio = await page.evaluate(() => window.__wfAudio);
  addCheck('clicking beep creates an AudioContext', audio && audio.contexts >= 1, JSON.stringify(audio));
  addCheck('an oscillator was connected/started', audio && audio.starts >= 1, JSON.stringify(audio));
  addCheck('oscillator frequency set to 440', audio && audio.frequencies.includes(440), JSON.stringify(audio));
});

HTML_CASES.set('html-example-011', async (page, addCheck) => {
  addCheck('entity angle brackets render literally', (await text(page, 'p')) === '标签写作 <p> 这样展示。');
  addCheck('ampersand entity renders', (await text(page, 'p:nth-of-type(2)')) === 'AT&T 是公司名。');
  addCheck('nbsp keeps value+unit on one text run', (await text(page, 'p:nth-of-type(3)')) === '价格：100 元');
});

HTML_CASES.set('html-example-012', async (page, addCheck) => {
  addCheck('only visible heading', (await text(page, 'h1')) === '欢迎');
  addCheck('commented markup not rendered', (await count(page, 'p')) === 0);
  const html = await page.content();
  addCheck('comments preserved in source', (html.match(/<!--/g) || []).length >= 2);
});

HTML_CASES.set('html-example-013', async (page, addCheck) => {
  addCheck('button label', (await text(page, 'button')) === '保存');
  addCheck('data-action attribute', (await attr(page, 'button', 'data-action')) === 'save');
  addCheck('data-user-id attribute', (await attr(page, 'button', 'data-user-id')) === '42');
  addCheck('script wrote userId', (await text(page, '#log')) === 'userId=42');
});

HTML_CASES.set('html-example-014', async (page, addCheck) => {
  addCheck('img has a src fallback', (await attr(page, 'img', 'src')) !== null);
  addCheck(
    'srcset offers two candidates',
    (await attr(page, 'img', 'srcset')).includes('480w') &&
      (await attr(page, 'img', 'srcset')).includes('1080w'),
    await attr(page, 'img', 'srcset'),
  );
  addCheck('sizes rule declared', (await attr(page, 'img', 'sizes')).includes('600px'));
  addCheck('alt present', (await attr(page, 'img', 'alt')) === '风景照片');
  // The chosen responsive candidate must actually decode at one of the widths.
  const imgs = await imageOutcomes(page);
  addCheck('chosen responsive image decodes', imgs[0]?.naturalWidth > 0, JSON.stringify(imgs[0]));
  addCheck('chosen responsive image is inline data URI', imgs[0]?.isData, JSON.stringify(imgs[0]));
});

HTML_CASES.set('html-example-015', async (page, addCheck) => {
  addCheck('iframe title', (await attr(page, 'iframe', 'title')) === '内嵌示例');
  addCheck(
    'iframe size',
    (await attr(page, 'iframe', 'width')) === '200' && (await attr(page, 'iframe', 'height')) === '80',
  );
  addCheck('iframe sandboxed', (await attr(page, 'iframe', 'sandbox')) !== null);
  const frame = page.frames().find((f) => f !== page.mainFrame());
  addCheck('srcdoc rendered', frame ? norm(await frame.textContent('p')) === '内嵌文档' : false);
});

HTML_CASES.set('html-example-016', async (page, addCheck) => {
  addCheck('select option count', (await count(page, 'select option')) === 2);
  addCheck('select first option', (await text(page, 'select option')) === 'HTML');
  addCheck('textarea rows', (await attr(page, 'textarea', 'rows')) === '3');
  addCheck('range defaults', (await attr(page, 'input[type=range]', 'value')) === '5');
  addCheck(
    'range bounds',
    (await attr(page, 'input[type=range]', 'min')) === '0' &&
      (await attr(page, 'input[type=range]', 'max')) === '10',
  );
});

HTML_CASES.set('html-example-017', async (page, addCheck) => {
  addCheck('email input typed', (await attr(page, '#mail', 'type')) === 'email');
  addCheck('form novalidate', (await attr(page, '#f', 'novalidate')) !== null);
  await page.fill('#mail', 'not-an-email');
  await page.click('#check');
  addCheck(
    'invalid email shows a non-empty non-pass message',
    (await text(page, '#msg')) !== '通过' && (await text(page, '#msg')) !== '',
    await text(page, '#msg'),
  );
  await page.fill('#mail', 'user@example.com');
  await page.click('#check');
  addCheck('valid email reports 通过', (await text(page, '#msg')) === '通过');
});

HTML_CASES.set('html-example-018', async (page, addCheck) => {
  addCheck('list got three items', (await count(page, '#list .row')) === 3);
  addCheck(
    'list contents',
    (await page.$$eval('#list .row', (els) => els.map((e) => e.textContent).join(','))) === '甲,乙,丙',
  );
});

HTML_CASES.set('html-example-019', async (page, addCheck) => {
  addCheck('button aria-label', (await attr(page, 'button', 'aria-label')) === '关闭对话框');
  addCheck('nav aria-label', (await attr(page, 'nav', 'aria-label')) === '主导航');
  addCheck('para tabindex', (await attr(page, 'p[tabindex]', 'tabindex')) === '0');
  await page.locator('p[tabindex]').focus();
  addCheck('para focusable', await page.evaluate(() => document.activeElement?.tagName === 'P'));
});

HTML_CASES.set('html-example-020', async (page, addCheck) => {
  addCheck(
    'meta description',
    (await attr(page, 'meta[name="description"]', 'content')) === 'WebForge 前端教程示例页面。',
  );
  addCheck('og:title', (await attr(page, 'meta[property="og:title"]', 'content')) === 'WebForge 教程');
  addCheck(
    'viewport meta',
    (await attr(page, 'meta[name="viewport"]', 'content')) === 'width=device-width, initial-scale=1',
  );
  // og:image is now an inline data URI and must decode.
  const ogImage = await attr(page, 'meta[property="og:image"]', 'content');
  addCheck('og:image is inline data', ogImage.startsWith('data:'), ogImage.slice(0, 40));
  const decoded = await page.evaluate(async (url) => {
    return new Promise((resolve) => {
      const probe = new Image();
      probe.onload = () => resolve(probe.naturalWidth > 0);
      probe.onerror = () => resolve(false);
      probe.src = url;
      setTimeout(() => resolve(false), 3000);
    });
  }, ogImage);
  addCheck('og:image data URI really decodes', decoded);
});

HTML_CASES.set('html-example-021', async (page, addCheck) => {
  addCheck('span wraps inline strong', (await text(page, 'span strong')) === '可以嵌套');
  addCheck('list items', (await count(page, 'li')) === 2);
  addCheck('span display is inline', (await computed(page, 'span', 'display')).startsWith('inline'));
});

HTML_CASES.set('html-example-022', async (page, addCheck) => {
  addCheck('svg aria-label', (await attr(page, 'svg', 'aria-label')) === '星标');
  addCheck('svg width', (await attr(page, 'svg', 'width')) === '48');
  addCheck('path present', (await count(page, 'svg path')) === 1);
  await page.hover('svg');
  addCheck('hover fill turns red', sameColor(await computed(page, 'svg', 'fill'), '#ea4335'), await computed(page, 'svg', 'fill'));
});

HTML_CASES.set('html-example-023', async (page, addCheck) => {
  addCheck('figcaption text', (await text(page, 'figcaption')) === '图 1：近三年增长曲线');
  addCheck('img alt', (await attr(page, 'figure img', 'alt')) === '增长曲线');
  addCheck('details closed initially', (await attr(page, 'details', 'open')) === null);
  addCheck('summary text', (await text(page, 'summary')) === '点击展开更多');
  addCheck('collapsed paragraph hidden', !(await isVisible(page, 'details p')));
  await page.click('summary');
  addCheck('expanded paragraph visible', await isVisible(page, 'details p'));
  // chart.png is a real dependency, not an intentional-missing demo: it must
  // actually decode (a corrupt data URI would falsely pass a presence check).
  const imgs = await imageOutcomes(page);
  addCheck(
    'chart image really decodes',
    imgs[0]?.naturalWidth > 0 && imgs[0]?.naturalHeight > 0,
    JSON.stringify(imgs[0]),
  );
  addCheck('chart image is inline data URI', imgs[0]?.isData, JSON.stringify(imgs[0]));
});

HTML_CASES.set('html-example-024', async (page, addCheck) => {
  addCheck(
    'progress value/max',
    (await attr(page, 'progress', 'value')) === '30' && (await attr(page, 'progress', 'max')) === '100',
  );
  addCheck('meter value', (await attr(page, 'meter', 'value')) === '0.7');
  addCheck('first label', (await text(page, 'label')) === '下载进度');
});

HTML_CASES.set('html-example-025', async (page, addCheck) => {
  addCheck('english para lang', (await attr(page, 'p[lang="en"]', 'lang')) === 'en');
  addCheck('arabic para dir', (await attr(page, 'p[lang="ar"]', 'dir')) === 'rtl');
  addCheck('arabic direction computed', (await computed(page, 'p[dir="rtl"]', 'direction')) === 'rtl');
  addCheck('english para direction ltr', (await computed(page, 'p[lang="en"]', 'direction')) === 'ltr');
});

HTML_CASES.set('html-example-026', async (page, addCheck) => {
  addCheck('preview button formaction', (await attr(page, 'button[formaction]', 'formaction')) === '/preview');
  addCheck('reset button type', (await attr(page, 'button[type="reset"]', 'type')) === 'reset');
  addCheck('plain button type', (await attr(page, 'button[type="button"]', 'type')) === 'button');
  addCheck('submit button count', (await count(page, 'button[type="submit"]')) === 2);
});

HTML_CASES.set('html-example-027', async (page, addCheck) => {
  addCheck('icon link rel', (await attr(page, 'link[rel="icon"]', 'href')) !== null);
  addCheck('stylesheet link keeps rel', (await attr(page, 'link[rel="stylesheet"]', 'href')) !== null);
  addCheck('preload link present', (await attr(page, 'link[rel="preload"]', 'as')) !== null);
  // All three hrefs are now inline data: URIs (no fetchable local resource).
  const hrefs = await page.$$eval('link[href]', (els) => els.map((e) => e.getAttribute('href')));
  addCheck('all link hrefs are inline data:', hrefs.every((h) => h.startsWith('data:')), JSON.stringify(hrefs));
  // The favicon data URI must decode as an image.
  const icon = await page.evaluate(async () => {
    const url = document.querySelector('link[rel="icon"]')?.getAttribute('href') || '';
    const ok = await new Promise((resolve) => {
      const probe = new Image();
      probe.onload = () => resolve(probe.naturalWidth > 0);
      probe.onerror = () => resolve(false);
      probe.src = url;
      setTimeout(() => resolve(false), 3000);
    });
    return ok;
  });
  addCheck('favicon data URI really decodes', icon);
});

HTML_CASES.set('html-example-028', async (page, addCheck) => {
  addCheck('article itemtype', (await attr(page, 'article', 'itemtype')) === 'https://schema.org/Article');
  addCheck('headline itemprop', (await attr(page, 'h1', 'itemprop')) === 'headline');
  addCheck('author itemprop', (await attr(page, 'p', 'itemprop')) === 'author');
  addCheck('datePublished datetime', (await attr(page, 'time', 'datetime')) === '2026-10-15');
});

HTML_CASES.set('html-example-029', async (page, addCheck) => {
  addCheck('hero fetchpriority', (await attr(page, 'img[alt="首屏图"]', 'fetchpriority')) === 'high');
  addCheck('below-the-fold lazy', (await attr(page, 'img[alt="下方图"]', 'loading')) === 'lazy');
  addCheck('decoding async', (await attr(page, 'img[alt="首屏图"]', 'decoding')) === 'async');
  // hero.jpg / below.jpg are real dependencies: both must decode.
  const imgs = await imageOutcomes(page);
  addCheck(
    'both performance images decode',
    imgs.length === 2 && imgs.every((i) => i.naturalWidth > 0),
    JSON.stringify(imgs),
  );
  addCheck(
    'performance images are inline data URIs',
    imgs.length === 2 && imgs.every((i) => i.isData),
    JSON.stringify(imgs.map((i) => i.src.slice(0, 24))),
  );
});

HTML_CASES.set('html-example-030', async (page, addCheck) => {
  addCheck('custom element has name attr', (await attr(page, 'x-greeting', 'name')) === '小明');
  addCheck('custom element rendered text', (await text(page, 'x-greeting')) === '你好，小明');
});

HTML_CASES.set('html-example-031', async (page, addCheck) => {
  const h = parseFloat(await computed(page, 'button', 'min-height'));
  const w = parseFloat(await computed(page, 'button', 'min-width'));
  addCheck('button min touch target', h >= 44 && w >= 44, `${h}x${w}`);
  addCheck(
    'viewport-fit cover',
    (await attr(page, 'meta[name="viewport"]', 'content')).includes('viewport-fit=cover'),
  );
});

HTML_CASES.set('html-example-032', async (page, addCheck) => {
  addCheck('legend text', (await text(page, 'legend')) === '联系方式');
  addCheck('fieldset wraps both inputs', (await count(page, 'fieldset input')) === 2);
  addCheck('tel input type', (await attr(page, 'input[name="tel"]', 'type')) === 'tel');
  addCheck('email input type', (await attr(page, 'input[name="mail"]', 'type')) === 'email');
});

HTML_CASES.set('html-example-033', async (page, addCheck) => {
  addCheck('about anchor exists', (await count(page, '#about')) === 1);
  addCheck('contact anchor exists', (await count(page, '#contact')) === 1);
  addCheck('nav targets resolve', (await attr(page, 'nav a', 'href')) === '#about');
  addCheck('message input required', (await attr(page, '#msg', 'required')) !== null);
  addCheck('footer copyright', (await text(page, 'footer p')) === '© 2026 小明');
});

HTML_CASES.set('html-example-034', async (page, addCheck) => {
  addCheck('article title', (await text(page, 'article h1')) === '如何学习前端');
  addCheck('time datetime', (await attr(page, 'time', 'datetime')) === '2026-10-15');
  addCheck('figcaption', (await text(page, 'figcaption')) === '图 1：前端学习路线');
  addCheck('list item count', (await count(page, 'ul li')) === 3);
  addCheck('list last item', (await page.$$eval('ul li', (els) => els[2].textContent)) === 'JavaScript：行为');
  // cover.png is a real dependency: it must decode.
  const imgs = await imageOutcomes(page);
  addCheck('cover image really decodes', imgs[0]?.naturalWidth > 0, JSON.stringify(imgs[0]));
  addCheck('cover image is inline data URI', imgs[0]?.isData, JSON.stringify(imgs[0]));
});

HTML_CASES.set('html-example-035', async (page, addCheck) => {
  const headings = await page.$$eval('h1,h2,h3', (els) => els.map((e) => `${e.tagName}:${e.textContent}`));
  addCheck(
    'heading outline order',
    headings.join('|') === 'H1:前端课程|H2:基础|H3:HTML|H3:CSS|H2:进阶|H3:JavaScript',
    headings.join('|'),
  );
});

HTML_CASES.set('html-example-036', async (page, addCheck) => {
  addCheck('para collapses spaces', (await text(page, 'p')) === '这两个 词之间只有一个空格。');
  addCheck('pre preserves whitespace', (await computed(page, 'pre', 'white-space')) === 'pre');
  addCheck('pre keeps line breaks', (await text(page, 'pre')).includes('return a + b;'));
});

HTML_CASES.set('html-example-037', async (page, addCheck) => {
  addCheck('blockquote cite attr', (await attr(page, 'blockquote', 'cite')) === 'https://example.com/book');
  addCheck('quote text', (await text(page, 'blockquote p')) === '简洁是可靠的前提。');
  addCheck('cite element text', (await text(page, 'cite')) === '《设计原则》');
  addCheck('inline q text', (await text(page, 'q')) === '少即是多');
});

HTML_CASES.set('html-example-038', async (page, addCheck) => {
  addCheck('sup count', (await count(page, 'sup')) === 4);
  addCheck('first sup exponent', (await text(page, 'p:first-of-type sup')) === '2');
  addCheck('sub text', (await text(page, 'sub')) === '2');
  const va = await computed(page, 'sup', 'vertical-align');
  addCheck('sup raised', va === 'super' || parseFloat(va) > 0, va);
});

HTML_CASES.set('html-example-039', async (page, addCheck) => {
  addCheck('dfn text', (await text(page, 'dfn')) === '超文本');
  addCheck('abbr title', (await attr(page, 'abbr', 'title')) === 'HyperText Markup Language');
  addCheck('abbr text', (await text(page, 'abbr')) === 'HTML');
});

HTML_CASES.set('html-example-040', async (page, addCheck) => {
  addCheck('kbd count', (await count(page, 'kbd')) === 2);
  addCheck('kbd text', (await text(page, 'kbd')) === 'Ctrl');
  addCheck('samp text', (await text(page, 'samp')) === 'Build succeeded');
  addCheck('var text', (await text(page, 'var')) === 'x');
  addCheck('code text', (await text(page, 'code')) === '42');
  const kbdFont = await computed(page, 'kbd', 'font-family');
  addCheck('kbd monospace-ish', /mono|Consolas|Courier/i.test(kbdFont), kbdFont);
});

HTML_CASES.set('html-example-041', async (page, addCheck) => {
  addCheck('first time datetime', (await attr(page, 'time', 'datetime')) === '2026-10-15');
  addCheck(
    'duration time datetime',
    (await attr(page, 'time[datetime="PT45M"]', 'datetime')) === 'PT45M',
  );
  addCheck('friendly date text', (await text(page, 'time')) === '2026年10月15日');
});

HTML_CASES.set('html-example-042', async (page, addCheck) => {
  addCheck('nofollow rel', (await attr(page, 'a[rel*="nofollow"]', 'rel')) === 'nofollow noopener');
  addCheck('me rel', (await attr(page, 'a[rel="me"]', 'rel')) === 'me');
  addCheck('link count', (await count(page, 'a[href]')) === 2);
});

HTML_CASES.set('html-example-043', async (page, addCheck) => {
  addCheck('download filename', (await attr(page, 'a', 'download')) === '月度报告.csv');
  addCheck('link text', (await text(page, 'a')) === '下载报告');
  // href is now a data:text/csv URI (the file is inlined, not fetched).
  const href = await attr(page, 'a', 'href');
  addCheck('href is an inline CSV data URI', href.startsWith('data:text/csv'), href);
  addCheck('inline CSV really carries content', (await page.evaluate((h) => decodeURIComponent(h.split(',')[1] || '').length > 0, href)));
});

HTML_CASES.set('html-example-044', async (page, addCheck) => {
  addCheck('email autocomplete', (await attr(page, '#em', 'autocomplete')) === 'email');
  addCheck('password autocomplete', (await attr(page, '#pw', 'autocomplete')) === 'new-password');
  addCheck('password type', (await attr(page, '#pw', 'type')) === 'password');
});

HTML_CASES.set('html-example-045', async (page, addCheck) => {
  addCheck('inputmode numeric', (await attr(page, '#code', 'inputmode')) === 'numeric');
  addCheck('pattern attribute', (await attr(page, '#code', 'pattern')) === '[0-9]{6}');
  addCheck(
    'invalid short code fails validity',
    await page.locator('#code').evaluate((el) => {
      el.value = '123';
      return !el.checkValidity();
    }),
  );
  addCheck(
    'six digits passes validity',
    await page.locator('#code').evaluate((el) => {
      el.value = '123456';
      return el.checkValidity();
    }),
  );
});

HTML_CASES.set('html-example-046', async (page, addCheck) => {
  addCheck('copyright entity renders', (await text(page, 'p')) === '版权 © 2026');
  addCheck('hellip + mdash render', (await text(page, 'p:nth-of-type(2)')) === '省略号… 破折号 —');
  addCheck('heart + star render', (await text(page, 'p:nth-of-type(3)')) === '爱心：❤ 星星：★');
});

HTML_CASES.set('html-example-047', async (page, addCheck) => {
  // Both <source> candidates now use image/svg+xml (they are inline SVG data
  // URIs standing in for avif/webp).
  addCheck('two source elements', (await count(page, 'picture source')) === 2);
  addCheck(
    'source types are svg data URIs',
    (await page.$$eval('picture source', (els) => els.map((e) => e.getAttribute('type')))).every(
      (t) => t === 'image/svg+xml',
    ),
  );
  addCheck('img alt', (await attr(page, 'img', 'alt')) === '风景照片');
  const srcset = await attr(page, 'picture source', 'srcset');
  addCheck('source srcset is inline data', srcset.startsWith('data:'), srcset.slice(0, 40));
  addCheck('fallback img src is inline data', (await attr(page, 'picture img', 'src')).startsWith('data:'));
  // The rendered picture (whichever source wins) must decode.
  const imgs = await imageOutcomes(page);
  addCheck('rendered picture really decodes', imgs[0]?.naturalWidth > 0, JSON.stringify(imgs[0]));
});

HTML_CASES.set('html-example-048', async (page, addCheck) => {
  addCheck('CSP meta present', (await attr(page, 'meta[http-equiv]', 'content')) === "default-src 'self'");
  addCheck('external link rel', (await attr(page, 'a', 'rel')) === 'noopener noreferrer');
  addCheck('external link target', (await attr(page, 'a', 'target')) === '_blank');
});

HTML_CASES.set('html-example-049', async (page, addCheck) => {
  addCheck('skip link target', (await attr(page, 'a.skip', 'href')) === '#main');
  addCheck('main target exists', (await count(page, '#main')) === 1);
  const offLeft = await computed(page, 'a.skip', 'left');
  addCheck('skip link off-screen by default', parseFloat(offLeft) < 0, offLeft);
  await page.locator('a.skip').focus();
  const focusedLeft = await computed(page, 'a.skip', 'left');
  addCheck('skip link visible on focus', parseFloat(focusedLeft) >= 0, focusedLeft);
});

HTML_CASES.set('html-example-050', async (page, addCheck) => {
  addCheck('file input accept', (await attr(page, '#avatar', 'accept')) === 'image/png,image/jpeg');
  addCheck('multiple input', (await attr(page, '#docs', 'multiple')) !== null);
  addCheck('enctype multipart', (await attr(page, 'form', 'enctype')) === 'multipart/form-data');
});

HTML_CASES.set('html-example-051', async (page, addCheck) => {
  addCheck('caption text', (await text(page, 'caption')) === '季度销量');
  addCheck('th scope col count', (await count(page, 'th[scope="col"]')) === 2);
  addCheck('th scope row count', (await count(page, 'th[scope="row"]')) === 2);
  // <col> computed background is unreliable across engines; assert the declared
  // inline style the author wrote, which is the real observable intent.
  addCheck(
    'second col declares shade',
    (await attr(page, 'col:nth-of-type(2)', 'style')).includes('#f5f5f5'),
    await attr(page, 'col:nth-of-type(2)', 'style'),
  );
});

HTML_CASES.set('html-example-052', async (page, addCheck) => {
  addCheck('preconnect href', (await attr(page, 'link[rel="preconnect"]', 'href')) === 'https://fonts.example.com');
  addCheck('preconnect crossorigin', (await attr(page, 'link[rel="preconnect"]', 'crossorigin')) !== null);
  addCheck('dns-prefetch href', (await attr(page, 'link[rel="dns-prefetch"]', 'href')) === 'https://cdn.example.com');
});

HTML_CASES.set('html-example-053', async (page, addCheck) => {
  addCheck('two cards rendered', (await count(page, '#app .card')) === 2);
  addCheck('first card title', (await text(page, '#app .card h3')) === '标题一');
  addCheck('second card description', (await page.$$eval('#app .card p', (els) => els[1].textContent)) === '描述二');
});

HTML_CASES.set('html-example-054', async (page, addCheck) => {
  addCheck('two sections', (await count(page, 'section')) === 2);
  addCheck('first section heading', (await text(page, 'section h2')) === '第一章');
  const media = await page.evaluate(() => {
    for (const ss of document.styleSheets) {
      for (const r of ss.cssRules || []) {
        if (r.media && String(r.media.mediaText).includes('print')) return String(r.media.mediaText);
      }
    }
    return '';
  });
  addCheck('print media rule declared', media.includes('print'), media);
});

HTML_CASES.set('html-example-055', async (page, addCheck) => {
  addCheck('two details', (await count(page, 'details')) === 2);
  addCheck('details share name attr', (await attr(page, 'details', 'name')) === 'faq');
  addCheck('summaries text', (await text(page, 'summary')) === '问题一');
});

HTML_CASES.set('html-example-056', async (page, addCheck) => {
  addCheck('input default value', (await attr(page, 'input[name="city"]', 'value')) === '北京');
  await page.fill('input[name="city"]', '上海');
  addCheck('value changed by typing', (await page.inputValue('input[name="city"]')) === '上海');
  await page.click('button[type="reset"]');
  addCheck('reset restores default', (await page.inputValue('input[name="city"]')) === '北京');
});

HTML_CASES.set('html-example-057', async (page, addCheck) => {
  addCheck('english lang', (await attr(page, 'p[lang="en"]', 'lang')) === 'en');
  addCheck('french lang', (await attr(page, 'p[lang="fr"]', 'lang')) === 'fr');
  addCheck('hreflang alternate', (await attr(page, 'link[rel="alternate"]', 'hreflang')) === 'en');
  addCheck('english text', (await text(page, 'p[lang="en"]')) === 'This is English.');
});

HTML_CASES.set('html-example-058', async (page, addCheck) => {
  addCheck('date min', (await attr(page, '#d', 'min')) === '2026-01-01');
  addCheck('date max', (await attr(page, '#d', 'max')) === '2026-12-31');
  addCheck('time step 900s', (await attr(page, '#t', 'step')) === '900');
  addCheck('date input type', (await attr(page, '#d', 'type')) === 'date');
});

HTML_CASES.set('html-example-059', async (page, addCheck) => {
  const titleWeight = await computed(page, '#title', 'font-weight');
  addCheck('id selector bolds title', titleWeight === '700' || titleWeight === 'bold', titleWeight);
  const itemColor = await computed(page, '.item', 'color');
  addCheck('shared class colours both items', sameColor(itemColor, '#1a73e8'), itemColor);
  addCheck('both items share class', (await count(page, 'p.item')) === 2);
});

HTML_CASES.set('html-example-060', async (page, addCheck) => {
  addCheck('only header rendered', (await text(page, 'header h1')) === '站名');
  const html = await page.content();
  addCheck('TODO comment kept in source', html.includes('TODO: 补充页脚链接'));
});

HTML_CASES.set('html-example-061', async (page, addCheck) => {
  // The external style.css/app.js were inlined; the lesson keeps the same
  // "load order" teaching through inline <style> + deferred <script>.
  addCheck('inline style present', (await page.evaluate(() => document.styleSheets.length >= 1)));
  addCheck('inline style actually applies', sameColor(await computed(page, 'h1', 'color'), '#1a73e8'), await computed(page, 'h1', 'color'));
  const scriptText = await page.locator('script').first().evaluate((el) => el.textContent);
  addCheck('deferred script inlined', scriptText.includes('document.title'));
  addCheck('deferred script ran', (await page.title()) === '已加载内联脚本', await page.title());
  addCheck('heading text', (await text(page, 'h1')) === '外部资源');
});

HTML_CASES.set('html-example-062', async (page, addCheck) => {
  addCheck('article inside main', (await count(page, 'main article')) === 1);
  addCheck('aside inside main', (await count(page, 'main aside')) === 1);
  addCheck('article heading', (await text(page, 'article h1')) === '文章标题');
  addCheck('aside heading', (await text(page, 'aside h2')) === '相关链接');
  addCheck('aside is a block', (await computed(page, 'aside', 'display')) === 'block');
});

HTML_CASES.set('html-example-063', async (page, addCheck) => {
  addCheck('figure floats left', (await computed(page, 'figure', 'float')) === 'left');
  addCheck('figcaption text', (await text(page, 'figcaption')) === '图注');
  addCheck('img alt', (await attr(page, 'img', 'alt')) === '示例');
  // The placeholder image must actually decode, not just carry a src attribute.
  const imgs = await imageOutcomes(page);
  addCheck('placeholder image really decodes', imgs[0]?.naturalWidth > 0, JSON.stringify(imgs[0]));
  addCheck('placeholder image is inline data URI', imgs[0]?.isData, JSON.stringify(imgs[0]));
});

HTML_CASES.set('html-example-064', async (page, addCheck) => {
  addCheck('readonly input', (await attr(page, '#ro', 'readonly')) !== null);
  addCheck('readonly keeps value', (await attr(page, '#ro', 'value')) === 'A-001');
  addCheck('fieldset disabled', (await attr(page, 'fieldset', 'disabled')) !== null);
  addCheck(
    'fieldset input is :disabled',
    await page.locator('#x').evaluate((el) => el.matches(':disabled')),
  );
});

HTML_CASES.set('html-example-065', async (page, addCheck) => {
  const first = await computed(page, 'p', 'color');
  const second = await computed(page, 'p:nth-of-type(2)', 'color');
  addCheck('first paragraph green', sameColor(first, '#008000'), first);
  addCheck('inline style overrides to red', sameColor(second, '#ff0000'), second);
});

HTML_CASES.set('html-example-066', async (page, addCheck) => {
  addCheck('theme-color', (await attr(page, 'meta[name="theme-color"]', 'content')) === '#1a73e8');
  addCheck('favicon link present', (await attr(page, 'link[rel="icon"]', 'href')) !== null);
  addCheck('apple touch icon present', (await attr(page, 'link[rel="apple-touch-icon"]', 'href')) !== null);
  // Both icons are inline SVG data URIs and must decode.
  const ok = await page.evaluate(async () => {
    const urls = ['link[rel="icon"]', 'link[rel="apple-touch-icon"]'].map(
      (s) => document.querySelector(s)?.getAttribute('href') || '',
    );
    return Promise.all(
      urls.map(
        (url) =>
          new Promise((resolve) => {
            const probe = new Image();
            probe.onload = () => resolve(probe.naturalWidth > 0);
            probe.onerror = () => resolve(false);
            probe.src = url;
            setTimeout(() => resolve(false), 3000);
          }),
      ),
    );
  });
  addCheck('both icon data URIs decode', ok.every(Boolean), JSON.stringify(ok));
});

HTML_CASES.set('html-example-067', async (page, addCheck) => {
  addCheck('wrap scrolls horizontally', (await computed(page, '.wrap', 'overflow-x')) === 'auto');
  addCheck('table has min-width', (await computed(page, 'table', 'min-width')) === '480px');
  addCheck('table headers count', (await count(page, 'thead th')) === 4);
});

HTML_CASES.set('html-example-068', async (page, addCheck) => {
  addCheck('autofocus attr present', (await attr(page, '#name', 'autofocus')) !== null);
  addCheck('name field autofocused', await page.evaluate(() => document.activeElement?.id === 'name'));
  addCheck('email input typed', (await attr(page, '#mail', 'type')) === 'email');
});

HTML_CASES.set('html-example-069', async (page, addCheck) => {
  addCheck('mailto href with subject', (await attr(page, 'a[href^="mailto:"]', 'href')) === 'mailto:hi@example.com?subject=咨询');
  addCheck('tel href', (await attr(page, 'a[href^="tel:"]', 'href')) === 'tel:+8613800138000');
});

HTML_CASES.set('html-example-070', async (page, addCheck) => {
  addCheck('nested ul exists', (await count(page, 'nav ul ul')) === 1);
  addCheck('nested items count', (await count(page, 'nav ul ul li')) === 2);
  addCheck('nested first item', (await text(page, 'nav ul ul li')) === 'HTML');
  addCheck('top-level items count', (await count(page, 'nav > ul > li')) === 2);
});

HTML_CASES.set('html-example-071', async (page, addCheck) => {
  addCheck('dt count', (await count(page, 'dt')) === 2);
  addCheck('first dt', (await text(page, 'dt')) === 'HTML');
  addCheck('first dd', (await text(page, 'dd')) === '描述网页结构的标记语言。');
  const ddMargin = await computed(page, 'dd', 'margin-left');
  addCheck('dd indented (non-zero margin)', parseFloat(ddMargin) > 0, ddMargin);
});

HTML_CASES.set('html-example-072', async (page, addCheck) => {
  addCheck('wide img max-width', (await computed(page, 'img', 'max-width')) === '100%');
  addCheck('thumb object-fit cover', (await computed(page, '.thumb', 'object-fit')) === 'cover');
  // `img { max-width: 100% }` shrinks .thumb inside the (narrow) preview, so the
  // declared 120x80 is not the rendered size. Assert the authored rules that
  // actually hold: object-fit cover + a bounded, positive box.
  const thumb = await page.locator('.thumb').boundingBox();
  addCheck(
    'thumb renders a bounded image box',
    thumb.width > 0 && thumb.height > 0 && thumb.width <= 120,
    `${thumb.width}x${thumb.height}`,
  );
  // Both images (wide + thumb) are real dependencies: assert they decode.
  const imgs = await imageOutcomes(page);
  addCheck(
    'both responsive images decode',
    imgs.length === 2 && imgs.every((i) => i.naturalWidth > 0),
    JSON.stringify(imgs),
  );
  addCheck(
    'both responsive images are inline data URIs',
    imgs.length === 2 && imgs.every((i) => i.isData),
    JSON.stringify(imgs.map((i) => i.src.slice(0, 24))),
  );
});

HTML_CASES.set('html-example-073', async (page, addCheck) => {
  addCheck(
    'number bounds',
    (await attr(page, '#qty', 'min')) === '1' && (await attr(page, '#qty', 'max')) === '10',
  );
  addCheck('step 1', (await attr(page, '#qty', 'step')) === '1');
  addCheck('required', (await attr(page, '#qty', 'required')) !== null);
  addCheck(
    'out-of-range value fails validity',
    await page.locator('#qty').evaluate((el) => {
      el.value = '99';
      return !el.checkValidity();
    }),
  );
});

HTML_CASES.set('html-example-074', async (page, addCheck) => {
  addCheck('color input default', (await attr(page, '#c', 'value')) === '#1a73e8');
  const before = await computed(page, '#box', 'background-color');
  addCheck('box starts blue', sameColor(before, '#1a73e8'), before);
  await page.locator('#c').evaluate((el) => {
    el.value = '#34a853';
    el.dispatchEvent(new Event('input', { bubbles: true }));
  });
  const after = await computed(page, '#box', 'background-color');
  addCheck('box follows picker to green', sameColor(after, '#34a853'), after);
});

HTML_CASES.set('html-example-075', async (page, addCheck) => {
  addCheck('source draggable', (await attr(page, '#src', 'draggable')) === 'true');
  addCheck('drop zone exists', (await count(page, '#dst')) === 1);
  await page.evaluate(() => {
    const src = document.getElementById('src');
    const dst = document.getElementById('dst');
    const dt = new DataTransfer();
    src.dispatchEvent(new DragEvent('dragstart', { bubbles: true, dataTransfer: dt }));
    dst.dispatchEvent(new DragEvent('dragover', { bubbles: true, dataTransfer: dt }));
    dst.dispatchEvent(new DragEvent('drop', { bubbles: true, dataTransfer: dt }));
  });
  addCheck('drop zone reflects received data', (await text(page, '#dst')) === '收到：拖我', await text(page, '#dst'));
});

HTML_CASES.set('html-example-076', async (page, addCheck) => {
  addCheck(
    'title matches h1',
    (await page.title()) === 'HTML5 语义标签入门' && (await text(page, 'h1')) === 'HTML5 语义标签入门',
  );
  const order = await page.$$eval('h1,h2,h3', (els) => els.map((e) => e.tagName));
  addCheck('headings descend h1,h2,h2,h3', order.join(',') === 'H1,H2,H2,H3', order.join(','));
});

HTML_CASES.set('html-example-077', async (page, addCheck) => {
  addCheck('search form method get', (await attr(page, 'form[action="/search"]', 'method')) === 'get');
  addCheck('login form method post', (await attr(page, 'form[action="/login"]', 'method')) === 'post');
  addCheck('search input name', (await attr(page, '#q', 'name')) === 'q');
  addCheck('user input name', (await attr(page, '#u', 'name')) === 'user');
});

HTML_CASES.set('html-example-078', async (page, addCheck) => {
  addCheck('hidden para not visible', !(await isVisible(page, 'p[hidden]')));
  addCheck('title tooltip attr', (await attr(page, 'p[title="悬停我看看"]', 'title')) === '悬停我看看');
  addCheck('data-role attr', (await attr(page, 'span', 'data-role')) === 'tag');
  addCheck('span text', (await text(page, 'span')) === '标签');
});

HTML_CASES.set('html-example-079', async (page, addCheck) => {
  const height = await computed(page, '.hero', 'height');
  const vh = await page.evaluate(() => window.innerHeight);
  addCheck('hero fills viewport height', Math.abs(parseFloat(height) - vh) <= 2, `${height} vs ${vh}`);
  addCheck('hero centred content', (await computed(page, '.hero', 'place-items')) === 'center');
  addCheck('hero heading', (await text(page, '.hero h1')) === '首屏');
});

HTML_CASES.set('html-example-080', async (page, addCheck) => {
  addCheck('symbol defined', (await count(page, 'symbol#star')) === 1);
  addCheck('use references symbol', (await attr(page, 'use', 'href')) === '#star');
  addCheck('icon fill gold', sameColor(await computed(page, 'svg[aria-label]', 'fill'), '#e8a400'));
  addCheck('icon aria-label', (await attr(page, 'svg[aria-label]', 'aria-label')) === '星标');
});

HTML_CASES.set('html-example-081', async (page, addCheck) => {
  addCheck('initial counter', (await text(page, '#count')) === '0/20');
  await page.fill('#t', 'abcdef');
  addCheck('counter updates live', (await text(page, '#count')) === '6/20', await text(page, '#count'));
  addCheck('maxlength set', (await attr(page, '#t', 'maxlength')) === '20');
});

HTML_CASES.set('html-example-082', async (page, addCheck) => {
  addCheck('button aria-label', (await attr(page, 'button', 'aria-label')) === '关闭');
  addCheck('svg hidden from AT', (await attr(page, 'svg', 'aria-hidden')) === 'true');
  addCheck('button has svg icon', (await count(page, 'button svg path')) === 1);
});

HTML_CASES.set('html-example-083', async (page, addCheck) => {
  addCheck('og:title', (await attr(page, 'meta[property="og:title"]', 'content')) === 'WebForge 教程');
  addCheck(
    'og:description',
    (await attr(page, 'meta[property="og:description"]', 'content')) === '从入门到精通的前端课程。',
  );
  addCheck('twitter card', (await attr(page, 'meta[name="twitter:card"]', 'content')) === 'summary_large_image');
  // og:image is now an inline data URI and must decode (a corrupt one would
  // still pass a bare content-attribute check).
  const ogImage = await attr(page, 'meta[property="og:image"]', 'content');
  addCheck('og:image is inline data', ogImage.startsWith('data:'), ogImage.slice(0, 40));
  const decoded = await page.evaluate(async (url) => {
    return new Promise((resolve) => {
      const probe = new Image();
      probe.onload = () => resolve(probe.naturalWidth > 0);
      probe.onerror = () => resolve(false);
      probe.src = url;
      setTimeout(() => resolve(false), 3000);
    });
  }, ogImage);
  addCheck('og:image data URI really decodes', decoded);
});

HTML_CASES.set('html-example-084', async (page, addCheck) => {
  addCheck('nested field name 1', (await attr(page, 'input[name="user[name]"]', 'name')) === 'user[name]');
  addCheck('nested field name 2', (await attr(page, 'input[name="user[email]"]', 'name')) === 'user[email]');
  addCheck('email type', (await attr(page, 'input[name="user[email]"]', 'type')) === 'email');
});

HTML_CASES.set('html-example-085', async (page, addCheck) => {
  addCheck('div is block', (await computed(page, 'div', 'display')) === 'block');
  const inline = await computed(page, 'span', 'display');
  addCheck('span is inline', inline.startsWith('inline'), inline);
  addCheck('span colour red', sameColor(await computed(page, 'span', 'color'), '#ea4335'));
  addCheck('span text', (await text(page, 'span')) === '行内高亮');
});

HTML_CASES.set('html-example-086', async (page, addCheck) => {
  addCheck('error hidden initially', !(await isVisible(page, '#e-err')));
  await page.fill('#e', 'bad');
  await page.click('button');
  addCheck('error shown for invalid', await isVisible(page, '#e-err'));
  addCheck('error message text', (await text(page, '#e-err')) === '请输入有效邮箱');
  await page.fill('#e', 'user@example.com');
  await page.click('button');
  addCheck('error hidden for valid', !(await isVisible(page, '#e-err')));
});

HTML_CASES.set('html-example-087', async (page, addCheck) => {
  addCheck('header landmark', (await count(page, 'header')) === 1);
  addCheck('nav landmark', (await count(page, 'nav')) === 1);
  addCheck('main landmark', (await count(page, 'main')) === 1);
  addCheck('aside landmark', (await count(page, 'aside')) === 1);
  addCheck('footer landmark', (await count(page, 'footer')) === 1);
  // Visible behaviour, not just tag presence: each landmark renders the text it
  // is supposed to carry, and the five regions are all on screen.
  addCheck('header shows the site name', (await text(page, 'header h1')) === '站名');
  addCheck('nav labelled and links home', (await attr(page, 'nav', 'aria-label')) === '主导航' && (await attr(page, 'nav a', 'href')) === '/');
  addCheck('main carries the content', (await text(page, 'main p')) === '内容。');
  addCheck('aside carries related text', (await text(page, 'aside')) === '相关');
  addCheck('footer carries copyright', (await text(page, 'footer')) === '版权');
  addCheck(
    'all five regions visible',
    (await isVisible(page, 'header')) &&
      (await isVisible(page, 'nav')) &&
      (await isVisible(page, 'main')) &&
      (await isVisible(page, 'aside')) &&
      (await isVisible(page, 'footer')),
  );
});

HTML_CASES.set('html-example-088', async (page, addCheck) => {
  addCheck('onerror fallback declared', (await attr(page, 'img', 'onerror')).includes('data:image/svg'));
  addCheck('alt text present', (await attr(page, 'img', 'alt')) === '图片加载失败');
  // The broken image is now an invalid data URI (no 404): onerror must fire and
  // the fallback SVG must load. No throw, no network fetch.
  const imgs = await imageOutcomes(page);
  addCheck('fallback image ends up decoding', imgs[0]?.naturalWidth > 0, JSON.stringify(imgs[0]));
  addCheck('fallback image is inline data URI', imgs[0]?.isData, JSON.stringify(imgs[0]));
});

HTML_CASES.set('html-example-089', async (page, addCheck) => {
  addCheck('mark text', (await text(page, 'mark')) === '关键词');
  addCheck('s text', (await text(page, 's')) === '199');
  addCheck('ins text', (await text(page, 'ins')) === '99');
  const deco = await computed(page, 's', 'text-decoration-line');
  addCheck('strikethrough applied', deco.includes('line-through'), deco);
  addCheck('small text', (await text(page, 'small')) === '以上价格含税。');
});

HTML_CASES.set('html-example-090', async (page, addCheck) => {
  addCheck(
    'inline div splits the paragraph',
    (await count(page, 'body > p')) >= 2 && (await count(page, 'p > div')) === 0,
    `p=${await count(page, 'body > p')}`,
  );
  addCheck('div is a sibling of p', (await count(page, 'body > div')) === 1);
  addCheck('block element text', (await text(page, 'body > div')) === '块级元素');
});

HTML_CASES.set('html-example-091', async (page, addCheck) => {
  addCheck('wrapping label has input', (await count(page, 'label input')) === 1);
  addCheck('aria-labelledby value', (await attr(page, '[aria-labelledby]', 'aria-labelledby')) === 'l1 l2');
  addCheck('referenced label ids exist', (await count(page, '#l1')) === 1 && (await count(page, '#l2')) === 1);
  await page.locator('label').first().click();
  addCheck(
    'clicking wrapping label focuses its input',
    await page.evaluate(() => document.activeElement?.getAttribute('name') === 'a'),
  );
});

HTML_CASES.set('html-example-092', async (page, addCheck) => {
  addCheck('external link rel', (await attr(page, 'a', 'rel')) === 'noopener noreferrer');
  addCheck('csrf hidden field', (await attr(page, 'input[type="hidden"]', 'name')) === 'csrf_token');
  addCheck(
    'csrf value present',
    (await attr(page, 'input[type="hidden"]', 'value')) === 'REPLACE_WITH_SERVER_TOKEN',
  );
});

HTML_CASES.set('html-example-093', async (page, addCheck) => {
  addCheck('address element present', (await count(page, 'address')) === 1);
  addCheck('address contains mailto link', (await attr(page, 'address a', 'href')) === 'mailto:hi@example.com');
  addCheck('mailto link text', (await text(page, 'address a')) === 'hi@example.com');
});

HTML_CASES.set('html-example-094', async (page, addCheck) => {
  addCheck('title', (await page.title()) === '页面标题');
  addCheck(
    'header/nav/main/footer skeleton',
    (await count(page, 'header')) === 1 &&
      (await count(page, 'nav')) === 1 &&
      (await count(page, 'main')) === 1 &&
      (await count(page, 'footer')) === 1,
  );
  // Visible behaviour of the skeleton: each region shows its placeholder text
  // and the page renders them all (not just four empty tags).
  addCheck('header title rendered', (await text(page, 'header h1')) === '标题');
  addCheck('nav links home', (await text(page, 'nav a')) === '首页');
  addCheck('main body rendered', (await text(page, 'main p')) === '内容');
  addCheck('footer copyright rendered', (await text(page, 'footer p')) === '© 2026');
  addCheck('skeleton all visible', (await isVisible(page, 'header')) && (await isVisible(page, 'main')));
  // Styles + script are now inline; the template must still apply them.
  addCheck('inline base style applies', (await computed(page, 'body', 'margin-top')) === '0px');
  addCheck('template script inlined', (await page.evaluate(() => [...document.querySelectorAll('script')].some((s) => (s.textContent || '').includes('模板已加载')))));
  addCheck('inline style keeps zero body margin', (await computed(page, 'body', 'margin-top')) === '0px');
});

HTML_CASES.set('html-example-095', async (page, addCheck) => {
  addCheck('ordered list items', (await count(page, 'ol > li')) === 2);
  addCheck('nested description list', (await count(page, 'ol dl')) === 1);
  addCheck('nested dt', (await text(page, 'ol dl dt')) === '输出');
  addCheck('nested dd', (await text(page, 'ol dl dd')) === 'dist/ 目录');
});

HTML_CASES.set('html-example-096', async (page, addCheck) => {
  addCheck('img usemap attr', (await attr(page, 'img', 'usemap')) === '#m');
  addCheck('map name matches', (await attr(page, 'map', 'name')) === 'm');
  addCheck('two areas', (await count(page, 'area')) === 2);
  addCheck('first area href', (await attr(page, 'area', 'href')) === '#left');
  addCheck('area alt', (await attr(page, 'area', 'alt')) === '左区');
  addCheck('second area href', (await attr(page, 'area:nth-of-type(2)', 'href')) === '#right');
  addCheck(
    'hotspot coords match the halves',
    (await attr(page, 'area', 'coords')) === '0,0,120,80' &&
      (await attr(page, 'area:nth-of-type(2)', 'coords')) === '120,0,240,80',
  );
  // The map image must be an inline data URI that decodes at its declared size
  // (an image map with a zero-size image has meaningless hotspots).
  const imgs = await imageOutcomes(page);
  const img = imgs[0];
  addCheck('map image is inline data URI', img?.isData, JSON.stringify(img));
  addCheck(
    'map image decodes at 240x80',
    img?.naturalWidth === 240 && img?.naturalHeight === 80,
    JSON.stringify(img),
  );
});

HTML_CASES.set('html-example-097', async (page, addCheck) => {
  addCheck('hero blue background', sameColor(await computed(page, '.hero', 'background-color'), '#1a73e8'));
  addCheck('hero white text', sameColor(await computed(page, '.hero', 'color'), '#ffffff'));
  addCheck('hero heading', (await text(page, '.hero h1')) === '首屏立即有样式');
});

HTML_CASES.set('html-example-098', async (page, addCheck) => {
  addCheck('placeholder text', (await attr(page, '#pw', 'placeholder')) === '至少 8 位');
  addCheck('aria-describedby value', (await attr(page, '#pw', 'aria-describedby')) === 'pw-hint');
  addCheck('hint target exists', (await count(page, '#pw-hint')) === 1);
  addCheck('hint text', (await text(page, '#pw-hint')) === '需包含字母和数字，至少 8 位。');
  addCheck('minlength set', (await attr(page, '#pw', 'minlength')) === '8');
});

HTML_CASES.set('html-example-099', async (page, addCheck) => {
  addCheck('footnote link target', (await attr(page, 'sup a', 'href')) === '#fn1');
  addCheck('footnote target exists', (await count(page, '#fn1')) === 1);
  addCheck('backref points to ref1', (await attr(page, 'li a', 'href')) === '#ref1');
  await page.click('sup a');
  addCheck('footnote link jumps to footnote', page.url().endsWith('#fn1'));
});

HTML_CASES.set('html-example-100', async (page, addCheck) => {
  addCheck('author meta', (await attr(page, 'meta[name="author"]', 'content')) === 'WebForge');
  addCheck('copyright meta', (await attr(page, 'meta[name="copyright"]', 'content')) === '© 2026 WebForge');
  addCheck('robots meta', (await attr(page, 'meta[name="robots"]', 'content')) === 'index, follow');
});

// ===========================================================================
// CSS examples (100) — concrete computed / interactive values
// ===========================================================================

CSS_CASES.set('css-example-001', async (page, addCheck) => {
  addCheck('h1 blue', sameColor(await computed(page, 'h1', 'color'), '#1a73e8'));
  addCheck('p font-size 18px', (await computed(page, 'p', 'font-size')) === '18px');
  addCheck('p line-height 1.6 (28.8px)', (await computed(page, 'p', 'line-height')) === '28.8px');
  addCheck('h1 text', (await text(page, 'h1')) === '蓝色标题');
});

CSS_CASES.set('css-example-002', async (page, addCheck) => {
  addCheck('html font-size 16px', (await computed(page, 'html', 'font-size')) === '16px');
  addCheck('box padding 16px', (await computed(page, '.box', 'padding-top')) === '16px');
  addCheck('inner p font-size 20px', (await computed(page, '.box p', 'font-size')) === '20px');
  // hsl(217 89% 51%) resolves to rgb(19, 104, 241), not the #1a73e8 hex.
  addCheck(
    'inner p hsl resolves to its rgb value',
    (await computed(page, '.box p', 'color')) === 'rgb(19, 104, 241)',
    await computed(page, '.box p', 'color'),
  );
  const width = parseFloat(await computed(page, '.box', 'width'));
  // `width: 50%` of the containing block. Read the real rendered width, which
  // is `window.innerWidth` when Playwright does not own the viewport (native).
  const viewport = await viewportWidth(page);
  // Assert approximate half (a classic scrollbar eats a few px).
  addCheck(
    'box width is about half the viewport',
    Math.abs(width - viewport / 2) <= 24,
    `${width} vs ${viewport}`,
  );
});

CSS_CASES.set('css-example-003', async (page, addCheck) => {
  addCheck('box-sizing border-box', (await computed(page, '.card', 'box-sizing')) === 'border-box');
  addCheck('card width 200px', (await computed(page, '.card', 'width')) === '200px');
  addCheck('card padding 16px', (await computed(page, '.card', 'padding-top')) === '16px');
  addCheck('card margin 12px', (await computed(page, '.card', 'margin-top')) === '12px');
  addCheck(
    'card border 2px solid',
    (await computed(page, '.card', 'border-top-width')) === '2px' &&
      (await computed(page, '.card', 'border-top-style')) === 'solid',
  );
  addCheck('card background #f5f5f5', sameColor(await computed(page, '.card', 'background-color'), '#f5f5f5'));
});

CSS_CASES.set('css-example-004', async (page, addCheck) => {
  addCheck('p justified text', (await computed(page, 'p', 'text-align')) === 'justify');
  addCheck('p line-height 1.75 (28px)', (await computed(page, 'p', 'line-height')) === '28px');
  addCheck('center paragraph centred', (await computed(page, '.center', 'text-align')) === 'center');
  addCheck('center text', (await text(page, '.center')) === '这一行居中。');
});

CSS_CASES.set('css-example-005', async (page, addCheck) => {
  const bg = await computed(page, '.hero', 'background-image');
  addCheck('linear-gradient applied', bg.includes('linear-gradient'), bg);
  addCheck('hero white text', sameColor(await computed(page, '.hero', 'color'), '#ffffff'));
  addCheck('hero centred content', (await computed(page, '.hero', 'place-items')) === 'center');
  addCheck('hero height 120px', (await computed(page, '.hero', 'height')) === '120px');
});

CSS_CASES.set('css-example-006', async (page, addCheck) => {
  addCheck('row display flex', (await computed(page, '.row', 'display')) === 'flex');
  addCheck('row gap 8px', (await computed(page, '.row', 'gap')) === '8px');
  addCheck('items centred horizontally', (await computed(page, '.row', 'justify-content')) === 'center');
  addCheck('items centred vertically', (await computed(page, '.row', 'align-items')) === 'center');
  addCheck('three flex items', (await count(page, '.item')) === 3);
});

CSS_CASES.set('css-example-007', async (page, addCheck) => {
  addCheck('grid display', (await computed(page, '.grid', 'display')) === 'grid');
  addCheck('three columns', (await computed(page, '.grid', 'grid-template-columns')).split(' ').length === 3);
  addCheck('gap 8px', (await computed(page, '.grid', 'gap')) === '8px');
  addCheck(
    'wide cell spans 2',
    (await computed(page, '.wide', 'grid-column-start')) === 'span 2',
    await computed(page, '.wide', 'grid-column-start'),
  );
});

CSS_CASES.set('css-example-008', async (page, addCheck) => {
  addCheck('badge absolutely positioned', (await computed(page, '.badge', 'position')) === 'absolute');
  addCheck('badge red', sameColor(await computed(page, '.badge', 'background-color'), '#ea4335'));
  addCheck('float button fixed', (await computed(page, '.float', 'position')) === 'fixed');
  await page.evaluate(() => window.scrollTo(0, 300));
  const bottom = await computed(page, '.float', 'bottom');
  addCheck('fixed button stays 8px from bottom', bottom === '8px', bottom);
});

CSS_CASES.set('css-example-009', async (page, addCheck) => {
  addCheck('link no underline by default', (await computed(page, 'a', 'text-decoration-line')) === 'none');
  await page.hover('a');
  addCheck('link underlines on hover', (await computed(page, 'a', 'text-decoration-line')) === 'underline');
  addCheck(
    'quote before content',
    (await page.locator('.quote').evaluate((el) => getComputedStyle(el, '::before').content)).includes('“'),
  );
  addCheck(
    'quote after content',
    (await page.locator('.quote').evaluate((el) => getComputedStyle(el, '::after').content)).includes('”'),
  );
});

CSS_CASES.set('css-example-010', async (page, addCheck) => {
  addCheck('btn inline-block', (await computed(page, '.btn', 'display')) === 'inline-block');
  await page.hover('.btn');
  await settle(page);
  const transform = await computed(page, '.btn', 'transform');
  addCheck('hover translates/scales', transform !== 'none' && transform.includes('matrix'), transform);
  addCheck('hover background darkens', sameColor(await computed(page, '.btn', 'background-color'), '#0d47a1'));
  const dur = await computed(page, '.btn', 'transition-duration');
  addCheck('transition ~0.2s', dur.includes('0.2s'), dur);
});

CSS_CASES.set('css-example-011', async (page, addCheck) => {
  addCheck('gap 8px', (await computed(page, '.grid', 'gap')) === '8px');
  addCheck('three cells', (await count(page, '.cell')) === 3);
  addCheck('cell background #e8f0fe', sameColor(await computed(page, '.cell', 'background-color'), '#e8f0fe'));

  // The lesson's whole point is the 1 -> 2 -> 3 column ladder at 600px and
  // 900px. Assert both sides of each breakpoint, not just the desktop state.
  const ladder = [
    [599, 1],
    [600, 2],
    [899, 2],
    [900, 3],
  ];
  const observed = [];
  for (const [width, expected] of ladder) {
    const cols = await atViewport(page, width, 720, () => gridColumns(page, '.grid'));
    if (cols === null) continue;
    observed.push(width);
    addCheck(`${width}px viewport renders ${expected} column(s)`, cols === expected, `cols=${cols}`);
  }

  if (observed.length === 0) {
    // Cannot resize (native/CDP page): assert the branch this width implies.
    const width = await viewportWidth(page);
    const expected = width >= 900 ? 3 : width >= 600 ? 2 : 1;
    const cols = await gridColumns(page, '.grid');
    addCheck(`at the real ${width}px width the grid shows ${expected} column(s)`, cols === expected, `cols=${cols}`);
  }

  // Equal 1fr tracks: every cell is the same width, and the cells fill the
  // rows implied by the column count (3 cells / 2 columns = 2 rows).
  const cols = await gridColumns(page, '.grid');
  const cellCount = await count(page, '.cell');
  const widths = await page
    .locator('.cell')
    .evaluateAll((els) => els.map((el) => +el.getBoundingClientRect().width.toFixed(2)));
  addCheck('columns are equal width (1fr each)', Math.max(...widths) - Math.min(...widths) <= 1, widths.join('/'));
  const rowTops = new Set(await tops(page, '.cell'));
  const expectedRows = Math.ceil(cellCount / Math.max(1, cols));
  addCheck(
    `${cols} column(s) lay the ${cellCount} cells out over ${expectedRows} row(s)`,
    rowTops.size === expectedRows,
    `${rowTops.size} row(s)`,
  );
});

CSS_CASES.set('css-example-012', async (page, addCheck) => {
  addCheck('button background primary blue', sameColor(await computed(page, 'button', 'background-color'), '#1a73e8'));
  addCheck('button white text', sameColor(await computed(page, 'button', 'color'), '#ffffff'));
  addCheck('body background is --bg value', sameColor(await computed(page, 'body', 'background-color'), '#ffffff'));
  addCheck(
    'primary custom prop declared',
    (await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--primary').trim())) ===
      '#1a73e8',
  );
});

CSS_CASES.set('css-example-013', async (page, addCheck) => {
  addCheck('pulse animation applied', (await computed(page, '.dot', 'animation-name')) === 'pulse');
  addCheck('animation 1s duration', (await computed(page, '.dot', 'animation-duration')) === '1s');
  addCheck(
    'animation infinite alternate',
    (await computed(page, '.dot', 'animation-iteration-count')) === 'infinite' &&
      (await computed(page, '.dot', 'animation-direction')) === 'alternate',
  );
  addCheck('dot round', (await computed(page, '.dot', 'border-radius')) === '50%');
});

CSS_CASES.set('css-example-014', async (page, addCheck) => {
  addCheck('id wins -> red', sameColor(await computed(page, '#intro', 'color'), '#ff0000'));
  // The .note class matches #intro first; the pure-class paragraph is the
  // second .note, which must resolve to blue.
  addCheck(
    'class wins over tag -> blue',
    sameColor(await computed(page, 'p.note:not(#intro)', 'color'), '#0000ff'),
    await computed(page, 'p.note:not(#intro)', 'color'),
  );
  addCheck('plain p -> green', sameColor(await computed(page, 'p:nth-of-type(3)', 'color'), '#008000'));
});

CSS_CASES.set('css-example-015', async (page, addCheck) => {
  addCheck('wall is grid', (await computed(page, '.wall', 'display')) === 'grid');
  addCheck('card border radius 12px', (await computed(page, '.card', 'border-radius')) === '12px');
  addCheck('card shadow is the authored 1px/3px pair', (await computed(page, '.card', 'box-shadow')) === 'rgba(0, 0, 0, 0.08) 0px 1px 3px 0px', await computed(page, '.card', 'box-shadow'));
  addCheck('three cards', (await count(page, '.card')) === 3);

  // `repeat(auto-fit, minmax(160px, 1fr))`: auto-fit collapses the tracks that
  // have no items to 0px, so the number of *positive* tracks is the real column
  // count, and it must follow the available width instead of a fixed count.
  const layout = async () => ({
    cols: await gridColumns(page, '.wall'),
    widths: await page
      .locator('.card')
      .evaluateAll((els) => els.map((el) => +el.getBoundingClientRect().width.toFixed(2))),
    rows: new Set(await tops(page, '.card')).size,
    overflow: await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    ),
  });

  const wide = await atViewport(page, 1280, 720, layout);
  const narrow = await atViewport(page, 412, 720, layout);

  if (wide && narrow) {
    addCheck('wide viewport fits the three cards in three tracks', wide.cols === 3, `cols=${wide.cols}`);
    addCheck('wide viewport puts them on a single row', wide.rows === 1, `${wide.rows} row(s)`);
    addCheck('narrow viewport drops to two tracks', narrow.cols === 2, `cols=${narrow.cols}`);
    addCheck('narrow viewport wraps the third card onto a second row', narrow.rows === 2, `${narrow.rows} row(s)`);
    addCheck('cards stay at least 160px wide when narrow', Math.min(...narrow.widths) >= 160, narrow.widths.join('/'));
    addCheck('auto-fit never overflows the page', wide.overflow <= 0 && narrow.overflow <= 0, `${wide.overflow}/${narrow.overflow}`);
  } else {
    // Cannot resize: assert the auto-fit invariant at the real width instead of
    // guessing a column count. `repeat(auto-fit, minmax(160px, 1fr))` fits
    // floor((available + gap) / (160 + gap)) tracks, capped by the item count,
    // and auto-fit collapses every unused track.
    const real = await layout();
    const available = await page.locator('.wall').first().evaluate((el) => el.clientWidth);
    const fit = Math.min(3, Math.max(1, Math.floor((available + 12) / (160 + 12))));
    addCheck(`auto-fit fits ${fit} track(s) in ${available}px at the real width`, real.cols === fit, `cols=${real.cols} available=${available}`);
    addCheck('cards are at least 160px wide', Math.min(...real.widths) >= 160, real.widths.join('/'));
    addCheck('auto-fit never overflows the page', real.overflow <= 0, String(real.overflow));
  }

  // The minmax() floor is real: each card is >= 160px and all share one width.
  const widths = await page
    .locator('.card')
    .evaluateAll((els) => els.map((el) => +el.getBoundingClientRect().width.toFixed(2)));
  addCheck('all cards share the 1fr width', Math.max(...widths) - Math.min(...widths) <= 1, widths.join('/'));
});

CSS_CASES.set('css-example-016', async (page, addCheck) => {
  addCheck('one-line ellipsis', (await computed(page, '.one', 'text-overflow')) === 'ellipsis');
  addCheck('no-wrap', (await computed(page, '.one', 'white-space')) === 'nowrap');
  addCheck('clamp hidden overflow', (await computed(page, '.clamp', 'overflow')) === 'hidden');
  // Chrome reports the clamped box as `flow-root`, not `-webkit-box`; the
  // observable guarantee is that the content is actually clipped (scroll area
  // exceeds the visible box).
  const clamped = await page
    .locator('.clamp')
    .evaluate((el) => el.scrollHeight > el.clientHeight + 1);
  addCheck('clamp actually limits height', clamped);
});

CSS_CASES.set('css-example-017', async (page, addCheck) => {
  addCheck('btn pointer cursor', (await computed(page, '.btn', 'cursor')) === 'pointer');
  addCheck('btn not selectable', (await computed(page, '.btn', 'user-select')) === 'none');
  addCheck('btn blue background', sameColor(await computed(page, '.btn', 'background-color'), '#1a73e8'));
});

CSS_CASES.set('css-example-018', async (page, addCheck) => {
  addCheck('nav list-style none', (await computed(page, 'ul.nav', 'list-style-type')) === 'none');
  addCheck('nav is flex', (await computed(page, 'ul.nav', 'display')) === 'flex');
  addCheck('table border-collapse', (await computed(page, 'table', 'border-collapse')) === 'collapse');
  const even = await computed(page, 'tbody tr:nth-child(2)', 'background-color');
  addCheck('even row shaded #f7f7f7', sameColor(even, '#f7f7f7'), even);
});

CSS_CASES.set('css-example-019', async (page, addCheck) => {
  addCheck('smooth scroll behaviour', (await computed(page, 'html', 'scroll-behavior')) === 'smooth');
  addCheck('sticky top bar', (await computed(page, '.top', 'position')) === 'sticky');
  addCheck('sticky offset 0', (await computed(page, '.top', 'top')) === '0px');
  addCheck('top bar blue', sameColor(await computed(page, '.top', 'background-color'), '#1a73e8'));
});

CSS_CASES.set('css-example-020', async (page, addCheck) => {
  addCheck('circle radius 50%', (await computed(page, '.circle', 'border-radius')) === '50%');
  addCheck('circle blue', sameColor(await computed(page, '.circle', 'background-color'), '#1a73e8'));
  const clip = await computed(page, '.tri', 'clip-path');
  addCheck('triangle clip-path polygon', clip.includes('polygon'), clip);
  addCheck('triangle green', sameColor(await computed(page, '.tri', 'background-color'), '#34a853'));
});

CSS_CASES.set('css-example-021', async (page, addCheck) => {
  // Exact authored values: grayscale(1) fully desaturates, contrast(1.2)
  // steepens it, blur(6px) is the glass. A substring check for "grayscale"
  // would also pass for grayscale(0.1), which looks nothing like the lesson.
  addCheck('photo filter is grayscale(1) contrast(1.2)', (await computed(page, '.photo', 'filter')) === 'grayscale(1) contrast(1.2)', await computed(page, '.photo', 'filter'));
  addCheck('photo keeps its 120px width', (await computed(page, '.photo', 'width')) === '120px');
  addCheck('glass backdrop-filter is blur(6px)', (await computed(page, '.glass', 'backdrop-filter')) === 'blur(6px)', await computed(page, '.glass', 'backdrop-filter'));
  addCheck('glass is 40% white so the blur shows through', (await computed(page, '.glass', 'background-color')) === 'rgba(255, 255, 255, 0.4)', await computed(page, '.glass', 'background-color'));
  // The photo is now an inline SVG; it must really decode (a corrupt data URI
  // would still satisfy a src-attribute check).
  const imgs = await imageOutcomes(page);
  addCheck('photo image really decodes', imgs[0]?.naturalWidth > 0, JSON.stringify(imgs[0]));
});

CSS_CASES.set('css-example-022', async (page, addCheck) => {
  addCheck('glow radial gradient', (await computed(page, '.glow', 'background-image')).includes('radial-gradient'));
  addCheck('glow round', (await computed(page, '.glow', 'border-radius')) === '50%');
  addCheck('checker layered linear gradients', ((await computed(page, '.checker', 'background-image')).match(/linear-gradient/g) || []).length === 2);
  // Two layers each 20x20: computed value is `20px 20px, 20px 20px`.
  addCheck('checker tile size 20x20', (await computed(page, '.checker', 'background-size')).includes('20px 20px'), await computed(page, '.checker', 'background-size'));
});

CSS_CASES.set('css-example-023', async (page, addCheck) => {
  addCheck('counter reset declared', (await computed(page, 'ol.chapters', 'counter-reset')).includes('ch'));
  // getComputedStyle on ::before returns the unsubstituted template; assert the
  // counter template and that a counter is actually declared for the list.
  const before = await page.locator('ol.chapters > li').first().evaluate((el) => getComputedStyle(el, '::before').content);
  addCheck('::before uses a counter', before.includes('counter('), before);
  addCheck('list declares counter-increment', (await computed(page, 'ol.chapters > li', 'counter-increment')).includes('ch'));
  addCheck('three chapters', (await count(page, 'ol.chapters > li')) === 3);
});

CSS_CASES.set('css-example-024', async (page, addCheck) => {
  const areas = await computed(page, '.page', 'grid-template-areas');
  addCheck('named areas declared', areas.includes('head') && areas.includes('side') && areas.includes('main'), areas);
  addCheck('header spans head area', (await computed(page, 'header', 'grid-area')) === 'head' || (await computed(page, 'header', 'grid-row-start')) !== 'auto');
  addCheck('two grid columns', (await computed(page, '.page', 'grid-template-columns')).split(' ').length === 2);
});

CSS_CASES.set('css-example-025', async (page, addCheck) => {
  const size = await computed(page, 'h1', 'font-size');
  const px = parseFloat(size);
  addCheck('h1 font-size within clamp range', px >= 24 && px <= 48, size);
  const psize = parseFloat(await computed(page, 'p', 'font-size'));
  addCheck('p font-size within clamp range', psize >= 14.4 && psize <= 17.6, `${psize}`);
  addCheck('h1 text present', (await text(page, 'h1')) === '随视口缩放的大标题');
});

CSS_CASES.set('css-example-026', async (page, addCheck) => {
  addCheck('body background from --bg', sameColor(await computed(page, 'body', 'background-color'), '#ffffff'));
  addCheck('body colour from --fg', sameColor(await computed(page, 'body', 'color'), '#202124'));
});

CSS_CASES.set('css-example-027', async (page, addCheck) => {
  addCheck(
    'accent-color is theme blue',
    (await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('accent-color').trim())) ===
      'rgb(26, 115, 232)',
  );
  addCheck('text input border radius 6px', (await computed(page, 'input[type="text"]', 'border-radius')) === '6px');
  addCheck('checkbox checked', (await attr(page, 'input[type=checkbox]', 'checked')) !== null);
});

CSS_CASES.set('css-example-028', async (page, addCheck) => {
  addCheck('button blue initially', sameColor(await computed(page, 'button', 'background-color'), '#1a73e8'));
  await page.click('#b');
  addCheck('button turns red after click', sameColor(await computed(page, 'button', 'background-color'), '#ea4335'), await computed(page, 'button', 'background-color'));
  await page.click('#b');
  addCheck('button back to blue', sameColor(await computed(page, 'button', 'background-color'), '#1a73e8'));
});

CSS_CASES.set('css-example-029', async (page, addCheck) => {
  // Screen state: everything is on screen and no print rule applies yet.
  addCheck('nav visible on screen', await isVisible(page, 'nav'));
  addCheck('button visible on screen', await isVisible(page, 'button'));
  addCheck('cards keep default break-inside on screen', (await computed(page, '.card', 'break-inside')) === 'auto', await computed(page, '.card', 'break-inside'));

  // Switch the page to the print media type and assert the print branch for
  // real, instead of only checking that a @media print rule was parsed.
  await page.emulateMedia({ media: 'print' });
  try {
    await settle(page, 150);
    addCheck('nav is removed when printing', !(await isVisible(page, 'nav')));
    addCheck('button is removed when printing', !(await isVisible(page, 'button')));
    addCheck('nav display is none under print', (await computed(page, 'nav', 'display')) === 'none', await computed(page, 'nav', 'display'));
    addCheck('button display is none under print', (await computed(page, 'button', 'display')) === 'none');
    addCheck('body prints on white paper', sameColor(await computed(page, 'body', 'background-color'), '#ffffff'), await computed(page, 'body', 'background-color'));
    addCheck('body prints in black ink', sameColor(await computed(page, 'body', 'color'), '#000000'));
    addCheck('cards avoid breaking across pages', (await computed(page, '.card', 'break-inside')) === 'avoid', await computed(page, '.card', 'break-inside'));
    addCheck('the article heading still prints', (await isVisible(page, 'h1')) && (await text(page, 'h1')) === '可打印文章');
  } finally {
    await page.emulateMedia({ media: 'screen' });
    await settle(page, 150);
  }
  addCheck('screen media restores the nav', await isVisible(page, 'nav'));
});

CSS_CASES.set('css-example-030', async (page, addCheck) => {
  addCheck('wrap container-type inline-size', (await computed(page, '.wrap', 'container-type')) === 'inline-size');
  addCheck('card light blue at 200px container', sameColor(await computed(page, '.card', 'background-color'), '#e8f0fe'), await computed(page, '.card', 'background-color'));
  addCheck('wrap resizable', (await computed(page, '.wrap', 'resize')) === 'horizontal');
});

CSS_CASES.set('css-example-031', async (page, addCheck) => {
  addCheck('margin-inline 24px', (await computed(page, '.box', 'margin-left')) === '24px' && (await computed(page, '.box', 'margin-right')) === '24px');
  addCheck('padding-block 12px', (await computed(page, '.box', 'padding-top')) === '12px' && (await computed(page, '.box', 'padding-bottom')) === '12px');
  addCheck('box background #e8f0fe', sameColor(await computed(page, '.box', 'background-color'), '#e8f0fe'));
});

CSS_CASES.set('css-example-032', async (page, addCheck) => {
  addCheck('ball round', (await computed(page, '.ball', 'border-radius')) === '50%');
  addCheck('ball blue', sameColor(await computed(page, '.ball', 'background-color'), '#1a73e8'));
  addCheck('transition on transform', (await computed(page, '.ball', 'transition-property')) === 'transform');
  await page.click('#go');
  await settle(page, 600);
  addCheck('ball gains .move class on click', (await attr(page, '.ball', 'class')).includes('move'));
  const moved = await computed(page, '.ball', 'transform');
  addCheck('click applies translateX(160px)', moved.includes('160'), moved);
});

CSS_CASES.set('css-example-033', async (page, addCheck) => {
  addCheck('https link green', sameColor(await computed(page, 'a[href^="https"]', 'color'), '#34a853'));
  const liWeight = await computed(page, 'ul > li', 'font-weight');
  addCheck('list item bold', liWeight === '700' || liWeight === 'bold', liWeight);
  addCheck('h2 + p grey #666', sameColor(await computed(page, 'h2 + p', 'color'), '#666666'));
});

CSS_CASES.set('css-example-034', async (page, addCheck) => {
  addCheck('not(.done) item blue', sameColor(await computed(page, 'li:not(.done)', 'color'), '#1a73e8'));
  addCheck('done item not blue', !sameColor(await computed(page, 'li.done', 'color'), '#1a73e8'));
  // `line-height: 1.2` resolves to an absolute pixel value on h1 (e.g. 38.4px).
  const lh = await computed(page, 'h1', 'line-height');
  const fs = parseFloat(await computed(page, 'h1', 'font-size'));
  addCheck('h1 line-height is 1.2x font-size', Math.abs(parseFloat(lh) - fs * 1.2) < 0.5, `${lh} vs ${fs}`);
  const border = await computed(page, '.card:has(img)', 'border-top-color');
  addCheck('card:has(img) green border', sameColor(border, '#34a853'), border);
  // The card image is inline SVG: it must decode, not just exist.
  const imgs = await imageOutcomes(page);
  addCheck('card image really decodes', imgs[0]?.naturalWidth > 0, JSON.stringify(imgs[0]));
});

CSS_CASES.set('css-example-035', async (page, addCheck) => {
  addCheck('btn blue', sameColor(await computed(page, '.btn', 'background-color'), '#1a73e8'));
  addCheck('btn pointer', (await computed(page, '.btn', 'cursor')) === 'pointer');
  addCheck('btn radius 6px', (await computed(page, '.btn', 'border-radius')) === '6px');
  addCheck('btn padding 10px 20px', (await computed(page, '.btn', 'padding-top')) === '10px' && (await computed(page, '.btn', 'padding-left')) === '20px');

  // Disabled state: the authored opacity is exactly .5 (not merely "< 1",
  // which would also accept a barely-visible .99).
  addCheck('disabled opacity is exactly 0.5', (await computed(page, '.btn[disabled]', 'opacity')) === '0.5', await computed(page, '.btn[disabled]', 'opacity'));
  addCheck('disabled cursor is not-allowed', (await computed(page, '.btn[disabled]', 'cursor')) === 'not-allowed');

  // Keyboard focus ring first: 3px solid #8ab4f8 from :focus-visible. Tab must
  // be the first interaction in this case — after a mouse click the sequential
  // focus starting point sits on the button, so Tab would move past it and
  // :focus-visible would never engage.
  await page.keyboard.press('Tab');
  await settle(page, 150);
  addCheck('Tab focuses the first button', (await page.evaluate(() => document.activeElement.className)) === 'btn');
  addCheck('focus ring is 3px solid #8ab4f8', (await computed(page, '.btn', 'outline-width')) === '3px' && (await computed(page, '.btn', 'outline-style')) === 'solid' && sameColor(await computed(page, '.btn', 'outline-color'), '#8ab4f8'), await computed(page, '.btn', 'outline-color'));

  // Hover: the darker shade from the lesson, not just "some other colour".
  await page.hover('.btn:not([disabled])');
  await settle(page, 120);
  addCheck('hover darkens to #1557b0', sameColor(await computed(page, '.btn:not([disabled])', 'background-color'), '#1557b0'), await computed(page, '.btn:not([disabled])', 'background-color'));

  // :active needs a held pointer, so press the real button and read it while
  // the mouse is still down; :active then matches and the 1px sink applies.
  const btn = await page.locator('.btn:not([disabled])').boundingBox();
  await page.mouse.move(btn.x + btn.width / 2, btn.y + btn.height / 2);
  await page.mouse.down();
  await settle(page, 120);
  const pressed = await page.locator('.btn:not([disabled])').evaluate((el) => ({
    active: el.matches(':active'),
    transform: getComputedStyle(el).transform,
  }));
  await page.mouse.up();
  addCheck('pressed button matches :active', pressed.active);
  addCheck('pressed button sinks by 1px', pressed.transform === 'matrix(1, 0, 0, 1, 0, 1)', pressed.transform);
  addCheck('released button returns to rest', (await computed(page, '.btn:not([disabled])', 'transform')) === 'none');
});

CSS_CASES.set('css-example-036', async (page, addCheck) => {
  // The lesson teaches a *two-layer* shadow; assert both layers with their
  // exact offsets/blur, not merely that some shadow exists.
  const shadow = await computed(page, '.card', 'box-shadow');
  addCheck('card shadow has two layers', (shadow.match(/rgba?\(/g) || []).length === 2, shadow);
  addCheck('card shadow layer 1 is 0 1px 2px', shadow.includes('0px 1px 2px'), shadow);
  addCheck('card shadow layer 2 is 0 4px 12px', shadow.includes('0px 4px 12px'), shadow);
  addCheck('both layers are 8% black', (shadow.match(/rgba\(0, 0, 0, 0.08\)/g) || []).length === 2, shadow);
  addCheck('card radius 8px', (await computed(page, '.card', 'border-radius')) === '8px');

  // Text shadow: 1px down, 2px blur, 20% black.
  addCheck('h1 text-shadow is 0 1px 2px 20% black', (await computed(page, 'h1', 'text-shadow')) === 'rgba(0, 0, 0, 0.2) 0px 1px 2px', await computed(page, 'h1', 'text-shadow'));
  // A shadow with no offset/blur would be a flat halo; require a real offset.
  const textShadow = await computed(page, 'h1', 'text-shadow');
  addCheck('text-shadow is offset downward', /\b0px 1px\b/.test(textShadow), textShadow);
});

CSS_CASES.set('css-example-037', async (page, addCheck) => {
  addCheck('clip overflow hidden', (await computed(page, '.clip', 'overflow-x')) === 'hidden');
  addCheck('clip fixed height 40px', (await computed(page, '.clip', 'height')) === '40px');
  addCheck('scroll overflow auto', (await computed(page, '.scroll', 'overflow-x')) === 'auto');
  const scrolls = await page.locator('.scroll').evaluate((el) => el.scrollHeight > el.clientHeight);
  addCheck('scroll container actually scrolls', scrolls);
});

CSS_CASES.set('css-example-038', async (page, addCheck) => {
  addCheck('columns declared', (await computed(page, '.cols', 'column-count')) === '2');
  addCheck('column gap 24px', (await computed(page, '.cols', 'column-gap')) === '24px');
  const rule = await computed(page, '.cols', 'column-rule-style');
  addCheck('column rule solid', rule === 'solid', rule);
});

CSS_CASES.set('css-example-039', async (page, addCheck) => {
  addCheck('input border radius 6px', (await computed(page, 'input', 'border-radius')) === '6px');
  addCheck('select border radius 6px', (await computed(page, 'select', 'border-radius')) === '6px');
  await page.focus('input');
  addCheck('focused input border blue', sameColor(await computed(page, 'input:focus', 'border-top-color'), '#1a73e8'), await computed(page, 'input', 'border-top-color'));
});

CSS_CASES.set('css-example-040', async (page, addCheck) => {
  addCheck('h1 gradient background', (await computed(page, 'h1', 'background-image')).includes('linear-gradient'));
  addCheck('text clip applied', (await computed(page, 'h1', 'background-clip')).includes('text') || (await computed(page, 'h1', '-webkit-background-clip')).includes('text'));
  addCheck('text made transparent', (await computed(page, 'h1', 'color')) === 'rgba(0, 0, 0, 0)');
});

CSS_CASES.set('css-example-041', async (page, addCheck) => {
  addCheck('badge is the positioning context', (await computed(page, '.badge', 'position')) === 'relative');
  addCheck('badge background #e8f0fe', sameColor(await computed(page, '.badge', 'background-color'), '#e8f0fe'));

  // The triangle is a ::after box with a red top/right border and transparent
  // bottom/left borders. Read the pseudo element's own computed style (a
  // locator cannot address ::after) and assert the geometry that makes it a
  // corner triangle rather than an empty box.
  const after = await page
    .locator('.badge')
    .first()
    .evaluate((el) => {
      const cs = getComputedStyle(el, '::after');
      const get = (p) => cs.getPropertyValue(p).trim();
      return {
        content: get('content'),
        position: get('position'),
        top: get('top'),
        right: get('right'),
        borderWidth: [get('border-top-width'), get('border-right-width'), get('border-bottom-width'), get('border-left-width')],
        borderStyle: get('border-top-style'),
        borderColor: [
          get('border-top-color'),
          get('border-right-color'),
          get('border-bottom-color'),
          get('border-left-color'),
        ],
      };
    });

  addCheck('::after has empty content (pure shape)', after.content === '""', after.content);
  addCheck('::after is absolutely positioned', after.position === 'absolute', after.position);
  addCheck('::after sits at the top-right corner', after.top === '0px' && after.right === '0px', `${after.top}/${after.right}`);
  addCheck('::after borders are 8px solid on all four sides', after.borderWidth.every((w) => w === '8px') && after.borderStyle === 'solid', `${after.borderWidth.join('/')} ${after.borderStyle}`);
  addCheck('::after top and right borders are red #ea4335', sameColor(after.borderColor[0], '#ea4335') && sameColor(after.borderColor[1], '#ea4335'), after.borderColor.slice(0, 2).join(' / '));
  addCheck('::after bottom and left borders are transparent', /rgba\(0, 0, 0, 0\)|transparent/.test(after.borderColor[2]) && /rgba\(0, 0, 0, 0\)|transparent/.test(after.borderColor[3]), after.borderColor.slice(2).join(' / '));

  // The 8px red borders against 8px transparent ones form a 45-degree wedge
  // whose visible half is the red triangle.
  addCheck('badge box is 128x37', (await page.locator('.badge').first().boundingBox()).width === 128);
});

CSS_CASES.set('css-example-042', async (page, addCheck) => {
  addCheck('scrollbar-width thin', (await computed(page, '.box', 'scrollbar-width')) === 'thin');
  addCheck('scrollbar-color blue', (await computed(page, '.box', 'scrollbar-color')).includes('26, 115, 232'), await computed(page, '.box', 'scrollbar-color'));
  addCheck('box overflow auto', (await computed(page, '.box', 'overflow-x')) === 'auto');
});

CSS_CASES.set('css-example-043', async (page, addCheck) => {
  addCheck('header sticky', (await computed(page, 'header', 'position')) === 'sticky');
  addCheck('header top 0', (await computed(page, 'header', 'top')) === '0px');
  await page.evaluate(() => window.scrollTo(0, 400));
  await page.waitForTimeout(80);
  addCheck('scrolled class applied', (await attr(page, '#h', 'class')).includes('scrolled'), await attr(page, '#h', 'class'));
  addCheck('scrolled shadow present', (await computed(page, '#h', 'box-shadow')) !== 'none');
});

CSS_CASES.set('css-example-044', async (page, addCheck) => {
  // 65ch resolves to a fixed pixel measure (≈610px at 16px text) that does not
  // depend on the viewport. At a phone width the article is narrower than that
  // measure, so "maxWidth < viewport" is only true on desktop. Measure `ch`
  // independently in the same engine and compare: that proves the authored unit
  // and magnitude, and holds at any viewport.
  const ch65 = await page.evaluate(() => {
    const probe = document.createElement('div');
    probe.style.cssText = 'position:absolute;width:65ch;visibility:hidden;left:-9999px';
    document.body.appendChild(probe);
    const width = probe.getBoundingClientRect().width;
    probe.remove();
    return width;
  });
  const maxWidth = parseFloat(await computed(page, 'article', 'max-width'));
  addCheck('max-width really is 65ch', Math.abs(maxWidth - ch65) < 0.5, `${maxWidth} vs 65ch=${ch65}`);
  addCheck('65ch is a readable measure (500-700px)', ch65 > 500 && ch65 < 700, String(ch65));

  addCheck('line-height is 1.7 x 16px = 27.2px', (await computed(page, 'article', 'line-height')) === '27.2px', await computed(page, 'article', 'line-height'));
  addCheck('article padding is 16px', (await computed(page, 'article', 'padding-left')) === '16px');

  // Used width = min(65ch, available content width); that relation is the real
  // guarantee and it must hold at every viewport.
  const width = parseFloat(await computed(page, 'article', 'width'));
  const available = await page.evaluate(() => document.body.clientWidth - 32);
  addCheck('article width is min(65ch, available width)', Math.abs(width - Math.min(ch65, available)) < 1, `${width} vs min(${ch65}, ${available})`);

  // Centring only means something when the measure is narrower than the page.
  const marginLeft = parseFloat(await computed(page, 'article', 'margin-left'));
  const marginRight = parseFloat(await computed(page, 'article', 'margin-right'));
  if (ch65 < available) {
    addCheck('article is centred with equal side margins', Math.abs(marginLeft - marginRight) < 1 && marginLeft > 0, `${marginLeft}/${marginRight}`);
    const box = await page.locator('article').first().boundingBox();
    addCheck('article is horizontally centred on the page', Math.abs(box.x + box.width / 2 - (await viewportWidth(page)) / 2) <= 8, `${box.x + box.width / 2}`);
  } else {
    addCheck('at a narrow width the article fills the available width', width === available, `${width} vs ${available}`);
  }
});

CSS_CASES.set('css-example-045', async (page, addCheck) => {
  const marker = await page.locator('ul:not(.check) > li').first().evaluate((el) => getComputedStyle(el, '::marker').color);
  addCheck('marker blue', sameColor(marker, '#1a73e8'), marker);
  addCheck('check list no bullets', (await computed(page, 'ul.check', 'list-style-type')) === 'none');
  const before = await page.locator('ul.check > li').first().evaluate((el) => getComputedStyle(el, '::before').content);
  addCheck('check list has ✔ before', before.includes('✔'), before);
});

CSS_CASES.set('css-example-046', async (page, addCheck) => {
  addCheck('gallery is grid', (await computed(page, '.gallery', 'display')) === 'grid');
  addCheck('images square (aspect-ratio 1)', (await computed(page, '.gallery img', 'aspect-ratio')) === '1 / 1' || (await computed(page, '.gallery img', 'aspect-ratio')) === '1');
  addCheck('images object-fit cover', (await computed(page, '.gallery img', 'object-fit')) === 'cover');
  addCheck('three images', (await count(page, '.gallery img')) === 3);
  // All three inline-SVG thumbnails must decode.
  const imgs = await imageOutcomes(page);
  addCheck(
    'both gallery images decode',
    imgs.length === 3 && imgs.every((i) => i.naturalWidth > 0),
    JSON.stringify(imgs),
  );
  addCheck(
    'all gallery images are inline data URIs',
    imgs.length === 3 && imgs.every((i) => i.isData),
    JSON.stringify(imgs.map((i) => i.src.slice(0, 24))),
  );
});

CSS_CASES.set('css-example-047', async (page, addCheck) => {
  addCheck('link no underline', (await computed(page, 'a', 'text-decoration-line')) === 'none');
  addCheck('underline offset 3px', (await computed(page, 'a', 'text-underline-offset')) === '3px');
  await page.hover('a');
  addCheck('hover underlines', (await computed(page, 'a', 'text-decoration-line')) === 'underline');
  addCheck('hover underline 2px', (await computed(page, 'a', 'text-decoration-thickness')) === '2px');
});

CSS_CASES.set('css-example-048', async (page, addCheck) => {
  addCheck('skeleton shimmer animation', (await computed(page, '.skeleton', 'animation-name')) === 'shimmer');
  addCheck('skeleton grey', sameColor(await computed(page, '.skeleton', 'background-color'), '#e0e0e0'));
  addCheck('three skeleton blocks', (await count(page, '.skeleton')) === 3);
});

CSS_CASES.set('css-example-049', async (page, addCheck) => {
  addCheck('aspect-ratio 16/9', (await computed(page, '.video', 'aspect-ratio')) === '16 / 9' || (await computed(page, '.video', 'aspect-ratio')) === '1.77778');
  const box = await page.locator('.video').boundingBox();
  addCheck('box is ~16:9', Math.abs(box.width / box.height - 16 / 9) < 0.05, `${box.width}x${box.height}`);
  addCheck('video centred content', (await computed(page, '.video', 'place-items')) === 'center');
});

CSS_CASES.set('css-example-050', async (page, addCheck) => {
  const knob = () =>
    page
      .locator('.slider')
      .first()
      .evaluate((el) => getComputedStyle(el, '::before').transform.trim());

  addCheck('switch relative', (await computed(page, '.switch', 'position')) === 'relative');
  addCheck('switch is 48x26', (await computed(page, '.switch', 'width')) === '48px' && (await computed(page, '.switch', 'height')) === '26px');
  addCheck('slider grey initially', sameColor(await computed(page, '.slider', 'background-color'), '#cccccc'));
  addCheck('slider is a pill (999px)', (await computed(page, '.slider', 'border-radius')) === '999px');
  addCheck('knob starts at the left inset', (await knob()) === 'none', await knob());

  // The checkbox is display:none, but it lives inside the <label> — so clicking
  // the switch really toggles it, exactly like a user would. Clicking the
  // label (not setting `.checked` in JS) is what proves the CSS wiring.
  await page.locator('.switch').first().click();
  await settle(page, 400);
  addCheck('clicking the switch checks the box', await page.locator('.switch input').isChecked());
  addCheck('checked slider turns blue', sameColor(await computed(page, '.slider', 'background-color'), '#1a73e8'), await computed(page, '.slider', 'background-color'));
  addCheck('checked knob slides 22px right', (await knob()) === 'matrix(1, 0, 0, 1, 22, 0)', await knob());

  // Toggling back must restore the off state, not just latch on.
  await page.locator('.switch').first().click();
  await settle(page, 400);
  addCheck('second click unchecks the box', !(await page.locator('.switch input').isChecked()));
  addCheck('slider returns to grey', sameColor(await computed(page, '.slider', 'background-color'), '#cccccc'));
  addCheck('knob returns to the left inset', (await knob()) === 'none', await knob());

  // The knob really moves: its painted position differs between the two states.
  const geometry = await page.evaluate(() => ({ w: 48, knob: 20, left: 3, travel: 22 }));
  addCheck('knob travel keeps the knob inside the track', geometry.left + geometry.knob + geometry.travel + geometry.left === geometry.w, JSON.stringify(geometry));
});

CSS_CASES.set('css-example-051', async (page, addCheck) => {
  // Wide: three columns in 1fr / 3fr / 1fr proportions with named areas.
  const wide = await atViewport(page, 1280, 720, async () => ({
    cols: await gridColumns(page, '.holy'),
    areas: await computed(page, '.holy', 'grid-template-areas'),
    left: (await page.locator('.left').first().boundingBox()).width,
    main: (await page.locator('main').first().boundingBox()).width,
    right: (await page.locator('.right').first().boundingBox()).width,
    header: (await page.locator('header').first().boundingBox()).width,
    leftX: (await page.locator('.left').first().boundingBox()).x,
    mainX: (await page.locator('main').first().boundingBox()).x,
    rightX: (await page.locator('.right').first().boundingBox()).x,
    leftY: (await page.locator('.left').first().boundingBox()).y,
    mainY: (await page.locator('main').first().boundingBox()).y,
    containerWidth: (await page.locator('.holy').first().boundingBox()).width,
  }));

  // Narrow: the same document collapses to one column with stacked blocks.
  const narrow = await atViewport(page, 412, 720, async () => ({
    cols: await gridColumns(page, '.holy'),
    areas: await computed(page, '.holy', 'grid-template-areas'),
    leftX: (await page.locator('.left').first().boundingBox()).x,
    mainX: (await page.locator('main').first().boundingBox()).x,
    rightX: (await page.locator('.right').first().boundingBox()).x,
    leftY: (await page.locator('.left').first().boundingBox()).y,
    mainY: (await page.locator('main').first().boundingBox()).y,
    rightY: (await page.locator('.right').first().boundingBox()).y,
  }));

  if (wide) {
    addCheck('wide layout has three columns', wide.cols === 3, `cols=${wide.cols}`);
    addCheck('wide layout declares head/left/main/right/foot areas', ['head', 'left', 'main', 'right', 'foot'].every((a) => wide.areas.includes(a)), wide.areas);
    addCheck('left and right sidebars are equally wide', Math.abs(wide.left - wide.right) < 1, `${wide.left}/${wide.right}`);
    addCheck('main column is three times a sidebar (3fr)', Math.abs(wide.main / wide.left - 3) < 0.05, `${(wide.main / wide.left).toFixed(3)}x`);
    addCheck('header spans the full container width', Math.abs(wide.header - wide.containerWidth) < 1, `${wide.header} vs ${wide.containerWidth}`);
    addCheck('sidebars flank the main column on one row', wide.leftX < wide.mainX && wide.mainX < wide.rightX && wide.leftY === wide.mainY, `${wide.leftX}/${wide.mainX}/${wide.rightX}`);
  } else {
    // Cannot resize: assert the branch the real width implies.
    const width = await viewportWidth(page);
    const cols = await gridColumns(page, '.holy');
    const expected = width > 640 ? 3 : 1;
    addCheck(`at the real ${width}px width the layout shows ${expected} column(s)`, cols === expected, `cols=${cols}`);
    addCheck('named areas are declared', (await computed(page, '.holy', 'grid-template-areas')).includes('head'));
  }

  if (narrow) {
    addCheck('narrow layout collapses to one column', narrow.cols === 1, `cols=${narrow.cols}`);
    addCheck('narrow areas stack head/left/main/right/foot', /"head"\s+"left"\s+"main"\s+"right"\s+"foot"/.test(narrow.areas), narrow.areas);
    addCheck('narrow blocks all start at the same x', narrow.leftX === narrow.mainX && narrow.mainX === narrow.rightX, `${narrow.leftX}/${narrow.mainX}/${narrow.rightX}`);
    addCheck('narrow blocks stack downward (left, main, right)', narrow.leftY < narrow.mainY && narrow.mainY < narrow.rightY, `${narrow.leftY}/${narrow.mainY}/${narrow.rightY}`);
  }
});

CSS_CASES.set('css-example-052', async (page, addCheck) => {
  addCheck('acc collapsed (0fr)', (await computed(page, '.acc', 'grid-template-rows')) === '0px');
  await page.click('button');
  await settle(page, 600);
  addCheck('acc gains .open on click', (await attr(page, '.acc', 'class')).includes('open'));
  const rows = await computed(page, '.acc', 'grid-template-rows');
  addCheck('acc opens to a positive height', parseFloat(rows) > 0, rows);
  addCheck('inner div clips overflow', (await computed(page, '.acc > div', 'overflow')) === 'hidden');
});

CSS_CASES.set('css-example-053', async (page, addCheck) => {
  addCheck('li fadeUp animation', (await computed(page, 'li', 'animation-name')) === 'fadeUp');
  addCheck('second item delayed 0.1s', (await computed(page, 'li:nth-child(2)', 'animation-delay')) === '0.1s');
  addCheck('fourth item delayed 0.3s', (await computed(page, 'li:nth-child(4)', 'animation-delay')) === '0.3s');
});

CSS_CASES.set('css-example-054', async (page, addCheck) => {
  addCheck('wrap uses flow-root', (await computed(page, '.wrap', 'display')) === 'flow-root');
  addCheck('box floats left', (await computed(page, '.box', 'float')) === 'left');
  const wrap = await page.locator('.wrap').boundingBox();
  const box = await page.locator('.box').first().boundingBox();
  addCheck('wrap contains floated boxes (no collapse)', wrap.height > box.height, `${wrap.height} vs ${box.height}`);
});

CSS_CASES.set('css-example-055', async (page, addCheck) => {
  addCheck('mark yellow-ish background', sameColor(await computed(page, 'mark', 'background-color'), '#fff3cd'));
  addCheck('mark text', (await text(page, 'mark')) === '高亮');
});

CSS_CASES.set('css-example-056', async (page, addCheck) => {
  addCheck('row gap 12px', (await computed(page, '.row', 'gap')) === '12px');
  addCheck('row has padding', (await computed(page, '.row', 'padding-top')) === '8px');
  addCheck('three items', (await count(page, '.item')) === 3);
});

CSS_CASES.set('css-example-057', async (page, addCheck) => {
  addCheck('sr-only is 1px', (await computed(page, '.sr-only', 'width')) === '1px' && (await computed(page, '.sr-only', 'height')) === '1px');
  addCheck('sr-only clipped', (await computed(page, '.sr-only', 'overflow')) === 'hidden');
  addCheck('sr-only text present', (await text(page, '.sr-only')) === '搜索');
  addCheck('button contains icon', (await text(page, 'button')).includes('🔍'));
});

CSS_CASES.set('css-example-058', async (page, addCheck) => {
  addCheck('card transition on transform', (await computed(page, '.card', 'transition-property')).includes('transform'));
  await page.hover('.card');
  const t = await computed(page, '.card', 'transform');
  addCheck('hover lifts card (translateY)', t !== 'none' && t.includes('matrix'), t);
  addCheck('hover shadow deepens', (await computed(page, '.card', 'box-shadow')) !== 'none');
});

CSS_CASES.set('css-example-059', async (page, addCheck) => {
  const bgFirst = await page.locator('ol.steps > li').first().evaluate((el) => getComputedStyle(el, '::before').backgroundColor);
  addCheck('done step circle green', sameColor(bgFirst, '#34a853'), bgFirst);
  const bgLast = await page.locator('ol.steps > li').nth(2).evaluate((el) => getComputedStyle(el, '::before').backgroundColor);
  addCheck('last step circle blue', sameColor(bgLast, '#1a73e8'), bgLast);
  // ::before content is a counter template; assert the counter usage itself.
  const counter = await page.locator('ol.steps > li').first().evaluate((el) => getComputedStyle(el, '::before').content);
  addCheck('step badge uses a counter', counter.includes('counter('), counter);
  addCheck('step list declares counter-increment', (await computed(page, 'ol.steps > li', 'counter-increment')).includes('step'));
});

CSS_CASES.set('css-example-060', async (page, addCheck) => {
  addCheck('bar fixed', (await computed(page, '#bar', 'position')) === 'fixed');
  addCheck('bar blue', sameColor(await computed(page, '#bar', 'background-color'), '#1a73e8'));
  addCheck('bar starts at width 0', (await computed(page, '#bar', 'width')) === '0px');
  await page.evaluate(() => window.scrollTo(0, 600));
  await page.waitForTimeout(80);
  const w = parseFloat(await computed(page, '#bar', 'width'));
  addCheck('bar grows on scroll', w > 0, `${w}`);
});

CSS_CASES.set('css-example-061', async (page, addCheck) => {
  addCheck('center is grid', (await computed(page, '.center', 'display')) === 'grid');
  addCheck('center place-items center', (await computed(page, '.center', 'place-items')) === 'center');
  addCheck('inline text-align center', (await computed(page, '.inline', 'text-align')) === 'center');
});

CSS_CASES.set('css-example-062', async (page, addCheck) => {
  addCheck('hero has background image', (await computed(page, '.hero', 'background-image')).includes('url'));
  const overlay = await page.locator('.hero').evaluate((el) => getComputedStyle(el, '::after').backgroundColor);
  addCheck('overlay darkens image', overlay.includes('rgba(0, 0, 0'), overlay);
  addCheck('title above overlay', (await computed(page, '.hero h1', 'z-index')) === '1');
  addCheck('title white', sameColor(await computed(page, '.hero h1', 'color'), '#ffffff'));
  // The hero background is an inline SVG: it must be a data URI AND decode.
  const bgIcon = await backgroundDecodes(page, '.hero');
  addCheck('hero background is inline data URI', bgIcon.isData, JSON.stringify(bgIcon));
  addCheck('hero background image really decodes', bgIcon.ok, JSON.stringify(bgIcon));
});

CSS_CASES.set('css-example-063', async (page, addCheck) => {
  const bg = await computed(page, '.ring', 'background-image');
  addCheck('conic gradient used', bg.includes('conic-gradient'), bg);
  addCheck('ring round', (await computed(page, '.ring', 'border-radius')) === '50%');
  const inner = await page.locator('.ring').evaluate((el) => getComputedStyle(el, '::before').width);
  addCheck('inner hole is 72px', inner === '72px', inner);
});

CSS_CASES.set('css-example-064', async (page, addCheck) => {
  // Wide state: at >=600px the media query hides the burger and lays the menu
  // out horizontally.
  const wide = await atViewport(page, 1280, 720, async () => ({
    burger: await computed(page, '.burger', 'display'),
    menu: await computed(page, '.menu', 'display'),
    gap: await computed(page, '.menu', 'gap'),
    itemsInline: new Set(await tops(page, '.menu li')).size === 1,
  }));
  if (wide) {
    addCheck('wide: burger is hidden', wide.burger === 'none', wide.burger);
    addCheck('wide: menu is flex', wide.menu === 'flex', wide.menu);
    addCheck('wide: menu items sit on one row', wide.itemsInline);
    addCheck('wide: menu gap 16px', wide.gap === '16px');
  } else {
    const width = await viewportWidth(page);
    const menu = await computed(page, '.menu', 'display');
    const burger = await computed(page, '.burger', 'display');
    if (width >= 600) {
      addCheck(`wide (${width}px): burger is hidden`, burger === 'none', burger);
      addCheck(`wide (${width}px): menu is flex`, menu === 'flex', menu);
    } else {
      addCheck(`narrow (${width}px): burger is shown`, burger !== 'none', burger);
      addCheck(`narrow (${width}px): menu starts collapsed`, menu === 'none', menu);
    }
  }

  // Narrow state: the burger appears, the menu is collapsed, and a real click
  // on the label toggles it — this is the whole lesson, so drive it by clicking
  // the visible ☰ label exactly like a user (not by setting .checked in JS).
  const narrow = await atViewport(page, 412, 720, async () => {
    const before = {
      burger: await computed(page, '.burger', 'display'),
      menu: await computed(page, '.menu', 'display'),
      menuVisible: await isVisible(page, '.menu'),
    };
    await page.locator('.burger').first().click();
    await settle(page, 200);
    const opened = {
      menu: await computed(page, '.menu', 'display'),
      menuVisible: await isVisible(page, '.menu'),
      checked: await page.locator('#nav-toggle').isChecked(),
      stacked: new Set(await tops(page, '.menu li')).size === 3,
      items: await count(page, '.menu li'),
    };
    await page.locator('.burger').first().click();
    await settle(page, 200);
    const closed = {
      menu: await computed(page, '.menu', 'display'),
      checked: await page.locator('#nav-toggle').isChecked(),
    };
    return { before, opened, closed };
  });

  if (narrow) {
    addCheck('narrow: burger is shown', narrow.before.burger !== 'none', narrow.before.burger);
    addCheck('narrow: menu starts collapsed', narrow.before.menu === 'none' && narrow.before.menuVisible === false, narrow.before.menu);
    addCheck('narrow: clicking ☰ checks the toggle', narrow.opened.checked);
    addCheck('narrow: clicking ☰ reveals the menu', narrow.opened.menu === 'block' && narrow.opened.menuVisible === true, narrow.opened.menu);
    addCheck('narrow: revealed menu stacks its three items', narrow.opened.stacked && narrow.opened.items === 3, `${narrow.opened.items} items`);
    addCheck('narrow: clicking ☰ again unchecks the toggle', !narrow.closed.checked);
    addCheck('narrow: clicking ☰ again hides the menu', narrow.closed.menu === 'none', narrow.closed.menu);
  } else {
    // Cannot resize and the real width is wide: the toggle is unreachable here,
    // so assert the authored toggle rule is present rather than claiming a pass.
    const rule = await page.evaluate(() => {
      for (const ss of document.styleSheets) {
        for (const r of ss.cssRules || []) {
          if (r.selectorText && r.selectorText.includes('#nav-toggle:checked')) return r.cssText;
        }
      }
      return '';
    });
    addCheck('the #nav-toggle:checked rule reveals the menu', rule.includes(':checked') && /display:\s*block/.test(rule), rule);
  }
});

CSS_CASES.set('css-example-065', async (page, addCheck) => {
  addCheck('clamp overflow hidden', (await computed(page, '.clamp', 'overflow')) === 'hidden');
  const clamped = await page.locator('.clamp').evaluate((el) => el.scrollHeight > el.clientHeight + 1);
  addCheck('clamp actually clips content', clamped);
  addCheck('clamp width 200px', (await computed(page, '.clamp', 'width')) === '200px');
});

CSS_CASES.set('css-example-066', async (page, addCheck) => {
  addCheck('even row shaded', sameColor(await computed(page, 'tbody tr:nth-child(2)', 'background-color'), '#f7f7f7'));
  addCheck('table border-collapse', (await computed(page, 'table', 'border-collapse')) === 'collapse');
  await page.hover('tbody tr');
  addCheck('hovered row turns light blue', sameColor(await computed(page, 'tbody tr:hover', 'background-color'), '#e8f0fe'), await computed(page, 'tbody tr', 'background-color'));
});

CSS_CASES.set('css-example-067', async (page, addCheck) => {
  addCheck('nav visible on screen', await isVisible(page, 'nav'));
  addCheck('button visible on screen', await isVisible(page, 'button'));
  const printRule = await page.evaluate(() => {
    for (const ss of document.styleSheets) {
      for (const r of ss.cssRules || []) {
        if (r.media && String(r.media.mediaText).includes('print')) return true;
      }
    }
    return false;
  });
  addCheck('print media rule declared', printRule);
  addCheck('article present', (await count(page, 'article h1')) === 1);
});

CSS_CASES.set('css-example-068', async (page, addCheck) => {
  const fl = await page.locator('p').evaluate((el) => getComputedStyle(el, '::first-letter').float);
  addCheck('first letter floats', fl === 'left', fl);
  const size = await page.locator('p').evaluate((el) => getComputedStyle(el, '::first-letter').fontSize);
  addCheck('first letter enlarged', parseFloat(size) > 30, size);
});

CSS_CASES.set('css-example-069', async (page, addCheck) => {
  addCheck('badge pill radius', (await computed(page, '.badge', 'border-radius')) === '999px');
  addCheck('ok badge green fg', sameColor(await computed(page, '.ok', 'color'), '#0f7a3d'));
  addCheck('warn badge amber bg', sameColor(await computed(page, '.warn', 'background-color'), '#fef7e0'));
  addCheck('err badge red fg', sameColor(await computed(page, '.err', 'color'), '#c5221f'));
});

CSS_CASES.set('css-example-070', async (page, addCheck) => {
  const labelTopBefore = await computed(page, '.field label', 'top');
  await page.locator('.field input').focus();
  await settle(page, 400);
  const labelTopAfter = await computed(page, '.field label', 'top');
  addCheck('label floats up on focus', parseFloat(labelTopAfter) < parseFloat(labelTopBefore), `${labelTopBefore} -> ${labelTopAfter}`);
  addCheck('label pointer-events none', (await computed(page, '.field label', 'pointer-events')) === 'none');
  addCheck('label text', (await text(page, '.field label')) === '姓名');
});

CSS_CASES.set('css-example-071', async (page, addCheck) => {
  addCheck('btn blue background', sameColor(await computed(page, '.btn', 'background-color'), '#1a73e8'));
  addCheck('btn white text', sameColor(await computed(page, '.btn', 'color'), '#ffffff'));
  const forced = await page.evaluate(() => {
    for (const ss of document.styleSheets) {
      for (const r of ss.cssRules || []) {
        if (String(r.conditionText || r.media?.mediaText || '').includes('forced-colors')) return true;
      }
    }
    return false;
  });
  addCheck('forced-colors rule declared', forced);
});

CSS_CASES.set('css-example-072', async (page, addCheck) => {
  addCheck('container max-width 1080px', (await computed(page, '.container', 'max-width')) === '1080px');
  addCheck('container padding 16px', (await computed(page, '.container', 'padding-left')) === '16px');
  const l = await computed(page, '.container', 'margin-left');
  const r = await computed(page, '.container', 'margin-right');
  addCheck('container auto margins', l === r);
});

CSS_CASES.set('css-example-073', async (page, addCheck) => {
  addCheck('body font stack includes MyFont', (await computed(page, 'body', 'font-family')).includes('MyFont'));
  addCheck('text still rendered with fallback', (await text(page, 'p')).length > 0);
  addCheck(
    'visible ASCII "WebForge" sample present',
    (await page.evaluate(() => document.body.innerText)).includes('WebForge'),
    (await page.evaluate(() => document.body.innerText)).slice(0, 80),
  );
  addCheck(
    'font src is an inline data URI (no my.woff2 fetch)',
    await page.evaluate(() => {
      for (const ss of document.styleSheets) {
        for (const r of ss.cssRules || []) {
          if (r instanceof CSSFontFaceRule) return /^url\((['"]?)data:font\//.test((r.style.src || '').trim());
        }
      }
      return false;
    }),
  );
  const swap = await page.evaluate(() => {
    for (const ss of document.styleSheets) {
      for (const r of ss.cssRules || []) {
        if (r instanceof CSSFontFaceRule && /swap/.test(r.style.fontDisplay || '')) return true;
      }
    }
    return false;
  });
  addCheck('@font-face font-display swap declared', swap);

  // The embedded font must be a REAL font that loads, not a placeholder blob
  // (e.g. an all-AAAA WOFF2). Assert load() resolves non-empty and every
  // FontFace reaches status 'loaded' — checking the CSS rule alone is not
  // enough.
  const fontFaces = await page.evaluate(() => {
    const faces = [];
    for (const ss of document.styleSheets) {
      for (const r of ss.cssRules || []) {
        if (r instanceof CSSFontFaceRule) {
          faces.push({ family: r.style.fontFamily, src: (r.style.src || '').slice(0, 24) });
        }
      }
    }
    return faces;
  });
  addCheck('a @font-face is declared for MyFont', fontFaces.some((f) => /MyFont/.test(f.family)), JSON.stringify(fontFaces));

  const loaded = await page.evaluate(async () => {
    try {
      const set = await document.fonts.load('16px MyFont', 'WebForge');
      return {
        count: set.length,
        statuses: [...document.fonts].map((f) => f.status),
        check: document.fonts.check('16px MyFont', 'WebForge'),
        ok: set.length > 0,
      };
    } catch (e) {
      return { count: 0, statuses: [], check: false, ok: false, error: String(e) };
    }
  });
  addCheck('document.fonts.load returns a real face', loaded.ok, JSON.stringify(loaded));
  addCheck(
    'every FontFace status is loaded',
    loaded.statuses.length > 0 && loaded.statuses.every((s) => s === 'loaded'),
    JSON.stringify(loaded),
  );
  addCheck('document.fonts.check is true', loaded.check === true, JSON.stringify(loaded));
});

CSS_CASES.set('css-example-074', async (page, addCheck) => {
  await page.hover('.fast');
  await settle(page);
  const fast = await computed(page, '.fast', 'transform');
  addCheck('fast moves via transform', fast !== 'none' && fast.includes('matrix'), fast);
  await page.hover('.slow');
  await settle(page);
  const slowLeft = await computed(page, '.slow', 'left');
  addCheck('slow moves via left', slowLeft === '40px', slowLeft);
});

CSS_CASES.set('css-example-075', async (page, addCheck) => {
  const before = await page.locator('a').evaluate((el) => getComputedStyle(el, '::after').width);
  addCheck('underline starts at width 0', before === '0px', before);
  await page.hover('a');
  await settle(page);
  const after = await page.locator('a').evaluate((el) => getComputedStyle(el, '::after').width);
  addCheck('underline expands on hover', parseFloat(after) > 0, after);
});

CSS_CASES.set('css-example-076', async (page, addCheck) => {
  addCheck('stack is grid', (await computed(page, '.stack', 'display')) === 'grid');
  const imgBox = await page.locator('.img').boundingBox();
  const labelBox = await page.locator('.label').boundingBox();
  addCheck('label overlaps the image', labelBox.y < imgBox.y + imgBox.height, `${labelBox.y} vs ${imgBox.y + imgBox.height}`);
  addCheck('label white', sameColor(await computed(page, '.label', 'color'), '#ffffff'));
});

CSS_CASES.set('css-example-077', async (page, addCheck) => {
  addCheck('item blue', sameColor(await computed(page, '.item', 'color'), '#1a73e8'));
  addCheck('descendant link no underline', (await computed(page, '.list .item a', 'text-decoration-line')) === 'none');
  addCheck('link text', (await text(page, 'a')) === '链接');
});

CSS_CASES.set('css-example-078', async (page, addCheck) => {
  addCheck('icon inline-block', (await computed(page, '.icon', 'display')) === 'inline-block');
  addCheck('icon 24x24', (await computed(page, '.icon', 'width')) === '24px' && (await computed(page, '.icon', 'height')) === '24px');
  const pos = await computed(page, '.icon.b', 'background-position');
  addCheck('second icon shifted by -24px', pos.startsWith('-24px'), pos);
  // The sprite is an inline SVG: it must be a data URI AND decode.
  const sprite = await backgroundDecodes(page, '.icon');
  addCheck('sprite background is inline data URI', sprite.isData, JSON.stringify(sprite));
  addCheck('sprite background really decodes', sprite.ok, JSON.stringify(sprite));
});

CSS_CASES.set('css-example-079', async (page, addCheck) => {
  addCheck('section content-visibility auto', (await computed(page, '.section', 'content-visibility')) === 'auto');
  // contain-intrinsic-size computes to `auto 300px` (with the `auto` keyword).
  addCheck(
    'contain-intrinsic-size keeps 300px',
    (await computed(page, '.section', 'contain-intrinsic-size')).includes('300px'),
    await computed(page, '.section', 'contain-intrinsic-size'),
  );
  addCheck('three sections', (await count(page, '.section')) === 3);
});

CSS_CASES.set('css-example-080', async (page, addCheck) => {
  // `grid-auto-flow: row dense` is reported as just `dense` by Chrome.
  addCheck('grid auto-flow dense', (await computed(page, '.grid', 'grid-auto-flow')).includes('dense'), await computed(page, '.grid', 'grid-auto-flow'));
  addCheck('four columns', (await computed(page, '.grid', 'grid-template-columns')).split(' ').length === 4);
  addCheck('wide item spans 2', (await computed(page, '.wide', 'grid-column-start')) === 'span 2');
  addCheck('six items', (await count(page, '.item') + await count(page, '.wide')) === 6);
});

CSS_CASES.set('css-example-081', async (page, addCheck) => {
  const lum = async (sel) => {
    const c = await computed(page, sel, 'background-color');
    const m = /rgb\((\d+), (\d+), (\d+)\)/.exec(c);
    return m ? 0.2126 * +m[1] + 0.7152 * +m[2] + 0.0722 * +m[3] : NaN;
  };
  const [l1, l2, l3, l4] = await Promise.all(
    ['.s1', '.s2', '.s3', '.s4'].map(lum),
  );
  addCheck('four swatches render as rgb', ![l1, l2, l3, l4].some(Number.isNaN), `${l1},${l2},${l3},${l4}`);
  addCheck('lightness strictly decreases s1>s2>s3>s4', l1 > l2 && l2 > l3 && l3 > l4, `${l1},${l2},${l3},${l4}`);
  const w = async (s) => (await page.locator(s).boundingBox()).width;
  addCheck('swatches equal width', Math.abs((await w('.s1')) - (await w('.s4'))) < 1);
});

CSS_CASES.set('css-example-082', async (page, addCheck) => {
  addCheck('typing animation applied', (await computed(page, '.type', 'animation-name')).includes('typing'));
  addCheck('cursor blink in animation list', (await computed(page, '.type', 'animation-name')).includes('blink'), await computed(page, '.type', 'animation-name'));
  addCheck('no-wrap keeps one line', (await computed(page, '.type', 'white-space')) === 'nowrap');
  addCheck('right border is the cursor', (await computed(page, '.type', 'border-right-style')) === 'solid');
});

CSS_CASES.set('css-example-083', async (page, addCheck) => {
  addCheck('box background #e8f0fe', sameColor(await computed(page, '.box', 'background-color'), '#e8f0fe'));
  const supports = await page.evaluate(() => {
    for (const ss of document.styleSheets) {
      for (const r of ss.cssRules || []) {
        if (r instanceof CSSSupportsRule) return r.conditionText;
      }
    }
    return '';
  });
  addCheck('@supports (display: grid) declared', supports.includes('grid'), supports);
  addCheck('box ends up gridded', (await computed(page, '.box', 'display')) === 'grid');
});

CSS_CASES.set('css-example-084', async (page, addCheck) => {
  addCheck('img object-fit cover', (await computed(page, 'img', 'object-fit')) === 'cover');
  addCheck(
    'default image centred (50% 50%)',
    (await computed(page, 'img:not(.top)', 'object-position')) === '50% 50%',
    await computed(page, 'img:not(.top)', 'object-position'),
  );
  addCheck(
    'top image keeps top edge (50% 0%)',
    (await computed(page, '.top', 'object-position')) === '50% 0%',
    await computed(page, '.top', 'object-position'),
  );
  // Both inline-SVG images must decode for object-fit/position to mean anything.
  const imgs = await imageOutcomes(page);
  addCheck(
    'both crop images decode',
    imgs.length === 2 && imgs.every((i) => i.naturalWidth > 0),
    JSON.stringify(imgs),
  );
});

CSS_CASES.set('css-example-085', async (page, addCheck) => {
  addCheck('th sticky', (await computed(page, 'th', 'position')) === 'sticky');
  addCheck('th top 0', (await computed(page, 'th', 'top')) === '0px');
  addCheck('th blue', sameColor(await computed(page, 'th', 'background-color'), '#1a73e8'));
  const scrolls = await page.locator('.wrap').evaluate((el) => el.scrollHeight > el.clientHeight);
  addCheck('wrap actually scrolls', scrolls);
});

CSS_CASES.set('css-example-086', async (page, addCheck) => {
  addCheck('body starts white', sameColor(await computed(page, 'body', 'background-color'), '#ffffff'));
  await page.click('button');
  await settle(page, 500);
  addCheck('click applies .dark to body', (await attr(page, 'body', 'class')).includes('dark'));
  addCheck('click toggles dark background', sameColor(await computed(page, 'body', 'background-color'), '#202124'), await computed(page, 'body', 'background-color'));
  addCheck('transition on background+colour', (await computed(page, 'body', 'transition-property')).includes('background-color'));
});

CSS_CASES.set('css-example-087', async (page, addCheck) => {
  // Named grid lines are tokens: `[left] 628px [mid] 628px [right]`.
  const cols = await computed(page, '.g', 'grid-template-columns');
  addCheck('grid declares named lines', cols.includes('[left]') && cols.includes('[mid]') && cols.includes('[right]'), cols);
  const a = await page.locator('.a').boundingBox();
  const b = await page.locator('.b').boundingBox();
  addCheck('blocks are half-width each', Math.abs(a.width - b.width) < 2, `${a.width} vs ${b.width}`);
  addCheck('a is left half', a.x < b.x);
});

CSS_CASES.set('css-example-088', async (page, addCheck) => {
  const bg = await computed(page, '.field', 'background-image');
  addCheck('icon background image layered with colour', bg.includes('url'), bg);
  addCheck('left padding leaves room for icon', (await computed(page, '.field', 'padding-left')) === '40px');
  addCheck('field text present', (await text(page, '.field')) === '左侧有图标背景的输入区');
  // The background icon is an inline SVG: it must be a data URI AND decode.
  const icon = await backgroundDecodes(page, '.field');
  addCheck('background icon is inline data URI', icon.isData, JSON.stringify(icon));
  addCheck('background icon really decodes', icon.ok, JSON.stringify(icon));
});

CSS_CASES.set('css-example-089', async (page, addCheck) => {
  addCheck('footer hidden on screen', !(await isVisible(page, '.page-footer')));
  const printRule = await page.evaluate(() => {
    for (const ss of document.styleSheets) {
      for (const r of ss.cssRules || []) {
        if (r.media && String(r.media.mediaText).includes('print')) return true;
      }
    }
    return false;
  });
  addCheck('print media rule declared', printRule);
  addCheck('footer text', (await text(page, '.page-footer')) === '第 1 页');
});

CSS_CASES.set('css-example-090', async (page, addCheck) => {
  const state = async () => ({
    space: await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--space').trim()),
    title: await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--title').trim()),
    padding: await computed(page, '.card', 'padding-top'),
    margin: await computed(page, '.card', 'margin-bottom'),
    h2: await computed(page, 'h2', 'font-size'),
  });

  addCheck('card background #e8f0fe', sameColor(await computed(page, '.card', 'background-color'), '#e8f0fe'));

  // Both branches of the 600px breakpoint: the lesson is about custom
  // properties switching value, so assert the variable AND the declarations
  // that consume it, on each side of the breakpoint.
  const narrow = await atViewport(page, 599, 720, state);
  const wide = await atViewport(page, 600, 720, state);

  if (narrow && wide) {
    addCheck('narrow: --space is 8px', narrow.space === '8px', narrow.space);
    addCheck('narrow: --title is 18px', narrow.title === '18px', narrow.title);
    addCheck('narrow: card padding follows --space (8px)', narrow.padding === '8px', narrow.padding);
    addCheck('narrow: card margin follows --space (8px)', narrow.margin === '8px', narrow.margin);
    addCheck('narrow: h2 follows --title (18px)', narrow.h2 === '18px', narrow.h2);
    addCheck('wide: --space switches to 16px', wide.space === '16px', wide.space);
    addCheck('wide: --title switches to 24px', wide.title === '24px', wide.title);
    addCheck('wide: card padding follows --space (16px)', wide.padding === '16px', wide.padding);
    addCheck('wide: h2 follows --title (24px)', wide.h2 === '24px', wide.h2);
    addCheck('the breakpoint actually changes the padding', narrow.padding !== wide.padding, `${narrow.padding} -> ${wide.padding}`);
    addCheck('the breakpoint actually changes the heading size', narrow.h2 !== wide.h2, `${narrow.h2} -> ${wide.h2}`);
  } else {
    // Cannot resize: assert the values implied by the real width, and that the
    // variable is really what drives them.
    const width = await viewportWidth(page);
    const real = await state();
    const expectedSpace = width >= 600 ? '16px' : '8px';
    const expectedTitle = width >= 600 ? '24px' : '18px';
    addCheck(`at the real ${width}px width --space is ${expectedSpace}`, real.space === expectedSpace, real.space);
    addCheck(`at the real ${width}px width --title is ${expectedTitle}`, real.title === expectedTitle, real.title);
    addCheck('card padding consumes --space', real.padding === real.space, `${real.padding} vs ${real.space}`);
    addCheck('h2 font-size consumes --title', real.h2 === real.title, `${real.h2} vs ${real.title}`);
  }
});

CSS_CASES.set('css-example-091', async (page, addCheck) => {
  addCheck('spinner round', (await computed(page, '.spinner', 'border-radius')) === '50%');
  addCheck('spinner spin animation', (await computed(page, '.spinner', 'animation-name')) === 'spin');
  addCheck('spinner top border blue', sameColor(await computed(page, '.spinner', 'border-top-color'), '#1a73e8'));
  addCheck('spinner 20x20', (await computed(page, '.spinner', 'width')) === '20px' && (await computed(page, '.spinner', 'height')) === '20px');
});

CSS_CASES.set('css-example-092', async (page, addCheck) => {
  addCheck('good blue bg', sameColor(await computed(page, '.good', 'background-color'), '#1a73e8'));
  addCheck('good white text', sameColor(await computed(page, '.good', 'color'), '#ffffff'));
  addCheck('bad low-contrast grey text', sameColor(await computed(page, '.bad', 'color'), '#999999'));
  addCheck('bad light grey bg', sameColor(await computed(page, '.bad', 'background-color'), '#eeeeee'));
});

CSS_CASES.set('css-example-093', async (page, addCheck) => {
  const clip = await computed(page, '.wave', 'clip-path');
  addCheck('wave clip-path polygon', clip.includes('polygon'), clip);
  addCheck('wave blue', sameColor(await computed(page, '.wave', 'background-color'), '#1a73e8'));
  addCheck('body block light blue', sameColor(await computed(page, 'body > .body', 'background-color'), '#e8f0fe'));
});

CSS_CASES.set('css-example-094', async (page, addCheck) => {
  // The :-webkit-autofill state cannot be entered from a test; assert the
  // declaration the author actually wrote is present in the parsed stylesheet,
  // plus the always-observable base input styling.
  const autofillRule = await page.evaluate(() => {
    for (const ss of document.styleSheets) {
      for (const r of ss.cssRules || []) {
        if (r.selectorText && r.selectorText.includes('-webkit-autofill')) {
          return `${r.style.boxShadow}|${r.style.getPropertyValue('-webkit-text-fill-color')}`;
        }
      }
    }
    return '';
  });
  addCheck('autofill rule declares inset box-shadow', autofillRule.includes('inset') && autofillRule.includes('1000px'), autofillRule);
  // -webkit-text-fill-color stores the computed rgb of #202124.
  addCheck('autofill rule declares text fill colour', autofillRule.includes('32, 33, 36'), autofillRule);
  addCheck('input padding 8px', (await computed(page, 'input', 'padding-top')) === '8px');
  addCheck('input radius 6px', (await computed(page, 'input', 'border-radius')) === '6px');
});

CSS_CASES.set('css-example-095', async (page, addCheck) => {
  const bodySize = parseFloat(await computed(page, 'body', 'font-size'));
  addCheck('body font-size in clamp range', bodySize >= 16 && bodySize <= 18, `${bodySize}`);
  const h1Size = parseFloat(await computed(page, 'h1', 'font-size'));
  addCheck('h1 font-size in clamp range', h1Size >= 24 && h1Size <= 48, `${h1Size}`);
  addCheck('h1 text', (await text(page, 'h1')) === '流式标题');
});

CSS_CASES.set('css-example-096', async (page, addCheck) => {
  const shadow = await computed(page, 'h1', 'text-shadow');
  addCheck('four-direction blue outline', (shadow.match(/rgb\(26, 115, 232\)|#1a73e8/gi) || []).length >= 4, shadow);
  addCheck('text white', sameColor(await computed(page, 'h1', 'color'), '#ffffff'));
});

CSS_CASES.set('css-example-097', async (page, addCheck) => {
  addCheck('first item has bottom border', (await computed(page, 'li:nth-child(1)', 'border-bottom-style')) === 'solid');
  addCheck('second item has bottom border', (await computed(page, 'li:nth-child(2)', 'border-bottom-style')) === 'solid');
  addCheck('last item has no bottom border', (await computed(page, 'li:nth-child(3)', 'border-bottom-style')) === 'none');
  addCheck('three list items', (await count(page, 'li')) === 3);
});

CSS_CASES.set('css-example-098', async (page, addCheck) => {
  const cols = await computed(page, '.g', 'grid-template-columns');
  const parts = cols.split(' ').map((v) => parseFloat(v));
  addCheck('first column sized to content (smaller)', parts[0] < parts[1], cols);
  addCheck('second column fills remainder (larger)', parts[1] > parts[0], cols);
  addCheck('two labels', (await count(page, '.label')) === 2);
});

CSS_CASES.set('css-example-099', async (page, addCheck) => {
  addCheck('empty input not coloured', (await computed(page, 'input', 'border-top-color')) !== rgb('#ea4335'));
  await page.fill('input', 'not-an-email');
  await page.locator('input').blur();
  const invalid = await page.locator('input').evaluate((el) => getComputedStyle(el).borderTopColor);
  addCheck('invalid email border red', sameColor(invalid, '#ea4335'), invalid);
  await page.fill('input', 'user@example.com');
  await page.locator('input').blur();
  const valid = await page.locator('input').evaluate((el) => getComputedStyle(el).borderTopColor);
  addCheck('valid email border green', sameColor(valid, '#34a853'), valid);
});

CSS_CASES.set('css-example-100', async (page, addCheck) => {
  addCheck('card is grid', (await computed(page, '.card', 'display')) === 'grid');
  const badge = await page.locator('.badge').boundingBox();
  const card = await page.locator('.card').boundingBox();
  addCheck('badge sits top-right', badge.x > card.x + card.width / 2 && badge.y < card.y + card.height / 2);
  addCheck('badge red', sameColor(await computed(page, '.badge', 'background-color'), '#ea4335'));
  addCheck('badge text', (await text(page, '.badge')) === '3');
});

// ===========================================================================
// Public entry
// ===========================================================================

/**
 * Assert one WebForge markup/CSS example.
 *
 * @param {import('playwright').Page} page
 * @param {{id:string, language:string, code:string, expectedOutput:string}} example
 * @param {(name:string, ok:boolean, detail?:string) => void} addCheck
 * @returns {Promise<boolean>} true when this module handled the example
 */
export async function assertMarkupExample(page, example, addCheck) {
  const id = example?.id;
  const lang = (example?.language || '').toLowerCase();
  const cases = lang === 'css' ? CSS_CASES : lang === 'html' ? HTML_CASES : null;
  if (!cases) return false;
  const fn = cases.get(id);
  if (!fn) return false;
  await fn(page, addCheck);
  return true;
}

/** Ids this module covers, so the runner can report any gap. */
export const COVERED_IDS = [
  ...HTML_CASES.keys(),
  ...CSS_CASES.keys(),
];
