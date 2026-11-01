// Lightweight lifecycle checks for the actual generated JS053 lesson script.
// This does not provide browser gesture, layout, permission or OHOS evidence.
// Run: node --test scripts/test_clipboard_lifecycle.mjs
// Old-asset negative: node scripts/test_clipboard_lifecycle.mjs --catalog <examples.json>
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const args = process.argv.slice(2);
if (args.length !== 0 && (args.length !== 2 || args[0] !== '--catalog')) {
  throw new Error('Expected no arguments or --catalog <examples.json>');
}
const catalogPath = args[1] || fileURLToPath(new URL('../assets/content/examples.json', import.meta.url));
const catalog = JSON.parse(readFileSync(catalogPath, 'utf8'));
const examples = catalog.entries.filter((entry) => entry.id === 'js-example-053');
assert.equal(examples.length, 1, 'catalog must contain exactly one JS053 document');
const documentCode = examples[0].code;
assert.match(documentCode, /\bid=["']paste["']/);
assert.match(documentCode, /\bid=["']out["']/);
const scripts = [...documentCode.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script\s*>/gi)];
assert.equal(scripts.length, 1, 'JS053 must expose one complete authored script');
assert.doesNotMatch(scripts[0][1], /\bsrc\s*=/i, 'lifecycle runner cannot supply external scripts');
const authoredScript = new vm.Script(scripts[0][2], { filename: 'generated-js-example-053.js' });

function createClock() {
  let now = 0;
  let nextId = 0;
  const timers = new Map();
  return {
    setTimeout(callback, delay = 0) {
      assert.equal(typeof callback, 'function');
      const id = ++nextId;
      timers.set(id, { callback, due: now + Math.max(0, Number(delay) || 0) });
      return id;
    },
    clearTimeout(id) { timers.delete(id); },
    advance(milliseconds) {
      const until = now + milliseconds;
      let callbacks = 0;
      for (;;) {
        const next = [...timers].filter(([, value]) => value.due <= until)
          .sort(([aId, a], [bId, b]) => a.due - b.due || aId - bId)[0];
        if (!next) break;
        if (++callbacks > 1000) throw new Error('Lesson timer loop exceeded the test budget');
        const [id, timer] = next;
        timers.delete(id);
        now = timer.due;
        timer.callback();
      }
      now = until;
    },
    pending: () => timers.size,
  };
}

function lesson({ supported = true, missingMethod = false, throwOnRead = null } = {}) {
  const clock = createClock();
  const listeners = [];
  const reads = [];
  const logs = [];
  const writes = [];
  const errors = [];
  const out = {
    get textContent() { return writes.at(-1) || ''; },
    set textContent(value) { writes.push(String(value)); },
  };
  const button = {
    addEventListener(event, listener) {
      assert.equal(event, 'click');
      listeners.push(listener);
    },
  };
  const clipboard = missingMethod ? {} : {
    readText() {
      if (throwOnRead) throw throwOnRead;
      let resolve;
      let reject;
      const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
      reads.push({ resolve, reject });
      return promise;
    },
  };
  const sandbox = {
    document: {
      getElementById(id) {
        if (id === 'out') return out;
        if (id === 'paste') return button;
        throw new Error(`Unexpected DOM dependency: ${id}`);
      },
    },
    navigator: supported ? { clipboard } : {},
    console: { log: (...values) => logs.push(values.map(String).join(' ')) },
    setTimeout: clock.setTimeout,
    clearTimeout: clock.clearTimeout,
  };
  authoredScript.runInNewContext(sandbox, { timeout: 1000 });
  assert.equal(listeners.length, 1, 'authored script must register the action handler');
  return {
    clock, reads, logs, writes,
    output: () => out.textContent,
    click() {
      // Dispatch the registered authored callback. Real reachable gestures are
      // separately covered by the Playwright/ArkWeb semantic oracle.
      for (const listener of listeners) {
        try {
          Promise.resolve(listener({ type: 'click', target: button }))
            .catch((error) => errors.push(error));
        } catch (error) { errors.push(error); }
      }
    },
    async flush() {
      // Drain the authored async handler's Promise continuations without real
      // wall-clock waits or running the deterministic watchdog clock.
      for (let turn = 0; turn < 8; turn++) await Promise.resolve();
      assert.deepEqual(errors, [], 'authored action must not escape with an unhandled error');
    },
  };
}

test('starts empty, shows progress synchronously and starts exactly one read', async () => {
  const page = lesson();
  assert.equal(page.output(), '');
  page.click();
  assert.equal(page.output(), '读取中');
  assert.equal(page.reads.length, 1);
  assert.deepEqual(page.logs, []);
  await page.flush();
  assert.equal(page.output(), '读取中');
});

test('success renders and logs supplied text and cancels the watchdog', async () => {
  const page = lesson();
  page.click();
  page.reads[0].resolve('中文 😀 <b>literal</b>');
  await page.flush();
  assert.equal(page.output(), '内容：中文 😀 <b>literal</b>');
  assert.deepEqual(page.logs, ['内容：中文 😀 <b>literal</b>']);
  assert.equal(page.clock.pending(), 0);
  page.clock.advance(2000);
  assert.equal(page.output(), '内容：中文 😀 <b>literal</b>');
});

test('denial renders the actual failure reason and cancels the watchdog', async () => {
  const page = lesson();
  page.click();
  page.reads[0].reject(new Error('Document is not focused'));
  await page.flush();
  assert.equal(page.output(), '读取失败：Document is not focused');
  assert.deepEqual(page.logs, ['读取失败：Document is not focused']);
  assert.equal(page.clock.pending(), 0);
});

for (const [name, options] of [
  ['missing clipboard API', { supported: false }],
  ['missing readText method', { missingMethod: true }],
]) {
  test(`${name} reports unsupported without starting a read`, async () => {
    const page = lesson(options);
    page.click();
    await page.flush();
    assert.equal(page.output(), '读取失败：不支持读取');
    assert.equal(page.reads.length, 0);
    assert.deepEqual(page.logs, ['读取失败：不支持读取']);
    assert.equal(page.clock.pending(), 0);
  });
}

test('synchronous platform exception becomes visible feedback', async () => {
  const page = lesson({ throwOnRead: new Error('Platform read failed') });
  page.click();
  await page.flush();
  assert.equal(page.output(), '读取失败：Platform read failed');
  assert.deepEqual(page.logs, ['读取失败：Platform read failed']);
  assert.equal(page.clock.pending(), 0);
});

test('a hanging read reaches a bounded timeout and logs it once', async () => {
  const page = lesson();
  page.click();
  page.clock.advance(400);
  assert.equal(page.output(), '读取中');
  page.clock.advance(600);
  await page.flush();
  assert.equal(page.output(), '读取超时');
  assert.deepEqual(page.logs, ['读取超时']);
  page.clock.advance(5000);
  assert.deepEqual(page.logs, ['读取超时']);
});

for (const completion of ['resolve', 'reject']) {
  test(`late ${completion} cannot replace the settled timeout`, async () => {
    const page = lesson();
    page.click();
    page.clock.advance(1000);
    page.reads[0][completion](completion === 'resolve' ? 'LATE' : new Error('Late denial'));
    await page.flush();
    assert.equal(page.output(), '读取超时');
    assert.deepEqual(page.logs, ['读取超时']);
    assert.equal(page.clock.pending(), 0);
  });
}

test('an older timeout cannot overwrite the newest successful read', async () => {
  const page = lesson();
  page.click();
  page.clock.advance(200);
  page.click();
  assert.equal(page.reads.length, 2);
  page.reads[1].resolve('LATEST');
  await page.flush();
  assert.equal(page.output(), '内容：LATEST');
  page.clock.advance(1000);
  await page.flush();
  assert.equal(page.output(), '内容：LATEST');
  assert.deepEqual(page.logs, ['内容：LATEST']);
});

for (const completion of ['resolve', 'reject']) {
  test(`an older ${completion} cannot replace latest progress or its result`, async () => {
    const page = lesson();
    page.click();
    page.clock.advance(200);
    page.click();
    assert.equal(page.reads.length, 2);
    page.reads[0][completion](completion === 'resolve' ? 'STALE' : new Error('Stale denial'));
    await page.flush();
    assert.equal(page.output(), '读取中');
    assert.deepEqual(page.logs, []);
    page.reads[1].resolve('LATEST');
    await page.flush();
    assert.equal(page.output(), '内容：LATEST');
    assert.deepEqual(page.logs, ['内容：LATEST']);
    page.clock.advance(2000);
    assert.equal(page.output(), '内容：LATEST');
  });
}

for (const completion of ['resolve', 'reject']) {
  test(`an older ${completion} cannot overwrite the newest successful result`, async () => {
    const page = lesson();
    page.click();
    page.clock.advance(200);
    page.click();
    page.reads[1].resolve('LATEST');
    await page.flush();
    page.reads[0][completion](completion === 'resolve' ? 'STALE' : new Error('Stale denial'));
    await page.flush();
    assert.equal(page.output(), '内容：LATEST');
    assert.deepEqual(page.logs, ['内容：LATEST']);
    assert.equal(page.clock.pending(), 0);
  });
}

test('only the newest hanging read may report its timeout', async () => {
  const page = lesson();
  page.click();
  page.clock.advance(400);
  page.click();
  page.clock.advance(500);
  await page.flush();
  assert.equal(page.output(), '读取中');
  assert.deepEqual(page.logs, []);
  page.clock.advance(500);
  await page.flush();
  assert.equal(page.output(), '读取超时');
  assert.deepEqual(page.logs, ['读取超时']);
});
