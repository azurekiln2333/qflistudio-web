#!/usr/bin/env node
// Executes actual EntryAbility + URL policy with OHOS/Flutter boundary doubles.
// Supplementary channel tests only; no actual OHOS intent or browser is started.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { resolve } from 'node:path';
import { performance } from 'node:perf_hooks';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import vm from 'node:vm';

const { values: options } = parseArgs({ options: {
  entry: { type: 'string' },
  'startup-progress': { type: 'string', default: 'present' },
} });
const startupProgressProfile = options['startup-progress'];
assert.ok(['present', 'absent'].includes(startupProgressProfile), '--startup-progress must be present or absent');
const entryPath = options.entry === undefined
  ? fileURLToPath(new URL('../ohos/entry/src/main/ets/entryability/EntryAbility.ets', import.meta.url))
  : resolve(options.entry);
const typescriptPath = process.env.QFLI_OHOS_TYPESCRIPT || 'D:/ProgramFiles/Huawei/DevEco Studio/sdk/default/openharmony/ets/build-tools/ets-loader/node_modules/typescript/lib/typescript.js';
const ts = createRequire(import.meta.url)(typescriptPath);
const policyPath = fileURLToPath(new URL('../ohos/entry/src/main/ets/entryability/OfflinePreviewPolicy.ets', import.meta.url));
const hashes = new Map();
function compile(path) {
  const source = readFileSync(path, 'utf8');
  hashes.set(path, createHash('sha256').update(source).digest('hex'));
  const output = ts.transpileModule(source, { fileName: path, reportDiagnostics: true,
    compilerOptions: { target: ts.ScriptTarget.ES2020, module: ts.ModuleKind.CommonJS, esModuleInterop: true } });
  const errors = (output.diagnostics || []).filter((item) => item.category === ts.DiagnosticCategory.Error);
  assert.equal(errors.length, 0, errors.map((item) => ts.flattenDiagnosticMessageText(item.messageText, '\n')).join('\n'));
  return new vm.Script(output.outputText, { filename: path });
}
const policyScript = compile(policyPath);
const entryScript = compile(entryPath);
const policyContext = vm.createContext({ exports: {} });
policyScript.runInContext(policyContext, { timeout: 1000 });
const policy = policyContext.exports;
const PICKER_METHODS = ['pickDocument', 'saveDocument', 'pickPhotos', 'readUri', 'writeUri'];
const CALL_TIMEOUT_MS = 500;
const SUITE_TIMEOUT_MS = 5000;
let channelCalls = 0;

const accepted = [
  'http://127.0.0.1:1',
  'http://127.0.0.1:65535/',
  'https://127.0.0.1:443/index.html',
  'http://127.0.0.1:8080/project/main%20page.html?x=1#section',
  'http://[::1]:1/',
  'https://[::1]:65535/path?q=value#part',
  'HTTP://127.0.0.1:80/',
  'HtTpS://[::1]:443/',
  'http://127.0.0.1:3000?name=%E4%B8%AD%20x#fragment',
  'http://[::1]:8080/目录/文件.html',
  'http://127.0.0.1:8080/a%2Fb/%40user?target=https%3A%2F%2Fforeign.invalid%2Fx',
  'http://127.0.0.1:80//foreign.invalid/path#https://foreign.invalid/',
];

const rejected = [
  '', 'http://127.0.0.1', 'https://[::1]/', 'http://127.0.0.1:/',
  'http://127.0.0.1:0/', 'http://127.0.0.1:65536/', 'http://127.0.0.1:99999/',
  'http://127.0.0.1:-1/', 'http://127.0.0.1:+80/', 'http://127.0.0.1:1.5/',
  'http://127.0.0.1:1e3/', 'http://127.0.0.1:080/', 'http://127.0.0.1:00001/',
  'http://127.0.0.1:8080:80/', 'http://127.0.0.1:８０/',
  'http://localhost:8080/', 'http://localhost.:8080/', 'http://example.invalid:8080/',
  'http://127.0.0.1.example.invalid:8080/', 'http://127.0.0.1.:8080/',
  'http://192.168.1.1:8080/', 'https://10.0.0.1:443/', 'http://8.8.8.8:80/',
  'http://0.0.0.0:8080/', 'http://127.0.0.2:8080/', 'http://2130706433:8080/',
  'http://127.1:8080/', 'http://0177.0.0.1:8080/', 'http://0x7f000001:8080/',
  'http://0x7f.0.0.1:8080/', 'http://127.000.000.001:8080/',
  'http://[::ffff:127.0.0.1]:8080/', 'http://[::ffff:7f00:1]:8080/',
  'http://[0:0:0:0:0:0:0:1]:8080/', 'http://[::1%25lo]:8080/',
  'http://[fe80::1]:8080/', 'http://[fd00::1]:8080/', 'http://::1:8080/',
  'http://[[::1]]:8080/', 'http://[::1]:80.example.invalid/',
  'http://user@127.0.0.1:8080/', 'http://user:password@[::1]:8080/',
  'http://127.0.0.1:8080@foreign.invalid/', 'http://foreign.invalid@127.0.0.1:8080/',
  'http://127%2e0%2e0%2e1:8080/', 'http://127.0.0.1%3a8080/',
  '//127.0.0.1:8080/', '127.0.0.1:8080/', 'http:127.0.0.1:8080/',
  'file:///127.0.0.1:8080/index.html', 'data:text/html,local', 'javascript:alert(1)',
  'ftp://127.0.0.1:21/', 'ws://127.0.0.1:8080/', 'wss://[::1]:8080/',
  'intent://127.0.0.1:8080/', 'mailto:127.0.0.1:8080',
  ' http://127.0.0.1:8080/', 'http://127.0.0.1:8080/ ',
  'http://127.0.0.1:8080/\n', 'http://127.0.0.1:8080/\r\nX-Header:value',
  'http://127.0.\t0.1:8080/', 'http://127.0.0.1:8080/\u0000',
  'http://127.0.0.1:8080/\u001f', 'http://127.0.0.1:8080/\u007f',
  'http://127.0.0.1:8080/\u0085', 'http://127.0.0.1:8080/\u009f',
  'http://127.0.0.1:8080/\u00a0', 'http://127.0.0.1:8080/\u2028',
  'http://127.0.0.1:8080/\ufeff', 'http://127.0.0.1:8080/\\foreign.invalid/',
  'http://127.0.0.1:8080\\@foreign.invalid/', 'http:\\127.0.0.1:8080/',
  undefined, null, false, 8080, [], {}, new String('http://127.0.0.1:8080/'),
  { toString() { throw new Error('URL policy must not coerce arbitrary values'); } },
];

function createAbility(options = {}) {
  const state = { order: [], wants: [], events: [], shares: [], pickers: [], channels: [], windowStages: [] };
  const abilityContext = {
    config: { colorMode: options.dark ? 0 : 1 },
    eventHub: { emit: (...args) => state.events.push(args) },
    startAbility: (want) => {
      state.wants.push(Object.fromEntries(Object.entries(want)));
      return options.startFailure ? Promise.reject({ code: 16000001, message: 'Fixture browser unavailable' }) : Promise.resolve();
    },
  };
  const messenger = {};
  const engine = { dartExecutor: { getBinaryMessenger: () => messenger } };
  class FlutterAbility {
    constructor() { this.context = abilityContext; }
    configureFlutterEngine(value) { assert.equal(value, engine); state.order.push('base.configure'); }
    onWindowStageCreate(value) { state.windowStages.push(value); state.order.push('base.window'); }
    onDestroy() { state.order.push('base.destroy'); }
  }
  class MethodChannel {
    constructor(value, name) {
      assert.equal(value, messenger);
      this.name = name;
      state.channels.push(this);
    }
    setMethodCallHandler(handler) { assert.equal(this.handler, undefined); this.handler = handler; }
  }
  class SharedData {
    constructor(record) { this.record = Object.fromEntries(Object.entries(record)); }
  }
  class ShareController {
    constructor(data) { this.data = data; }
    show(context, config) {
      assert.equal(context, abilityContext);
      assert.deepEqual(Object.keys(config), []);
      state.shares.push(this.data.record);
      return options.shareFailure ? Promise.reject({ code: 9001, message: 'Fixture share unavailable' }) : Promise.resolve();
    }
  }
  const modules = new Map([
    ['@ohos/flutter_ohos', { FlutterAbility, MethodChannel }],
    ['@kit.ShareKit', { systemShare: { SharedData, ShareController } }],
    ['@kit.AbilityKit', { ConfigurationConstant: { ColorMode: { COLOR_MODE_DARK: 0 } } }],
    ['../plugins/GeneratedPluginRegistrant', { GeneratedPluginRegistrant: { registerWith: (value) => {
      assert.equal(value, engine); state.order.push('plugins.register');
    } } }],
    ['./NginxBridge', { configureNginxChannel: (value) => {
      assert.equal(value, engine); state.order.push('nginx.configure');
    }, stopActiveNginx: () => state.order.push('nginx.stop') }],
    ['./PickerBridge', { isPickerMethod: (method) => PICKER_METHODS.includes(method), handlePickerCall: (context, call, result) => {
      assert.equal(context, abilityContext);
      state.pickers.push({ call, argument: call.argument('fixture') });
      result.success(`fixture-picker:${call.method}`);
    } }],
    ['./OfflinePreviewPolicy', policy],
  ]);
  const context = vm.createContext({ exports: {}, require: (name) => {
    assert.ok(modules.has(name), `Unexpected runtime import ${name}`);
    return modules.get(name);
  } });
  entryScript.runInContext(context, { timeout: 1000 });
  const ability = new context.exports.default();
  ability.configureFlutterEngine(engine);
  assert.deepEqual(state.order, ['base.configure', 'plugins.register', 'nginx.configure']);
  assert.equal(state.channels.length, 1);
  const channel = state.channels[0];
  assert.equal(channel.name, 'qflistudio/platform');
  assert.equal(typeof channel.handler?.onMethodCall, 'function');
  return {
    state, ability,
    dispatch: async (method, args = {}) => {
      channelCalls++;
      let timer;
      let settlements = 0;
      const call = { method, argument: (name) => args[name] };
      try {
        const outcome = await Promise.race([
          new Promise((resolve) => {
            const settle = (value) => { settlements++; resolve(value); };
            channel.handler.onMethodCall(call, {
              success: (value) => settle({ kind: 'success', value }),
              error: (code, message, details) => settle({ kind: 'error', code, message, details }),
              notImplemented: () => settle({ kind: 'notImplemented' }),
            });
          }),
          new Promise((resolve, reject) => { timer = setTimeout(() => reject(new Error('MethodChannel result timed out')), CALL_TIMEOUT_MS); }),
        ]);
        await Promise.resolve();
        assert.equal(settlements, 1, 'Each channel call must settle once');
        return outcome;
      } finally { clearTimeout(timer); }
    },
  };
}

const cases = [];
const add = (name, action) => cases.push({ name, action });

add(`policy permits ${accepted.length} explicit-port literal-loopback URLs`, async () => {
  for (const value of accepted) assert.equal(policy.isOfflinePreviewUrl(value), true, value);
});

add(`policy rejects ${rejected.length} nonlocal/ambiguous/type-confused values`, async () => {
  for (const value of rejected) assert.equal(policy.isOfflinePreviewUrl(value), false, typeof value === 'string' ? value : typeof value);
});

add(`actual openUrl handler rejects all ${rejected.length} values before startAbility`, async () => {
  const fixture = createAbility();
  for (const url of rejected) {
    const result = await fixture.dispatch('openUrl', { url });
    assert.equal(result.kind, 'error');
    assert.equal(result.code, 'OFFLINE_ONLY');
    assert.equal(typeof result.message, 'string');
    assert.ok(result.message.length > 0);
    assert.equal(result.details, null);
    assert.equal(fixture.state.wants.length, 0, 'Rejected URL reached startAbility');
    assert.equal(fixture.state.shares.length, 0);
    assert.equal(fixture.state.pickers.length, 0);
  }
});

add(`actual openUrl handler preserves all ${accepted.length} original Want URIs`, async () => {
  const fixture = createAbility();
  for (const url of accepted) {
    assert.deepEqual(await fixture.dispatch('openUrl', { url }), { kind: 'success', value: null });
    assert.deepEqual(fixture.state.wants.at(-1), { action: 'ohos.want.action.viewData', uri: url });
  }
  assert.equal(fixture.state.wants.length, accepted.length);
});

add('actual openUrl handler propagates browser-launch failure', async () => {
  const fixture = createAbility({ startFailure: true });
  assert.deepEqual(await fixture.dispatch('openUrl', { url: accepted[0] }),
    { kind: 'error', code: '16000001', message: 'Fixture browser unavailable', details: null });
  assert.deepEqual(fixture.state.wants, [{ action: 'ohos.want.action.viewData', uri: accepted[0] }]);
});

add(startupProgressProfile === 'present'
  ? 'startup progress retains clamping and event identity'
  : 'absent startup progress returns notImplemented for valid values without events', async () => {
  const fixture = createAbility();
  const values = [-2, 0, 0.45, 1, 9];
  for (const progress of values) {
    assert.deepEqual(await fixture.dispatch('startupProgress', { progress }), startupProgressProfile === 'present'
      ? { kind: 'success', value: null }
      : { kind: 'notImplemented' });
  }
  assert.deepEqual(fixture.state.events, startupProgressProfile === 'present'
    ? [0, 0, 0.45, 1, 1].map((value) => ['EVENT_STARTUP_PROGRESS', value])
    : []);
  assert.equal(fixture.state.wants.length, 0);
});

add(startupProgressProfile === 'present'
  ? 'invalid startup progress retains INVALID_PROGRESS without events'
  : 'absent startup progress returns notImplemented for invalid values without events', async () => {
  const fixture = createAbility();
  for (const progress of [NaN, Infinity, -Infinity, '0.2', null, undefined, {}, true]) {
    const result = await fixture.dispatch('startupProgress', { progress });
    if (startupProgressProfile === 'present') {
      assert.equal(result.kind, 'error');
      assert.equal(result.code, 'INVALID_PROGRESS');
    } else {
      assert.deepEqual(result, { kind: 'notImplemented' });
    }
  }
  assert.equal(fixture.state.events.length, 0);
  assert.equal(fixture.state.wants.length, 0);
});

add('share retains exact plain-text record and success', async () => {
  const fixture = createAbility();
  assert.deepEqual(await fixture.dispatch('shareText', { title: '离线笔记', text: 'const answer = 42;' }), { kind: 'success', value: null });
  assert.deepEqual(fixture.state.shares, [{ utd: 'general.plain-text', content: 'const answer = 42;', title: '离线笔记' }]);
  assert.equal(fixture.state.wants.length, 0);
});

add('share failure retains SHARE_FAILED mapping', async () => {
  const fixture = createAbility({ shareFailure: true });
  assert.deepEqual(await fixture.dispatch('shareText', { title: 'Title', text: 'Text' }),
    { kind: 'error', code: 'SHARE_FAILED', message: '9001: Fixture share unavailable', details: null });
});

add('all five picker methods retain delegation and original call arguments', async () => {
  const fixture = createAbility();
  for (const method of PICKER_METHODS) {
    const marker = { method, preserved: true };
    assert.deepEqual(await fixture.dispatch(method, { fixture: marker }), { kind: 'success', value: `fixture-picker:${method}` });
    assert.equal(fixture.state.pickers.at(-1).call.method, method);
    assert.equal(fixture.state.pickers.at(-1).argument, marker);
  }
  assert.equal(fixture.state.pickers.length, 5);
  assert.equal(fixture.state.wants.length, 0);
});

add('unknown methods retain notImplemented', async () => {
  const fixture = createAbility();
  assert.deepEqual(await fixture.dispatch('unrecognizedMethod'), { kind: 'notImplemented' });
  assert.deepEqual(await fixture.dispatch('openURL', { url: accepted[0] }), { kind: 'notImplemented' });
  assert.equal(fixture.state.wants.length, 0);
  assert.equal(fixture.state.pickers.length, 0);
});

add('window background retains dark/light colors and superclass continuation', async () => {
  for (const dark of [false, true]) {
    const fixture = createAbility({ dark });
    const colors = [];
    const stage = { getMainWindowSync: () => ({ setWindowBackgroundColor: (color) => colors.push(color) }) };
    fixture.ability.onWindowStageCreate(stage);
    assert.deepEqual(colors, [dark ? '#FF111418' : '#FFF8F9FF']);
    assert.equal(fixture.state.windowStages[0], stage);
  }
  const fixture = createAbility();
  const stage = { getMainWindowSync() { throw new Error('Fixture window unavailable'); } };
  fixture.ability.onWindowStageCreate(stage);
  assert.equal(fixture.state.windowStages[0], stage);
});

add('destroy retains Nginx stop before base ability teardown', async () => {
  const fixture = createAbility();
  fixture.ability.onDestroy();
  assert.deepEqual(fixture.state.order, ['base.configure', 'plugins.register', 'nginx.configure', 'nginx.stop', 'base.destroy']);
});

const started = performance.now();
const watchdog = setTimeout(() => { throw new Error('Native offline channel fixture suite exceeded 5000 ms'); }, SUITE_TIMEOUT_MS);
try {
  const failures = [];
  console.log(`PROFILE startup-progress=${startupProgressProfile}\nENTRY_SOURCE ${entryPath}`);
  console.log(`SDK_TYPESCRIPT ${typescriptPath}\nTYPESCRIPT_VERSION ${ts.version}`);
  for (const [path, hash] of hashes) console.log(`SOURCE ${path}\nSHA256 ${hash}`);
  for (const test of cases) {
    try {
      await test.action();
      console.log(`PASS ${test.name}`);
    } catch (failure) {
      failures.push({ name: test.name, failure });
      console.error(`FAIL ${test.name}: ${failure.message}`);
    }
  }
  for (const [path, hash] of hashes) assert.equal(createHash('sha256').update(readFileSync(path, 'utf8')).digest('hex'), hash, 'Source changed during test');
  console.log(`RESULT ${cases.length - failures.length}/${cases.length} supplementary channel cases; ${accepted.length} accepted/${rejected.length} rejected URL vectors; ${channelCalls} actual-handler dispatches; ${(performance.now() - started).toFixed(1)} ms; no actual OHOS acceptance`);
  console.log(`LIMITS channel-result=${CALL_TIMEOUT_MS}ms suite-loop=${SUITE_TIMEOUT_MS}ms VM-module-evaluation=1000ms`);
  assert.equal(failures.length, 0, failures.map(({ name }) => name).join('\n'));
} finally { clearTimeout(watchdog); }
