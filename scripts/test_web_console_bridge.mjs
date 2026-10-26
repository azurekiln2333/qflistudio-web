#!/usr/bin/env node
// Observe authored fixtures through the production preview endpoint. This
// harness never injects console calls or sends diagnostic POSTs itself.
import { chromium } from 'playwright';
import { get } from 'node:http';

let input = '';
for await (const chunk of process.stdin) input += chunk;
const { baseUrl, cases } = JSON.parse(input);
const origin = new URL(baseUrl).origin;
if (new URL(baseUrl).hostname !== '127.0.0.1') {
  throw new Error('A production loopback preview URL is required');
}

function previewBytes(url) {
  if (url.origin !== origin || url.protocol !== 'http:') {
    throw new Error('Raw source observation must stay on the preview origin');
  }
  return new Promise((resolve, reject) => {
    const request = get(url, { agent: false }, (response) => {
      if (response.statusCode !== 200) {
        response.resume();
        reject(new Error(`Raw source returned HTTP ${response.statusCode}`));
        return;
      }
      const chunks = [];
      let size = 0;
      response.on('data', (chunk) => {
        size += chunk.length;
        if (size > 1024 * 1024) {
          response.destroy(new Error('Raw fixture source exceeds 1 MiB'));
        } else {
          chunks.push(chunk);
        }
      });
      response.on('end', () => resolve(Buffer.concat(chunks)));
      response.on('error', reject);
    });
    request.setTimeout(5000, () => request.destroy(new Error('Raw source timed out')));
    request.on('error', reject);
  });
}

const browser = await chromium.launch({ headless: true });
const report = { browserVersion: browser.version(), externalRequests: [], cases: [] };
try {
  for (const fixture of cases) {
    const context = await browser.newContext({ serviceWorkers: 'block' });
    try {
      await context.route('**/*', async (route) => {
        const url = route.request().url();
        if (new URL(url).origin !== origin) {
          report.externalRequests.push(url);
          await route.abort('blockedbyclient');
        } else {
          await route.continue();
        }
      });
      const page = await context.newPage();
      page.setDefaultTimeout(5000);
      const consoleEvents = [];
      const errors = [];
      const posts = [];
      page.on('console', (event) => consoleEvents.push({ level: event.type(), message: event.text() }));
      page.on('pageerror', (error) => errors.push(error.message));
      page.on('response', (response) => {
        const request = response.request();
        if (request.method() === 'POST' && new URL(response.url()).pathname === '/__webforge/debug') {
          posts.push({ ...request.postDataJSON(), status: response.status(), origin: request.headers().origin });
        }
      });
      const response = await page.goto(new URL(fixture.path, baseUrl).href, { waitUntil: 'load' });
      if (!response || response.status() !== 200) throw new Error(`Fixture failed to load: ${fixture.path}`);
      if (fixture.done) {
        await page.waitForFunction((id) => window.__bridgeFixtureDone === id, fixture.done);
      }
      // Await actual network responses. On a regression keep observations for
      // the Dart assertion, including browser events absent from debugStream.
      const deadline = Date.now() + 1000;
      while (posts.length < fixture.expectedPosts && Date.now() < deadline) {
        await page.waitForTimeout(20);
      }
      // Chromium's response-body observation also consumes the UTF-8 BOM.
      // Read a second response over raw HTTP, without executing its scripts,
      // so exact-source/BOM retention remains a byte-level transport assertion.
      const sourceBytes = await previewBytes(new URL(fixture.path, baseUrl));
      const source = sourceBytes.toString('utf8');
      const bridge = /<script>\r?\n\(\(\) => \{[\s\S]*?\r?\n<\/script>\r?\n/g;
      const bridgeMatches = [...source.matchAll(bridge)];
      report.cases.push({
        path: fixture.path,
        status: response.status(),
        engineHeader: response.headers()['x-webforge-engine'] ?? null,
        sourceWithoutBridge: source.replace(bridge, ''),
        bridgeCount: bridgeMatches.length,
        consoleEvents,
        errors,
        posts,
        dom: await page.evaluate(() => ({
          compatMode: document.compatMode,
          fixture: document.body?.getAttribute('data-fixture') ?? null,
          headNote: document.head?.getAttribute('data-note') ?? null,
          rawStyle: document.querySelector('#raw-style')?.textContent ?? null,
          rawScript: document.querySelector('#raw-script')?.textContent ?? null,
          bridgeScripts: [...document.scripts].filter((script) => script.textContent.includes("fetch('/__webforge/debug'")).length,
        })),
      });
    } finally {
      await context.close();
    }
  }
  process.stdout.write(`${JSON.stringify(report)}\n`);
} finally {
  await browser.close();
}
