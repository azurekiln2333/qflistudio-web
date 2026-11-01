// Task-local one-off transform: rewrite `(await text(page, SEL)).then((s) => EXPR)`
// into `await probeText(page, SEL, (s) => EXPR)` in the expansion oracle, and
// insert the probeText helper. Not part of the shipped product.
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../../../..');
const file = resolve(repo, 'scripts/html_expansion_assertions.mjs');
let src = readFileSync(file, 'utf8');

function findClose(s, openIdx) {
  // openIdx points at '('
  let depth = 0;
  for (let i = openIdx; i < s.length; i++) {
    const ch = s[i];
    if (ch === '(') depth++;
    else if (ch === ')') {
      depth--;
      if (depth === 0) return i;
    } else if (ch === "'" || ch === '"' || ch === '`') {
      const quote = ch;
      i++;
      while (i < s.length) {
        if (s[i] === '\\') { i += 2; continue; }
        if (s[i] === quote) break;
        i++;
      }
    }
  }
  return -1;
}

let replaced = 0;
for (;;) {
  const marker = '(await text(page, ';
  const start = src.indexOf(marker);
  if (start === -1) break;
  const textCallOpen = start + '(await text'.length; // '(' of text(...)
  const textCallClose = findClose(src, textCallOpen);
  if (textCallClose === -1) throw new Error('unbalanced text() call');
  const afterText = src.slice(textCallClose + 1);
  if (!afterText.startsWith(').then((s) => ')) {
    // Already transformed or different shape: skip this occurrence.
    const next = src.indexOf(marker, start + 1);
    if (next === -1) break;
    // Temporarily mask this occurrence to continue scanning.
    src = src.slice(0, start) + src.slice(start).replace(marker, '__SKIP__(await text(page, ');
    continue;
  }
  const sel = src.slice(start + '(await text('.length, textCallClose); // "page, '#state'"
  const thenArrowIdx = textCallClose + 1 + ').then((s) => '.length;
  // find the closing ')' of .then( ... ) : depth starting at 0, the .then call's
  // paren is right before the arrow
  const thenCallParen = src.indexOf('(', textCallClose + 1); // the '(' of .then(
  const thenCallClose = findClose(src, thenCallParen);
  if (thenCallClose === -1) throw new Error('unbalanced then() call');
  const expr = src.slice(thenArrowIdx, thenCallClose);
  const replacement = `await probeText(${sel}, (s) => ${expr})`;
  src = src.slice(0, start) + replacement + src.slice(thenCallClose + 1);
  replaced++;
}
src = src.replace(/__SKIP__\(await text\(page, /g, '(await text(page, ');

const helperAnchor = 'const settle = (page, ms = 150) => page.waitForTimeout(ms);';
const helper = `const probeText = async (page, sel, fn) => Boolean(fn((await text(page, sel)) || ''));\n`;
if (!src.includes('const probeText')) {
  src = src.replace(helperAnchor, `${helperAnchor}\n\n${helper}`);
}

writeFileSync(file, src, 'utf8');
console.log('rewrote', replaced, 'then() probes');
