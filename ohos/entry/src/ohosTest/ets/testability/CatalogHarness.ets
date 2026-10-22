import common from '@ohos.app.ability.common';
import cryptoFramework from '@ohos.security.cryptoFramework';
import util from '@ohos.util';
import deviceInfo from '@ohos.deviceInfo';

export const BOOTSTRAP_URL = 'http://127.0.0.1:19999/__qfli_catalog/bootstrap';

interface CatalogFile {
  path: string;
  bytes: number;
  sha256: string;
}
interface CatalogFiles {
  examples: CatalogFile;
  tutorials: CatalogFile;
}
interface CatalogCounts {
  examples: number;
  tutorials: number;
  lessons: number;
}
interface CatalogManifest {
  schemaVersion: number;
  kind: string;
  files: CatalogFiles;
  counts: CatalogCounts;
}
interface CatalogExample {
  id: string;
  code: string;
}
interface ExampleDocument {
  schemaVersion: number;
  entries: CatalogExample[];
}
interface CatalogCase {
  id: string;
  url: string;
  origin: string;
}
interface CatalogEnvironment {
  bundleName: string;
  moduleName: string;
  abilityName: string;
  osFullName: string;
  sdkApiVersion: number;
  deviceType: string;
}

export class CatalogHarness {
  private readonly sources: Map<string, string> = new Map<string, string>();
  private bootstrap: string = '';

  async prepare(context: common.UIAbilityContext): Promise<void> {
    try {
      const resourceManager = context.resourceManager;
      const manifestBytes = await resourceManager.getRawFileContent('ohos_catalog/manifest.json');
      const manifestText = new util.TextDecoder('utf-8', { fatal: true }).decodeWithStream(manifestBytes);
      const manifest = JSON.parse(manifestText) as CatalogManifest;
      if (manifest.schemaVersion !== 1 || manifest.kind !== 'qfli-ohos-catalog' ||
        manifest.files.examples.path !== 'ohos_catalog/examples.json' ||
        manifest.files.tutorials.path !== 'ohos_catalog/tutorials.json') {
        throw new Error('Invalid test catalog manifest');
      }
      const exampleBytes = await resourceManager.getRawFileContent(manifest.files.examples.path);
      const tutorialBytes = await resourceManager.getRawFileContent(manifest.files.tutorials.path);
      await this.verify(exampleBytes, manifest.files.examples);
      await this.verify(tutorialBytes, manifest.files.tutorials);
      const examplesText = new util.TextDecoder('utf-8', { fatal: true }).decodeWithStream(exampleBytes);
      const tutorialsText = new util.TextDecoder('utf-8', { fatal: true }).decodeWithStream(tutorialBytes);
      const examples = JSON.parse(examplesText) as ExampleDocument;
      if (examples.schemaVersion !== 1 || examples.entries.length !== manifest.counts.examples ||
        examples.entries.length > 45536) {
        throw new Error('Invalid test example inventory');
      }
      const cases: CatalogCase[] = [];
      const ids: Set<string> = new Set<string>();
      this.sources.clear();
      for (let index = 0; index < examples.entries.length; index++) {
        const example = examples.entries[index];
        if (!example.id || !example.code || ids.has(example.id)) {
          throw new Error('Missing or duplicate test example');
        }
        ids.add(example.id);
        const origin = `http://127.0.0.1:${20000 + index}`;
        const address = `${origin}/index.html`;
        cases.push({ id: example.id, url: address, origin: origin });
        this.sources.set(address, example.code);
      }
      // Only the bootstrap announces metadata. Case responses contain the exact
      // authored source, without helper scripts, assertions or companion assets.
      // Public platform and ability metadata deliberately exclude device IDs,
      // serial numbers, signing material and other private identifiers.
      const environment: CatalogEnvironment = {
        bundleName: context.abilityInfo.bundleName,
        moduleName: context.abilityInfo.moduleName,
        abilityName: context.abilityInfo.name,
        osFullName: deviceInfo.osFullName,
        sdkApiVersion: deviceInfo.sdkApiVersion,
        deviceType: deviceInfo.deviceType
      };
      const payload = `{"schemaVersion":1,"backend":"arkweb-test",` +
        `"runId":${JSON.stringify(`${Date.now()}`)},"manifest":${manifestText},` +
        `"environment":${JSON.stringify(environment)},` +
        `"tutorials":${tutorialsText},"examples":${examplesText},"cases":${JSON.stringify(cases)}}`;
      const safePayload = payload.replace(/</g, '\\u003c');
      this.bootstrap = '<!doctype html><html><head><meta charset="utf-8">' +
        '<title>QFLI OHOS catalog verification</title></head><body>' +
        '<p>Test-only packaged catalog ready. Attach the host semantic runner.</p>' +
        `<script>window.__QFLI_OHOS_CATALOG__=${safePayload};</script></body></html>`;
    } catch (failure) {
      throw new Error(`Packaged catalog preparation failed: ${failure}`);
    }
  }

  private async verify(bytes: Uint8Array, expected: CatalogFile): Promise<void> {
    try {
      if (bytes.byteLength !== expected.bytes) {
        throw new Error(`Catalog byte length mismatch: ${expected.path}`);
      }
      const digest = cryptoFramework.createMd('SHA256');
      await digest.update({ data: bytes });
      const result = await digest.digest();
      let actual = '';
      for (let index = 0; index < result.data.length; index++) {
        actual += result.data[index].toString(16).padStart(2, '0');
      }
      if (actual !== expected.sha256) {
        throw new Error(`Catalog SHA256 mismatch: ${expected.path}`);
      }
    } catch (failure) {
      throw new Error(`Packaged catalog verification failed: ${failure}`);
    }
  }

  response(address: string, method: string): WebResourceResponse | null {
    if (address.startsWith('data:') || address.startsWith('blob:') || address === 'about:blank') {
      return null;
    }
    if (method !== 'GET' && method !== 'HEAD') {
      return this.document('Method not allowed', 405, 'text/plain');
    }
    if (address === BOOTSTRAP_URL) {
      return this.document(method === 'HEAD' ? '' : this.bootstrap, 200, 'text/html');
    }
    // Query/fragment variants identify the same HTTP document. No companion
    // resources are synthesized: absent image/script/style paths stay absent.
    const source = this.sources.get(address.split('#')[0].split('?')[0]);
    if (source !== undefined) {
      return this.document(method === 'HEAD' ? '' : source, 200, 'text/html');
    }
    if (/^http:\/\/127\.0\.0\.1:(19999|[2-6][0-9]{4})(\/|$)/.test(address)) {
      return this.document('Not found', 404, 'text/plain');
    }
    return this.document('External requests are blocked by the offline catalog harness', 403, 'text/plain');
  }

  private document(source: string, code: number, mime: string): WebResourceResponse {
    const response = new WebResourceResponse();
    response.setResponseData(source);
    response.setResponseCode(code);
    response.setReasonMessage(code === 200 ? 'OK' : (code === 404 ? 'Not Found' : 'Blocked'));
    response.setResponseMimeType(mime);
    response.setResponseEncoding('utf-8');
    response.setResponseHeader([{ headerKey: 'Cache-Control', headerValue: 'no-store' }]);
    return response;
  }
}
