#!/usr/bin/env node
// Supplementary byte-protocol tests of the exact test-only ArkTS source.
// SDK/NAPI boundaries are fixtures. This is not ArkTS/native/ArkWeb acceptance.
import assert from 'node:assert/strict';
import { createHash, randomBytes } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { performance } from 'node:perf_hooks';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const DEFAULT_TYPESCRIPT = 'D:/ProgramFiles/Huawei/DevEco Studio/sdk/default/openharmony/ets/build-tools/ets-loader/node_modules/typescript/lib/typescript.js';
const typescriptPath = process.env.QFLI_OHOS_TYPESCRIPT || DEFAULT_TYPESCRIPT;
const ts = createRequire(import.meta.url)(typescriptPath);
const sourcePath = fileURLToPath(new URL('../ohos/entry/src/ohosTest/ets/testability/SelfCdpProof.ets', import.meta.url));
const source = readFileSync(sourcePath, 'utf8');
const sha256 = (value) => createHash('sha256').update(value).digest('hex');
const sourceHash = sha256(source);
const transpiled = ts.transpileModule(source, {
  fileName: sourcePath,
  reportDiagnostics: true,
  compilerOptions: { target: ts.ScriptTarget.ES2020, module: ts.ModuleKind.CommonJS, esModuleInterop: true },
});
const errors = (transpiled.diagnostics || []).filter((item) => item.category === ts.DiagnosticCategory.Error);
assert.equal(errors.length, 0, errors.map((item) => ts.flattenDiagnosticMessageText(item.messageText, '\n')).join('\n'));
const moduleScript = new vm.Script(transpiled.outputText, { filename: sourcePath });
const EMPTY = new ArrayBuffer(0);
const MAX_CASE_MS = 2000;
const MAX_SUITE_MS = 10000;
const MAX_FIXTURE_CALLS = 50000;
const MAX_FIXTURE_BYTES = 1024 * 1024;
const GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11';
const encoder = new TextEncoder();

function serverFrame(opcode, payload = Buffer.alloc(0), { final = true, masked = false } = {}) {
  payload = Buffer.from(payload);
  let prefix;
  if (payload.length < 126) prefix = Buffer.from([(final ? 128 : 0) | opcode, payload.length]);
  else if (payload.length <= 65535) {
    prefix = Buffer.alloc(4);
    prefix[0] = (final ? 128 : 0) | opcode;
    prefix[1] = 126;
    prefix.writeUInt16BE(payload.length, 2);
  } else {
    prefix = Buffer.alloc(10);
    prefix[0] = (final ? 128 : 0) | opcode;
    prefix[1] = 127;
    prefix.writeBigUInt64BE(BigInt(payload.length), 2);
  }
  if (!masked) return Buffer.concat([prefix, payload]);
  prefix[1] |= 128;
  const mask = Buffer.from([1, 2, 3, 4]);
  return Buffer.concat([prefix, mask, Buffer.from(payload.map((value, index) => value ^ mask[index % 4]))]);
}

const jsonFrame = (value) => serverFrame(1, Buffer.from(JSON.stringify(value)));

class ResourceResponse {
  setResponseData(value) { this.data = value; }
  setResponseCode(value) { this.code = value; }
  setReasonMessage(value) { this.reason = value; }
  setResponseMimeType(value) { this.mime = value; }
  setResponseEncoding(value) { this.encoding = value; }
  setResponseHeader(value) { this.headers = Array.from(value, (item) => ({ ...item })); }
}

class Fixture {
  constructor(options = {}) {
    this.options = options;
    this.active = new Map();
    this.connections = [];
    this.requests = [];
    this.frames = [];
    this.commands = [];
    this.closed = [];
    this.boundaryErrors = [];
    this.randomDraws = [];
    this.timers = new Map();
    this.timerRequests = [];
    this.calls = 0;
    this.queuedBytes = 0;
    this.writtenBytes = 0;
    this.readIndex = 0;
    this.writeIndex = 0;
    this.nextTimer = 1;
    this.stats = { shortWrites: 0, splitReads: 0, readAgain: 0, readIntr: 0, writeAgain: 0, writeIntr: 0 };
    this.polled = new Promise((resolve) => { this.resolvePolled = resolve; });
    this.transport = Object.fromEntries(['openSelf', 'read', 'write', 'close'].map((name) => [name, (...args) => {
      try {
        assert.ok(++this.calls <= MAX_FIXTURE_CALLS, 'Fixture call bound exceeded');
        return this[name](...args);
      } catch (failure) {
        this.boundaryErrors.push(failure);
        throw failure;
      }
    }]));
  }

  instantiate() {
    const crypto = {
      createRandom: () => ({ generateRandomSync: (length) => {
        assert.ok([4, 16, 24].includes(length), 'Unexpected random request');
        const bytes = Uint8Array.from(randomBytes(length));
        this.randomDraws.push(Buffer.from(bytes));
        return { data: bytes };
      } }),
      createMd: (algorithm) => {
        assert.equal(algorithm, 'SHA1');
        const hash = createHash('sha1');
        return {
          update: async ({ data }) => { hash.update(data); },
          digest: async () => ({ data: Uint8Array.from(hash.digest()) }),
        };
      },
    };
    const util = {
      TextEncoder: class { encodeInto(value) { return encoder.encode(value); } },
      TextDecoder: { create: (encoding, options) => {
        const decoder = new TextDecoder(encoding, options);
        return { decodeWithStream: (bytes) => decoder.decode(bytes) };
      } },
      Base64Helper: class { encodeToStringSync(bytes) { return Buffer.from(bytes).toString('base64'); } },
    };
    const allowed = new Map([
      ['@ohos.security.cryptoFramework', crypto], ['@ohos.util', util],
      ['@ohos.process', { pid: 424242 }], ['libqfli_web_cdp_transport.so', this.transport],
    ]);
    const context = vm.createContext({
      exports: {}, WebResourceResponse: ResourceResponse,
      require: (name) => { assert.ok(allowed.has(name), `Unexpected import ${name}`); return allowed.get(name); },
      setTimeout: (callback, delay) => {
        assert.ok(delay === 10 || delay === 20000, 'Unexpected source timer duration');
        const id = this.nextTimer++;
        this.timerRequests.push(delay);
        this.timers.set(id, setTimeout(() => { this.timers.delete(id); callback(); }, delay));
        if (delay === 10) this.resolvePolled();
        return id;
      },
      clearTimeout: (id) => { clearTimeout(this.timers.get(id)); this.timers.delete(id); },
    });
    moduleScript.runInContext(context, { timeout: 1000 });
    this.proof = new context.exports.SelfCdpProof();
    this.bootstrap = this.proof.bootstrapUrl;
    assert.match(this.bootstrap, /^http:\/\/127\.0\.0\.1:19998\/__qfli_self_cdp\/[0-9a-f]{48}$/);
    assert.equal(this.bootstrap.split('/').at(-1), this.randomDraws[0].toString('hex'));
    return this.proof;
  }

  openSelf(...args) {
    assert.equal(args.length, 0, 'Endpoint must not be supplied to openSelf');
    assert.ok(this.connections.length < 2, 'Only discovery and owned WebSocket handles are expected');
    const handle = (9007199254740993n + BigInt(this.connections.length)).toString();
    const connection = { handle, purpose: this.connections.length === 0 ? 'discovery' : 'websocket',
      phase: 'http', input: Buffer.alloc(0), queue: Buffer.alloc(0), eof: false };
    this.connections.push(connection);
    this.active.set(handle, connection);
    return { status: 0, handle };
  }

  connection(handle) {
    assert.equal(typeof handle, 'string', 'Opaque handles must remain strings');
    assert.ok(this.active.has(handle), 'I/O attempted after native handle closure');
    return this.active.get(handle);
  }

  enqueue(connection, bytes) {
    bytes = Buffer.from(bytes);
    this.queuedBytes += bytes.length;
    assert.ok(this.queuedBytes <= MAX_FIXTURE_BYTES, 'Fixture input byte bound exceeded');
    connection.queue = Buffer.concat([connection.queue, bytes]);
  }

  read(handle, capacity) {
    const connection = this.connection(handle);
    assert.equal(capacity, 4096, 'Expected the bounded native read capacity');
    const pattern = this.options.readPattern || [4096];
    const step = pattern[this.readIndex++ % pattern.length];
    if (step === -11 || step === -4) {
      this.stats[step === -11 ? 'readAgain' : 'readIntr']++;
      return { status: step, bytes: EMPTY };
    }
    if (connection.queue.length === 0) return { status: connection.eof ? 0 : -11, bytes: EMPTY };
    const count = Math.min(capacity, step, connection.queue.length);
    if (count < connection.queue.length) this.stats.splitReads++;
    const bytes = Uint8Array.from(connection.queue.subarray(0, count)).buffer;
    connection.queue = connection.queue.subarray(count);
    return { status: count, bytes };
  }

  write(handle, arrayBuffer) {
    const connection = this.connection(handle);
    assert.equal(Object.prototype.toString.call(arrayBuffer), '[object ArrayBuffer]');
    const bytes = Buffer.from(new Uint8Array(arrayBuffer));
    assert.ok(bytes.length >= 1 && bytes.length <= 65536, 'Native write transfer bound');
    const pattern = this.options.writePattern || [65536];
    const step = pattern[this.writeIndex++ % pattern.length];
    if (step === -11 || step === -4) {
      this.stats[step === -11 ? 'writeAgain' : 'writeIntr']++;
      return step;
    }
    const count = Math.min(step, bytes.length);
    if (count < bytes.length) this.stats.shortWrites++;
    this.writtenBytes += count;
    assert.ok(this.writtenBytes <= MAX_FIXTURE_BYTES, 'Fixture output byte bound exceeded');
    connection.input = Buffer.concat([connection.input, bytes.subarray(0, count)]);
    this.consume(connection);
    return count;
  }

  close(handle) {
    this.connection(handle);
    this.active.delete(handle);
    this.closed.push(handle);
    return this.options.closeFailure && this.closed.length === 2 ? -5 : 0;
  }

  consume(connection) {
    if (connection.phase === 'http') {
      const end = connection.input.indexOf('\r\n\r\n');
      if (end < 0) return;
      const header = connection.input.subarray(0, end).toString('ascii');
      connection.input = connection.input.subarray(end + 4);
      const [requestLine, ...lines] = header.split('\r\n');
      const fields = new Map(lines.map((line) => {
        const colon = line.indexOf(':');
        assert.ok(colon > 0, 'Malformed emitted HTTP header');
        return [line.slice(0, colon).toLowerCase(), line.slice(colon + 1).trim()];
      }));
      assert.equal(fields.size, lines.length, 'Duplicate emitted HTTP header');
      assert.equal(fields.get('host'), 'localhost');
      this.requests.push({ requestLine, fields });
      if (connection.purpose === 'discovery') {
        assert.equal(requestLine, 'GET /json/list HTTP/1.1');
        assert.deepEqual([...fields], [['host', 'localhost'], ['connection', 'close']]);
        assert.equal(connection.input.length, 0, 'Unexpected discovery request body');
        connection.phase = 'done';
        this.discovery(connection);
        return;
      }
      assert.equal(requestLine, 'GET /devtools/page/owned-42 HTTP/1.1');
      assert.equal(fields.get('upgrade'), 'websocket');
      assert.equal(fields.get('connection'), 'Upgrade');
      assert.equal(fields.get('sec-websocket-version'), '13');
      const key = fields.get('sec-websocket-key');
      assert.equal(Buffer.from(key, 'base64').length, 16);
      assert.equal(key, this.randomDraws.find((draw) => draw.length === 16).toString('base64'));
      const accept = this.options.wrongAccept ? 'invalid-accept' : createHash('sha1').update(key + GUID).digest('base64');
      this.enqueue(connection, Buffer.from('HTTP/1.1 101 Switching Protocols\r\nUpgrade: WebSocket\r\n' +
        `Connection: keep-alive, Upgrade\r\nSec-WebSocket-Accept: ${accept}\r\n\r\n`));
      connection.phase = 'ws';
    }
    while (connection.phase === 'ws' && connection.input.length >= 2) {
      const bytes = connection.input;
      assert.equal(bytes[0] & 240, 128, 'Client frame must have FIN and no RSV bits');
      assert.equal(bytes[1] & 128, 128, 'Every client frame must be masked');
      const opcode = bytes[0] & 15;
      assert.ok([1, 8, 10].includes(opcode), 'Unexpected emitted client opcode');
      let length = bytes[1] & 127;
      let prefix = 2;
      if (length === 126) {
        if (bytes.length < 4) return;
        length = bytes.readUInt16BE(2);
        assert.ok(length >= 126, 'Client frame length must be minimal');
        prefix = 4;
      } else assert.ok(length < 126, 'Unexpected 64-bit client frame');
      if (bytes.length < prefix + 4 + length) return;
      assert.ok(opcode === 1 || length <= 125, 'Client control frame exceeds limit');
      const mask = bytes.subarray(prefix, prefix + 4);
      const expectedMask = this.randomDraws.filter((draw) => draw.length === 4)[this.frames.length];
      assert.deepEqual(mask, expectedMask, 'Client frame did not use its fresh random draw');
      const payload = Buffer.from(bytes.subarray(prefix + 4, prefix + 4 + length)
        .map((value, index) => value ^ mask[index % 4]));
      connection.input = bytes.subarray(prefix + 4 + length);
      this.frames.push({ opcode, payload, mask: Buffer.from(mask) });
      if (opcode === 1) {
        const command = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(payload));
        this.commands.push(command);
        this.command(connection, command);
      } else if (opcode === 8) assert.deepEqual(payload, Buffer.from([3, 232]), 'Expected normal client close');
      else assert.deepEqual(payload, Buffer.from('proof-ping'), 'Pong must echo server Ping');
    }
  }

  discovery(connection) {
    if (this.options.stall) return;
    const target = { id: 'owned-42', type: 'page', url: this.bootstrap, webSocketDebuggerUrl: 'ws://localhost/devtools/page/owned-42' };
    let targets = [target];
    if (this.options.mismatchedBootstrap) target.url += '/foreign';
    if (this.options.duplicateBootstrap) targets.push({ ...target, id: 'second', webSocketDebuggerUrl: 'ws://localhost/devtools/page/second' });
    if (this.options.foreignEndpoint) target.webSocketDebuggerUrl = 'ws://127.0.0.1:9222/devtools/page/owned-42';
    const body = Buffer.from(JSON.stringify(targets));
    const padding = this.options.headerPadding ? `X-Padding: ${'x'.repeat(this.options.headerPadding)}\r\n` : '';
    const duplicate = this.options.duplicateLength ? `Content-Length: ${body.length}\r\n` : '';
    this.enqueue(connection, Buffer.concat([Buffer.from('HTTP/1.1 200 OK\r\nContent-Type: application/json; charset=UTF-8\r\n' +
      `${padding}Content-Length: ${body.length}\r\n${duplicate}\r\n`), body]));
  }

  command(connection, command) {
    const methods = ['Page.getFrameTree', 'Runtime.enable', 'Runtime.evaluate'];
    assert.equal(command.id, this.commands.length, 'CDP request IDs must be ordered');
    assert.equal(command.method, methods[command.id - 1], 'Unexpected CDP method/order');
    if (command.id < 3) assert.deepEqual(command, { id: command.id, method: methods[command.id - 1] });
    else assert.deepEqual(command.params, { expression: '(6 * 7)', returnByValue: true, timeout: 1000 });
    if (command.id === 1) {
      if (this.options.wireFailure) {
        this.enqueue(connection, this.options.wireFailure);
        connection.eof = !!this.options.eof;
        return;
      }
      if (this.options.eventFlood) {
        this.enqueue(connection, Buffer.concat(Array.from({ length: 128 }, () => jsonFrame({ method: 'Page.frameStartedLoading' }))));
        return;
      }
      const result = { id: 1, result: { frameTree: { frame: { id: 'main', url: this.options.wrongFrame ? this.bootstrap + '/wrong' : this.bootstrap } }, note: 'UTF-8 ✓😀' } };
      if (this.options.fragmentedSuccess) {
        const encoded = Buffer.from(JSON.stringify(result));
        const split = encoded.indexOf(Buffer.from('😀')) + 1;
        this.enqueue(connection, Buffer.concat([
          jsonFrame({ method: 'Page.frameStartedLoading' }),
          serverFrame(1, encoded.subarray(0, split), { final: false }),
          serverFrame(9, Buffer.from('proof-ping')), serverFrame(10),
          serverFrame(0, encoded.subarray(split)),
        ]));
      } else this.enqueue(connection, jsonFrame(result));
    } else if (command.id === 2) {
      this.enqueue(connection, jsonFrame(this.options.cdpError ? { id: 2, error: { code: -32601, message: 'Fixture rejection' } } : { id: 2, result: {} }));
    } else this.enqueue(connection, jsonFrame({ id: 3, result: { result: { type: 'number', value: this.options.wrongValue ? 41 : 42 } } }));
  }

  verifyCleanup(expectedHandles) {
    assert.equal(this.boundaryErrors.length, 0, this.boundaryErrors.map(String).join('\n'));
    assert.equal(this.active.size, 0, 'A transport handle leaked');
    assert.equal(this.closed.length, expectedHandles, 'Every opened handle must close exactly once');
    assert.equal(new Set(this.closed).size, this.closed.length, 'Duplicate native Close');
    assert.equal(this.timers.size, 0, 'A source timer leaked');
    for (const connection of this.connections) assert.equal(connection.input.length, 0, 'An emitted request/frame was truncated');
    assert.equal(this.randomDraws.filter((draw) => draw.length === 4).length, this.frames.length, 'Every emitted frame needs its own random mask draw');
  }

  dispose() {
    this.proof?.cancel();
    for (const timer of this.timers.values()) clearTimeout(timer);
    this.timers.clear();
  }
}

async function bounded(promise, milliseconds = MAX_CASE_MS) {
  let timer;
  try {
    return await Promise.race([promise, new Promise((resolve, reject) => {
      timer = setTimeout(() => reject(new Error(`Harness deadline exceeded ${milliseconds} ms`)), milliseconds);
    })]);
  } finally { clearTimeout(timer); }
}

const cases = [];
const add = (name, action) => cases.push({ name, action });

add('static bootstrap response allows only exact GET/HEAD', async () => {
  const fixture = new Fixture();
  try {
    const proof = fixture.instantiate();
    const response = proof.response(proof.bootstrapUrl, 'GET');
    assert.equal(response.code, 200);
    assert.equal(response.mime, 'text/html');
    assert.ok(!/<script|\bon\w+\s*=|\b(?:src|href)\s*=/i.test(response.data), 'Bootstrap must be static and contain no resource links');
    assert.deepEqual(response.headers, [
      { headerKey: 'Cache-Control', headerValue: 'no-store' },
      { headerKey: 'Content-Security-Policy', headerValue: "default-src 'none'; base-uri 'none'; form-action 'none'" },
    ]);
    assert.equal(proof.response(proof.bootstrapUrl, 'HEAD').data, '');
    assert.equal(proof.response(proof.bootstrapUrl, 'POST').code, 403);
    assert.equal(proof.response('https://foreign.invalid/', 'GET').code, 403);
    fixture.verifyCleanup(0);
  } finally { fixture.dispose(); }
});

add('success: split UTF-8/frames, short writes, EAGAIN/EINTR, Ping/Pong', async () => {
  const fixture = new Fixture({ fragmentedSuccess: true, readPattern: [1, -11, 2, -4, 7, 4096], writePattern: [1, -11, 5, -4, 65536] });
  const reports = [];
  try {
    const proof = fixture.instantiate();
    await bounded(proof.run((report) => reports.push({ ...report })));
    assert.deepEqual(reports.filter((item) => item.state === 'pass').map((item) => item.stage),
      ['discovery', 'upgrade', 'frame', 'runtime', 'evaluate', 'complete']);
    assert.equal(reports.filter((item) => item.stage === 'complete' && item.state === 'pass').length, 1);
    assert.deepEqual(fixture.commands.map((command) => command.method), ['Page.getFrameTree', 'Runtime.enable', 'Runtime.evaluate']);
    assert.deepEqual(fixture.frames.map((frame) => frame.opcode), [1, 10, 1, 1, 8]);
    for (const [name, count] of Object.entries(fixture.stats)) assert.ok(count > 0, `Success did not exercise ${name}`);
    assert.ok(reports.every((item) => item.detail.length <= 512));
    fixture.verifyCleanup(2);
    await assert.rejects(proof.run(() => {}), /single-use/);
    fixture.verifyCleanup(2);
  } finally { fixture.dispose(); }
});

function rejects(name, options, expected, expectedHandles = 2, expectedMethods = ['Page.getFrameTree']) {
  add(name, async () => {
    const fixture = new Fixture(options);
    const reports = [];
    try {
      const proof = fixture.instantiate();
      await assert.rejects(bounded(proof.run((report) => reports.push({ ...report }))), expected);
      assert.ok(reports.some((report) => report.state === 'fail'), 'Failure must be observable');
      assert.ok(!reports.some((report) => report.stage === 'complete' && report.state === 'pass'), 'Failure emitted a complete pass');
      assert.deepEqual(fixture.commands.map((command) => command.method), expectedMethods);
      fixture.verifyCleanup(expectedHandles);
    } finally { fixture.dispose(); }
  });
}

rejects('discovery rejects a mismatched bootstrap', { mismatchedBootstrap: true }, /exactly one owned bootstrap target, got 0/, 1, []);
rejects('discovery rejects duplicate bootstrap targets', { duplicateBootstrap: true }, /exactly one owned bootstrap target, got 2/, 1, []);
rejects('discovery rejects a foreign returned WebSocket endpoint', { foreignEndpoint: true }, /exact WebSocket host\/path/, 1, []);
rejects('discovery rejects duplicate Content-Length', { duplicateLength: true }, /Duplicate HTTP header: content-length/, 1, []);
rejects('discovery enforces the 16 KiB HTTP header bound', { headerPadding: 17000 }, /HTTP headers exceed 16 KiB/, 1, []);
rejects('work bound stops a stream of tiny synchronous reads', { headerPadding: 5000, readPattern: [1] }, /work bound exceeded/, 1, []);
rejects('upgrade rejects the wrong SHA-1 accept', { wrongAccept: true }, /WebSocket upgrade status\/accept\/headers mismatch/, 2, []);
rejects('frame identity fails before Runtime commands', { wrongFrame: true }, /main-frame URL differs/);
rejects('server frames must not be masked', { wireFailure: serverFrame(1, Buffer.from('{}'), { masked: true }) }, /Unexpected WebSocket RSV\/mask\/opcode/);
rejects('control frames must not be fragmented', { wireFailure: serverFrame(9, Buffer.alloc(0), { final: false }) }, /frame\/control length exceeds bound/);
rejects('control frames cannot exceed 125 bytes', { wireFailure: serverFrame(9, Buffer.alloc(126)) }, /frame\/control length exceeds bound/);
rejects('126-byte encoding must be minimal', { wireFailure: Buffer.from([129, 126, 0, 1, 123]) }, /Nonminimal WebSocket length/);
rejects('64-bit encoding must be minimal', { wireFailure: Buffer.from([129, 127, 0, 0, 0, 0, 0, 0, 0, 1, 123]) }, /Nonminimal WebSocket 64-bit length/);
rejects('continuation requires an open fragmented message', { wireFailure: serverFrame(0) }, /Invalid WebSocket continuation sequence/);
rejects('text messages reject malformed UTF-8', { wireFailure: serverFrame(1, Buffer.from([195, 40])) }, /encoded data was not valid/);
rejects('a frame over 256 KiB is rejected before its payload', { wireFailure: Buffer.from([129, 127, 0, 0, 0, 0, 0, 4, 0, 1]) }, /frame\/control length exceeds bound/);
rejects('EOF inside a payload is an explicit failure', { wireFailure: Buffer.from([129, 10, 123, 125]), eof: true }, /Unexpected self-socket EOF/);
rejects('128 events without the requested reply fail', { eventFlood: true }, /128-event bound/);
rejects('CDP command errors stop before evaluate', { cdpError: true }, /rejected CDP command 2/, 2, ['Page.getFrameTree', 'Runtime.enable']);
rejects('evaluate must return the actual number 42', { wrongValue: true }, /did not return the number 42/, 2, ['Page.getFrameTree', 'Runtime.enable', 'Runtime.evaluate']);
rejects('native close failure cannot produce complete pass', { closeFailure: true }, /Native transport cleanup failed/, 2, ['Page.getFrameTree', 'Runtime.enable', 'Runtime.evaluate']);

add('cancel during polling closes immediately and never reports a late pass', async () => {
  const fixture = new Fixture({ stall: true });
  const reports = [];
  try {
    const proof = fixture.instantiate();
    const outcome = proof.run((report) => reports.push({ ...report })).then(() => null, (error) => error);
    await bounded(fixture.polled);
    proof.cancel();
    assert.equal(fixture.active.size, 0, 'Cancel must synchronously close its handle');
    const failure = await bounded(outcome);
    assert.match(String(failure), /disposed|cancelled/);
    assert.ok(reports.some((report) => report.state === 'cancelled'));
    assert.ok(!reports.some((report) => report.state === 'pass'));
    const count = reports.length;
    fixture.enqueue(fixture.connections[0], Buffer.from('HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n'));
    await new Promise((resolve) => setTimeout(resolve, 30));
    assert.equal(reports.length, count, 'Disposed work emitted a late report');
    fixture.verifyCleanup(1);
  } finally { fixture.dispose(); }
});

const started = performance.now();
const watchdog = setTimeout(() => { throw new Error(`Protocol suite exceeded ${MAX_SUITE_MS} ms`); }, MAX_SUITE_MS);
try {
  console.log(`SOURCE ${sourcePath}\nSHA256 ${sourceHash}\nSDK_TYPESCRIPT ${typescriptPath}\nTYPESCRIPT_VERSION ${ts.version}`);
  for (const test of cases) {
    const before = performance.now();
    await bounded(test.action());
    console.log(`PASS ${test.name} (${(performance.now() - before).toFixed(1)} ms)`);
  }
  assert.equal(sha256(readFileSync(sourcePath, 'utf8')), sourceHash, 'Proof source changed during the run');
  console.log(`PASS ${cases.length} supplementary protocol fixture cases in ${(performance.now() - started).toFixed(1)} ms; no ArkTS/native/ArkWeb acceptance`);
  console.log(`LIMITS per-case=${MAX_CASE_MS}ms suite=${MAX_SUITE_MS}ms calls/case=${MAX_FIXTURE_CALLS} bytes/direction/case=${MAX_FIXTURE_BYTES}`);
} finally { clearTimeout(watchdog); }
