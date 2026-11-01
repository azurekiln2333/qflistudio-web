// Task-local repro/verify for the two OHOS HTML failures (135 picture art
// direction, 144 declarative shadow DOM host border).
//
// It runs the shipped oracle against the shipped documents in two host
// Chromium contexts:
//   * desktop  1280x720 (isMobile false)
//   * phone     412x915 (isMobile true, deviceScaleFactor 2) -- the ArkWeb case
//
// Phone emulation is what reproduces the OHOS result: without a viewport meta
// the layout viewport is 980px, so `matchMedia('(min-width: 600px)')` is true
// while <picture><source media> resolves against the physical viewport.
//
// Usage: node .trellis/tasks/10-22-standalone-offline-ide/research/verify_html_135_144.mjs
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createServer } from 'node:http';
import { chromium } from 'playwright';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../../../..');
const oracle = await import(pathToFileURL(resolve(repo, 'scripts/html_expansion_assertions.mjs')).href);
const docs = JSON.parse(readFileSync(resolve(here, 'html-expansion-documents.json'), 'utf8'));
const wanted = process.argv.slice(2);
const targets = docs.filter((d) => (wanted.length ? wanted : ['html-example-135', 'html-example-144', 'html-example-160']).includes(d.id));

let current = '';
const server = createServer((req, res) => {
  res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
  res.end(current);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const origin = `http://127.0.0.1:${server.address().port}/`;

const contexts = [
  { name: 'desktop-1280', options: { viewport: { width: 1280, height: 720 } } },
  {
    name: 'phone-412',
    options: { viewport: { width: 412, height: 915 }, isMobile: true, deviceScaleFactor: 2 },
  },
];

const browser = await chromium.launch();
let failures = 0;

for (const ctx of contexts) {
  for (const doc of targets) {
    const context = await browser.newContext(ctx.options);
    const page = await context.newPage();
    page.setDefaultTimeout(4000);
    const checks = [];
    const addCheck = (name, ok, detail = '') => checks.push({ name, ok: !!ok, detail: String(detail) });
    const errors = [];
    page.on('pageerror', (e) => errors.push(String(e).split('\n')[0]));
    current = doc.code;
    await page.goto(origin, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(250);
    try {
      const handled = await oracle.assertExpansionExample(page, doc, addCheck);
      if (!handled) addCheck('handled', false, doc.id);
    } catch (e) {
      addCheck('oracle threw', false, String(e).split('\n')[0]);
    }
    const env = await page.evaluate(() => ({
      innerWidth: window.innerWidth,
      visual: window.visualViewport ? Math.round(window.visualViewport.width) : null,
      wide: matchMedia('(min-width: 600px)').matches,
      medium: matchMedia('(min-width: 300px)').matches,
      naturalWidth: document.getElementById('fallback') ? document.getElementById('fallback').naturalWidth : null,
      border: document.getElementById('card') ? getComputedStyle(document.getElementById('card')).borderTopWidth : null,
    }));
    const failed = checks.filter((c) => !c.ok);
    failures += failed.length;
    console.log(
      `${ctx.name.padEnd(12)} ${doc.id}  ${failed.length === 0 ? 'PASS' : 'FAIL'}  checks=${checks.length}  ` +
        `innerWidth=${env.innerWidth} visual=${env.visual} wide=${env.wide} medium=${env.medium} ` +
        `naturalWidth=${env.naturalWidth} hostBorder=${env.border}` +
        (errors.length ? `  ERR=${errors[0]}` : ''),
    );
    for (const f of failed) console.log(`    - ${f.name}: ${f.detail}`);
    await context.close();
  }
}

await browser.close();
await server.close();
process.exit(failures === 0 ? 0 : 1);
