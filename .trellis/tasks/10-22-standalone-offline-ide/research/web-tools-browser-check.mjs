import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const fixture = JSON.parse(await fs.readFile(process.argv[2], 'utf8'));
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
const requests = [];
await page.route('**/*', route => {
  requests.push(route.request().url());
  return route.abort();
});
async function observe(html, css) {
  await page.setContent(html);
  await page.addStyleTag({ content: css });
  await page.waitForFunction(() => getComputedStyle(document.querySelector('.probe')).height === '45px');
  return page.evaluate(() => {
    const probe = document.querySelector('.probe');
    const style = getComputedStyle(probe);
    return {
      text: probe.textContent,
      rawScript: document.querySelector('script').textContent,
      programValue: window.preserved,
      pre: document.querySelector('pre').textContent,
      textarea: document.querySelector('textarea').value,
      color: style.color,
      width: style.width,
      height: style.height,
      margin: style.margin,
      display: style.display,
      pseudoContent: getComputedStyle(probe, '::after').content,
    };
  });
}
try {
  const before = await observe(fixture.html, fixture.css);
  const after = await observe(fixture.formattedHtml, fixture.formattedCss);
  assert.deepEqual(after, before);
  assert.equal(after.color, 'rgb(255, 0, 0)');
  assert.equal(after.width, '123px');
  assert.equal(after.height, '45px');
  assert.equal(after.margin, '7px');
  assert.equal(after.display, 'grid');
  assert.equal(after.text, 'AB C');
  assert.equal(after.pseudoContent, '"a  b"');
  assert.deepEqual(fixture.rawTextFindings, []);
  const fragments = [];
  for (const fixtureFragment of fixture.fragments) {
    await page.setContent(fixtureFragment.source);
    const beforeText = await page.locator('body').innerText();
    await page.setContent(fixtureFragment.formatted);
    const afterText = await page.locator('body').innerText();
    assert.equal(afterText, beforeText);
    fragments.push({ beforeText, afterText });
  }
  assert.equal(fragments[0].afterText, 'AB');
  assert.equal(fragments[1].afterText, 'A B');
  assert.equal(fragments[2].afterText, 'first bold tail');
  assert.deepEqual(requests, []);
  const result = JSON.stringify({ status: 'pass', checks: 16, requests, before, after, fragments }, null, 2);
  if (process.argv[3]) await fs.writeFile(process.argv[3], result);
  process.stdout.write(result);
} finally {
  await browser.close();
}
