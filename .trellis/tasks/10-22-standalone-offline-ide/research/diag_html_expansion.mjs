// Task-local diagnostic probe: prints raw page state for selected ids so the
// authored expectations can be corrected against the real Chromium result.
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from 'node:http';
import { chromium } from 'playwright';

const here = dirname(fileURLToPath(import.meta.url));
const docs = JSON.parse(readFileSync(resolve(here, 'html-expansion-documents.json'), 'utf8'));
const wanted = process.argv.slice(2);
const targets = docs.filter((d) => wanted.includes(d.id));

let current = '';
const server = createServer((req, res) => {
  res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
  res.end(current);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const origin = `http://127.0.0.1:${server.address().port}/`;
const browser = await chromium.launch();

for (const doc of targets) {
  const page = await browser.newPage();
  const errs = [];
  page.on('pageerror', (e) => errs.push(String(e).split('\n')[0]));
  current = doc.code;
  await page.goto(origin, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(500);
  console.log('='.repeat(70));
  console.log(doc.id, doc.title, errs.length ? `ERR: ${errs.join(' ; ')}` : '');
  const dump = await page.evaluate(() => {
    const q = (s) => document.querySelector(s);
    const out = {};
    out.state = (q('#state') && q('#state').textContent) || null;
    out.status = (q('#status') && q('#status').textContent) || null;
    out.meta = (q('#meta') && q('#meta').textContent) || null;
    out.msg = (q('#msg') && q('#msg').textContent) || null;
    out.count = (q('#count') && q('#count').textContent) || null;
    out.h2 = q('h2') ? q('h2').textContent : null;
    // generic element info for selectors of interest
    const info = (sel) => {
      const el = q(sel);
      if (!el) return null;
      const cs = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      return {
        text: el.textContent,
        tag: el.tagName.toLowerCase(),
        js: el,
        w: Math.round(r.width),
        h: Math.round(r.height),
        display: cs.display,
        direction: cs.direction,
        unicodeBidi: cs.unicodeBidi,
        contentVisibility: cs.contentVisibility,
        fontStyle: cs.fontStyle,
      };
    };
    out.info = {};
    for (const sel of ['#zh', '#zh rt', '#user', '#forced', '#auto', '#einstein', '#avg mfrac', '#board', '#clip', '#chart-title', '#chart-desc', '#card', '#chip', '#status', '#details']) {
      const i = info(sel);
      if (i) {
        delete i.js;
        out.info[sel] = i;
      }
    }
    out.mathML = !!(window.MathMLElement);
    out.subCount = document.querySelectorAll('sub').length;
    out.supCount = document.querySelectorAll('sup').length;
    out.bdiCount = document.querySelectorAll('bdi').length;
    out.shadow = q('#card') ? q('#card').shadowRoot !== null : null;
    out.children0 = q('#chip') ? q('#chip').shadowRoot !== null : null;
    out.trackCues = (() => {
      const clip = q('#clip');
      if (!clip || !clip.textTracks || !clip.textTracks[0]) return null;
      const t = clip.textTracks[0];
      return { kind: t.kind, cues: t.cues ? t.cues.length : 0, first: t.cues && t.cues[0] ? t.cues[0].text : null };
    })();
    out.objectDoc = (() => {
      const o = q('#figure');
      if (!o) return 'no-object';
      return o.contentDocument ? o.contentDocument.documentElement.tagName : null;
    })();
    out.dpr = window.devicePixelRatio;
    out.canvas = (() => {
      const c = q('#board');
      if (!c) return null;
      const cs = getComputedStyle(c);
      return { attrW: c.width, attrH: c.height, cssW: cs.width, cssH: cs.height, rect: Math.round(c.getBoundingClientRect().width), textContent: c.textContent };
    })();
    return out;
  });
  console.log(JSON.stringify(dump, null, 1));
  await page.close();
}
await browser.close();
await server.close();
