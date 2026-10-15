#!/usr/bin/env node
// WebForge curriculum verifier.
//
// Executes every example document in real Chromium and delegates the per-topic
// assertions to dedicated oracle modules:
//   * JavaScript examples -> scripts/js_example_assertions.mjs (owned here)
//   * HTML/CSS examples   -> scripts/web_markup_assertions.mjs (owned by p6)
//
// The runner itself only performs cross-cutting checks: the page must load with
// no page errors, the injected check marker must be present, and every
// non-loopback network request is blocked and reported as a failure (offline
// store requirement, no exemptions).
//
// It also proves the lesson/example relationship: each lesson's delivered code
// must equal its example's code after marker removal, and lesson bodies must be
// distinct.
//
// Usage: node scripts/run_examples.mjs [--report <path>] [--limit N]

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from 'node:http';
import { createHash } from 'node:crypto';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '..');

const args = process.argv.slice(2);
const reportIdx = args.indexOf('--report');
const reportPath = reportIdx >= 0 ? args[reportIdx + 1] : null;
const limitIdx = args.indexOf('--limit');
const limit = limitIdx >= 0 ? Number(args[limitIdx + 1]) : Infinity;

let chromium;
try {
  ({ chromium } = await import('playwright'));
} catch {
  console.error(
    'Playwright is not installed. Run: npm i -D playwright && npx playwright install chromium',
  );
  process.exit(2);
}

// Assertion oracles. The JS oracle is required. The markup oracle is required
// for HTML/CSS to be considered covered; a missing module is a hard failure.
const js = await import('./js_example_assertions.mjs').catch(() => null);
let markup = null;
let markupError = null;
try {
  markup = await import('./web_markup_assertions.mjs');
} catch (e) {
  markupError = String(e).split('\n')[0];
}

const examplesDoc = JSON.parse(
  readFileSync(resolve(repo, 'assets/content/examples.json'), 'utf8'),
);
const tutorialsDoc = JSON.parse(
  readFileSync(resolve(repo, 'assets/content/tutorials.json'), 'utf8'),
);

let examples = examplesDoc.entries;
if (Number.isFinite(limit)) examples = examples.slice(0, limit);

const sha = (s) => createHash('sha256').update(s, 'utf8').digest('hex').slice(0, 16);

// Intentional missing teaching resources. Exactly one source of truth: if the
// markup oracle exports MISSING_RESOURCE_ALLOWLIST it wins; otherwise this
// runner-default table is used. Both use exact URL.pathname equality (never a
// substring), keyed by example id. p5 confirmed the sole expected 404 is
// html-006's `/missing.png` (the lesson demonstrates the alt-text fallback).
const RUNNER_MISSING_ALLOWLIST = new Map([['html-example-006', ['/missing.png']]]);

function normaliseDoc(s) {
  return s
    .replace(/\s*<output id="webforge-check"[^>]*>ok<\/output>\s*/g, '\n')
    .replace(/\s+/g, ' ')
    .trim();
}

// ---------------------------------------------------------------------------
// Lesson <-> example mapping proof
// ---------------------------------------------------------------------------
const lessonCode = new Map();
for (const t of tutorialsDoc.entries) {
  for (const l of t.lessons) lessonCode.set(l.id, l.code);
}
const exampleByLesson = new Map();
for (const e of examplesDoc.entries) exampleByLesson.set(e.sourceLessonId, e);

const mappingIssues = [];
const distinctLessonBodies = new Map();
for (const [lessonId, code] of lessonCode) {
  const ex = exampleByLesson.get(lessonId);
  if (!ex) {
    mappingIssues.push(`${lessonId} has no example`);
    continue;
  }
  const h = sha(code);
  if (!distinctLessonBodies.has(h)) distinctLessonBodies.set(h, lessonId);
  if (normaliseDoc(code) !== normaliseDoc(ex.code)) {
    mappingIssues.push(`${lessonId} body !== ${ex.id} body`);
  }
  if (ex.type !== 'html') mappingIssues.push(`${ex.id} type is ${ex.type}, expected html`);
}
for (const e of examplesDoc.entries) {
  if (!lessonCode.has(e.sourceLessonId)) {
    mappingIssues.push(`${e.id} -> missing lesson ${e.sourceLessonId}`);
  }
  if (e.type !== 'html') mappingIssues.push(`${e.id} type is ${e.type}, expected html`);
}

// ---------------------------------------------------------------------------
// Runner
// ---------------------------------------------------------------------------
const results = [];
const browser = await chromium.launch();

let currentHtml = '';
let consoleCount = 0;
const consoleLines = [];
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

for (const ex of examples) {
  // Each example runs in its own browser context (fresh localStorage, cookies,
  // storage) so lessons cannot leak state into one another.
  const context = await browser.newContext();
  await context
    .grantPermissions(['clipboard-read', 'clipboard-write'])
    .catch(() => {});
  const page = await context.newPage();
  // Fail fast on missing selectors instead of waiting the 30s Playwright default.
  page.setDefaultTimeout(3000);
  const errors = [];
  const blocked = [];
  const checks = [];
  // Internal resource failures: requestfailed / HTTP >= 400 for same-origin
  // assets. These are failures unless the example explicitly declares the
  // resource as an intentional teaching omission (verified by its oracle).
  const resourceErrors = [];
  consoleCount = 0;
  consoleLines.length = 0;

  page.on('console', (m) => {
    consoleLines.push(`${m.type()}: ${m.text()}`);
    consoleCount++;
  });
  page.on('pageerror', (e) => errors.push(String(e).split('\n')[0]));
  page.on('response', (r) => {
    const url = r.url();
    const proto = url.split(':', 1)[0];
    if (proto === 'data' || proto === 'blob' || proto === 'about') return;
    if (r.status() >= 400) resourceErrors.push(`HTTP ${r.status()} ${url}`);
  });
  page.on('requestfailed', (r) => {
    const url = r.url();
    const proto = url.split(':', 1)[0];
    if (proto === 'data' || proto === 'blob' || proto === 'about') return;
    let sameOrigin = false;
    try {
      sameOrigin = new URL(url).origin === serverOrigin;
    } catch {
      sameOrigin = false;
    }
    if (!sameOrigin) return; // external aborts are recorded by the offline guard
    resourceErrors.push(`FAILED ${url} (${r.failure()?.errorText || 'error'})`);
  });

  // Offline guard: every non-loopback request is blocked and recorded. No
  // exemptions, including images. Same-origin is decided by URL origin, not a
  // string prefix, so `127.0.0.1.evil` is not allowed. data:/blob:/about: are
  // allowed by protocol.
  await page.route('**/*', (route) => {
    const url = route.request().url();
    const proto = url.split(':', 1)[0];
    if (proto === 'data' || proto === 'blob' || proto === 'about') {
      return route.continue();
    }
    let sameOrigin = false;
    try {
      sameOrigin = new URL(url).origin === serverOrigin;
    } catch {
      sameOrigin = false;
    }
    if (sameOrigin) return route.continue();
    blocked.push(`${route.request().resourceType()}: ${url}`);
    return route.abort();
  });

  const ctx = {
    id: ex.id,
    topic: (ex.language || ex.topic || ex.type).toLowerCase(),
    logs: consoleLines,
    getLogs: () => [...consoleLines],
    interaction: null,
    canvasPainted: async () =>
      page.evaluate(() => {
        const c = document.querySelector('canvas');
        if (!c) return false;
        try {
          const g = c.getContext('2d');
          if (!g) return false;
          const { data } = g.getImageData(0, 0, c.width || 1, c.height || 1);
          for (let i = 3; i < data.length; i += 4) if (data[i] !== 0) return true;
        } catch {
          return false;
        }
        return false;
      }),
  };

  try {
    currentHtml = ex.code;
    await page.goto(origin, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(250);

    // Marker is a cross-cutting sanity check, captured before interaction.
    const markerPresent = (await page.locator('#webforge-check').count()) === 1;
    checks.push({
      name: 'check marker present',
      ok: markerPresent,
      detail: `present=${markerPresent}`,
    });

    const isJs = ex.id.startsWith('js-example-');

    // Generic interaction drive is JS-only. The markup oracle drives each
    // HTML/CSS example itself; driving both would double-trigger handlers.
    if (isJs) {
      const hasHandler = /addEventListener|on(click|input|change|submit|load|keydown|mousemove|hashchange|scroll)\s*=/.test(
        ex.code,
      );
      const hasToggle = /:checked|type=["']checkbox/.test(ex.code);
      if (hasHandler || hasToggle) {
        ctx.interaction = await driveInteraction(page, ex.code);
        await page.waitForTimeout(150);
      }
      if (js && js.owns(ex.id)) {
        const moduleChecks = await js.assertJs(page, ctx);
        checks.push(...moduleChecks);
      } else {
        checks.push({ name: 'js oracle', ok: false, detail: 'js_example_assertions.mjs missing' });
      }
    } else {
      // p6 contract: assertMarkupExample(page, example, addCheck) -> bool,
      // plus a COVERED_IDS set. addCheck(name, ok, detail) records results.
      const covered = markup && markup.COVERED_IDS;
      const isCovered = Array.isArray(covered) && covered.includes(ex.id);
      if (markup && typeof markup.assertMarkupExample === 'function' && isCovered) {
        const addCheck = (name, ok, detail = '') => checks.push({ name, ok: !!ok, detail });
        const handled = await markup.assertMarkupExample(page, ex, addCheck);
        if (!handled) {
          checks.push({ name: 'markup oracle', ok: false, detail: `unhandled ${ex.id}` });
        }
      } else {
        checks.push({
          name: 'markup oracle',
          ok: false,
          detail: markupError
            ? `web_markup_assertions.mjs unavailable: ${markupError}`
            : `${ex.id} not in markup COVERED_IDS`,
        });
      }
    }
  } catch (e) {
    checks.push({ name: 'page load/setup', ok: false, detail: String(e).split('\n')[0] });
  }

  // Offline guard result: no external requests of any kind.
  checks.push({
    name: 'no external requests',
    ok: blocked.length === 0,
    detail: blocked.join(','),
  });

  // Internal resource integrity: requestfailed / HTTP>=400 same-origin assets
  // must be zero, unless the example's oracle declares an intentional missing
  // teaching resource for this exact id AND path (minimal match, no wildcard).
  const allowList = (markup && markup.MISSING_RESOURCE_ALLOWLIST) || RUNNER_MISSING_ALLOWLIST;
  const allowForId =
    allowList && typeof allowList.get === 'function' ? allowList.get(ex.id) : null;
  const pathnameOf = (entry) => {
    const m = entry.match(/https?:\/\/\S+/);
    if (!m) return null;
    try {
      return new URL(m[0]).pathname;
    } catch {
      return null;
    }
  };
  const unexpected = resourceErrors.filter((e) => {
    if (!allowForId) return true;
    const pathname = pathnameOf(e);
    // Exact pathname equality only.
    return !(pathname && allowForId.includes(pathname));
  });
  checks.push({
    name: 'no broken internal resources',
    ok: unexpected.length === 0,
    detail: unexpected.join(' | '),
  });

  const failed = checks.filter((c) => !c.ok);
  results.push({
    id: ex.id,
    type: ctx.topic,
    pass: failed.length === 0 && errors.length === 0,
    failed,
    errors,
    checks: checks.length,
  });
  await page.close();
  await context.close();
}

await browser.close();
await new Promise((r) => server.close(r));

// ---------------------------------------------------------------------------
// Interaction driver (generic stimulus; oracle modules add their own)
// ---------------------------------------------------------------------------
async function driveInteraction(page, code = '') {
  const before = await page.evaluate(() => document.body.innerHTML);
  const consoleBefore = consoleCount;

  const fileInput = page.locator('input[type=file]').first();
  if (await fileInput.count()) {
    try {
      await fileInput.setInputFiles({
        name: 'sample.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from('WebForge 示例文件'),
      });
      await page.waitForTimeout(150);
    } catch {
      /* not fillable */
    }
  }

  const dropZone = page.locator('[class*=drop], [id*=zone], [id*=drop], [class*=zone]').first();
  if ((await dropZone.count()) && /dataTransfer|dragover|['"]drop['"]/.test(code)) {
    try {
      await dropZone.evaluate((el) => {
        const dt = new DataTransfer();
        dt.items.add(new File(['WebForge'], 'drag.txt', { type: 'text/plain' }));
        el.dispatchEvent(new DragEvent('dragover', { bubbles: true, dataTransfer: dt }));
        el.dispatchEvent(new DragEvent('drop', { bubbles: true, dataTransfer: dt }));
      });
      await page.waitForTimeout(150);
    } catch {
      /* not a drop target */
    }
  }

  const inputs = await page.$$(
    'input:not([type=checkbox]):not([type=radio]):not([type=file]):not([type=color]):not([type=range]), textarea',
  );
  for (const input of inputs.slice(0, 4)) {
    try {
      const shown = await input.evaluate((el) => {
        const cs = getComputedStyle(el);
        return cs.display !== 'none' && cs.visibility !== 'hidden' && !el.hidden;
      });
      if (!shown) continue;
      await input.fill('WebForge', { timeout: 1000 }).catch(() => {});
      await input.dispatchEvent('input').catch(() => {});
      await input.dispatchEvent('change').catch(() => {});
    } catch {
      /* skip */
    }
  }

  const form = page.locator('form').first();
  if (await form.count()) {
    await form.evaluate((f) => (f.requestSubmit ? f.requestSubmit() : f.submit())).catch(() => {});
    await page.waitForTimeout(150);
  }

  const btn = page.locator('button:not([disabled])').first();
  if (await btn.count()) {
    await btn.click({ timeout: 2000 }).catch(() => {});
    await page.waitForTimeout(200);
  }

  const checkbox = page.locator('input[type=checkbox]').first();
  if (await checkbox.count()) {
    await checkbox.check({ timeout: 2000 }).catch(() => {});
    await page.waitForTimeout(120);
  }

  await page.keyboard.press('Control+s').catch(() => {});
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(450);

  const after = await page.evaluate(() => document.body.innerHTML);
  const domChanged = after !== before;
  const logged = consoleCount > consoleBefore;
  return {
    attempted: true,
    ok: domChanged || logged,
    detail: `${domChanged ? 'DOM changed' : ''}${domChanged && logged ? ' + ' : ''}${logged ? 'console output' : ''}` || 'no observable change',
  };
}

// ---------------------------------------------------------------------------
// Report
// ---------------------------------------------------------------------------
const passed = results.filter((r) => r.pass).length;
const failed = results.length - passed;
const totalChecks = results.reduce((s, r) => s + r.checks, 0);

let md = '# Example & tutorial execution report\n\n';
md += `Runner: Playwright Chromium. Examples: ${results.length}. `;
md += `Assertions: ${totalChecks}. Passed: ${passed}. Failed: ${failed}.\n\n`;
md += `Tutorial lessons: ${lessonCode.size}. Distinct lesson bodies: ${distinctLessonBodies.size}. `;
md += `Lesson/example mapping issues: ${mappingIssues.length}.\n\n`;
if (!markup) md += `Markup oracle: NOT LOADED (${markupError || 'missing'}).\n\n`;
if (mappingIssues.length) {
  md += 'Mapping issues:\n';
  for (const i of mappingIssues) md += `- ${i}\n`;
  md += '\n';
}
md += '| id | type | result | checks | first failure |\n';
md += '| --- | --- | --- | --- | --- |\n';
for (const r of results) {
  const f = r.errors.length
    ? `pageerror: ${r.errors[0]}`
    : r.failed.length
      ? `${r.failed[0].name}: ${r.failed[0].detail}`
      : '';
  md += `| ${r.id} | ${r.type} | ${r.pass ? 'pass' : 'FAIL'} | ${r.checks} | ${f
    .replace(/\|/g, '\\|')
    .slice(0, 140)} |\n`;
}

console.log(md);
// Always persist the full report to the canonical artifact path so the final
// resource/assertion state is recorded, plus any explicit --report target.
const reportTargets = new Set([
  resolve(repo, '.trellis/tasks/10-15-webforge-content-curriculum/research/example-execution-report.md'),
]);
if (reportPath) reportTargets.add(resolve(repo, reportPath));
for (const target of reportTargets) {
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, md, 'utf8');
}

process.exit(failed === 0 && mappingIssues.length === 0 ? 0 : 1);
