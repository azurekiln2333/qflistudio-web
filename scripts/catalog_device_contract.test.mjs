import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { validateCdpEndpoint, validateDeviceCatalog } from './catalog_device_contract.mjs';

function fixture() {
  const examplesSource = JSON.stringify({ entries: [
    { id: 'js-example-001', code: '<p>中文😀</p>\r\n' },
    { id: 'html-example-001', code: '<p>second</p>' },
  ] }, null, 2) + '\n';
  const tutorialsSource = JSON.stringify({ entries: [{ id: 'lesson', lessons: [
    { id: 'first', code: '<p>中文😀</p>\r\n' }, { id: 'second', code: '<p>second</p>' },
  ] }] });
  const files = {};
  for (const [kind, source] of Object.entries({ examples: examplesSource, tutorials: tutorialsSource })) {
    files[kind] = { path: `ohos_catalog/${kind}.json`, bytes: Buffer.byteLength(source),
      sha256: createHash('sha256').update(source).digest('hex') };
  }
  return { examplesSource, tutorialsSource, bootstrap: {
    schemaVersion: 1, backend: 'arkweb-test', runId: 'native-session',
    environment: { bundleName: 'com.azurekiln.qfli.webforge', moduleName: 'entry_test',
      abilityName: 'TestAbility', osFullName: 'OpenHarmony-test', sdkApiVersion: 20, deviceType: 'phone' },
    manifest: { schemaVersion: 1, kind: 'qfli-ohos-catalog', files,
      counts: { examples: 2, tutorials: 1, lessons: 2 } },
    examples: JSON.parse(examplesSource), tutorials: JSON.parse(tutorialsSource),
    cases: ['js-example-001', 'html-example-001'].map((id, index) => ({
      id, url: `http://127.0.0.1:${20000 + index}/index.html`, origin: `http://127.0.0.1:${20000 + index}`,
    })),
  } };
}

test('accepts exact packaged UTF-8 bytes and isolated cases', () => {
  const f = fixture();
  const result = validateDeviceCatalog(f.bootstrap, f.examplesSource, f.tutorialsSource);
  assert.equal(result.cases.size, 2);
  assert.equal(result.cases.get('js-example-001').origin, 'http://127.0.0.1:20000');
  assert.equal(result.environment.sdkApiVersion, 20);
  assert.ok(f.bootstrap.manifest.files.examples.bytes > f.examplesSource.length);
});

for (const [name, mutate, expected] of [
  ['host bootstrap', (f) => { f.bootstrap.backend = 'host-chromium'; }, /native test ArkWeb/],
  ['production ability', (f) => { f.bootstrap.environment.abilityName = 'EntryAbility'; }, /identity/],
  ['other product', (f) => { f.bootstrap.environment.bundleName = 'com.example.other'; }, /identity/],
  ['missing environment', (f) => { delete f.bootstrap.environment; }, /identity/],
  ['missing native version', (f) => { f.bootstrap.environment.osFullName = ''; }, /OS\/API/],
  ['invalid API', (f) => { f.bootstrap.environment.sdkApiVersion = 20.5; }, /OS\/API/],
  ['stale HAP', (f) => { f.examplesSource += ' '; }, /byte length/],
  ['wrong hash with equal length', (f) => { f.bootstrap.manifest.files.examples.sha256 = '0'.repeat(64); }, /SHA256/],
  ['source substituted after manifest', (f) => { f.bootstrap.examples.entries[0].code = 'fake'; }, /document differs/],
  ['missing tutorial bodies', (f) => { f.bootstrap.tutorials.entries[0].lessons = []; }, /document differs/],
  ['partial case table', (f) => { f.bootstrap.cases.pop(); }, /incomplete/],
  ['reused origin', (f) => { Object.assign(f.bootstrap.cases[1], { url: f.bootstrap.cases[0].url, origin: f.bootstrap.cases[0].origin }); }, /reused/],
  ['duplicate case ID', (f) => { f.bootstrap.cases[1].id = f.bootstrap.cases[0].id; }, /duplicate/],
  ['external origin', (f) => { f.bootstrap.cases[0].url = 'https://example.org/index.html'; }, /loopback/],
  ['loopback hostname impersonation', (f) => { f.bootstrap.cases[0].url = 'http://127.0.0.1.evil:20000/index.html'; }, /loopback/],
  ['wrong origin declaration', (f) => { f.bootstrap.cases[0].origin = 'http://127.0.0.1:20001'; }, /inconsistent/],
  ['changed counts', (f) => { f.bootstrap.manifest.counts.lessons = 1; }, /counts/],
]) {
  test(`rejects ${name}`, () => {
    const f = fixture(); mutate(f);
    assert.throws(() => validateDeviceCatalog(f.bootstrap, f.examplesSource, f.tutorialsSource), expected);
  });
}

test('CDP endpoint requires explicit loopback and no credentials', () => {
  assert.equal(validateCdpEndpoint('http://127.0.0.1:9222'), 'http://127.0.0.1:9222/');
  for (const url of ['https://remote.example:9222', 'http://127.0.0.1.evil:9222', 'file:///catalog', 'http://user@localhost:9222']) {
    assert.throws(() => validateCdpEndpoint(url));
  }
});
