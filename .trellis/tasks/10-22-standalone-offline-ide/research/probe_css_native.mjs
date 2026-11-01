// Native ArkWeb probe: connect over CDP, reuse the ONE existing page, never
// create a context/page, never close the page (browser.close() only drops the
// CDP transport, exactly like scripts/run_examples.mjs does).
//
// Usage:
//   node probe_css_native.mjs --list                 enumerate targets only
//   node probe_css_native.mjs --case 129             probe one css-example id
//   node probe_css_native.mjs --probe '<json>'       run a named probe group
import { resolve, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../../../..');
const CDP = process.env.NATIVE_CDP || 'http://127.0.0.1:9222';

const args = process.argv.slice(2);
const argValue = (name, fallback = '') => {
  const i = args.indexOf(name);
  return i >= 0 && args[i + 1] ? args[i + 1] : fallback;
};

const { chromium } = await import(pathToFileURL(resolve(repo, 'node_modules/playwright/index.mjs')).href);
const browser = await chromium.connectOverCDP(CDP);
const version = browser.version();
const contexts = browser.contexts();
const pages = contexts.flatMap((c) => c.pages());

if (args.includes('--list')) {
  console.log(JSON.stringify({
    version,
    contexts: contexts.length,
    pages: pages.map((p) => ({ url: p.url().slice(0, 140) })),
  }, null, 1));
  await browser.close(); // transport only
  process.exit(0);
}

// Reuse the single existing native page: same rule the runner uses.
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

// Baseline environment facts the CSS oracle depends on.
const env = await page.evaluate(() => {
  const probe = document.createElement('div');
  probe.style.cssText = 'position:absolute;left:-9999px;visibility:hidden';
  document.body.appendChild(probe);
  const measureFont = (px) => {
    const el = document.createElement('span');
    el.style.cssText = `font-size:${px}px;line-height:normal;position:absolute;visibility:hidden`;
    el.textContent = 'MMMM';
    document.body.appendChild(el);
    const h = el.getBoundingClientRect().height;
    el.remove();
    return h;
  };
  const fontSizes = [4, 5, 6, 7, 8, 9, 10, 12, 16, 20, 40];
  const measured = Object.fromEntries(fontSizes.map((px) => [px, +measureFont(px).toFixed(4)]));
  const overflowProbe = document.createElement('div');
  overflowProbe.style.cssText = 'position:absolute;left:-9999px;width:100px;height:50px;overflow:auto';
  const inner = document.createElement('div');
  inner.style.cssText = 'height:200px';
  overflowProbe.appendChild(inner);
  document.body.appendChild(overflowProbe);
  const gutter = overflowProbe.offsetWidth - overflowProbe.clientWidth;
  overflowProbe.remove();
  probe.remove();
  return {
    innerWidth,
    innerHeight,
    devicePixelRatio,
    visualViewportScale: window.visualViewport ? window.visualViewport.scale : null,
    documentClientWidth: document.documentElement.clientWidth,
    docScrollWidth: document.documentElement.scrollWidth,
    viewportMeta: (document.querySelector('meta[name="viewport"]') || {}).content || null,
    fontMetrics: measured,
    scrollbarGutterWidth: gutter,
    supports: {
      hyphens: CSS.supports('hyphens', 'auto'),
      overflowWrapAnywhere: CSS.supports('overflow-wrap', 'anywhere'),
      textBoxTrim: CSS.supports('text-box-trim', 'trim-both'),
      textBoxEdge: CSS.supports('text-box-edge', 'cap alphabetic'),
      overscrollBehavior: CSS.supports('overscroll-behavior', 'contain'),
      scrollbarGutterStable: CSS.supports('scrollbar-gutter', 'stable'),
      marginInline: CSS.supports('margin-inline', '24px'),
      cqw: CSS.supports('font-size', '2.5cqw'),
      textEmphasis: CSS.supports('text-emphasis-style', 'dot'),
      minusVar: CSS.supports('font-size', 'min(10px, 2vw)'),
    },
    ua: navigator.userAgent.slice(0, 200),
  };
});

console.log(JSON.stringify(env, null, 1));
await browser.close(); // disconnect transport only; the native page stays alive
