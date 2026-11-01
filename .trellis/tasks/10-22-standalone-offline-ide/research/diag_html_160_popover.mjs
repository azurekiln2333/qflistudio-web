// Diagnostic for html-example-160: popover geometry, reachability and the
// close-button click, at desktop and phone-emulated sizes.
//
// Usage: node .trellis/tasks/10-22-standalone-offline-ide/research/diag_html_160_popover.mjs
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from 'node:http';
import { chromium } from 'playwright';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../../../..');
const docs = JSON.parse(readFileSync(resolve(here, 'html-expansion-documents.json'), 'utf8'));
const doc = docs.find((d) => d.id === 'html-example-160');
if (!doc) throw new Error('html-example-160 not in dump');
const hasMeta = doc.code.includes('name="viewport"');

let current = '';
const server = createServer((req, res) => {
  res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
  res.end(current);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const origin = `http://127.0.0.1:${server.address().port}/`;

const contexts = [
  { name: 'desktop-1280', options: { viewport: { width: 1280, height: 720 } } },
  { name: 'phone-412', options: { viewport: { width: 412, height: 915 }, isMobile: true, deviceScaleFactor: 2 } },
];

const browser = await chromium.launch();
console.log(`document has viewport meta: ${hasMeta}`);

for (const ctx of contexts) {
  const context = await browser.newContext(ctx.options);
  const page = await context.newPage();
  page.setDefaultTimeout(3000);
  current = doc.code;
  await page.goto(origin, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(200);

  let openError = '';
  try {
    await page.locator('#open-help').click();
  } catch (e) {
    openError = String(e).split('\n')[0];
  }
  await page.waitForTimeout(150);

  const geom = await page.evaluate(() => {
    const pop = document.getElementById('help');
    const btn = document.getElementById('close-help');
    const box = (el) => {
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      return {
        x: Math.round(r.x),
        y: Math.round(r.y),
        w: Math.round(r.width),
        h: Math.round(r.height),
        display: cs.display,
        position: cs.position,
        visibility: cs.visibility,
      };
    };
    const popBox = box(pop);
    const btnBox = box(btn);
    const hit = document.elementFromPoint(
      btnBox.x + btnBox.w / 2,
      btnBox.y + btnBox.h / 2,
    );
    return {
      layoutWidth: window.innerWidth,
      visualWidth: window.visualViewport ? Math.round(window.visualViewport.width) : null,
      visualScale: window.visualViewport ? Number(window.visualViewport.scale.toFixed(3)) : null,
      popoverOpen: pop.matches(':popover-open'),
      pop: popBox,
      btn: btnBox,
      btnInsideLayout: btnBox.x >= 0 && btnBox.x + btnBox.w <= window.innerWidth,
      hitAtBtnCenter: hit ? `${hit.tagName}#${hit.id}` : null,
    };
  });

  let closeError = '';
  let closed = false;
  try {
    await page.locator('#close-help').click({ timeout: 3000 });
    closed = await page.locator('#help').evaluate((el) => !el.matches(':popover-open'));
  } catch (e) {
    closeError = String(e).split('\n').slice(0, 4).join(' | ');
  }

  console.log(`\n=== ${ctx.name} ===`);
  console.log(JSON.stringify(geom));
  console.log(`open click: ${openError || 'ok'}`);
  console.log(`close click: ${closeError ? 'TIMEOUT/ERROR -> ' + closeError : 'ok'}, closed=${closed}`);
  await context.close();
}

await browser.close();
await server.close();
