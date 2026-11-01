// Task-local browser harness for the 60 HTML expansion documents.
//
// It applies the real oracle (scripts/html_expansion_assertions.mjs) to the real
// delivered documents, under the same offline rules as scripts/run_examples.mjs:
//   * every non-loopback request is blocked and reported;
//   * same-origin HTTP >= 400 / requestfailed is a failure;
//   * the webforge-check marker must be present exactly once;
//   * every id must produce >= 3 checks and zero failures.
//
// It deliberately does NOT touch scripts/run_examples.mjs, assets/content/*.json,
// scripts/emit_content.py or the historical reports.
//
// Usage: node .trellis/tasks/10-22-standalone-offline-ide/research/html_expansion_harness.mjs [--limit N]

import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createServer } from 'node:http';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../../../..');

const { chromium } = await import('playwright');
const oracle = await import(pathToFileURL(resolve(repo, 'scripts/html_expansion_assertions.mjs')).href);

const docs = JSON.parse(readFileSync(resolve(here, 'html-expansion-documents.json'), 'utf8'));
const limitIdx = process.argv.indexOf('--limit');
const limit = limitIdx >= 0 ? Number(process.argv[limitIdx + 1]) : Infinity;
const targets = docs.slice(0, limit);

let currentHtml = '';
const server = createServer((req, res) => {
  const path = (req.url || '/').split('?')[0];
  if (path === '/' || path === '/index.html') {
    res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
    res.end(currentHtml);
    return;
  }
  res.writeHead(404, { 'content-type': 'text/plain' });
  res.end('not found');
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const origin = `http://127.0.0.1:${server.address().port}/`;
const serverOrigin = new URL(origin).origin;

const browser = await chromium.launch();
const results = [];

for (const doc of targets) {
  const context = await browser.newContext();
  const page = await context.newPage();
  page.setDefaultTimeout(4000);
  const checks = [];
  const errors = [];
  const blocked = [];
  const resourceErrors = [];

  page.on('console', (m) => {
    if (m.type() === 'error') errors.push(`console: ${m.text()}`);
  });
  page.on('pageerror', (e) => errors.push(`pageerror: ${String(e).split('\n')[0]}`));
  page.on('response', (r) => {
    const proto = r.url().split(':', 1)[0];
    if (proto === 'data' || proto === 'blob' || proto === 'about') return;
    if (r.status() >= 400) resourceErrors.push(`HTTP ${r.status()} ${r.url()}`);
  });
  page.on('requestfailed', (r) => {
    const url = r.url();
    const proto = url.split(':', 1)[0];
    if (proto === 'data' || proto === 'blob' || proto === 'about') return;
    let same = false;
    try {
      same = new URL(url).origin === serverOrigin;
    } catch {
      same = false;
    }
    if (same) resourceErrors.push(`FAILED ${url}`);
  });
  await page.route('**/*', (route) => {
    const url = route.request().url();
    const proto = url.split(':', 1)[0];
    if (proto === 'data' || proto === 'blob' || proto === 'about') return route.continue();
    let same = false;
    try {
      same = new URL(url).origin === serverOrigin;
    } catch {
      same = false;
    }
    if (same) return route.continue();
    blocked.push(`${route.request().resourceType()}: ${url}`);
    return route.abort();
  });

  const addCheck = (name, ok, detail = '') =>
    checks.push({ name, ok: !!ok, detail: String(detail) });

  try {
    currentHtml = doc.code;
    await page.goto(origin, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(250);

    const markers = await page.locator('#webforge-check').count();
    addCheck('check marker present', markers === 1, `count=${markers}`);

    const handled = await oracle.assertExpansionExample(page, doc, addCheck);
    if (!handled) addCheck('expansion oracle handled id', false, doc.id);
  } catch (e) {
    addCheck('page load/setup', false, String(e).split('\n')[0]);
  }

  addCheck('no external requests', blocked.length === 0, blocked.join(','));
  addCheck('no broken internal resources', resourceErrors.length === 0, resourceErrors.join(' | '));
  addCheck('at least 3 semantic checks', checks.length >= 4, `${checks.length} checks`);

  const failed = checks.filter((c) => !c.ok);
  results.push({
    id: doc.id,
    title: doc.title,
    pass: failed.length === 0 && errors.length === 0,
    checks: checks.length,
    failed,
    errors,
  });

  await page.close();
  await context.close();
}

await browser.close();
await new Promise((r) => server.close(r));

const passed = results.filter((r) => r.pass).length;
const failed = results.length - passed;
const totalChecks = results.reduce((s, r) => s + r.checks, 0);

let md = '# HTML expansion browser verification\n\n';
md += `Documents: ${results.length}. Assertions: ${totalChecks}. Passed: ${passed}. Failed: ${failed}.\n\n`;
md += '| id | topic | result | checks | first failure |\n| --- | --- | --- | --- | --- |\n';
for (const r of results) {
  const first = r.errors.length
    ? r.errors[0]
    : r.failed.length
      ? `${r.failed[0].name}: ${r.failed[0].detail}`
      : '';
  md += `| ${r.id} | ${r.title.replace(/\|/g, '\\|')} | ${r.pass ? 'pass' : 'FAIL'} | ${r.checks} | ${first
    .replace(/\|/g, '\\|')
    .slice(0, 160)} |\n`;
}
if (failed) {
  md += '\n## Failures\n\n';
  for (const r of results.filter((x) => !x.pass)) {
    md += `### ${r.id} — ${r.title}\n\n`;
    for (const f of r.failed) md += `- ${f.name} (ok=${f.ok}) ${f.detail}\n`;
    for (const e of r.errors) md += `- error: ${e}\n`;
    md += '\n';
  }
}

writeFileSync(resolve(here, 'html-expansion-verification.md'), md, 'utf8');
console.log(md.split('\n').slice(0, 6).join('\n'));
if (failed) {
  for (const r of results.filter((x) => !x.pass)) {
    console.log(`FAIL ${r.id}: ${r.failed.map((f) => `${f.name}=${f.detail}`).join(' | ')}${r.errors.length ? ' ERR ' + r.errors[0] : ''}`);
  }
}
process.exit(failed === 0 ? 0 : 1);
