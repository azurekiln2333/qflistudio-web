// Replay the whole CSS oracle (baseline 100 + expansion 60) against
// scripts/web_markup_assertions.mjs and css_expansion_assertions.mjs.
//
// This mirrors scripts/run_examples.mjs semantics for the CSS subset only:
//   * serve the lesson document with the same <output id="webforge-check">
//     marker emit_content.py injects,
//   * create a fresh context per example,
//   * count external requests, page errors and broken internal resources,
//   * run the oracle, then report per-example pass/fail.
//
// Flags:
//   --only 011,044       restrict to specific example numbers
//   --width 1280         context viewport width (default 1280)
//   --height 720         context viewport height
//   --native             create the context with viewport: null (ArkWeb-like:
//                        viewportSize() is null and setViewportSize throws)
//   --report <path>      write the markdown report here
import { execFileSync } from 'node:child_process';
import { resolve, dirname } from 'node:path';
import { writeFileSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createServer } from 'node:http';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../../../..');

const args = process.argv.slice(2);
const argValue = (name, fallback) => {
  const i = args.indexOf(name);
  return i >= 0 && args[i + 1] ? args[i + 1] : fallback;
};
const only = argValue('--only', '')
  .split(',')
  .map((s) => s.trim())
  .filter(Boolean)
  .map(Number);
const width = Number(argValue('--width', '1280'));
const height = Number(argValue('--height', '720'));
const native = args.includes('--native');
// --baseline-only restricts the run to the shipped 100 CSS examples, so the
// baseline can be verified in isolation from the 60 expanded ones.
const baselineOnly = args.includes('--baseline-only');
// With --native the window size comes from the browser launch flags, which is
// how a real host browser behaves. --window 412x915 makes that a phone-sized
// native window so the "cannot resize" fallback branches are exercised at a
// narrow width instead of only at the default desktop one.
const windowSize = argValue('--window', '');
const reportPath = argValue('--report', resolve(here, 'css-suite-verify.md'));

const dumpScript = `
import json, sys
sys.path.insert(0, ${JSON.stringify(resolve(repo, 'scripts'))})
from curriculum import css_data, css_data2, css_data3, css_data4, css_data5, supplement, css_expansion
base = css_data.CSS + css_data2.CSS2 + css_data3.CSS3 + css_data4.CSS4 + css_data5.CSS5 + supplement.CSS6
print(json.dumps([{'id': f'css-example-{i:03d}', 'code': x['code'], 'title': x['t']} for i, x in enumerate(base, 1)]
               + [{'id': f'css-example-{100 + i:03d}', 'code': x['code'], 'title': x['t']} for i, x in enumerate(css_expansion.CSS_EXTRA, 1)],
               ensure_ascii=False))
`;
const lessons = JSON.parse(
  execFileSync('python', ['-X', 'utf8', '-c', dumpScript], {
    cwd: repo,
    encoding: 'utf8',
    maxBuffer: 128 * 1024 * 1024,
  }),
);

const markup = await import(pathToFileURL(resolve(repo, 'scripts/web_markup_assertions.mjs')).href);
const expansion = await import(pathToFileURL(resolve(repo, 'scripts/css_expansion_assertions.mjs')).href);
const { chromium } = await import(pathToFileURL(resolve(repo, 'node_modules/playwright/index.mjs')).href);

const marker = (code) =>
  code.includes('</body>')
    ? code.replace('</body>', '  <output id="webforge-check" hidden>ok</output>\n</body>')
    : `${code}\n<output id="webforge-check" hidden>ok</output>`;

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

const browser = await chromium.launch(
  windowSize
    ? {
        args: [
          `--window-size=${windowSize.replace('x', ',')}`,
          '--window-position=0,0',
          '--force-device-scale-factor=1',
        ],
      }
    : {},
);
const browserVersion = browser.version();
const selected = (only.length ? lessons.filter((l) => only.includes(Number(l.id.slice(-3)))) : lessons).filter(
  (l) => !baselineOnly || Number(l.id.slice(-3)) <= 100,
);
const rows = [];

for (const lesson of selected) {
  const context = await browser.newContext(
    native ? { viewport: null } : { viewport: { width, height } },
  );
  const page = await context.newPage();
  page.setDefaultTimeout(6000);

  const external = [];
  const errors = [];
  const badResources = [];
  page.on('request', (r) => {
    const url = r.url();
    if (!url.startsWith(origin) && !url.startsWith('data:') && !url.startsWith('blob:') && !url.startsWith('about:')) {
      external.push(url.slice(0, 120));
    }
  });
  page.on('requestfailed', (r) => {
    if (r.url().startsWith(origin)) badResources.push(r.url().slice(0, 120));
  });
  page.on('response', (r) => {
    if (r.url().startsWith(origin) && r.status() >= 400) badResources.push(`${r.status()} ${r.url().slice(0, 100)}`);
  });
  page.on('pageerror', (e) => errors.push(String(e).split('\n')[0].slice(0, 160)));

  currentHtml = marker(lesson.code);
  const checks = [];
  const addCheck = (name, ok, detail = '') => checks.push({ name, ok: !!ok, detail: String(detail ?? '') });
  let thrown = null;
  try {
    await page.goto(origin, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await page.waitForTimeout(300);
    const handled =
      (await markup.assertMarkupExample(page, { id: lesson.id, language: 'css', code: currentHtml }, addCheck)) ||
      (await expansion.assertExpansionExample(page, { id: lesson.id, language: 'css', code: currentHtml }, addCheck));
    if (!handled) addCheck('oracle handled the example', false, 'no case registered');
  } catch (e) {
    thrown = String(e).split('\n')[0].slice(0, 200);
  }

  const failed = checks.filter((c) => !c.ok);
  const markerPresent = await page
    .locator('#webforge-check')
    .count()
    .catch(() => 0);

  rows.push({
    id: lesson.id,
    title: lesson.title,
    checks: checks.length,
    failed,
    thrown,
    external,
    errors,
    badResources,
    markerPresent,
    allChecks: checks,
    ok:
      !thrown &&
      failed.length === 0 &&
      external.length === 0 &&
      errors.length === 0 &&
      badResources.length === 0 &&
      markerPresent === 1 &&
      checks.length > 0,
  });

  await page.close();
  await context.close();
}

if (args.includes('--verbose')) {
  for (const r of rows) {
    console.log(`# ${r.id} ${r.title}`);
    for (const c of r.allChecks) console.log(`   ${c.ok ? 'ok  ' : 'FAIL'} ${c.name}${c.detail ? ` (${c.detail})` : ''}`);
  }
}

await browser.close();
await new Promise((r) => server.close(r));

const pass = rows.filter((r) => r.ok).length;
const totalChecks = rows.reduce((a, r) => a + r.checks, 0);
const mode = native ? 'native (viewport: null)' : `${width}x${height}`;

let md = '# CSS oracle suite replay\n\n';
md += `Generated: ${new Date().toISOString()}\n\n`;
md += `Chromium ${browserVersion} (bundled Playwright). Context: ${mode}.\n\n`;
md += `Examples: ${rows.length}. Passed: ${pass}. Failed: ${rows.length - pass}. Assertions: ${totalChecks}.\n\n`;
md += '| id | title | checks | result | first failure |\n| --- | --- | --- | --- | --- |\n';
for (const r of rows) {
  const first = r.thrown
    ? `THREW ${r.thrown}`
    : r.failed[0]
      ? `${r.failed[0].name}${r.failed[0].detail ? ` (${r.failed[0].detail})` : ''}`
      : r.external.length
        ? `external request ${r.external[0]}`
        : r.errors.length
          ? `page error ${r.errors[0]}`
          : r.badResources.length
            ? `bad resource ${r.badResources[0]}`
            : r.markerPresent !== 1
              ? 'marker missing'
              : '';
  md += `| ${r.id} | ${r.title.replace(/\|/g, '\\|')} | ${r.checks} | ${r.ok ? 'pass' : 'FAIL'} | ${String(first).replace(/\|/g, '\\|').slice(0, 140)} |\n`;
}

writeFileSync(reportPath, md, 'utf8');
console.log(`mode: ${mode}`);
console.log(`Examples: ${rows.length}. Passed: ${pass}. Failed: ${rows.length - pass}. Assertions: ${totalChecks}.`);
for (const r of rows.filter((x) => !x.ok)) {
  console.log(`FAIL ${r.id} ${r.title}`);
  if (r.thrown) console.log(`   threw: ${r.thrown}`);
  for (const f of r.failed.slice(0, 4)) console.log(`   - ${f.name} ${f.detail}`);
  for (const e of r.external.slice(0, 2)) console.log(`   external: ${e}`);
  for (const e of r.errors.slice(0, 2)) console.log(`   pageerror: ${e}`);
  for (const e of r.badResources.slice(0, 2)) console.log(`   resource: ${e}`);
  if (r.markerPresent !== 1) console.log(`   marker count: ${r.markerPresent}`);
}
console.log(`report: ${reportPath}`);
process.exit(rows.length - pass === 0 ? 0 : 1);
