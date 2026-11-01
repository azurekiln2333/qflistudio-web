# Existing CSS oracle — static quality audit

Source: scripts/web_markup_assertions.mjs (read-only). Cases: 100. addCheck calls: 362.

Cases with at least one non-literal / host-bound expectation: 47/100.

## css-example-005 (4 checks)
- substring-only: 'linear-gradient applied', bg.includes('linear-gradient'), bg

## css-example-009 (4 checks)
- substring-only:  'quote before content', (await page.locator('.quote').evaluate((el) => getComputedStyle(e
- substring-only:  'quote after content', (await page.locator('.quote').evaluate((el) => getComputedStyle(el

## css-example-010 (4 checks)
- non-none: 'hover translates/scales', transform !== 'none' && transform.includes('matrix'), transform
- substring-only: 'transition ~0.2s', dur.includes('0.2s'), dur

## css-example-015 (5 checks)
- non-none:  'auto-fit minmax columns resolve', (await computed(page, '.wall', 'grid-template-columns'
- non-none: 'card has box shadow', (await computed(page, '.card', 'box-shadow')) !== 'none'

## css-example-020 (4 checks)
- substring-only: 'triangle clip-path polygon', clip.includes('polygon'), clip

## css-example-021 (3 checks)
- positive: 'photo image really decodes', imgs[0]?.naturalWidth > 0, JSON.stringify(imgs[0])
- substring-only: 'photo grayscale+contrast filter', filter.includes('grayscale') && filter.includes('contra
- substring-only: 'glass backdrop blur', backdrop.includes('blur'), backdrop

## css-example-022 (4 checks)
- or-fallback: 'checker layered linear gradients', ((await computed(page, '.checker', 'background-image')
- substring-only: 'glow radial gradient', (await computed(page, '.glow', 'background-image')).includes('radi
- substring-only: 'checker tile size 20x20', (await computed(page, '.checker', 'background-size')).includes(

## css-example-023 (4 checks)
- substring-only: 'counter reset declared', (await computed(page, 'ol.chapters', 'counter-reset')).includes(
- substring-only: '::before uses a counter', before.includes('counter('), before
- substring-only: 'list declares counter-increment', (await computed(page, 'ol.chapters > li', 'counter-incr

## css-example-024 (3 checks)
- or-fallback: 'header spans head area', (await computed(page, 'header', 'grid-area')) === 'head' || (awa
- substring-only: 'named areas declared', areas.includes('head') && areas.includes('side') && areas.includes

## css-example-027 (3 checks)
- non-null: 'checkbox checked', (await attr(page, 'input[type=checkbox]', 'checked')) !== null

## css-example-029 (4 checks)
- positive: 'print media rule declared', printRule.includes('print') || printRule.length > 0, printRul
- or-fallback: 'print media rule declared', printRule.includes('print') || printRule.length > 0, printRul
- non-empty: 'print media rule declared', printRule.includes('print') || printRule.length > 0, printRul
- or-fallback: 'print rule avoids breaks inside cards', printRule.includes('break-inside') || printRule.i
- substring-only: 'print media rule declared', printRule.includes('print') || printRule.length > 0, printRul
- substring-only: 'print rule avoids breaks inside cards', printRule.includes('break-inside') || printRule.i

## css-example-032 (5 checks)
- substring-only: 'ball gains .move class on click', (await attr(page, '.ball', 'class')).includes('move')
- substring-only: 'click applies translateX(160px)', moved.includes('160'), moved

## css-example-033 (3 checks)
- or-fallback: 'list item bold', liWeight === '700' || liWeight === 'bold', liWeight

## css-example-034 (5 checks)
- positive: 'card image really decodes', imgs[0]?.naturalWidth > 0, JSON.stringify(imgs[0])

## css-example-036 (3 checks)
- non-none: 'card box-shadow present', (await computed(page, '.card', 'box-shadow')) !== 'none'
- non-none: 'h1 text-shadow present', (await computed(page, 'h1', 'text-shadow')) !== 'none'

## css-example-040 (3 checks)
- or-fallback: 'text clip applied', (await computed(page, 'h1', 'background-clip')).includes('text') || (
- substring-only: 'h1 gradient background', (await computed(page, 'h1', 'background-image')).includes('linea
- substring-only: 'text clip applied', (await computed(page, 'h1', 'background-clip')).includes('text') || (

## css-example-041 (3 checks)
- non-null: 'badge has ::after block', borderTop !== null
- or-fallback: '::after has no text content', content === '""' || content === 'none' || content === 'norm

## css-example-042 (3 checks)
- substring-only: 'scrollbar-color blue', (await computed(page, '.box', 'scrollbar-color')).includes('26, 11

## css-example-043 (4 checks)
- non-none: 'scrolled shadow present', (await computed(page, '#h', 'box-shadow')) !== 'none'
- substring-only: 'scrolled class applied', (await attr(page, '#h', 'class')).includes('scrolled'), await at

## css-example-044 (3 checks)
- positive: 'article width constrained (65ch)', maxWidth > 0 && maxWidth < viewport, `${maxWidth}`

## css-example-045 (3 checks)
- substring-only: 'check list has ✔ before', before.includes('✔'), before

