// Prove the css-050 fix addresses the real cause: a click issued immediately
// after the dispatcher parks the pointer off-document can be dropped by an engine
// that hit-tests before processing the move. Host Chromium is used as the control
// because the native slot is revoked.
import { execFileSync } from 'node:child_process';
import { resolve, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createServer } from 'node:http';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../../../..');

const dumpScript = `
import json, sys
sys.path.insert(0, ${JSON.stringify(resolve(repo, 'scripts'))})
from curriculum import css_data, css_data2, css_data3, css_data4, css_data5, supplement
base = css_data.CSS + css_data2.CSS2 + css_data3.CSS3 + css_data4.CSS4 + css_data5.CSS5 + supplement.CSS6
print(json.dumps([{'id': f'css-example-{i:03d}', 'code': x['code']} for i, x in enumerate(base, 1)], ensure_ascii=False))
`;
const lessons = JSON.parse(execFileSync('python', ['-X', 'utf8', '-c', dumpScript], { cwd: repo, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 }));
const lesson = lessons.find((l) => l.id === 'css-example-050');

const markup = await import(pathToFileURL(resolve(repo, 'scripts/web_markup_assertions.mjs')).href);
const { chromium } = await import(pathToFileURL(resolve(repo, 'node_modules/playwright/index.mjs')).href);

const browser = await chromium.launch();
let current = lesson.code.replace('</body>', '  <output id="webforge-check" hidden>ok</output>\n</body>');
const server = createServer((req, res) => {
  res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
  res.end(current);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const origin = `http://127.0.0.1:${server.address().port}/`;

async function runCase(label, prepare) {
  const context = await browser.newContext({ viewport: { width: 412, height: 800 } });
  const page = await context.newPage();
  page.setDefaultTimeout(4000);
  const checks = [];
  let error = null;
  try {
    await page.goto(origin, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(200);
    if (prepare) await prepare(page);
    const addCheck = (name, ok, detail = '') => checks.push({ name, ok: !!ok, detail });
    await markup.assertMarkupExample(page, { id: 'css-example-050', code: current, language: 'css' }, addCheck);
  } catch (e) {
    error = String(e).split('\n')[0];
  }
  await page.close();
  await context.close();
  const failed = checks.filter((c) => !c.ok);
  return { label, checks: checks.length, failed: failed.length, failures: failed.map((c) => `${c.name} (${c.detail})`), error };
}

// A: exactly what the dispatcher does — park, then the case runs. This is the
//    scenario the native run hit.
const parked = await runCase('pointer parked off-document (dispatcher behaviour)', async (page) => {
  await page.mouse.move(-1, -1);
});

// B: control — pointer left where the browser put it.
const untouched = await runCase('pointer untouched (control)', null);

console.log(JSON.stringify([parked, untouched], null, 1));
await browser.close();
await new Promise((r) => server.close(r));
process.exit(parked.failed === 0 && untouched.failed === 0 ? 0 : 1);
