#!/usr/bin/env node
// Task-local verification harness for the CSS expansion module.
//
// It reproduces exactly what `scripts/emit_content.py` would do with
// `curriculum/css_expansion.py` (CSS_EXTRA -> example documents with the
// runner's injected `webforge-check` marker), then:
//
//   1. schema / policy checks on the 60 authored lessons,
//   2. executes each generated example against the NEW oracle module
//      (`scripts/css_expansion_assertions.mjs`) at a pinned viewport,
//   3. replays the same oracle at a second viewport to prove the oracle is not
//      host-width dependent,
//   4. enforces the offline guard + internal-resource integrity like the runner.
//
// Nothing here writes repository files. Report: research/css-expansion-verify.md
//
// Usage:
//   node .../css-expansion-verify.mjs                 # full run
//   node .../css-expansion-verify.mjs --only 101,105  # subset (first-number index)
//   node .../css-expansion-verify.mjs --dump 101      # dump computed styles
//   node .../css-expansion-verify.mjs --schema        # schema checks only

import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createServer } from 'node:http';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../../../..');

const args = process.argv.slice(2);
const flag = (name) => {
  const i = args.indexOf(name);
  return i >= 0 ? args[i + 1] : null;
};

// --- 1. Export the authored lessons through the same path emit_content uses ---
function loadLessons() {
  const script = `
import json, sys
sys.path.insert(0, ${JSON.stringify(resolve(repo, 'scripts'))})
from curriculum import css_expansion
print(json.dumps([
    {k: v for k, v in lesson.items()} for lesson in css_expansion.CSS_EXTRA
], ensure_ascii=False))
`;
  const out = execFileSync('python', ['-X', 'utf8', '-c', script], {
    cwd: repo,
    encoding: 'utf8',
    maxBuffer: 64 * 1024 * 1024,
  });
  return JSON.parse(out);
}

// Same transform as emit_content.example_document() for the css language.
function exampleDocument(lesson) {
  const code = lesson.code;
  const marker = 'webforge-check';
  const doc = code.includes('</body>')
    ? code.replace('</body>', `  <output id="${marker}" hidden>ok</output>\n</body>`)
    : code + `\n<output id="${marker}" hidden>ok</output>`;
  return { code: doc, marker };
}

// --- 2. Schema / policy checks --------------------------------------------
function schemaChecks(lessons) {
  const issues = [];
  if (lessons.length !== 60) issues.push(`CSS_EXTRA has ${lessons.length} entries, expected 60`);
  const titles = new Map();
  const bodies = new Map();
  const required = ['t', 'level', 'obj', 'pre', 'con', 'explain', 'code', 'out', 'pit', 'ex'];
  const levels = new Set(['beginner', 'intermediate', 'advanced']);
  let minExplain = Infinity;
  let minCode = Infinity;
  lessons.forEach((l, i) => {
    const idx = 101 + i;
    const at = `entry ${idx}`;
    for (const k of required) if (!(k in l)) issues.push(`${at}: missing key ${k}`);
    if (typeof l.t !== 'string' || !l.t.trim()) issues.push(`${at}: empty title`);
    else if (titles.has(l.t)) issues.push(`${at}: duplicate title of ${titles.get(l.t)}`);
    else titles.set(l.t, idx);
    if (!levels.has(l.level)) issues.push(`${at}: bad level ${l.level}`);
    if (typeof l.obj !== 'string' || l.obj.length < 8) issues.push(`${at}: objective too short`);
    if (!Array.isArray(l.pre)) issues.push(`${at}: pre is not a list`);
    if (!Array.isArray(l.con) || l.con.length < 4 || l.con.length > 7)
      issues.push(`${at}: concepts ${l.con?.length} not in 4..7`);
    if (new Set(l.con || []).size !== (l.con || []).length) issues.push(`${at}: duplicate concepts`);
    if (typeof l.explain !== 'string' || l.explain.length < 180)
      issues.push(`${at}: explain ${l.explain?.length} < 180 chars`);
    minExplain = Math.min(minExplain, l.explain?.length || 0);
    if (!Array.isArray(l.pit) || l.pit.length !== 3) issues.push(`${at}: pitfalls != 3`);
    if (!Array.isArray(l.ex) || l.ex.length < 1) issues.push(`${at}: no exercise`);
    for (const ex of l.ex || []) {
      if (!Array.isArray(ex) || ex.length !== 3 || ex.some((s) => typeof s !== 'string' || !s.trim()))
        issues.push(`${at}: exercise is not a (prompt, hint, answer) triple`);
    }
    if (typeof l.out !== 'string' || l.out.length < 8) issues.push(`${at}: output too short`);
    // Code document rules
    const c = l.code || '';
    if (!/^<!doctype html>/i.test(c)) issues.push(`${at}: code missing doctype`);
    if (!/lang="zh-CN"/.test(c)) issues.push(`${at}: code missing lang="zh-CN"`);
    if (!/<meta charset="utf-8">/i.test(c)) issues.push(`${at}: code missing charset`);
    if (!/<\/html>\s*$/.test(c.trim() + '\n') && !/<html[\s\S]*<\/html>/i.test(c))
      issues.push(`${at}: code is not a complete document`);
    if (/webforge-check/.test(c)) issues.push(`${at}: code must NOT contain the injected marker`);
    if (/<script/i.test(c)) issues.push(`${at}: CSS lesson must not need <script>`);
    if (/(src|href)\s*=\s*["']?(https?:)?\/\//i.test(c))
      issues.push(`${at}: code references an external URL`);
    if (!/<style>/.test(c)) issues.push(`${at}: code has no inline <style>`);
    minCode = Math.min(minCode, c.length);
    if (bodies.has(c)) issues.push(`${at}: identical code body to ${bodies.get(c)}`);
    else bodies.set(c, idx);
  });
  return { issues, minExplain, minCode, distinct: bodies.size };
}

// --- 3. Execution ----------------------------------------------------------
async function run() {
  const lessons = loadLessons();
  const schema = schemaChecks(lessons);
  const report = { schema, rows: [], issues: [] };
  if (args.includes('--schema')) return { lessons, report, schema };

  const markup = await import(pathToFileURL(resolve(repo, 'scripts/css_expansion_assertions.mjs')).href).catch(
    (e) => ({ __error: String(e).split('\n')[0] }),
  );
  const { chromium } = await import(pathToFileURL(resolve(repo, 'node_modules/playwright/index.mjs')).href);
  const browser = await chromium.launch();

  const only = flag('--only');
  const wanted = only ? new Set(only.split(',').map((s) => Number(s.trim()))) : null;

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
  const serverOrigin = new URL(origin).origin;

  const dump = flag('--dump');

  for (let i = 0; i < lessons.length; i++) {
    const n = 101 + i;
    if (wanted && !wanted.has(n)) continue;
    const lesson = lessons[i];
    const id = `css-example-${n}`;
    const { code } = exampleDocument(lesson);

    const attempts = [];
    const altSpec = (process.env.CSS_VERIFY_ALT || '1280x900').split('x').map(Number);
    for (const vp of [
      { name: 'pinned', width: 960, height: 720 },
      { name: 'alt', width: altSpec[0], height: altSpec[1] },
    ]) {
      const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
      const page = await context.newPage();
      page.setDefaultTimeout(3000);
      const checks = [];
      const errors = [];
      const blocked = [];
      const resourceErrors = [];
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

      if (dump) {
        currentHtml = code;
        await page.goto(origin, { waitUntil: 'domcontentloaded', timeout: 15000 });
        await page.waitForTimeout(250);
        const info = await page.evaluate(() => {
          const out = {};
          for (const el of document.querySelectorAll('body *')) {
            if (el.id === 'webforge-check') continue;
            const cs = getComputedStyle(el);
            const r = el.getBoundingClientRect();
            const key = `${el.tagName.toLowerCase()}${el.id ? '#' + el.id : ''}${el.className ? '.' + String(el.className).trim().split(/\s+/).join('.') : ''}`;
            const props = {};
            for (const p of [
              'display', 'color', 'background-color', 'background-image', 'font-size', 'font-weight', 'line-height',
              'width', 'height', 'padding-top', 'padding-left', 'margin-top', 'margin-left', 'gap', 'border-top-width',
              'border-top-color', 'border-radius', 'position', 'top', 'left', 'right', 'bottom', 'z-index', 'opacity',
              'transform', 'transition-property', 'transition-duration', 'transition-timing-function', 'animation-name',
              'animation-duration', 'animation-fill-mode', 'animation-delay', 'font-variant-numeric', 'text-wrap',
              'mask-image', 'background-blend-mode', 'border-image-source', 'overscroll-behavior', 'field-sizing',
              'appearance', 'scroll-snap-type', 'contain', 'text-box-trim', 'text-decoration-skip-ink',
              'box-decoration-break', 'overflow', 'overflow-clip-margin', 'color-scheme', 'grid-template-columns',
              'container-type', 'anchor-name', 'position-anchor', 'position-area', 'order', 'flex-basis', 'align-content',
              'justify-content', 'place-items', 'writing-mode', 'animation-composition', 'hyphens', 'overflow-wrap',
              'text-emphasis-style', 'text-emphasis-color', '-webkit-text-stroke-width', '-webkit-text-stroke-color',
              'scrollbar-gutter', 'outline-color', 'outline-width', 'text-decoration-line', 'visibility',
              'mask-composite', 'mask-size', 'mask-repeat', 'border-image-slice', 'border-image-width',
              'text-emphasis-position', 'text-decoration-thickness', 'text-decoration-offset',
              'text-underline-offset', 'text-box-edge', 'scroll-snap-align', 'scroll-padding-top',
              'animation-timeline', 'animation-range', 'transition-behavior', 'animation-range-start',
              'container-name', 'flex', 'flex-grow', 'flex-shrink', 'grid-auto-rows', 'grid-auto-flow',
              'grid-column-start', 'grid-row-start', 'scrollbar-color', 'scrollbar-width', 'will-change',
            ])
              props[p] = cs.getPropertyValue(p);
            out[key] = {
              rect: { x: Math.round(r.x * 100) / 100, y: Math.round(r.y * 100) / 100, w: Math.round(r.width * 100) / 100, h: Math.round(r.height * 100) / 100 },
              props,
            };
          }
          return out;
        });
        console.log(JSON.stringify(info, null, 1));
        await page.close();
        await context.close();
        attempts.push({ vp: vp.name, dumped: true });
        continue;
      }

      try {
        currentHtml = code;
        await page.goto(origin, { waitUntil: 'domcontentloaded', timeout: 15000 });
        await page.waitForTimeout(250);
        const markerPresent = (await page.locator('#webforge-check').count()) === 1;
        checks.push({ name: 'check marker present', ok: markerPresent });
        const addCheck = (name, ok, detail = '') => checks.push({ name, ok: !!ok, detail });
        let handled = false;
        if (markup.__error) {
          checks.push({ name: 'expansion oracle', ok: false, detail: markup.__error });
        } else if (!markup.COVERED_IDS.includes(id)) {
          checks.push({ name: 'expansion oracle coverage', ok: false, detail: `${id} missing from COVERED_IDS` });
        } else {
          handled = await markup.assertExpansionExample(page, { id, code, language: 'css' }, addCheck);
          if (!handled) checks.push({ name: 'expansion oracle', ok: false, detail: `returned false for ${id}` });
        }
      } catch (e) {
        checks.push({ name: 'page load/setup', ok: false, detail: String(e).split('\n')[0] });
      }
      checks.push({ name: 'no external requests', ok: blocked.length === 0, detail: blocked.join(',') });
      checks.push({ name: 'no broken internal resources', ok: resourceErrors.length === 0, detail: resourceErrors.join(' | ') });
      attempts.push({ vp: vp.name, checks, errors });
      await page.close();
      await context.close();
    }

    const pinned = attempts[0];
    const alt = attempts[1];
    const failed = (pinned.checks || []).filter((c) => !c.ok);
    // Viewport independence: the same names must pass at the second viewport.
    const altFailed = (alt.checks || []).filter((c) => !c.ok);
    report.rows.push({
      id,
      title: lesson.t,
      checks: (pinned.checks || []).length,
      pass: failed.length === 0 && (pinned.errors || []).length === 0,
      failed,
      errors: pinned.errors || [],
      altPass: altFailed.length === 0 && (alt.errors || []).length === 0,
      altFailed,
    });
  }

  await browser.close();
  await new Promise((r) => server.close(r));
  return { lessons, report, schema };
}

// --- 4. Report -------------------------------------------------------------
const result = await run();
const { report, schema } = result;
const rows = report.rows || [];
const schemaIssues = schema.issues;

let md = '# CSS expansion — module self-verification\n\n';
md += `Generated: ${new Date().toISOString()}\n\n`;
md += 'Reproduces `emit_content.py` output for `curriculum/css_expansion.py` (marker injection\n';
md += 'included) and executes every generated example against\n';
md += '`scripts/css_expansion_assertions.mjs`, at a pinned 960x720 viewport and again at\n';
md += '1280x900 to prove the oracle is not host-width dependent.\n\n';

md += '## Schema / policy\n\n';
md += `- entries: ${result.lessons.length}\n`;
md += `- distinct code bodies: ${schema.distinct}\n`;
md += `- shortest explain: ${schema.minExplain} chars; shortest document: ${schema.minCode} chars\n`;
md += `- issues: ${schemaIssues.length}\n\n`;
for (const i of schemaIssues) md += `  - ${i}\n`;
if (schemaIssues.length) md += '\n';

if (rows.length) {
  const passed = rows.filter((r) => r.pass).length;
  const altPassed = rows.filter((r) => r.altPass).length;
  const totalChecks = rows.reduce((s, r) => s + r.checks, 0);
  md += '## Execution\n\n';
  md += `Examples: ${rows.length}. Passed (pinned): ${passed}. Passed (alt viewport): ${altPassed}. Assertions: ${totalChecks}.\n\n`;
  md += '| id | title | checks | pinned | alt viewport | first failure |\n| --- | --- | --- | --- | --- | --- |\n';
  for (const r of rows) {
    const f = r.errors.length
      ? `pageerror: ${r.errors[0]}`
      : r.failed.length
        ? `${r.failed[0].name}: ${(r.failed[0].detail || '').slice(0, 120)}`
        : r.altFailed.length
          ? `alt: ${r.altFailed[0].name}: ${(r.altFailed[0].detail || '').slice(0, 100)}`
          : '';
    md += `| ${r.id} | ${r.title} | ${r.checks} | ${r.pass ? 'pass' : 'FAIL'} | ${r.altPass ? 'pass' : 'FAIL'} | ${String(f).replace(/\|/g, '\\|')} |\n`;
  }
  md += '\n';
}

if (!args.includes('--dump')) writeFileSync(resolve(here, 'css-expansion-verify.md'), md, 'utf8');
console.log(md);
const ok = schemaIssues.length === 0 && rows.every((r) => r.pass && r.altPass);
process.exit(ok ? 0 : 1);
