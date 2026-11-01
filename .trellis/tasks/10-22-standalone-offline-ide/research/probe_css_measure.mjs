// Targeted native measurement for the residual CSS failures.
//
// Reuses the single existing page; navigates only to packaged case URLs from the
// packaged bootstrap; never creates contexts/pages; browser.close() drops only
// the CDP transport.
import { resolve, dirname } from 'node:path';
import { writeFileSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../../../..');
const CDP = process.env.NATIVE_CDP || 'http://127.0.0.1:9222';

const { chromium } = await import(pathToFileURL(resolve(repo, 'node_modules/playwright/index.mjs')).href);
const { OHOS_BOOTSTRAP_URL } = await import(pathToFileURL(resolve(repo, 'scripts/catalog_device_contract.mjs')).href);

// Per-case measurement. Runs in the page; returns a plain object.
const MEASURE = {
  'css-example-035': () => {
    const btn = document.querySelector('.btn');
    const cs = getComputedStyle(btn);
    return {
      outlineWidth: cs.outlineWidth,
      outlineStyle: cs.outlineStyle,
      outlineColor: cs.outlineColor,
      outlineOffset: cs.outlineOffset,
      focusVisible: btn.matches(':focus-visible'),
    };
  },
  'css-example-041': () => {
    const badge = document.querySelector('.badge');
    const r = badge.getBoundingClientRect();
    const cs = getComputedStyle(badge);
    const after = getComputedStyle(badge, '::after');
    return {
      badgeW: +r.width.toFixed(4), badgeH: +r.height.toFixed(4),
      padding: cs.padding, lineHeight: cs.lineHeight, fontSize: cs.fontSize,
      afterW: after.width, afterH: after.height,
      afterTop: after.top, afterRight: after.right,
      borderTopWidth: after.borderTopWidth,
    };
  },
  'css-example-123': () => {
    const box = document.querySelector('#box');
    const r = box.getBoundingClientRect();
    const cs = getComputedStyle(box);
    const p = document.querySelector('p');
    return {
      boxW: +r.width.toFixed(4), boxH: +r.height.toFixed(4),
      cssH: cs.height, contain: cs.contain,
      scrollH: box.scrollHeight, clientH: box.clientHeight,
      pY: +p.getBoundingClientRect().y.toFixed(4),
      innerH: box.firstElementChild ? +box.firstElementChild.getBoundingClientRect().height.toFixed(4) : null,
    };
  },
  'css-example-125': () => {
    const g = (s) => {
      const el = document.querySelector(s);
      const r = el.getBoundingClientRect();
      return { w: +r.width.toFixed(4), css: getComputedStyle(el).width };
    };
    const word = 'Supercalifragilisticexpialidocious';
    const span = document.querySelector('#min span') || document.querySelector('#min');
    const text = (span.textContent || '').trim();
    const longest = text.split(/\s+/).sort((a, b) => b.length - a.length)[0] || text;
    const c = document.createElement('canvas').getContext('2d');
    c.font = getComputedStyle(document.querySelector('#min')).font;
    const m = c.measureText(longest);
    const c2 = document.createElement('canvas').getContext('2d');
    c2.font = getComputedStyle(document.querySelector('#max')).font;
    const full = (document.querySelector('#max').textContent || '').trim();
    return {
      fit: g('#fit'), max: g('#max'), min: g('#min'),
      longestWord: longest,
      canvasLongest: +m.width.toFixed(4),
      canvasFullLine: +c2.measureText(full).width.toFixed(4),
      fullText: full,
    };
  },
  'css-example-129': () => {
    const fs = (s) => {
      const el = document.querySelector(s);
      const r = el.getBoundingClientRect();
      return { fontSize: getComputedStyle(el).fontSize, h: +r.height.toFixed(4) };
    };
    return { tw: fs('#tw'), bw: fs('#bw'), tn: fs('#tn'), bn: fs('#bn') };
  },
  'css-example-141': () => {
    const p = document.querySelector('p');
    const em = document.querySelector('#em');
    const before = { p: +p.getBoundingClientRect().height.toFixed(4), lh: getComputedStyle(p).lineHeight, fs: getComputedStyle(p).fontSize };
    em.classList.remove('em');
    const plain = +p.getBoundingClientRect().height.toFixed(4);
    em.classList.add('em');
    return { withEmphasis: before.p, plain, lineHeight: before.lh, fontSize: before.fs };
  },
  'css-example-144': () => {
    const h = document.querySelector('#hyphenated');
    const b = document.querySelector('#broken');
    const span = h.querySelector('span');
    const r = (el) => { const x = el.getBoundingClientRect(); return { w: +x.width.toFixed(4), h: +x.height.toFixed(4) }; };
    return {
      brokenBox: r(b), brokenSpan: r(b.querySelector('span')),
      hyphenBox: r(h), hyphenSpan: r(span),
      hyphens: getComputedStyle(span).hyphens,
      overflowWrap: getComputedStyle(b.querySelector('span')).overflowWrap,
      hyphenLines: span.getClientRects().length,
      brokenLines: b.querySelector('span').getClientRects().length,
      lang: h.getAttribute('lang'),
    };
  },
  'css-example-145': () => {
    const w = (s) => { const el = document.querySelector(s); const r = el.getBoundingClientRect(); return +r.width.toFixed(6); };
    const cs = (s) => getComputedStyle(document.querySelector(s)).fontVariantNumeric;
    return {
      t1: w('#t1'), t2: w('#t2'), p1: w('#p1'), p2: w('#p2'),
      tnum: cs('#tnum'), pnum: cs('#pnum'),
    };
  },
  'css-example-147': () => {
    const hl = document.querySelector('#hl');
    const narrow = document.querySelector('.narrow');
    const cs = getComputedStyle(hl);
    const r = narrow.getBoundingClientRect();
    return {
      fragments: hl.getClientRects().length,
      borderLeft: cs.borderLeftWidth,
      paddingLeft: cs.paddingLeft,
      bg: cs.backgroundColor,
      narrowW: +r.width.toFixed(4),
      narrowCssW: getComputedStyle(narrow).width,
      narrowBorder: getComputedStyle(narrow).borderLeftWidth,
      narrowPadding: getComputedStyle(narrow).paddingLeft,
    };
  },
  'css-example-148': () => {
    const plain = document.querySelector('#plain');
    const trim = document.querySelector('#trim');
    const fs = parseFloat(getComputedStyle(trim).fontSize);
    const c = document.createElement('canvas').getContext('2d');
    c.font = getComputedStyle(trim).font;
    const H = c.measureText('H');
    const x = c.measureText('x');
    return {
      plainH: +plain.getBoundingClientRect().height.toFixed(4),
      trimH: +trim.getBoundingClientRect().height.toFixed(4),
      fontSize: fs,
      lineHeight: getComputedStyle(trim).lineHeight,
      canvasCapAscent: +H.actualBoundingBoxAscent.toFixed(4),
      canvasXAscent: +x.actualBoundingBoxAscent.toFixed(4),
      canvasXDescent: +x.actualBoundingBoxDescent.toFixed(4),
      canvasFontAscent: +H.fontBoundingBoxAscent.toFixed(4),
      canvasFontDescent: +H.fontBoundingBoxDescent.toFixed(4),
      trim: getComputedStyle(trim).textBoxTrim,
      edge: getComputedStyle(trim).textBoxEdge,
    };
  },
  'css-example-156': () => {
    const short = document.querySelector('#short');
    const plain = document.querySelector('#plain');
    const probe = document.createElement('div');
    probe.style.cssText = 'position:absolute;left:-9999px;width:100px;height:40px;overflow:scroll';
    const inner = document.createElement('div');
    inner.style.height = '200px';
    probe.appendChild(inner);
    document.body.appendChild(probe);
    const classicGutter = probe.offsetWidth - probe.clientWidth;
    probe.remove();
    return {
      shortW: +short.getBoundingClientRect().width.toFixed(4),
      shortCssW: getComputedStyle(short).width,
      plainW: +plain.getBoundingClientRect().width.toFixed(4),
      gutter: getComputedStyle(short).scrollbarGutter,
      classicGutter,
      shortScrollH: short.scrollHeight, shortClientH: short.clientHeight,
    };
  },
  'css-example-157': () => {
    const outer = document.querySelector('#outer');
    const r = outer.getBoundingClientRect();
    return {
      outerX: +r.x.toFixed(4), outerY: +r.y.toFixed(4),
      outerW: +r.width.toFixed(4), outerH: +r.height.toFixed(4),
      innerWidth: window.innerWidth, innerHeight: window.innerHeight,
      overscroll: getComputedStyle(outer).overscrollBehavior,
      scrollable: outer.scrollHeight > outer.clientHeight,
      docScrollH: document.documentElement.scrollHeight,
      scrollY: window.scrollY,
      pointerEvents: getComputedStyle(outer).pointerEvents,
      supports: CSS.supports('overscroll-behavior', 'contain'),
    };
  },
  'css-example-158': () => {
    const input = document.querySelector('#input');
    const ta = document.querySelector('#textarea');
    const cs = getComputedStyle(input);
    return {
      inputW: +input.getBoundingClientRect().width.toFixed(4),
      inputCssW: cs.width,
      maxW: cs.maxWidth, minW: cs.minWidth,
      boxSizing: cs.boxSizing,
      padding: cs.padding, border: cs.borderWidth,
      taH: +ta.getBoundingClientRect().height.toFixed(4),
    };
  },
  'css-example-131': () => {
    const r = (s) => { const el = document.querySelector(s); const x = el.getBoundingClientRect(); return { w: +x.width.toFixed(4), h: +x.height.toFixed(4), cssW: getComputedStyle(el).width, cssH: getComputedStyle(el).height }; };
    return { a: r('.clip'), b: r('.hidden') };
  },
  'css-example-132': () => {
    const sw = [...document.querySelectorAll('.sw')].map((el) => { const x = el.getBoundingClientRect(); return { w: +x.width.toFixed(4), h: +x.height.toFixed(4), x: +x.x.toFixed(4) }; });
    return { swatches: sw };
  },
  'css-example-133': () => {
    const sw = [...document.querySelectorAll('.sw')].map((el) => { const x = el.getBoundingClientRect(); return { w: +x.width.toFixed(4), h: +x.height.toFixed(4) }; });
    return { swatches: sw };
  },
  'css-example-135': () => {
    const sw = [...document.querySelectorAll('.sw')].map((el) => { const x = el.getBoundingClientRect(); return { w: +x.width.toFixed(4), h: +x.height.toFixed(4) }; });
    return { swatches: sw };
  },
  'css-example-136': () => {
    const r = (s) => { const el = document.querySelector(s); const x = el.getBoundingClientRect(); return { w: +x.width.toFixed(4), h: +x.height.toFixed(4), cssW: getComputedStyle(el).width, cssH: getComputedStyle(el).height }; };
    return { stroke: r('#stroke') };
  },
  'css-example-137': () => {
    const r = (s) => { const el = document.querySelector(s); const x = el.getBoundingClientRect(); return { w: +x.width.toFixed(4), h: +x.height.toFixed(4), cssW: getComputedStyle(el).width, cssH: getComputedStyle(el).height }; };
    return { fade: r('#fade') };
  },
  'css-example-138': () => {
    const r = (s) => { const el = document.querySelector(s); const x = el.getBoundingClientRect(); return { w: +x.width.toFixed(4), h: +x.height.toFixed(4), cssW: getComputedStyle(el).width, cssH: getComputedStyle(el).height }; };
    return { blend: r('#blend') };
  },
  'css-example-139': () => {
    const r = (s) => { const el = document.querySelector(s); const x = el.getBoundingClientRect(); return { w: +x.width.toFixed(4), h: +x.height.toFixed(4), cssW: getComputedStyle(el).width, cssH: getComputedStyle(el).height }; };
    return { block: r('#block') };
  },
  'css-example-150': () => {
    const r = (s) => { const el = document.querySelector(s); const x = el.getBoundingClientRect(); return { w: +x.width.toFixed(4), h: +x.height.toFixed(4), cssW: getComputedStyle(el).width }; };
    return { bar: r('#bar') };
  },
  'css-example-153': () => {
    const r = (s) => { const el = document.querySelector(s); const x = el.getBoundingClientRect(); return { w: +x.width.toFixed(4), h: +x.height.toFixed(4), cssW: getComputedStyle(el).width, cssH: getComputedStyle(el).height }; };
    return { spinner: r('#spinner') };
  },
  'css-example-154': () => {
    const r = (s) => { const el = document.querySelector(s); const x = el.getBoundingClientRect(); return { w: +x.width.toFixed(4), h: +x.height.toFixed(4) }; };
    return { rep: r('#rep'), acc: r('#acc') };
  },
  'css-example-155': () => {
    const rail = document.querySelector('#rail');
    const x = rail.getBoundingClientRect();
    return { railW: +x.width.toFixed(4), cssW: getComputedStyle(rail).width, clientW: rail.clientWidth, scrollW: rail.scrollWidth };
  },
  'css-example-122': () => {
    const g = document.querySelector('.grid');
    const p = document.querySelector('.grid > p') || document.querySelector('p');
    const cells = [...g.children].map((el) => ({ tag: el.tagName, y: +el.getBoundingClientRect().y.toFixed(4), x: +el.getBoundingClientRect().x.toFixed(4) }));
    return { pX: +p.getBoundingClientRect().x.toFixed(4), pY: +p.getBoundingClientRect().y.toFixed(4), children: cells };
  },
  'css-example-124': () => {
    const s = document.querySelector('#small');
    return { smallW: +s.getBoundingClientRect().width.toFixed(4), cssW: getComputedStyle(s).width };
  },
  'css-example-126': () => {
    const b = document.querySelector('#badge');
    const stage = document.querySelector('.stage') || b.parentElement;
    return {
      badgeX: +b.getBoundingClientRect().x.toFixed(4),
      stageX: +stage.getBoundingClientRect().x.toFixed(4),
      delta: +(b.getBoundingClientRect().x - stage.getBoundingClientRect().x).toFixed(4),
      left: getComputedStyle(b).left,
    };
  },
  'css-example-127': () => {
    const side = document.querySelector('#side');
    return { sideY: +side.getBoundingClientRect().y.toFixed(4), top: getComputedStyle(side).top };
  },
};

const ids = Object.keys(MEASURE);

const browser = await chromium.connectOverCDP(CDP);
const pages = browser.contexts().flatMap((c) => c.pages());
const page = pages.find((p) => {
  try {
    const u = new URL(p.url());
    return u.hostname === '127.0.0.1' && Number(u.port) >= 19999 && Number(u.port) <= 65535;
  } catch {
    return false;
  }
});
page.setDefaultTimeout(15000);

await page.goto(OHOS_BOOTSTRAP_URL, { waitUntil: 'domcontentloaded' });
const catalog = await page.evaluate(() => window.__QFLI_OHOS_CATALOG__);
const urls = new Map(catalog.cases.map((c) => [c.id, c.url]));

const out = {};
for (const id of ids) {
  const url = urls.get(id);
  if (!url) {
    out[id] = { error: 'no url' };
    continue;
  }
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(200);
  await page.mouse.move(-1, -1);
  await page.waitForTimeout(60);
  try {
    out[id] = await page.evaluate(MEASURE[id]);
  } catch (e) {
    out[id] = { error: String(e).split('\n')[0].slice(0, 160) };
  }
}

console.log(JSON.stringify(out, null, 1));
writeFileSync(resolve(here, 'probe-native-measure.json'), JSON.stringify(out, null, 1), 'utf8');
await page.goto(OHOS_BOOTSTRAP_URL, { waitUntil: 'domcontentloaded' }).catch(() => {});
await browser.close();
