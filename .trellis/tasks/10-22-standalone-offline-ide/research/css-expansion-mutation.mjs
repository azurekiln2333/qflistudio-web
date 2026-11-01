// Mutation test: prove each expansion oracle fails when its lesson is broken.
//
// For every authored example, apply a small semantic mutation to the document
// (wrong colour / wrong size / removed rule) and require the oracle to report at
// least one failing check. A mutation that still passes means the assertion set
// is vacuous for that lesson.
import { execFileSync } from 'node:child_process';
import { resolve, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createServer } from 'node:http';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../../../..');

const lessons = JSON.parse(
  execFileSync(
    'python',
    [
      '-X',
      'utf8',
      '-c',
      `import json,sys
sys.path.insert(0, ${JSON.stringify(resolve(repo, 'scripts'))})
from curriculum import css_expansion
print(json.dumps(css_expansion.CSS_EXTRA, ensure_ascii=False))`,
    ],
    { cwd: repo, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 },
  ),
);

// One deterministic, semantic mutation per lesson: replace the first occurrence
// of a taught literal with something clearly different.
const MUTATIONS = {
  101: [['color: #1a73e8', 'color: #ea4335']],
  102: [['color: #202124 !important', 'color: #5f6368 !important']],
  103: [['color: #1a73e8', 'color: #ea4335']],
  104: [['initial-value: #1a73e8', 'initial-value: #ea4335']],
  105: [['color: #202124', 'color: #5f6368']],
  106: [['background: #e8f0fe', 'background: #ffffff']],
  107: [['border-color: #1a73e8', 'border-color: #ea4335']],
  108: [['border-color: #1a73e8', 'border-color: #34a853']],
  109: [['border-color: #ea4335', 'border-color: #fbbc04']],
  110: [['border-color: #1a73e8', 'border-color: #34a853']],
  111: [['content: "暂无数据"', 'content: "空"']],
  112: [['color: #1a73e8', 'color: #ea4335']],
  113: [['background: #1a73e8', 'background: #34a853']],
  114: [['flex: 1 1 0', 'flex: 1 1 auto']],
  115: [['order: 3', 'order: 0']],
  116: [['align-content: flex-start', 'align-content: center']],
  117: [['gap: 6px', 'gap: 16px']],
  118: [['grid-template-columns: 120px 1fr 80px', 'grid-template-columns: 200px 1fr 80px']],
  119: [['minmax(150px, 1fr)', 'minmax(80px, 1fr)']],
  120: [['grid-auto-rows: 40px', 'grid-auto-rows: 80px']],
  121: [['place-content: end space-between', 'place-content: start']],
  122: [['display: contents', 'display: block']],
  123: [['contain: layout paint', 'contain: none']],
  124: [['width: clamp(200px, 40vw, 320px)', 'width: clamp(200px, 40vw, 420px)']],
  125: [['width: fit-content', 'width: max-content']],
  126: [['inset-inline-start: 20px', 'inset-inline-start: 60px']],
  127: [['scroll-margin-top: 60px', 'scroll-margin-top: 0px']],
  128: [['height: 50dvh', 'height: 40dvh']],
  129: [['font-size: 10cqi', 'font-size: 20cqi']],
  130: [['max-width: 60ch', 'max-width: 30ch']],
  131: [['overflow-clip-margin: 10px', 'overflow-clip-margin: 30px']],
  132: [['oklch(0.6 0.17 255)', 'oklch(0.8 0.17 255)']],
  133: [['#1a73e8 50%, #ffffff', '#1a73e8 90%, #ffffff']],
  134: [['light-dark(#f1f3f4, #303134)', 'light-dark(#e8f0fe, #303134)']],
  135: [['calc(r + 60)', 'calc(r + 20)']],
  136: [['#ffffff 10px 20px', '#ffffff 10px 40px']],
  137: [['to right', 'to left']],
  138: [['mask-composite: intersect', 'mask-composite: add']],
  139: [['background-blend-mode: multiply', 'background-blend-mode: normal']],
  140: [['border: 8px solid transparent', 'border: 4px solid transparent']],
  141: [['text-emphasis-color: #1a73e8', 'text-emphasis-color: #ea4335']],
  142: [['-webkit-text-stroke: 2px #1a73e8', '-webkit-text-stroke: 1px #1a73e8']],
  143: [['text-wrap: balance', 'text-wrap: wrap']],
  144: [
    ['overflow-wrap: anywhere', 'overflow-wrap: normal'],
    // The containment guarantee is the pair `hyphens: auto` + the break-word
    // fallback, so removing the fallback must be caught on engines without a
    // hyphenation dictionary.
    ['hyphens: auto; overflow-wrap: break-word', 'hyphens: auto'],
  ],
  145: [['tabular-nums', 'proportional-nums']],
  146: [['text-underline-offset: 4px', 'text-underline-offset: 12px']],
  147: [['box-decoration-break: clone', 'box-decoration-break: slice']],
  148: [['text-box-trim: trim-both', 'text-box-trim: none']],
  149: [['allow-discrete', 'normal']],
  150: [['forwards', 'none']],
  151: [['cubic-bezier(0.2, 0.8, 0.2, 1)', 'linear']],
  152: [['animation-timeline: scroll(root)', 'animation-timeline: auto']],
  153: [['animation: none', 'animation: spin 1s linear infinite']],
  154: [['accumulate, accumulate', 'replace, replace']],
  155: [['scroll-snap-type: x mandatory', 'scroll-snap-type: none']],
  156: [['scrollbar-gutter: stable', 'scrollbar-gutter: auto']],
  157: [
    ['overscroll-behavior: contain', 'overscroll-behavior: auto'],
    // The bounded wheel fallback is the second half of the lesson; each of its two
    // essential parts must be independently required.
    ['if (atTop || atEnd) event.preventDefault();', ''],
    ['}, { passive: false });', '});'],
  ],
  158: [['field-sizing: content', 'field-sizing: fixed']],
  159: [['appearance: none', 'appearance: auto']],
  160: [['position-area: bottom', 'position-area: top']],
};

const markup = await import(pathToFileURL(resolve(repo, 'scripts/css_expansion_assertions.mjs')).href);
const { chromium } = await import(pathToFileURL(resolve(repo, 'node_modules/playwright/index.mjs')).href);
const browser = await chromium.launch();

let currentHtml = '';
const server = createServer((req, res) => {
  res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
  res.end(currentHtml);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const origin = `http://127.0.0.1:${server.address().port}/`;

const rows = [];
for (let i = 0; i < lessons.length; i++) {
  const n = 101 + i;
  const id = `css-example-${n}`;
  const lesson = lessons[i];
  for (const [from, to] of MUTATIONS[n] || []) {
    if (!from || !lesson.code.includes(from)) {
      rows.push({ id, mutation: `${from} -> ${to}`, applied: false, failed: 0, ok: false, note: 'mutation target missing' });
      continue;
    }
    const mutated = lesson.code.replace(from, to);
    currentHtml = mutated.replace('</body>', '  <output id="webforge-check" hidden>ok</output>\n</body>');

    const context = await browser.newContext({ viewport: { width: 960, height: 720 } });
    const page = await context.newPage();
    page.setDefaultTimeout(3000);
    const checks = [];
    let error = null;
    try {
      await page.goto(origin, { waitUntil: 'domcontentloaded', timeout: 15000 });
      await page.waitForTimeout(250);
      const addCheck = (name, ok, detail = '') => checks.push({ name, ok: !!ok, detail });
      await markup.assertExpansionExample(page, { id, code: currentHtml, language: 'css' }, addCheck);
    } catch (e) {
      error = String(e).split('\n')[0];
    }
    const failed = checks.filter((c) => !c.ok);
    rows.push({
      id,
      mutation: `${from.slice(0, 52)} -> ${to.slice(0, 20)}`,
      applied: true,
      failed: failed.length,
      ok: failed.length > 0 || error !== null,
      note: error || failed.slice(0, 2).map((c) => c.name).join('; '),
    });
    await page.close();
    await context.close();
  }
}

await browser.close();
await new Promise((r) => server.close(r));

const undetected = rows.filter((r) => !r.ok);
let md = '# Mutation test — do the expansion oracles detect broken lessons?\n\n';
md += `Mutations: ${rows.length}. Detected: ${rows.length - undetected.length}. Undetected: ${undetected.length}.\n\n`;
md += '| id | mutation | detected | first failing checks |\n| --- | --- | --- | --- |\n';
for (const r of rows) {
  md += `| ${r.id} | ${r.mutation.replace(/\|/g, '\\|')} | ${r.ok ? 'yes' : 'NO'} | ${String(r.note).replace(/\|/g, '\\|').slice(0, 110)} |\n`;
}
console.log(md);
process.exit(undetected.length === 0 ? 0 : 1);
