// Negative control: serve html-example-160 with the popover deliberately pushed
// off-screen and confirm the new oracle check fails (the check is discriminating,
// not tautological) while the Escape light-dismiss path still passes.
//
// Usage: node .trellis/tasks/10-22-standalone-offline-ide/research/negative_html_160.mjs
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createServer } from 'node:http';
import { chromium } from 'playwright';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../../../..');
const oracle = await import(pathToFileURL(resolve(repo, 'scripts/html_expansion_assertions.mjs')).href);
const docs = JSON.parse(readFileSync(resolve(here, 'html-expansion-documents.json'), 'utf8'));
const doc = docs.find((d) => d.id === 'html-example-160');

// Push the fixed popover 400px below the viewport (a scaled-layout-viewport
// position is what the real failure looked like) while keeping the meta.
const broken = { ...doc, code: doc.code.replace('#help { inset: auto 12px 12px;', '#help { inset: auto 12px -400px;') };
if (broken.code === doc.code) throw new Error('negative-control patch did not apply');

let current = '';
const server = createServer((req, res) => {
  res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
  res.end(current);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const origin = `http://127.0.0.1:${server.address().port}/`;

const browser = await chromium.launch();
const context = await browser.newContext({ viewport: { width: 412, height: 915 }, isMobile: true, deviceScaleFactor: 2 });
const page = await context.newPage();
page.setDefaultTimeout(3000);
const checks = [];
const addCheck = (name, ok, detail = '') => checks.push({ name, ok: !!ok, detail: String(detail) });
current = broken.code;
await page.goto(origin, { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(200);
let threw = '';
try {
  await oracle.assertExpansionExample(page, broken, addCheck);
} catch (e) {
  threw = String(e).split('\n')[0];
}
for (const c of checks) console.log(`${c.ok ? 'ok  ' : 'FAIL'} ${c.name}${c.detail ? ' | ' + c.detail : ''}`);
console.log('threw:', threw || 'no');
await browser.close();
await server.close();
process.exit(threw ? 0 : 1);