// Diagnose why the runner's page reports different computed colours than a
// plain probe: replicate the runner's per-case setup step by step.
//
// Reuses the single native page; never creates contexts/pages; browser.close()
// drops only the CDP transport.
import { resolve, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../../../..');
const CDP = process.env.NATIVE_CDP || 'http://127.0.0.1:9222';

const { chromium } = await import(pathToFileURL(resolve(repo, 'node_modules/playwright/index.mjs')).href);
const { OHOS_BOOTSTRAP_URL } = await import(pathToFileURL(resolve(repo, 'scripts/catalog_device_contract.mjs')).href);

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
const context = page.context();

await page.goto(OHOS_BOOTSTRAP_URL, { waitUntil: 'domcontentloaded' });
const catalog = await page.evaluate(() => window.__QFLI_OHOS_CATALOG__);
const url = catalog.cases.find((c) => c.id === 'css-example-035').url;
const origin = new URL(url).origin;

const read = () =>
  page.evaluate(() => {
    const b = document.querySelector('.btn');
    const cs = getComputedStyle(b);
    return {
      bg: cs.backgroundColor,
      marginLeft: cs.marginLeft,
      cls: b.className,
      matchesDisabled: b.matches('[disabled]'),
      firstBtnBg: cs.backgroundColor,
      allBtn: [...document.querySelectorAll('.btn')].map((e) => getComputedStyle(e).backgroundColor),
      colorScheme: getComputedStyle(document.documentElement).colorScheme,
      dpr: devicePixelRatio,
      scale: window.visualViewport ? window.visualViewport.scale : null,
    };
  });

// Step 1: plain navigation (what a naive probe does).
await page.goto(url, { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(250);
console.log('A plain          :', JSON.stringify(await read()));

// Step 2: add the runner's offline-guard route, then reload.
await page.route('**/*', (route) => {
  const u = route.request().url();
  const proto = u.split(':', 1)[0];
  if (proto === 'data' || proto === 'blob' || proto === 'about') return route.continue();
  let same = false;
  try {
    same = new URL(u).origin === origin;
  } catch {
    same = false;
  }
  return same ? route.continue() : route.abort();
});
await page.goto(url, { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(250);
console.log('B with route     :', JSON.stringify(await read()));

// Step 3: also grant clipboard permissions like the runner does per case.
await context.grantPermissions(['clipboard-read', 'clipboard-write']).catch(() => {});
await page.goto(url, { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(250);
console.log('C route + perms  :', JSON.stringify(await read()));

// Step 4: what the button actually is after the runner's CSS-probe order.
await page.goto(url, { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(250);
const detail = await page.evaluate(() => {
  const btn = document.querySelector('.btn');
  const cs = getComputedStyle(btn);
  const probe = document.createElement('code');
  probe.style.color = '#1a73e8';
  document.body.appendChild(probe);
  const probeColor = getComputedStyle(probe).color;
  probe.remove();
  return {
    btnBg: cs.backgroundColor,
    btnBgRaw: cs.getPropertyValue('background-color'),
    probeColor,
    sameAsProbe: cs.backgroundColor === probeColor,
    bodyStyleAttr: document.body.getAttribute('style'),
    forcedColors: matchMedia('(forced-colors: active)').matches,
    prefersDark: matchMedia('(prefers-color-scheme: dark)').matches,
  };
});
console.log('D parse check    :', JSON.stringify(detail));

await page.unrouteAll({ behavior: 'wait' }).catch(() => {});
await page.goto(OHOS_BOOTSTRAP_URL, { waitUntil: 'domcontentloaded' }).catch(() => {});
await browser.close();
