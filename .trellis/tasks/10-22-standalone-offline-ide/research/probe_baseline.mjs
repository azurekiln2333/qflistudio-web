// Probe computed values for baseline CSS lessons so oracle literals are real.
//
// Usage:
//   node probe_baseline.mjs <id> <width|x0> '<json steps>'
// steps: [{ "op": "viewport", "width": 500, "height": 720 },
//         { "op": "click"|"hover"|"focus"|"media", "sel"|"media" },
//         { "op": "wait", "ms": 500 },
//         { "op": "dump", "label": "x", "spec": ["sel|prop1,prop2", "sel::after|content"] },
//         { "op": "rect", "label": "x", "sel": ".card" },
//         { "op": "count", "label": "x", "sel": ".card" },
//         { "op": "eval", "label": "x", "js": "return 1" }]
import { execFileSync } from 'node:child_process';
import { resolve, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createServer } from 'node:http';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../../../..');

import { readFileSync } from 'node:fs';

const id = Number(process.argv[2]);
const widthArg = process.argv[3] || '1280';
const stepsArg = process.argv[4] || '[]';
const steps = JSON.parse(
  stepsArg.startsWith('@') ? readFileSync(stepsArg.slice(1), 'utf8') : stepsArg,
);

const lesson = JSON.parse(
  execFileSync(
    'python',
    [
      '-X',
      'utf8',
      '-c',
      `import json,sys
sys.path.insert(0, ${JSON.stringify(resolve(repo, 'scripts'))})
from curriculum import css_data, css_data2, css_data3, css_data4, css_data5, supplement
base = css_data.CSS + css_data2.CSS2 + css_data3.CSS3 + css_data4.CSS4 + css_data5.CSS5 + supplement.CSS6
print(json.dumps(base[${id} - 1], ensure_ascii=False))`,
    ],
    { cwd: repo, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 },
  ),
);

const { chromium } = await import(pathToFileURL(resolve(repo, 'node_modules/playwright/index.mjs')).href);

let html = lesson.code;
const server = createServer((req, res) => {
  res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
  res.end(html);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const origin = `http://127.0.0.1:${server.address().port}/`;

const browser = await chromium.launch();
const context = await browser.newContext(
  widthArg === 'native' ? { viewport: null } : { viewport: { width: Number(widthArg), height: 720 } },
);
const page = await context.newPage();
page.setDefaultTimeout(4000);
await page.goto(origin, { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(300);

const out = {};
const rectOf = (sel) =>
  page.locator(sel).first().evaluate((el) => {
    const r = el.getBoundingClientRect();
    return { x: +r.x.toFixed(2), y: +r.y.toFixed(2), w: +r.width.toFixed(2), h: +r.height.toFixed(2) };
  });

for (const step of steps) {
  if (step.op === 'viewport') {
    try {
      await page.setViewportSize({ width: step.width, height: step.height ?? 720 });
      await page.waitForTimeout(200);
      out[`viewport:${step.width}`] = 'ok';
    } catch (e) {
      out[`viewport:${step.width}`] = `FAILED ${String(e).split('\n')[0]}`;
    }
  } else if (step.op === 'click') {
    await page.click(step.sel);
    await page.waitForTimeout(step.ms ?? 250);
  } else if (step.op === 'hover') {
    await page.hover(step.sel);
    await page.waitForTimeout(step.ms ?? 250);
  } else if (step.op === 'focus') {
    await page.focus(step.sel);
    await page.waitForTimeout(step.ms ?? 150);
  } else if (step.op === 'key') {
    await page.keyboard.press(step.key);
    await page.waitForTimeout(step.ms ?? 150);
  } else if (step.op === 'media') {
    await page.emulateMedia({ media: step.media });
    await page.waitForTimeout(step.ms ?? 200);
  } else if (step.op === 'wait') {
    await page.waitForTimeout(step.ms ?? 300);
  } else if (step.op === 'scroll') {
    await page.evaluate((y) => window.scrollTo(0, y), step.y);
    await page.waitForTimeout(200);
  } else if (step.op === 'dump') {
    const result = {};
    for (const spec of step.spec) {
      const [sel, props] = spec.split('|');
      if (props === 'rect') {
        result[spec] = await rectOf(sel).catch(() => null);
        continue;
      }
      result[spec] = await page
        .locator(sel)
        .first()
        .evaluate((el, list) => {
          const cs = getComputedStyle(el);
          const acc = {};
          for (const p of list.split(',')) acc[p] = cs.getPropertyValue(p).trim();
          return acc;
        }, props)
        .catch((e) => `ERR ${String(e).split('\n')[0]}`);
    }
    out[step.label || `dump${Object.keys(out).length}`] = result;
  } else if (step.op === 'mousedown') {
    const target = step.sel || '.btn';
    const box = await page.locator(target).first().boundingBox();
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.mouse.down();
    await page.waitForTimeout(step.ms ?? 200);
    out[step.label || 'mousedown'] = 'down';
  } else if (step.op === 'mouseup') {
    await page.mouse.up();
    await page.waitForTimeout(step.ms ?? 200);
    out[step.label || 'mouseup'] = 'up';
  } else if (step.op === 'pseudo') {
    out[step.label] = await page
      .locator(step.sel)
      .first()
      .evaluate((el, args) => {
        const cs = getComputedStyle(el, args.pseudo);
        const acc = {};
        for (const p of args.props.split(',')) acc[p] = cs.getPropertyValue(p).trim();
        return acc;
      }, { pseudo: step.pseudo, props: step.props })
      .catch((e) => `ERR ${String(e).split('\n')[0]}`);
  } else if (step.op === 'rect') {
    out[step.label] = await rectOf(step.sel).catch(() => null);
  } else if (step.op === 'count') {
    out[step.label] = await page.locator(step.sel).count();
  } else if (step.op === 'text') {
    out[step.label] = await page.locator(step.sel).first().innerText().catch(() => null);
  } else if (step.op === 'visible') {
    out[step.label] = await page.locator(step.sel).first().isVisible().catch(() => false);
  } else if (step.op === 'eval') {
    out[step.label] = await page.evaluate(new Function(step.js)).catch((e) => `ERR ${String(e).split('\n')[0]}`);
  }
}

out['__innerWidth'] = await page.evaluate(() => window.innerWidth);
out['__viewportSize'] = page.viewportSize();
console.log(JSON.stringify(out, null, 1));

await browser.close();
await new Promise((r) => server.close(r));
