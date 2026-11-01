import { resolve, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../../../../');
const { chromium } = await import(pathToFileURL(resolve(repo, 'node_modules/playwright/index.mjs')).href);
const { OHOS_BOOTSTRAP_URL } = await import(pathToFileURL(resolve(repo, 'scripts/catalog_device_contract.mjs')).href);
const b = await chromium.connectOverCDP('http://127.0.0.1:9222');
const pages = b.contexts().flatMap(c=>c.pages());
const page = pages.find(p=>{try{const u=new URL(p.url());return u.hostname==='127.0.0.1'&&+u.port>=19999&&+u.port<=65535;}catch{return false;}});
await page.goto(OHOS_BOOTSTRAP_URL,{waitUntil:'domcontentloaded'});
const cat = await page.evaluate(()=>window.__QFLI_OHOS_CATALOG__);
const url = cat.cases.find(c=>c.id==='css-example-035').url;
await page.goto(url,{waitUntil:'domcontentloaded'}); await page.waitForTimeout(200);

const hovered = () => page.evaluate(()=>[...document.querySelectorAll(':hover')].map(e=>e.tagName+(e.className?'.'+e.className:'')).join(','));
const bg = () => page.evaluate(()=>getComputedStyle(document.querySelector('.btn')).backgroundColor);

// put pointer on the button first
const bb = await page.locator('.btn').first().boundingBox();
await page.mouse.move(bb.x+bb.width/2, bb.y+bb.height/2); await page.waitForTimeout(120);
console.log('hovered on btn :', await hovered(), await bg());

for (const [label, fn] of [
  ['move(0,0)', () => page.mouse.move(0,0)],
  ['move(-1,-1)', () => page.mouse.move(-1,-1)],
  ['move(W+50,H+50)', async () => page.mouse.move(980+50, 1990+50)],
  ['cdp mouseMoved -1', async () => { const s = await page.context().newCDPSession(page); await s.send('Input.dispatchMouseEvent',{type:'mouseMoved',x:-1,y:-1,button:'none',buttons:0}); await s.detach(); }],
]) {
  try { await fn(); await page.waitForTimeout(150);
    console.log(label.padEnd(20), '-> hover:', (await hovered())||'(none)', '| bg:', await bg());
  } catch (e) { console.log(label.padEnd(20), '-> ERR', String(e).split('\n')[0].slice(0,90)); }
}
await page.goto(OHOS_BOOTSTRAP_URL,{waitUntil:'domcontentloaded'}).catch(()=>{});
await b.close();
