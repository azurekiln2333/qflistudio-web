#!/usr/bin/env node
// Observe the production response policy. Routing is only a fail-closed guard:
// a forbidden request reaching it is a failure, never proof of CSP enforcement.
import assert from 'node:assert/strict';
import { chromium } from 'playwright';

let input = '';
for await (const chunk of process.stdin) input += chunk;
const { baseUrl, externalSocketUrl, externalObjectUrls, reportPageUrl, catalogPages } = JSON.parse(input);
const origin = new URL(baseUrl).origin;
const externalObjectOrigin = new URL(externalObjectUrls[0]).origin;
assert.notEqual(externalObjectOrigin, origin);
assert.equal(externalObjectUrls.length, 2);
assert.ok(externalObjectUrls.every(url => new URL(url).origin === externalObjectOrigin));
assert.equal(new URL(baseUrl).hostname, '127.0.0.1');
const browser = await chromium.launch();
let phase = 'launch';
let page;
try {
  const context = await browser.newContext({ serviceWorkers: 'block' });
  const escapedRequests = [];
  await context.route('**/*', async (route) => {
    const url = route.request().url();
    const parsed = new URL(url);
    if (parsed.protocol !== 'data:' && parsed.origin !== origin) {
      escapedRequests.push(url);
      await route.abort('blockedbyclient');
    } else {
      await route.continue();
    }
  });
  page = await context.newPage();
  page.setDefaultTimeout(5000);
  page.setDefaultNavigationTimeout(5000);
  await page.addInitScript(() => {
    window.__offlineCatalogPolicyViolations = [];
    document.addEventListener('securitypolicyviolation', event => {
      window.__offlineCatalogPolicyViolations.push({ directive: event.effectiveDirective, uri: event.blockedURI });
    });
  });
  phase = 'load';
  const response = await page.goto(baseUrl, { waitUntil: 'load' });
  assert.equal(response.status(), 200);
  phase = 'fetch settlement';
  await page.waitForFunction(() => window.__offlineFetchDone === true);
  await page.waitForFunction((url) => window.__offlineViolations.some((item) => item.directive === 'connect-src' && item.uri === url), externalSocketUrl);
  phase = 'cross-origin loopback objects';
  // Cross-origin CSP reports may strip the path from blockedURI. Both nodes
  // must be blocked; an allowed load still fails the route and real sentinels.
  await page.waitForFunction((blockedOrigin) => window.__offlineViolations.filter(item =>
    item.directive === 'object-src' && (item.uri === blockedOrigin || item.uri.startsWith(`${blockedOrigin}/`))).length >= 2, externalObjectOrigin);
  phase = 'form gesture';
  await page.locator('#external-form button').click({ noWaitAfter: true });
  phase = 'form policy violation';
  await page.waitForFunction(() => window.__offlineViolations.some((item) => item.directive === 'form-action'));
  phase = 'same-origin object document';
  await page.waitForFunction(() => document.querySelector('#local-object')
    ?.contentDocument?.querySelector('#local-object-content')?.textContent === 'Local object document');
  phase = 'policy assertions';
  const observed = await page.evaluate(() => ({
    violations: window.__offlineViolations,
    localScript: window.__offlineLocalScript,
    evaluated: window.__offlineEval,
    fetchBlocked: window.__offlineFetchBlocked,
    websocketError: window.__offlineWebsocketError,
    color: getComputedStyle(document.querySelector('#local')).color,
    localObject: document.querySelector('#local-object').contentDocument.querySelector('#local-object-content').textContent,
    url: location.href,
  }));
  assert.equal(observed.localScript, 'loaded-from-project');
  assert.equal(observed.localObject, 'Local object document', 'Same-origin object documents remain usable');
  assert.equal(observed.evaluated, 42);
  assert.equal(observed.color, 'rgb(0, 128, 0)');
  assert.equal(observed.fetchBlocked, true);
  assert.ok(observed.violations.some((item) => item.directive === 'connect-src' && item.uri === externalSocketUrl));
  assert.equal(observed.url, baseUrl);
  assert.deepEqual(escapedRequests, [], 'CSP must block before the safety route');
  for (const directive of ['script-src-elem', 'style-src-elem', 'img-src', 'frame-src', 'connect-src', 'form-action']) {
    assert.ok(observed.violations.some((item) => item.directive === directive && item.uri.includes('qfli-offline.invalid')), directive);
  }
  assert.ok(observed.violations.filter(item => item.directive === 'object-src'
    && (item.uri === externalObjectOrigin || item.uri.startsWith(`${externalObjectOrigin}/`))).length >= 2,
  'Objects and embeds at another loopback port remain blocked');
  for (const kind of ['object', 'embed']) {
    assert.ok(observed.violations.some((item) => item.directive === 'object-src' && item.uri.includes(`${kind}.qfli-offline.invalid`)), `${kind} stays blocked before the safety route`);
  }
  phase = 'proxied report policy';
  const reportResponse = await page.goto(reportPageUrl, { waitUntil: 'load' });
  assert.equal(reportResponse.status(), 200);
  for (const header of ['content-security-policy-report-only', 'reporting-endpoints', 'report-to', 'nel']) {
    assert.equal(reportResponse.headers()[header], undefined, header);
  }
  await page.waitForTimeout(100);
  const reporting = await page.evaluate(() => ({ marker: window.__reportMarker, violations: window.__reportViolations }));
  assert.equal(reporting.marker, 42, 'Local proxied scripts still execute');
  assert.deepEqual(reporting.violations, [], 'No upstream report-only policy may run');
  const catalogAssertions = {
    'html-example-027': async () => {
      await page.waitForFunction(() => getComputedStyle(document.body).color === 'rgb(26, 115, 232)');
      const style = await page.evaluate(() => ({ color: getComputedStyle(document.body).color, fontFamily: getComputedStyle(document.body).fontFamily }));
      assert.equal(style.color, 'rgb(26, 115, 232)', 'Shipped data stylesheet applies');
      assert.ok(style.fontFamily.includes('sans-serif'));
      return style;
    },
    'html-example-097': async () => {
      await page.waitForFunction(() => {
        const style = getComputedStyle(document.querySelector('.lazy'));
        return style.color === 'rgb(107, 114, 128)' && style.fontStyle === 'italic';
      });
      const style = await page.evaluate(() => {
        const lazy = getComputedStyle(document.querySelector('.lazy'));
        return { color: lazy.color, fontStyle: lazy.fontStyle };
      });
      assert.equal(style.color, 'rgb(107, 114, 128)', 'Shipped Blob stylesheet applies');
      assert.equal(style.fontStyle, 'italic');
      return style;
    },
    'html-example-137': async () => {
      await page.waitForFunction(() => {
        const figure = document.querySelector('#figure');
        return figure.contentDocument?.querySelector('#inner')?.textContent === '运行内联的 HTML 文档'
          && document.querySelector('#state')?.textContent.includes('内嵌根元素=html');
      });
      const embedded = await page.evaluate(() => {
        const figure = document.querySelector('#figure');
        return {
          text: figure.contentDocument.querySelector('#inner').textContent,
          root: figure.contentDocument.documentElement.tagName.toLowerCase(),
          state: document.querySelector('#state').textContent,
        };
      });
      assert.equal(embedded.text, '运行内联的 HTML 文档', 'Shipped Blob HTML document loads');
      assert.equal(embedded.root, 'html');
      assert.equal(embedded.state, 'type=text/html / data 是 Blob=true / 内嵌根元素=html / 内嵌文本=运行内联的 HTML 文档 / 回退段数=1');
      const bounds = await page.locator('#figure').boundingBox();
      assert.equal(bounds.width, 240);
      assert.equal(bounds.height, 80);
      return embedded;
    },
    'html-example-138': async () => {
      await page.waitForFunction(() => document.querySelector('#state')?.textContent.includes('内部文本=srcdoc 渲染的内容'));
      const isSvgFrame = frame => frame.parentFrame() === page.mainFrame() && frame.url().startsWith('data:image/svg+xml');
      const svgFrame = page.frames().find(isSvgFrame)
        ?? await page.waitForEvent('framenavigated', { predicate: isSvgFrame });
      await svgFrame.waitForSelector('circle');
      const embedded = await svgFrame.evaluate(() => {
        const svg = document.documentElement.getBoundingClientRect();
        const circle = document.querySelector('circle');
        const bounds = circle.getBoundingClientRect();
        return {
          fill: getComputedStyle(circle).fill,
          svgWidth: svg.width,
          svgHeight: svg.height,
          circleWidth: bounds.width,
          circleHeight: bounds.height,
        };
      });
      assert.deepEqual(embedded, { fill: 'rgb(26, 115, 232)', svgWidth: 80, svgHeight: 40, circleWidth: 32, circleHeight: 32 }, 'Shipped data SVG is decoded and rendered in the actual embed');
      const bounds = await page.locator('#emb').boundingBox();
      assert.equal(bounds.width, 80);
      assert.equal(bounds.height, 40);
      return embedded;
    },
    'js-example-017': async () => {
      await page.waitForFunction(() => document.querySelector('#out')?.textContent === 'WebForge 本地数据');
      const output = await page.locator('#out').textContent();
      assert.equal(output, 'WebForge 本地数据', 'Shipped fetch reads its local Blob JSON');
      return { output };
    },
  };
  assert.deepEqual(Object.keys(catalogPages), Object.keys(catalogAssertions));
  const catalogChecks = [];
  for (const [id, check] of Object.entries(catalogAssertions)) {
    phase = `shipped catalog ${id}`;
    const catalogResponse = await page.goto(catalogPages[id], { waitUntil: 'load' });
    assert.equal(catalogResponse.status(), 200, id);
    assert.equal(catalogResponse.headers()['content-security-policy'], response.headers()['content-security-policy'], id);
    const result = await check();
    const violations = await page.evaluate(() => window.__offlineCatalogPolicyViolations);
    assert.deepEqual(violations, [], `${id} must remain usable under the production policy`);
    catalogChecks.push({ id, ...result, violations });
  }
  assert.deepEqual(escapedRequests, []);
  process.stdout.write(`${JSON.stringify({ browserVersion: browser.version(), policy: response.headers()['content-security-policy'], escapedRequests, reporting, catalogChecks, ...observed })}\n`);
} catch (error) {
  const observed = page && !page.isClosed()
    ? await page.evaluate(() => ({ url: location.href, ready: window.__offlineFetchDone, violations: window.__offlineViolations, catalogViolations: window.__offlineCatalogPolicyViolations, output: document.querySelector('#out')?.textContent, state: document.querySelector('#state')?.textContent })).catch(() => null)
    : null;
  process.stderr.write(`${JSON.stringify({ phase, observed })}\n`);
  throw error;
} finally {
  await browser.close();
}
