import cryptoFramework from '@ohos.security.cryptoFramework';
import util from '@ohos.util';
import process from '@ohos.process';
import * as selfCdp from 'libqfli_web_cdp_transport.so';

// Test-only protocol client. Its only native endpoint is openSelf(): neither
// discovery nor the returned WebSocket URL can supply a socket host/path/PID.
const HTTP_HOST = 'localhost';
const MAX_HEADER = 16384;
const MAX_DISCOVERY = 65536;
const MAX_MESSAGE = 262144;
const MAX_BUFFER = MAX_MESSAGE + MAX_HEADER;
const MAX_POLL_TURNS = 3000;
const DEADLINE_MS = 20000;
const EAGAIN = -11;
const EINTR = -4;

interface HttpHead {
  status: number;
  fields: Map<string, string>;
}

interface DevtoolsTarget {
  id: string;
  type: string;
  url: string;
  webSocketDebuggerUrl: string;
}

interface CdpError {
  code?: number;
  message?: string;
}

interface CdpRemoteObject {
  type?: string;
  value?: number;
}

interface CdpException {
  text?: string;
}

interface CdpFrame {
  id?: string;
  url?: string;
}

interface CdpFrameTree {
  frame?: CdpFrame;
}

interface CdpResult {
  frameTree?: CdpFrameTree;
  result?: CdpRemoteObject;
  exceptionDetails?: CdpException;
}

interface CdpEnvelope {
  id?: number;
  method?: string;
  result?: CdpResult;
  error?: CdpError;
}

export interface SelfCdpReport {
  stage: string;
  state: string;
  detail: string;
}

type ReportCallback = (report: SelfCdpReport) => void;

function utf8(text: string): Uint8Array {
  return new util.TextEncoder().encodeInto(text);
}

function text(bytes: Uint8Array): string {
  return util.TextDecoder.create('utf-8', { fatal: true }).decodeWithStream(bytes);
}

function join(first: Uint8Array, second: Uint8Array, limit: number): Uint8Array {
  if (first.byteLength + second.byteLength > limit) {
    throw new Error('Protocol byte bound exceeded');
  }
  const merged = new Uint8Array(first.byteLength + second.byteLength);
  merged.set(first, 0);
  merged.set(second, first.byteLength);
  return merged;
}

function randomBytes(length: number): Uint8Array {
  const bytes = cryptoFramework.createRandom().generateRandomSync(length).data;
  if (bytes.byteLength !== length) throw new Error('Random source returned an invalid length');
  return bytes;
}

function randomHex(): string {
  const bytes = randomBytes(24);
  let token = '';
  for (let index = 0; index < bytes.length; index++) {
    token += bytes[index].toString(16).padStart(2, '0');
  }
  return token;
}

function headerEnd(bytes: Uint8Array): number {
  for (let index = 0; index + 3 < bytes.length; index++) {
    if (bytes[index] === 13 && bytes[index + 1] === 10 &&
      bytes[index + 2] === 13 && bytes[index + 3] === 10) return index + 4;
  }
  return -1;
}

function parseHead(bytes: Uint8Array): HttpHead {
  for (let index = 0; index < bytes.length; index++) {
    const value = bytes[index];
    if (value !== 9 && value !== 10 && value !== 13 && (value < 32 || value > 126)) {
      throw new Error('HTTP headers are not ASCII');
    }
  }
  const lines = text(bytes).split('\r\n');
  const statusMatch = /^HTTP\/1\.[01] ([0-9]{3})(?: [\x20-\x7e]*)?$/.exec(lines[0]);
  if (statusMatch === null || lines.length > 130) throw new Error('Invalid HTTP status/header count');
  const fields = new Map<string, string>();
  for (let index = 1; index < lines.length - 2; index++) {
    const match = /^([!#$%&'*+.^_`|~0-9A-Za-z-]+):[\t ]*([^\r\n]*)$/.exec(lines[index]);
    if (match === null) throw new Error('Malformed or folded HTTP header');
    const key = match[1].toLowerCase();
    if (fields.has(key)) throw new Error(`Duplicate HTTP header: ${key}`);
    fields.set(key, match[2].trim());
  }
  return { status: Number(statusMatch[1]), fields: fields };
}

class SelfReader {
  private pending: Uint8Array = new Uint8Array(0);
  private owner: SelfCdpProof;
  private handle: string;

  constructor(owner: SelfCdpProof, handle: string) {
    this.owner = owner;
    this.handle = handle;
  }

  async head(): Promise<HttpHead> {
    while (true) {
      const end = headerEnd(this.pending);
      if (end >= 0) {
        if (end > MAX_HEADER) throw new Error('HTTP headers exceed 16 KiB');
        const header = this.pending.slice(0, end);
        this.pending = this.pending.slice(end);
        return parseHead(header);
      }
      if (this.pending.length >= MAX_HEADER) throw new Error('HTTP headers exceed 16 KiB');
      await this.more();
    }
  }

  async exact(length: number): Promise<Uint8Array> {
    if (!Number.isInteger(length) || length < 0 || length > MAX_MESSAGE) {
      throw new Error('Invalid bounded protocol read');
    }
    while (this.pending.length < length) await this.more();
    const result = this.pending.slice(0, length);
    this.pending = this.pending.slice(length);
    return result;
  }

  hasPending(): boolean {
    return this.pending.length > 0;
  }

  private async more(): Promise<void> {
    while (true) {
      this.owner.checkActive();
      const result = selfCdp.read(this.handle, 4096);
      if (result.status > 0) {
        if (!Number.isInteger(result.status) || result.status > 4096 ||
          result.bytes.byteLength !== result.status) throw new Error('Invalid native read result');
        this.pending = join(this.pending, new Uint8Array(result.bytes), MAX_BUFFER);
        return;
      }
      if (result.bytes.byteLength !== 0) throw new Error('Native read returned bytes without a count');
      if (result.status === 0) throw new Error('Unexpected self-socket EOF');
      if (result.status !== EAGAIN && result.status !== EINTR) {
        throw new Error(`Self-socket read failed: errno ${-result.status}`);
      }
      await this.owner.poll();
    }
  }
}

export class SelfCdpProof {
  readonly bootstrapUrl: string = `http://127.0.0.1:19998/__qfli_self_cdp/${randomHex()}`;
  private readonly handles: Set<string> = new Set<string>();
  private cancelled: boolean = false;
  private disposed: boolean = false;
  private started: boolean = false;
  private turns: number = 0;
  private timer: number = -1;
  private pollTimer: number = -1;
  private wake: (() => void) | undefined = undefined;
  private abort: ((error: Error) => void) | undefined = undefined;
  private callback: ReportCallback | undefined = undefined;
  private stage: string = 'created';
  private cleanupErrors: number = 0;

  // This source has no script, event handlers, subresources or authored project
  // content. Only the fixed CDP evaluate below executes JS, after target proof.
  response(address: string, method: string): WebResourceResponse {
    const permitted = address === this.bootstrapUrl && (method === 'GET' || method === 'HEAD');
    const source = permitted ? '<!doctype html><html><head><meta charset="utf-8">' +
      '<title>QFLI same-app CDP proof</title></head><body><p>Static bootstrap ready.</p></body></html>' :
      'Only the test-owned bootstrap is available';
    const response = new WebResourceResponse();
    response.setResponseData(method === 'HEAD' ? '' : source);
    response.setResponseCode(permitted ? 200 : 403);
    response.setReasonMessage(permitted ? 'OK' : 'Forbidden');
    response.setResponseMimeType(permitted ? 'text/html' : 'text/plain');
    response.setResponseEncoding('utf-8');
    response.setResponseHeader([
      { headerKey: 'Cache-Control', headerValue: 'no-store' },
      { headerKey: 'Content-Security-Policy', headerValue: "default-src 'none'; base-uri 'none'; form-action 'none'" }
    ]);
    return response;
  }

  async run(callback: ReportCallback): Promise<void> {
    if (this.started || this.cancelled) throw new Error('Self CDP proof is single-use');
    this.started = true;
    this.callback = callback;
    const interrupted = new Promise<void>((resolve, reject) => {
      this.abort = reject;
      this.timer = setTimeout(() => this.interrupt(new Error('20-second self CDP proof timeout')), DEADLINE_MS);
    });
    try {
      await Promise.race([this.perform(), interrupted]);
      this.checkActive();
      this.report('complete', 'pass', 'Unique owned target; frame URL; Runtime.enable; actual evaluate number 42');
    } catch (failure) {
      this.report(this.stage, this.disposed ? 'cancelled' : 'fail', `${failure}`);
      throw new Error(`Self CDP proof failed at ${this.stage}: ${failure}`);
    } finally {
      if (this.timer >= 0) clearTimeout(this.timer);
      this.timer = -1;
      this.abort = undefined;
      this.closeAll();
      if (this.cleanupErrors > 0) this.report('cleanup', 'fail', `Native close failures: ${this.cleanupErrors}`);
      this.callback = undefined;
    }
  }

  cancel(): void {
    this.disposed = true;
    this.interrupt(new Error('Owned Web page disposed'));
  }

  checkActive(): void {
    if (this.cancelled) throw new Error('Self CDP proof cancelled');
    this.turns++;
    if (this.turns > MAX_POLL_TURNS) throw new Error('Self CDP proof work bound exceeded');
  }

  async poll(): Promise<void> {
    this.checkActive();
    await new Promise<void>((resolve) => {
      this.wake = resolve;
      this.pollTimer = setTimeout(() => {
        this.pollTimer = -1;
        this.wake = undefined;
        resolve();
      }, 10);
    });
    this.checkActive();
  }

  private interrupt(error: Error): void {
    this.cancelled = true;
    this.closeAll();
    if (this.pollTimer >= 0) clearTimeout(this.pollTimer);
    this.pollTimer = -1;
    const wake = this.wake;
    this.wake = undefined;
    if (wake !== undefined) wake();
    const abort = this.abort;
    if (abort !== undefined) abort(error);
  }

  private report(stage: string, state: string, detail: string): void {
    if (this.cancelled && state !== 'cancelled' && state !== 'fail') return;
    this.stage = stage;
    const callback = this.callback;
    if (callback !== undefined) callback({ stage: stage, state: state, detail: detail.slice(0, 512) });
  }

  private open(): string {
    this.checkActive();
    const opened = selfCdp.openSelf();
    if (opened.status !== 0 || !/^[1-9][0-9]{0,18}$/.test(opened.handle)) {
      throw new Error(`openSelf failed: status ${opened.status}`);
    }
    if (this.handles.has(opened.handle)) throw new Error('Native transport reused a live handle');
    this.handles.add(opened.handle);
    return opened.handle;
  }

  private close(handle: string): void {
    if (!this.handles.has(handle)) return;
    this.handles.delete(handle);
    try {
      if (selfCdp.close(handle) < 0) this.cleanupErrors++;
    } catch (failure) {
      // One close failure must not prevent the remaining owned handles closing.
      this.cleanupErrors++;
    }
  }

  private closeAll(): void {
    this.handles.forEach((handle: string) => this.close(handle));
  }

  private async writeAll(handle: string, bytes: Uint8Array): Promise<void> {
    let offset = 0;
    while (offset < bytes.byteLength) {
      this.checkActive();
      const part = bytes.slice(offset, Math.min(offset + 65536, bytes.byteLength));
      const count = selfCdp.write(handle, part.buffer as ArrayBuffer);
      if (Number.isInteger(count) && count > 0 && count <= part.byteLength) {
        offset += count;
      } else if (count === EAGAIN || count === EINTR) {
        await this.poll();
      } else {
        throw new Error(`Self-socket write failed or invalid count: ${count}`);
      }
    }
  }

  private async discover(): Promise<DevtoolsTarget> {
    const handle = this.open();
    try {
      await this.writeAll(handle, utf8(`GET /json/list HTTP/1.1\r\nHost: ${HTTP_HOST}\r\nConnection: close\r\n\r\n`));
      const reader = new SelfReader(this, handle);
      const head = await reader.head();
      const lengthText = head.fields.get('content-length');
      const mime = head.fields.get('content-type');
      if (head.status !== 200 || head.fields.has('transfer-encoding') || lengthText === undefined ||
        !/^(0|[1-9][0-9]{0,5})$/.test(lengthText) || Number(lengthText) > MAX_DISCOVERY ||
        mime === undefined || !/^application\/json(?:\s*;|$)/i.test(mime)) {
        throw new Error('Discovery requires HTTP200 bounded Content-Length JSON without transfer encoding');
      }
      const body = await reader.exact(Number(lengthText));
      if (reader.hasPending()) throw new Error('Unexpected bytes after discovery body');
      const targets = JSON.parse(text(body)) as DevtoolsTarget[];
      if (!Array.isArray(targets) || targets.length > 128) throw new Error('Invalid bounded target inventory');
      const matches: DevtoolsTarget[] = [];
      for (let index = 0; index < targets.length; index++) {
        const target = targets[index];
        if (target !== null && typeof target === 'object' && target.url === this.bootstrapUrl) matches.push(target);
      }
      if (matches.length !== 1) throw new Error(`Expected exactly one owned bootstrap target, got ${matches.length}`);
      const owned = matches[0];
      if (owned.type !== 'page' || typeof owned.id !== 'string' || !/^[0-9A-Za-z._-]{1,160}$/.test(owned.id) ||
        typeof owned.webSocketDebuggerUrl !== 'string' ||
        owned.webSocketDebuggerUrl !== `ws://${HTTP_HOST}/devtools/page/${owned.id}`) {
        throw new Error('Owned target has an unexpected type/id/exact WebSocket host/path');
      }
      return owned;
    } finally {
      this.close(handle);
    }
  }

  private async upgrade(handle: string, path: string): Promise<SelfReader> {
    const base64 = new util.Base64Helper();
    const key = base64.encodeToStringSync(randomBytes(16));
    const digest = cryptoFramework.createMd('SHA1');
    await digest.update({ data: utf8(`${key}258EAFA5-E914-47DA-95CA-C5AB0DC85B11`) });
    const sum = await digest.digest();
    this.checkActive();
    const accept = base64.encodeToStringSync(sum.data);
    await this.writeAll(handle, utf8(`GET ${path} HTTP/1.1\r\nHost: ${HTTP_HOST}\r\n` +
      `Upgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: ${key}\r\nSec-WebSocket-Version: 13\r\n\r\n`));
    const reader = new SelfReader(this, handle);
    const head = await reader.head();
    const upgrade = head.fields.get('upgrade');
    const connection = head.fields.get('connection');
    if (head.status !== 101 || upgrade === undefined || upgrade.toLowerCase() !== 'websocket' ||
      connection === undefined || connection.toLowerCase().split(',').map((part: string) => part.trim()).indexOf('upgrade') < 0 ||
      head.fields.get('sec-websocket-accept') !== accept || head.fields.has('sec-websocket-extensions') ||
      head.fields.has('sec-websocket-protocol') || head.fields.has('content-length') || head.fields.has('transfer-encoding')) {
      throw new Error('WebSocket upgrade status/accept/headers mismatch');
    }
    return reader;
  }

  private async frame(handle: string, opcode: number, payload: Uint8Array): Promise<void> {
    if (payload.length > 65535 || (opcode >= 8 && payload.length > 125)) throw new Error('Client frame exceeds bound');
    const prefix = payload.length < 126 ? 2 : 4;
    const bytes = new Uint8Array(prefix + 4 + payload.length);
    bytes[0] = 128 | opcode;
    if (prefix === 2) bytes[1] = 128 | payload.length;
    else {
      bytes[1] = 128 | 126;
      bytes[2] = Math.floor(payload.length / 256);
      bytes[3] = payload.length % 256;
    }
    const mask = randomBytes(4);
    bytes.set(mask, prefix);
    for (let index = 0; index < payload.length; index++) bytes[prefix + 4 + index] = payload[index] ^ mask[index % 4];
    await this.writeAll(handle, bytes);
  }

  private async message(handle: string, reader: SelfReader): Promise<string> {
    let message = new Uint8Array(0);
    let fragmented = false;
    for (let frames = 0; frames < 256; frames++) {
      this.checkActive();
      const header = await reader.exact(2);
      const final = (header[0] & 128) !== 0;
      const opcode = header[0] & 15;
      if ((header[0] & 112) !== 0 || (header[1] & 128) !== 0 ||
        (opcode !== 0 && opcode !== 1 && opcode !== 8 && opcode !== 9 && opcode !== 10)) {
        throw new Error('Unexpected WebSocket RSV/mask/opcode');
      }
      let length = header[1] & 127;
      if (length === 126) {
        const extended = await reader.exact(2);
        length = extended[0] * 256 + extended[1];
        if (length < 126) throw new Error('Nonminimal WebSocket length');
      } else if (length === 127) {
        const extended = await reader.exact(8);
        if (extended[0] !== 0 || extended[1] !== 0 || extended[2] !== 0 || extended[3] !== 0) {
          throw new Error('WebSocket 64-bit length exceeds bound');
        }
        length = extended[4] * 16777216 + extended[5] * 65536 + extended[6] * 256 + extended[7];
        if (length < 65536) throw new Error('Nonminimal WebSocket 64-bit length');
      }
      if (length > MAX_MESSAGE || (opcode >= 8 && (!final || length > 125))) {
        throw new Error('WebSocket frame/control length exceeds bound');
      }
      const payload = await reader.exact(length);
      if (opcode === 8) {
        if (length === 1) throw new Error('Invalid close frame length');
        if (length >= 2) {
          const code = payload[0] * 256 + payload[1];
          const standard = code >= 1000 && code <= 1014 && code !== 1004 && code !== 1005 && code !== 1006;
          if (!standard && (code < 3000 || code > 4999)) throw new Error('Invalid WebSocket close status');
          text(payload.slice(2)); // Fatal UTF-8 validation of the optional reason.
        }
        await this.frame(handle, 8, payload);
        throw new Error('ArkWeb closed the WebSocket before proof completion');
      }
      if (opcode === 9) {
        await this.frame(handle, 10, payload);
        continue;
      }
      if (opcode === 10) continue;
      if ((opcode === 0 && !fragmented) || (opcode === 1 && fragmented)) {
        throw new Error('Invalid WebSocket continuation sequence');
      }
      message = join(message, payload, MAX_MESSAGE);
      if (final) return text(message);
      fragmented = true;
    }
    throw new Error('WebSocket message exceeds 256-frame bound');
  }

  private async reply(handle: string, reader: SelfReader, id: number, request: string): Promise<CdpResult> {
    await this.frame(handle, 1, utf8(request));
    for (let events = 0; events < 128; events++) {
      const envelope = JSON.parse(await this.message(handle, reader)) as CdpEnvelope;
      if (envelope === null || typeof envelope !== 'object' || Array.isArray(envelope)) {
        throw new Error('CDP response must be an object');
      }
      if (envelope.id === undefined && typeof envelope.method === 'string') continue;
      if (envelope.id !== id) throw new Error(`Unexpected CDP reply ID (wanted ${id})`);
      if (envelope.error !== undefined) throw new Error(`ArkWeb rejected CDP command ${id}`);
      if (envelope.result === undefined || envelope.result === null || typeof envelope.result !== 'object' ||
        Array.isArray(envelope.result)) throw new Error('CDP reply has no result object');
      return envelope.result;
    }
    throw new Error('CDP reply exceeded 128-event bound');
  }

  private async perform(): Promise<void> {
    this.report('discovery', 'running', `Own PID ${process.pid}; webview_devtools_remote_${process.pid}; self Unix only`);
    const target = await this.discover();
    this.checkActive();
    this.report('discovery', 'pass', 'Exactly one page matches this launch\'s random bootstrap URL');
    const handle = this.open();
    try {
      this.report('upgrade', 'running', 'Exact discovery host/path; fresh key; SHA-1 accept verification');
      const reader = await this.upgrade(handle, `/devtools/page/${target.id}`);
      this.report('upgrade', 'pass', 'HTTP101 and exact Sec-WebSocket-Accept verified; no extensions');
      this.report('frame', 'running', 'Page.getFrameTree main URL identity check');
      const frame = await this.reply(handle, reader, 1, '{"id":1,"method":"Page.getFrameTree"}');
      if (frame.frameTree?.frame?.url !== this.bootstrapUrl) throw new Error('Attached main-frame URL differs from owned bootstrap');
      this.report('frame', 'pass', 'Actual main-frame URL equals the unique owned bootstrap');
      this.report('runtime', 'running', 'Runtime.enable over masked WebSocket client frames');
      await this.reply(handle, reader, 2, '{"id":2,"method":"Runtime.enable"}');
      this.report('runtime', 'pass', 'Actual Runtime.enable reply received');
      this.report('evaluate', 'running', 'Evaluate fixed expression after target and frame identity proof');
      const evaluated = await this.reply(handle, reader, 3,
        '{"id":3,"method":"Runtime.evaluate","params":{"expression":"(6 * 7)","returnByValue":true,"timeout":1000}}');
      if (evaluated.exceptionDetails !== undefined || evaluated.result?.type !== 'number' || evaluated.result?.value !== 42) {
        throw new Error('Actual Runtime.evaluate did not return the number 42');
      }
      this.report('evaluate', 'pass', 'Actual ArkWeb Runtime.evaluate returned type=number, value=42');
      await this.frame(handle, 8, new Uint8Array([3, 232]));
    } finally {
      this.close(handle);
    }
    if (this.cleanupErrors > 0) throw new Error('Native transport cleanup failed');
  }
}
