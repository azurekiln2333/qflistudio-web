// Read-only helper: print the oracle case blocks for given ids.
import { readFileSync } from 'node:fs';
const src = readFileSync('scripts/html_expansion_assertions.mjs', 'utf8');
const ids = process.argv.slice(2);
for (const id of ids) {
  const start = src.indexOf("CASES.set('" + id + "'");
  if (start === -1) {
    console.log('MISSING CASE', id);
    continue;
  }
  const next = src.indexOf("CASES.set('", start + 10);
  const stop = next === -1 ? src.length : next;
  console.log('='.repeat(30), id);
  console.log(src.slice(start, stop).trimEnd());
}
