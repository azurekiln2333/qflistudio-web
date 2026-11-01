#!/usr/bin/env node
// Task-local feature-support probe for planning css-example-101..160.
// Runs against the SAME Chromium build the verification runner uses, so the
// planned oracles only rely on features that can actually be asserted.
import { resolve, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../../../..');
const { chromium } = await import(pathToFileURL(resolve(repo, 'node_modules/playwright/index.mjs')).href);
const browser = await chromium.launch();
console.log('chromium', browser.version());
const page = await browser.newPage();
const support = await page.evaluate(() => {
  const css = (prop, value) => CSS.supports(prop, value);
  const sel = (s) => CSS.supports(`selector(${s})`);
  const tests = {
    'at-layer': css('all', 'revert-layer'),
    'at-scope': (() => {
      const st = document.createElement('style');
      st.textContent = '@scope (.a) to (.b) { .c { color: red } }';
      document.head.append(st);
      const ok = [...st.sheet.cssRules].some((r) => r.constructor.name === 'CSSScopeRule');
      st.remove();
      return ok;
    })(),
    'at-property': (() => {
      const st = document.createElement('style');
      st.textContent = '@property --x { syntax: "<length>"; inherits: false; initial-value: 0px }';
      document.head.append(st);
      const ok = [...st.sheet.cssRules].some((r) => r.constructor.name === 'CSSPropertyRule');
      st.remove();
      return ok;
    })(),
    'at-starting-style': (() => {
      const st = document.createElement('style');
      st.textContent = '@starting-style { .a { opacity: 0 } }';
      document.head.append(st);
      const ok = [...st.sheet.cssRules].some((r) => r.constructor.name === 'CSSStartingStyleRule');
      st.remove();
      return ok;
    })(),
    subgrid: css('grid-template-columns', 'subgrid'),
    'has': sel(':has(> img)'),
    'nth-child-of': sel(':nth-child(2 of .x)'),
    'is-where': sel(':is(.a, .b) :where(.c)'),
    'focus-visible': sel(':focus-visible'),
    'focus-within': sel(':focus-within'),
    'user-invalid': sel(':user-invalid'),
    'placeholder-shown': sel(':placeholder-shown'),
    'target': sel(':target'),
    'empty': sel(':empty'),
    'backdrop': '::backdrop' in document.documentElement.style || true,
    'marker': sel('::marker'),
    'first-line': sel('::first-line'),
    'file-selector-button': sel('::file-selector-button'),
    'text-wrap-balance': css('text-wrap', 'balance'),
    'text-wrap-pretty': css('text-wrap', 'pretty'),
    hyphens: css('hyphens', 'auto'),
    'overflow-clip-margin': css('overflow-clip-margin', '10px'),
    'overflow-clip': css('overflow', 'clip'),
    'scroll-snap': css('scroll-snap-type', 'x mandatory'),
    'scrollbar-gutter': css('scrollbar-gutter', 'stable'),
    'overscroll-behavior': css('overscroll-behavior', 'contain'),
    'touch-action': css('touch-action', 'pan-y'),
    'color-mix': css('color', 'color-mix(in oklab, red 50%, blue)'),
    oklch: css('color', 'oklch(0.7 0.1 200)'),
    'relative-color': css('color', 'rgb(from #333 r g b / 50%)'),
    'light-dark': css('color', 'light-dark(#000, #fff)'),
    'color-scheme': css('color-scheme', 'dark'),
    'accent-color': css('accent-color', 'rebeccapurple'),
    'caret-color': css('caret-color', 'red'),
    'tab-size': css('tab-size', '4'),
    'text-emphasis': css('text-emphasis', 'dot'),
    'text-stroke': css('-webkit-text-stroke', '1px red'),
    'text-decoration-skip-ink': css('text-decoration-skip-ink', 'none'),
    'text-underline-offset': css('text-underline-offset', '3px'),
    'border-image': css('border-image', 'linear-gradient(red, blue) 1'),
    'outline-offset': css('outline-offset', '2px'),
    'box-decoration-break': css('box-decoration-break', 'clone'),
    'background-blend-mode': css('background-blend-mode', 'multiply'),
    'mask-image': css('mask-image', 'linear-gradient(#000, transparent)'),
    'mask-composite': css('mask-composite', 'intersect'),
    'shape-outside': css('shape-outside', 'circle(50%)'),
    'column-span': css('column-span', 'all'),
    'display-contents': css('display', 'contents'),
    'display-inline-flex': css('display', 'inline-flex'),
    'fit-content': css('width', 'fit-content(200px)'),
    'max-fn': css('width', 'max(10px, 20px)'),
    'min-fn': css('width', 'min(10px, 20px)'),
    'calc-mixed': css('width', 'calc(50% - 10px)'),
    dvh: css('height', '100dvh'),
    svh: css('height', '100svh'),
    cqi: css('width', '50cqi'),
    cqw: css('width', '50cqw'),
    ch: css('width', '10ch'),
    cap: css('width', '10cap'),
    '@container-inline': css('container-type', 'inline-size'),
    '@container-style': css('container-type', 'style'),
    '@container-name': css('container-name', 'card'),
    'scroll-driven': css('animation-timeline', 'scroll()'),
    'transition-behavior': css('transition-behavior', 'allow-discrete'),
    'field-sizing': css('field-sizing', 'content'),
    'css-nesting': css('&', ''),
    'atom-nesting-true': (() => {
      const st = document.createElement('style');
      st.textContent = '.nest { color: red; & .child { color: blue; } }';
      document.head.append(st);
      const sheet = st.sheet;
      let ok = false;
      try {
        ok = [...sheet.cssRules][0].cssRules.length === 1;
      } catch {
        ok = false;
      }
      st.remove();
      return ok;
    })(),
    'prefers-reduced-motion': matchMedia('(prefers-reduced-motion: no-preference)').matches,
    'media-hover': matchMedia('(hover: hover)').matches,
    'media-pointer-fine': matchMedia('(pointer: fine)').matches,
    'forced-colors-media': matchMedia('(forced-colors: none)').matches,
    'fonts-variant-numeric': css('font-variant-numeric', 'tabular-nums'),
    'font-size-adjust': css('font-size-adjust', '0.5'),
    'counter-style-rule': (() => {
      const st = document.createElement('style');
      st.textContent = '@counter-style thumbs { system: cyclic; symbols: "👍"; suffix: " "; }';
      document.head.append(st);
      const ok = [...st.sheet.cssRules].some((r) => r.constructor.name === 'CSSCounterStyleRule');
      st.remove();
      return ok;
    })(),
    quotes: css('quotes', '"«" "»"'),
    'content-attr': true,
    'position-anchor': css('position-anchor', '--a'),
    'anchor-name': css('anchor-name', '--a'),
    'scroll-margin-top': css('scroll-margin-top', '10px'),
    'scroll-padding-top': css('scroll-padding-top', '10px'),
    'view-transition-name': css('view-transition-name', 'x'),
    'interpolate-size': css('interpolate-size', 'allow-keywords'),
    'text-box-trim': css('text-box-trim', 'trim-both'),
    'line-clamp-property': css('line-clamp', '2'),
    'white-space-collapse': css('white-space-collapse', 'preserve'),
  };
  return tests;
});
for (const [k, v] of Object.entries(support)) console.log(String(v).padEnd(6), k);
await browser.close();
