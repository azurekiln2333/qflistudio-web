// Prove BOTH css-156 branches are live and correctly attributed.
//
// Branch A (reserved === 0) is what ArkWeb does. This host engine reserves 15px,
// so the branch cannot be reached naturally here; it is exercised by neutralising
// `scrollbar-gutter` on every element with an author style, which makes the
// reservation 0 exactly like an engine that ignores the property.
import { execFileSync } from 'node:child_process';
import { resolve, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createServer } from 'node:http';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../../../..');

const dumpScript = `
import json, sys
sys.path.insert(0, ${JSON.stringify(resolve(repo, 'scripts'))})
from curriculum import css_expansion
print(json.dumps([{'id': f'css-example-{100 + i:03d}', 'code': x['code']} for i, x in enumerate(css_expansion.CSS_EXTRA, 1)], ensure_ascii=False))
`;
const lessons = JSON.parse(execFileSync('python', ['-X', 'utf8', '-c', dumpScript], { cwd: repo, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 }));
const lesson = lessons.find((l) => l.id === 'css-example-156');

const markup = await import(pathToFileURL(resolve(repo, 'scripts/css_expansion_assertions.mjs')).href);
const { chromium } = await import(pathToFileURL(resolve(repo, 'node_modules/playwright/index.mjs')).href);

const browser = await chromium.launch();
const server = createServer((req, res) => {
  res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
  res.end(current);
});
let current = '';
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const origin = `http://127.0.0.1:${server.address().port}/`;

const marker = (html) => html.replace('</body>', '  <output id="webforge-check" hidden>ok</output>\n</body>');

// Appended AFTER the lesson stylesheet so it wins the cascade. `scrollbar-width:
// none` removes the scrollbar and the gutter space entirely while leaving
// `scrollbar-gutter: stable` as the computed declaration — exactly the observable
// behaviour of an engine that accepts the property but reserves nothing (ArkWeb).
const KILL_GUTTER = '<style>*{scrollbar-width:none !important}</style>';

async function run(label, html, setup) {
  current = marker(html);
  const context = await browser.newContext({ viewport: { width: 960, height: 720 } });
  const page = await context.newPage();
  page.setDefaultTimeout(4000);
  const checks = [];
  let error = null;
  try {
    await page.goto(origin, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(200);
    if (setup) await setup(page);
    const addCheck = (name, ok, detail = '') => checks.push({ name, ok: !!ok, detail });
    await markup.assertExpansionExample(page, { id: 'css-example-156', code: current, language: 'css' }, addCheck);
  } catch (e) {
    error = String(e).split('\n')[0];
  }
  await page.close();
  await context.close();
  return { label, checks, error };
}

// 1. Unmodified lesson on this engine: the reservation branch must run.
const normal = await run('unmodified', lesson.code);

// 2. Gutter neutralised: the no-reservation branch must run, and the case must
//    still pass (because the lesson's guarantee then genuinely holds trivially).
const neutralised = await run('gutter neutralised (ArkWeb-like)', lesson.code.replace('</head>', `${KILL_GUTTER}</head>`));

// 3. Gutter neutralised AND the lesson rule removed: the declaration check must
//    fail, proving the case is not a free pass under the no-reservation branch.
const removed = await run('gutter rule removed under neutralisation', lesson.code.replace('scrollbar-gutter: stable;', '').replace('</head>', `${KILL_GUTTER}</head>`));

const rows = [];
for (const r of [normal, neutralised, removed]) {
  const failed = r.checks.filter((c) => !c.ok);
  rows.push({
    label: r.label,
    checks: r.checks.length,
    failed: failed.length,
    names: r.checks.map((c) => c.name).join(' | '),
    firstFailures: failed.map((c) => `${c.name} (${c.detail})`).join('; '),
    error: r.error,
  });
}

console.log(JSON.stringify(rows, null, 1));
await browser.close();
await new Promise((r) => server.close(r));

const reservationBranch = normal.checks.some((c) => c.name === 'the stable box reserves exactly what this engine reserves');
const noReservationBranch = neutralised.checks.some((c) => c.name === 'this engine reserves nothing for the stable gutter');
const removedFails = removed.checks.filter((c) => !c.ok).length > 0 || removed.error !== null;

console.log('\n=== branch liveness');
console.log('reservation branch ran:      ', reservationBranch);
console.log('no-reservation branch ran:   ', noReservationBranch);
console.log('neutralised case passes:     ', neutralised.checks.every((c) => c.ok));
console.log('rule-removed case fails:     ', removedFails);

process.exit(reservationBranch && noReservationBranch && neutralised.checks.every((c) => c.ok) && removedFails ? 0 : 1);
