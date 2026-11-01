// Probe the ACTUAL packaged CSS cases on the native ArkWeb page.
//
// Reuses the single existing page, navigates it to the packaged case URL taken
// from window.__QFLI_OHOS_CATALOG__ (the same source the runner uses), and never
// creates contexts/pages or closes the page. browser.close() only drops the CDP
// transport, matching scripts/run_examples.mjs.
//
// Usage:
//   node probe_css_cases.mjs <id>[,<id>...] [--json]
import { resolve, dirname } from 'node:path';
import { writeFileSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../../../..');
const CDP = process.env.NATIVE_CDP || 'http://127.0.0.1:9222';

const ids = (process.argv[2] || '').split(',').map((s) => s.trim()).filter(Boolean);
if (!ids.length) {
  console.error('usage: node probe_css_cases.mjs <id>[,<id>...]');
  process.exit(1);
}

const { chromium } = await import(pathToFileURL(resolve(repo, 'node_modules/playwright/index.mjs')).href);
const browser = await chromium.connectOverCDP(CDP);

const pages = browser.contexts().flatMap((c) => c.pages());
const candidates = pages.filter((p) => {
  try {
    const url = new URL(p.url());
    return url.hostname === '127.0.0.1' && Number(url.port) >= 19999 && Number(url.port) <= 65535;
  } catch {
    return false;
  }
});
if (candidates.length !== 1) {
  console.error(`expected exactly one native test target, got ${candidates.length}`);
  await browser.close();
  process.exit(2);
}
const page = candidates[0];
page.setDefaultTimeout(15000);

// Packaged catalog bootstrap gives the real per-case URLs.
const bootstrapUrl = page.url();
await page.goto(bootstrapUrl, { waitUntil: 'domcontentloaded' });
const catalog = await page.evaluate(() => window.__QFLI_OHOS_CATALOG__);
const caseUrls = new Map();
const collect = (node) => {
  if (!node || typeof node !== 'object') return;
  if (Array.isArray(node)) {
    for (const item of node) collect(item);
    return;
  }
  if (typeof node.id === 'string' && typeof node.url === 'string') caseUrls.set(node.id, node.url);
  for (const value of Object.values(node)) collect(value);
};
collect(catalog);

const out = {};
for (const id of ids) {
  const url = caseUrls.get(id);
  if (!url) {
    out[id] = { error: 'no packaged url in catalog' };
    continue;
  }
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(180);
  out[id] = await page.evaluate(() => {
    const cs = (sel, props) => {
      const el = document.querySelector(sel);
      if (!el) return { error: 'no element' };
      const s = getComputedStyle(el);
      const o = {};
      for (const p of props) o[p] = s.getPropertyValue(p).trim();
      return o;
    };
    const rect = (sel) => {
      const el = document.querySelector(sel);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return {
        x: +r.x.toFixed(4), y: +r.y.toFixed(4), w: +r.width.toFixed(4), h: +r.height.toFixed(4),
        cssW: getComputedStyle(el).width, cssH: getComputedStyle(el).height,
      };
    };
    return {
      innerWidth,
      innerHeight,
      dpr: devicePixelRatio,
      scale: window.visualViewport ? window.visualViewport.scale : null,
      viewportMeta: (document.querySelector('meta[name="viewport"]') || {}).content || null,
      body: { contentW: document.body.clientWidth, scrollW: document.documentElement.scrollWidth },
    };
  });
}

console.log(JSON.stringify(out, null, 1));
writeFileSync(resolve(here, 'probe-css-cases.json'), JSON.stringify({ bootstrapUrl, out }, null, 1), 'utf8');
await browser.close(); // transport only
