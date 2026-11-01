// Mutation test for the repaired baseline cases.
//
// For each repaired example, apply targeted semantic mutations (removed media
// query, wrong breakpoint, wrong colour/shadow/filter, flipped toggle wiring…)
// and require the oracle to fail at least one check. This proves the new
// assertions actually pin the lesson behaviour rather than passing vacuously.
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

// [id, label, from, to]
const MUTATIONS = [
  // 011 — breakpoint ladder
  ['css-example-011', 'drop the 900px breakpoint', '@media (min-width: 900px) { .grid { grid-template-columns: repeat(3, 1fr); } }', ''],
  ['css-example-011', 'move the 2-col breakpoint to 700px', '@media (min-width: 600px)', '@media (min-width: 700px)'],
  ['css-example-011', 'wrong gap', 'gap: 8px', 'gap: 20px'],
  // 015 — auto-fit
  ['css-example-015', 'drop auto-fit (fixed 3 columns)', 'repeat(auto-fit, minmax(160px, 1fr))', 'repeat(3, 1fr)'],
  ['css-example-015', 'shrink the minmax floor', 'minmax(160px, 1fr)', 'minmax(80px, 1fr)'],
  ['css-example-015', 'wrong radius', 'border-radius: 12px', 'border-radius: 4px'],
  // 021 — filters
  ['css-example-021', 'weaken grayscale', 'grayscale(1)', 'grayscale(0.2)'],
  ['css-example-021', 'wrong contrast', 'contrast(1.2)', 'contrast(2)'],
  ['css-example-021', 'wrong blur', 'blur(6px)', 'blur(1px)'],
  // 029 — print
  ['css-example-029', 'stop hiding the nav when printing', 'nav, button { display: none; }', 'button { display: none; }'],
  ['css-example-029', 'drop break-inside', '.card { break-inside: avoid; }', '.card { break-inside: auto; }'],
  ['css-example-029', 'print with dark background', 'background: #fff;', 'background: #333;'],
  // 035 — states
  ['css-example-035', 'disabled barely translucent', 'opacity: .5', 'opacity: .95'],
  ['css-example-035', 'hover shade equals base', '.btn:hover { background: #1557b0; }', '.btn:hover { background: #1a73e8; }'],
  ['css-example-035', 'no press sink', '.btn:active { transform: translateY(1px); }', ''],
  ['css-example-035', 'focus ring colour', 'outline: 3px solid #8ab4f8', 'outline: 3px solid #ff0000'],
  // 036 — shadows
  ['css-example-036', 'single-layer card shadow', '0 1px 2px rgba(0,0,0,.08), 0 4px 12px rgba(0,0,0,.08)', '0 1px 2px rgba(0,0,0,.08)'],
  ['css-example-036', 'wrong text shadow offset', 'text-shadow: 0 1px 2px rgba(0,0,0,.2)', 'text-shadow: 0 0 2px rgba(0,0,0,.2)'],
  // 041 — pseudo element
  ['css-example-041', 'drop the red top border', 'border-top-color: #ea4335;', ''],
  ['css-example-041', 'make the triangle edges opaque', 'border: 8px solid transparent;', 'border: 8px solid #ea4335;'],
  ['css-example-041', 'move the triangle off the corner', 'top: 0; right: 0;', 'top: 8px; right: 8px;'],
  // 044 — measure
  ['css-example-044', 'wrong measure', 'max-width: 65ch', 'max-width: 30ch'],
  ['css-example-044', 'wrong line height', 'line-height: 1.7', 'line-height: 1.2'],
  ['css-example-044', 'not centred', 'margin: 0 auto', 'margin: 0'],
  // 050 — switch
  ['css-example-050', 'checked state never turns blue', '.switch input:checked + .slider { background: #1a73e8; }', ''],
  ['css-example-050', 'knob does not slide', '.switch input:checked + .slider::before { transform: translateX(22px); }', ''],
  ['css-example-050', 'knob slides too far', 'translateX(22px)', 'translateX(40px)'],
  // 051 — holy grail
  ['css-example-051', 'drop the mobile collapse', '@media (max-width: 640px) { .holy { grid-template-columns: 1fr; grid-template-areas: "head" "left" "main" "right" "foot"; } }', ''],
  ['css-example-051', 'equal side columns instead of 3fr main', 'grid-template-columns: 1fr 3fr 1fr', 'grid-template-columns: 1fr 1fr 1fr'],
  ['css-example-051', 'drop the named areas', 'grid-template-areas: "head head head" "left main right" "foot foot foot"', ''],
  // 064 — hamburger
  ['css-example-064', 'toggle no longer reveals the menu', '#nav-toggle:checked ~ .menu { display: block; }', ''],
  ['css-example-064', 'burger never shows on mobile', '.burger { cursor: pointer; font-size: 22px; }', '.burger { display: none; cursor: pointer; font-size: 22px; }'],
  ['css-example-064', 'menu never becomes horizontal', '@media (min-width: 600px) { .burger { display: none; } .menu { display: flex; gap: 16px; } }', '@media (min-width: 600px) { .burger { display: none; } }'],
  // 090 — responsive variables
  ['css-example-090', 'variables never switch', '@media (min-width: 600px) { :root { --space: 16px; --title: 24px; } }', ''],
  ['css-example-090', 'variables switch at the wrong breakpoint', '@media (min-width: 600px)', '@media (min-width: 500px)'],
  ['css-example-090', 'card ignores --space', 'padding: var(--space)', 'padding: 4px'],
];

const markup = await import(pathToFileURL(resolve(repo, 'scripts/web_markup_assertions.mjs')).href);
const { chromium } = await import(pathToFileURL(resolve(repo, 'node_modules/playwright/index.mjs')).href);

let currentHtml = '';
const server = createServer((req, res) => {
  res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
  res.end(currentHtml);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const origin = `http://127.0.0.1:${server.address().port}/`;
const marker = (code) =>
  code.replace('</body>', '  <output id="webforge-check" hidden>ok</output>\n</body>');

const browser = await chromium.launch();
const rows = [];

for (const [id, label, from, to] of MUTATIONS) {
  const lesson = lessons.find((l) => l.id === id);
  if (!lesson.code.includes(from)) {
    rows.push({ id, label, applied: false, detected: false, note: 'mutation source not found' });
    continue;
  }
  const mutated = lesson.code.replace(from, to);
  currentHtml = marker(mutated);

  const context = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const page = await context.newPage();
  page.setDefaultTimeout(6000);
  const checks = [];
  const addCheck = (name, ok, detail = '') => checks.push({ name, ok: !!ok, detail: String(detail ?? '') });

  let thrown = null;
  try {
    await page.goto(origin, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(250);
    await markup.assertMarkupExample(page, { id, language: 'css', code: currentHtml }, addCheck);
  } catch (e) {
    thrown = String(e).split('\n')[0].slice(0, 160);
  }

  const failed = checks.filter((c) => !c.ok);
  rows.push({
    id,
    label,
    applied: true,
    detected: failed.length > 0 || thrown !== null,
    note: thrown ? `threw: ${thrown}` : failed.slice(0, 2).map((c) => c.name).join('; '),
  });
  await page.close();
  await context.close();
}

await browser.close();
await new Promise((r) => server.close(r));

const undetected = rows.filter((r) => !r.detected);
let md = '# Mutation test — repaired baseline CSS cases\n\n';
md += `Mutations: ${rows.length}. Detected: ${rows.length - undetected.length}. Undetected: ${undetected.length}.\n\n`;
md += '| id | mutation | detected | first failing checks |\n| --- | --- | --- | --- |\n';
for (const r of rows) {
  md += `| ${r.id} | ${r.label} | ${r.detected ? 'yes' : 'NO'} | ${String(r.note).replace(/\|/g, '\\|').slice(0, 130)} |\n`;
}
writeFileSync(resolve(here, 'css-repair-mutation.md'), md, 'utf8');
console.log(md);
process.exit(undetected.length === 0 ? 0 : 1);
