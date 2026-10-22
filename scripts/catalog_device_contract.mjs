import { createHash } from 'node:crypto';

export const OHOS_BOOTSTRAP_URL = 'http://127.0.0.1:19999/__qfli_catalog/bootstrap';

const digest = (text) => createHash('sha256').update(text, 'utf8').digest('hex');
const requireContract = (ok, message) => {
  if (!ok) throw new Error(`OHOS packaged catalog: ${message}`);
};

/** Refuse stale, partial or host-substituted content before target execution. */
export function validateDeviceCatalog(bootstrap, examplesSource, tutorialsSource) {
  requireContract(bootstrap?.schemaVersion === 1 && bootstrap.backend === 'arkweb-test',
    'expected the native test ArkWeb bootstrap (no host fallback)');
  requireContract(typeof bootstrap.runId === 'string' && bootstrap.runId.length > 0,
    'missing native test session identity');
  const identity = bootstrap.environment;
  requireContract(identity?.bundleName === 'com.azurekiln.qfli.webforge' &&
    identity.moduleName === 'entry_test' && identity.abilityName === 'TestAbility',
  'unexpected bundle/module/ability identity');
  requireContract(typeof identity.osFullName === 'string' && identity.osFullName.trim().length > 0 &&
    Number.isSafeInteger(identity.sdkApiVersion) && identity.sdkApiVersion >= 9 &&
    typeof identity.deviceType === 'string' && identity.deviceType.trim().length > 0,
  'missing native OS/API/device-type evidence');
  const environment = Object.freeze({
    bundleName: identity.bundleName, moduleName: identity.moduleName, abilityName: identity.abilityName,
    osFullName: identity.osFullName, sdkApiVersion: identity.sdkApiVersion, deviceType: identity.deviceType,
  });
  const manifest = bootstrap.manifest;
  requireContract(manifest?.schemaVersion === 1 && manifest.kind === 'qfli-ohos-catalog',
    'unsupported manifest');
  const sources = { examples: examplesSource, tutorials: tutorialsSource };
  const catalogs = {};
  for (const [kind, source] of Object.entries(sources)) {
    const file = manifest.files?.[kind];
    requireContract(file?.path === `ohos_catalog/${kind}.json`, `${kind} resource path differs`);
    requireContract(file.bytes === Buffer.byteLength(source, 'utf8'), `${kind} byte length differs`);
    requireContract(file.sha256 === digest(source), `${kind} SHA256 differs; rebuild the test HAP`);
    catalogs[kind] = JSON.parse(source);
    requireContract(Array.isArray(catalogs[kind].entries), `${kind} entries missing`);
    requireContract(JSON.stringify(bootstrap[kind]) === JSON.stringify(catalogs[kind]),
      `${kind} packaged document differs from the verified source`);
  }
  const examples = catalogs.examples.entries;
  const tutorials = catalogs.tutorials.entries;
  const lessons = tutorials.flatMap((tutorial) => tutorial.lessons);
  requireContract(manifest.counts?.examples === examples.length &&
    manifest.counts.tutorials === tutorials.length && manifest.counts.lessons === lessons.length,
  'manifest counts differ');
  requireContract(Array.isArray(bootstrap.cases) && bootstrap.cases.length === examples.length,
    'native case table is incomplete');
  const ids = new Set(examples.map((example) => example.id));
  requireContract(ids.size === examples.length, 'duplicate example IDs');
  const cases = new Map();
  const origins = new Set();
  for (const entry of bootstrap.cases) {
    requireContract(ids.has(entry.id) && !cases.has(entry.id), `unknown/duplicate case ${entry.id}`);
    let url;
    try { url = new URL(entry.url); } catch { throw new Error('OHOS packaged catalog: invalid case URL'); }
    requireContract(url.protocol === 'http:' && url.hostname === '127.0.0.1' &&
      Number(url.port) >= 20000 && Number(url.port) <= 65535 &&
      url.pathname === '/index.html' && !url.search && !url.hash && !url.username && !url.password,
    `invalid isolated loopback URL for ${entry.id}`);
    requireContract(url.origin === entry.origin && !origins.has(url.origin),
      `case origin is inconsistent/reused for ${entry.id}`);
    origins.add(url.origin);
    cases.set(entry.id, Object.freeze({ id: entry.id, url: url.href, origin: url.origin }));
  }
  return { cases, manifest, runId: bootstrap.runId, environment };
}

export function validateCdpEndpoint(endpoint) {
  const url = new URL(endpoint);
  if (!['http:', 'https:', 'ws:', 'wss:'].includes(url.protocol) ||
      !['127.0.0.1', 'localhost', '[::1]'].includes(url.hostname) || url.username || url.password) {
    throw new Error('OHOS CDP must use an explicit local HDC forwarding endpoint');
  }
  return url.href;
}
