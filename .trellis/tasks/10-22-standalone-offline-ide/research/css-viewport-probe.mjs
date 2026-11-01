#!/usr/bin/env node
// Task-local probe: does the existing CSS oracle depend on the host viewport?
//
// The runner never sets a viewport, so Playwright's default 1280x720 is used.
// On an OHOS ArkWeb build the catalog harness will present a phone-sized
// viewport instead. This probe replays the UNMODIFIED oracle at several
// viewports and reports which examples only pass at desktop width.
//
// Usage: node .trellis/tasks/10-22-standalone-offline-ide/research/css-viewport-probe.mjs

import { readFileSync, writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createServer } from 'node:http';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../../../..');

const { chromium } = await import(pathToFileURL(resolve(repo, 'node_modules/playwright/index.mjs')).href);
const markup = await import(pathToFileURL(resolve(repo, 'scripts/web_markup_assertions.mjs')).href);

const doc = JSON.parse(readFileSync(resolve(repo, 'assets/content/examples.json'), 'utf8'));
const examples = doc.entries.filter((e) => e.language === 'css');

const VIEWPORTS = [
  { name: 'desktop', width: 1280, height: 720 },
  { name: 'tablet', width: 800, height: 1180 },
  { name: 'phone', width: 412, height: 915 },
];

const browser = await chromium.launch();
let currentHtml = '';
const server = createServer((req, res) => {
  const p = (req.url || '/').split('?')[0];
  if (p === '/' || p === '/index.html') {
    res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
    res.end(currentHtml);
    return;
  }
  res.writeHead(404);
  res.end('nf');
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const origin = `http://127.0.0.1:${server.address().port}/`;

const matrix = new Map(); // id -> { viewportName: failures[] }

for (const vp of VIEWPORTS) {
  for (const ex of examples) {
    const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
    const page = await context.newPage();
    page.setDefaultTimeout(3000);
    const checks = [];
    try {
      currentHtml = ex.code;
      await page.goto(origin, { waitUntil: 'domcontentloaded', timeout: 15000 });
      await page.waitForTimeout(250);
      const addCheck = (name, ok, detail = '') => checks.push({ name, ok: !!ok, detail });
      await markup.assertMarkupExample(page, ex, addCheck);
    } catch (e) {
      checks.push({ name: 'setup', ok: false, detail: String(e).split('\n')[0] });
    }
    if (!matrix.has(ex.id)) matrix.set(ex.id, {});
    matrix.get(ex.id)[vp.name] = checks.filter((c) => !c.ok).map((c) => `${c.name} [${c.detail}]`);
    await page.close();
    await context.close();
  }
}

await browser.close();
await new Promise((r) => server.close(r));

let md = '# Existing CSS oracle vs viewport\n\n';
md += 'Unmodified oracle, three viewports. A row is a real portability defect when it\n';
md += 'passes on desktop but fails on a narrower viewport: the acceptance runner and the\n';
md += 'OHOS catalog harness would then disagree about the same shipped document.\n\n';
md += '| id | desktop | tablet | phone | failing checks (narrow) |\n| --- | --- | --- | --- | --- |\n';
let narrowFailures = 0;
for (const [id, byVp] of matrix) {
  const d = byVp.desktop || [];
  const t = byVp.tablet || [];
  const p = byVp.phone || [];
  const fails = d.length || !t.length ? t.length + p.length : t.length + p.length;
  if (fails) narrowFailures++;
  md += `| ${id} | ${d.length ? 'FAIL' : 'pass'} | ${t.length ? 'FAIL' : 'pass'} | ${p.length ? 'FAIL' : 'pass'} | ${[...new Set([...t, ...p])].slice(0, 4).join('<br>').replace(/\|/g, '\\|')} |\n`;
}
md = md.replace(
  'A row is a real portability defect when it',
  `Examples that fail at a narrow viewport: ${narrowFailures}/${matrix.size}.\n\nA row is a real portability defect when it`,
);
writeFileSync(resolve(here, 'css-viewport-probe.md'), md, 'utf8');
console.log(md.split('\n').slice(0, 14).join('\n'));
console.log('...');
console.log(md.split('\n').filter((l) => l.includes('FAIL')).slice(0, 25).join('\n'));
