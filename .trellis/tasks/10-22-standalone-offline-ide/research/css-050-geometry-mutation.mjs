// Confirm the new css-050 geometry checks are falsifiable: mutate the knob travel
// and the track width and require them to fail. Also record the measured values so
// the report shows real numbers, not constants.
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
let current = '';
const server = createServer((req, res) => {
  res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
  res.end(current);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const origin = `http://127.0.0.1:${server.address().port}/`;

async function run(label, html) {
  current = html.replace('</body>', '  <output id="webforge-check" hidden>ok</output>\n</body>');
  const context = await browser.newContext({ viewport: { width: 412, height: 800 } });
  const page = await context.newPage();
  page.setDefaultTimeout(4000);
  const checks = [];
  let error = null;
  let measured = null;
  try {
    await page.goto(origin, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(200);
    const addCheck = (name, ok, detail = '') => {
      checks.push({ name, ok: !!ok, detail });
      if (name.startsWith('the checked knob travels')) measured = detail;
    };
    await markup.assertMarkupExample(page, { id: 'css-example-050', code: current, language: 'css' }, addCheck);
  } catch (e) {
    error = String(e).split('\n')[0];
  }
  await page.close();
  await context.close();
  const failed = checks.filter((c) => !c.ok);
  return { label, failed: failed.length, failures: failed.map((c) => c.name), measured, error };
}

const base = lesson.code;
const results = [
  await run('unmodified', base),
  // travel too short: knob no longer reaches the far edge
  await run('travel shortened to 10px', base.replace('transform: translateX(22px)', 'transform: translateX(10px)')),
  // travel too far: knob overflows the track
  await run('travel pushed to 30px', base.replace('transform: translateX(22px)', 'transform: translateX(30px)')),
  // wider track: 22px no longer fills it
  await run('track widened to 60px', base.replace('width: 48px', 'width: 60px')),
];

console.log(JSON.stringify(results, null, 1));
await browser.close();
await new Promise((r) => server.close(r));

const ok = results[0].failed === 0 && results.slice(1).every((r) => r.failed > 0 || r.error !== null);
console.log('\nall three mutations detected:', ok);
process.exit(ok ? 0 : 1);
