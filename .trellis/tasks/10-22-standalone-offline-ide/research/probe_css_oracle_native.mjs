// Run the REAL CSS oracles against the REAL packaged cases on the native
// ArkWeb page, and capture every check (name, ok, detail).
//
// Reuses the single existing page (no context/page creation). Never closes the
// page; browser.close() only drops the CDP transport, like run_examples.mjs.
// Restores the page to the packaged bootstrap URL when finished.
//
// Usage: node probe_css_oracle_native.mjs <id>[,<id>...] [--report <path>]
import { resolve, dirname } from 'node:path';
import { writeFileSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../../../..');
const CDP = process.env.NATIVE_CDP || 'http://127.0.0.1:9222';

const argv = process.argv.slice(2);
const argValue = (name, fallback = '') => {
  const i = argv.indexOf(name);
  return i >= 0 && argv[i + 1] ? argv[i + 1] : fallback;
};
const ids = (argv[0] || '').split(',').map((s) => s.trim()).filter(Boolean);
const reportPath = argValue('--report', resolve(here, 'probe-css-oracle-native.md'));
if (!ids.length) {
  console.error('usage: node probe_css_oracle_native.mjs <id>[,<id>...]');
  process.exit(1);
}

const markup = await import(pathToFileURL(resolve(repo, 'scripts/web_markup_assertions.mjs')).href);
const expansion = await import(pathToFileURL(resolve(repo, 'scripts/css_expansion_assertions.mjs')).href);
const { OHOS_BOOTSTRAP_URL } = await import(pathToFileURL(resolve(repo, 'scripts/catalog_device_contract.mjs')).href);
const { chromium } = await import(pathToFileURL(resolve(repo, 'node_modules/playwright/index.mjs')).href);

const browser = await chromium.connectOverCDP(CDP);
const pages = browser.contexts().flatMap((c) => c.pages());
const candidates = pages.filter((p) => {
  try {
    const url = new URL(p.url());
    return url.hostname === '127.0.0.1' && Number(url.port) >= 19999 && Number(url.port) <= 65535;
  } catch {
    return false;
  }
});
if (candidates.length !== 1) {
  console.error(`expected exactly one native test target, got ${candidates.length}`);
  await browser.close();
  process.exit(2);
}
const page = candidates[0];
page.setDefaultTimeout(15000);

const bootstrapUrl = OHOS_BOOTSTRAP_URL;
await page.goto(bootstrapUrl, { waitUntil: 'domcontentloaded' });
const catalog = await page.evaluate(() => window.__QFLI_OHOS_CATALOG__);
const caseUrls = new Map();
const collect = (node) => {
  if (!node || typeof node !== 'object') return;
  if (Array.isArray(node)) {
    for (const item of node) collect(item);
    return;
  }
  if (typeof node.id === 'string' && typeof node.url === 'string') caseUrls.set(node.id, node.url);
  for (const value of Object.values(node)) collect(value);
};
collect(catalog);

const rows = [];
for (const id of ids) {
  const url = caseUrls.get(id);
  if (!url) {
    rows.push({ id, checks: [], thrown: 'no packaged url', ok: false });
    continue;
  }
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(200);

  const checks = [];
  const addCheck = (name, ok, detail = '') => checks.push({ name, ok: !!ok, detail: String(detail ?? '') });
  let thrown = null;
  try {
    const example = { id, language: 'css', code: '' };
    const handled =
      (await markup.assertMarkupExample(page, example, addCheck)) ||
      (await expansion.assertExpansionExample(page, example, addCheck));
    if (!handled) addCheck('handled by an oracle', false, 'no case registered');
  } catch (e) {
    thrown = String(e).split('\n')[0].slice(0, 220);
  }
  rows.push({ id, checks, thrown, ok: !thrown && checks.every((c) => c.ok) });
}

// Leave the page on the packaged bootstrap, exactly as the runner does.
await page.goto(bootstrapUrl, { waitUntil: 'domcontentloaded' }).catch(() => {});
await browser.close(); // transport only

let md = '# Native ArkWeb probe — real CSS oracles on packaged cases\n\n';
md += `Generated: ${new Date().toISOString()}\n\n`;
md += `| id | result | failing checks |\n| --- | --- | --- |\n`;
for (const r of rows) {
  const bad = r.checks.filter((c) => !c.ok);
  md += `| ${r.id} | ${r.ok ? 'pass' : 'FAIL'} | ${(r.thrown || bad.map((c) => `${c.name}${c.detail ? ` (${c.detail})` : ''}`).join('<br>') || '').replace(/\|/g, '\\|').slice(0, 400)} |\n`;
}
md += '\n## All checks\n';
for (const r of rows) {
  md += `\n### ${r.id}\n`;
  if (r.thrown) md += `THREW: ${r.thrown}\n`;
  for (const c of r.checks) {
    md += `- ${c.ok ? 'ok  ' : 'FAIL'} ${c.name}${c.detail ? ` — ${c.detail}` : ''}\n`;
  }
}
writeFileSync(reportPath, md, 'utf8');
console.log(md.split('\n').slice(0, 30).join('\n'));
console.log(`\nreport: ${reportPath}`);
