// Force the "cannot resize" branch and prove the responsive fallbacks are right.
//
// In a real ArkWeb/CDP session `page.viewportSize()` is null and
// `page.setViewportSize()` throws, because the host browser owns the window.
// Playwright's own `viewport: null` context does not reproduce the throw, so
// this harness wraps a normal Page in a proxy that does, then runs the
// responsive cases at several real widths and checks that each one asserts the
// branch its width implies (instead of silently asserting desktop).
import { execFileSync } from 'node:child_process';
import { resolve, dirname } from 'node:path';
import { writeFileSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createServer } from 'node:http';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../../../..');

const dumpScript = `
import json, sys
sys.path.insert(0, ${JSON.stringify(resolve(repo, 'scripts'))})
from curriculum import css_data, css_data2, css_data3, css_data4, css_data5, supplement
base = css_data.CSS + css_data2.CSS2 + css_data3.CSS3 + css_data4.CSS4 + css_data5.CSS5 + supplement.CSS6
print(json.dumps([{'id': f'css-example-{i:03d}', 'code': x['code'], 'title': x['t']} for i, x in enumerate(base, 1)], ensure_ascii=False))
`;
const lessons = JSON.parse(
  execFileSync('python', ['-X', 'utf8', '-c', dumpScript], {
    cwd: repo,
    encoding: 'utf8',
    maxBuffer: 64 * 1024 * 1024,
  }),
);

const expansionDump = `
import json, sys
sys.path.insert(0, ${JSON.stringify(resolve(repo, 'scripts'))})
from curriculum import css_expansion
print(json.dumps([{'id': f'css-example-{100 + i:03d}', 'code': x['code'], 'title': x['t']} for i, x in enumerate(css_expansion.CSS_EXTRA, 1)], ensure_ascii=False))
`;
const expansionLessons = JSON.parse(
  execFileSync('python', ['-X', 'utf8', '-c', expansionDump], {
    cwd: repo,
    encoding: 'utf8',
    maxBuffer: 64 * 1024 * 1024,
  }),
);
const allLessons = [...lessons, ...expansionLessons];

const markup = await import(pathToFileURL(resolve(repo, 'scripts/web_markup_assertions.mjs')).href);
const expansionOracle = await import(pathToFileURL(resolve(repo, 'scripts/css_expansion_assertions.mjs')).href);
const { chromium } = await import(pathToFileURL(resolve(repo, 'node_modules/playwright/index.mjs')).href);

// The cases that branch on the rendered width. Pass --all to exercise every
// baseline example under the host-owned constraints, --expansion to include the
// 60 authored lessons (whose pinViewport must also survive a host-owned window).
const ALL = process.argv.includes('--all');
const WITH_EXPANSION = process.argv.includes('--expansion');
const BASE_IDS = ALL
  ? lessons.map((l) => l.id)
  : ['css-example-002', 'css-example-011', 'css-example-015', 'css-example-044', 'css-example-051', 'css-example-064', 'css-example-090'];
const IDS = WITH_EXPANSION ? [...BASE_IDS, ...expansionLessons.map((l) => l.id)] : BASE_IDS;
const WIDTHS = ALL ? [412, 800, 1280] : [360, 412, 599, 600, 800, 900, 1280];

let currentHtml = '';
const server = createServer((req, res) => {
  res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
  res.end(currentHtml);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const origin = `http://127.0.0.1:${server.address().port}/`;

const marker = (code) =>
  code.replace('</body>', '  <output id="webforge-check" hidden>ok</output>\n</body>');

/** Wrap a Page so it looks like a host-owned window: no viewport, no resizing. */
function hostOwnedPage(page) {
  return new Proxy(page, {
    get(target, prop) {
      if (prop === 'viewportSize') return () => null;
      if (prop === 'setViewportSize') {
        return async () => {
          throw new Error('Cannot change the viewport size of a host-owned window');
        };
      }
      const value = target[prop];
      return typeof value === 'function' ? value.bind(target) : value;
    },
  });
}

const browser = await chromium.launch();
const rows = [];

for (const width of WIDTHS) {
  for (const id of IDS) {
    const lesson = allLessons.find((l) => l.id === id);
    const context = await browser.newContext({ viewport: { width, height: 800 } });
    const page = await context.newPage();
    page.setDefaultTimeout(6000);
    currentHtml = marker(lesson.code);

    const checks = [];
    const addCheck = (name, ok, detail = '') => checks.push({ name, ok: !!ok, detail: String(detail ?? '') });

    let thrown = null;
    try {
      await page.goto(origin, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(250);
      await markup.assertMarkupExample(
        hostOwnedPage(page),
        { id, language: 'css', code: currentHtml },
        addCheck,
      );
      await expansionOracle.assertExpansionExample(
        hostOwnedPage(page),
        { id, language: 'css', code: currentHtml },
        addCheck,
      );
    } catch (e) {
      thrown = String(e).split('\n')[0];
    }

    const failed = checks.filter((c) => !c.ok);
    // Cases whose assertions branch on the rendered width must have taken the
    // fallback path; 002 and 044 are width-tolerant by design and have none.
    const branched = id !== 'css-example-002' && id !== 'css-example-044' &&
      !['css-example-011', 'css-example-015', 'css-example-051', 'css-example-064', 'css-example-090'].includes(id);
    const usedFallback = checks.some((c) => /(at the real (\d+px|width)|wide \(\d+px|narrow \(\d+px)/.test(c.name));
    rows.push({ width, id, checks: checks.length, failed, thrown, usedFallback, branched, names: checks.map((c) => c.name) });
    await page.close();
    await context.close();
  }
}

await browser.close();
await new Promise((r) => server.close(r));

let md = '# Host-owned viewport (no resizing) — responsive fallbacks\n\n';
md += `Simulated: \`viewportSize() === null\` and \`setViewportSize()\` throws, at ${WIDTHS.join(', ')} px.\n\n`;
md += '| width | id | checks | fallback branch | result | first failure |\n| --- | --- | --- | --- | --- | --- |\n';
let failures = 0;
for (const r of rows) {
  const bad = r.thrown || r.failed.length > 0;
  if (bad) failures++;
  const first = r.thrown || (r.failed[0] ? `${r.failed[0].name} (${r.failed[0].detail})` : '');
  md += `| ${r.width} | ${r.id} | ${r.checks} | ${r.usedFallback ? 'yes' : 'no (resizable)'} | ${bad ? 'FAIL' : 'pass'} | ${String(first).replace(/\|/g, '\\|').slice(0, 120)} |\n`;
}

// The fallback must actually engage for every case that branches on width.
const BRANCHING = ['css-example-011', 'css-example-015', 'css-example-051', 'css-example-064', 'css-example-090'];
const branchedRows = rows.filter((r) => BRANCHING.includes(r.id));
const missingFallback = branchedRows.filter((r) => !r.usedFallback);
md += `\nRows: ${rows.length}. Failures: ${failures}.\n`;
md += `Width-branching rows: ${branchedRows.length}. Of those, rows that did NOT use the width fallback: ${missingFallback.length}.\n`;
if (missingFallback.length) {
  md += `\n${missingFallback.map((r) => `- ${r.width}px ${r.id}`).join('\n')}\n`;
}

writeFileSync(resolve(here, ALL ? 'css-host-viewport-all.md' : 'css-host-viewport.md'), md, 'utf8');
console.log(md);
process.exit(failures === 0 && missingFallback.length === 0 ? 0 : 1);
