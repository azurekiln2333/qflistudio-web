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
for (const id of ['css-example-035','css-example-031']) {
  const url = cat.cases.find(c=>c.id===id).url;
  await page.goto(url,{waitUntil:'domcontentloaded'}); await page.waitForTimeout(200);
  const before = await page.evaluate(()=>({bg:getComputedStyle(document.querySelector('.btn')||document.querySelector('.box')).backgroundColor, ml:getComputedStyle(document.querySelector('.btn')||document.querySelector('.box')).marginLeft}));
  await page.mouse.move(2, 2);
  await page.waitForTimeout(150);
  const after = await page.evaluate(()=>({bg:getComputedStyle(document.querySelector('.btn')||document.querySelector('.box')).backgroundColor, ml:getComputedStyle(document.querySelector('.btn')||document.querySelector('.box')).marginLeft}));
  console.log(id, 'hovered:', JSON.stringify(before), '-> moved:', JSON.stringify(after));
}
await page.goto(OHOS_BOOTSTRAP_URL,{waitUntil:'domcontentloaded'}).catch(()=>{});
await b.close();
