import { resolve, dirname } from 'node:path';
import { writeFileSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../../../..');
const { chromium } = await import(pathToFileURL(resolve(repo, 'node_modules/playwright/index.mjs')).href);
const { OHOS_BOOTSTRAP_URL } = await import(pathToFileURL(resolve(repo, 'scripts/catalog_device_contract.mjs')).href);
const b = await chromium.connectOverCDP('http://127.0.0.1:9222');
const pages = b.contexts().flatMap(c=>c.pages());
const page = pages.find(p=>{try{const u=new URL(p.url());return u.hostname==='127.0.0.1'&&+u.port>=19999&&+u.port<=65535;}catch{return false;}});
page.setDefaultTimeout(15000);
await page.goto(OHOS_BOOTSTRAP_URL,{waitUntil:'domcontentloaded'});
const cat = await page.evaluate(()=>window.__QFLI_OHOS_CATALOG__);
const url = cat.cases.find(c=>c.id==='css-example-157').url;
await page.goto(url,{waitUntil:'domcontentloaded'}); await page.waitForTimeout(300);
await page.mouse.move(-1,-1);
const pre = await page.evaluate(()=>{
  const o=document.getElementById('outer');
  return { docSH: document.documentElement.scrollHeight, bodySH: document.body.scrollHeight,
    innerH: window.innerHeight, innerW: window.innerWidth, scrollY: window.scrollY,
    outerScrollH: o.scrollHeight, outerClientH: o.clientHeight,
    tallH: document.querySelector('.tall').getBoundingClientRect().height,
    bodyMargin: getComputedStyle(document.body).margin };
});
await page.evaluate(()=>{ const o=document.getElementById('outer'); o.scrollTop=o.scrollHeight; });
await page.waitForTimeout(120);
const outerBox = await page.locator('#outer').boundingBox();
await page.mouse.move(outerBox.x + outerBox.width/2, outerBox.y + outerBox.height/2);
const before = await page.evaluate(()=>({y: window.scrollY, top: document.getElementById('outer').scrollTop}));
await page.mouse.wheel(0, 600);
await page.waitForTimeout(400);
const after = await page.evaluate(()=>({y: window.scrollY, top: document.getElementById('outer').scrollTop}));
console.log(JSON.stringify({pre, outerBox, before, after}, null, 1));
writeFileSync(resolve(here,'probe-native-157.json'), JSON.stringify({pre,outerBox,before,after},null,1),'utf8');
await page.goto(OHOS_BOOTSTRAP_URL,{waitUntil:'domcontentloaded'}).catch(()=>{});
await b.close();
