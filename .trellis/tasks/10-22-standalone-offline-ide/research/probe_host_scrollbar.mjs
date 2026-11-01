// Measure how this engine reports scrollbar space, for every probe shape that
// matters to css-156. Host-only (Playwright), no device.
import { chromium } from 'playwright';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 960, height: 720 } });
await page.setContent(`<style>
  body { margin: 0; }
  .plain { width: 200px; height: 60px; overflow-y: auto; background: #f1f3f4; }
  .short { width: 200px; height: 60px; overflow-y: auto; scrollbar-gutter: stable; background: #e8f0fe; }
</style>
<div class="plain" id="plain">x</div>
<div class="short" id="short">x</div>`);

const report = await page.evaluate(() => {
  const mk = (css, content = 'x') => {
    const el = document.createElement('div');
    el.style.cssText = `position:absolute;left:-9999px;${css}`;
    el.textContent = content;
    document.body.appendChild(el);
    const out = {
      offsetW: el.offsetWidth,
      clientW: el.clientWidth,
      computedW: getComputedStyle(el).width,
      rectW: el.getBoundingClientRect().width,
      scrollH: el.scrollHeight,
      clientH: el.clientHeight,
    };
    el.remove();
    return out;
  };

  const tall = '<div style="height:200px"></div>';

  const plainScrollFits = mk('width:100px;height:40px;overflow-y:scroll');
  const plainScrollTall = (() => {
    const el = document.createElement('div');
    el.style.cssText = 'position:absolute;left:-9999px;width:100px;height:40px;overflow-y:scroll';
    el.innerHTML = tall;
    document.body.appendChild(el);
    const out = { offsetW: el.offsetWidth, clientW: el.clientWidth, computedW: getComputedStyle(el).width, rectW: el.getBoundingClientRect().width };
    el.remove();
    return out;
  })();
  const plainScrollBorderBox = (() => {
    const el = document.createElement('div');
    el.style.cssText = 'position:absolute;left:-9999px;box-sizing:border-box;width:100px;height:40px;overflow-y:scroll';
    el.innerHTML = tall;
    document.body.appendChild(el);
    const out = { offsetW: el.offsetWidth, clientW: el.clientWidth, computedW: getComputedStyle(el).width };
    el.remove();
    return out;
  })();

  const rootScrollbar = window.innerWidth - document.documentElement.clientWidth;

  const plainEl = document.querySelector('#plain');
  const shortEl = document.querySelector('#short');
  const before = {
    plainClientW: plainEl.clientWidth,
    plainOffsetW: plainEl.offsetWidth,
    shortClientW: shortEl.clientWidth,
    shortOffsetW: shortEl.offsetWidth,
    shortComputedW: getComputedStyle(shortEl).width,
    plainComputedW: getComputedStyle(plainEl).width,
  };
  const fill = () => {
    const d = document.createElement('div');
    d.style.height = '400px';
    return d;
  };
  plainEl.appendChild(fill());
  shortEl.appendChild(fill());
  const after = {
    plainClientW: plainEl.clientWidth,
    plainOffsetW: plainEl.offsetWidth,
    shortClientW: shortEl.clientWidth,
    shortOffsetW: shortEl.offsetWidth,
    shortComputedW: getComputedStyle(shortEl).width,
    plainComputedW: getComputedStyle(plainEl).width,
  };

  return { plainScrollFits, plainScrollTall, plainScrollBorderBox, rootScrollbar, before, after };
});

console.log(JSON.stringify(report, null, 1));
await browser.close();
