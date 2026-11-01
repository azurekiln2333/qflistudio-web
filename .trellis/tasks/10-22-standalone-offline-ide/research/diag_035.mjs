import { resolve, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../../../../');
const { chromium } = await import(pathToFileURL(resolve(repo, 'node_modules/playwright/index.mjs')).href);
const { OHOS_BOOTSTRAP_URL } = await import(pathToFileURL(resolve(repo, 'scripts/catalog_device_contract.mjs')).href);
const b = await chromium.connectOverCDP('http://127.0.0.1:9222');
const pages = b.contexts().flatMap(c=>c.pages());
const page = pages.find(p=>{try{const u=new URL(p.url());return u.hostname==='127.0.0.1'&&+u.port>=19999&&+u.port<=65535;}catch{return false;}});
page.setDefaultTimeout(15000);
await page.goto(OHOS_BOOTSTRAP_URL,{waitUntil:'domcontentloaded'});
const cat = await page.evaluate(()=>window.__QFLI_OHOS_CATALOG__);
const url = cat.cases.find(c=>c.id==='css-example-035').url;
await page.goto(url,{waitUntil:'domcontentloaded'}); await page.waitForTimeout(250);
await page.mouse.move(-1,-1);
await page.keyboard.press('Tab');
await page.waitForTimeout(200);
const r = await page.evaluate(()=>{
  const b=document.querySelector('.btn'); const cs=getComputedStyle(b);
  return { active: document.activeElement.className, focusVisible: b.matches(':focus-visible'),
    ow: cs.outlineWidth, os: cs.outlineStyle, oc: cs.outlineColor, oo: cs.outlineOffset };
});
console.log(JSON.stringify(r,null,1));
await page.goto(OHOS_BOOTSTRAP_URL,{waitUntil:'domcontentloaded'}).catch(()=>{});
await b.close();
