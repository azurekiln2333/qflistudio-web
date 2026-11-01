#!/usr/bin/env node
// Task-local (research-only) CSS baseline audit for 10-22-standalone-offline-ide.
//
// Read-only with respect to the repository: it imports the existing p6 markup
// oracle and the emitted catalogs, replays exactly the runner's cross-cutting
// checks (marker, page errors, offline guard, internal resource integrity) for
// the CSS examples only, and writes its report into THIS task's research dir.
// It never writes assets/content or the runner's canonical report path.
//
// Usage: node .trellis/tasks/10-22-standalone-offline-ide/research/css-baseline-audit.mjs
//        [--report <path>] [--language css|html|javascript]

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createServer } from 'node:http';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../../../..');

const args = process.argv.slice(2);
const reportIdx = args.indexOf('--report');
const reportPath =
  reportIdx >= 0 ? resolve(repo, args[reportIdx + 1]) : resolve(here, 'css-baseline-report.md');
const langIdx = args.indexOf('--language');
const language = langIdx >= 0 ? args[langIdx + 1] : 'css';

const { chromium } = await import(pathToFileURL(resolve(repo, 'node_modules/playwright/index.mjs')).href);
const markup = await import(pathToFileURL(resolve(repo, 'scripts/web_markup_assertions.mjs')).href);

const examplesDoc = JSON.parse(readFileSync(resolve(repo, 'assets/content/examples.json'), 'utf8'));
const tutorialsDoc = JSON.parse(readFileSync(resolve(repo, 'assets/content/tutorials.json'), 'utf8'));

const examples = examplesDoc.entries.filter((e) => e.language === language);

const lessonById = new Map();
for (const t of tutorialsDoc.entries) for (const l of t.lessons) lessonById.set(l.id, l);
const exampleByLesson = new Map();
for (const e of examplesDoc.entries) exampleByLesson.set(e.sourceLessonId, e);

// Structural mapping audit for the selected language.
const structural = [];
for (const ex of examples) {
  const lesson = lessonById.get(ex.sourceLessonId);
  if (!lesson) structural.push(`${ex.id}: missing lesson ${ex.sourceLessonId}`);
  if (!lessonById.has(ex.sourceLessonId)) continue;
  if (ex.type !== 'html') structural.push(`${ex.id}: type ${ex.type} != html`);
  if (exampleByLesson.get(ex.sourceLessonId)?.id !== ex.id)
    structural.push(`${ex.id}: lesson maps to a different example`);
}
const lessonBodies = new Map();
for (const ex of examples) {
  const lesson = lessonById.get(ex.sourceLessonId);
  if (!lesson) continue;
  const h = lesson.code.replace(/\s+/g, ' ').trim();
  if (lessonBodies.has(h)) structural.push(`${ex.id}: duplicate lesson body of ${lessonBodies.get(h)}`);
  else lessonBodies.set(h, ex.id);
}
// covered-id audit
const missingFromOracle = examples.filter((e) => !markup.COVERED_IDS.includes(e.id)).map((e) => e.id);

const browser = await chromium.launch();
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

const allowList = markup.MISSING_RESOURCE_ALLOWLIST;
const pathnameOf = (entry) => {
  const m = entry.match(/https?:\/\/\S+/);
  if (!m) return null;
  try {
    return new URL(m[0]).pathname;
  } catch {
    return null;
  }
};

const results = [];
for (const ex of examples) {
  const context = await browser.newContext();
  const page = await context.newPage();
  page.setDefaultTimeout(3000);
  const errors = [];
  const blocked = [];
  const resourceErrors = [];
  const checks = [];

  page.on('pageerror', (e) => errors.push(String(e).split('\n')[0]));
  page.on('console', (m) => {
    if (m.type() === 'error') errors.push(`console.error: ${m.text()}`);
  });
  page.on('response', (r) => {
    const proto = r.url().split(':', 1)[0];
    if (proto === 'data' || proto === 'blob' || proto === 'about') return;
    if (r.status() >= 400) resourceErrors.push(`HTTP ${r.status()} ${r.url()}`);
  });
  page.on('requestfailed', (r) => {
    const proto = r.url().split(':', 1)[0];
    if (proto === 'data' || proto === 'blob' || proto === 'about') return;
    let same = false;
    try {
      same = new URL(r.url()).origin === serverOrigin;
    } catch {
      same = false;
    }
    if (same) resourceErrors.push(`FAILED ${r.url()}`);
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

  try {
    currentHtml = ex.code;
    await page.goto(origin, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(250);
    const markerPresent = (await page.locator('#webforge-check').count()) === 1;
    checks.push({ name: 'check marker present', ok: markerPresent });
    const addCheck = (name, ok, detail = '') => checks.push({ name, ok: !!ok, detail });
    const handled = await markup.assertMarkupExample(page, ex, addCheck);
    if (!handled) checks.push({ name: 'markup oracle', ok: false, detail: `unhandled ${ex.id}` });
  } catch (e) {
    checks.push({ name: 'page load/setup', ok: false, detail: String(e).split('\n')[0] });
  }

  checks.push({ name: 'no external requests', ok: blocked.length === 0, detail: blocked.join(',') });
  const allowForId = allowList?.get?.(ex.id) || null;
  const unexpected = resourceErrors.filter((e) => {
    if (!allowForId) return true;
    const p = pathnameOf(e);
    return !(p && allowForId.includes(p));
  });
  checks.push({ name: 'no broken internal resources', ok: unexpected.length === 0, detail: unexpected.join(' | ') });

  const failed = checks.filter((c) => !c.ok);
  results.push({ id: ex.id, pass: failed.length === 0 && errors.length === 0, failed, errors, checks: checks.length });
  await page.close();
  await context.close();
}

await browser.close();
await new Promise((r) => server.close(r));

const passed = results.filter((r) => r.pass).length;
const failedCount = results.length - passed;
let md = `# CSS baseline audit (${language}) — task-local replay\n\n`;
md += `Date: ${new Date().toISOString()}\n\n`;
md += `Oracle: scripts/web_markup_assertions.mjs (unmodified). Examples: ${results.length}. Passed: ${passed}. Failed: ${failedCount}.\n\n`;
md += `Oracle coverage gaps (${language} ids not in COVERED_IDS): ${missingFromOracle.length}${missingFromOracle.length ? ' -> ' + missingFromOracle.join(', ') : ''}\n\n`;
md += `Structural mapping issues: ${structural.length}${structural.length ? '\n' + structural.map((s) => `- ${s}`).join('\n') : ''}\n\n`;
md += '| id | result | checks | first failure |\n| --- | --- | --- | --- |\n';
for (const r of results) {
  const f = r.errors.length
    ? `pageerror: ${r.errors[0]}`
    : r.failed.length
      ? `${r.failed[0].name}: ${(r.failed[0].detail || '').slice(0, 200)}`
      : '';
  md += `| ${r.id} | ${r.pass ? 'pass' : 'FAIL'} | ${r.checks} | ${f.replace(/\|/g, '\\|')} |\n`;
}
mkdirSync(dirname(reportPath), { recursive: true });
writeFileSync(reportPath, md, 'utf8');
console.log(md);
process.exit(failedCount === 0 && structural.length === 0 && missingFromOracle.length === 0 ? 0 : 1);
