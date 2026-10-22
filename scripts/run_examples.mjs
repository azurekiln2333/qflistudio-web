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
//        [--filter <regex>] [--ohos-cdp <local HDC URL>] [--viewport WIDTHxHEIGHT]
// OHOS reuses the native test target and verifies its packaged source bytes.
// --viewport is host-only; OHOS uses the real native viewport.
// A JSON sibling records all assertions and exact catalog/source hashes.

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from 'node:http';
import { createHash } from 'node:crypto';
import { OHOS_BOOTSTRAP_URL, validateCdpEndpoint, validateDeviceCatalog } from './catalog_device_contract.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '..');

const args = process.argv.slice(2);
const options = new Map();
for (let i = 0; i < args.length; i += 2) {
  const name = args[i];
  if (!['--report', '--limit', '--filter', '--ohos-cdp', '--viewport'].includes(name) ||
      options.has(name) || !args[i + 1] || args[i + 1].startsWith('--')) {
    throw new Error(`Unknown, repeated or missing-value option: ${name}`);
  }
  options.set(name, args[i + 1]);
}
const reportIdx = args.indexOf('--report');
const reportPath = reportIdx >= 0 ? args[reportIdx + 1] : null;
const limitIdx = args.indexOf('--limit');
const limit = limitIdx >= 0 ? Number(args[limitIdx + 1]) : Infinity;
const cdpIdx = args.indexOf('--ohos-cdp');
const cdpEndpoint = cdpIdx >= 0 ? validateCdpEndpoint(args[cdpIdx + 1]) : null;
const filterIdx = args.indexOf('--filter');
const filter = filterIdx >= 0 ? new RegExp(args[filterIdx + 1]) : null;
const viewportOption = options.get('--viewport');
if (viewportOption && (!/^\d+x\d+$/.test(viewportOption) || cdpEndpoint)) {
  throw new Error('--viewport requires WIDTHxHEIGHT and is host-only');
}
const viewport = viewportOption
  ? Object.fromEntries(viewportOption.split('x').map((value, index) => [index ? 'height' : 'width', Number(value)]))
  : { width: 1280, height: 720 };
if (Object.values(viewport).some((value) => !Number.isSafeInteger(value) || value < 100 || value > 10000)) {
  throw new Error('Viewport dimensions must be integers from 100 to 10000');
}
if ((reportIdx >= 0 && (!reportPath || reportPath.startsWith('--'))) ||
    (limitIdx >= 0 && (!Number.isSafeInteger(limit) || limit < 1))) {
  throw new Error('Expected --report <path> and --limit <positive integer>');
}

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
const expansionNames = ['html', 'css', 'js'];
const expansions = await Promise.all(expansionNames.map(async (subject) => {
  try {
    return await import(`./${subject}_expansion_assertions.mjs`);
  } catch {
    // A missing module cannot claim coverage: its entries fail below.
    return null;
  }
}));
const covers = (module, id) => module &&
  (Array.isArray(module.COVERED_IDS)
    ? module.COVERED_IDS.includes(id)
    : module.COVERED_IDS instanceof Set && module.COVERED_IDS.has(id));
let markup = null;
let markupError = null;
try {
  markup = await import('./web_markup_assertions.mjs');
} catch (e) {
  markupError = String(e).split('\n')[0];
}

const examplesSource = readFileSync(resolve(repo, 'assets/content/examples.json'), 'utf8');
const tutorialsSource = readFileSync(resolve(repo, 'assets/content/tutorials.json'), 'utf8');
const examplesDoc = JSON.parse(examplesSource);
const tutorialsDoc = JSON.parse(tutorialsSource);

let examples = examplesDoc.entries;
if (filter) examples = examples.filter((example) => filter.test(example.id));
if (Number.isFinite(limit)) examples = examples.slice(0, limit);
if (examples.length === 0) throw new Error('No examples selected; refusing an empty pass');

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
const requireUnique = (values, label) => {
  const seen = new Set();
  for (const value of values) {
    if (!value || seen.has(value)) mappingIssues.push(`${label} duplicate/empty: ${value}`);
    seen.add(value);
  }
};
requireUnique(tutorialsDoc.entries.map((entry) => entry.id), 'tutorial ID');
requireUnique(tutorialsDoc.entries.flatMap((entry) => entry.lessons.map((lesson) => lesson.id)), 'lesson ID');
requireUnique(examplesDoc.entries.map((entry) => entry.id), 'example ID');
requireUnique(examplesDoc.entries.map((entry) => entry.sourceLessonId), 'example lesson mapping');
const distinctLessonBodies = new Map();
for (const [lessonId, code] of lessonCode) {
  const ex = exampleByLesson.get(lessonId);
  if (!ex) {
    mappingIssues.push(`${lessonId} has no example`);
    continue;
  }
  const h = sha(code);
  if (distinctLessonBodies.has(h)) {
    mappingIssues.push(`${lessonId} duplicates ${distinctLessonBodies.get(h)}`);
  } else {
    distinctLessonBodies.set(h, lessonId);
  }
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
const browser = cdpEndpoint
  ? await chromium.connectOverCDP(cdpEndpoint)
  : await chromium.launch();
const browserVersion = browser.version();
const startedAt = new Date().toISOString();
let deviceEvidence = null;
let nativePage = null;
let nativeContext = null;

let currentHtml = '';
let consoleCount = 0;
const consoleLines = [];
let server = null;
let hostOrigin = null;
try {
if (cdpEndpoint) {
  // ArkWeb supplies one existing native target. It does not need to support
  // Chromium's Browser.createBrowserContext or Target.createTarget commands.
  const candidates = browser.contexts().flatMap((context) => context.pages()).filter((page) => {
    try {
      const url = new URL(page.url());
      return url.hostname === '127.0.0.1' && Number(url.port) >= 19999 && Number(url.port) <= 65535;
    } catch { return false; }
  });
  if (candidates.length !== 1) throw new Error(`Expected exactly one test-only native ArkWeb target, got ${candidates.length}`);
  nativePage = candidates[0];
  nativeContext = nativePage.context();
  await nativePage.goto(OHOS_BOOTSTRAP_URL, { waitUntil: 'domcontentloaded', timeout: 15000 });
  const bootstrap = await nativePage.evaluate(() => window.__QFLI_OHOS_CATALOG__);
  deviceEvidence = validateDeviceCatalog(bootstrap, examplesSource, tutorialsSource);
} else {
server = createServer((req, res) => {
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
hostOrigin = `http://127.0.0.1:${server.address().port}/`;
}

for (const ex of examples) {
  // Host cases get independent contexts. Native cases have unique origins in
  // a fresh incognito renderer; cookies (which ignore port) are cleared too.
  const context = nativeContext || await browser.newContext({ viewport });
  if (nativeContext) {
    await nativePage.goto(OHOS_BOOTSTRAP_URL, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await context.clearCookies();
    await nativePage.evaluate(() => { window.name = ''; });
    const session = await context.newCDPSession(nativePage);
    try {
      await session.send('Storage.clearDataForOrigin', {
        origin: deviceEvidence.cases.get(ex.id).origin,
        storageTypes: 'all',
      });
    } finally {
      await session.detach();
    }
  }
  await context
    .grantPermissions(['clipboard-read', 'clipboard-write'])
    .catch(() => {});
  const page = nativePage || await context.newPage();
  const origin = deviceEvidence ? deviceEvidence.cases.get(ex.id).url : hostOrigin;
  const serverOrigin = new URL(origin).origin;
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

  const onConsole = (m) => {
    consoleLines.push(`${m.type()}: ${m.text()}`);
    consoleCount++;
  };
  const onPageError = (e) => errors.push(String(e).split('\n')[0]);
  const onResponse = (r) => {
    const url = r.url();
    const proto = url.split(':', 1)[0];
    if (proto === 'data' || proto === 'blob' || proto === 'about') return;
    if (r.status() >= 400) resourceErrors.push(`HTTP ${r.status()} ${url}`);
  };
  const onRequestFailed = (r) => {
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
  };
  page.on('console', onConsole);
  page.on('pageerror', onPageError);
  page.on('response', onResponse);
  page.on('requestfailed', onRequestFailed);

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
    const owners = expansions.filter((module) => covers(module, ex.id));
    const baselineOwns = isJs ? js?.owns(ex.id) : covers(markup, ex.id);
    checks.push({
      name: 'exactly one semantic oracle',
      ok: owners.length + (baselineOwns ? 1 : 0) === 1,
      detail: `owners=${owners.length + (baselineOwns ? 1 : 0)}`,
    });

    // Generic interaction drive is JS-only. The markup oracle drives each
    // HTML/CSS example itself; driving both would double-trigger handlers.
    if (owners.length === 1) {
      const before = checks.length;
      const addCheck = (name, ok, detail = '') => checks.push({ name, ok: ok === true, detail });
      const handled = await owners[0].assertExpansionExample(page, ex, addCheck);
      checks.push({
        name: 'expansion semantic coverage',
        ok: handled === true && checks.length > before,
        detail: `handled=${handled}, assertions=${checks.length - before}`,
      });
    } else if (isJs) {
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
    assertions: checks,
    codeSha256: createHash('sha256').update(ex.code, 'utf8').digest('hex'),
    console: [...consoleLines],
    blockedRequests: blocked,
    resourceErrors,
  });
  page.off('console', onConsole);
  page.off('pageerror', onPageError);
  page.off('response', onResponse);
  page.off('requestfailed', onRequestFailed);
  await page.unrouteAll({ behavior: 'wait' });
  if (!nativePage) {
    await page.close();
    await context.close();
  }
}
} finally {
  // For connectOverCDP this disconnects the transport; never close the native
  // page/context or terminate another app's renderer.
  await browser.close();
  if (server) await new Promise((r) => server.close(r));
}

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
md += `Runner: ${deviceEvidence ? 'OHOS ArkWeb via local CDP' : 'Playwright Chromium (host)'}. Examples: ${results.length}. `;
md += `Assertions: ${totalChecks}. Passed: ${passed}. Failed: ${failed}.\n\n`;
md += `Tutorial lessons: ${lessonCode.size}. Distinct lesson bodies: ${distinctLessonBodies.size}. `;
md += `Lesson/example mapping issues: ${mappingIssues.length}.\n\n`;
md += `Browser: ${browserVersion}. Started: ${startedAt}. `;
md += `Complete catalog: ${results.length === examplesDoc.entries.length ? 'yes' : 'NO (partial run)'}.\n\n`;
if (deviceEvidence) md += `Packaged native session: ${deviceEvidence.runId}. Catalog byte lengths and SHA256 verified. ` +
  `Environment: ${JSON.stringify(deviceEvidence.environment)}.\n\n`;
else md += `Host viewport: ${viewport.width} × ${viewport.height}.\n\n`;
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
// An explicit destination owns the current run. Keep dated historical task
// evidence immutable when verifying a newer source/catalog revision.
const reportTargets = new Set([
  resolve(repo, reportPath || 'build/content/example-execution-report.md'),
]);
for (const target of reportTargets) {
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, md, 'utf8');
  const jsonTarget = /\.md$/i.test(target) ? target.replace(/\.md$/i, '.json') : `${target}.json`;
  writeFileSync(jsonTarget, JSON.stringify({
    schemaVersion: 1,
    runtime: deviceEvidence ? 'ohos-arkweb' : 'host-chromium',
    device: deviceEvidence ? { runId: deviceEvidence.runId, manifest: deviceEvidence.manifest,
      environment: deviceEvidence.environment } : null,
    viewport: deviceEvidence ? null : viewport,
    host: { platform: process.platform, architecture: process.arch, node: process.version },
    browserVersion,
    startedAt,
    completedAt: new Date().toISOString(),
    catalog: {
      examplesSha256: createHash('sha256').update(examplesSource).digest('hex'),
      tutorialsSha256: createHash('sha256').update(tutorialsSource).digest('hex'),
      totalExamples: examplesDoc.entries.length,
      totalLessons: lessonCode.size,
      executedExamples: results.length,
      complete: results.length === examplesDoc.entries.length,
    },
    passed,
    failed,
    totalChecks,
    mappingIssues,
    results,
  }, null, 2) + '\n', 'utf8');
}

process.exit(failed === 0 && mappingIssues.length === 0 ? 0 : 1);
